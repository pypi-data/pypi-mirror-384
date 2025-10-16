from torch import nn, Tensor
from typing import Optional, Tuple
import torch
import math
from .nn import *

################
codevector_dim = 256
proj_codevector_dim = 256
mask_time_length = 10
mask_time_prob = 0.65
num_codevectors_per_group = 320
num_codevector_groups = 2
diversity_loss_weight = 0.1
initializer_range = 0.02
num_negatives = 100
contrastive_logits_temperature = 0.1
#############



class Wav2Vec2Model(nn.Module):
    def __init__(self, config):
        super().__init__()
        
        self.conv_dim = config['feature_extractor']['conv_dim']
        self.conv_kernel = config['feature_extractor']['conv_kernel']
        self.conv_stride = config['feature_extractor']['conv_stride_pretrain']
        
        self.n_heads = config['encoder']['n_heads']
        self.num_blocks = config['encoder']['num_blocks']
        self.dropout = config['encoder']['dropout']
        self.embed_size = config['encoder']['embed_size']
        self.expansion_factor = config['encoder']['expansion_factor']

        self.use_quantizer = config['encoder']['use_quantizer']
        self.activation = activation_fn(config['general']['activation'])
        self.fast = config['encoder']['fast']
        self.norm = config['general']['norm']
        self.alphabet = config['basecaller']['alphabet']
        
        self.stride = config['encoder']['stride']
        self.scale_factor = int(math.prod(self.conv_stride) / self.stride)
        
        self.feature_extractor = FeatureExtraction(self.conv_dim, self.conv_kernel, self.conv_stride, activation=self.activation)
        self.feature_projection = FeatureProjection(self.conv_dim[-1], self.embed_size, norm=self.norm)
        
        self.encoder = Encoder(config)
        
        self.masked_spec_embed = nn.Parameter(torch.FloatTensor(self.embed_size).uniform_())
        self.dropout_input = nn.Dropout(0)

        

        ### pretrain###
        if self.use_quantizer:
            self.quantizer = Wav2Vec2GumbelVectorQuantizer(G=2, V=320, cdim=codevector_dim, conv_dim=self.conv_dim[-1])
            self.project_hid = nn.Linear(self.embed_size, proj_codevector_dim) # from c to compare
            self.project_q = nn.Linear(codevector_dim, proj_codevector_dim)#from codebook to compare
        else:
            self.project_hid = nn.Linear(self.embed_size, proj_codevector_dim) # from c to compare
            self.project_q = nn.Linear(self.conv_dim[-1], proj_codevector_dim)
            
        
        self.apply(self._init_weights)

    def calculate_loss(self, x) -> Tensor:
        extract_features = self.feature_extractor(x).transpose(1, 2)
        hidden_states, extract_features = self.feature_projection(extract_features)
        hidden_states, mask_time_indices = self._mask_hidden_states(hidden_states)

        encoder_outputs = self.encoder(hidden_states)
        if type(encoder_outputs) is tuple:
            encoder_outputs = encoder_outputs[-1]

        transformer_features = self.project_hid(encoder_outputs)

        extract_features = self.dropout_input(extract_features)
        
        if self.use_quantizer:
        
            quantized_features, codevector_perplexity = self.quantizer(extract_features, mask_time_indices)
            quantized_features = quantized_features.to(self.project_q.weight.dtype)
            quantized_features = self.project_q(quantized_features)


            negative_quantized_features = self._sample_negatives(
                quantized_features, num_negatives, attention_mask=None
            )

            logits = self.compute_contrastive_logits(
                quantized_features[None, :],
                negative_quantized_features,
                transformer_features,
                contrastive_logits_temperature)

            neg_is_pos = (quantized_features == negative_quantized_features).all(-1)

            if neg_is_pos.any():
                logits[1:][neg_is_pos] = float("-inf") # k,b,l

            logits = logits.transpose(0, 2).reshape(-1, logits.size(0))

            target = ((1 - mask_time_indices.long()) * -100).transpose(0, 1).flatten()
            contrastive_loss = nn.functional.cross_entropy(logits.float(), target, reduction="mean")

            num_codevectors = num_codevectors_per_group * num_codevector_groups
            diversity_loss = ((num_codevectors - codevector_perplexity) / num_codevectors) #* mask_time_indices.sum()

            loss = contrastive_loss + diversity_loss_weight * diversity_loss
        
        else:

            y = self.project_q(extract_features)
            
            negative_features = self._sample_negatives(
                y, num_negatives, attention_mask=None
            )
 
            logits = self.compute_contrastive_logits(
                y[None, :],
                negative_features,
                transformer_features,
                contrastive_logits_temperature
            )

            neg_is_pos = (y == negative_features).all(-1)
 
            if neg_is_pos.any():
                logits[1:][neg_is_pos] = float("-inf")
                
            #print(logits.shape, mask_time_indices.shape)
                
            logits = logits.transpose(0, 2).reshape(-1, logits.size(0))
            target = ((1 - mask_time_indices.long()) * -100).transpose(0, 1).flatten()
            contrastive_loss = nn.functional.cross_entropy(logits.float(), target, reduction="mean")

            loss = contrastive_loss
            codevector_perplexity = diversity_loss = torch.tensor(0.0) 
            


        return loss, contrastive_loss, diversity_loss, codevector_perplexity, mask_time_indices


    def _mask_hidden_states(
        self,
        hidden_states: torch.FloatTensor,
        mask_time_indices: Optional[torch.FloatTensor] = None,
        attention_mask: Optional[torch.LongTensor] = None,
    ):

        

        batch_size, sequence_length, hidden_size = hidden_states.size()

        if mask_time_indices is not None:
            # apply SpecAugment along time axis with given mask_time_indices
            hidden_states[mask_time_indices] = self.masked_spec_embed.to(hidden_states.dtype)
        elif mask_time_prob > 0:
            mask_time_indices = _compute_mask_indices(
                (batch_size, sequence_length),
                mask_prob=mask_time_prob,
                mask_length=mask_time_length,
                device=hidden_states.device,
                attention_mask=attention_mask,
                min_masks=2,
            )
            hidden_states[mask_time_indices] = self.masked_spec_embed.to(hidden_states.dtype)
        

        return hidden_states, mask_time_indices

    def set_gumbel_temperature(self, temperature: int):
        return self.quantizer.set_temperature(temperature)


    @torch.no_grad()        
    def _init_weights(self, module):
        """Initialize the weights"""
        # Wav2Vec2ForPreTraining last 2 linear layers need standard Linear init.
        self.project_hid.reset_parameters()
        self.project_q.reset_parameters()

        
        # gumbel softmax requires special init
        if isinstance(module, Wav2Vec2GumbelVectorQuantizer):
            module.weight_proj.weight.data.normal_(mean=0.0, std=1)
            module.weight_proj.bias.data.zero_()
            nn.init.uniform_(module.codevectors)
        elif isinstance(module, Wav2Vec2PositionalConvEmbedding):
            nn.init.normal_(
                module.conv.weight,
                mean=0,
                std=2 * math.sqrt(1 / (module.conv.kernel_size[0] * module.conv.in_channels)),
            )
            nn.init.constant_(module.conv.bias, 0)
        elif isinstance(module, FeatureProjection):
            if  hasattr(module, "projection"):
                k = math.sqrt(1 / module.projection.in_features)
                nn.init.uniform_(module.projection.weight, a=-k, b=k)
                nn.init.uniform_(module.projection.bias, a=-k, b=k)
        elif isinstance(module, nn.Linear):
            module.weight.data.normal_(mean=0.0, std=initializer_range)

            if module.bias is not None:
                module.bias.data.zero_()
                
        elif isinstance(module, (nn.LayerNorm, nn.GroupNorm)):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)
        elif isinstance(module, nn.Conv1d):
            nn.init.kaiming_normal_(module.weight)

            if module.bias is not None:
                k = math.sqrt(module.groups / (module.in_channels * module.kernel_size[0]))
                nn.init.uniform_(module.bias, a=-k, b=k)

    @staticmethod
    def _sample_negatives(
        features: torch.FloatTensor, num_negatives: int, attention_mask: Optional[torch.LongTensor] = None
    ):
        batch_size, sequence_length, hidden_size = features.shape
        if sequence_length <= 1:
            raise ValueError(
                f"`features should have `sequence_length` > 1, but are of shape (batch_size, sequence_length, hidden_size) = ({batch_size, sequence_length, hidden_size})."
            )

        features = features.view(-1, hidden_size)  # B,l,C => (B*l),C

        with torch.no_grad():

            sampled_negative_indices = []
            for batch_idx in range(batch_size):
                high = attention_mask[batch_idx].sum() - 1 if attention_mask is not None else sequence_length - 1
                sampled_indices_slice = torch.randint(
                    0, high, size=(num_negatives * sequence_length,), device=features.device
                )
                sampled_negative_indices.append(sampled_indices_slice)

            sampled_negative_indices = torch.stack(sampled_negative_indices)



            feature_indices = (
                torch.arange(sequence_length, device=features.device)[:, None]
                .expand(sequence_length, num_negatives)
                .flatten()
            )

            sampled_negative_indices[sampled_negative_indices >= feature_indices] += 1

        for batch_idx in range(1, batch_size):
            sampled_negative_indices[batch_idx] += batch_idx * sequence_length

        sampled_negatives = features[sampled_negative_indices.view(-1)]
        sampled_negatives = sampled_negatives.view(batch_size, sequence_length, num_negatives, hidden_size).permute(
            2, 0, 1, 3
        )

        return sampled_negatives     # K,b,l,256

    @staticmethod
    def compute_contrastive_logits(
            target_features: torch.FloatTensor, # 1,b,l,256
            negative_features: torch.FloatTensor,
            predicted_features: torch.FloatTensor,  # b,l,256
            temperature=1.0,
    ):
        target_features = torch.cat([target_features, negative_features], dim=0)

        logits = torch.cosine_similarity(predicted_features.float(), target_features.float(), dim=-1).type_as(
            target_features
        )

        logits = logits / temperature # 
        return logits

    
        
        
    def freeze_feature_extractor(self):
        self.feature_extractor._freeze_parameters()



