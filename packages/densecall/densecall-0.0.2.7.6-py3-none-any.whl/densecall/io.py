"""
modified based on Bonito io
"""

import os
import sys
import csv
import pandas as pd
from threading import Thread
from logging import getLogger
from collections import namedtuple, defaultdict
from contextlib import contextmanager
from os.path import realpath, splitext, dirname
from remora.util import format_mm_ml_tags
import mappy
from remora import data_chunks
import array
import numpy as np
from Bio.Seq import reverse_complement
from pysam import AlignmentFile, AlignmentHeader, AlignedSegment
import re
import densecall
import threading
from densecall.util import mean_qscore_from_qstring
from remora.util import softmax_axis1
from densecall.mod_util import mods_tags_to_str, convert_base_name


logger = getLogger("densecall")
Format = namedtuple("Format", "aligned name mode")

__ont_bam_spec__ = "0.0.2"

def pprint(*msg):
    print(*msg, file=sys.stderr)
    

def typical_indices(x, n=2.5):
    mu, sd = np.mean(x), np.std(x)
    (idx,) = np.where((mu - n * sd < x) & (x < mu + n * sd))
    return idx


def biofmt(aligned=False):
    """
    Select the output format.
    """
    mode, name = ("w", "sam") if aligned else ("wfq", "fastq")
    aligned = "aligned" if aligned else "unaligned"
    stdout = realpath("/dev/fd/1")
    if sys.stdout.isatty() or stdout.startswith("/proc"):
        return Format(aligned, name, mode)
    ext = stdout.split(os.extsep)[-1]
    if ext in ["fq", "fastq"]:
        return Format(aligned, "fastq", "wfq")
    elif ext == "bam":
        return Format(aligned, "bam", "wb")
    elif ext == "cram":
        return Format(aligned, "cram", "wc")
    elif ext == "sam":
        return Format(aligned, "sam", "w")
    else:
        return Format(aligned, name, mode)


def encode_moves(moves, stride, sep=","):
    """
    Encode a numpy array of integers into a comma seperated string
    starting with `stride`. For efficiency, this method is only
    valid for +ve single digit values in `moves`.

    >>> encode_moves(np.array([0, 1, 0, 1, 1], dtype=np.int8), 5)
    '5,0,1,0,1,1'
    """

    moves = np.array(moves)
    separators = np.full(2 * moves.size, ord(sep), dtype=np.dtype("B"))

    # convert moves to ascii and interleave with separators
    #  ~3 orders faster than `sep.join(np.char.mod("%d", moves))`
    separators[1::2] = moves + ord("0")

    return f"{stride}{separators.tobytes().decode('ascii')}"


@contextmanager
def devnull(*args, **kwds):
    """
    A context manager that sends all out stdout & stderr to devnull.
    """
    save_fds = [os.dup(1), os.dup(2)]
    null_fds = [os.open(os.devnull, os.O_RDWR) for _ in range(2)]
    os.dup2(null_fds[0], 1)
    os.dup2(null_fds[1], 2)
    try:
        yield
    finally:
        os.dup2(save_fds[0], 1)
        os.dup2(save_fds[1], 2)
        for fd in null_fds + save_fds:
            os.close(fd)


def write_fasta(header, sequence, fd=sys.stdout):
    """
    Write a fasta record to a file descriptor.
    """
    fd.write(f">{header}\n{sequence}\n")


def write_fastq(header, sequence, qstring, fd=sys.stdout, tags=None, sep="\t"):
    """
    Write a fastq record to a file descriptor.
    """
    if tags is not None:
        fd.write(f"@{header} {sep.join(tags)}\n")
    else:
        fd.write(f"@{header}\n")
    fd.write(f"{sequence}\n+\n{qstring}\n")


