import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')


class FRNormalizer:
    def __init__(self, df, fr_col='FR', td_col='TD', class_col='Class', 
                 stage_col='Stages', grade_col='Grade', patient_col='Patient_id'):
        self.df = df.copy()
        self.fr_col = fr_col
        self.td_col = td_col
        self.class_col = class_col
        self.stage_col = stage_col
        self.grade_col = grade_col
        self.patient_col = patient_col
        self.results = {}
        
        # Generate normalized column names
        self.fr_td_ratio_col = f"{fr_col}_TD_ratio"
        self.fr_residual_global_col = f"{fr_col}_residual"
        
    def calculate_normalized_fr(self):
        """Calculate normalized FR metrics"""
        print("Calculating FR/TD ratio...")
        self.df[self.fr_td_ratio_col] = self.df[self.fr_col] / self.df[self.td_col]
        
        print("Calculating regression residuals...")
        mask = (~self.df[self.fr_col].isna()) & (~self.df[self.td_col].isna())
        if mask.sum() > 10:
            X = self.df.loc[mask, [self.td_col]].values
            y = self.df.loc[mask, self.fr_col].values
            
            reg = LinearRegression()
            reg.fit(X, y)
            
            self.df.loc[mask, self.fr_residual_global_col] = y - reg.predict(X)
            
            self.global_regression = {
                'r_squared': reg.score(X, y)
            }
            
            print(f"FR-TD correlation: r^2 = {self.global_regression['r_squared']:.3f}")
        
        return self.df
    
    def patient_level_mannwhitney(self, fr_metrics, normal_label='Normal', tumor_label='Tumor', min_cells=3):
        """
        Perform Mann-Whitney U test within each patient, then summarize across patients
        
        Parameters:
        -----------
        fr_metrics : list
            List of FR metrics to analyze
        normal_label : str
            Value in class_col representing normal tissue
        tumor_label : str
            Value in class_col representing tumor tissue
        min_cells : int
            Minimum number of cells required for each group
            
        Returns:
        --------
        tuple : (patient_df, summary_df)
            Detailed patient-level results and summary statistics
        """
        # Get eligible patients (with both normal and tumor samples)
        patient_class_counts = self.df.groupby([self.patient_col, self.class_col]).size().unstack(fill_value=0)
        eligible_patients = patient_class_counts[
            (patient_class_counts[normal_label] >= min_cells) & 
            (patient_class_counts[tumor_label] >= min_cells)
        ].index
        
        patient_results = []
        
        # Within-patient Mann-Whitney U tests
        for patient_id in eligible_patients:
            patient_subset = self.df[self.df[self.patient_col] == patient_id]
            normal_subset = patient_subset[patient_subset[self.class_col] == normal_label]
            tumor_subset = patient_subset[patient_subset[self.class_col] == tumor_label]
            
            for metric in fr_metrics:
                normal_values = normal_subset[metric].dropna()
                tumor_values = tumor_subset[metric].dropna()
                
                if len(normal_values) < min_cells or len(tumor_values) < min_cells:
                    continue
                
                # Mann-Whitney U test within patient
                try:
                    mannw_stat, mannw_pval = stats.mannwhitneyu(
                        tumor_values, normal_values, alternative='two-sided'
                    )
                except ValueError:
                    mannw_stat, mannw_pval = np.nan, 1.0
                
                patient_results.append({
                    'Patient_ID': patient_id,
                    'FR_metric': metric,
                    'MannW_pvalue': mannw_pval,
                    'Normal_Median': normal_values.median(),
                    'Tumor_Median': tumor_values.median(),
                    'Median_diff': tumor_values.median() - normal_values.median(),
                    'Significant': mannw_pval < 0.05
                })
        
        patient_df = pd.DataFrame(patient_results)
        
        # Summarize patient results and apply FDR correction
        summary_results = []
        for metric in fr_metrics:
            metric_data = patient_df[patient_df['FR_metric'] == metric]
            if len(metric_data) == 0:
                continue
                
            # Calculate median differences across patients
            median_diffs = metric_data['Median_diff'].dropna()
            if len(median_diffs) < 3:
                continue
            
            # One-sample t-test on patient differences (test if median difference ≠ 0)
            try:
                t_stat, t_pval = stats.ttest_1samp(median_diffs, 0)
            except:
                t_stat, t_pval = np.nan, np.nan
                
            # Calculate various statistics...
            
            summary_results.append({
                'FR_metric': metric,
                'One-sample t-test p-value': t_pval,
                # Other statistics...
            })
        
        summary_df = pd.DataFrame(summary_results)
        
        return patient_df, summary_df

    ##################################
    ##### Mixed Effects Analysis #####
    ##################################

    def mixed_effects_analysis(self,data, response_var, fixed_effects, group_var, 
                          verbose=True, return_results=True):
        """
        Perform mixed-effects model analysis for paired sample designs.
        
        This function fits a linear mixed-effects model to analyze differences
        between paired samples (e.g., tumor vs normal tissues) while accounting
        for repeated measurements and within-subject correlation.

        Parameters:
        -----------
        data : pandas.DataFrame
            The dataset containing all variables for analysis
        response_var : str
            The name of the dependent/response variable (e.g., 'FR')
        fixed_effects : list
        between paired samples (e.g., tumor vs normal tissues) while accounting 
        for repeated measurements and within-subject correlation.
        
        Parameters:
        -----------
        data : pandas.DataFrame
            The dataset containing all variables for analysis
        response_var : str
            The name of the dependent/response variable (e.g., 'FR')
        fixed_effects : list
            List of fixed effect variables (e.g., ['Class'])
        group_var : str
            The name of the grouping variable for random effects (e.g., 'Patient id')
        verbose : bool, default=True
            Whether to print detailed results to console
        return_results : bool, default=True
            Whether to return the model results and summary dataframe
            
        Returns:
        --------
        tuple or None
            If return_results=True, returns a tuple containing:
            - model_result: The fitted statsmodels MixedLM result object
            - results_df: A pandas DataFrame containing fixed effects estimates
            Otherwise returns None
        
        Examples:
        ---------
        >>> result, summary = mixed_effects_analysis(
        ...     data=my_data, 
        ...     response_var='FR', 
        ...     fixed_effects=['Class'], 
        ...     group_var='Patient id'
        ... )
        """
        import statsmodels.formula.api as smf
        data = data[data[response_var].notna()]
        print(f"Data shape after dropping NA in {response_var}: {data.shape}")
        # Construct formula for mixed model
        formula = f"{response_var} ~ {' + '.join(fixed_effects)}"
        
        # Fit mixed effects model
        model = smf.mixedlm(formula, data, groups=data[group_var])
        result = model.fit()
        
        if verbose:
            # Print model summary
            print(result.summary())
            
            # Extract and format fixed effects parameters
            coefs = result.fe_params
            conf_int = result.conf_int()
            pvalues = result.pvalues
            formatted_pvalues = [f"{p:.6e}" if p < 0.001 else f"{p:.6f}" for p in pvalues]

            # Create results dataframe
            results_df = pd.DataFrame({
                'Coefficient': coefs,
                'Lower_CI': conf_int[0],
                'Upper_CI': conf_int[1],
                'p_value': formatted_pvalues,
            })
            
            print("\nFixed Effects Parameter Estimates:")
            print(results_df)
            
            # Random effects parameters
            print("\nRandom Effects Parameter Estimates:")
            print(f"Between-group variance ({group_var}): {result.cov_re.iloc[0, 0]:.6f}")
        
        if return_results:
            # Extract parameters for reporting
            coefs = result.fe_params
            conf_int = result.conf_int()
            pvalues = result.pvalues
            
            # Create results dataframe
            results_df = pd.DataFrame({
                'Coefficient': coefs,
                'Lower_CI': conf_int[0],
                'Upper_CI': conf_int[1],
                'p_value': pvalues
            })
            
            return result, results_df
        
        return None


    def run_mixed_effects(self, fr_metrics=None, verbose=False, return_results=True):
        """
        Run mixed effects analysis for comparing tumor vs normal tissue
        
        Parameters:
        -----------
        fr_metrics : list or None
            List of FR metrics to analyze. If None, uses default metrics
        verbose : bool
            Whether to print detailed output
        return_results : bool
            Whether to return detailed results
            
        Returns:
        --------
        DataFrame
            Mixed effects model results
        """
        if fr_metrics is None:
            fr_metrics = [self.fr_col, self.fr_td_ratio_col, self.fr_residual_global_col]
        
        fr_metrics = [col for col in fr_metrics if col in self.df.columns]
        
        print("Running Mixed Effects Analysis...")
        
        mixed_results = pd.DataFrame()

        for metric in fr_metrics:
            print(f"\nAnalyzing {metric}...")
            try:
                model_result, results_df = self.mixed_effects_analysis(
                    data=self.df,
                    response_var=metric,
                    fixed_effects=[self.class_col],
                    group_var=self.patient_col,
                    verbose=verbose,
                    return_results=return_results
                )

                mixed_df = pd.DataFrame({
                    'Tumor Coef': results_df.loc['Class[T.Tumor]', 'Coefficient'],
                    'Tumor CI Low': results_df.loc['Class[T.Tumor]', 'Lower_CI'],
                    'Tumor CI High': results_df.loc['Class[T.Tumor]', 'Upper_CI'],
                    'Tumor p-val': results_df.loc['Class[T.Tumor]', 'p_value'],
                    'Group Coef': results_df.loc['Group Var', 'Coefficient'],
                    'Group CI Low': results_df.loc['Group Var', 'Lower_CI'],
                    'Group CI High': results_df.loc['Group Var', 'Upper_CI'],
                    'Group p-val': results_df.loc['Group Var', 'p_value'],
                    'Int. Coef': results_df.loc['Intercept', 'Coefficient'],
                    'Int. CI Low': results_df.loc['Intercept', 'Lower_CI'],
                    'Int. CI High': results_df.loc['Intercept', 'Upper_CI'],
                    'Int. p-val': results_df.loc['Intercept', 'p_value']
                }, index=[metric])
                if model_result is not None and len(results_df) > 0:
                    mixed_df['FR_metric'] = metric
                    # mixed_df['Method'] = 'Mixed Effects'
                    mixed_results = pd.concat((mixed_results, mixed_df))
                else:
                    print(f"⚠ No valid results for {metric}")
                
            except Exception as e:
                print(f"⚠ Mixed effects failed for {metric}: {e}")
                continue
        
        return mixed_results
    
    ##################################
    ######## Run Analysis ###########
    ##################################

    def run_stat_methods(self, fr_metrics=None):
        """
        Compare Patient-Level Mann-Whitney vs Mixed Effects approaches
        
        Parameters:
        -----------
        fr_metrics : list or None
            List of FR metrics to analyze. If None, uses default metrics
            
        Returns:
        --------
        tuple : (patient_stats, patient_summary, mixed_results)
            Results from both methods for comparison
        """
        if fr_metrics is None:
            fr_metrics = [self.fr_col, self.fr_td_ratio_col, self.fr_residual_global_col]

        print("=== Multiple statistical tests ===")

        # Run both analyses
        print("\n1. Patient-Level Mann-Whitney Analysis...")
        patient_stats, patient_summary = self.patient_level_mannwhitney(fr_metrics)
        
        print("\n2. Mixed Effects Analysis...")
        mixed_results = self.run_mixed_effects(fr_metrics)
        return patient_stats, patient_summary, mixed_results
    

