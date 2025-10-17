import io
import os
import sys
import csv
import gzip
import time
import random
import secrets
import subprocess
import json
import resource
import itertools
import multiprocessing
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import statsmodels.api as sm
import scipy
from typing import Union, Tuple, List
from scipy.stats import poisson
from scipy.stats import chi2
from scipy.stats import friedmanchisquare
from scipy.stats import studentized_range
pd.options.mode.chained_assignment = None

from .auxiliary import *
from .save import *
from .read import *
from .variables import *

__all__ = ["aggregate_r2", "extract_hla_type", "convert_indel", "subtract_bed_by_chr", "multi_subtract_bed", "filter_afs", "imputation_calculation_preprocess", "gather_hla_alleles"]

def aggregate_r2(df):
    tmp = df.copy().groupby(['AF', 'panel'])['corr'].mean().reset_index()
    res_ary = []
    for i in tmp['panel'].unique():
        imp_res = tmp[tmp['panel'] == i]
        imp_res['sort'] = imp_res['AF'].apply(lambda x: x.split('-')[0]).astype(float)
        imp_res = imp_res.sort_values(by = 'sort', ascending = True).drop(columns = 'sort')
        res_ary.append(imp_res.reset_index(drop = True))
    return res_ary
# Currently the saved version is gzip rather than bgzip
def convert_indel(vcf, save = False, prefix = 'chr', outdir = 'test.vcf.gz'):
    metadata = read_metadata(vcf)
    df = read_vcf(vcf)
    indels = df[(df['ref'] == '-') | (df['alt'] == '-')]
    indels = indels.apply(recode_indel, axis = 1)
    snps = df[(df['ref'] != '-') & (df['alt'] != '-')]
    df = pd.concat([snps, indels]).sort_values(by = ['chr', 'pos'], ascending = True)
    if save:
        save_vcf(df, metadata, prefix, save_name = outdir)
    return df

def subtract_bed_by_chr(cov, region, q = None):
    i = 0
    tmp = 0
    for j in range(region.shape[0]):
        chr, start, end = region.iloc[j,:]
        while start > cov.iloc[i,2]:
            i += 1
        if start < cov.iloc[i,1]:
            cov.iloc[i-1, 2] = start
            if end < cov.iloc[i,2]:
                cov.iloc[i,1] = end
            elif end == cov.iloc[i,2]:
                cov.iloc[i,3] = -9
                i += 1
            else:
                tmp = i
                while end > cov.iloc[tmp,2]:
                    tmp += 1
                if end < cov.iloc[tmp, 2]:
                    cov.iloc[tmp, 1] = end
                    cov.iloc[i:tmp, 3] = -9
                    i = tmp
                else:
                    cov.iloc[i:tmp+1, 3] = -9
                    i = tmp
        elif start == cov.iloc[i,1]:
            if end < cov.iloc[i,2]:
                cov.iloc[i,1] = end
            elif end == cov.iloc[i,2]:
                cov.iloc[i, 3] = -9
            else:
                tmp = i
                while end > cov.iloc[tmp,2]:
                    tmp += 1
                if end < cov.iloc[tmp, 2]:
                    cov.iloc[tmp, 1] = end
                    cov.iloc[i:tmp+1, 3] = -9
                    i = tmp
                else:
                    cov.iloc[i:tmp, 3] = -9
                    i = tmp
        else:
            idx = cov.index.max() + 1
            cov.loc[idx] = {'chr': chr, 'start': cov.iloc[i,1], 'end': start, 'cov': cov.iloc[i,3]}
            if end < cov.iloc[i, 2]:
                cov.iloc[i, 1] = end
            elif end == cov.iloc[i, 2]:
                cov.iloc[i, 3] = -9
            else:
                tmp = i
                while end > cov.iloc[tmp,2]:
                    tmp += 1
                if end < cov.iloc[tmp, 2]:
                    cov.iloc[tmp, 1] = end
                    cov.iloc[i:tmp, 3] = -9
                    i = tmp
                else:
                    cov.iloc[i:tmp+1, 3] = -9
                    i = tmp
    res = cov[cov['cov'] >= 0].sort_values(by = cov.columns[:2].to_list()).reset_index(drop = True)
    if q is None:
        return res
    else:
        q.put(res)

def multi_subtract_bed(chromosomes, covs, regions, combine = True):
    manager = multiprocessing.Manager()
    q = manager.Queue()
    processes = []
    for i in range(len(chromosomes)):
        tmp = multiprocessing.Process(target=subtract_bed_by_chr, args=(covs[i], regions[i], q))
        tmp.start()
        processes.append(tmp)
    for process in processes:
        process.join()
    res_lst = []
    while not q.empty():
        res_lst.append(q.get())
    if combine:
        return combine_df(res_lst)
    else:
        return res_lst

