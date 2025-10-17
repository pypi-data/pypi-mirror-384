"""
denovo basecalling of DNA modificaitons
focus on CG motif
"""

import torch
from torch.nn import functional as F
import numpy as np
from functools import partial
import sys, re
from remora.util import format_mm_ml_tags
import array
from collections import namedtuple
from densecall.util import phred
from fast_ctc_decode import beam_search, viterbi_search
from densecall.multiprocessing import process_map
from densecall.util import mean_qscore_from_qstring
from densecall.util import chunk, stitch, batchify, unbatchify, permute
from densecall.mod_util import mods_tags_to_str, convert_base_name
from densecall.io import pprint

def basecall(model, reads, beamsize=1, chunksize=0, overlap=0, batchsize=1, qscores=True, reverse=None, rna=False):
    """
    Basecalls a set of reads.
    """

    chunks = ((read, chunk(torch.tensor(read.signal), chunksize, overlap)) for read in reads)

    scores = unbatchify((k, compute_scores(model, v)) for k, v in batchify(chunks, batchsize))
    scores = ((read, {"read": read, "scores": stitch(v, chunksize, overlap, len(read.signal), model.stride)}) for read, v in scores)
    decoder = partial(decode, alphabet=model.alphabet, beamsize=beamsize, qscores=qscores, stride=model.stride, rna=rna)
    basecalls = process_map(decoder, scores, n_proc=4)
    return basecalls


def compute_scores(model, batch):
    """
    Compute scores for model.
    """
    #print(batch.shape)

    with torch.no_grad():
        device = next(model.parameters()).device
        chunks = batch.to(torch.half).to(device)
        scores = model(chunks)
        if isinstance(scores, tuple):
            scores = scores[0]
    
    scores = permute(scores, 'TNC', 'NTC')
    return scores.cpu().to(torch.float32)


def build_moves(path):

    path = np.array(path, dtype=int)
    total_length = path[-1]
    moves = np.zeros(total_length, dtype=int)
    insert_indices = path[:-1]
    moves[insert_indices] = 1
    return moves


def decode(scores, alphabet, beamsize=1, qscores=True, stride=1, rna=False):
    """
    Convert the network scores into a sequence.
    """

    translation_table = str.maketrans("YIZHP", "AACGT")
    fliprna = (lambda x: x[::-1]) if rna else (lambda x: x)

    num_samples, trimmed_samples = scores["read"].num_samples, scores["read"].trimmed_samples
    actual_sample = (num_samples - trimmed_samples) // stride
    scores["scores"] = scores["scores"][:actual_sample, :]
    
    nn_prob = F.softmax(scores["scores"], -1).cpu().numpy().astype(np.float32)
    seq, path = viterbi_search(nn_prob, alphabet, qscores, 1, 0)

                
    semi = len(path)
    seq, qstring = seq[:semi], seq[semi:]

    # modified_seq = seq.encode('ascii') 
    # zg = b'ZG'
    # cg = b'CG'
    # zg_count = modified_seq.count(zg)
    # cg_count = modified_seq.count(cg)
    # total_count = zg_count + cg_count
    # if total_count > 0:
    #     zg_percent = zg_count / (zg_count + cg_count)
    # else:
    #     zg_percent = 0
    # zg_tag = f'zg:i:{int(zg_percent * 255)}'
    
    seq = seq.translate(translation_table)
    #seq = fliprna(seq)
    #qstring = fliprna(qstring)
    #path = np.flip(path, axis=1) if rna else path
    #print(nn_prob.shape,)



    
    mod_prob = build_mod_probs(alphabet, nn_prob, path)
    mods = modcall(mod_prob, seq, rna=rna)

    path = np.insert(path, len(path), actual_sample)
    moves = build_moves(path)
    # print(path, len(path), len(moves), len(seq), len(np.nonzero(moves)[0]), len(seq) == len(np.nonzero(moves)[0]))
    assert len(seq) == np.sum(moves), (len(seq), np.sum(moves))
    assert len(moves) == actual_sample
    return {"sequence": fliprna(seq), 
            "qstring": fliprna(qstring), "stride": stride, "moves": None, 
            "mods_densecall": mods}

#    (('Y', 'I', 'A'), lambda: prob_map['Y'] / (prob_map['Y'] + prob_map['I'] + prob_map['A']), 'A', 'a', 'DRACH'),
#     (('Y', 'I', 'A'), lambda: prob_map['I'] / (prob_map['Y'] + prob_map['I'] + prob_map['A']), 'A', '17596', 'A'),
     
def build_mod_probs(alphabet, nn_prob, path):
    Mod = namedtuple('Mod', 'base prob code motif')
    idx = {b: i for i, b in enumerate(alphabet)}
    prob = nn_prob[path]
    
    prob_map = {b: prob[:, idx[b]] for b in idx if b in {'Z', 'C', 'Y', 'I', 'A', 'H', 'G', 'P', 'T'}}
    
    mod_definitions = [
        (('Z', 'C'), lambda: prob_map['Z'] / (prob_map['C'] + prob_map['Z']), 'C', 'm', 'CG'),
        (('Y', 'A'), lambda: prob_map['Y'] / (prob_map['Y'] + prob_map['A']), 'A', 'a', 'A'),
        (('H', 'G'), lambda: prob_map['H'] / (prob_map['H'] + prob_map['G']), None, None, None),
        (('P', 'T'), lambda: prob_map['P'] / (prob_map['P'] + prob_map['T']), 'T', '17802', 'T')
    ]
    
    mod_prob = []
    for keys, calc_func, base, code, motif in mod_definitions:
        if all(k in prob_map for k in keys):
            try:
                result = calc_func()
                if base is not None:
                    mod_prob.append(Mod(base, result, code, motif))
            except ZeroDivisionError:
                continue
    
    return mod_prob



def modcall(mods_densecall, seq, rna=False):
    
    basecall_mods = []
    mm_tags, ml_arr = [], array.array("B")
    if len(mods_densecall) > 0:
        for can_base, nn_probs, mod_bases, motif in mods_densecall:
            if rna:
                nn_probs = nn_probs[::-1]
                seq = seq[::-1]
                
            kmer_fillter = convert_base_name(motif)
            nn_probs = nn_probs.reshape(-1, 1)
            r_poss = np.array([x.start() for x in re.finditer(kmer_fillter, seq)], dtype=int)
            r_probs = nn_probs[r_poss]
            #pprint(np.frombuffer(seq.encode(), 'S1')[r_poss])
            #assert np.all(np.frombuffer(seq.encode(), 'S1')[r_poss] == b'A')

            cb_mm, cb_ml = format_mm_ml_tags(seq, r_poss, r_probs, mod_bases, can_base)
            mm_tags.append(cb_mm)
            ml_arr.extend(cb_ml)

        basecall_mods = mods_tags_to_str(mm_tags, ml_arr)
        
    return basecall_mods