class Wav2Vec2GumbelVectorQuantizer(nn.Module):
    

    def __init__(self, G=2, V=320, cdim=256, conv_dim=512):
        super().__init__()
        self.num_groups = G # G
        self.num_vars = V # V
        self.cdim = cdim
        self.conv_dim = conv_dim

        # storage for codebook variables (codewords)
        self.codevectors = nn.Parameter(
            torch.FloatTensor(1, self.num_groups * self.num_vars, self.cdim // self.num_groups) # 1*640*128
        )
        self.weight_proj = nn.Linear(self.conv_dim, self.num_groups * self.num_vars) # 512 to 320*2

        # can be decayed for training
        self.temperature = 2

    def set_temperature(self, temperature: int):
        self.temperature = temperature

    @staticmethod
    def _compute_perplexity(probs, mask=None): # 
        if mask is not None:
            mask_extended = mask.flatten()[:, None, None].expand(probs.shape)
            probs = torch.where(mask_extended, probs, torch.zeros_like(probs)) # if true -> probs, false -> zero
            mean_probs_by_each_component = probs.sum(dim=0) / mask.sum() # mean concerning mask
        else:
            mean_probs_by_each_component = probs.mean(dim=0)

        perplexity = torch.exp(-torch.sum(mean_probs_by_each_component * torch.log(mean_probs_by_each_component + 1e-7), dim=-1)).sum()

        return perplexity # 

    def forward(self, hidden_states, mask_time_indices=None):
        batch_size, sequence_length, hidden_size = hidden_states.shape

        # project to codevector dim
        hidden_states = self.weight_proj(hidden_states) # codebook linear mapping -> B,L,640
        hidden_states = hidden_states.view(batch_size * sequence_length * self.num_groups, -1) # B*L*2,320

        if self.training:
            # sample code vector probs via gumbel in differentiateable way

            # gumbel softmax 
            codevector_probs = nn.functional.gumbel_softmax(
                hidden_states.float(), tau=self.temperature, hard=True
            ).type_as(hidden_states) # 

            # compute perplexity
            codevector_soft_dist = torch.softmax(
                hidden_states.view(batch_size * sequence_length, self.num_groups, -1).float(), dim=-1
            )
            perplexity = self._compute_perplexity(codevector_soft_dist, mask_time_indices)
        else:
            # take argmax in non-differentiable way
            # comptute hard codevector distribution (one hot)
            codevector_idx = hidden_states.argmax(dim=-1)
            codevector_probs = hidden_states.new_zeros(*hidden_states.shape).scatter_(
                -1, codevector_idx.view(-1, 1), 1.0
            )
            codevector_probs = codevector_probs.view(batch_size * sequence_length, self.num_groups, -1)

            perplexity = self._compute_perplexity(codevector_probs, mask_time_indices)

        codevector_probs = codevector_probs.view(batch_size * sequence_length, -1) #B*L,640 

        # use probs to retrieve codevectors
        codevectors_per_group = codevector_probs.unsqueeze(-1) * self.codevectors # (B*L,640,1) * (1,640,128) ->  B*L,640,128
        codevectors = (
            codevectors_per_group.view(batch_size * sequence_length, self.num_groups, self.num_vars, -1) # B*L,2,320,128
            .sum(-2) # B*L,2,128
            .view(batch_size, sequence_length, -1) # B,L,256
        )

        return codevectors, perplexity
    
    
def _compute_mask_indices(
    shape: Tuple[int, int],
    mask_prob: float,
    mask_length: int,
    device: torch.device,
    attention_mask: Optional[torch.tensor] = None,
    min_masks: int = 0,
) -> torch.tensor:
    """
    Computes random mask spans for a given shape. Used to implement `SpecAugment: A Simple Data Augmentation Method for
    ASR <https://arxiv.org/abs/1904.08779>`__.

    Args:
        shape: the the shape for which to compute masks.
            should be of size 2 where first element is batch size and 2nd is timesteps
        mask_prob: probability for each token to be chosen as start of the span to be masked. this will be multiplied by
            number of timesteps divided by length of mask span to mask approximately this percentage of all elements.
            however due to overlaps, the actual number will be smaller (unless no_overlap is True)
        mask_length: size of the mask
        min_masks: minimum number of masked spans

    """
    batch_size, sequence_length = shape

    if mask_length < 1:
        raise ValueError("`mask_length` has to be bigger than 0.")

    if mask_length > sequence_length:
        raise ValueError(
            f"`mask_length` has to be smaller than `sequence_length`, but got `mask_length`: {mask_length} and `sequence_length`: {sequence_length}`"
        )

    # compute number of masked spans in batch
    num_masked_spans = int(mask_prob * sequence_length / mask_length + torch.rand((1,)).item())
    num_masked_spans = max(num_masked_spans, min_masks)

    # make sure num masked indices <= sequence_length
    if num_masked_spans * mask_length > sequence_length:
        num_masked_spans = sequence_length // mask_length

    # SpecAugment mask to fill
    spec_aug_mask = torch.zeros((batch_size, sequence_length), device=device, dtype=torch.bool)

    # uniform distribution to sample from, make sure that offset samples are < sequence_length
    uniform_dist = torch.ones((batch_size, sequence_length - (mask_length - 1)), device=device) 

    # get random indices to mask
    spec_aug_mask_idxs = torch.multinomial(uniform_dist, num_masked_spans) 

    # expand masked indices to masked spans
    spec_aug_mask_idxs = (
        spec_aug_mask_idxs.unsqueeze(dim=-1) # b,spans,1
        .expand((batch_size, num_masked_spans, mask_length))
        .reshape(batch_size, num_masked_spans * mask_length) # ex) spec_aug_mask_idxs[0] = [1111111111777777777..]
    )
    offsets = (
        torch.arange(mask_length, device=device)[None, None, :]
        .expand((batch_size, num_masked_spans, mask_length))
        .reshape(batch_size, num_masked_spans * mask_length)
    )
    spec_aug_mask_idxs = spec_aug_mask_idxs + offsets

    # scatter indices to mask
    spec_aug_mask = spec_aug_mask.scatter(1, spec_aug_mask_idxs, True) 

    return spec_aug_mask