import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np 
from fast_ctc_decode import beam_search, viterbi_search, crf_greedy_search, crf_beam_search
from abc import abstractmethod
from torch.nn.functional import log_softmax, ctc_loss
from torch.autograd import Variable
from transformers.models.wav2vec2.modeling_wav2vec2 import _compute_mask_indices, _sample_negative_indices, Wav2Vec2GumbelVectorQuantizer
from functools import partial
from typing import Optional, Tuple, Union




class FeatureProjection(nn.Module):
    def __init__(self, fin, fout):
        super().__init__()
        self.layer_norm = nn.LayerNorm(fin, eps=1e-5)
        self.projection = nn.Linear(fin, fout)
        self.dropout = nn.Dropout(0.1)

    def forward(self, hidden_states):
        # non-projected hidden states are needed for quantization
        norm_hidden_states = self.layer_norm(hidden_states)
        hidden_states = self.projection(norm_hidden_states)
        hidden_states = self.dropout(hidden_states)
        return hidden_states, norm_hidden_states
    
class Wav2Vec2GumbelVectorQuantizer(nn.Module):
    """
    Vector quantization using gumbel softmax. See `[CATEGORICAL REPARAMETERIZATION WITH
    GUMBEL-SOFTMAX](https://arxiv.org/pdf/1611.01144.pdf) for more information.
    """

    def __init__(self, config):
        super().__init__()
        self.num_groups = config.num_codevector_groups
        self.num_vars = config.num_codevectors_per_group

        if config.codevector_dim % self.num_groups != 0:
            raise ValueError(
                f"`config.codevector_dim {config.codevector_dim} must be divisible "
                f"by `config.num_codevector_groups` {self.num_groups} for concatenation"
            )

        # storage for codebook variables (codewords)
        self.codevectors = nn.Parameter(
            torch.FloatTensor(1, self.num_groups * self.num_vars, config.codevector_dim // self.num_groups)
        )
        self.weight_proj = nn.Linear(config.conv_dim[-1], self.num_groups * self.num_vars)

        # can be decayed for training
        self.temperature = 2

    @staticmethod
    def _compute_perplexity(probs, mask=None):
        if mask is not None:
            mask_extended = mask.flatten()[:, None, None].expand(probs.shape)
            print(333)
            probs = torch.where(mask_extended, probs, torch.zeros_like(probs))
            marginal_probs = probs.sum(dim=0) / mask.sum()
        else:
            marginal_probs = probs.mean(dim=0)

        perplexity = torch.exp(-torch.sum(marginal_probs * torch.log(marginal_probs + 1e-7), dim=-1)).sum()
        return perplexity

    def forward(self, hidden_states, mask_time_indices=None):
        batch_size, sequence_length, hidden_size = hidden_states.shape

        # project to codevector dim
        hidden_states = self.weight_proj(hidden_states)
        hidden_states = hidden_states.view(batch_size * sequence_length * self.num_groups, -1)

        if self.training:
            # sample code vector probs via gumbel in differentiateable way
            codevector_probs = nn.functional.gumbel_softmax(
                hidden_states.float(), tau=self.temperature, hard=True
            ).type_as(hidden_states)

            # compute perplexity
            codevector_soft_dist = torch.softmax(
                hidden_states.view(batch_size * sequence_length, self.num_groups, -1).float(), dim=-1
            )
            perplexity = self._compute_perplexity(codevector_soft_dist, mask_time_indices)
        else:
            # take argmax in non-differentiable way
            # comptute hard codevector distribution (one hot)
            codevector_idx = hidden_states.argmax(dim=-1)
            codevector_probs = hidden_states.new_zeros(hidden_states.shape).scatter_(
                -1, codevector_idx.view(-1, 1), 1.0
            )
            codevector_probs = codevector_probs.view(batch_size * sequence_length, self.num_groups, -1)

            perplexity = self._compute_perplexity(codevector_probs, mask_time_indices)

        codevector_probs = codevector_probs.view(batch_size * sequence_length, -1)
        # use probs to retrieve codevectors
        codevectors_per_group = codevector_probs.unsqueeze(-1) * self.codevectors
        codevectors = codevectors_per_group.view(batch_size * sequence_length, self.num_groups, self.num_vars, -1)
        codevectors = codevectors.sum(-2).view(batch_size, sequence_length, -1)

        return codevectors, perplexity
    
def compute_contrastive_logits(
        target_features: torch.FloatTensor,
        negative_features: torch.FloatTensor,
        predicted_features: torch.FloatTensor,
        temperature: int = 0.1,
    ):
        """
        Compute logits for contrastive loss based using cosine similarity as the distance measure between
        `[positive_feature, negative_features]` and `[predicted_features]`. Additionally, temperature can be applied.
        """
        target_features = torch.cat([target_features, negative_features], dim=0)

        logits = torch.cosine_similarity(predicted_features.float(), target_features.float(), dim=-1).type_as(
            target_features
        )

        # apply temperature
        logits = logits / temperature
        return logits
    
def pad_list(xs, pad_value):
    n_batch = len(xs)
    max_len = max(x.size(0) for x in xs)
    pad = xs[0].new(n_batch, max_len, *xs[0].size()[1:]).fill_(pad_value)

    for i in range(n_batch):
        pad[i, : xs[i].size(0)] = xs[i]

    return pad

def add_sos_eos(ys_pad, sos, eos, ignore_id):

    _sos = ys_pad.new([sos])
    _eos = ys_pad.new([eos])
    ys = [y[y != ignore_id] for y in ys_pad]  
    ys_in = [torch.cat([_sos, y], dim=0) for y in ys]
    ys_out = [torch.cat([y, _eos], dim=0) for y in ys]
    return pad_list(ys_in, eos), pad_list(ys_out, ignore_id)

class Permute(nn.Module):

    def __init__(self, dims):
        super().__init__()
        self.dims = dims

    def forward(self, x):
        return x.permute(*self.dims)

    def to_dict(self, include_weights=False):
        return {'dims': self.dims}

    def extra_repr(self):
        return 'dims={}'.format(self.dims)
    
class BaseModel(nn.Module):
    
    def __init__(self, config, *args, **kwargs):
        
        super(BaseModel, self).__init__()
        self.config = config
        
    @abstractmethod
    def forward(self, batch):
        """Forward through the network
        """
        raise NotImplementedError()
    
    def ctc_label_smoothing_loss(self, log_probs, targets, lengths, weights=None):
        T, N, C = log_probs.shape
        weights = weights or torch.cat([torch.tensor([0.4]), (0.1 / (C - 1)) * torch.ones(C - 1)])
        log_probs_lengths = torch.full(size=(N, ), fill_value=T, dtype=torch.int64)
        loss = ctc_loss(log_probs.to(torch.float32), targets, log_probs_lengths, lengths, reduction='mean')
        label_smoothing_loss = -((log_probs * weights.to(log_probs.device)).mean())
        return {'total_loss': loss + label_smoothing_loss, 'loss': loss, 'label_smooth_loss': label_smoothing_loss}

    def loss(self, log_probs, targets, lengths):
        return self.ctc_label_smoothing_loss(log_probs, targets, lengths)
    
    def use_koi(self, **kwargs):
        pass
    
    
    def decode(self, x, beamsize=5, threshold=1e-3, qscores=False, return_path=False):
        #print(x)
        x = x.exp().cpu().numpy().astype(np.float32)
        #print(x)
        if beamsize == 1 or qscores:
            seq, path  = viterbi_search(x, self.alphabet, qscores, self.qscale, self.qbias)
        else:
            
            seq, path = beam_search(x, self.alphabet, beamsize, threshold)
            qstring = ''.join(phred(np.max(x[path], 1), self.qscale, self.qbias).astype(str))
            seq += qstring
        if return_path: return seq, path
        return seq
    
    # @torch.no_grad()
    # def decode_batch(self, encoder_outputs: Tensor) -> Tensor:
    #     logits = list()
    #     batch_size = encoder_outputs.size(0)
    #     T = encoder_outputs.size(1)
    #     self.max_length = 361

    #     input_var = torch.full((batch_size, 1), 0, dtype=torch.long, device=encoder_outputs.device)


    #     for di in range(1, self.max_length):
    #         input_lengths = torch.tensor([di] * batch_size, dtype=torch.int64, device=encoder_outputs.device)
    #         outputs = self.forward_step(
    #             decoder_inputs=input_var,
    #             decoder_input_lengths=input_lengths,
    #             encoder_outputs=encoder_outputs,
    #             positional_encoding_length=di,
    #             flag=False
    #         )

    #         step_output = self.fc(outputs).log_softmax(dim=-1)
    #         logits.append(step_output[:, -1, :])
    #         next_token = logits[-1].topk(1)[1]
    #         input_var = torch.cat([input_var, next_token], dim=1)
    #         if all((input_var == 0).any(dim=1)):
    #             break

    #     logits  = torch.stack(logits, dim=1)
    #     logits = torch.argmax(logits, dim=-1)
    #     seqs = []
    #     for x in logits:
    #         seq = []
    #         for i in x:
    #             seq.append(self.alphabet[i])
    #         seqs.append(''.join(seq))
    #         print(len(seq), seq[:30])
    #     return seqs

    
 
def phred(prob: np.ndarray, qscale: float = 1, qbias: float = 0) -> np.ndarray:
    max_value = 1e-4
    # 使用np.maximum确保p至少为max_value
    p = np.maximum(max_value, 1.0 - prob)
    # 计算Q值
    q = -10.0 * np.log10(p) * qscale + qbias
    # 将q值四舍五入并且转换为整数
    q_rounded = np.round(q).astype(int)
    # 转换为字符
    result = (q_rounded + 33).astype(np.uint8).view('S1')
    return result
    
class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super(PositionalEncoding, self).__init__()
        position = torch.arange(0, max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * -(torch.log(torch.tensor(10000.0)) / d_model))
        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(position.float() * div_term)
        pe[:, 1::2] = torch.cos(position.float() * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)

    def forward(self, x):
        return x + self.pe[:x.size(0), :]

class TransformerWithConvInput(nn.Module):
    def __init__(self, n_channels, d_model, nhead, dim_feedforward, num_layers, max_len=5000):
        super(TransformerWithConvInput, self).__init__()
        self.conv = nn.Conv1d(in_channels=n_channels, out_channels=d_model, kernel_size=3, padding=1)
        self.pos_encoder = PositionalEncoding(d_model, max_len=max_len)
        encoder_layers = nn.TransformerEncoderLayer(d_model, nhead, dim_feedforward)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers)
        self.fc = nn.Linear(d_model, n_channels)

    def forward(self, src):
        #src = src.permute(0, 2, 1)  # Conv1d expects input in (batch_size, channels, seq_len) format
        src = F.relu(self.conv(src))
        src = src.permute(2, 0, 1)  # Transformer expects input in (seq_len, batch_size, channels) format
        src = self.pos_encoder(src)
        output = self.transformer_encoder(src)
        output = self.fc(output)
        output = output.permute(1, 2, 0)  # Back to (batch_size, channels, seq_len ) format
        return output
    
    