def sam_header(groups, sep="\t"):
    """
    Format a string sam header.
    """
    HD = sep.join(
        [
            "@HD",
            "VN:1.5",
            "SO:unknown",
            "ob:%s" % __ont_bam_spec__,
        ]
    )
    PG1 = sep.join(
        [
            "@PG",
            "ID:basecaller",
            "PN:densecall",
            "VN:%s" % densecall.__version__,
            "CL:densecall %s" % " ".join(sys.argv[1:]),
        ]
    )
    PG2 = sep.join(
        [
            "@PG",
            "ID:aligner",
            "PN:minimap2",
            "VN:%s" % mappy.__version__,
            "DS:mappy",
        ]
    )
    return "%s\n" % os.linesep.join([HD, PG1, PG2, *groups])


def sam_record(read_id, sequence, qstring, mapping, tags=None, sep="\t"):
    """
    Format a string sam record.
    """
    if mapping:
        softclip = ["%sS" % mapping.q_st if mapping.q_st else "", mapping.cigar_str, "%sS" % (len(sequence) - mapping.q_en) if len(sequence) - mapping.q_en else ""]
        record = [
            read_id,
            0 if mapping.strand == +1 else 16,
            mapping.ctg,
            mapping.r_st + 1,
            mapping.mapq,
            "".join(softclip if mapping.strand == +1 else softclip[::-1]),
            "*",
            0,
            0,
            sequence if mapping.strand == +1 else mappy.revcomp(sequence),
            qstring,
            "NM:i:%s" % mapping.NM,
            "MD:Z:%s" % mapping.MD,
        ]
    else:
        record = [read_id, 4, "*", 0, 0, "*", "*", 0, 0, sequence, qstring, "NM:i:0"]

    if tags is not None:
        record.extend(tags)

    return sep.join(map(str, record))


def summary_file():
    """
    Return the filename to use for the summary tsv.
    """
    stdout = realpath("/dev/fd/1")
    if sys.stdout.isatty() or stdout.startswith("/proc"):
        return "summary.tsv"
    return "%s_summary.tsv" % splitext(stdout)[0]


summary_field_names = [
    "filename",
    "read_id",
    "run_id",
    "channel",
    "mux",
    "start_time",
    "duration",
    "template_start",
    "template_duration",
    "sequence_length_template",
    "mean_qscore_template",
    # if alignment
    "alignment_genome",
    "alignment_genome_start",
    "alignment_genome_end",
    "alignment_strand_start",
    "alignment_strand_end",
    "alignment_direction",
    "alignment_length",
    "alignment_num_aligned",
    "alignment_num_correct",
    "alignment_num_insertions",
    "alignment_num_deletions",
    "alignment_num_substitutions",
    "alignment_mapq",
    "alignment_strand_coverage",
    "alignment_identity",
    "alignment_accuracy",
]


def summary_row(read, seqlen, qscore,alignment=False):
    """
    Summary tsv row.
    """
    fields = [
        read.filename,
        read.read_id,
        read.run_id,
        read.channel,
        read.mux,
        read.start,
        read.duration,
        read.template_start,
        read.template_duration,
        seqlen,
        qscore,

    ]

    if alignment:

        ins = sum(count for count, op in alignment.cigar if op == 1)
        dels = sum(count for count, op in alignment.cigar if op == 2)
        subs = alignment.NM - ins - dels
        length = alignment.blen
        matches = length - ins - dels
        correct = alignment.mlen

        fields.extend(
            [
                alignment.ctg,
                alignment.r_st,
                alignment.r_en,
                alignment.q_st if alignment.strand == +1 else seqlen - alignment.q_en,
                alignment.q_en if alignment.strand == +1 else seqlen - alignment.q_st,
                "+" if alignment.strand == +1 else "-",
                length,
                matches,
                correct,
                ins,
                dels,
                subs,
                alignment.mapq,
                (alignment.q_en - alignment.q_st) / seqlen,
                correct / matches,
                correct / length,
            ]
        )

    elif alignment is None:
        fields.extend(["*", -1, -1, -1, -1, "*", 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0])

    return dict(zip(summary_field_names, fields))


