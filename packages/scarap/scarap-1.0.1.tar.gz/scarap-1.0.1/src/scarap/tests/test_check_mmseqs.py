#!/usr/bin/env python3

from pan import *
from checkers import check_mmseqs

# setup logging
logging.basicConfig(
    level = logging.INFO,
    format = '[%(asctime)s] %(levelname)s: %(message)s',
    datefmt = '%d/%m %H:%M:%S'
)
logging.info("welcome to this test")

# prepare the pan object
check_mmseqs()
