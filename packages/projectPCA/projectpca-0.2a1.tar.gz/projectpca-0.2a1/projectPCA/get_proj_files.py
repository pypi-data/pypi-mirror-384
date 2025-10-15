### Get Files for Projections
# Strucure: A main class that is implement according to PC projection
# Factory Function (returning right sub class depending on mode at the bottom)

import pandas as pd
from importlib import resources as impresources

from projectPCA import data

#################################
### Class to give projection files
class Projection_Files(object):
    """Class the required files for projection.
    Can return SNP weight file or modern background"""

    dfw = "" # SNP weight File
    df_bgrd_pcs = "" # Default Projections

    def get_snp_weights(self):
        """Return SNP weight dataframe."""
        return self.dfw

    def get_projections_ref(self):
        """Return the default Projections."""
        return self.df_bgrd_pcs
        

class Projection_Files_HO(Projection_Files):
    """HO Origin Projection"""
    
    
    def __init__(self):
        path_wts = impresources.files(data) / "we_v1" / "20250422.ho_ptn_weights_p.tsv"
        self.dfw = pd.read_csv(path_wts, sep="\t")

        path_ho_pcs = impresources.files(data) / "we_v1" / "20250422.ho_projections.tsv"
        self.df_bgrd_pcs = pd.read_csv(path_ho_pcs, sep="\t")

class Projection_Files_EU(Projection_Files):
    """Based on Joscha's PCA"""
    
    def __init__(self):
        path_wts = impresources.files(data) / "joscha_v1" / "joscha.weights_p.tsv"
        self.dfw = pd.read_csv(path_wts, sep="\t")

        path_ho_pcs = impresources.files(data) / "joscha_v1" / "joscha.ho_proj.maf05.tsv"
        self.df_bgrd_pcs = pd.read_csv(path_ho_pcs, sep="\t")

         
def get_projection_files(mode="HO"):
    """Factory Function to return the right Projection_Files object. Currently implemented:
    HO: Human origin West Eurasia projection
    EU: Based on Joscha's  Fine-Scale EU PCA 
    (see Gretzinger et al 2022, https://doi.org/10.1038/s41586-022-05247-2)
    """

    if mode=="HO":
        return Projection_Files_HO()

    elif mode=="EU":
        return Projection_Files_EU()

    else:
        raise RuntimeWarning(f"Mode: `{mode}` is not implemented. Please provide one of HO/ EU.")