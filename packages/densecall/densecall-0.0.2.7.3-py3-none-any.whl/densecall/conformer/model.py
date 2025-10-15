import numpy as np
import torch
from torch.nn.utils.rnn import pad_sequence
from torch import nn
import torch.nn.functional as F
from torch import Tensor
from fast_ctc_decode import beam_search, viterbi_search
from .criterion import *
from .nn import *
from densecall.util import qstring_
from .wav2vec2 import Wav2Vec2Model as KQWav2Vec2Model
from transformers import Wav2Vec2Model, Wav2Vec2Config
from transformers import AutoTokenizer, AutoModel
from functorch import vmap 
from torchaudio.models.decoder import ctc_decoder

# LM_WEIGHT = 1
# WORD_SCORE = 2
# lm = 'dna_lm_6gram.bin'
# lm_decoder = ctc_decoder(
#     lexicon=None,
#     tokens=['N', 'A', 'C', 'G', 'T'],
#     nbest=1,
#     beam_size=5,
#     beam_threshold=50,
#     blank_token="N",
#     sil_token="N",


# )



        

class PretrainedModel(nn.Module):
    
    def __init__(self, config={}):
        super(PretrainedModel, self).__init__()
        
        self.config = config
        self.alphabet = config['basecaller']['alphabet']
        
        self.qbias =  config['qscore']['bias']
        self.qscale =  config['qscore']['scale']
        self.criterion = config['criterion']['loss']
        self.stride = config['encoder']['stride']

        
        #configuration = Wav2Vec2Config()
        # configuration.conv_stride = [1, 1, 1, 6]
        # configuration.conv_dim = [1, 32, 64, 128]
        # configuration.num_hidden_layers = 6
        # configuration.hidden_size = 256
        # configuration.num_attention_heads = 4
        # configuration.intermediate_size = 2048
        # self.sub_model = Wav2Vec2Model(configuration)
        
        self.sub_model = Wav2Vec2Model.from_pretrained('facebook/wav2vec2-base', attn_implementation="flash_attention_2")
        for single_cnn in self.sub_model.feature_extractor.conv_layers:
            single_cnn.conv.stride=(1,)
        single_cnn.conv.stride=(5,)
        self.drop_out = nn.Dropout(0.1)
        self.classifier= nn.Linear(self.sub_model.config.hidden_size, len(self.alphabet))
        print(self.sub_model)
        self.sub_model.freeze_feature_encoder()

    def forward(self, x, mask = None):
        x = self.sub_model(input_values = x.squeeze(1), attention_mask = mask)
        x = x[0]
        x = self.classifier(self.drop_out(x)).transpose(0, 1)
        return x
    
    @torch.no_grad()
    def decode(self, x, beamsize=5, threshold=1e-3, qscores=False, return_path=False):
            
        x = F.softmax(x, -1) #NTC, has been transposed, so it is NTC
        x = x.cpu().numpy()
            
        if beamsize == 1:
            seq, path  = viterbi_search(x, self.alphabet, qscores, self.qscale, self.qbias)
        else:
            seq, path = beam_search(x.astype(np.float32), self.alphabet, beamsize, threshold)
            qstring = ''.join(phred(np.max(x[path], 1), self.qscale, self.qbias).astype(str))
            if qscores:
                seq += qstring
        if return_path: return seq, path
        return seq
    

    def loss(self, ctc_logits, data_lengths_, targets, lengths):
        
        data_lengths_ = data_lengths_ // self.stride
        
        ctc_log_probs = F.log_softmax(ctc_logits, -1) #TNC
        T, N, C = ctc_log_probs.shape
        log_probs_lengths = torch.full(size=(N,), fill_value=T, dtype=torch.int64, device=ctc_log_probs.device)

        labels_mask = targets > 0
        target_lengths = labels_mask.sum(-1)
        flattened_targets = targets.masked_select(labels_mask)

        if self.criterion == 'focal':
            return focal_ctc_label_smoothing_loss(ctc_log_probs, log_probs_lengths, targets, lengths)

        ctc_loss = F.ctc_loss(ctc_log_probs, flattened_targets, log_probs_lengths, target_lengths, reduction="mean", zero_infinity=True)

        self.weights = torch.tensor([0.35, 0.025, 0.025, 0.05, 0.025, 0.025])
           
        label_smoothing_loss =  -((ctc_log_probs * self.weights.to(ctc_log_probs.device)).mean())
             
        total_loss = ctc_loss  + label_smoothing_loss
        
        return {"total_loss":total_loss, "loss":ctc_loss, "smooth_loss":label_smoothing_loss}
    
    

