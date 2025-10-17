#!/usr/bin/env python
#
# RODAN
# v1.0
# (c) 2020,2021,2022 Don Neumann
#
# for both RNA and DNA:
# minimap2 --secondary=no -ax map-ont -t 32 --cs genomefile fastafile > file.sam
#

import re, sys, argparse, pysam, os
import numpy as np
import subprocess
from argparse import ArgumentDefaultsHelpFormatter
import pandas as pd 
import matplotlib.pyplot as plt 
import seaborn as sns 
from tabulate import tabulate
#from numba import jit, njit
#plt.rcParams["font.sans-serif"] = "Noto Sans CJK JP"
def parse_cs_tag(tag, refseq, readseq, debug=False):
    ret = ""
    match = 0
    mismatch = 0
    deletions = 0
    insertions = 0
    refpos = 0
    readpos = 0
    refstr = ""
    readstr = ""
    p = re.findall(r":([0-9]+)|(\*[a-z][a-z])|(=[A-Za-z]+)|(\+[A-Za-z]+)|(\-[A-Za-z]+)", tag)
    for i, x in enumerate(p):
        #print(x)
        if len(x[0]):
            q = int(x[0])
            if debug: print("match:", i, q)
            match+= int(q)
            refstr+=refseq[refpos:refpos+q]
            refpos+=q
            readstr+=readseq[readpos:readpos+q]
            readpos+=q
            ret+= "|" * q
        if len(x[1]):
            q = int((len(x[1])-1)/2)
            if debug: print("mismatch:", i, q)
            mismatch+= q
            refstr+=refseq[refpos:refpos+q]
            refpos+=q
            readstr+=readseq[readpos:readpos+q]
            readpos+=q
            ret+= "*" * q
        if len(x[2]):
            if debug: print("FAIL")
        if len(x[3]):
            q = len(x[3])-1
            if debug: print("insertion:", i, q, x[3])
            insertions+=q
            refstr+="-"*q
            readstr+=readseq[readpos:readpos+q]
            readpos+=q
            ret+= " " * q
        if len(x[4]):
            q = len(x[4])-1
            if debug: print("deletion:", i, q)
            deletions+=q
            refstr+=refseq[refpos:refpos+q]
            refpos+=q
            readstr+="-"*q
            ret+= " " * q
    if debug:
        print("match:", match, "mismatch:", mismatch, "deletions:", deletions, "insertions:", insertions)
        print(len(refstr), len(ret), len(readstr))
        print(refstr[:80])
        print(ret[:80])
        print(readstr[:80])
    tot = match+mismatch+deletions+insertions
    totfail = mismatch+deletions+insertions
    return tot, totfail, match/tot, mismatch/tot, deletions/tot, insertions/tot

def kde_accuracy(arr, filename, total):
    quality = arr[:, 6]
    accuracy = arr[:, 0]
    coverage = arr[:, 5]
    df = pd.DataFrame({
        'Quality': quality,
        'Accuracy': accuracy,
        'Coverage': coverage,
    })

    # 创建图形
    plt.figure(figsize=(10, 6))

    # 绘制散点图
    sns.scatterplot(data=df, x='Quality', y='Accuracy', alpha=0.5, color='tab:blue', label='Accuracy vs Quality')

    # 绘制 KDE 图
    sns.kdeplot(data=df, x='Quality', fill=True, alpha=0.3, color='tab:red', label='Quality KDE')
    plt.axhline(y=0.9, color='black', linestyle='--', label='Accuracy = 0.9')
    colors = ['tab:green', 'tab:orange', 'tab:purple', 'tab:brown', 'tab:pink']

    # 绘制不同颜色的垂直线并计算统计信息
    quality_thresholds = [1, 7, 10, 12]
    for i, q in enumerate(quality_thresholds):
        plt.axvline(x=q, color=colors[i % len(colors)], linestyle='--', label=f'Quality = {q}')

    # 将文本信息放在图的右下角
    text_str = ""
    for q in quality_thresholds:
        subset = df[df['Quality'] >= q]
        if len(subset) == 0:continue
        percent = len(subset) / total
        median_accuracy = np.median(subset['Accuracy'].to_numpy())
        median_coverage = np.median(subset['Coverage'].to_numpy())
        text_str += f'Quality >= {q}:\nPercent: {percent*100:.2f}%\nMedian Accuracy: {median_accuracy*100:.2f}%\nMedian Coverage: {median_coverage*100:.2f}%\n\n'

    plt.figtext(0.75, 0.1, text_str, horizontalalignment='right', verticalalignment='bottom', fontsize=10,
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.5'))
        
    plt.xlabel('Quality')
    plt.ylabel('Accuracy')
    plt.title('Scatter Plot of Accuracy vs Quality with Quality KDE')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')

    plt.tight_layout(rect=[0, 0, 0.75, 1])  # 调整图形布局，留出图例空间
    plt.savefig(f'{filename}.png')
    

def argparser():
    parser = argparse.ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
        add_help=False)
    parser.add_argument("fastq", default=None, type=str)
    parser.add_argument("genomefile", default=None, type=str)
    parser.add_argument("--short-rna", default=False, action="store_true", help="use short rna mode")
    parser.add_argument("--keepall", default=False, action="store_true", help="do not discard supplementary alignments")
    parser.add_argument("-k", default=15, type=int, help="k-mer size (no larger than 28) [7]", required=False)
    parser.add_argument("-q", default=10, type=float, help="quality", required=False)

    return parser
    
    
