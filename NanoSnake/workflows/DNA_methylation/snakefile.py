# -*- coding: utf-8 -*-

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Imports~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# Std lib
from glob import glob
from os import path
import yaml

# Third party lib
import pandas as pd
from snakemake.utils import min_version

# set minimum snakemake version
min_version("5.4.2")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Load sample sheets~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

sample_df = pd.read_csv (config["sample_sheet"], comment="#", skip_blank_lines=True, sep="\t", index_col=0)
sample_list = list(sample_df.index)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Getters~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

def get_fastq (wildcards):
    return sample_df.loc[wildcards.sample, "fastq"]

def get_fast5 (wildcards):
    return sample_df.loc[wildcards.sample, "fast5"]

def get_seq_summary (wildcards):
    return sample_df.loc[wildcards.sample, "seq_summary"]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Top Rules~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

rule all:
    input:
        expand(path.join("results","merge_filter_fastq","{sample}.fastq"), sample=sample_list),
        expand(path.join("results","pycoqc","{sample}_pycoqc.html"), sample=sample_list),
        expand(path.join("results","pycoqc","{sample}_pycoqc.json"), sample=sample_list),
        expand(path.join("results","minimap2_index","ref.mmi")),
        expand(path.join("results","minimap2_align", "{sample}.bam"), sample=sample_list),
        expand(path.join("results","bamqc","{sample}","qualimapReport.html"), sample=sample_list),
        expand(path.join("results","bamqc","{sample}_samtools_stats.txt"), sample=sample_list),
        expand(path.join("results","bamqc","{sample}_samtools_flagstat.txt"), sample=sample_list),
        expand(path.join("results","bamqc","{sample}_samtools_idxstats.txt"), sample=sample_list),
        expand(path.join("results","samtools_filter", "{sample}.bam"), sample=sample_list),
        expand(path.join("results","genomecov","{sample}.bedgraph"), sample=sample_list),
        expand(path.join("results", "merge_filter_fastq","{sample}.fastq.index"), sample=sample_list),
        expand(path.join("results", "merge_filter_fastq","{sample}.fastq.index.fai"), sample=sample_list),
        expand(path.join("results", "merge_filter_fastq","{sample}.fastq.index.gzi"), sample=sample_list),
        expand(path.join("results", "merge_filter_fastq","{sample}.fastq.index.readdb"), sample=sample_list),
        expand(path.join("results", "nanopolish_call_methylation","{sample}_call_methylation.tsv"), sample=sample_list),
        expand(path.join("results", "nanopolish_call_methylation","{sample}_freq_meth_calculate.bed"), sample=sample_list),
        expand(path.join("results", "nanopolish_call_methylation","{sample}_freq_meth_calculate.tsv"), sample=sample_list),

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Rules~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

rule merge_filter_fastq:
    input: get_fastq
    output: path.join("results","merge_filter_fastq","{sample}.fastq")
    log: path.join("logs","merge_filter_fastq","{sample}.log")
    threads: config["merge_filter_fastq"].get("threads", 1)
    params: opt=config["merge_filter_fastq"].get("opt", "")
    resources: mem_mb=config["merge_filter_fastq"].get("mem", 1000)
    wrapper: "merge_filter_fastq"

rule pycoqc:
    input:
        seq_summary = get_seq_summary
    output:
        html=path.join("results","pycoqc","{sample}_pycoqc.html"),
        json=path.join("results","pycoqc","{sample}_pycoqc.json")
    log: path.join("logs", "pycoqc","{sample}_pycoqc.log")
    threads: config["pycoqc"].get("threads", 2)
    params: opt=config["pycoqc"].get("opt", "")
    resources: mem_mb=config["pycoqc"].get("mem", 1000)
    wrapper: "pycoqc"

rule minimap2_index:
    input: config["reference"]
    output: path.join("results","minimap2_index","ref.mmi")
    log: path.join("logs","minimap2_index","ref.log")
    threads: config["minimap2_index"].get("threads", 1)
    params: opt=config["minimap2_index"].get("opt", "")
    resources: mem_mb=config["minimap2_index"].get("mem", 1000)
    wrapper: "minimap2_index"

rule minimap2_align:
    input:
        index=rules.minimap2_index.output,
        fastq=rules.merge_filter_fastq.output
    output: path.join("results","minimap2_align","{sample}.bam")
    log: path.join("logs","minimap2_align","{sample}.log")
    threads: config["minimap2_align"].get("threads", 4)
    params: opt=config["minimap2_align"].get("opt", "")
    resources: mem_mb=config["minimap2_align"].get("mem", 1000)
    wrapper: "minimap2_align"

rule bamqc:
    input: rules.minimap2_align.output,
    output:
        qualimap=path.join("results","bamqc","{sample}","qualimapReport.html"),
        stats=path.join("results","bamqc","{sample}_samtools_stats.txt"),
        flagstat=path.join("results","bamqc","{sample}_samtools_flagstat.txt"),
        idxstats=path.join("results","bamqc","{sample}_samtools_idxstats.txt"),
    log: path.join("logs","bamqc","{sample}.log")
    threads: config["bamqc"].get("threads", 1)
    params: opt=config["bamqc"].get("opt", "")
    resources: mem_mb=config["bamqc"].get("mem", 1000)
    wrapper: "bamqc"

rule samtools_filter:
    input: rules.minimap2_align.output
    output: path.join("results","samtools_filter","{sample}.bam")
    log: path.join("logs","samtools_filter","{sample}.log")
    threads: config["samtools_filter"].get("threads", 2)
    params: opt=config["samtools_filter"].get("opt", "")
    resources: mem_mb=config["samtools_filter"].get("mem", 1000)
    wrapper: "samtools_filter"

rule genomecov:
    input: rules.samtools_filter.output
    output: path.join("results","genomecov","{sample}.bedgraph")
    log: path.join("logs","genomecov","{sample}.log")
    threads: config["genomecov"].get("threads", 1)
    params: opt=config["genomecov"].get("opt", "")
    resources: mem_mb=config["genomecov"].get("mem", 1000)
    wrapper: "genomecov"

rule nanopolish_call_methylation:
    input:
        fastq = rules.merge_filter_fastq.output,
        fast5 = get_fast5,
        seq_summary = get_seq_summary,
        bam = rules.samtools_filter.output,
        ref = config["reference"],
    output:
        call = path.join("results", "nanopolish_call_methylation","{sample}_call_methylation.tsv"),
        bed = path.join("results", "nanopolish_call_methylation","{sample}_freq_meth_calculate.bed"),
        tsv = path.join("results", "nanopolish_call_methylation","{sample}_freq_meth_calculate.tsv"),
    log: path.join("logs","nanopolish_call_methylation","{sample}.log")
    threads: config["nanopolish_call_methylation"].get("threads", 2)
    params:
        opt_nanopolish=config["nanopolish_call_methylation"].get("opt_nanopolish", ""),
        opt_nanopolishcomp=config["nanopolish_call_methylation"].get("opt_nanopolishcomp", ""),
    resources: mem_mb=config["nanopolish_call_methylation"].get("mem", 1000)
    wrapper: "nanopolish_call_methylation"