duplex_summary_field_names = [
    "filename_template",
    "read_id_template",
    "filename_complement",
    "read_id_complement",
    "run_id",
    "channel_template",
    "mux_template",
    "channel_complement",
    "mux_complement",
    "sequence_length_duplex",
    "mean_qscore_duplex",
    # if alignment
    "alignment_genome",
    "alignment_genome_start",
    "alignment_genome_end",
    "alignment_strand_start",
    "alignment_strand_end",
    "alignment_direction",
    "alignment_length",
    "alignment_num_aligned",
    "alignment_num_correct",
    "alignment_num_insertions",
    "alignment_num_deletions",
    "alignment_num_substitutions",
    "alignment_mapq",
    "alignment_strand_coverage",
    "alignment_identity",
    "alignment_accuracy",
]


def duplex_summary_row(read_temp, comp_read, seqlen, qscore, alignment=False):
    """
    Duplex summary tsv row.
    """
    fields = [
        read_temp.filename,
        read_temp.read_id,
        comp_read.filename,
        comp_read.read_id,
        read_temp.run_id,
        read_temp.channel,
        read_temp.mux,
        comp_read.channel,
        comp_read.mux,
        seqlen,
        qscore,
    ]

    if alignment:

        ins = sum(count for count, op in alignment.cigar if op == 1)
        dels = sum(count for count, op in alignment.cigar if op == 2)
        subs = alignment.NM - ins - dels
        length = alignment.blen
        matches = length - ins - dels
        correct = alignment.mlen

        fields.extend(
            [
                alignment.ctg,
                alignment.r_st,
                alignment.r_en,
                alignment.q_st if alignment.strand == +1 else seqlen - alignment.q_en,
                alignment.q_en if alignment.strand == +1 else seqlen - alignment.q_st,
                "+" if alignment.strand == +1 else "-",
                length,
                matches,
                correct,
                ins,
                dels,
                subs,
                alignment.mapq,
                (alignment.q_en - alignment.q_st) / seqlen,
                correct / matches,
                correct / length,
            ]
        )

    elif alignment is None:
        fields.extend(["*", -1, -1, -1, -1, "*", 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0])

    return dict(zip(duplex_summary_field_names, fields))


class CSVLogger:
    def __init__(self, filename, sep=","):
        self.filename = str(filename)
        if os.path.exists(self.filename):
            with open(self.filename) as f:
                self.columns = csv.DictReader(f).fieldnames
        else:
            self.columns = None
        self.fh = open(self.filename, "a", newline="")
        self.csvwriter = csv.writer(self.fh, delimiter=sep)
        self.count = 0

    def set_columns(self, columns):
        if self.columns:
            raise Exception("Columns already set")
        self.columns = list(columns)
        self.csvwriter.writerow(self.columns)

    def append(self, row):
        if self.columns is None:
            self.set_columns(row.keys())
        self.csvwriter.writerow([row.get(k, "-") for k in self.columns])
        self.count += 1
        if self.count > 100:
            self.count = 0
            self.fh.flush()

    def close(self):
        self.fh.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class NullWriter(Thread):

    def __init__(self, mode, iterator, duplex=False, **kwargs):
        super().__init__()
        self.log = []
        self.duplex = duplex
        self.iterator = iterator

    def run(self):

        for read, res in self.iterator:
            if self.duplex:
                samples = len(read[0].signal) + len(read[1].signal)
                read_id = "%s;%s" % (read[0].read_id, read[1].read_id)
            else:
                samples = len(read.signal)
                read_id = read.read_id
            self.log.append((read_id, samples))


