#!/usr/bin/env python3

import time

from pan import *

# setup logging
logging.basicConfig(
    level = logging.INFO,
    format = '[%(asctime)s] %(levelname)s: %(message)s',
    datefmt = '%d/%m %H:%M:%S'
)
logging.info("welcome to this test")

# prepare test family
sequences = read_fasta("testfams/testfam.fasta")
genes = [s.id for s in sequences]

# run ficlin
t0 = time.time()
clusters = run_ficlin(sequences, n_clusters = 30, dout_tmp = "tmp", threads = 1)
t1 = time.time()
logging.info(f"time: {t1 - t0}")

# # select representatives
# genes_reps = select_reps(genes, clusters, sequences)
# write_tsv(genes_reps, "genes_reps.tsv")
# 
# # write representatives as fasta 
# reps = [s for s in sequences if s.id in genes_reps["rep"].unique().tolist()]
# write_fasta(reps, "reps.fasta")
