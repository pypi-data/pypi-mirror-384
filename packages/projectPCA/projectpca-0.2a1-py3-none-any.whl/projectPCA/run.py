###############################################
### Core Run Functions for Package 
### Wrap other content

import numpy as np
import pandas as pd
import os as os

### Imports from Package
from projectPCA.get_proj_files import get_projection_files # Load pre-comp data
from projectPCA.loadEigenstrat import get_eigenstrat_object # Load eigenstrat
from projectPCA.proj_pca import get_pcs_proj_gts # Calculte new PCA projection
from projectPCA.plot_pca import plot_df_pc, plot_df_pc_plotly # Plotting functions


def project_eigenstrat(es_path="", pca="HO", savepath="", fig_path="",
                       df_snp=[], df_ind=[], iids=[], dfw=[], df_bgrd_pcs=[],
                       plot=["pc1", "pc2"], es_type="standard", min_snps=10000):
    """Load and project eigenstrat file. Plot, save, and return PC projection dataframe
    Main input:
    es_path: Path to the target eigenstrat (up to .geno, .ind and .snp suffix)
    pca: Which PC to project on. One of HO / EU
    es_type: Which eigenstrat type to load. One of default/eager/autoeager
    
    Optional input to overwrite default loading:
    df_snp: SNP dataframe with snp column, PCA weights, and allele frequency (p)
    df_ind: Individual dataframe
    iids: Use only these iids to project
    dfw: SNP weights from PCA
    df_bgrd_pcs: Background PCs to plot

    Optional output parameters:
    plot: List of length 2: In which order pc1 and pc2 are plotted. If empty, no plot.
    plot_flip_pcs: Whether to flip PC1 and PC2
    fig_path: Where to save the figure of the PC projection. If empty, not plot saved.
    savepath: Where to save the output table of PC coordinates. If empty, do not save.
    """
    
    pf = get_projection_files(pca) # Load the pre-computed PC Object
    if len(dfw)==0:
        dfw = pf.get_snp_weights()
    if len(df_bgrd_pcs)==0:
        df_bgrd_pcs = pf.get_projections_ref()

    es = get_eigenstrat_object(es_path, mode=es_type) # Load the eigenstrat Object

    df_pc = project_es_obj(es=es, dfw=dfw, df_bgrd_pcs=df_bgrd_pcs,
                           df_snp=df_snp, df_ind=df_ind, iids=iids,
                           savepath=savepath, fig_path=fig_path, 
                           plot=plot, min_snps=min_snps)
    return df_pc


def project_es_obj(es=None, dfw=[], df_bgrd_pcs=[],
                   df_snp=[], df_ind=[], iids=[],
                   plot=["pc1", "pc2"], savepath="", fig_path="", min_snps=10000):
    """Load and project eigenstrat file. Plot, save, and return PC projection dataframe
    es_path: Path to the target eigenstrat (up to .geno, .ind and .snp)
    dfw: Weight file to use
    savepath: Where to save the output table of PC coordinates. If empty, do not save.
    fig_path: Where to save the figure of the PC projection. If empty, not plot saved.
    df_snp: Optional, use this as SNP df
    df_ind: Optional, use this as iid df
    iids: Optional, if given, use these iids to project
    df_bgrd_pcs: Which background PCs to plot"""

    if len(df_ind)==0:
        df_ind = es.load_ind_df()
    if len(df_snp)==0:
        df_snp = es.load_snp_df()
    if len(iids)==0:
        iids = df_ind["iid"][:].values
        
    df_pc = proj_iids_ESobj(iids=iids, es=es, dfw=dfw, df_snp=df_snp, min_snps=min_snps)

    if len(savepath)>0:
        df_pc.to_csv(savepath, index=False, sep="\t")
    
    if len(plot)==2: 

        if fig_path.endswith(".html"): # # Use Plotly function if html
            plot_df_pc_plotly(df_pcs=df_pc, df_bgrd_pcs=df_bgrd_pcs, 
                   plot_cols=plot, savepath=fig_path)
        else:
            plot_df_pc(df_pcs=df_pc, df_bgrd_pcs=df_bgrd_pcs, 
                       plot_cols=plot, savepath=fig_path)
    return df_pc


###############################################
### Project general eigenstrat (e.g., AADR)

def proj_iids_ESobj(iids=[], es=None, dfw=[], df_snp=[], min_snps=10000, maf=0.05):
    """Get PCA dataframe starting from ES Object as input.
    es: hapROH eigenstrat object. created via load_eigenstrat factory function."""

    ### Load genotype data
    gt = np.array([es.get_geno_iid(iid) for iid in iids], dtype="float16")
    
    ### Run Projection
    df_pc = get_pcs_proj_gts(g=gt, dfw=dfw, df_snp=df_snp, min_snps=min_snps, maf=maf)
    df_pc["iid"] = iids
    return df_pc