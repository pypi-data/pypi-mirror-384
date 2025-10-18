#!/usr/bin/env python3

from pan import *
from readerswriters import *

# setup logging
logging.basicConfig(
    level = logging.INFO,
    format = '[%(asctime)s] %(levelname)s: %(message)s',
    datefmt = '%d/%m %H:%M:%S'
)
logging.info("welcome to this test")

# prepare the pan object
sequences = read_fasta("testfams/testfam.fasta")
sequences = sequences[0:100]
write_fasta(sequences, "testfams/testfam_sub.fasta")
genes = [seq.id for seq in sequences]
pan = read_genes("testfams/pangenome.tsv")
pan = pan.loc[pan.gene.isin(genes)]
pan["orthogroup"] = "testfam_sub" 

# test superfamily splitting on pan object
pan = split_superfamily(pan, "FH", "testfams", 1, "tmp")

# check output
print(pan)
# write_tsv(pan, "testfams/pangenome_result.tsv")
