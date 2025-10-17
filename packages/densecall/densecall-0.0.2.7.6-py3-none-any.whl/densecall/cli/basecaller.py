"""
modified based on Bonito Basecaller
"""

import os
import sys
import numpy as np
from tqdm import tqdm
from time import perf_counter
from functools import partial
from datetime import timedelta
from itertools import islice as take
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import mappy
from densecall.aligner import align_map, Aligner
from densecall.reader import read_chunks, Reader
from densecall.io import CTCWriter, Writer, biofmt
from densecall.mod_util import call_mods, load_mods_model
from bonito.cli.download import Downloader, models
from densecall.util import __models_dir__
#print(__models_dir__)
from densecall.multiprocessing import process_cancel, process_itemmap
from densecall.util import column_to_set, load_symbol, load_model, init
import torch
import torch._dynamo



def main(args):

    init(args.seed, args.device)

    try:
        reader = Reader(args.reads_directory, args.recursive)
        sys.stderr.write("> reading %s\n" % reader.fmt)
    except FileNotFoundError:
        sys.stderr.write("> error: no suitable files found in %s\n" % args.reads_directory)
        exit(1)

    fmt = biofmt(aligned=args.reference is not None)

    if args.reference and args.reference.endswith(".mmi") and fmt.name == "cram":
        sys.stderr.write("> error: reference cannot be a .mmi when outputting cram\n")
        exit(1)
    elif args.reference and fmt.name == "fastq":
        sys.stderr.write(f"> warning: did you really want {fmt.aligned} {fmt.name}?\n")
    else:
        sys.stderr.write(f"> outputting {fmt.aligned} {fmt.name}\n")

    if args.model_directory in models and not (__models_dir__ / args.model_directory).exists():
        sys.stderr.write("> downloading model\n")
        Downloader(__models_dir__).download(args.model_directory)

    sys.stderr.write(f"> loading model {args.model_directory}\n")
    try:
        model = load_model(
            args.model_directory,
            args.device,
            weights=args.weights if args.weights > 0 else None,
            chunksize=args.chunksize,
            overlap=args.overlap,
            batchsize=args.batchsize,
            quantize=args.quantize,
            use_koi=not(args.no_koi),
        )
    
    
    except FileNotFoundError:
        sys.stderr.write(f"> error: failed to load {args.model_directory}\n")
        sys.stderr.write(f"> available models:\n")
        for model in sorted(models): sys.stderr.write(f" - {model}\n")
        exit(1)
       
    if args.compile: 
        model = torch.compile(model)

    if args.verbose:
        sys.stderr.write(f"> model basecaller params: {model.config['basecaller']}\n")

  
    if  (not args.mod) or model.alphabet == 'NACGT' or ''.join(model.alphabet) == 'NACGT':
        sys.stderr.write(f"> using standard basecall\n")
        basecall = load_symbol(args.model_directory, "basecall")
    else:
        sys.stderr.write(f"> using modified basecall\n")
        basecall = load_symbol(args.model_directory, "basecall_mod")

    mods_model = []
    if args.modified_base_model is not None or args.modified_bases is not None:
        sys.stderr.write("> loading remora models\n")
        assert len(args.modified_base_model) == len(args.modified_codes)
        assert all(char in args.alphabet for char in args.modified_codes)
        for modified_base_model, code in zip(args.modified_base_model, args.modified_codes):
            modified_base_model = os.path.abspath(os.path.expanduser(modified_base_model))
            sys.stderr.write(f"> {modified_base_model}\n")
            mods_model_ = load_mods_model(
                None, args.model_directory, modified_base_model,
                device=args.modified_device,
            )
            assert mods_model_[1]['can_base'] in args.alphabet
            mods_model.append((mods_model_, code))
            remora_model, remora_metadata = mods_model_
            sys.stderr.write(f"> {remora_metadata}\n")
            sys.stderr.write(f"> {mods_model_[1]['alphabet_str']}\n")    

    if args.reference:
        sys.stderr.write("> loading reference\n")
        if args.min_accuracy_save_ctc < 0.65:
            sys.stderr.write("> k=7 for min_accuracy_save_ctc < 0.65\n")
            if args.chunksize < 12000: 
                raise ValueError("k=7 is not supported for chunksize < 12000")
            aligner = Aligner(args.reference, preset=args.mm2_preset, best_n=1, scoring=[1, 1, 1, 1, 1, 1], k=7)
        else:
            aligner = Aligner(args.reference, preset=args.mm2_preset, best_n=1)
            
        # if args.rna:
        #     aligner = Aligner(args.reference, preset='map-ont', best_n=1, scoring=[2, 2, 1, 1, 32, 0], k=13, w=4, min_cnt=1, min_chain_score = 15, min_dp_score=30)
        #     #: -k13 -w4 -n1 -m15 -s30 -A2 -B2 -O1,32 -E1,0.
        
        # if args.r10:
        #     aligner = Aligner(args.reference, preset='map-ont', best_n=1, k=19, w=19, min_cnt=1, min_chain_score = 15, min_dp_score=30)
        #     #: -x map-ont -k19 -w 19 -U50,500 -g10k
        
        if not aligner:
            sys.stderr.write("> failed to load/build index\n")
            exit(1)
    else:
        aligner = None

    if args.save_ctc and not args.reference:
        sys.stderr.write("> a reference is needed to output ctc training data\n")
        exit(1)

    if fmt.name != 'fastq':
        groups, num_reads = reader.get_read_groups(
            args.reads_directory, args.model_directory,
            n_proc=8, recursive=args.recursive,
            read_ids=column_to_set(args.read_ids), skip=args.skip,
            cancel=process_cancel()
        )
    else:
        groups = []
        num_reads = None

    #sys.stderr.write(f"> scaling: {model.config.get('scaling')}\n")
    reads = reader.get_reads(
        args.reads_directory, n_proc=8, recursive=args.recursive,
        read_ids=column_to_set(args.read_ids), skip=args.skip,
        do_trim=not args.no_trim,
        scaling_strategy=model.config.get("scaling"),
        norm_params=(model.config.get("standardisation")
                     if (model.config.get("scaling") and
                         model.config.get("scaling").get("strategy") == "pa")
                     else model.config.get("normalisation")
                     ),
        cancel=process_cancel()
    )

    if args.verbose:
        sys.stderr.write(f"> read scaling: {model.config.get('scaling')}\n")
    
    if args.max_reads:
        reads = take(reads, args.max_reads)

    if args.save_ctc:
        reads = (
            chunk for read in reads
            for chunk in read_chunks(
                read,
                chunksize=model.config["basecaller"]["chunksize"],
                overlap=model.config["basecaller"]["overlap"]
            )
        )
        ResultsWriter = CTCWriter
    else:
        ResultsWriter = Writer
      
    results = basecall(
        model, reads, reverse=args.revcomp, rna=args.rna,
        batchsize=model.config["basecaller"]["batchsize"],
        chunksize=model.config["basecaller"]["chunksize"],
        overlap=model.config["basecaller"]["overlap"]
    )

            
    if aligner:
        results = align_map(aligner, results, n_thread=args.alignment_threads, mod_model = mods_model, use_reference_anchored = args.save_ctc)

    writer_kwargs = {'aligner': aligner,
                     'group_key': args.model_directory,
                     'ref_fn': args.reference,
                     'groups': groups,
                     'min_qscore': args.min_qscore,
                     'args': args}
    
    if args.save_ctc:
        writer_kwargs['rna'] = args.rna
        writer_kwargs['min_accuracy'] = args.min_accuracy_save_ctc
        writer_kwargs['min_coverage'] = args.min_coverage
        if args.tail:
            writer_kwargs['end_quantile'] = 0.9
        if args.head:
            writer_kwargs['start_quantile'] = 0.1
            
        
    writer = ResultsWriter(
        fmt.mode, tqdm(results, desc="> calling", unit=" reads", leave=False,
                       total=num_reads, smoothing=0, ascii=True, ncols=100),
        **writer_kwargs)

    t0 = perf_counter()
    writer.start()
    writer.join()
    duration = perf_counter() - t0
    num_samples = sum(num_samples for read_id, num_samples in writer.log)

    sys.stderr.write("> completed reads: %s\n" % len(writer.log))
    sys.stderr.write("> duration: %s\n" % timedelta(seconds=np.round(duration)))
    sys.stderr.write("> samples per second %.1E\n" % (num_samples / duration))
    sys.stderr.write("> done\n")