class Model(nn.Module):
    def __init__(self, config={}):

        super(Model, self).__init__()

        
        self.config = config

        self.conv_dim = config['feature_extractor']['conv_dim']
        self.conv_kernel = config['feature_extractor']['conv_kernel']
        self.conv_stride = config['feature_extractor']['conv_stride_finetune']
        self.stride = config['encoder']['stride']
        self.scale_factor = int(math.prod(self.conv_stride) / self.stride)
        self.alphabet = config['basecaller']['alphabet']
        self.activation = activation_fn(config['general']['activation'])
        
        self.embed_size = config['encoder']['embed_size']
        self.n_heads = config['encoder']['n_heads']
        self.norm = config['general']['norm']
        
        self.qbias =  config['qscore']['bias']
        self.qscale =  config['qscore']['scale']
        self.criterion = config['criterion']['loss']
        self.hybrid = config['encoder']['hybrid']
        self.use_smoothed_loss = config['criterion']['use_smoothed_loss']
        

        self.feature_extractor = FeatureExtraction(self.conv_dim, self.conv_kernel, self.conv_stride, activation=self.activation)
        self.feature_projection = FeatureProjection(self.conv_dim[-1], self.embed_size, norm=self.norm)
        

        self.encoder = Encoder(config)
        self.classifier = self.encoder.classifier
        self.weights = self.smooth_weights()
    
        if self.hybrid:
            self.attn_decoder = AttentionDecoder(len(self.alphabet), self.embed_size, self.n_heads,  num_layers=1)
        
        #self.o1loss = O1Loss(len(self.alphabet), beam_size=10)

        #self._init_conv_layers()
        #self.apply(self._init_weights)
        

    @torch.no_grad()        
    def _init_conv_layers(self):

        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_uniform_(m.weight, a=math.sqrt(5))
                if m.bias is not None:
                    fan_in, _ = nn.init._calculate_fan_in_and_fan_out(m.weight)
                    bound = 1 / math.sqrt(fan_in) if fan_in > 0 else 0
                    nn.init.uniform_(m.bias, -bound, bound)
                    
            if isinstance(m, nn.Conv1d):
                nn.init.kaiming_uniform_(m.weight, a=math.sqrt(5))
                if m.bias is not None:
                    fan_in, _ = nn.init._calculate_fan_in_and_fan_out(m.weight)
                    if fan_in != 0:
                        bound = 1 / math.sqrt(fan_in)
                        nn.init.uniform_(m.bias, -bound, bound)
           
    @torch.no_grad()        
    def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, FeatureProjection):
            if  hasattr(module, "projection"):
                k = math.sqrt(1 / module.projection.in_features)
                nn.init.uniform_(module.projection.weight, a=-k, b=k)
                nn.init.uniform_(module.projection.bias, a=-k, b=k)
        elif isinstance(module, nn.Linear):
            module.weight.data.normal_(mean=0.0, std=0.02)
            if module.bias is not None:
                module.bias.data.zero_()
                

    def smooth_weights(self):
        acgt_count = sum(c in 'ACGT' for c in self.alphabet)
        acgt_weight = 0.1 / acgt_count if acgt_count else 0
        other_base_count = sum(c not in 'NACGT' for c in self.alphabet)
        other_base_weight = acgt_weight * 3
        weights = []
        for c in self.alphabet:
            if c in 'ACGT':
                weights.append(acgt_weight)
            elif c == 'N':
                weights.append(0.4 - other_base_count * other_base_weight)
            else:
                weights.append(other_base_weight)
        return torch.tensor(weights)
            

            
    def forward(self, x):
        x = self.feature_extractor(x).transpose(1, 2)  # NTC
        x, _ = self.feature_projection(x)    
        inter_logits, h = self.encoder(x)
        logits = self.classifier(h).transpose(0,1)
        return (logits, inter_logits, h) #TNC

    

    @torch.no_grad()
    def decode(self, x, beamsize=5, threshold=1e-3, qscores=False, return_path=False):
            
        x = F.softmax(x, -1) #NTC, has been transposed, so it is NTC
        x = x.cpu().numpy()
            
        if beamsize == 1:
            seq, path  = viterbi_search(x, self.alphabet, qscores, self.qscale, self.qbias)
        else:
            seq, path = beam_search(x.astype(np.float32), self.alphabet, beamsize, threshold)
            qstring = ''.join(qstring_(np.max(x[path], 1), self.qscale, self.qbias).astype(str))
            if qscores:
                seq += qstring
        if return_path: return seq, path
        return seq
    

    @torch.no_grad()
    def joint_decode2(self, xs, beamsize=10, threshold=1e-3, qscores=False, return_path=False):
        
        from densecall.conformer.beam_search import beam_search
            
        ctc_logits, _, encoder_out = xs
        ctc_probs = F.softmax(ctc_logits, dim=-1).transpose(0,1) #NTC
        B, T, V = ctc_probs.shape
        seqs = []
        paths = []
        for b in range(B):
            ctc_prob = ctc_probs[b]
            h = encoder_out[b]
            probs = ctc_prob.cpu().numpy()
            beams, beam_paths, scores = beam_search(probs, self.alphabet, beamsize, threshold)
            scores = torch.tensor(scores, device=h.device)
            scores = torch.log(scores + 1e-9)

            if len(beams) == 1:
                seq = ''.join([self.alphabet[i] for i in beams[0] if i > 0])
                seqs.append(seq)
                continue

            # 第2步：Attention批量重打分
            L = len(beams)
            max_len = max((beam > 0).sum() for beam in beams)
            ys = torch.zeros((L, max_len + 1), dtype=torch.long, device=h.device)
            for i, seq in enumerate(beams):
                seq = torch.tensor(seq, device=h.device)
                ys[i, 1:1 + seq.size(0)] = seq
                
            logits = self.attn_decoder(ys[:, :-1], h.unsqueeze(0).expand(L, -1, -1), h_mask=None)
            attn_scores = torch.gather(torch.log_softmax(logits, dim=-1), 2, ys[:, 1:].unsqueeze(-1)).squeeze(-1).sum(dim=1)
            total = attn_scores + scores
            best_idx = total.argmax()
            seq = ''.join([self.alphabet[i] for i in beams[best_idx]])
            qstring = ''.join(phred(np.max(probs[beam_paths[best_idx]], 1), self.qscale, self.qbias).astype(str))
            if qscores:
                seq += qstring

            seqs.append(seq)
            paths.append(beam_paths[best_idx])
        if return_path: return seqs, paths
        return seqs

    def loss(self, scores, data_lengths_, targets, lengths):
        
        data_lengths_ = data_lengths_ // self.stride

        ctc_logits, ctc_inter_logits, h = scores
        
        ctc_log_probs = F.log_softmax(ctc_logits, -1) #TNC
        T, N, C = ctc_log_probs.shape
        log_probs_lengths = torch.full(size=(N,), fill_value=T, dtype=torch.int64, device=ctc_log_probs.device)

        labels_mask = targets > 0
        target_lengths = labels_mask.sum(-1)
        flattened_targets = targets.masked_select(labels_mask)
        
        other_loss = {}
    

        if self.criterion == 'focal':
            ctc_loss =  focal_ctc(ctc_log_probs, log_probs_lengths, targets, lengths, alphabet=self.alphabet)
            
        elif self.criterion == 'ctc':
            ctc_loss = F.ctc_loss(ctc_log_probs, flattened_targets, log_probs_lengths, target_lengths, reduction="mean", zero_infinity=True)
        
        else:
            raise ValueError(f'Unknown criterion {self.criterion}')
        
        inter_loss = torch.tensor(0.0, device=ctc_logits.device)
        if len(ctc_inter_logits) > 0:
            inter_logits = torch.cat(ctc_inter_logits, 1)
            if self.criterion == 'focal':
                inter_loss = focal_ctc(F.log_softmax(inter_logits, -1), log_probs_lengths.repeat(len(ctc_inter_logits)), targets.repeat(len(ctc_inter_logits), 1), lengths.repeat(len(ctc_inter_logits)))
            else:
                inter_loss = _single_ctc(F.log_softmax(inter_logits, -1), log_probs_lengths.repeat(len(ctc_inter_logits)), targets.repeat(len(ctc_inter_logits), 1), lengths.repeat(len(ctc_inter_logits)))
            other_loss['inter_loss'] = inter_loss / len(ctc_inter_logits)



        ctc_loss = (ctc_loss + inter_loss / len(ctc_inter_logits)) / 2 if len(ctc_inter_logits) > 0 else ctc_loss
        
        if self.hybrid:
            h_mask = torch.arange(T, device=h.device).unsqueeze(0) >= data_lengths_.unsqueeze(1)
            y_in  = torch.cat([torch.ones(targets.size(0),1, dtype=torch.long, device=targets.device)*0, targets], dim=1)[:,:-1]
            logits_att = self.attn_decoder(y_in, h, h_mask)
            unique_labels, counts = torch.unique(flattened_targets, return_counts=True)
            total_count = counts.sum().float()
            freq = torch.zeros(C, device=ctc_logits.device)
            freq[unique_labels] = counts.float() / total_count
            dynamic_weights = 1.0 / (freq + 1e-8)
            dynamic_weights = dynamic_weights / dynamic_weights.mean()
            loss_att = F.cross_entropy(logits_att.reshape(-1, logits_att.size(-1)), targets.reshape(-1), ignore_index=0, weight=dynamic_weights)
            alpha = 0.5
            other_loss['loss_att'] = loss_att
        else:
            loss_att = torch.tensor(0.0, device=ctc_logits.device)
            alpha = 1
        
            
        total_loss = alpha * ctc_loss + (1 - alpha) * loss_att 
        
        if self.use_smoothed_loss:
            label_smoothing_loss =  -((ctc_log_probs * self.weights.to(ctc_log_probs.device)).mean())
            total_loss += label_smoothing_loss
            other_loss['smooth_loss'] = label_smoothing_loss
        
        return {"total_loss":total_loss, "loss":ctc_loss, **other_loss}
    
    
    def loss2(self, scores, data_lengths_, targets, lengths):
            
        ctc_logits, _, _ = scores
        ctc_log_probs = F.log_softmax(ctc_logits, -1) #TNC
        T, N, C = ctc_log_probs.shape
        log_probs_lengths = torch.full(size=(N,), fill_value=T, dtype=torch.int64, device=ctc_log_probs.device)

        
        if self.criterion == 'ctc':
            ctc_loss = ctc_label_smoothing_loss(ctc_log_probs, log_probs_lengths, targets, lengths, weights = self.weights)
        elif self.criterion == 'crf':
            ctc_loss = crf_loss(ctc_log_probs, targets, lengths, self.ctc_crf)  
        elif self.criterion == 'focal':
            ctc_loss = focal_ctc_label_smoothing_loss(ctc_log_probs, log_probs_lengths, targets, lengths)

        return ctc_loss


def _single_ctc(ctc_log_probs, log_probs_lengths, tgt, tgt_len):
    #print(ctc_log_probs.shape, tgt.shape, tgt_len.shape)
    T, N, C = ctc_log_probs.shape
    log_probs_lengths = torch.full(size=(N,), fill_value=T, dtype=torch.int64, device=ctc_log_probs.device)
    return F.ctc_loss(ctc_log_probs.to(torch.float32), tgt,
                      log_probs_lengths,
                      tgt_len, reduction='mean', zero_infinity=True)