def run_fr_analysis(df, fr_col='FR', td_col='TD', 
                   class_col='Class', patient_col='Patient_id', min_cells=3):
    """
    Run simplified fractal dimension analysis with both statistical methods
    
    Parameters:
    -----------
    df : DataFrame
        Input data with FR, TD, class and patient columns
    fr_col : str
        Column name for fractal dimension
    td_col : str
        Column name for texture dimension
    class_col : str
        Column name for sample class (tumor/normal)
    patient_col : str
        Column name for patient ID
    min_cells : int
        Minimum number of cells required for each group
        
    Returns:
    --------
    tuple : (normalized_df, patient_stats, patient_summary, mixed_results, analyzer)
        Results from analysis and the analyzer object
    """
    print("=== Simplified FR Analysis ===")
    print(f"Input data: {len(df)} samples")
    
    # Initialize analyzer
    analyzer = FRNormalizer(
        df, fr_col=fr_col, td_col=td_col, class_col=class_col, patient_col=patient_col
    )
    
    # Calculate normalized FR metrics
    print("\n1. Computing normalized FR metrics...")
    normalized_df = analyzer.calculate_normalized_fr()
    
    # Run comparison analysis
    print("\n2. Running method comparison...")
    patient_stats, patient_summary, mixed_results = analyzer.run_stat_methods()

    return normalized_df, patient_stats, patient_summary, mixed_results, analyzer


