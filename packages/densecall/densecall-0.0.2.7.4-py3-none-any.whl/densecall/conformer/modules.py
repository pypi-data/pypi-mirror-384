import math
import numpy as np 
from functools import partial
from functools import lru_cache
import torch
import torch.nn as nn

from torch import Tensor
from .conv import *
from .flash import *

layers = {}

def register(layer):
    layer.name = layer.__name__.lower()
    layers[layer.name] = layer
    return layer


def activation_fn(activation):
    activation_dict = {
        "relu": nn.ReLU,
        "gelu": nn.GELU,
        "glu": nn.GLU,
        "tanh": nn.Tanh,
        "sigmoid": nn.Sigmoid,
        "silu": nn.SiLU,
        "swish": nn.SiLU
    }
    if activation in activation_dict:
        return activation_dict[activation]
    else:
        raise ValueError("Unknown activation function {} specified".format(activation))
    
def norm_fn(norm):
    
    if norm == 'layer':
        return nn.LayerNorm
    
    elif norm == 'batch':
        return BatchNorm
    elif norm == 'norm':
        return Norm
    else:
        raise ValueError("Unknown norm function {} specified".format(norm))
    
@lru_cache(maxsize=2)
def sliding_window_mask(seq_len, window, device):
    band = torch.full((seq_len, seq_len), fill_value=1.0)
    band = torch.triu(band, diagonal=-window[0])
    band = band * torch.tril(band, diagonal=window[1])
    band = band.to(torch.bool).to(device)
    return band
    
    
class SubPixelUpsample(nn.Module):
    def __init__(self, in_ch, r=2):
        super().__init__()
        self.conv = nn.Conv1d(in_ch, in_ch*r, 3, padding=1)
        self.r = r
    def forward(self, x):
        B, C, T = x.shape
        x = self.conv(x)                 # (B, C*r, T)
        x = x.view(B, C, self.r, T).permute(0,1,3,2)  # (B,C,T,r)
        return x.reshape(B, C, T*self.r) 
    
class LinearUpsample(nn.Module):
    """
    Applies a linear transformation to upsample the sequence length by ``scale_factor``.
    """

    def __init__(self, d_model, scale_factor, batch_first=True):
        super().__init__()
        self.d_model = d_model
        self.scale_factor = scale_factor
        self.batch_first = batch_first
        self.linear = nn.Linear(d_model, self.scale_factor * d_model)

    def forward(self, src):
        if not self.batch_first:
            src = src.permute([1, 0, 2])
        N, L, E = src.shape
        
        h = self.linear(src)
        h = h.reshape(N, self.scale_factor * L, E)
        if not self.batch_first:
            h = h.permute([1, 0, 2])
        return h

    def output_stride(self, input_stride):
        return input_stride // self.scale_factor

    def to_dict(self, include_weights=False):
        if include_weights:
            raise NotImplementedError
        return {
            "d_model": self.d_model,
            "scale_factor": self.scale_factor,
            "batch_first": self.batch_first
        }
    

