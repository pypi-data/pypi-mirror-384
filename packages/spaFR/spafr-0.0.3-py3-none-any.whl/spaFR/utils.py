import pandas as pd
import os

def read_csv_tsv(filename):
    if ('csv' in filename) or ('.log' in filename):
        tmp = pd.read_csv(filename, sep = ',',header = 0,index_col=0)
    else:
        tmp = pd.read_csv(filename, sep = '\t',header = 0,index_col=0)
    return tmp



def load_pathway_lr():
    """
    Load default pathway and ligand-receptor pair data from the package's pathway directory.
    
    Returns:
        tuple: (pathway_df, lr_df)
            - pathway_df (pd.DataFrame): Pathway data
            - lr_df (pd.DataFrame): Ligand-receptor pairs data
    """
    try:
        # Get the directory where this file is located and add /pathway/
        data_path = os.path.dirname(os.path.realpath(__file__)) + '/pathway/'
        
        # Load pathway data
        pathway_df = pd.read_csv(f'{data_path}/pathways.txt', header=0, index_col=0, sep='\t')
        
        # Load ligand-receptor pairs data
        lr_df = pd.read_csv(f'{data_path}/lrpairs.txt', header=0, index_col=0, sep='\t')
        
        return pathway_df, lr_df
    
    except FileNotFoundError as e:
        print(f"Error: Required data file not found: {e}")
        raise
    except Exception as e:
        print(f"Error loading pathway data: {e}")
        raise


