import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from torch import Tensor
import torch.nn.init as init
import math
from functools import partial

from .linformer import LinformerSelfAttention
from .cgmlp import MultiConvolutionalGatingMLP
from .flash import *
from .conv import *
from .modules import *

class FeatureExtraction(nn.Module):
    def __init__(self, out_channels=[512, 512, 512, 512, 512, 512, 512], kernel_sizes=(10, 3, 3, 3, 3, 3, 3), strides=(1, 1, 1, 1, 1, 2, 2), activation=nn.GELU):
        super(FeatureExtraction, self).__init__()
        self.activation = activation
        self.out_channels = out_channels
        self.kernel_sizes = kernel_sizes
        self.strides = strides

        assert len(out_channels) == len(kernel_sizes) == len(strides), "out_channels, kernel_sizes, and strides must have the same length"

        self.conv_layers = nn.ModuleList()
        in_channels = 1
        # DepthwiseSeparableConv(in_channels, out_channels[i], norm=True, kernel_size=kernel_sizes[i], stride=strides[i], padding=(kernel_sizes[i]-1)//2, bias=False),

        for i in range(len(out_channels)):
            if i == 0:
                # 第一层添加 GroupNorm
                layer = nn.Sequential(
                    nn.Conv1d(in_channels, out_channels[i], kernel_size=kernel_sizes[i], stride=strides[i], padding=(kernel_sizes[i]-1)//2, bias=False),
                    nn.Dropout(p=0.0, inplace=False),
                    nn.GroupNorm(out_channels[i], out_channels[i], eps=1e-05, affine=True),
                    self.activation()
                )
            else:
                layer = nn.Sequential(
                    nn.Conv1d(in_channels, out_channels[i], kernel_size=kernel_sizes[i], stride=strides[i], padding=(kernel_sizes[i]-1)//2, bias=False),
                    nn.Dropout(p=0.0, inplace=False),
                    self.activation()
                )
            self.conv_layers.append(layer)
            in_channels = out_channels[i]

        self._requires_grad = True

    def forward(self, x):
        if self._requires_grad and self.training:
            x.requires_grad = True
            
        for layer in self.conv_layers:
            x = layer(x)
        return x
    
    def _freeze_parameters(self):
        for param in self.parameters():
            param.requires_grad = False
        self._requires_grad = False

    
class FeatureProjection(nn.Module):
    def __init__(self, conv_dim, hidden_size, norm='layer'):
        super().__init__()
        self.conv_dim = conv_dim
        self.hidden_size = hidden_size
        self.layer_norm = norm_fn(norm)(conv_dim)
        if self.conv_dim != hidden_size:
            self.projection = nn.Linear(self.conv_dim, self.hidden_size)
        self.dropout = nn.Dropout(0)

    def forward(self, hidden_states):
        # non-projected hidden states are needed for quantization
        norm_hidden_states = self.layer_norm(hidden_states)
        
        if self.conv_dim != self.hidden_size:
            hidden_states = self.projection(norm_hidden_states)
        else:
            hidden_states = hidden_states.clone()
            
        hidden_states = self.dropout(hidden_states)
        return hidden_states, norm_hidden_states

class FeedForward(nn.Module):
    def __init__(self, embed_size, expansion_factor=4, dropout=0.1, activation=nn.GELU):
        super(FeedForward, self).__init__()
        self.fc1 = nn.Linear(embed_size, expansion_factor * embed_size, bias=True)
        self.fc2 = nn.Linear(expansion_factor * embed_size, embed_size, bias=True)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
        self.activation = activation()


    def forward(self, x):
        out = self.dropout1(self.activation(self.fc1(x)))
        out = self.fc2(out)
        out = self.dropout2(out)
        return  out
    

class SDPA(nn.Module):
    def __init__(self, d_model, num_heads, is_causal=False, attn_window=(127, 128)):
        super(SDPA, self).__init__()
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads
        #assert self.head_dim in [64, 128], "head_dim should be 64 or 128"
        self.qkv_proj = nn.Linear(d_model, 3 * d_model)

        self.is_causal = is_causal
        self.attn_window = (-1, -1) if attn_window is None else tuple(attn_window)
        
    def forward(self, x):
        batch_size, seq_len, _ = x.shape
        qkv = self.qkv_proj(x)
        q, k, v = torch.chunk(qkv, 3, dim=-1)
        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)

        mask = sliding_window_mask(qkv.shape[1], self.attn_window, q.device)

        # sageattn F.scaled_dot_product_attention
        attn_output = F.scaled_dot_product_attention(q, k, v, attn_mask=mask, is_causal=self.is_causal)
                
        attn_output = attn_output.transpose(1, 2).contiguous().view(batch_size, seq_len, self.d_model)
        
        return attn_output


class AttentionDecoder(nn.Module):
    def __init__(self, vocab_size, d_model=256, nhead=4, num_layers=2):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, d_model)
        self.pos   = PositionalEncoding(d_model)
        layer = nn.TransformerDecoderLayer(d_model, nhead, dim_feedforward=2048,
                                           batch_first=True)
        self.layers = nn.TransformerDecoder(layer, num_layers)
        self.classifier =nn.Linear(d_model, vocab_size)
        
    def forward(self, ys, h, h_mask):
        # ys:[B,L]  h:[B,T,d]  h_mask:[B,T]
        tgt_mask = nn.Transformer.generate_square_subsequent_mask(ys.size(1)).to(ys.device)
        y = self.embed(ys)
        y = y + self.pos(y)
        z = self.layers(y, h, tgt_mask=tgt_mask,
                        memory_key_padding_mask=h_mask)
        return self.classifier(z)  # [B,L,vocab]
    