class RelPositionalEncoding(nn.Module):
    """
    Relative positional encoding module.
    Args:
        d_model: Embedding dimension.
        max_len: Maximum input length.
    """

    def __init__(self, d_model: int = 512, max_len: int = 5000) -> None:
        super(RelPositionalEncoding, self).__init__()
        self.d_model = d_model
        self.pe = None
        self.extend_pe(torch.tensor(0.0).expand(1, max_len))

    def extend_pe(self, x):
        if self.pe is not None:
            if self.pe.size(1) >= x.size(1) * 2 - 1:
                if self.pe.dtype != x.dtype or self.pe.device != x.device:
                    self.pe = self.pe.to(dtype=x.dtype, device=x.device)
                return

        pe_positive = torch.zeros(x.size(1), self.d_model)
        pe_negative = torch.zeros(x.size(1), self.d_model)
        position = torch.arange(0, x.size(1), dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, self.d_model, 2, dtype=torch.float32) * -(math.log(10000.0) / self.d_model)
        )
        pe_positive[:, 0::2] = torch.sin(position * div_term)
        pe_positive[:, 1::2] = torch.cos(position * div_term)
        pe_negative[:, 0::2] = torch.sin(-1 * position * div_term)
        pe_negative[:, 1::2] = torch.cos(-1 * position * div_term)

        pe_positive = torch.flip(pe_positive, [0]).unsqueeze(0)
        pe_negative = pe_negative[1:].unsqueeze(0)
        pe = torch.cat([pe_positive, pe_negative], dim=1)
        self.pe = pe.to(device=x.device, dtype=x.dtype)

    def forward(self, x: torch.Tensor):
        """
        Args:
            x : Input tensor B X T X C
        Returns:
            torch.Tensor: Encoded tensor B X T X C
        """
        self.extend_pe(x)
        pos_emb = self.pe[
            :,
            self.pe.size(1) // 2 - x.size(1) + 1 : self.pe.size(1) // 2 + x.size(1),
        ]
        return pos_emb


class ResidualConnectionModule(nn.Module):
    """
    Residual Connection Module.
    outputs = (module(inputs) x module_factor + inputs x input_factor)
    """

    def __init__(self, module: nn.Module, module_factor: float = 1.0) -> None:
        super(ResidualConnectionModule, self).__init__()
        self.module = module
        self.module_factor = module_factor

    def forward(self, inputs: Tensor) -> Tensor:
        return (self.module(inputs) * self.module_factor) + inputs


class Transpose(nn.Module):
    """Wrapper class of torch.transpose() for Sequential module."""

    def __init__(self, shape: tuple) -> None:
        super(Transpose, self).__init__()
        self.shape = shape

    def forward(self, x: Tensor) -> Tensor:
        return x.transpose(*self.shape)