# Usage example with your mixed_effects_analysis function
# normalized_df, man_patient_stats, man_patient_summary, mixed_results, analyzer = run_fr_analysis(
#     df=sc_meta2[sc_meta2[tp_key2] == tp2],
#     fr_col='FR',
#     td_col='TD',
#     class_col=class_col2,
#     patient_col=patient_col2,
#     min_cells=3
# )




########################################
#### Centrality methods comparison #####
########################################

def compare_centrality_methods(tp_fr_dict, tp_key, output_dir, 
                              cell_types_to_use=None,
                              n_bootstrap=100, 
                              bootstrap_size=0.8, 
                              top_n_values=[10, 20, 50]):  # Use list to accept multiple top_n values
    """
    Compare network centrality methods (PageRank, Eigenvector, Degree) and evaluate stability and overlap.
    Also outputs a merged dataframe comparing rankings from all three methods and identifies
    genes that consistently rank highly across all methods.
    
    Parameters:
    -----------
    tp_fr_dict : dict
        Dictionary containing adjacency matrices for each tissue/cell type
    tp_key : str
        Key/column name for tissue/cell type
    output_dir : str
        Directory to save results
    cell_types_to_use : list, optional
        List of cell types to analyze. Default is all cell types in tp_fr_dict.
    n_bootstrap : int, optional
        Number of bootstrap iterations for stability analysis
    bootstrap_size : float, optional
        Fraction of edges to sample in bootstrap iterations
    top_n_values : list, optional
        List of top_n values to use for analysis (default: [10, 20, 50])
        
    Returns:
    --------
    dict
        Dictionary containing all analysis results
    """
    import networkx as nx
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    import os
    import warnings
    warnings.filterwarnings('ignore')
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(f"{output_dir}/figures", exist_ok=True)
    # Create subdirectories for different top_n values
    for top_n in top_n_values:
        os.makedirs(f"{output_dir}/top_{top_n}", exist_ok=True)
    
    # Fixed set of methods to use
    methods_to_use = ['pagerank', 'eigenvector', 'degree']
    method_names = {'pagerank': 'PageRank', 'eigenvector': 'Eigenvector', 'degree': 'Degree'}
    
    # Available centrality methods
    all_available_methods = {
        'pagerank': lambda G, weight: nx.pagerank(G, weight=weight),
        'eigenvector': lambda G, weight: nx.eigenvector_centrality(G, weight=weight, max_iter=1000),
        'degree': lambda G, weight: nx.degree_centrality(G)
    }
    
    # Use all cell types if none specified
    if cell_types_to_use is None:
        cell_types_to_use = list(tp_fr_dict.keys())
    else:
        # Check that specified cell types exist
        for cell_type in cell_types_to_use:
            if cell_type not in tp_fr_dict:
                print(f"Warning: Cell type '{cell_type}' not found in data")
    
    print(f"Analyzing {len(cell_types_to_use)} cell types with PageRank, Eigenvector, and Degree centrality")
    print(f"Using top_n values: {top_n_values}")
    
    # Dictionary to store results
    centrality_results = {method: pd.DataFrame() for method in methods_to_use}
    
    # Create pairs of methods for comparison
    method_pairs = ['PA_EI', 'PA_DE', 'EI_DE']
    
    # Create results tables for each top_n value
    overlap_results = {top_n: pd.DataFrame(index=cell_types_to_use, columns=method_pairs + ['Avg_Overlap']) 
                     for top_n in top_n_values}
    
    stability_cols = ['PA_Stability', 'EI_Stability', 'DE_Stability']
    stability_results = {top_n: pd.DataFrame(index=cell_types_to_use, columns=stability_cols + ['Avg_Stability']) 
                       for top_n in top_n_values}
    
    # Create merged dataframes for each cell type
    merged_rankings = {}
    
    # Dictionary to store consensus genes for each top_n
    consensus_genes = {top_n: {} for top_n in top_n_values}
    
    # Process each cell type
    for tp in cell_types_to_use:
        if tp not in tp_fr_dict:
            continue
        
        value = tp_fr_dict[tp]
        if value.empty or value.sum().sum() == 0:
            continue
            
        print(f"Processing {tp}...")
        
        # Create NetworkX graph from adjacency matrix (do this only once per cell type)
        tmp = value.reset_index()
        tmp.rename(columns={'index': 'Gene'}, inplace=True)
        melt_df = tmp.melt(id_vars='Gene')
        melt_df.columns = ['gene1','gene2','weight']
        melt_df = melt_df[melt_df['weight'] > 0]
        
        G = nx.from_pandas_edgelist(melt_df, 'gene1', 'gene2', ['weight'])
        
        # Calculate centrality for each method
        method_dfs = {}
        top_genes = {top_n: {} for top_n in top_n_values}
        
        for method in methods_to_use:
            try:
                centrality_func = all_available_methods[method]
                centrality_values = centrality_func(G, 'weight')
                
                sorted_values = sorted(centrality_values.items(), key=lambda x: x[1], reverse=True)
                tmp_result = pd.DataFrame(sorted_values, columns=['gene', 'centrality'])
                tmp_result[tp_key] = tp
                
                # Store results
                centrality_results[method] = pd.concat((centrality_results[method], tmp_result))
                
                # Store for current cell type analysis
                method_dfs[method] = tmp_result.copy()
                method_dfs[method]['source'] = method_names[method]
                
                # Store top genes for each top_n
                for top_n in top_n_values:
                    top_genes[top_n][method] = tmp_result.nlargest(top_n, 'centrality')['gene'].tolist()
                
            except Exception as e:
                print(f"{method.capitalize()} centrality failed for {tp}: {str(e)}")
                for top_n in top_n_values:
                    top_genes[top_n][method] = []
        
        # Create merged ranking dataframe for this cell type
        # First, get all unique genes across all methods
        all_genes = set()
        for method in methods_to_use:
            if method in method_dfs:
                all_genes.update(method_dfs[method]['gene'].tolist())
        
        # Create pivot table with rankings from each method
        pivot_df = pd.DataFrame()
        pivot_df['Gene'] = list(all_genes)
        
        # Add ranks from each method
        for method in methods_to_use:
            if method in method_dfs:
                temp_df = method_dfs[method][['gene', 'centrality']]
                temp_df['rank'] = temp_df['centrality'].rank(ascending=False)
                temp_df['rank'] = temp_df['rank'].astype(int)
                
                # Merge with pivot table
                pivot_df = pivot_df.merge(
                    temp_df[['gene', 'rank', 'centrality']], 
                    left_on='Gene', 
                    right_on='gene', 
                    how='left'
                )
                pivot_df.drop('gene', axis=1, inplace=True)
                pivot_df.rename(columns={
                    'rank': f'{method_names[method]} Rank',
                    'centrality': f'{method_names[method]} Score'
                }, inplace=True)
        
        # Add cell type info
        pivot_df[tp_key] = tp
        
        # Add a consensus rank (average of available ranks)
        rank_cols = [col for col in pivot_df.columns if 'Rank' in col]
        if rank_cols:
            pivot_df['Consensus Rank'] = pivot_df[rank_cols].mean(axis=1)
            pivot_df = pivot_df.sort_values('Consensus Rank')
        
        # Find genes that appear in top ranks of all methods for each top_n value
        for top_n in top_n_values:
            # Create a column indicating if gene is in top_n for each method
            for method in methods_to_use:
                method_col = f'{method_names[method]} Rank'
                if method_col in pivot_df.columns:
                    pivot_df[f'{method_names[method]} Top{top_n}'] = pivot_df[method_col] <= top_n
            
            # Identify consensus genes (in top N for all methods)
            top_cols = [col for col in pivot_df.columns if f'Top{top_n}' in col]
            if len(top_cols) == len(methods_to_use):  # Only if we have data for all methods
                pivot_df[f'In_All_Top{top_n}'] = pivot_df[top_cols].all(axis=1)
                consensus_genes[top_n][tp] = pivot_df[pivot_df[f'In_All_Top{top_n}']].copy()
            else:
                consensus_genes[top_n][tp] = pd.DataFrame()  # Empty DataFrame if missing data
                
        # Store merged rankings for this cell type
        merged_rankings[tp] = pivot_df
        
        # Save the merged rankings for this cell type
        pivot_df.to_csv(f'{output_dir}/{tp}_merged_rankings.tsv', sep='\t', index=False)
        
        # For each top_n value, calculate overlap and stability
        for top_n in top_n_values:
            # Calculate overlap between methods
            if ('pagerank' in top_genes[top_n] and 'eigenvector' in top_genes[top_n] and 
                len(top_genes[top_n]['pagerank']) > 0 and len(top_genes[top_n]['eigenvector']) > 0):
                overlap_results[top_n].loc[tp, 'PA_EI'] = (
                    len(set(top_genes[top_n]['pagerank']) & set(top_genes[top_n]['eigenvector'])) / top_n
                )
            
            if ('pagerank' in top_genes[top_n] and 'degree' in top_genes[top_n] and 
                len(top_genes[top_n]['pagerank']) > 0 and len(top_genes[top_n]['degree']) > 0):
                overlap_results[top_n].loc[tp, 'PA_DE'] = (
                    len(set(top_genes[top_n]['pagerank']) & set(top_genes[top_n]['degree'])) / top_n
                )
            
            if ('eigenvector' in top_genes[top_n] and 'degree' in top_genes[top_n] and 
                len(top_genes[top_n]['eigenvector']) > 0 and len(top_genes[top_n]['degree']) > 0):
                overlap_results[top_n].loc[tp, 'EI_DE'] = (
                    len(set(top_genes[top_n]['eigenvector']) & set(top_genes[top_n]['degree'])) / top_n
                )
            
            # Average overlap
            valid_overlaps = [
                overlap_results[top_n].loc[tp, pair] 
                for pair in method_pairs 
                if not pd.isna(overlap_results[top_n].loc[tp, pair])
            ]
            overlap_results[top_n].loc[tp, 'Avg_Overlap'] = np.mean(valid_overlaps) if valid_overlaps else np.nan
            
            # Calculate stability via bootstrap for this top_n
            np.random.seed(42)
            stability_scores = {}
            
            for method in methods_to_use:
                if method not in top_genes[top_n] or not top_genes[top_n][method]:
                    continue
                    
                bootstrap_rankings = []
                for _ in range(n_bootstrap):
                    try:
                        # Sample edges
                        sampled_edges = melt_df.sample(frac=bootstrap_size)
                        
                        # Create sampled graph
                        G_sample = nx.from_pandas_edgelist(sampled_edges, 'gene1', 'gene2', ['weight'])
                        
                        # Calculate centrality
                        centrality_func = all_available_methods[method]
                        centrality_values = centrality_func(G_sample, 'weight')
                        
                        # Get top N
                        sorted_centrality = sorted(centrality_values.items(), key=lambda x: x[1], reverse=True)
                        bootstrap_topN = [item[0] for item in sorted_centrality[:top_n]]
                        bootstrap_rankings.append(bootstrap_topN)
                    except:
                        continue
                
                # Calculate Jaccard stability
                if bootstrap_rankings:
                    jaccard_scores = []
                    for bootstrap_top in bootstrap_rankings:
                        jaccard = len(set(top_genes[top_n][method]) & set(bootstrap_top)) / len(set(top_genes[top_n][method]) | set(bootstrap_top))
                        jaccard_scores.append(jaccard)
                    stability_scores[method] = np.mean(jaccard_scores)
            
            # Add stability scores to results
            method_abbrevs = {'pagerank': 'PA', 'eigenvector': 'EI', 'degree': 'DE'}
            for method, abbrev in method_abbrevs.items():
                if method in stability_scores:
                    stability_results[top_n].loc[tp, f"{abbrev}_Stability"] = stability_scores[method]
            
            # Average stability
            valid_stabilities = [s for s in stability_scores.values() if not np.isnan(s)]
            stability_results[top_n].loc[tp, 'Avg_Stability'] = np.mean(valid_stabilities) if valid_stabilities else np.nan
    
    # Save individual method results after processing all cell types
    for method, df in centrality_results.items():
        df.to_csv(f'{output_dir}/{method}_results.tsv', sep='\t', index=False)
    
    # Save results for each top_n value
    for top_n in top_n_values:
        # Create a directory for this top_n value
        top_n_dir = f'{output_dir}/top_{top_n}'
        
        # Save overlap and stability results
        overlap_results[top_n].to_csv(f'{top_n_dir}/overlap_results.tsv', sep='\t')
        stability_results[top_n].to_csv(f'{top_n_dir}/stability_results.tsv', sep='\t')
        
        # Save consensus genes that rank highly in all methods for this top_n
        all_consensus = pd.concat([df for df in consensus_genes[top_n].values() if not df.empty])
        if not all_consensus.empty:
            all_consensus.to_csv(f'{top_n_dir}/consensus_genes.tsv', sep='\t', index=False)
    
    # Create a combined merged ranking file with all cell types
    all_merged = pd.concat(merged_rankings.values())
    all_merged.to_csv(f'{output_dir}/all_merged_rankings.tsv', sep='\t', index=False)
    
    # Find best method for each top_n
    best_methods = {}
    for top_n in top_n_values:
        best_method_col = stability_results[top_n][stability_cols].mean().idxmax()
        if best_method_col == 'PA_Stability':
            best_methods[top_n] = ('PageRank', 'pagerank')
        elif best_method_col == 'EI_Stability':
            best_methods[top_n] = ('Eigenvector', 'eigenvector')
        elif best_method_col == 'DE_Stability':
            best_methods[top_n] = ('Degree', 'degree')
    
    # Generate a comprehensive report
    with open(f'{output_dir}/centrality_comparison_report.txt', 'w') as f:
        f.write("NETWORK CENTRALITY COMPARISON REPORT\n")
        f.write("====================================\n\n")
        
        f.write("1. OVERVIEW\n")
        f.write("-----------\n")
        f.write(f"Cell types analyzed: {len(cell_types_to_use)}\n")
        f.write(f"Centrality measures compared: PageRank, Eigenvector, Degree\n")
        f.write(f"Top-N thresholds used: {top_n_values}\n\n")
        
        f.write("2. METHOD STABILITY BY TOP-N\n")
        f.write("---------------------------\n")
        for top_n in top_n_values:
            f.write(f"Top-{top_n} stability:\n")
            avg_stability = stability_results[top_n][stability_cols].mean().sort_values(ascending=False)
            for col, stability in avg_stability.items():
                method_name = col.split('_')[0]
                if method_name == 'PA':
                    method_name = 'PageRank'
                elif method_name == 'EI':
                    method_name = 'Eigenvector'
                elif method_name == 'DE':
                    method_name = 'Degree'
                f.write(f"  {method_name} Centrality: {stability:.3f}\n")
            f.write("\n")
        
        f.write("3. TOP-N OVERLAP BETWEEN METHODS\n")
        f.write("-------------------------------\n")
        for top_n in top_n_values:
            f.write(f"Top-{top_n} average overlap:\n")
            avg_overlap = overlap_results[top_n][method_pairs].mean().sort_values(ascending=False)
            for pair, overlap in avg_overlap.items():
                if pair == 'PA_EI':
                    methods = 'PageRank-Eigenvector'
                elif pair == 'PA_DE':
                    methods = 'PageRank-Degree'
                elif pair == 'EI_DE':
                    methods = 'Eigenvector-Degree'
                f.write(f"  {methods}: {overlap:.3f}\n")
            f.write("\n")
        
        f.write("4. RECOMMENDED METHOD BY TOP-N\n")
        f.write("-----------------------------\n")
        for top_n in top_n_values:
            best_method_name, _ = best_methods[top_n]
            f.write(f"Top-{top_n}: {best_method_name} Centrality\n")
        f.write("\n")
        
        f.write("5. CONSENSUS GENES BY TOP-N\n")
        f.write("--------------------------\n")
        for top_n in top_n_values:
            f.write(f"Top-{top_n} consensus genes (in all three methods):\n")
            
            # Count consensus genes across all cell types
            consensus_count = sum(1 for tp in consensus_genes[top_n] if tp in consensus_genes[top_n] and not consensus_genes[top_n][tp].empty)
            total_genes = sum(len(df) for df in consensus_genes[top_n].values() if not df.empty)
            
            f.write(f"  {consensus_count} cell types have consensus genes, total {total_genes} consensus genes\n\n")
            
            # Report consensus genes by cell type
            for tp in cell_types_to_use:
                if tp in consensus_genes[top_n] and not consensus_genes[top_n][tp].empty:
                    f.write(f"  {tp}: {len(consensus_genes[top_n][tp])} genes\n")
                    for gene in consensus_genes[top_n][tp]['Gene'][:10]:  # List up to 10 genes
                        f.write(f"    - {gene}\n")
                    if len(consensus_genes[top_n][tp]) > 10:
                        f.write(f"    - ... and {len(consensus_genes[top_n][tp])-10} more\n")
                    f.write("\n")
    
    # Return results dictionary
    return {
        'overlap': overlap_results,
        'stability': stability_results,
        'best_methods': best_methods,
        'results': {method: df for method, df in centrality_results.items()},
        'merged_rankings': merged_rankings,
        'all_merged': all_merged,
        'consensus_genes': consensus_genes,
        'top_n_values': top_n_values
    }


