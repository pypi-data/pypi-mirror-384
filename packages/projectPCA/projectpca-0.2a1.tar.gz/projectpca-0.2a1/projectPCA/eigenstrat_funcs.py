# Functions to load and analyze eigentrat files
### Harald Ringbauer, April 18th 2025

import numpy as np
import pandas as pd
import os

def pw_mm_rate(g1, g2, val_missing=57):
    """ Calculate Pairwise Mismatch Rate between two samples.
    g1, g2: Array of genotype values
    val_missing: Value of Missing data.
    Return PMR, # mismatches, # SNPs covered in both"""
    idx_both = (g1!=val_missing) & (g2!=val_missing)
    snps = np.sum(idx_both)
    mms = np.sum(idx_both * (g1 != g2)) 
    
    pw_mm_rate = mms / snps
    return pw_mm_rate, mms, snps

def get_geno_iid(dfj, gt, iid=""):
    """Extract Genotype of IID iid.
    dfj: matching janno file to genotype matrix gt [#IIDsx #SNPs]"""
    
    idx = dfj["Poseidon_ID"] == iid
    idcs = np.where(idx)[0]
    if len(idcs)==0:
        raise RuntimeWarning(f"IID: {iid} not found.")
        return []
    assert(len(idcs)==1)
    return gt[idcs[0],:]

def load_unpacked_eigenstrat(file_path, num_samples=0, num_snps=1233013):
    # Read the unpacked genotype file
    with open(file_path, "rb") as f:
        # Load all genotype data as unsigned 8-bit integers
        genotype_data = np.frombuffer(f.read(), dtype=np.uint8)
    
    if num_samples==0:
        num_cols = int(genotype_data.size / num_snps)
    else:
        num_cols = num_samples + 1
        
        
    # Check that the file size matches the expected number of genotypes
    expected_size = num_cols * num_snps # Add one column for the last one
    assert genotype_data.size == expected_size, "File size does not match expected number of genotypes based on samples and SNPs"

    # Reshape the data into a matrix with shape (num_samples, num_snps)
    genotype_matrix = genotype_data.reshape((num_snps, num_cols)).T
    return genotype_matrix[:-1,:] # Delete last, empty row

def get_geno_autoeager_path(iid="", code="SG", strand="single"):
    """Get the autoeager .geno output path of individual iid.
    Return that path.
    iid: String of Pandora ID"""
    site = iid[:3]
    path_geno = f"/mnt/archgen/Autorun_eager/eager_outputs/{code}/{site}/{iid}/genotyping/pileupcaller.{strand}.geno"
    return path_geno

def load_geno_autoeager(iid="", code="SG", strand="single", num_snps=1233013):
    """Load genotype data for iid in df_bam.
    The respective eager eigenstrat geno file is loaded and returned."""
    site = iid[:3]
    path_geno = get_geno_autoeager_path(iid=iid, code=code, strand=strand) # Get the path
    if os.path.exists(path_geno):
        g = load_unpacked_eigenstrat(path_geno, num_snps=num_snps) # load the geno matrix
    else:
        raise RuntimeWarning(f"Geno File not found for {iid}: \n{path_geno}", RuntimeWarning)
        g=[]
    return g

def load_genos_autoeager(iids=[],  code="SG", strand="single", num_snps=1233013):
    """Load eager genotype data for iids (list)
        The respective eager eigenstrat geno files are loaded, concatenated, and returned."""
    iids = np.array(iids) #Make sure it is numpy array of values
    n = len(iids)
    gs = np.empty((n, num_snps), dtype="float")
    gs[:] = np.nan # Fill with NANs
    
    for i in range(n):
        iid = iids[i]
        g= load_geno_autoeager(iid=iid, code=code, 
                              strand=strand, num_snps=num_snps)
        if len(g)>0: # if not empty
            gs[i] = g
            
    return gs
    

def update_values(gt, x=[48,49,50,57], y=[2,1,0,9], copy=False):
    """"Update Values in numpy matrix gt. 
    x: List of original values.
    y: Updated values"""
    if copy:
        gt2 = gt.astype("float") # hard copy, necessary if values intersect

    else:
        gt2 = gt # only pointer
        
    for i,j in zip(x,y):
        idx = gt == i
        gt2[idx] = j
    return gt2