def filter_afs(df1, df2, diff=0.2, z_score=None):
    # df1 is the main vcf in which afs are to be filtered out
    # df2 is the ref panel afs
    # Either filter by z-score (suggested 2 sds so 1.96 or diff=0.2)
    res = pd.merge(df1, df2, on=['chr', 'pos', 'ref', 'alt'])
    if z_score is not None:
        res = res[(res['prop_y'] != 0) & (res['prop_y'] != 1)]
        res['z'] = (res['prop_x'] - res['prop_y']) / np.sqrt(
            res['prop_y'] * (1 - res['prop_y']))
        res = res[abs(res['z']) <= z_score]
        return res.drop(columns=['prop_x', 'prop_y', 'z'])
    else:
        res = res[abs(res['prop_x'] - res['prop_y']) < diff]
        return res.drop(columns=['prop_y']).rename(columns={'prop_x': 'prop'})

def extract_hla_type(input_vcf, csv_path, json_path, two_field = True):
    vcf = read_vcf(input_vcf)
    vcf = vcf[vcf['ID'].str.contains('HLA')]
    if two_field:
        vcf = vcf[vcf['ID'].str.contains(':')]
    samples = list(vcf.columns[9:])

    for i in samples:
        vcf[i] = vcf[i].apply(encode_hla)

    types = vcf['ID'].str.split('*').str.get(0).unique()
    types.sort()
    hla = pd.DataFrame({'Name': samples})
    for i in types:
        hla[i + '_1'] = 0
        hla[i + '_2'] = 0
    hla.set_index('Name', inplace=True)

    num_type = len(types) * 2
    hla_abnormal = {}
    for sample in samples:
        hla_type = []
        for gene in types:
            tmp_vcf = vcf[vcf['ID'].str.contains(gene)].reset_index().drop(
                columns='index')
            hla_subtype = []
            for i in range(tmp_vcf.shape[0]):
                if tmp_vcf.loc[i, sample] == 1:
                    hla_subtype.append(tmp_vcf.iloc[i, 2])
                elif tmp_vcf.loc[i, sample] == 2:
                    hla_subtype.append(tmp_vcf.iloc[i, 2])
                    hla_subtype.append(tmp_vcf.iloc[i, 2])
                else:
                    pass
            if len(hla_subtype) < 2:
                hla_subtype = hla_subtype + ['N/A'] * (2 - len(hla_subtype))
            hla_type = hla_type + hla_subtype
        if len(hla_type) == num_type:
            hla.loc[sample, :] = hla_type
        else:
            hla_abnormal[sample] = hla_type

    hla.to_csv(csv_path, header = True, index = True)
    if hla_abnormal != {}:
        with open(json_path, "w") as json_file:
            json.dump(hla_abnormal, json_file)

def imputation_calculation_preprocess(
        truth_vcf,
        imp_vcf,
        af_txt,
        chromosome=None,
        save_vcfs=False,
        lc_vcf_outdir=None,
        hc_vcf_outdir=None,
        af_outdir=None,
        lc_vcf_name=None,
        hc_vcf_name=None,
        af_name=None):

    # Truth_vcf should have GT rather than DS in its FORMAT field, whereas imp_vcf has to have DS
    af = read_af(af_txt)
    lc = read_vcf(imp_vcf).sort_values(by=['chr', 'pos'])
    chip = read_vcf(truth_vcf).sort_values(by=['chr', 'pos'])

    if chromosome is not None:
        lc = lc[lc['chr'] == int(chromosome)]
        chip = chip[chip['chr'] == int(chromosome)]
        af = af[af['chr'] == int(chromosome)]

    res = intersect_dfs([chip, lc, af])
    chip = res[0]
    lc = res[1]
    af = res[2]

    chip = reorder_cols(chip)
    lc = reorder_cols(lc)
    lc.columns = chip.columns

    drop_cols = ['ID', 'QUAL', 'FILTER', 'INFO', 'FORMAT']

    if save_vcfs:
        lc_metadata = read_metadata(imp_vcf, new_cols = list(lc.columns[9:]))
        hc_metadata = read_metadata(truth_vcf, new_cols = list(chip.columns[9:]))

        save_vcf(lc,
                 lc_metadata,
                 outdir=lc_vcf_outdir,
                 save_name=lc_vcf_name)

        save_vcf(chip,
                 hc_metadata,
                 outdir=hc_vcf_outdir,
                 save_name=hc_vcf_name)

        if not os.path.exists(af_outdir):
            os.makedirs(af_outdir)
        af.to_csv(af_outdir + af_name, sep = '\t', header = False, index = False)

    lc = lc.apply(extract_DS, axis=1)
    chip = chip.apply(encode_genotype, axis=1)

    lc = lc.drop(columns=drop_cols)
    chip = chip.drop(columns=drop_cols)

    return chip, lc, af

# This converts HLA direct sequencing results to two-field allelic format
def gather_hla_alleles(hla):
    result = hla.melt(id_vars=['Locus'], value_vars=['Two field1', 'Two field2'], var_name='variable', value_name='Two field').drop(columns=['variable'])
    result['Allele'] = result['Locus'] + '*' + result['Two field']
    result = result.drop(columns = 'Two field')
    return result