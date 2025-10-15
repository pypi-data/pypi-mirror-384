import numpy as np
import torch
from torch.nn.utils.rnn import pad_sequence
from torch import nn
import torch.nn.functional as F
from torch import Tensor
from fast_ctc_decode import beam_search, viterbi_search
from .criterion import *
from .nn import *
from densecall.util import phred
from .wav2vec2 import Wav2Vec2Model as KQWav2Vec2Model
from .beam_search import beam_search as lm_beam_search
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


class Transducer(nn.Module):
    import fast_rnnt

    def __init__(self, joiner):
        super().__init__()
        self.joiner = joiner
        
    def forward(self, am, lm, targets, y_lens):
        N, T, C = am.shape
        #am = am.transpose(0, 1)
        x_lens = torch.full(size=(N, ), fill_value=T, dtype=torch.int64, device=am.device)
        boundary = torch.zeros((N, 4), dtype=torch.int64, device=targets.device)
        boundary[:, 2] = y_lens
        boundary[:, 3] = x_lens

        simple_loss, (px_grad, py_grad) = self.fast_rnnt.rnnt_loss_smoothed(
            lm=lm,
            am=am,
            symbols=targets,
            termination_symbol=0,
            lm_only_scale=0.25,
            am_only_scale=0,
            boundary=boundary,
            reduction='mean',
            return_grad=True,
        )

        prune_range = 19
        ranges = self.fast_rnnt.get_rnnt_prune_ranges(
            px_grad=px_grad,
            py_grad=py_grad,
            boundary=boundary,
            s_range=prune_range,
        )

        am_pruned, lm_pruned = self.fast_rnnt.do_rnnt_pruning(
            am=am, lm=lm, ranges=ranges
        )

        logits = self.joiner(am_pruned, lm_pruned)

        #with torch.cuda.amp.autocast(enabled=False):
        pruned_loss = self.fast_rnnt.rnnt_loss_pruned(
            logits=logits.float(),
            symbols=targets,
            ranges=ranges,
            termination_symbol=0,
            boundary=boundary,
            reduction='mean',
        )
        
        return 0.1 * simple_loss + pruned_loss

class Joiner(nn.Module):
    def __init__(self, input_dim: int, inner_dim: int, output_dim: int):
        super().__init__()
        self.inner_linear = nn.Linear(input_dim, inner_dim)
        self.output_linear = nn.Linear(inner_dim, output_dim)

    def forward(self, encoder_out: torch.Tensor, decoder_out: torch.Tensor) -> torch.Tensor:
        assert encoder_out.ndim == decoder_out.ndim
        #assert encoder_out.ndim in (2, 4)
        assert encoder_out.shape == decoder_out.shape
        
        logit = encoder_out + decoder_out
        #print(logit.shape)
        logit = self.inner_linear(torch.tanh(logit))
        output = self.output_linear(F.relu(logit))
        return output

class Decoder(nn.Module):
    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int,
        blank_id: int,
        unk_id: int,
        context_size: int,
    ):
        super().__init__()
        self.embedding = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embedding_dim,
        )
        self.blank_id = blank_id
        self.unk_id = unk_id
        self.context_size = context_size
        self.vocab_size = vocab_size
        
        if context_size > 1:
            self.conv = nn.Conv1d(
                in_channels=embedding_dim,
                out_channels=embedding_dim,
                kernel_size=context_size,
                padding=0,
                groups=embedding_dim,
                bias=False,
            )
        else:
            self.conv = nn.Identity()
        self.output_linear = nn.Linear(embedding_dim, vocab_size)

    def forward(self, y: torch.Tensor, need_pad: bool = True) -> torch.Tensor:
        embedding_out = self.embedding(y.clamp(min=0)) * (y >= 0).unsqueeze(-1)
        if self.context_size > 1:
            embedding_out = embedding_out.permute(0, 2, 1)
            if need_pad is True:
                embedding_out = F.pad(embedding_out, pad=(self.context_size - 1, 0))
            else:
                assert embedding_out.size(-1) == self.context_size
            embedding_out = self.conv(embedding_out)
            embedding_out = embedding_out.permute(0, 2, 1)
        embedding_out = self.output_linear(F.relu(embedding_out))
        return embedding_out
    

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
        self.norm = config['general']['norm']
        
        self.qbias = config['qscore']['bias']
        self.qscale = config['qscore']['scale']
        
        self.feature_extractor = FeatureExtraction(self.conv_dim, self.conv_kernel, self.conv_stride, activation=self.activation)
        self.feature_projection = FeatureProjection(self.conv_dim[-1], self.embed_size, norm=self.norm)
        self.encoder = Encoder(config)
        
        vocab_size = len(self.alphabet)
        self.context_size = 19
        self.blank_id = 0
        
        self.decoder = Decoder(
            vocab_size=vocab_size,
            embedding_dim=self.embed_size,
            blank_id=self.blank_id,
            unk_id=0,
            context_size=self.context_size
        )
        
        self.joiner = Joiner(
            input_dim=vocab_size,
            inner_dim=self.embed_size,
            output_dim=vocab_size
        )
        
        self.transducer = Transducer(self.joiner)
        
    def forward(self, x):
        x = self.feature_extractor(x).transpose(1, 2)
        x, _ = self.feature_projection(x)
        encoder_out = self.encoder(x)
        return encoder_out
    
    def loss(self, encoder_out, data_lengths_, targets, lengths):
        encoder_out, *_ = encoder_out
        T, N, C = encoder_out.shape
        encoder_out = encoder_out.transpose(0, 1)
        
        targets_padded = torch.nn.functional.pad(targets, (1, 0), value=self.blank_id)
        
        decoder_out = self.decoder(targets_padded, need_pad=True)
        
        loss = self.transducer(
            am=encoder_out,
            lm=decoder_out,
            targets=targets,
            y_lens=lengths
        )
        
        return {"total_loss": loss, "loss": loss}

        
    
    def decode_batch(self, encoder_out, beamsize=5):
        encoder_out = encoder_out.transpose(0, 1)
        B, T, C = encoder_out.shape
        
        sequences = torch.full((B, T), self.blank_id, dtype=torch.long, device=encoder_out.device)
        context = torch.zeros(B, self.context_size, dtype=torch.long, device=encoder_out.device)
        
        for t in range(T):
            hidden = encoder_out[:, t:t+1, :]
            
            decoder_out = self.decoder(context, need_pad=False)
            decoder_out = decoder_out[:, -1:, :]
            
            logits = self.joiner(hidden, decoder_out)
            token_ids = torch.argmax(logits, dim=-1).squeeze(1)
            
            mask = token_ids != self.blank_id
            sequences[mask, t] = token_ids[mask]
            
            context = torch.cat([context[:, 1:], token_ids.unsqueeze(1)], dim=1)
        
        results = []
        for b in range(B):
            seq = sequences[b][sequences[b] != self.blank_id]
            results.append(''.join([self.alphabet[i] for i in seq.cpu().numpy()]))
        
        return results