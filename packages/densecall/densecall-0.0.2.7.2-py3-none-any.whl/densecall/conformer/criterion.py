import numpy as np
import torch
from torch import nn
import torch.nn.functional as F
from torch import Tensor
import math
#from .crf import LinearCRF as CRF
#from .dctc import DCTC 

#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2023 Lucky Wong
#  Apache 2.0  (http://www.apache.org/licenses/LICENSE-2.0)
"""Oracle and 1-best Hypothesis CTC loss definition."""

import torch
import torchaudio
from torchaudio.models.decoder import ctc_decoder


class O1Loss(torch.nn.Module):
    """
    O-1: Self-training with Oracle and 1-best Hypothesis
    https://arxiv.org/abs/2308.07486
    """

    def __init__(self, vocab_size, beam_size=8):
        """
        Args:
            beam_size (int): number of best decodings to return
        """
        super().__init__()
        tokens = [str(i) for i in range(vocab_size)]
        self.beam_search_decoder = ctc_decoder(
            lexicon=None,
            tokens=tokens,
            nbest=beam_size,
            beam_size=beam_size,
            blank_token="0",
            sil_token="0",
        )

    def forward(self, emissions, emissions_lengths, labels, labels_length):
        beam_search_results = self.beam_search_decoder(emissions.cpu(), emissions_lengths.cpu())
        
        # 提取所有batch的最大beam数量
        max_beam_size = max(len(result) for result in beam_search_results)
        
        # 预分配张量
        all_scores = torch.zeros(len(beam_search_results), max_beam_size)
        all_wers = torch.zeros(len(beam_search_results), max_beam_size)
        
        # 批量处理所有序列
        for batch_idx, beam_search_result in enumerate(beam_search_results):
            groud_turth = labels[batch_idx, :labels_length[batch_idx]].cpu()
            beam_size = len(beam_search_result)
            
            # 提取scores
            scores = torch.tensor([result.score for result in beam_search_result])
            all_scores[batch_idx, :beam_size] = scores
            
            # 批量计算WER
            for idx, one_result in enumerate(beam_search_result):
                tokens = one_result.tokens[1:-1]
                wer = torchaudio.functional.edit_distance(groud_turth, tokens) / len(groud_turth)
                all_wers[batch_idx, idx] = wer
        
        # 找到每个batch的oracle（最小WER）
        oracle_wers, oracle_indices = torch.min(all_wers, dim=1)
        oracle_scores = all_scores.gather(1, oracle_indices.unsqueeze(1)).squeeze(1)
        
        # 1-best（第一列）
        one_best_wers = all_wers[:, 0]
        one_best_scores = all_scores[:, 0]
        
        # 批量计算loss
        loss_o1 = -oracle_scores * (1 - oracle_wers) + one_best_scores * one_best_wers
        return loss_o1.sum().to(emissions.device)

    def forward2(
        self,
        emissions: torch.Tensor,
        emissions_lengths: torch.Tensor,
        labels: torch.Tensor,
        labels_length: torch.Tensor
    ) -> torch.Tensor:
        """
        Args:
            emissions (torch.FloatTensor): CPU tensor of shape `(batch, frame, num_tokens)` storing sequences of
                probability distribution over labels; output of acoustic model.
            labels (torch.FloatTensor): CPU tensor of shape `(batch, label_len)` storing labels.
            emissions_lengths (Tensor or None, optional): CPU tensor of shape `(batch, )` storing the valid length of
                in time axis of the output Tensor in each batch.
            labels_length (Tensor or None, optional): CPU tensor of shape `(batch, )` storing the valid length of
                label in each batch.

        Returns:
            torch.FloatTensor:
                O-1 loss.
        """
        beam_search_results = self.beam_search_decoder(
            emissions.cpu(), emissions_lengths.cpu())
        loss = torch.tensor(0.0)
        for batch_idx in range(emissions.size(0)):
            groud_turth = labels[batch_idx, :labels_length[batch_idx]].cpu()
            beam_search_result = beam_search_results[batch_idx]

            # The hypothesis with the best WER serves as the oracle hypothesis Y
            # oracle and the hypothesis with the top probability becomes the 1-best hypothesis Y1−best.
            # Both oracle and 1-best hypotheses are chosen from the beam while dropping the
            # rest of the hypotheses.
            for idx, one_result in enumerate(beam_search_result):
                tokens = one_result.tokens[1:-1]
                score = one_result.score
                beam_search_wer = torchaudio.functional.edit_distance(
                    groud_turth, tokens) / len(groud_turth)
                
                #print(beam_search_wer)
                if idx == 0:
                    # 1-best
                    one_best_score = score
                    one_best_wer = beam_search_wer
                    # orcle
                    oracle_wer = beam_search_wer
                    oracle_score = score
                elif oracle_wer < beam_search_wer:
                    # orcle
                    oracle_wer = beam_search_wer
                    oracle_score = score
            loss_o1 = -oracle_score*(1-oracle_wer)+one_best_score*one_best_wer
            loss += loss_o1
        return loss.to(emissions.device)

    
    