def recover_resolution(inputs: Tensor) -> Tensor:
    outputs = list()

    for idx in range(inputs.size(1) * 2):
        outputs.append(inputs[:, idx // 2, :])
    return torch.stack(outputs, dim=1)


class TimeReductionLayer(nn.Module):
    def __init__(
        self,
        in_channels: int = 1,
        out_channels: int = 1,
        kernel_size: int = 3,
        stride: int = 2,
        activation=nn.GELU
    ) -> None:
        super(TimeReductionLayer, self).__init__()
        self.activation = activation
        self.sequential = nn.Sequential(
            DepthwiseConv2d(
                in_channels=in_channels,
                out_channels=out_channels,
                kernel_size=kernel_size,
                stride=stride,
            ),
            self.activation(),
        )
        
    def forward(self, inputs: Tensor):
        outputs = self.sequential(inputs.unsqueeze(1))
        batch_size, channels, subsampled_lengths, subsampled_dim = outputs.size()

        outputs = outputs.permute(0, 2, 1, 3)
        outputs = outputs.contiguous().view(batch_size, subsampled_lengths, channels * subsampled_dim)

        return outputs
    
class PositionalEncodingTrain(nn.Module):
    def __init__(self, d_model: int, max_len: int = 5000):
        super(PositionalEncodingTrain, self).__init__()
        pe = torch.nn.Parameter(torch.empty(1, max_len, d_model))
        self.register_buffer('pe', pe)

    def forward(self, length) -> torch.Tensor:
        pe = self.pe[:, :length]
        return pe

class PositionalEncoding(nn.Module):
    """
    Positional Encoding proposed in "Attention Is All You Need".
    Since transformer contains no recurrence and no convolution, in order for the model to make
    use of the order of the sequence, we must add some positional information.

    "Attention Is All You Need" use sine and cosine functions of different frequencies:
        PE_(pos, 2i)    =  sin(pos / power(10000, 2i / d_model))
        PE_(pos, 2i+1)  =  cos(pos / power(10000, 2i / d_model))
    """
    def __init__(self, d_model: int = 512, max_len: int = 5000) -> None:
        super(PositionalEncoding, self).__init__()
        pe = torch.zeros(max_len, d_model, requires_grad=False)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * -(math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x) -> Tensor:
        return self.pe[:, :x.size(1)]
    
    
class Wav2Vec2PositionalConvEmbedding(nn.Module):
    def __init__(self, hidden_size, num_conv_pos_embeddings=128, groups=16, activation=nn.GELU):
        super().__init__()
        
        self.activation = activation()
        
        self.conv = nn.Conv1d(
            hidden_size,
            hidden_size,
            kernel_size=num_conv_pos_embeddings,
            padding=num_conv_pos_embeddings // 2,
            groups=groups,
        )

        weight_norm = nn.utils.weight_norm
        if hasattr(nn.utils.parametrizations, "weight_norm"):
            weight_norm = nn.utils.parametrizations.weight_norm


        self.conv = weight_norm(self.conv, name="weight", dim=2)

        self.padding = Wav2Vec2SamePadLayer(num_conv_pos_embeddings)


    def forward(self, hidden_states):
        hidden_states = hidden_states.transpose(1, 2)

        hidden_states = self.conv(hidden_states)
        hidden_states = self.padding(hidden_states)
        hidden_states = self.activation(hidden_states)

        hidden_states = hidden_states.transpose(1, 2)
        return hidden_states


class Wav2Vec2SamePadLayer(nn.Module):
    def __init__(self, num_conv_pos_embeddings):
        super().__init__()
        self.num_pad_remove = 1 if num_conv_pos_embeddings % 2 == 0 else 0

    def forward(self, hidden_states):
        if self.num_pad_remove > 0:
            hidden_states = hidden_states[:, :, : -self.num_pad_remove]
        return hidden_states
    
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
    
class Fp32GroupNorm(nn.GroupNorm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def forward(self, input):
        output = F.group_norm(
            input.float(),
            self.num_groups,
            self.weight.float() if self.weight is not None else None,
            self.bias.float() if self.bias is not None else None,
            self.eps,
        )
        return output.type_as(input)
  

class CTC(torch.nn.Module):
    """CTC module

    :param int odim: dimension of outputs
    :param int eprojs: number of encoder projection units
    :param float dropout_rate: dropout rate (0.0 ~ 1.0)
    :param str ctc_type: builtin or warpctc
    :param bool reduce: reduce the CTC loss into a scalar
    """

    def __init__(self, odim, eprojs, dropout_rate, ctc_type='builtin', reduce=True):
        super(CTC, self).__init__()
        self.dropout_rate = dropout_rate
        self.loss = None
        self.ctc_lo = torch.nn.Linear(eprojs, odim)
        self.ctc_type = ctc_type

        if self.ctc_type == 'builtin':
            reduction_type = 'sum' if reduce else 'none'
            self.ctc_loss = torch.nn.CTCLoss(reduction=reduction_type)
        elif self.ctc_type == 'warpctc':
            import warpctc_pytorch as warp_ctc
            self.ctc_loss = warp_ctc.CTCLoss(size_average=True)
        else:
            raise ValueError('ctc_type must be "builtin" or "warpctc": {}'
                             .format(self.ctc_type))

        self.ignore_id = -1
        self.reduce = reduce

    def loss_fn(self, th_pred, th_target, th_ilen, th_olen):
        if self.ctc_type == 'builtin':
            th_pred = th_pred.log_softmax(2)
            loss = self.ctc_loss(th_pred, th_target, th_ilen, th_olen)
            # Batch-size average
            loss = loss / th_pred.size(1)
            return loss
        elif self.ctc_type == 'warpctc':
            return self.ctc_loss(th_pred, th_target, th_ilen, th_olen)
        else:
            raise NotImplementedError

    def forward(self, hs_pad, hlens, ys_pad):
        """CTC forward

        :param torch.Tensor hs_pad: batch of padded hidden state sequences (B, Tmax, D)
        :param torch.Tensor hlens: batch of lengths of hidden state sequences (B)
        :param torch.Tensor ys_pad: batch of padded character id sequence tensor (B, Lmax)
        :return: ctc loss value
        :rtype: torch.Tensor
        """
        # TODO(kan-bayashi): need to make more smart way
        ys = [y[y != self.ignore_id] for y in ys_pad]  # parse padded ys

        self.loss = None
        hlens = torch.from_numpy(np.fromiter(hlens, dtype=np.int32))
        olens = torch.from_numpy(np.fromiter(
            (x.size(0) for x in ys), dtype=np.int32))

        # zero padding for hs
        ys_hat = self.ctc_lo(F.dropout(hs_pad, p=self.dropout_rate))

        # zero padding for ys
        ys_true = torch.cat(ys).cpu().int()  # batch x olen


        # get ctc loss
        # expected shape of seqLength x batchSize x alphabet_size
        ys_hat = ys_hat.transpose(0, 1)
        self.loss = self.loss_fn(ys_hat, ys_true, hlens, olens)

        return self.loss

    def log_softmax(self, hs_pad):
        """log_softmax of frame activations

        :param torch.Tensor hs_pad: 3d tensor (B, Tmax, eprojs)
        :return: log softmax applied 3d tensor (B, Tmax, odim)
        :rtype: torch.Tensor
        """
        return F.log_softmax(self.ctc_lo(hs_pad), dim=2)

    def argmax(self, hs_pad):
        """argmax of frame activations

        :param torch.Tensor hs_pad: 3d tensor (B, Tmax, eprojs)
        :return: argmax applied 2d tensor (B, Tmax)
        :rtype: torch.Tensor
        """
        return torch.argmax(self.ctc_lo(hs_pad), dim=2)
    
class CELabelSmoothingLoss(nn.Module):
    """Label-smoothing loss

    :param int size: the number of class
    :param int padding_idx: ignored class id
    :param float smoothing: smoothing rate (0.0 means the conventional CE)
    :param bool normalize_length: normalize loss by sequence length if True
    :param torch.nn.Module criterion: loss function to be smoothed
    """

    def __init__(self, size, padding_idx, smoothing, normalize_length=False, criterion=nn.KLDivLoss(reduce=False)):
        super(CELabelSmoothingLoss, self).__init__()
        self.criterion = criterion
        self.padding_idx = padding_idx
        self.confidence = 1.0 - smoothing
        self.smoothing = smoothing
        self.size = size
        self.true_dist = None
        self.normalize_length = normalize_length

    def forward(self, x, target):
        """Compute loss between x and target

        :param torch.Tensor x: prediction (batch, seqlen, class)
        :param torch.Tensor target: target signal masked with self.padding_id (batch, seqlen)
        :return: scalar float value
        :rtype torch.Tensor
        """
        assert x.size(2) == self.size
        batch_size = x.size(0)
        x = x.view(-1, self.size)
        target = target.view(-1)
        with torch.no_grad():
            true_dist = x.clone()
            true_dist.fill_(self.smoothing / (self.size - 1))
            ignore = target == self.padding_idx  # (B,)
            total = len(target) - ignore.sum().item()
            target = target.masked_fill(ignore, 0)  # avoid -1 index
            true_dist.scatter_(1, target.unsqueeze(1), self.confidence)
        kl = self.criterion(torch.log_softmax(x, dim=1), true_dist)
        denom = total if self.normalize_length else batch_size
        return kl.masked_fill(ignore.unsqueeze(1), 0).sum() / denom  
    

class Decoder(nn.Module):
    def __init__(self, alphabet, embed_size, n_heads, num_layers=1, dropout=0.1):
        super(Decoder, self).__init__(ignore_id=-1, eos=4, sos=4)
        self.embed_size = embed_size
        self.alphabet = alphabet
        self.n_heads = n_heads
        self.dropout = dropout
        self.num_layers = num_layers
        self.embedding = nn.Embedding(len(alphabet), embed_size)
        self.positional_encoding = PositionalEncoding(embed_size)
        self.sqrt_dim = np.sqrt(embed_size)
        self.input_dropout = nn.Dropout(dropout)
        self.layer_norm = Fp32LayerNorm(embed_size)
        self.criterion = CELabelSmoothingLoss(len(alphabet), padding_idx=-1, smoothing=0.1)
        
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=embed_size,
            nhead=n_heads,
            dim_feedforward=512,
            dropout=0.1,
            batch_first=True,
            norm_first=True,
        )
        self.decoder = nn.TransformerDecoder(decoder_layer, num_layers = self.num_layers)
        self.fc = nn.Linear(self.embed_size, len(self.alphabet))
        


    def forward(self, targets, target_lengths, encoder_outputs):
        
        targets = targets - 1
        ys_in_pad, ys_out_pad = self.add_sos_eos(targets)
        
        batch_size, tgt_seq_len = ys_in_pad.size(0), ys_in_pad.size(1)
        tgt_mask = torch.triu(torch.ones(tgt_seq_len, tgt_seq_len, device=targets.device), diagonal=1).bool()
    
        #tgt_mask = self.target_mask(ys_in_pad).squeeze(0).bool()
        
        positional_encoding_length = ys_in_pad.size(1)
  
        x = self.positional_encoding(positional_encoding_length) + self.embedding(ys_in_pad)*self.sqrt_dim
        x = self.input_dropout(x)
        #print(tgt_mask.shape, outputs.shape, encoder_outputs.shape)
        x = self.decoder(
            tgt=x,
            memory=encoder_outputs,
            tgt_mask=tgt_mask,
        )
        x = self.layer_norm(x)
        x = self.fc(x)
        loss = self.criterion(x, ys_out_pad)
        return loss
    
    def recognize(self, tgt, tgt_mask, memory):
        """recognize one step

        :param torch.Tensor tgt: input token ids, int64 (batch, maxlen_out)
        :param torch.Tensor tgt_mask: input token mask, uint8  (batch, maxlen_out)
        :param torch.Tensor memory: encoded memory, float32  (batch, maxlen_in, feat)
        :return x: decoded token score before softmax (batch, maxlen_out, token)
        :rtype: torch.Tensor
        """
        #print(tgt_mask.shape, tgt_mask.shape, memory.shape)
        batch_size, tgt_seq_len = tgt.size(0), tgt.size(1)
        tgt_mask = torch.triu(torch.ones(tgt_seq_len, tgt_seq_len, device=tgt.device), diagonal=1).bool()
        positional_encoding_length = tgt.size(1)
        x = self.positional_encoding(positional_encoding_length) + self.embedding(tgt)*self.sqrt_dim
        
        x = self.decoder(
            tgt=x,
            memory=memory,
            tgt_mask=tgt_mask,
        )

        x_ = self.layer_norm(x[:, -1])
        return torch.log_softmax(self.fc(x_), dim=-1)
 
    

class Permute(nn.Module):

    def __init__(self, dims):
        super().__init__()
        self.dims = dims

    def forward(self, x):
        #print(x.shape)
        return x.permute(*self.dims)

    def to_dict(self, include_weights=False):
        return {'dims': self.dims}

    def extra_repr(self):
        return 'dims={}'.format(self.dims)
    
    
class BatchNorm(nn.Module):
    "shape is NTC"
    def __init__(self, channels):
        super().__init__()
        self.bn = nn.BatchNorm1d(channels)
    
    def forward(self, x):
        x = x.transpose(1, 2)
        x = self.bn(x)
        x = x.transpose(1, 2)
        return x


class Norm(nn.Module):

    def __init__(self, channels):
        super().__init__()
        self.alpha = nn.Parameter(torch.ones(channels))
        self.beta = nn.Parameter(torch.zeros(channels))
    
    def forward(self, x):
        return x*self.alpha + self.beta