def calculate_statistics(arr, filter_value):
    """计算给定过滤条件下的统计信息"""
    filtered_arr = arr[arr[:, 6] >= filter_value]
    
    if filtered_arr.size == 0:
        # 返回 NaN 值，表示没有数据
        return {
            'Mapping reads': np.nan,
            'Median accuracy': np.nan,
            'Mean quality': np.nan,
            'Average accuracy': np.nan,
            'Median mismatch': np.nan,
            'Median deletions': np.nan,
            'Median insertions': np.nan,
            'Median tlen': np.nan,
            'Median coverage': np.nan,
            'N50': np.nan,
            'Max length':  np.nan,
        }
    
    return {
        'Mapping reads':len(filtered_arr),
        'Median accuracy': np.median(filtered_arr[:, 0]),
        'Mean quality': np.median(filtered_arr[:, 6]),
        'Average accuracy': np.mean(filtered_arr[:, 0]),
        'Median mismatch': np.median(filtered_arr[:, 1]),
        'Median deletions': np.median(filtered_arr[:, 2]),
        'Median insertions': np.median(filtered_arr[:, 3]),
        'Median tlen': np.median(filtered_arr[:, 4]),
        'Median coverage': np.median(filtered_arr[:, 5]), 
        'N50': calculate_n50(filtered_arr[:, 4]),
        'Max length': np.max(filtered_arr[:, 4]),
    }


def calculate_n50(lengths):
    lengths = np.array(lengths)
    sorted_lengths = np.sort(lengths)[::-1]
    total_length = np.sum(sorted_lengths)
    cumulative_sum = np.cumsum(sorted_lengths)
    n50_index = np.where(cumulative_sum >= total_length / 2)[0][0]
    return sorted_lengths[n50_index]
        
def create_summary_df(arr, total, quality):
    total_reads = len(total)
    total_bases = sum(total.values()) / 1e6

    #stats_1 = calculate_statistics(arr, 1)
    stats = calculate_statistics(arr, quality)

    df = pd.DataFrame({
        'Condition': [f'Q {quality}'],
        'Total reads': [total_reads],
        'Total bases (Mb)': [total_bases],
        'Mapping reads': [stats['Mapping reads']],
        'Mapping rate': [stats['Mapping reads'] / total_reads] ,
        'Mapping rate(mbq1)': [stats['Mapping reads'] / len(arr)] ,
        'Median accuracy': [stats['Median accuracy']],
        'Mean quality': [stats['Mean quality']],
        'Average accuracy': [stats['Average accuracy']],
        'Median mismatch': [stats['Median mismatch']],
        'Median deletions': [stats['Median deletions']],
        'Median insertions': [stats['Median insertions']],
        'Median tlen': [stats['Median tlen']],
        'Median coverage': [stats['Median coverage']],
        'N50': [stats['N50']],
        'Max length': [stats['Max length']],
    })
    
    return df



def main(args):
    fastafile = pysam.FastaFile(args.genomefile)

    
    samfile = os.path.basename(args.fastq) + '.sam'
    if args.k > 7:
        cmd = f'minimap2 --secondary=no -ax map-ont -t 12 -k {args.k} --cs {args.genomefile} {args.fastq} > ./{samfile}'
    else:
        cmd = f'minimap2 --secondary=no -ax map-ont -t 12 -A1 -B1 -O1 -E1 -k {args.k} -I50G --cs {args.genomefile} {args.fastq} > ./{samfile}'
    
    if args.short_rna:
        cmd = f'minimap2 --secondary=no -ax map-ont -t 12 -k13 -w4 -n1 -m15 -s30 -A2 -B2 -O1,32 -E1,0 --cs {args.genomefile} {args.fastq} > ./{samfile}'

    subprocess.call(cmd, shell=True)
    
    arr = []
    total = {}
    sf = pysam.AlignmentFile(samfile, "r")
    for read in sf.fetch():
        total[read.query_name] = read.query_length
        if read.is_unmapped: continue
        if not args.keepall and (read.flag & 256 or read.flag & 2048): continue
        refseq = fastafile.fetch(read.reference_name, read.reference_start, read.reference_end)
        if read.seq == None:
            print("FAIL:", read.qname, read.reference_name)
            continue
        seq = read.seq[read.query_alignment_start:read.query_alignment_end]
        #print(seq)
        cstag = read.get_tag("cs")
        ans = parse_cs_tag(cstag, refseq, seq)
        tlen = read.query_alignment_length #计算模板长度
        coverage = float(read.query_alignment_length) / read.query_length
        qs = np.array(read.query_qualities).astype(int)
        mean_err = np.exp(qs * (-np.log(10) / 10.)).mean()
        quality = -10 * np.log10(max(mean_err, 1e-4))
        arr.append([ans[2], ans[3], ans[4], ans[5], tlen, coverage, quality])

    arr = np.array(arr)

    df1 = create_summary_df(arr, total, 1)
    df7 = create_summary_df(arr, total, 7)
    df10 = create_summary_df(arr, total, args.q)
    df = pd.concat((df1, df7, df10), axis=0).drop_duplicates().reset_index(drop=True)
    print(tabulate(df, headers='keys', tablefmt='grid', floatfmt=".3f"))
    df.to_csv(f'{os.path.basename(args.fastq)}.csv', index=False, float_format='%.3f')
    kde_accuracy(arr, os.path.basename(args.fastq), len(total))
    

if __name__ == "__main__":
    parser = argparser()
    args = parser.parse_args()
    main(args)
    