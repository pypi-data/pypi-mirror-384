#!/usr/bin/env python3

"""
modified based on Bonito training.
"""

import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
os.environ["TOKENIZERS_PARALLELISM"] = "true"

from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter
from pathlib import Path
from importlib import import_module
from torch.utils.data import BatchSampler, SubsetRandomSampler, Sampler
from densecall.data import load_numpy, load_script, SequentialSampler
from densecall.util import load_model, load_symbol, init, half_supported
from bonito.util import __models_dir__, default_config
default_config = os.path.join(__models_dir__, "configs/dna_r9.4.1@v3.1.toml")
from densecall.training import load_state, Trainer
from densecall.data import load_numpy, load_script, SequentialSampler

import toml
import torch
import numpy as np
from torch.utils.data import DataLoader
import stat
import shutil
import torch._dynamo
torch._dynamo.config.suppress_errors = True



def main(args):

    workdir = os.path.expanduser(args.training_directory)
    if args.new and os.path.exists(workdir):
        # Prompt the user for confirmation
        confirm = input(f"Are you sure you want to delete the directory {workdir}? Enter 'y' to confirm, any other key to cancel: ").strip().lower()
        if confirm == 'y':
            shutil.rmtree(workdir, ignore_errors=True)
            print(f"Directory {workdir} has been deleted.")
        else:
            print("Deletion operation cancelled.")

    if os.path.exists(workdir) and not args.force:
        print("[error] %s exists, use -f to force continue training." % workdir)
        exit(1)

    init(args.seed, args.device, (not args.nondeterministic))
    device = torch.device(args.device)

    if not args.pretrained:
        config = toml.load(args.config)
    else:
        dirname = args.pretrained
        if not os.path.isdir(dirname) and os.path.isdir(os.path.join(__models_dir__, dirname)):
            dirname = os.path.join(__models_dir__, dirname)
        pretrain_file = os.path.join(dirname, 'config.toml')
        config = toml.load(pretrain_file)
        if 'lr_scheduler' in config:
            print("[ignoring 'lr_scheduler' in --pretrained config]")
            del config['lr_scheduler']
            
    if args.alphabet:
        def update_alphabet(data):
            if isinstance(data, dict):
                return {k: args.alphabet if k == 'alphabet' else update_alphabet(v) for k, v in data.items()}
            if isinstance(data, list):
                return [update_alphabet(x) for x in data]
            return data
        
        config = update_alphabet(config)
        
    argsdict = dict(training=vars(args))

    print("[loading model]")
    if args.pretrained:
        print("[using pretrained model {}]".format(args.pretrained))
        model = load_model(args.pretrained, device, half=False)
    else:
        try:
            if config.get("name") == "wav2vec2":
                model = load_symbol(config, 'PretrainedModel')(config)
            else:
                model = load_symbol(config, 'Model')(config)
        except Exception as e:
            print(f"[error] failed to load model: {e}")
            exit(1)
    
    
        
    teacher_model = None   
    if args.teacher:
        print("[loading teacher model]")
        print("[using teacher model {}]".format(args.teacher))
        teacher_model = load_model(args.teacher, device, half=False)
        for param in teacher_model.parameters():
            param.requires_grad = False
            

    
    print("[loading data]")
    try:
        train_loader_kwargs, valid_loader_kwargs = load_numpy(
            args.chunks, args.directory, valid_chunks = args.valid_chunks, mod=not(args.alphabet=='NACGT')
        )
    except FileNotFoundError:
        train_loader_kwargs, valid_loader_kwargs = load_script(
            args.directory,
            seed=args.seed,
            chunks=args.chunks,
            valid_chunks=args.valid_chunks,
            n_pre_context_bases=getattr(model, "n_pre_context_bases", 0),
            n_post_context_bases=getattr(model, "n_post_context_bases", 0),
        )

    loader_kwargs = {
        "num_workers": args.num_workers, "pin_memory": True, "prefetch_factor":2, "persistent_workers": True
    }
    
    train_sampler = SubsetRandomSampler(indices=np.arange(0, len(train_loader_kwargs['dataset']))[:args.chunks])
    train_batch_sampler = BatchSampler(train_sampler, batch_size=args.batch, drop_last=True)
    
    valid_sampler = SequentialSampler(valid_loader_kwargs['dataset'], chunks=args.valid_chunks)
    valid_batch_sampler = BatchSampler(valid_sampler, batch_size=args.batch//args.grad_accum_split, drop_last=True)
    
    train_loader = DataLoader(**train_loader_kwargs, batch_sampler=train_batch_sampler, **loader_kwargs)
    valid_loader = DataLoader(**valid_loader_kwargs, batch_sampler=valid_batch_sampler, **loader_kwargs)


    os.makedirs(workdir, exist_ok=True)
    toml.dump({**config, **argsdict}, open(os.path.join(workdir, 'config.toml'), 'w'))

    if config.get("lr_scheduler"):
        sched_config = config["lr_scheduler"]
        lr_scheduler_fn = getattr(
            import_module(sched_config["package"]), sched_config["symbol"]
        )(**sched_config)
    else:
        lr_scheduler_fn = None

    trainer = Trainer(
        model, device, train_loader, valid_loader,
        use_amp=half_supported() and not args.no_amp,
        lr_scheduler_fn=lr_scheduler_fn,
        restore_optim=args.restore_optim,
        save_optim_every=args.save_optim_every,
        grad_accum_split=args.grad_accum_split,
        pretrain_grad_accum_split=args.pretrain_grad_accum_split,
        pretrain_epochs=args.pretrain_epochs,
        pretrain = args.pretrain,
        pretrained_file = args.pretrained_file,
        quantile_grad_clip=args.quantile_grad_clip,
        config = config,
        teacher_model = teacher_model,
        compile = args.compile
    )

    if (',' in args.lr):
        lr = [float(x) for x in args.lr.split(',')]
    else:
        lr = float(args.lr)
    trainer.fit(workdir, args.epochs, lr)

def argparser():
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        add_help=False
    )
    parser.add_argument("training_directory")
    group = parser.add_mutually_exclusive_group()
    parser.add_argument('--compile', action="store_true", default=False)
    parser.add_argument('--teacher', default=None)
    group.add_argument('--config', default=default_config)
    group.add_argument('--pretrained', default="")
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--lr", default='2e-3')
    parser.add_argument("--seed", default=25, type=int)
    parser.add_argument("--epochs", default=5, type=int)
    parser.add_argument("--batch", default=64, type=int)
    parser.add_argument("--num-workers", default=4, type=int)
    parser.add_argument("--chunks", default=None, type=int)
    parser.add_argument("--valid-chunks", default=None, type=int)
    parser.add_argument("--no-amp", action="store_true", default=False)
    parser.add_argument("-f", "--force", action="store_true", default=False)
    parser.add_argument("--restore-optim", action="store_true", default=False)
    parser.add_argument("--nondeterministic", action="store_true", default=False)
    parser.add_argument("--save-optim-every", default=1, type=int)
    parser.add_argument("--grad-accum-split", default=1, type=int)
    parser.add_argument("--pretrain-grad-accum-split", default=1, type=int)
    parser.add_argument("--pretrain-epochs", default=100, type=int)
    parser.add_argument("--pretrain", action="store_true", default=False)
    parser.add_argument("--pretrained-file", default=None)
    quantile_group = parser.add_mutually_exclusive_group()
    quantile_group.add_argument('--quantile-grad-clip', dest='quantile_grad_clip', action='store_true')
    quantile_group.add_argument('--no-quantile-grad-clip', dest='quantile_grad_clip', action='store_false')
    quantile_group.set_defaults(quantile_grad_clip=True)
    parser.add_argument("--alphabet", default='NACGT')
    parser.add_argument("--new", action="store_true", default=False)
    return parser

if __name__ == "__main__":
    args = argparser().parse_args()
    main(args)