class AdaptiveBlock(nn.Module):
    def __init__(self, config, kernel_size=31, beta=0.379917, alpha=1.86120971, block_type='conformer'):
        super(AdaptiveBlock, self).__init__()
        self.config = config
        self.num_blocks = config['encoder']['num_blocks']
        self.embed_size = config['encoder']['embed_size']
        self.expansion_factor = config['encoder']['expansion_factor']
        self.n_heads = config['encoder']['n_heads']
        self.dropout = config['encoder']['dropout']
        self.activation = activation_fn(config['general']['activation'])
        self.norm = config['general']['norm']
        self.attn_type = config['encoder']['attn_type']
        self.kernel_size = kernel_size
        self.block_type = block_type
        self.alpha, self.beta = self._deepnorm_params()
        #print(f"DeepNorm alpha: {self.alpha}, beta: {self.beta}", file=sys.stderr)
        
        self.register_buffer("deepnorm_alpha", torch.tensor(alpha))
        self.register_buffer("deepnorm_beta", torch.tensor(beta))
        
        # 共享组件
        self.norm1 = nn.RMSNorm(self.embed_size)
        self.norm2 = nn.RMSNorm(self.embed_size)
        self.mhsa_module = self._build_attention()
        
        # Conformer特有组件
        if self.block_type == 'conformer':
            self.ffn_module1 = FeedForward(self.embed_size, self.expansion_factor, self.dropout, activation=self.activation)
            self.conv_module = ConformerConv(self.embed_size, kernel_size=self.kernel_size, activation=self.activation)
            self.ffn_module2 = FeedForward(self.embed_size, self.expansion_factor, self.dropout, activation=self.activation)
            self.norm3 = nn.RMSNorm(self.embed_size)
            self.norm4 = nn.RMSNorm(self.embed_size)
            self.feed_forward_residual_factor = self.config['encoder']['feed_forward_residual_factor']
        
        # Transformer特有组件
        elif self.block_type == 'transformer':
            self.ffn_module = FeedForward(self.embed_size, self.expansion_factor, self.dropout, activation=self.activation)
        

        self.pre_norm = self.config['encoder']['pre_norm']

            
        if not self.pre_norm and self.block_type != 'linformer':
            self.reset_parameters()
            
    def _deepnorm_params(self):
        return round((2 * self.num_blocks) ** 0.25, 7), round((8 * self.num_blocks) ** (-1/4), 7)

    def _build_attention(self):
        if self.attn_type == 'rsdpa':
            return RSDPA(self.embed_size, self.n_heads, attn_window=(127, 128))
        elif self.attn_type == 'sdpa':
            return SDPA(self.embed_size, self.n_heads, attn_window=(127, 128))
        elif self.attn_type == 'linformer':
            return LinformerSelfAttention(dim=self.embed_size, k = 128, seq_len=4096, heads=self.n_heads, one_kv_head = True, share_kv = True)
        else:
            return MultiHeadAttention(self.embed_size, self.n_heads, attn_window=(127, 128))

    def forward(self, x, mask=None):
        if self.block_type == 'conformer':
            return self._forward_conformer(x, mask)
        elif self.block_type == 'transformer':
            return self._forward_transformer(x, mask)
        else:
            raise ValueError(f"Unknown block_type: {self.block_type}")

    def _forward_conformer(self, x, mask=None):
        if self.pre_norm:
            x = x + self.mhsa_module(self.norm1(x))
            x = x + self.feed_forward_residual_factor * self.ffn_module1(self.norm2(x))
            x = x + self.conv_module(self.norm3(x))
            x = x + self.feed_forward_residual_factor * self.ffn_module2(self.norm4(x))
        else:
            x = self.norm1(self.deepnorm_alpha*x + self.mhsa_module(x))
            x = self.norm2(self.deepnorm_alpha*x + self.feed_forward_residual_factor * self.ffn_module1(x))
            x = self.norm3(self.deepnorm_alpha*x + self.conv_module(x))
            x = self.norm4(self.deepnorm_alpha*x + self.feed_forward_residual_factor * self.ffn_module2(x))
        return x

    def _forward_transformer(self, x, mask=None):
        if self.pre_norm:
            x = x + self.mhsa_module(self.norm1(x))
            x = x + self.ffn_module(self.norm2(x))
        else:
            x = self.norm1(self.deepnorm_alpha*x + self.mhsa_module(x))
            x = self.norm2(self.deepnorm_alpha*x + self.ffn_module(x))
        return x

    def reset_parameters(self):
        if hasattr(self, 'ffn_module1'):
            for module in [self.ffn_module1, self.ffn_module2]:
                if hasattr(module, 'fc1'):
                    torch.nn.init.xavier_normal_(module.fc1.weight, gain=self.deepnorm_beta)
                if hasattr(module, 'fc2'):
                    torch.nn.init.xavier_normal_(module.fc2.weight, gain=self.deepnorm_beta)
        
        if hasattr(self, 'ffn_module'):
            if hasattr(self.ffn_module, 'fc1'):
                torch.nn.init.xavier_normal_(self.ffn_module.fc1.weight, gain=self.deepnorm_beta)
            if hasattr(self.ffn_module, 'fc2'):
                torch.nn.init.xavier_normal_(self.ffn_module.fc2.weight, gain=self.deepnorm_beta)

        torch.nn.init.xavier_normal_(self.mhsa_module.out_proj.weight, gain=self.deepnorm_beta)
        torch.nn.init.xavier_normal_(self.mhsa_module.Wqkv.weight[:2*self.embed_size], gain=1.0)
        torch.nn.init.xavier_normal_(self.mhsa_module.Wqkv.weight[2*self.embed_size:], gain=self.deepnorm_beta)
    
         
