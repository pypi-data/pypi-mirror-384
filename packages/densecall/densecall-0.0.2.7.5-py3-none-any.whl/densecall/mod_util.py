"""
modified based on Bonito mod_util
"""

import sys, re
import logging
import numpy as np
import mappy
from remora import log
from remora.model_util import load_model
from remora.data_chunks import RemoraRead, compute_ref_to_signal
from remora.inference import call_read_mods
from remora.util import format_mm_ml_tags


def convert_base_name(base_name):
    """
    Converts a base name into a regular expression pattern.

    Args:
        base_name (str): Input base name to be converted.

    Returns:
        str: Regular expression pattern representing the converted base name.
    """
    merge_bases = {
        "A": "A",
        "C": "C",
        "G": "G",
        "T": "T",
        "M": "[AC]",
        "V": "[ACG]",
        "R": "[AG]",
        "H": "[ACT]",
        "W": "[AT]",
        "D": "[AGT]",
        "S": "[CG]",
        "B": "[CGT]",
        "Y": "[CT]",
        "N": "[ACGT]",
        "K": "[GT]",
    }
    pattern = ""
    for base in base_name:
        pattern += merge_bases.get(base, base)
    return pattern


class CustomFormatter(logging.Formatter):
    err_fmt = "> error (remora): %(msg)s"
    warn_fmt = "> warning (remora): %(msg)s"
    info_fmt = "> %(msg)s"

    def __init__(self, fmt="> %(message)s"):
        super().__init__(fmt=fmt, style="%")

    def format(self, record):
        format_orig = self._fmt
        if record.levelno == logging.INFO:
            self._style._fmt = self.info_fmt
        elif record.levelno == logging.WARNING:
            self._style._fmt = self.warn_fmt
        elif record.levelno == logging.ERROR:
            self._style._fmt = self.fmt
        result = logging.Formatter.format(self, record)
        self._fmt = format_orig
        return result

log.CONSOLE.setLevel(logging.WARNING)
log.CONSOLE.setFormatter(CustomFormatter())


def load_mods_model(mod_bases, bc_model_str, model_path, device=None):
    if mod_bases is not None:
        try:
            bc_model_type, model_version = bc_model_str.split('@')
            bc_model_type_attrs = bc_model_type.split('_')
            pore = '_'.join(bc_model_type_attrs[:-1])
            bc_model_subtype = bc_model_type_attrs[-1]
        except:
            sys.stderr.write(
                f"Could not parse basecall model directory ({bc_model_str}) "
                "for automatic modified base model loading"
            )
            sys.exit(1)
        return load_model(
            pore=pore,
            basecall_model_type=bc_model_subtype,
            basecall_model_version=model_version,
            modified_bases=mod_bases,
            quiet=True,
            device=device,
            eval_only=True
        )
    return load_model(model_path, quiet=True, device=device, eval_only=True)


def mods_tags_to_str(mm_tags, ml_arr):
    # TODO these operations are often quite slow
    return [
        f"MM:Z:{''.join(mm_tags)}",
        f"ML:B:C,{','.join(map(str, ml_arr))}",
    ]


def apply_stride_to_moves(attrs):
    moves = np.array(attrs['moves'], dtype=bool)
    sig_move = np.full(moves.size * attrs['stride'], False)
    sig_move[np.where(moves)[0] * attrs['stride']] = True
    return sig_move


def call_mods(mods_model, read, read_attrs, use_reference_anchored=False):
    #{'creation_date': '10/25/2022, 05:49:26', 'kmer_context_bases': [4, 4], 'chunk_context': [50, 50], 'base_pred': False, 'mod_bases': 'm', 'base_start_justify': False, 'offset': 0, 'model_params': {'size': 96, 'kmer_len': 9, 'num_out': 2}, 'mod_long_names_0': '5mC', 'num_motifs': '1', 'motif_0': 'CG', 'motif_offset_0': '0', 'doc_string': 'Nanopore Remora model', 'model_version': 3, 'reverse_signal': False, 'pa_scaling': None, 'mod_long_names': ['5mC'], 'kmer_len': 9, 'chunk_len': 100, 'motifs': [('CG', 0)], 'can_base': 'C', 'motif': ('CG', 0), 'alphabet_str': 'loaded modified base model to call (alt to C): m=5mC', 'sig_map_refiner': Loaded 0-mer table with 0 central position.}
    sequence = read_attrs['sequence']
    if len(read_attrs['sequence']) < 10:
        return read_attrs
    remora_model, remora_metadata = mods_model
    sig = read.signal

    # convert signal move table to remora read format
    sig_move = apply_stride_to_moves(read_attrs)
    seq_to_sig_map = np.empty(
        len(read_attrs['sequence']) + 1, dtype=np.int32
    )
    seq_to_sig_map[-1] = sig.shape[0]
    seq_to_sig_map[:-1] = np.where(sig_move)[0]
    
    
    #################################################
    if use_reference_anchored:
        refseq = read_attrs['refseq']
        cigar = read_attrs['cigar']
        if refseq is None or cigar is None:
            return read_attrs
        
        
        ref_to_signal = compute_ref_to_signal(
            query_to_signal=seq_to_sig_map,
            cigar=cigar,
        )
        if ref_to_signal.size != len(refseq) + 1:
            print(f"{read.read_id} discordant ref seq lengths: " f"move+cigar:{ref_to_signal.size} " f"ref_seq:{len(refseq)}", file=sys.stderr)
            raise ValueError("Discordant ref seq lengths")
        
        read_attrs['sequence'] = refseq
        seq_to_sig_map = ref_to_signal - ref_to_signal[0]
        sig = sig[ref_to_signal[0]:ref_to_signal[-1]]
    
    #################################################
    
    if remora_metadata["reverse_signal"]:
        sig = sig[::-1]
        seq_to_sig_map = seq_to_sig_map[-1] - seq_to_sig_map[::-1]
                    
    remora_read = RemoraRead(
        dacs=sig,
        shift=0,
        scale=1,
        seq_to_sig_map=seq_to_sig_map,
        str_seq=read_attrs['sequence'].upper(),
    )
    
    probs, labels, pos = call_read_mods(
            remora_read,
            remora_model,
            remora_metadata,
            return_mod_probs=True,
        )
    
    mods_tags = mods_tags_to_str(*format_mm_ml_tags(
            seq=remora_read.str_seq,
            poss=pos,
            probs=probs,
            mod_bases=remora_metadata["mod_bases"],
            can_base=remora_metadata["can_base"],
        ))
    
    read_attrs['modified_result'] = [probs, pos]
    read_attrs['mods'] = mods_tags
    read_attrs['sequence'] = sequence # in ctcwriter, if will reback to refseq, so keep it as basecall read
    return read_attrs
