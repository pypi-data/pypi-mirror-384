"""
modified based on Bonito Aligner
"""

from threading import Thread
from functools import partial
import mappy 
import numpy as np
from mappy import Aligner, ThreadBuffer
import sys 
from densecall.multiprocessing import ThreadMap
from densecall.mod_util import call_mods, load_mods_model

def align_map(aligner, sequences, n_thread=4, mod_model=None, use_reference_anchored=False):
    """
    Align `sequences` with minimap using `n_thread` threads.
    """
    return ThreadMap(partial(MappyWorker, aligner, mod_model, use_reference_anchored), sequences, n_thread)


class ManagedThreadBuffer:
    """
    Minimap2 ThreadBuffer that is periodically reallocated.
    """
    def __init__(self, max_uses=20):
        self.max_uses = max_uses
        self.uses = 0
        self._b = ThreadBuffer()

    @property
    def buffer(self):
        if self.uses > self.max_uses:
            self._b = ThreadBuffer()
            self.uses = 0
        self.uses += 1
        return self._b


class MappyWorker(Thread):
    """
    Process that reads items from an input_queue, applies a func to them and puts them on an output_queue
    """
    def __init__(self, aligner, mod_model, use_reference_anchored, input_queue=None, output_queue=None):
        super().__init__()
        self.aligner = aligner
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.mod_model = mod_model
        self.use_reference_anchored = use_reference_anchored

    def run(self):
        thrbuf = ManagedThreadBuffer()
        while True:
            item = self.input_queue.get()
            if item is StopIteration:
                self.output_queue.put(item)
                break
            k, v = item

            mapping = next(self.aligner.map(v['sequence'], buf=thrbuf.buffer, MD=True), None)
            
            if self.mod_model and mapping:
                
                refseq = self.aligner.seq(mapping.ctg, mapping.r_st, mapping.r_en)
                cigar = np.array(mapping.cigar)
                cigar = cigar[:, [1, 0]].tolist()
                if mapping.strand == -1:
                    refseq = mappy.revcomp(refseq)
                    cigar = cigar[::-1]
                    
                v['refseq'] = refseq
                v['cigar'] = cigar
                v['modified_results'] = []
                for mod_model, code in self.mod_model:
                    remora_model, remora_metadata = mod_model
                    can_base = remora_metadata['can_base']
                    v = call_mods(mod_model, k, v, use_reference_anchored=self.use_reference_anchored)
                    v['modified_results'].append((can_base, code, v['modified_result']))

            
            self.output_queue.put((k, {**v, 'mapping': mapping}))


