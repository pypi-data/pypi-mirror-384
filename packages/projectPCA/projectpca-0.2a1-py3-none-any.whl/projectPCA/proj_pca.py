# Functions to project new samples onto PCS
# Contains core projection and also wrappers for various data types
### Harald, Sep 2025

import numpy as np
import pandas as pd

from projectPCA.eigenstrat_funcs import load_genos_autoeager, update_values

##############
### Functions Harald PCA
def get_gts_norm(gts, p, maf=0.05):
    """ Normalize Genotype Matrix
    following smartpca way.
    gts: Genotype matrix
    p: Vector of allele frequencies"""
    assert(len(p)==np.shape(gts)[1]) ### Sanity Check

    ### Remove Fixed Values
    idx = np.isclose(p,1, atol=maf) | np.isclose(p,0, atol=maf)
    print(f"Filtering {np.sum(idx)} / {len(idx)} SNPs with MAF<{maf}.")
    p1 = p[~idx]
    gts1 = gts[:,~idx]

    ### Normalize
    g_norm = (gts1/2.0 - p1[None,:]) / np.sqrt(2.0*p1 * (1-p1))

    ### Re-Expand to full format
    g_norm0 = np.zeros(np.shape(gts), dtype="float") # re-introduces NANs
    g_norm0[:,~idx] = g_norm
    g_norm0[:, idx] = np.nan
    
    return g_norm0

def print_covered(gts, output=True):
    """Print and return # missing Genotypes"""
    idx_nan=np.isnan(gts)
    cov = np.sum(~idx_nan, axis=1)
    if output:
        print(cov)
    return cov

def get_proj_2d(dfw, gts, maf=0.05):
    p = dfw["p"].values
    g_norm = get_gts_norm(gts, p, maf=maf)

    ### Do the 2D projection
    pc1 = np.dot(g_norm, dfw["w1"])
    pc2 = np.dot(g_norm, dfw["w2"])

    return pc1, pc2

def get_least_square_2d(dfw,  gts, w1="w1", w2="w2", maf=0.05):
    """Get least square projection of gts using weights in dftw.
    gts MUST match dfw (weights)
    Return pc1 & pc2 coordinates"""
    p = dfw["p"].values
    g_norm = get_gts_norm(gts, p, maf=maf)
    
    a = np.array((dfw[w1], dfw[w2])).T

    n= len(g_norm) # Nr iids
    pcs = np.zeros((2,n), dtype="float")
    
    for g_n, i in zip(g_norm, np.arange(n)):
        idx = ~np.isnan(g_n)
        
        pcs0 = np.linalg.lstsq(a[idx], g_n[idx])[0]
        pcs[:,i] = pcs0

    return pcs

def get_pcs_proj(iids=[], code="SG", strand="single",
                 dfw=[], df_snp=[], min_snps=10000, maf=0.05):
    """Get PC Projection of IIDs.
    min_snps: Minimum Number of covered SNPs to be projected.
    If less than that, return NAN.
    g: If given, use this as Genotype Matrix"""
    ### Load Genotypes
    g = load_genos_autoeager(iids=iids,code=code, strand=strand)

    ### Filter to IIDs with genotype entries
    idx_missing = np.isnan(g).all(axis=1)
    if np.sum(idx_missing)>0:
        g = g[~idx_missing, :]
        iids = np.array(iids)[~idx_missing]
    
    g = update_values(g, x=[48, 49, 50, 57], y=[2, 1, 0, np.nan])
    assert(np.shape(g)[1] == len(df_snp)) # Sanity Check whether geno file matches snp file

    ### Do the projection 
    df_pc = get_pcs_proj_gts(g=g, dfw=dfw, df_snp=df_snp, min_snps=min_snps, maf=maf)
    df_pc["iid"]=iids # Set iids

    return df_pc


def get_pcs_proj_gts(g=[], dfw=[], df_snp=[], min_snps=10000, maf=0.05,
                     flip=False, rs_id_col="snp"):
    """Get PC Projection of IIDs.
    min_snps: Minimum Number of covered SNPs to be projected.
    If less than that, return NAN.
    g: Genotype Matrix (n iids x k SNPs) of entries 0/1/2
    df_snp: SNP dataframe matching gts (snp file to genotype file)
    flip: Whether to check for flipped alleles and flipping them"""
    ### Load Genotypes
    assert(np.shape(g)[1] == len(df_snp)) # Sanity Check whether geno file matches snp file

    ### Create SNP weights in genotyped positions
    dfw1240 = pd.merge(df_snp[[rs_id_col, "ref", "alt"]], dfw, 
                       left_on=rs_id_col, right_on=["snp"], how="left")
    
    idx = ~dfw1240["w1"].isnull() # SNPs with weight, e.g. in the weight file
    dfw1 = dfw1240[idx]
    g1= g[:,idx]

    if len(dfw1)==0:
        raise RuntimeWarning("No intersecting SNPs with projection weights. Please check snp column of input .snp file.")

    ### Flip (and and filter to matching only):
    if flip:
        idx1 = (dfw1["ref_x"]==dfw1["ref_y"]) & (dfw1["alt_x"]==dfw1["alt_y"]) # fit
        idx2 = (dfw1["ref_x"]==dfw1["alt_y"]) & (dfw1["alt_x"]==dfw1["ref_y"]) # flip
        idxb = idx1 | idx2
        print(f"Matching: {np.sum(idx1)}. Matching flip: {np.sum(idx2)} of {len(idx1)}.")

        g1[:,idx2] = 2 - g1[:,idx2] # Flip swapped alleles
        g1 = g1[:,idxb]
        dfw1 = dfw1[idxb]

    cov = print_covered(g1, output=False)

    ### Do the projection 
    pc_proj = get_least_square_2d(dfw1, g1, maf=maf)

    ### Create Output projection
    df_pc = pd.DataFrame({"pc1":pc_proj[0], "pc2":pc_proj[1], "#SNP":cov})
    idx = df_pc["#SNP"]<min_snps # Set pcs of iids with to few SNPs to NAN
    df_pc.loc[idx,["pc1","pc2"]] = np.nan

    return df_pc

def set_color_pca(df, c="red", c_low="yellow", snp_low=1e5):
    """Set Color of PCA projection df.
    df: Dataframe
    c: General color to plot in scatterplot
    c_low: Low coverage color
    snp_low: SNP cutoff for low color"""
    df["c"]=c
    idx = df["#SNP"]<snp_low
    print(f"Setting {np.sum(idx)}/{len(idx)} iids with <{snp_low} SNPs to {c_low}")
    df.loc[idx,"c"]=c_low

def get_gts_from_geno(path_geno="/mnt/archgen/users/xiaowen/public_data/HO/HO_WEA_4yilei.geno", num_snps=597573):
    gts = load_unpacked_eigenstrat(path_geno, num_snps=num_snps)
    #gts = gts.astype("float16")
    #gts = update_values(gts, x=[48, 49, 50, 57], y=[2, 1, 0, np.nan])
    return gts






    