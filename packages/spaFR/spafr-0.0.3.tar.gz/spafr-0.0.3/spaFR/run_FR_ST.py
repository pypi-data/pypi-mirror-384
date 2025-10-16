import os
import pickle
import utils
import pandas as pd
from tqdm import tqdm

import FR


class SpatialFRAnalyzer:
    """
    Spatial Functional Redundancy Analysis tool for single-cell expression data with spatial context.
    
    This class provides a comprehensive API for analyzing functional redundancy
    patterns across different cell types using spatially-resolved single-cell expression data.
    
    Attributes:
        st_exp (pd.DataFrame): Single-cell expression matrix (genes × cells)
        st_meta (pd.DataFrame): Metadata with cell type annotations and spatial coordinates
        tp_key (str): Column name for cell type in metadata
        x_colname (str): Column name for x-coordinate in metadata
        y_colname (str): Column name for y-coordinate in metadata
        species (str): Species name ('Human' or 'Mouse')
        out_dir (str): Output directory for results
        lr_graph_dict (dict): Dictionary of ligand-receptor graphs for each cell
        cell_type_lr_networks (dict): Dictionary of GTN data by cell type
        fr_df_dict (dict): Dictionary of functional redundancy scores by cell
        tp_fr_dict (dict): Dictionary of merged FR data by cell type
        coordinates (pd.DataFrame): DataFrame containing spatial coordinates
    """

    def __init__(self, expression_data=None, meta_data=None, 
                 x_colname='x', y_colname='y',
                 cell_type_column=None, 
                 species="Human", out_dir="./results"):
        """
        Initialize the SpatialFunctionalRedundancyAnalyzer object.
        
        Args:
            expression_data (pd.DataFrame, optional): Expression matrix, genes(rows) x cells(column)
            meta_data (pd.DataFrame, optional): Metadata, cells(row) x features(columns)
            x_colname (str, optional): Column name for x-coordinate in metadata
            y_colname (str, optional): Column name for y-coordinate in metadata
            cell_type_column (str, optional): Column name for cell type in metadata
            species (str, optional): Species name ('Human' or 'Mouse')
            out_dir (str, optional): Output directory for results
        """
        self.st_exp = expression_data
        self.st_meta = meta_data
        self.x_colname = x_colname
        self.y_colname = y_colname
        self.tp_key = cell_type_column
        self.species = species
        self.out_dir = out_dir
        
        # Initialize data containers
        self.coordinates = self.st_meta[[self.x_colname, self.y_colname]].copy()
        self.pathway = None
        self.lr_df = None
        self.lr_graph_dict = {}
        self.cell_type_lr_networks = {}
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
            self.st_exp = self.st_exp.loc[~((self.st_exp.index.duplicated()) & 
                                           (self.st_exp.sum(axis=1) == 0))]
            
            # Set cell type column
            if not self.tp_key in self.st_meta.columns:
                raise ValueError(f"Cell type column '{self.tp_key}' not found in metadata")

            print(f"Loaded expression data: {self.st_exp.shape[0]} genes, {self.st_exp.shape[1]} cells")
            print(f"Loaded metadata: {self.st_meta.shape[0]} cells")
            
            return self
            
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            raise
    
    def load_lr_data(self, lr_data=None):
        """
        Load ligand-receptor pair data.
        
        Args:
            lr_data (pd.DataFrame, optional): Ligand-receptor pairs data. If None, loads from default directory.

        Returns:
            self: Returns self for method chaining
        """
        try:
            # Handle user-provided data
            if lr_data is not None:
                self.lr_df = lr_data
            # Load default data if lr_data is still None
            if self.lr_df is None:
                _, default_lr = utils.load_pathway_lr()
                self.lr_df = default_lr

                if self.lr_df is None:
                    self.lr_df = default_lr
                    
            print(f"Loaded {self.lr_df.shape[0]} ligand-receptor pairs")
            
            return self
        except Exception as e:
            print(f"Error loading ligand-receptor data: {e}")
            return self
        

    def filter_lr_data(self):
        """
        Filter ligand-receptor pairs based on expression data.
        """
        # self.lr_df = FR.filter_lr(self.st_exp, self.lr_df, self.species)
        self.lr_df = self.lr_df[(self.lr_df['ligand'].isin(self.st_exp.index)) & 
                                       (self.lr_df['receptor'].isin(self.st_exp.index))]
        if self.lr_df.empty:
            print("No common ligand-receptor pairs found.")
        return self


    def calculate_knn(self, k=6):
        """Calculate K-nearest neighbors based on spatial coordinates"""
        self.k = k
        self.knn_dict = FR.findCellKNN(self.coordinates, k=self.k)
        print(f"Cell KNN calculated with k={k}")


    def build_ligand_receptor_networks(self, cache=True):
        """
        Build ligand-receptor network for each cell based on expression data and K-nearest neighbors.
        
        This function:
        1. Checks if cached networks exist and loads them if requested
        2. Iterates through each cell and its neighbors
        3. Extracts ligand expression for the center cell
        4. Extracts receptor expression for neighboring cells
        5. Creates an interaction matrix between ligands and receptors
        6. Filters out ligands with no receptors
        7. Stores and optionally caches the resulting networks
        
        Parameters:
        -----------
        cache : bool, default=True
            Whether to use cached results if available and save new results to cache
        
        Returns:
        --------
        dict
            Dictionary where keys are cell IDs and values are DataFrames representing 
            ligand-receptor interaction networks
        """
        # Define cache file path
        cache_file = os.path.join(self.out_dir, 'lr_graph_dict.pkl')
        
        # Check if cache exists and should be used
        if cache and os.path.exists(cache_file):
            print(f"Loading cached ligand-receptor networks from {cache_file}")
            with open(cache_file, 'rb') as f:
                self.lr_graph_dict = pickle.load(f)
            print(f"Loaded {len(self.lr_graph_dict)} ligand-receptor networks from cache")
            return self.lr_graph_dict
        
        # Initialize storage for networks if not already done
        if not hasattr(self, 'lr_graph_dict'):
            self.lr_graph_dict = {}
        
        print("Building ligand-receptor networks...")
        
        # Ensure ligand_receptor_pairs is initialized with correct columns
        if not hasattr(self, 'ligand_receptor_pairs') or 'ligand' not in self.ligand_receptor_pairs.columns or 'receptor' not in self.ligand_receptor_pairs.columns:
            # Create a DataFrame with all possible ligand-receptor pairs
            self.ligand_receptor_pairs = self.lr_df.copy()
            # Add a column for interaction values
            self.ligand_receptor_pairs['interaction_score'] = 0
        
        for cell_id, neighbor_ids in tqdm(self.knn_dict.items(), desc="Processing cells"):
            try:
                # Get ligand expression for the center cell
                ligand_expression = self.st_exp[cell_id]
                ligand_expression = ligand_expression.loc[self.lr_df['ligand']]
                ligand_expression = (ligand_expression > 0).astype(int)
                
                # Get receptor expression for the neighboring cells
                receptor_expression = self.st_exp[neighbor_ids]
                receptor_expression = (receptor_expression > 0).astype(int) 
                receptor_median = receptor_expression.loc[self.lr_df['receptor']].median(axis=1)
                
                # Calculate interaction score (ligand × receptor)
                interaction_scores = ligand_expression * receptor_median.values
                # Update the interaction values in ligand_receptor_pairs
                self.ligand_receptor_pairs['interaction_score'] = interaction_scores.values
                # Create an interaction matrix (ligands as rows, receptors as columns)
                interaction_matrix = self.ligand_receptor_pairs.pivot_table(
                    index='ligand', 
                    columns='receptor', 
                    values='interaction_score'
                )
                interaction_matrix.fillna(0, inplace=True)
                
                # Binarize interactions (0 or 1)
                interaction_matrix[interaction_matrix != 0] = 1
                
                # Filter out ligands with no receptors
                ligand_sums = interaction_matrix.sum(axis=1)
                interaction_matrix = interaction_matrix.loc[ligand_sums[ligand_sums > 0].index]
                
                # Store the network
                self.lr_graph_dict[cell_id] = interaction_matrix
                
            except KeyError as e:
                print(f"Warning: Skipping cell {cell_id} due to KeyError: {e}")
            except Exception as e:
                print(f"Warning: Error processing cell {cell_id}: {e}")
        
        print(f"Built ligand-receptor networks for {len(self.lr_graph_dict)} cells")
        
        # Cache the results if requested
        if cache:
            print(f"Caching ligand-receptor networks to {cache_file}")
            # Ensure output directory exists
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, 'wb') as f:
                pickle.dump(self.lr_graph_dict, f)
            print("Caching complete")
    
        return self.lr_graph_dict




    def aggregate_cell_type_networks(self, cache=True):
        """
        Aggregate ligand-receptor networks for cells of the same type to enable cell-type level GTN analysis.
        
        Args:
            use_cache (bool, optional): Whether to load/save results from/to disk cache
                
        Returns:
            dict: Dictionary mapping cell types to their aggregated ligand-receptor networks
        """
        # Validate prerequisite data
        if self.st_meta is None or not self.lr_graph_dict:
            raise ValueError("Single-cell metadata and ligand-receptor graph must be loaded before aggregation")
        
        # Check for and load cached results if available
        cache_path = os.path.join(self.out_dir, 'cell_type_lr_networks.pkl')
        if cache and os.path.exists(cache_path):
            print("Loading cached cell-type ligand-receptor networks")
            with open(cache_path, 'rb') as cache_file:
                self.cell_type_lr_networks = pickle.load(cache_file)
            return self.cell_type_lr_networks
        
        print("Aggregating ligand-receptor networks by cell type")
        self.cell_type_lr_networks = {}

        from tqdm import tqdm
        for cell_type in tqdm(self.st_meta[self.tp_key].unique(), desc="Processing cell types"):
            # Get cells belonging to this cell type

            cells_in_type = self.st_meta[self.st_meta[self.tp_key] == cell_type].index
            # Collect networks for all cells of this type
            cell_networks = []
            for cell_id in cells_in_type:
                if cell_id in self.lr_graph_dict:
                    # Reset index before appending to ensure proper concatenation
                    cell_networks.append(self.lr_graph_dict[cell_id].reset_index())
            
            # Skip if no networks were found for this cell type
            if not cell_networks:
                continue
            
            # Combine all networks at once instead of incrementally
            combined_networks = pd.concat(cell_networks, ignore_index=True)
            # Calculate median values across all cells of this type
            # Use 'index' column instead of actual index
            aggregated_network = combined_networks.groupby('ligand').median()
            aggregated_network = aggregated_network.fillna(0)
            aggregated_network = aggregated_network[aggregated_network.sum(axis=1) > 0]
            # Store the aggregated network
            self.cell_type_lr_networks[cell_type] = aggregated_network
        
        # Cache results if enabled
        if cache:
            with open(cache_path, 'wb') as cache_file:
                pickle.dump(self.cell_type_lr_networks, cache_file)
        
        return self.cell_type_lr_networks
    


    def calculate_functional_redundancy(self, cache=True):
        """
        Calculate functional redundancy scores for each cell.
        
        Args:
            cache (bool, optional): Whether to cache results to disk
            
        Returns:
            dict: Dictionary of functional redundancy scores by cell
        """
        # Check if required data is loaded
        if self.st_exp is None or self.st_meta is None or not self.cell_type_lr_networks:
            raise ValueError("Expression data, metadata, and GTN data must be loaded first")
        
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

        for tp, tp_gcn in self.cell_type_lr_networks.items():
            cell_sp_d = FR.cal_dist(tp_gcn.T)
            sub_meta = self.st_meta[self.st_meta[self.tp_key] == tp]
            
            for cell in tqdm(sub_meta.index, desc=f"Processing cells in {tp}"):
                tmp_exp_pre = pd.DataFrame(self.st_exp.loc[cell_sp_d.columns, cell])
                
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