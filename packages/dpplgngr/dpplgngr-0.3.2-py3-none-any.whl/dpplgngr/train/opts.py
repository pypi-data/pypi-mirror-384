# -*- coding: utf-8 -*-
"""Process all the options"""

__author__ = "Sean Benson"
__copyright__ = "MIT"

import json
import argparse


def init_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-size',
                        help='Batch size to use for training',
                        default=32,
                        type=int,
                        nargs='?',
                        )
    parser.add_argument('--epochs',
                        help='Number of epochs to train for',
                        default=1,
                        type=int,
                        nargs='?',
                        )
    parser.add_argument('--seed',
                        help='Reproduce results with a certain seed',
                        default=42,
                        type=int,
                        nargs='?',
                        )
    parser.add_argument('--model',
                        help="Which model do we want",
                        type=str,
                        nargs='?',
                        default="nominal",
                        )
    parser.add_argument('--load_json',
                        help="Specify args with a json",
                        type=str,
                        nargs='?',
                        default="",
                        )
    parser.add_argument('--dset',
                        help="Which dataset to use",
                        type=str,
                        nargs='?',
                        default="ltp",
                        )
    return parser