def crf_loss(log_probs, targets, lengths, crf_model, blank_id=0):

    T, N, C = log_probs.shape
    N, S = targets.shape
        
    #padded_targets = F.pad(targets, (0, T - targets.size(1)), "constant", blank_id)
    #tags = padded_targets
        
    mask = torch.arange(S, device=log_probs.device).expand(N, S) < lengths.unsqueeze(1)
    loss = crf_model(log_probs.transpose(0, 1), targets, mask=mask)
    
    return loss


def ctc_label_smoothing_loss(log_probs, log_probs_lengths, targets, lengths, weights=None):
    T, N, C = log_probs.shape
    log_probs_lengths = torch.full(size=(N, ), fill_value=T, dtype=torch.int64)
    loss = F.ctc_loss(log_probs.to(torch.float32), targets, log_probs_lengths, lengths, reduction='mean', zero_infinity=True)
    #weights = torch.tensor([0.35, 0.025, 0.025, 0.05, 0.025, 0.025])
    #weights = weights if weights is not None else torch.cat([torch.tensor([0.4]), (0.1 / (C - 1)) * torch.ones(C - 1)])    
    label_smoothing_loss = -((log_probs * weights.to(log_probs.device)).mean())
    #kldiv_loss = ace_loss(log_probs, log_probs_lengths, targets, lengths, alpha=0.1)
    #print(weights)
    
    return {'total_loss': loss + label_smoothing_loss, 
            'loss': loss, 'label_smooth_loss': label_smoothing_loss, 
            }


def ctc_label_smoothing_loss2(log_probs, log_probs_lengths, targets, lengths, weights=None):

    T, N, C = log_probs.shape  # TNC
    

    labels_mask = targets > 0
    target_lengths = labels_mask.sum(-1)
    flattened_targets = targets.masked_select(labels_mask)


    standard_ctc_loss = F.ctc_loss(log_probs, flattened_targets, log_probs_lengths, target_lengths, reduction="none", zero_infinity=True)
    standard_ctc_loss = (standard_ctc_loss / target_lengths.to(log_probs.device)).mean()


    weights = weights or torch.cat([torch.tensor([0.4]), (0.1 / (C - 1)) * torch.ones(C - 1)])
    label_smoothing_loss = -((log_probs * weights.to(log_probs.device)).mean())

    return {
        "total_loss": standard_ctc_loss + label_smoothing_loss,
        "loss": standard_ctc_loss,
        "label_smooth_loss": label_smoothing_loss,
    }
    
    
def focal_ctc2(log_probs, log_probs_lengths, targets, lengths, gamma=2, alpha=1, eps=1e-6):

    T, N, C = log_probs.shape  # TNC
    labels_mask = targets > 0
    target_lengths = labels_mask.sum(-1)
    flattened_targets = targets.masked_select(labels_mask)

    standard_ctc_loss = F.ctc_loss(log_probs, flattened_targets, log_probs_lengths, target_lengths, reduction="none", zero_infinity=True)


    p = torch.exp(-standard_ctc_loss)
    loss = alpha * torch.pow((1 - p), gamma) * standard_ctc_loss
    loss = (loss / lengths).mean() 
    #loss = 0.5 * loss + 0.5 * (standard_ctc_loss / lengths).mean()

    return loss