class Mish(nn.Module):
    def __init__(self):
        super().__init__()
    def forward(self, x):
        return x *( torch.tanh(torch.nn.functional.softplus(x)))

class squeeze_excite(torch.nn.Module):
    def __init__(self, in_channels = 512, size=1, reduction="/16", activation=torch.nn.GELU):
        super(squeeze_excite, self).__init__()
        self.in_channels = in_channels
        self.avg = torch.nn.AdaptiveAvgPool1d(1)
        if type(reduction) == str:
            self.reductionsize = self.in_channels // int(reduction[1:])
        else:
            self.reductionsize = reduction
        self.fc1 = nn.Linear(self.in_channels, self.reductionsize)
        self.activation = activation() # was nn.ReLU(inplace=True)
        self.fc2 = nn.Linear(self.reductionsize, self.in_channels)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        input = x
        x = self.avg(x)
        x = x.permute(0,2,1)
        x = self.activation(self.fc1(x))
        x = self.sigmoid(self.fc2(x))
        return input * x.permute(0,2,1)


class simpleRNN(nn.Module):
    def __init__(self, in_channel, out_channel):
        super(simpleRNN, self).__init__()
        self.relu0 =nn.ReLU()
        self.kernel_size1 = 7
        self.kernel_size2 = 7
        self.padding1 = 3
        self.padding2 = 3
        self.downsample = nn.MaxPool1d(3, stride=2, ceil_mode=True)
        self.upsample = nn.Upsample(scale_factor=2)
        self.convs1 = nn.Conv1d(in_channel, out_channel//4, self.kernel_size1, stride=2, padding=self.padding1)
        self.bns1 = nn.BatchNorm1d(out_channel//4)
        self.convs2 = nn.Conv1d(out_channel//4, out_channel//2, self.kernel_size2, stride=2, padding=self.padding2)
        self.bns2 = nn.BatchNorm1d(out_channel//2)
        self.convs3 = nn.Conv1d(out_channel//2, out_channel//2, self.kernel_size2, stride=2, padding=self.padding2)
        self.bns3 = nn.BatchNorm1d(out_channel//2)
        # fwB0 related
        self.lstm01 = nn.GRU(out_channel//4, out_channel//2, 1, batch_first=False, bidirectional=True)
        self.lstm02 = nn.GRU(out_channel, out_channel//2, 1, batch_first=False, bidirectional=True)
        self.lstm03 = nn.GRU(out_channel, out_channel//2, 1, batch_first=False, bidirectional=True)
        self.lstm04 = nn.GRU(out_channel, out_channel//2, 1, batch_first=False, bidirectional=True)
        self.lstm05 = nn.GRU(out_channel, out_channel//2, 1, batch_first=False, bidirectional=True)
        # fwB1 related
        self.lstm11 = nn.GRU(out_channel//2, out_channel//2, 1, batch_first=False, bidirectional=True)
        self.lstm12 = nn.GRU(out_channel, out_channel//2, 1, batch_first=False, bidirectional=True)
        self.lstm13 = nn.GRU(out_channel, out_channel//2, 1, batch_first=False, bidirectional=True)
        self.lstm14 = nn.GRU(out_channel, out_channel//2, 1, batch_first=False, bidirectional=True)
        self.lstm15 = nn.GRU(out_channel, out_channel//2, 1, batch_first=False, bidirectional=True)
        # fwB2 related
        self.lstm21 = nn.GRU(out_channel//2, out_channel//2, 1, batch_first=False, bidirectional=True)
        self.lstm22 = nn.GRU(out_channel, out_channel//2, 1, batch_first=False, bidirectional=True)
        self.lstm23 = nn.GRU(out_channel, out_channel//2, 1, batch_first=False, bidirectional=True)
        self.lstm24 = nn.GRU(out_channel, out_channel//2, 1, batch_first=False, bidirectional=True)
        self.lstm25 = nn.GRU(out_channel, out_channel//2, 1, batch_first=False, bidirectional=True)
        ###
        self.fusion   = nn.Conv1d(out_channel*2, out_channel, kernel_size=1, stride=1, bias=False)
        self.layer_norm = nn.LayerNorm(out_channel, eps=1e-6)

    def fwB0(self, x):
        x = x.permute(2, 0, 1)
        self.lstm01.flatten_parameters()
        x, _ = self.lstm01(x)
        self.lstm02.flatten_parameters()
        x, _ = self.lstm02(x)
        self.lstm03.flatten_parameters()
        x, _ = self.lstm03(x)
        self.lstm04.flatten_parameters()
        x, _ = self.lstm04(x)
        self.lstm05.flatten_parameters()
        x, _ = self.lstm05(x)
        x = x.permute(1, 2, 0)
        return x

    def fwB1(self, x):
        x = x.permute(2, 0, 1)
        self.lstm11.flatten_parameters()
        x, _ = self.lstm11(x)
        self.lstm12.flatten_parameters()
        x, _ = self.lstm12(x)
        self.lstm13.flatten_parameters()
        x, _ = self.lstm13(x)
        self.lstm14.flatten_parameters()
        x, _ = self.lstm14(x)
        self.lstm15.flatten_parameters()
        x, _ = self.lstm15(x)
        x = x.permute(1, 2, 0)
        return x

    def fwB2(self, x):
        x = x.permute(2, 0, 1)
        self.lstm21.flatten_parameters()
        x, _ = self.lstm21(x)
        self.lstm22.flatten_parameters()
        x, _ = self.lstm22(x)
        self.lstm23.flatten_parameters()
        x, _ = self.lstm23(x)
        self.lstm24.flatten_parameters()
        x, _ = self.lstm24(x)
        self.lstm25.flatten_parameters()
        x, _ = self.lstm25(x)
        x = x.permute(1, 2, 0)
        return x

    def forward(self, x):
        # x = (bs, 2048, 1)
        #x = x.transpose(2, 1)  # (bs, 1, 2048)
        x = self.convs1(x)     # (bs, 64, 1024)
        x = self.bns1(x)
        x0 = self.relu0(x)
        #
        x = self.convs2(x0)     # (bs, 128, 512)
        x = self.bns2(x)
        x1 = self.relu0(x)
        #
        x = self.convs3(x1)     # (bs, 128, 256)
        x = self.bns3(x)
        x2 = self.relu0(x)
        ###############
        x0 = self.fwB0(x0)
        x0 = self.downsample(x0)
        x1 = self.fwB1(x1)
        x2 = self.fwB2(x2)
        x2 = self.upsample(x2)
        x = self.fusion(torch.cat([x1, x2], 1))
        # x should be (bs, 256, 512)
        #####################
        x = x.transpose(2, 1)  # (bs, 512, 256)
        x = self.layer_norm(x)
        x = x.transpose(2, 1)
        
        return x


    
class BiGRU(nn.Module):
    def __init__(self, nIn, nHidden, nOut, num_layers=3):
        super(BiGRU, self).__init__()
        self.gru = nn.GRU(nIn, nHidden, num_layers=num_layers, batch_first=True, bidirectional=True)
        self.embedding = nn.Linear(nHidden*2, nOut)

    def forward(self, input):
        if not hasattr(self, '_flattened'):
            self.gru.flatten_parameters()
            setattr(self, '_flattened', True)
            
        x = input.permute(0, 2, 1)
        rnnOut, _ = self.gru(x)
        N, T, C = rnnOut.size()
        output = self.embedding(rnnOut)
        output = output.permute(0, 2, 1)
        return output
    
    
def layer_norm_backward_hook(module, grad_input, grad_output, clamp_value):
    return tuple(torch.clamp(v, min=-clamp_value, max=clamp_value) for v in grad_input)

class Fp32LayerNorm(nn.Module):
    def __init__(
        self,
        input_dim,
        clamp_grad=True,
        max_grad_value=256,
        eps=1e-5,
        elementwise_affine=True,
    ):
        super().__init__()
        self.torch_module = torch.nn.LayerNorm(
            input_dim, eps=eps, elementwise_affine=elementwise_affine
        )
        if clamp_grad:
            hook = partial(layer_norm_backward_hook, clamp_value=max_grad_value)
            self.torch_module.register_backward_hook(hook)

    def forward(self, input):
        output = torch.nn.functional.layer_norm(
            input.float(),
            self.torch_module.normalized_shape,
            self.torch_module.weight.float()
            if self.torch_module.weight is not None
            else None,
            self.torch_module.bias.float()
            if self.torch_module.bias is not None
            else None,
            self.torch_module.eps,
        ).type_as(input)
        return output