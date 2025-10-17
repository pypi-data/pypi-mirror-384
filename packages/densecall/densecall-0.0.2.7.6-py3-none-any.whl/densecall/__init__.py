from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from densecall.cli import train, basecaller, accuracy
import os

modules = [
    'accuracy', 'train','basecaller'
]

__version__ = '0.0.2.7.6'




def main():
    parser = ArgumentParser(
        'densecall',
        formatter_class=ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '-v', '--version', action='version',
        version='%(prog)s {}'.format(__version__)
    )

    subparsers = parser.add_subparsers(
        title='subcommands', description='valid commands',
        help='additional help', dest='command'
    )
    subparsers.required = True

    for module in modules:
        mod = globals()[module]
        p = subparsers.add_parser(module, parents=[mod.argparser()])
        p.set_defaults(func=mod.main)

    args = parser.parse_args()
    args.func(args)