def focal_ctc(log_probs, input_lengths, targets, target_lengths,
              blank=0, zero_infinity=True, gamma=2.0, alphabet='NACZGT'):
    device = log_probs.device
    T, N, C = log_probs.size()

    # 0. 1-D alpha 表：下标=class-id
    alpha_table = torch.full((C,), 1.0, device=device)
    alpha_table[0] = 0.1                       # blank
    for i, ch in enumerate(alphabet[1:], 1):
        alpha_table[i] = 1.0 if ch in 'ACGT' else 10.0

    # 1. CTC loss
    raw_loss = F.ctc_loss(log_probs, targets, input_lengths, target_lengths,
                          blank=blank, reduction='none', zero_infinity=False)
    if zero_infinity:
        raw_loss = torch.where(torch.isinf(raw_loss), 0., raw_loss)
        
    p = torch.exp(-raw_loss)
    focal_w = (1 - p) ** gamma

    # 2. 一次性映射 alpha（targets 已保证 2-D）
    alpha_mat = alpha_table[targets]           # (N, S)
    mask = torch.arange(targets.size(1), device=device).unsqueeze(0) < target_lengths.unsqueeze(1)
    alpha_w = (alpha_mat * mask).sum(1) / target_lengths.clamp(min=1)
    #print(alpha_w)

    # 3. 加权 + 官方 mean
    loss = alpha_w * focal_w * raw_loss
    return (loss / target_lengths).mean()


def ace_loss(log_probs, log_probs_lengths, targets, target_lengths, alpha=0.1):
    """
    Calculate the ACE label smoothing loss.

    Args:
        log_probs (Tensor): Input log probabilities with shape (sequence length, batch size, number of classes).
        targets (Tensor): Target labels with shape (batch size, label length).
        log_probs_lengths (Tensor): Lengths of input sequences with shape (batch size,).
        target_lengths (Tensor): Lengths of target sequences with shape (batch size,).
        alpha (float): Label smoothing parameter, default is 0.1.

    Returns:
        Tensor: ACE label smoothing loss value.
    """
    T_, bs, class_size = log_probs.size()
    probs = torch.exp(log_probs)  # Convert log probabilities to probabilities

    # Split the targets and pad them
    # targets_split = list(torch.split(targets, target_lengths.tolist()))
    # targets_padded = torch.nn.utils.rnn.pad_sequence(targets_split, batch_first=True, padding_value=0)

    # Convert to one-hot encoding and apply label smoothing
    targets_padded = F.one_hot(targets.long(), num_classes=class_size)
    targets_padded = (targets_padded * (1 - alpha)) + (alpha / class_size)

    # Sum to get the class count for each sample
    targets_padded = torch.sum(targets_padded, 1).float()  # batch * class

    # Handle the count of the blank class
    targets_padded[:, 0] = T_ - target_lengths

    # Normalize the probabilities and targets
    probs_sum = torch.sum(probs, 0)  # batch * class
    probs_sum = probs_sum / T_
    targets_padded = targets_padded / T_
    targets_padded = F.normalize(targets_padded, p=1, dim=1)

    # Calculate the KL divergence
    return F.kl_div(log_probs.mean(0), targets_padded, reduction="batchmean")

def label_smoothing_loss(log_probs, weights=None):
    T, N, C = log_probs.shape  # TNC
    weights = weights or torch.cat([torch.tensor([0.4]), (0.1 / (C - 1)) * torch.ones(C - 1)])
    loss = -((log_probs * weights.to(log_probs.device)).mean())
    return loss




def ce_label_smoothing_losss(decoder_log_probs, targets, smoothing = 0.1):
    # KL 散度损失
    N, T, C = decoder_log_probs.shape
    x = decoder_log_probs.view(-1, C)
    target = targets.view(-1)
    
    true_dist = torch.zeros_like(x)
    true_dist.fill_(smoothing/ (C - 1))
    ignore = target == 0  # (B,)
    total = len(target) - ignore.sum().item()
    target = target.masked_fill(ignore, 0)  # avoid -1 index
    true_dist.scatter_(1, target.unsqueeze(1), (1 - smoothing))
    kl = F.kl_div(x, true_dist, reduction='none')
    kl_loss = kl.masked_fill(ignore.unsqueeze(1), 0).sum() / total
    return kl_loss
    
# def rnnt_loss(am_logits, lm_logits, targets, lengths):
#     # # Transducer 损失
#     pruned_loss = transducer(am_logits, lm_logits, targets, lengths)
#     return pruned_loss