class Writer(Thread):

    def __init__(self, mode, iterator, aligner, fd=sys.stdout, ref_fn=None, groups=None, group_key=None, min_qscore=0, args=None):
        super().__init__()
        self.fd = fd
        self.log = []
        self.mode = mode
        self.aligner = aligner
        self.iterator = iterator
        self.fastq = mode == "wfq"
        self.group_key = group_key
        self.min_qscore = min_qscore
        self.args = args

        self.output = AlignmentFile(
            fd,
            "w" if self.fastq else self.mode,
            add_sam_header=not self.fastq,
            reference_filename=ref_fn,
            header=AlignmentHeader.from_references(
                reference_names=aligner.seq_names if aligner else [],
                reference_lengths=[len(aligner.seq(name)) for name in aligner.seq_names] if aligner else [],
                text=sam_header(groups),
            ),
        )

    def run(self):
        with CSVLogger(summary_file(), sep="\t") as summary:
            for read, res in self.iterator:

                seq = res["sequence"]
                qstring = res.get("qstring", "*")
                mean_qscore = res.get("mean_qscore", mean_qscore_from_qstring(qstring))
                mapping = res.get("mapping", False)
                mods_tags = res.get("mods", [])
                moves = res.get("moves", None)
                stride = res.get("stride", 1)
                mods_densecall = res.get("mods_densecall", []) 
                zg_tag = res.get("zg_tag", [])
                resquiggle_tag = ""

                if self.args.output_resquiggle and mapping:
                    sig_len = read.num_samples - read.trimmed_samples
                    ref_seq = self.aligner.seq(mapping.ctg, mapping.r_st, mapping.r_en)
                    query_to_signal = np.nonzero(moves)[0] * stride
                    query_to_signal = np.append(query_to_signal, sig_len)
                    cigar = np.array(mapping.cigar)
                    cigar = cigar[:, [1, 0]].tolist()
                    if mapping.strand == -1:
                        if ref_seq is not None:
                            ref_seq = mappy.revcomp(ref_seq)
                        cigar = cigar[::-1]

                    ref_to_signal = data_chunks.compute_ref_to_signal(
                        query_to_signal=query_to_signal,
                        cigar=cigar,
                    )

                    #print(ref_to_signal, sig_len, file=sys.stderr)
                    
                    if ref_to_signal.size != len(ref_seq) + 1:
                        print(f"{read.read_id} discordant ref seq lengths: " f"move+cigar:{ref_to_signal.size} " f"ref_seq:{len(ref_seq)}", file=sys.stderr)
                        raise ValueError("Discordant ref seq lengths")
                    if query_to_signal.size - 1 != len(seq):
                        raise ValueError("Move table discordant with basecalls")
                    if len(moves) != sig_len // stride:
                        print(f"moves: {len(moves)}, sig_len: {sig_len}, stride: {stride}", file=sys.stderr)
                        raise ValueError("Move table discordant with signal")

                    resquiggle_tag = "re:B:I," + ",".join(map(str, ref_to_signal))


                samples = len(read.signal)
                read_id = read.read_id

                self.log.append((read_id, samples))

                if mean_qscore < self.min_qscore:
                    continue

                tags = [
                    f"RG:Z:{read.run_id}_{self.group_key}",
                    f"qs:i:{round(mean_qscore)}",
                    f"ns:i:{read.num_samples}",
                    f"ts:i:{read.trimmed_samples}",
                    *zg_tag,
                    *read.tagdata(),
                    *mods_tags,
                    *mods_densecall,
        
                ]

                if res["moves"] is not None and self.mode != "wfq":
                    tags.append(f'mv:B:c,{encode_moves(res["moves"], res["stride"])}')
                if self.args.output_resquiggle:
                    tags.append(resquiggle_tag)
                    

                if len(seq):
                    if self.mode == "wfq":
                        write_fastq(read_id, seq, qstring, fd=self.fd, tags=tags)
                    else:
                        self.output.write(AlignedSegment.fromstring(sam_record(read_id, seq, qstring, mapping, tags=tags), self.output.header))
                    summary.append(summary_row(read, len(seq), mean_qscore, alignment=mapping))
                else:
                    logger.warn("> skipping empty sequence %s", read_id)