def argparser():
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        add_help=False
    )
    parser.add_argument("model_directory")
    parser.add_argument("reads_directory")
    parser.add_argument("--compile", action="store_true", default=False)
    parser.add_argument("--reference")
    parser.add_argument("--modified-bases", nargs="+")
    parser.add_argument("--modified-codes", type=lambda s: s.split(','))
    parser.add_argument("--modified-base-model", type=lambda s: s.split(','), help="Comma-separated list of modified base models")
    parser.add_argument("--modified-procs", default=8, type=int)
    parser.add_argument("--modified-device", default='cuda')
    parser.add_argument("--read-ids")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--seed", default=25, type=int)
    parser.add_argument("--weights", default=0, type=int)
    parser.add_argument("--skip", action="store_true", default=False)
    parser.add_argument("--no-koi", action="store_true", default=False)
    parser.add_argument("--no-trim", action="store_true", default=False)
    parser.add_argument("--save-ctc", action="store_true", default=False)
    parser.add_argument("--revcomp", action="store_true", default=False)
    parser.add_argument("--rna", action="store_true", default=False)
    parser.add_argument("--recursive", action="store_true", default=False)
    quant_parser = parser.add_mutually_exclusive_group(required=False)
    quant_parser.add_argument("--quantize", dest="quantize", action="store_true")
    quant_parser.add_argument("--no-quantize", dest="quantize", action="store_false")
    parser.set_defaults(quantize=None)
    parser.add_argument("--overlap", default=600, type=int)
    parser.add_argument("--chunksize", default=5000, type=int)
    parser.add_argument("--batchsize", default=None, type=int)
    parser.add_argument("--max-reads", default=0, type=int)
    parser.add_argument("--min-qscore", default=0, type=int)
    parser.add_argument("--mm2-preset", default='map-ont', type=str)
    parser.add_argument("--min-accuracy-save-ctc", default=0.99, type=float)
    parser.add_argument("--min-coverage", default=0.9, type=float)
    parser.add_argument("--tail", action="store_true", default=False, help="call tail of signal")
    parser.add_argument("--head", action="store_true", default=False, help="call head of signal")
    parser.add_argument("--alignment-threads", default=8, type=int)
    parser.add_argument("--alphabet", default="NACGT", type=str)
    parser.add_argument("--mod", action="store_true", default=False, help="basecall modified bases")
    parser.add_argument("--output-resquiggle", action="store_true", default=False, help="output resquiggle into sam file")
    parser.add_argument('-v', '--verbose', action='count', default=0)
    return parser
