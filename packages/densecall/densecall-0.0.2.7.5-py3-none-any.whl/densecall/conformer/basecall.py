"""
modified based on Bonito basecall
"""

import torch
import numpy as np
from functools import partial
import sys
from densecall.multiprocessing import process_map
from densecall.util import mean_qscore_from_qstring
from densecall.util import chunk, stitch, batchify, unbatchify, permute


def basecall(model, reads, beamsize=5, chunksize=0, overlap=0, batchsize=1, qscores=False, reverse=None, rna=False):
    """
    Basecalls a set of reads.
    """

    chunks = (
        (read, chunk(torch.tensor(read.signal), chunksize, overlap)) for read in reads
    )

    scores = unbatchify(
        (k, compute_scores(model, v)) for k, v in batchify(chunks, batchsize)
    )

    scores = (
        (read, {"read":read, 'scores': stitch(v, chunksize, overlap, len(read.signal), model.stride)}) for read, v in scores
    )
    decoder = partial(decode, decode=model.decode, beamsize=beamsize, qscores=qscores, stride=model.stride, rna=rna)
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

    path = np.array(path, dtype =int)
    total_length = path[-1] 
    moves = np.zeros(total_length, dtype=int)
    insert_indices = path[:-1]
    moves[insert_indices] = 1  
    return moves

def decode(scores, decode, beamsize=5, qscores=False, stride=1, rna=False):
    """
    Convert the network scores into a sequence.
    """
    translation_table = str.maketrans("YIZHP", "AACGT")
    fliprna = (lambda x:x[::-1]) if rna else (lambda x:x)

    num_samples, trimmed_samples = scores['read'].num_samples, scores['read'].trimmed_samples
    actual_sample = (num_samples - trimmed_samples) // stride
    scores['scores'] = scores['scores'][:actual_sample, :]

    if not (qscores or beamsize == 1):
        try:
            seq, path = decode(scores['scores'], beamsize=5, return_path=True, qscores=True)
            seq, qstring = seq[:len(path)], seq[len(path):]
        except Exception as e:
            print(e, file=sys.stderr)

    
    path = np.insert(path, len(path), actual_sample)
    moves = build_moves(path) 
    #print(path, len(path), len(moves), len(seq), len(np.nonzero(moves)[0]), len(seq) == len(np.nonzero(moves)[0]))
    assert len(seq) == len(np.nonzero(moves)[0]), (len(seq), len(np.nonzero(moves)[0]))
    assert len(moves) == actual_sample
    
    seq = seq.translate(translation_table)
    
    return {'sequence': fliprna(seq), 'qstring': fliprna(qstring), 'stride': stride, 'moves': moves}