class Encoder(nn.Module):
    def __init__(self, config):
        super(Encoder, self).__init__()
        self.config = config
        self.layer = config['encoder']['layer']
        self.embed_size = config['encoder']['embed_size'] 
        self.n_heads = config['encoder']['n_heads']
        self.conv_embeding = config['encoder']['conv_embeding']
        self.num_blocks = config['encoder']['num_blocks']
        self.alphabet = config['basecaller']['alphabet']
        self.activation = activation_fn(config['general']['activation'])
        self.dropout = config['encoder']['dropout']
        self.vocab_size = len(self.alphabet) 
        self.fast = config['encoder']['fast']
        self.norm = config['general']['norm']
        self.pre_norm = config['encoder']['pre_norm']
        self.inter_ctc_index = config['encoder']['inter_ctc_index']
        self.reduce_layer_index = config['encoder']['reduce_layer_index']
        
        if self.conv_embeding:
            self.embedding = Wav2Vec2PositionalConvEmbedding(self.embed_size, activation=self.activation)
            
        self.layers = nn.ModuleList()
        
        self.block = partial(AdaptiveBlock, config)
        self.block_types = ['transformer' if i % 2 == 0 else 'conformer' for i in range(self.num_blocks)]
        self.block_types = [self.layer] * self.num_blocks  # 全部使用Conformer块
        
        self.scale_factor = int(math.prod(config['feature_extractor']['conv_stride_finetune']) / config['encoder']['stride'])
        if self.scale_factor != 1:
            self.upsample = SubPixelUpsample(self.embed_size, self.scale_factor)
            
            
        if self.fast:
            self.stride = 2
            self.recover_layer_index = self.num_blocks - 1
            self.recover_tensor = None
            self.time_reduction_layer = TimeReductionLayer(activation=self.activation, stride=self.stride)
            self.time_reduction_proj = nn.Linear(self.embed_size // self.stride, self.embed_size)
            self.time_recover_layer = nn.Linear(self.embed_size, self.embed_size)
            self.kernel_size = [31]*self.reduce_layer_index + [9]*(self.num_blocks - self.reduce_layer_index)
            
            
            for idx in range(self.num_blocks):
                block_type = self.block_types[idx]
                if idx < self.reduce_layer_index:
                    self.layers.append(self.block(kernel_size=self.kernel_size[idx], block_type=block_type))
                elif  self.reduce_layer_index <= idx < self.recover_layer_index:
                    self.layers.append(ResidualConnectionModule(self.block(kernel_size=self.kernel_size[idx], block_type=block_type)))
                else:
                    self.layers.append(self.block(kernel_size=self.kernel_size[idx], block_type=block_type))
        
        else:
            for idx in range(self.num_blocks):
                self.layers.append(self.block(kernel_size=31, block_type=self.block_types[idx]))
        
        self.dropout_input = nn.Dropout(self.dropout)        
        #scCTC        
        #self.embed = nn.Parameter(torch.randn(self.vocab_size, self.embed_size))
        #self.gic_layers = [idx for idx in range(self.num_blocks) if not (idx+1) % self.sc_after and (idx+1)<self.num_blocks]


        #self.gic_block = GIC(C_a=self.embed_size, embed=self.embed)
        self.num_ctc = len(self.inter_ctc_index) + 1
        print(self.inter_ctc_index, self.num_ctc, file=sys.stderr)

        
        self.classifier =nn.Linear(self.embed_size, self.vocab_size)
            
        
        self.ln_module = norm_fn(self.norm)(self.embed_size)
            
        
        self.bottleneck = nn.Sequential(nn.Dropout(0.1), nn.Linear(self.vocab_size, self.embed_size))
            

    def forward(self, x):

        if self.conv_embeding:
            position_embeddings = self.embedding(x)
            x = x + position_embeddings
            
        outputs = self.dropout_input(x)
        inter_out = []
        j = 0
        for idx, layer in enumerate(self.layers):
            if self.fast:
                if idx == self.reduce_layer_index:
                    self.recover_tensor = outputs
                    outputs = self.time_reduction_layer(outputs)
                    outputs = self.time_reduction_proj(outputs)

                if idx == self.recover_layer_index:
                    
                    outputs = torch.repeat_interleave(outputs, repeats=self.stride, dim=1)
                    length = outputs.size(1)
                    outputs = self.time_recover_layer(outputs)
                    outputs += self.recover_tensor[:, :length, :]
           
            outputs = layer(outputs)
            # if idx in self.gic_layers:
            #     inter_ln = self.ln_modules[j](outputs)   
            #     logits = self.classifiers[j](inter_ln)
            #     inter_out.append(logits.transpose(0, 1))  #TNC
            #     outputs = self.gic_block(inter_ln, logits)
            #     j += 1
                
            if idx in self.inter_ctc_index and len(self.inter_ctc_index) > 0 :
                if self.pre_norm:
                    inter_ln = self.ln_module(outputs)
                else:
                    inter_ln = outputs
                logits = self.classifier(inter_ln)   
                inter_out.append(logits.transpose(0, 1))  #TNC
                outputs = self.bottleneck(F.softmax(logits, dim=-1)) + inter_ln
                j += 1
            
        if self.scale_factor != 1:
            outputs = self.upsample(outputs.transpose(2,1)).transpose(2,1)

        
        if self.pre_norm or self.scale_factor != 1:
            outputs = self.ln_module(outputs)

        return (inter_out, outputs)  #TNC
     
     

     
class GIC(nn.Module):
    def __init__(self, C_a=256, C_t=256, embed=None):
        super().__init__()
        assert C_a == C_t
        self.embed = embed
        self.W_g = nn.Linear(C_a + C_t, C_a)                 # (256+256)*256

    def forward(self, h, logits):
        # h: (N, T, C_a=256)   logits: (N, T, V=5000)
        prob = F.softmax(logits, dim=-1)                     # (N, T, V)
        z = torch.einsum("ntv,ve->nte", prob, self.embed)  # (N, T, 256)
                                        # (N, T, 256)
        gate = torch.sigmoid(self.W_g(torch.cat([h, z], dim=-1)))
        fused = gate * h + (1 - gate) * z
        return fused


    

    

    

    