def logadd(x0: torch.Tensor, x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
    return torch.logsumexp(torch.stack([x0, x1, x2]), dim=0)

def scan_simulate(fn, initial, inputs):
    outputs = []
    prev_output = initial
    for input_ in inputs.unbind(0):
        prev_output = fn(prev_output, input_)
        outputs.append(prev_output)
    return torch.stack(outputs)

def wctc_loss(log_probs : torch.Tensor, input_lengths : torch.Tensor, targets : torch.Tensor, target_lengths : torch.Tensor, 
    blank : int = 0, reduction : str = 'none', finfo_min_fp32: float = torch.finfo(torch.float32).min, finfo_min_fp16: float = torch.finfo(torch.float16).min, 
    alignment : bool = False, mode : str = 'soft', return_mean : bool = True, zero_infinity: bool = False) -> torch.Tensor:

    input_lengths = input_lengths.long()
    target_lengths = target_lengths.long()

    input_time_size, batch_size = log_probs.shape[:2]
    B = torch.arange(batch_size, device = input_lengths.device)

    # handle flattened targets
    if len(targets.shape) == 1: 
        max_len = torch.max(target_lengths)
        targets_copy = torch.full((batch_size, max_len), 0, device=log_probs.device, dtype=torch.long)
        i = 0
        cnt = 0
        for l in target_lengths:
            targets_copy[cnt, :l] = targets[i:i+l]
            i += l
            cnt += 1
    else:
        targets_copy = targets
    
    _t_a_r_g_e_t_s_ = torch.cat([targets_copy, targets_copy[:, :1]], dim = -1)
    _t_a_r_g_e_t_s_ = torch.stack([torch.full_like(_t_a_r_g_e_t_s_, blank), _t_a_r_g_e_t_s_], dim = -1).flatten(start_dim = -2)

    # make any padding token to 0
    _t_a_r_g_e_t_s_[_t_a_r_g_e_t_s_ < 0] = blank

    # make target 1 a diff_label
    diff_labels = torch.cat([torch.as_tensor([[False, True]], device = targets_copy.device).expand(batch_size, -1), _t_a_r_g_e_t_s_[:, 2:] != _t_a_r_g_e_t_s_[:, :-2]], dim = 1)
    
    zero_padding = 2
    zero = torch.tensor(finfo_min_fp16 if log_probs.dtype == torch.float16 else finfo_min_fp32, device = log_probs.device, dtype = log_probs.dtype)
    log_probs_ = log_probs.gather(-1, _t_a_r_g_e_t_s_.expand(input_time_size, -1, -1))
    log_alpha = torch.full((input_time_size, batch_size, zero_padding + _t_a_r_g_e_t_s_.shape[-1]), zero, device = log_probs.device, dtype = log_probs.dtype)

    # add wild-card in the first row
    log_alpha[:, :, 1] = 0.0 # log prob 1 = 0

    log_alpha[0, :, zero_padding + 0] = log_probs[0, :, blank]
    log_alpha[0, :, zero_padding + 1] = log_probs[0, B, _t_a_r_g_e_t_s_[:, 1]]

    def scan_fn(prev_log_alpha, log_probs_t):
        prev_log_alpha_2 = prev_log_alpha[:, 2:]
        prev_log_alpha_1 = prev_log_alpha[:, 1:-1]
        prev_log_alpha_0 = torch.where(diff_labels, prev_log_alpha[:, :-2], zero)
        new_log_alpha_2 = log_probs_t + logadd(prev_log_alpha_2, prev_log_alpha_1, prev_log_alpha_0)
        new_log_alpha = prev_log_alpha.clone()
        new_log_alpha[:, 2:] = new_log_alpha_2
        return new_log_alpha

    
    log_alpha_rest = scan_simulate(scan_fn, log_alpha[0], log_probs_[1:])
    log_alpha[1:] = log_alpha_rest

    # track the entire last row
    l1l2_indices = torch.stack([zero_padding + target_lengths * 2 - 1, zero_padding + target_lengths * 2], dim = -1).repeat(input_time_size, 1, 1)
    l1l2 = log_alpha.gather(-1, l1l2_indices)
    l1l2_sum = torch.logsumexp(l1l2, dim=-1)

    # 3 different modes
    if mode == 'soft':
        l1l2_sigma = torch.sum(F.softmax(l1l2_sum, dim=0) * l1l2_sum, dim=0)
    elif mode == 'max_prob':
        l1l2_sigma = torch.max(l1l2_sum, dim=0)[0]
    elif mode == 'sum_prob':
        l1l2_sigma = torch.logsumexp(l1l2_sum, dim=0)
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    if return_mean:
        return torch.mean(-l1l2_sigma)
    else:
        return -l1l2_sigma