def plot_method_stability_comparison(all_stab_res, output_dir='stability_figures'):
    """
    Create a plot comparing the stability of different centrality methods across different top_n values.
    
    Parameters:
    -----------
    all_stab_res : pandas.DataFrame
        DataFrame containing stability results with columns:
        - 'Top_N': the top_n threshold values
        - 'PA_Stability', 'EI_Stability', 'DE_Stability': stability scores for each method
    output_dir : str, optional
        Directory to save the output figure (default: 'stability_figures')
    
    Returns:
    --------
    None
        Saves the plot to file and displays it.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    import os
    
    # Create directory for saving results
    os.makedirs(output_dir, exist_ok=True)
    
    # Set up an aesthetically pleasing chart style
    sns.set(style="whitegrid")
    plt.rcParams.update({
        'font.family': 'Arial', 
        'font.size': 12,
        'figure.figsize': (12, 8)
    })
    
    # Create figure
    plt.figure(figsize=(5, 4))
    top_n_values = sorted(all_stab_res['Top_N'].unique())
    
    # Define methods with their colors and markers
    methods = ['PA_Stability', 'EI_Stability', 'DE_Stability']
    method_names = {'PA_Stability': 'PageRank', 'EI_Stability': 'Eigenvector', 'DE_Stability': 'Degree'}
    method_colors = {'PA_Stability': '#1f77b4', 'EI_Stability': '#ff7f0e', 'DE_Stability': '#2ca02c'}
    method_markers = {'PA_Stability': 'o', 'EI_Stability': 's', 'DE_Stability': '^'}
    
    # Calculate average stability for each method at each top_n value
    for method in methods:
        avg_by_topn = []
        std_by_topn = []  # Also calculate standard deviation for error bars
        
        for n in top_n_values:
            values = all_stab_res[all_stab_res['Top_N'] == n][method]
            avg_by_topn.append(values.mean())
            std_by_topn.append(values.std())
        
        # Draw line chart with error bars
        plt.errorbar(
            top_n_values, 
            avg_by_topn, 
            yerr=std_by_topn,
            fmt=f'-{method_markers[method]}',
            capsize=4,
            linewidth=2,
            markersize=8, 
            color=method_colors[method],
            label=method_names[method]
        )
    
    # Set chart title and labels
    plt.xlabel('Top N', fontsize=14, fontweight='bold')
    plt.ylabel('Average stability score', fontsize=14, fontweight='bold')
    plt.title('Comparison of centrality methods stability', fontsize=16, fontweight='bold')
    
    # Set X-axis ticks to actual top_n values
    plt.xticks(top_n_values, top_n_values, fontsize=12)
    
    # Set Y-axis range, adjusting based on the data
    y_min = max(0.5, all_stab_res[methods].min().min() - 0.05)
    y_max = min(1.0, all_stab_res[methods].max().max() + 0.05)
    plt.ylim(y_min, y_max)
    
    # Add legend
    plt.legend(fontsize=12, loc='lower right')
    
    # Add grid lines for better readability
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Save the chart
    plt.savefig(f'{output_dir}/centrality_comparison_by_topn.pdf', bbox_inches='tight')
    
    # Display the chart
    plt.show()