import os
import pickle
import utils
import pandas as pd
import FR


class FRAnalyzer:
    """
    Spatial Functional redundancy Analysis tool for single-cell expression data.
    
    This class provides a comprehensive API for analyzing functional redundancy
    patterns across different cell types using single-cell expression data.
    
    Attributes:
        sc_exp (pd.DataFrame): Single-cell expression matrix (genes × cells)
        sc_meta (pd.DataFrame): Metadata with cell type annotations
        tp_key (str): Column name for cell type in metadata
        species (str): Species name ('Human' or 'Mouse')
        max_hop (int): Maximum hop distance for R-TF graph
        out_dir (str): Output directory for results
        r_tf_graph_dict (dict): Dictionary of receptor-TF graphs for each cell
        cell_type_rtf_networks (dict): Dictionary of GCN data by cell type
        fr_df_dict (dict): Dictionary of functional redundancy scores by cell
        tp_fr_dict (dict): Dictionary of merged FR data by cell type
        pagerank_results (pd.DataFrame): PageRank centrality results
        se_cell_dict (dict): Dictionary of subtree entropy results by cell
    """

    def __init__(self, expression_data=None, meta_data=None, cell_type_column=None, 
                 species="Human", max_hop=4, out_dir="./results"):
        """
        Initialize the FRAnalyzer object.
        
        Args:
            expression (str, optional): Expression matrix, genes(rows) x cells(column)
            metadata (str, optional): Metadata, cells(row) x features(columns)
            cell_type_column (str, optional): Column name for cell type in metadata
            species (str, optional): Species name ('Human' or 'Mouse')
            max_hop (int, optional): Maximum hop distance for R-TF graph
            out_dir (str, optional): Output directory for results
        """
        self.sc_exp = expression_data
        self.sc_meta = meta_data
        self.tp_key = cell_type_column
        self.species = species
        self.max_hop = max_hop
        self.out_dir = out_dir
        
        # Initialize data containers
        self.pathway = None
        self.lr_df = None
        self.r_tf_graph_dict = {}
        self.cell_type_rtf_networks = {}
        self.fr_df_dict = {}
        self.sp_d = {}
        self.td_dict = {}
        self.nFR_dict = {}
        self.fr_dict = {}
        self.tp_fr_dict = {}
        self.pagerank_results = None

        # Create output directory if needed
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
    
    def check_data(self):
        """
        Load expression and metadata files.
        
        Args:
            expression_file (str): Path to expression matrix file
            metadata_file (str): Path to metadata file
            cell_type_column (str, optional): Column name for cell type in metadata
            
        Returns:
            self: Returns self for method chaining
        """
        try:
            # Remove duplicated genes with zero expression
            self.sc_exp = self.sc_exp.loc[~((self.sc_exp.index.duplicated()) & 
                                           (self.sc_exp.sum(axis=1) == 0))]
            
            # Set cell type column
            if not self.tp_key in self.sc_meta.columns:
                raise ValueError(f"Cell type column '{self.tp_key}' not found in metadata")

            print(f"Loaded expression data: {self.sc_exp.shape[0]} genes, {self.sc_exp.shape[1]} cells")
            print(f"Loaded metadata: {self.sc_meta.shape[0]} cells")
            
            return self
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            raise
    
    def load_pathway_data(self, pathway_data=None, lr_data=None):
        """
        Load pathway and ligand-receptor pair data.
        
        Args:
            pathway_data (pd.DataFrame, optional): Pathway data. If None, loads from default directory.
            lr_data (pd.DataFrame, optional): Ligand-receptor pairs data. If None, loads from default directory.

        Returns:
            self: Returns self for method chaining
        """
        try:
            # Handle user-provided data
            if lr_data is not None:
                self.lr_df = lr_data

            if pathway_data is not None:
                self.pathway = pathway_data

            # Load default data if either pathway or lr_data is still None
            if self.pathway is None or self.lr_df is None:
                default_pathway, default_lr = utils.load_pathway_lr()
                
                # Only update attributes that are still None
                if self.pathway is None:
                    self.pathway = default_pathway
                
                if self.lr_df is None:
                    self.lr_df = default_lr
                    
            print(f"Loaded {self.pathway.shape[0]} pathway records")
            print(f"Loaded {self.lr_df.shape[0]} ligand-receptor pairs")
            
            return self
        except Exception as e:
            print(f"Error loading pathway data: {e}")
            return self
        

    def filter_pathway(self):
        """
        Filter pathways and ligand-receptor pairs based on expression data.
        """
        self.pathway, self.lr_df = FR.filter_lr_pathway(self.sc_exp, 
                                                    self.pathway, self.lr_df, self.species)
        print(f"Filtered remains {self.pathway.shape[0]} pathway records")
        print(f"Filtered remains {self.lr_df.shape[0]} ligand-receptor pairs")
        self.ggi_tf = self.pathway[['src', 'dest', 'src_tf', 'dest_tf']]
        self.ggi_tf = self.ggi_tf.drop_duplicates()
        self.receptor_name = self.lr_df['receptor'].unique()
        return self

    
    def build_receptor_tf_GTN(self, max_hop=4, cache=True):
        """
        Build receptor-TF graphs for each cell.
        
        Args:
            max_hop (int, optional): Maximum hop distance, default as 4.
            cache (bool, optional): Whether to cache results to disk
            
        Returns:
            dict: Dictionary of receptor-TF graphs for each cell
        """
        if max_hop is not None:
            self.max_hop = max_hop
            
        # Check if required data is loaded
        if self.sc_exp is None or self.pathway is None or self.lr_df is None:
            raise ValueError("Expression and pathway data must be loaded first")
            
        # Check for cached results
        cache_file = os.path.join(self.out_dir, 'r_tf_graph_dict.pkl')
        if cache and os.path.exists(cache_file):
            print("Loading cached receptor-TF graphs")
            with open(cache_file, 'rb') as f:
                self.r_tf_graph_dict = pickle.load(f)
            return self.r_tf_graph_dict
                
        # Build graphs for each cell
        from tqdm import tqdm  # 使用标准 tqdm 而不是 notebook 版本
        self.r_tf_graph_dict = {}

        for cell in tqdm(self.sc_exp.columns, desc="Building R-TF graphs for each cell"):
            exp = self.sc_exp[cell]
            exp = exp[exp > 0]
            exp = pd.DataFrame(exp)
            r_tf_graph, ok_receptor = FR.get_ggi_res(self.receptor_name, self.ggi_tf, exp, self.max_hop)
            self.r_tf_graph_dict[cell] = r_tf_graph.fillna(0)
        
        # Save results if caching is enabled
        if cache:
            with open(cache_file, 'wb') as f:
                pickle.dump(self.r_tf_graph_dict, f)
        
        return self.r_tf_graph_dict
    

    def aggregate_cell_type_networks(self, cache=True):
        """
        Aggregate receptor-TF networks for cells of the same type to enable cell-type level GCN analysis.
        
        Args:
            use_cache (bool, optional): Whether to load/save results from/to disk cache
                
        Returns:
            dict: Dictionary mapping cell types to their aggregated receptor-TF networks
        """
        # Validate prerequisite data
        if self.sc_meta is None or not self.r_tf_graph_dict:
            raise ValueError("Single-cell metadata and receptor-TF networks must be loaded before aggregation")
        
        # Check for and load cached results if available
        cache_path = os.path.join(self.out_dir, 'cell_type_rtf_networks.pkl')
        if cache and os.path.exists(cache_path):
            print("Loading cached cell-type receptor-TF networks")
            with open(cache_path, 'rb') as cache_file:
                self.cell_type_rtf_networks = pickle.load(cache_file)
            return self.cell_type_rtf_networks
        
        print("Aggregating receptor-TF networks by cell type")
        self.cell_type_rtf_networks = {}
        
        from tqdm import tqdm
        for cell_type in tqdm(self.sc_meta[self.tp_key].unique(), desc="Processing cell types"):
            # Get cells belonging to this cell type
            cells_in_type = self.sc_meta[self.sc_meta[self.tp_key] == cell_type].index
            
            # Collect networks for all cells of this type
            cell_networks = []
            for cell_id in cells_in_type:
                if cell_id in self.r_tf_graph_dict:
                    # Reset index before appending to ensure proper concatenation
                    cell_networks.append(self.r_tf_graph_dict[cell_id].reset_index())
            
            # Skip if no networks were found for this cell type
            if not cell_networks:
                continue
            
            # Combine all networks at once instead of incrementally
            combined_networks = pd.concat(cell_networks, ignore_index=True)
            
            # Calculate median values across all cells of this type
            # Use 'index' column instead of actual index
            aggregated_network = combined_networks.groupby('index').median()
            aggregated_network = aggregated_network.fillna(0)
            
            # Store the aggregated network
            self.cell_type_rtf_networks[cell_type] = aggregated_network
        
        # Cache results if enabled
        if cache:
            with open(cache_path, 'wb') as cache_file:
                pickle.dump(self.cell_type_rtf_networks, cache_file)
        
        return self.cell_type_rtf_networks
    
    def calculate_functional_redundancy(self, cache=True):
        """
        Calculate functional redundancy scores for each cell.
        
        Args:
            cache (bool, optional): Whether to cache results to disk
            
        Returns:
            dict: Dictionary of functional redundancy scores by cell
        """
        # Check if required data is loaded
        if self.sc_exp is None or self.sc_meta is None or not self.cell_type_rtf_networks:
            raise ValueError("Expression data, metadata, and GCN data must be loaded first")
        
        # Check for cached results
        cache_file = os.path.join(self.out_dir, 'fr_df_dict.pkl')
        if cache and os.path.exists(cache_file):
            print("Loading cached functional redundancy data")
            with open(cache_file, 'rb') as f:
                self.fr_df_dict = pickle.load(f)
            with open(os.path.join(self.out_dir, 'sp_d.pkl'), 'rb') as f:
                self.sp_d = pickle.load(f)
            with open(os.path.join(self.out_dir, 'td_dict.pkl'), 'rb') as f:
                self.td_dict = pickle.load(f)
            with open(os.path.join(self.out_dir, 'nFR_dict.pkl'), 'rb') as f:
                self.nFR_dict = pickle.load(f)
            with open(os.path.join(self.out_dir, 'fr_dict.pkl'), 'rb') as f:
                self.fr_dict = pickle.load(f)
            
            return self.fr_df_dict
        
        print("Calculating functional redundancy scores")
        self.fr_df_dict = {}
        self.sp_d = {}
        self.td_dict = {}
        self.nFR_dict = {}
        self.fr_dict = {}
        scale_exp = pd.DataFrame()
        
        from tqdm import tqdm

        for tp, tp_gcn in self.cell_type_rtf_networks.items():
            cell_sp_d = FR.cal_dist(tp_gcn.T)
            sub_meta = self.sc_meta[self.sc_meta[self.tp_key] == tp]
            
            for cell in tqdm(sub_meta.index, desc=f"Processing cells in {tp}"):
                tmp_exp_pre = pd.DataFrame(self.sc_exp.loc[cell_sp_d.columns, cell])
                
                # Skip cells with no expression
                if tmp_exp_pre.sum().sum() == 0:
                    continue
                    
                # Scale to sum 1
                tmp_exp = tmp_exp_pre.div(tmp_exp_pre.sum(axis=0), axis=1)
                scale_exp = pd.concat([scale_exp, tmp_exp], axis=1)
                
                # Calculate functional redundancy
                fr_df, fr, nFR = FR.cal_nFR(tmp_exp.T, cell_sp_d)
                if fr_df is None:
                    print(f"The total expression of {cell} is 0, please check the input data")
                self.nFR_dict[cell] = nFR
                self.fr_dict[cell] = fr
                
                # Calculate topological distance
                td = FR.cal_TD(tmp_exp.T)
                self.td_dict[cell] = td
                
                if fr_df is not None:
                    self.fr_df_dict[cell] = fr_df
                    
            self.sp_d[tp] = cell_sp_d
        
        # Save scaled expression data
        scale_exp.fillna(0, inplace=True)
        scale_exp.to_csv(os.path.join(self.out_dir, 'scale_rec_exp.tsv'), sep='\t', header=True, index=True)
        
        # Save results if caching is enabled
        if cache:
            with open(os.path.join(self.out_dir, 'fr_df_dict.pkl'), 'wb') as f:
                pickle.dump(self.fr_df_dict, f)
            with open(os.path.join(self.out_dir, 'sp_d.pkl'), 'wb') as f:
                pickle.dump(self.sp_d, f)
            with open(os.path.join(self.out_dir, 'td_dict.pkl'), 'wb') as f:
                pickle.dump(self.td_dict, f)
            with open(os.path.join(self.out_dir, 'nFR_dict.pkl'), 'wb') as f:
                pickle.dump(self.nFR_dict, f)
            with open(os.path.join(self.out_dir, 'fr_dict.pkl'), 'wb') as f:
                pickle.dump(self.fr_dict, f)
        
        return self.fr_df_dict