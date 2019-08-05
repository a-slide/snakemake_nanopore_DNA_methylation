__author__ = "Adrien Leger"
__copyright__ = "Copyright 2019, Adrien Leger"
__email__ = "aleg@ebi.ac.uk"
__license__ = "MIT"

# Imports
import os
from snakemake.shell import shell

# Get optional args if unavailable
opt_nanopolish = snakemake.params.get("opt_nanopolish", "")
opt_nanopolishcomp = snakemake.params.get("opt_nanopolishcomp", "")

# Get outdir and outprefix for Freq_meth_calculate
outdir = os.path.dirname(snakemake.output.bed)
outprefix = os.path.basename(snakemake.output.bed).replace("_freq_meth_calculate.bed", "")

# Run shell commands
shell("echo '#### NANOPOLISH INDEX LOG ####' > {snakemake.log}")
shell("nanopolish index -d {snakemake.input.fast5} {snakemake.input.fastq} -s {snakemake.input.seq_summary} -v 2>> {snakemake.log}")

shell("echo '#### NANOPOLISH CALL-METHYLATION LOG ####' > {snakemake.log}")
shell("nanopolish call-methylation -t {snakemake.threads} {opt_nanopolish} -r {snakemake.input.fastq} -b {snakemake.input.bam} -g {snakemake.input.ref} > {snakemake.output.call} 2>> {snakemake.log}")

shell("echo '#### NANOPOLISHCOMP FREQ_METH_CALCULATE LOG ####' >> {snakemake.log}")
shell("NanopolishComp Freq_meth_calculate {opt_nanopolishcomp} -i {snakemake.output.call} -o {outdir} -p {outprefix} 2>> {snakemake.log}")