class DuplexWriter(Writer, Thread):

    def run(self):
        for read, res in self.iterator:

            read_id = "%s;%s" % (read[0], read[1])

            seq = res["sequence"]
            qstring = res.get("qstring", "*")
            mean_qscore = res.get("mean_qscore", mean_qscore_from_qstring(qstring))
            mapping = res.get("mapping", False)

            self.log.append((read_id, len(seq)))

            if mean_qscore < self.min_qscore:
                continue

            tags = [
                f"qs:i:{round(mean_qscore)}",
            ]

            if len(seq):
                if self.mode == "wfq":
                    write_fastq(read_id, seq, qstring, fd=self.fd, tags=tags)
                else:
                    self.output.write(AlignedSegment.fromstring(sam_record(read_id, seq, qstring, mapping, tags=tags), self.output.header))


class RejectCounter(dict):
    """Used to count reasons for rejection"""

    def __call__(self, reject_condition, condition_name):
        if reject_condition:
            self[condition_name] = self.get(condition_name, 0) + 1
        return reject_condition


class CTCWriter(Thread):
    """
    CTC writer process that writes output numpy training data.
    """

    def __init__(self, mode, iterator, aligner, fd=sys.stdout, min_coverage=0.9, min_accuracy=0.99, ref_fn=None, groups=None, group_key=None, min_qscore=None, rna=False, args=None):
        super().__init__()
        self.fd = fd
        self.log = []
        self.mode = mode
        self.aligner = aligner
        self.iterator = iterator
        self.group_key = group_key
        self.min_coverage = min_coverage
        self.min_accuracy = min_accuracy
        self.min_qscore = min_qscore
        self.rna = rna
        self.args = args
        self.alphabet = args.alphabet
        self.output = AlignmentFile(
            fd,
            "w" if self.mode == "wfq" else self.mode,
            add_sam_header=self.mode != "wfq",
            reference_filename=ref_fn,
            header=AlignmentHeader.from_references(
                reference_names=aligner.seq_names,
                reference_lengths=[len(aligner.seq(name)) for name in aligner.seq_names],
                text=sam_header(groups),
            ),
        )
        
        self.max_chunks = 100000

                   
        

    def run(self):

        chunks = []
        targets = []
        cano_targets = []
        lengths = []
        reject_counter = RejectCounter()
        counter = RejectCounter()
        with CSVLogger(summary_file(), sep="\t") as summary:
            for ctc_inx, (read, ctc_data) in enumerate(self.iterator):
                seq = ctc_data["sequence"]
                qstring = ctc_data["qstring"]
                mean_qscore = ctc_data.get("mean_qscore", mean_qscore_from_qstring(qstring))
                mapping = ctc_data.get("mapping", False)
                zg_tag = ctc_data.get("zg_tag", [])
                tags = [
                    *zg_tag,
                ]


                self.log.append((read.read_id, len(read.signal)))

                if reject_counter(mean_qscore < self.min_qscore, "low_qscore"):
                    continue
                if reject_counter(len(seq) == 0, "zerolen_sequence"):
                    continue
                if reject_counter(mapping is None, "no_mapping"):
                    continue

                cov = (mapping.q_en - mapping.q_st) / len(seq)
                acc = mapping.mlen / mapping.blen
                refseq = self.aligner.seq(mapping.ctg, mapping.r_st, mapping.r_en)
                
                if reject_counter(acc < self.min_accuracy, f"low_accuracy{self.min_accuracy:.2f}"):
                    continue
                if reject_counter(cov < self.min_coverage, f"low_coverage{self.min_coverage:.2f}"):
                    continue
                if reject_counter("N" in refseq, "N_in_sequence"):
                    continue

                self.output.write(AlignedSegment.fromstring(sam_record(read.read_id, seq, qstring, mapping, tags=tags), self.output.header))
                summary.append(summary_row(read, len(seq), mean_qscore, alignment=mapping))

                if mapping.strand == -1:
                    refseq = mappy.revcomp(refseq)
                    
                m_poss = defaultdict(list)
                #####################################################################
                # 方法一：根据remora标签标记单分子修饰状态
                modified_results = ctc_data.get("modified_results", [])
                flag = False
                if len(modified_results) > 0:
                    for can_base, code, modified_base in modified_results:
                        #can_base, code, modified_base = modified_results[0]
                        ml, r_poss = modified_base
                        #if reject_counter(sum(ml > 0.5) < 5, f"mlNone"): flag=True
                        
                        # for multi mod base
                        if reject_counter(len(ml) == 0, f"mlNone"): flag=True
                        sorted_indices = np.argsort(r_poss)
                        r_poss = r_poss[sorted_indices]
                        ml = ml[sorted_indices]
                        ml = ml.flatten()
                        assert len(ml) == len(r_poss)

                        l_poss = r_poss[ml < 0.5]
                        h_poss = r_poss[ml > 0.5]
                        
                        m_poss[can_base].append([h_poss, code])
                        
                        # if len(h_poss) == len(r_poss):
                        #     m_poss[can_base].append([h_poss, code])
                        #     if counter(len(h_poss) != 0, f"modbase_base{can_base}"): pass
                        # elif len(l_poss) == len(r_poss):
                        #     if counter(len(l_poss) != 0, f"can_base_base{can_base}"): pass
                        # else:
                        #     flag = True
                        
                processed_pos = set()
                for can_base in m_poss:
                    for poss, code in m_poss[can_base]:
                        if len(poss) == 0: flag = True
                        if processed_pos.intersection(poss):
                                flag = True
                        else:
                            processed_pos.update(poss)
                    
                if reject_counter(flag, f"modbase_base0"):
                    continue        

                    

                # 方法二：根据basecall结果取修饰reads
                # mod_prob = ctc_data.get("mod_prob", [])
                # if len(mod_prob) > 0 :
                #     assert len(mod_prob) == 1
                #     can_base, probs, mod_bases, motif = mod_prob[0]
                #     assert can_base == 'C'
                #     cigar = np.array(mapping.cigar)
                #     cigar = cigar[:, [1, 0]].tolist()
                #     if mapping.strand == -1:
                #         cigar = cigar[::-1]
                #     query_to_prob = np.arange(len(probs))
                #     ref_to_probs = data_chunks.compute_ref_to_signal(
                #         query_to_signal=query_to_prob,
                #         cigar=cigar,
                #     )
                #     if ref_to_probs.size != len(refseq) + 1:
                #         print(f"{read.read_id} discordant ref seq lengths: " f"move+cigar:{ref_to_probs.size} " f"ref_seq:{len(refseq)}", file=sys.stderr)
                #         raise ValueError("Discordant ref seq lengths")
                    
                #     ref_to_probs = ref_to_probs - ref_to_probs[0]
                #     refseq_probs = probs[ref_to_probs[0]:ref_to_probs[-1]]
                #     kmer_fillter = convert_base_name('CG')
                #     r_poss = np.array([x.start() for x in re.finditer(kmer_fillter, refseq)], dtype=int)
                #     m_poss = np.intersect1d(np.where(refseq_probs >= 0.95)[0], r_poss)

                #     if reject_counter(len(r_poss) > 1 and len(m_poss) == 0, f"modbase0"): continue

                ######################################################################

                base_to_int = {ord(x): str(i) for i, x in enumerate(self.alphabet)}
                target = np.array([int(x) for x in refseq.translate(base_to_int)])
                
                cano_base_to_int = {ord(x): str(i) for i, x in enumerate('NACGT')}
                target_canonical = np.array([int(x) for x in refseq.translate(cano_base_to_int)])
                
                if len(m_poss) > 0:
                    for can_base in m_poss:
                        for poss, code in m_poss[can_base]:
                            target[poss] = self.args.alphabet.index(code)

                
                # if self.args.mod:
                #     # CG -> ZG
                #     target_bytes = bytes(target)
                #     c_inx = self.args.alphabet.index('C')
                #     z_inx = self.args.alphabet.index('Z')
                #     g_inx = self.args.alphabet.index('G')
                #     old_bytes = bytes([c_inx, g_inx])
                #     new_bytes = bytes([z_inx, g_inx])
                #     replaced_bytes = target_bytes.replace(old_bytes, new_bytes)
                #     target = list(replaced_bytes)

                # RNA basecall already reversed. Flip back to signal-oriented for training.
                targets.append(target[::-1] if self.rna else target)
                cano_targets.append(target_canonical[::-1] if self.rna else target_canonical)
                chunks.append(read.signal)
                lengths.append(len(target))
                if ctc_inx % 10000 == 0:
                    pprint(f"current chunks: {len(targets)}")
                    
                if len(lengths) >= self.max_chunks: 
                    pprint("reach max chunks")
                    break


        if len(chunks) == 0:
            sys.stderr.write("> no suitable ctc data to write\n")
            return

        chunks = np.array(chunks, dtype=np.float16)
        targets_ = np.zeros((chunks.shape[0], max(lengths)), dtype=np.uint8)
        for idx, target in enumerate(targets):
            targets_[idx, : len(target)] = target
          
        cano_targets_ = np.zeros((chunks.shape[0], max(lengths)), dtype=np.uint8)  
        for idx, target_canonical in enumerate(cano_targets):
            cano_targets_[idx, : len(target_canonical)] = target_canonical
            
        lengths = np.array(lengths, dtype=np.uint16)
        indices = np.random.permutation(typical_indices(lengths))

        chunks = chunks[indices]
        targets_ = targets_[indices]
        cano_targets_ = cano_targets_[indices]
        lengths = lengths[indices]

        summary = pd.read_csv(summary_file(), sep="\t")
        summary.iloc[indices].to_csv(summary_file(), sep="\t", index=False)

        output_directory = "." if sys.stdout.isatty() else dirname(realpath("/dev/fd/1"))
        np.save(os.path.join(output_directory, "chunks.npy"), chunks)
        if self.alphabet != 'NACGT':
            np.save(os.path.join(output_directory, "mod_references.npy"), targets_)
        np.save(os.path.join(output_directory, "references.npy"), cano_targets_)
        np.save(os.path.join(output_directory, "reference_lengths.npy"), lengths)

        sys.stderr.write("> Chunks rejected from training data:\n")
        for condition_name, count in reject_counter.items():
            sys.stderr.write(f" - {condition_name}: {count}\n")
        for condition_name, count in counter.items():
            sys.stderr.write(f" - {condition_name}: {count}\n")
        sys.stderr.write(f"> written ctc training data to {output_directory}\n")
        sys.stderr.write("  - chunks.npy with shape (%s)\n" % ",".join(map(str, chunks.shape)))
        sys.stderr.write("  - references.npy with shape (%s)\n" % ",".join(map(str, cano_targets_.shape)))
        if self.alphabet != 'NACGT':
            sys.stderr.write("  - mod_references.npy with shape (%s)\n" % ",".join(map(str, targets_.shape)))
        sys.stderr.write("  - reference_lengths.npy shape (%s)\n" % ",".join(map(str, lengths.shape)))
        
        if self.alphabet != 'NACGT':
            labels, counts = np.unique(targets_, return_counts=True)
        else:
            labels, counts = np.unique(cano_targets_, return_counts=True)
            
        base_count_dict = {self.args.alphabet[label]: count for label, count in zip(labels, counts)}
        pprint(base_count_dict)
        


            
            
            
    def stop(self):
        
        self.join()

def reverse_mod_gaps(gaps, seq, can_base):
    
    """
    Reverse mod_gaps to get mod_poss.

    Args:
        mod_gaps (str): String of modified base gaps.
        seq (str): Read sequence.
        can_base (str): Canonical base.

    Returns:
        np.ndarray: Array of modified base positions.
    """


    # 计算 can_base_mod_poss
    can_base_mod_poss = np.cumsum(gaps + 1) - 1

    # 计算规范碱基的累积计数
    can_base_cum_count = np.cumsum([1 if b == can_base else 0 for b in seq])

    mod_poss = []
    for target_count in can_base_mod_poss:
        # 使用二分查找找到第一个累积计数大于等于目标计数的位置
        pos = np.searchsorted(can_base_cum_count, target_count + 1)
        if pos < len(seq) and can_base_cum_count[pos] == target_count + 1:
            mod_poss.append(pos)

    return np.array(mod_poss)