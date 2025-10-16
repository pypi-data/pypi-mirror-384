import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from statannot import add_stat_annotation
import matplotlib as mpl
mpl.rcParams['pdf.fonttype'] = 42
# from matplotlib_venn import venn2
import scipy.stats as st


def boxplot(data = None, palette_dict = None, box_pairs = [],
                 x = 'method', y = 'pair_num', hue='method',figsize = (2.4, 3),
                 ylabel='LRI count', dodge=False,legend = False,
                 test = 't-test_ind',rotate_x = False,
                 savefig = False, title = None):
    '''
    @ Wang Jingwan 0314
    test method can choose from 
    't-test_welch', 't-test_paired', 'Mann-Whitney', 'Mann-Whitney-gt', 
    'Mann-Whitney-ls', 'Levene', 'Wilcoxon', 'Kruskal', 'Brunner-Munzel'
    '''

    from statannot import add_stat_annotation
    # import itertools
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    plt.figure(figsize=figsize)
    ax = sns.boxplot(x=x, y=y, data=data, hue=hue, 
                     dodge=dodge, palette=palette_dict,
                     width=.8, showfliers = False)
    categories = data[hue].unique()
    # pairs = list(itertools.combinations(categories, 2))
    add_stat_annotation(ax,data=data, x=x, y=y, 
                        box_pairs=box_pairs, test=test, text_format='star', loc='inside', verbose=2)
    plt.tight_layout()
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    plt.xlabel('', size=16)
    plt.ylabel(ylabel, size=16)
    plt.title(title,size = 22)
    if rotate_x:
        plt.xticks(rotation=90)

    if legend:
        # plt.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
        leg = ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.16), ncol=3,
                        handletextpad=0.3,columnspacing=0.3,fontsize = 14)
        leg.get_frame().set_linewidth(0.0)  # Remove legend frame
    else:
        plt.legend([],[], frameon=False)




def batch_boxplot(data = None, x = None, y = None, hue = None, box_pairs = None, test_method = 'Mann-Whitney', palette_dict = [], 
                  row = 'cell_type', col = 'treatment_phase',
                  legend=False, xlabel='', ylabel='', rotate_x=False, title=None, savefig=''):
    """
    Plot subplots with statistical annotations.
    
    Parameters:
    data (pandas.DataFrame): Input data
    x (str): Variable for x-axis
    y (str): Variable for y-axis
    hue (str): Variable for color encoding
    box_pairs (list): Pairs of groups to perform statistical test on
    test_method (str): Statistical test method
    legend (bool): Whether to display the legend
    xlabel (str): Label for x-axis
    ylabel (str): Label for y-axis
    rotate_x (bool): Whether to rotate the x-axis labels
    title (str): Title of the plot
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    # from statannot import add_stat_annotation
    if len(data[col].unique())*len(data[row].unique()) >10:
        ROW = len(data[col].unique())*len(data[row].unique()) // 10 + 1
        COL = int(np.ceil(len(data[col].unique()) / ROW))
    else:
        ROW = len(data[row].unique())
        COL = int(len(data[col].unique()))
    print(f'Plotting {ROW} rows and {COL} columns of subplots.')
    ROW_L = 5
    COL_L = 3.5
    plt.figure(figsize=(COL_L*COL, ROW_L* ROW))
    
    i = 0
    for tp in data[row].unique():
        for treatment_phase in data[col].unique():
            i += 1
            plt.subplot(ROW, COL, i)
            
            sub_data = data[(data[row] == tp) & (data[col] == treatment_phase)]
            ax = sns.boxplot(data=sub_data, x=x, y=y, hue=hue, showfliers=False, dodge=False, 
                            palette=palette_dict)
            # print(sub_data)
            plt.title(f'{treatment_phase}', fontsize=26)
            if test_method is not None:
                add_stat_annotation(ax, data=sub_data, x=x, y=y, box_pairs=box_pairs, test=test_method, 
                                text_format='star', loc='inside', verbose=2)
            
            plt.tight_layout()
            plt.xticks(fontsize=22)
            plt.yticks(fontsize=18)
            plt.xlabel(xlabel, size=24)
            plt.ylabel(ylabel, size=24)
            
            if rotate_x:
                plt.xticks(rotation=90)
            
            if legend:
                leg = ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.16), ncol=3,
                               handletextpad=0.3, columnspacing=0.3, fontsize=14)
                leg.get_frame().set_linewidth(0.0)
            else:
                plt.legend([], [], frameon=False)
            if savefig:
                plt.savefig(f'{savefig}')
            
            

def clustermap(df, log = False, scale = False, row_cluster = True, col_cluster = True,dendrogram_ratio = 0.001,
                 value = '', cmap = 'coolwarm', title = '',figsize = (5,5),
                 highlight = None,   rotate_x = True,
                 xticks = True, yticks = True, 
                 xlabel = True, ylabel = True, cbar_x = 1.2,
                 col_colors = None, row_colors = None,
                 savefig = False):
    '''
    df: dataframe
    if df has there columns and required to be pivot, then use the following parameters
    otherwise set aggfunc as None
        index: row index
        col: column index
        value: value to fill the pivot table
        aggfunc: how to aggregate the value
    log: log the value or not
    row_cluster: cluster row or not
    col_cluster: cluster column or not
    highlight: highlight the rows
    title: title of the plot
    cmap: color map of heatmap
    col_color: color of the column [sorted by the df row's order]
    xticks: show xticks or not
    yticks: show yticks or not
    savefig: output directory
    '''
    n_tp_lri = df.copy()
    n_tp_lri = n_tp_lri.fillna(0)
    if log:
        n_tp_lri = np.log(n_tp_lri + 1)
        legend_label = f'{value} (log)'
    else:
        legend_label = f'{value}'

    if scale == True:
        n_tp_lri = n_tp_lri.apply(lambda x: (x - np.min(x)) / (np.max(x) - np.min(x)))
        
    clustermap = sns.clustermap(n_tp_lri,row_cluster=row_cluster,col_cluster=col_cluster,
               standard_scale=None,dendrogram_ratio=dendrogram_ratio,cmap = cmap, col_colors = col_colors,row_colors = row_colors,
               figsize=figsize, cbar_pos=(cbar_x, 0.5, 0.02, 0.2),cbar_kws={'orientation': 'vertical','label':legend_label})
    if not xticks:
        clustermap.ax_heatmap.set_xticklabels([])
        clustermap.ax_heatmap.set_xticks([])
    else:
        clustermap.ax_heatmap.xaxis.label.set_size(18)
        clustermap.ax_heatmap.xaxis.set_tick_params(labelsize=16)

    
    if not yticks:
        clustermap.ax_heatmap.set_yticklabels([])
        clustermap.ax_heatmap.set_yticks([])
    else:
        clustermap.ax_heatmap.yaxis.label.set_size(18)
        clustermap.ax_heatmap.yaxis.set_tick_params(labelsize=16)

    if not xlabel:
        clustermap.ax_heatmap.set_xlabel('')
    else:
        if xlabel != True:
            clustermap.ax_heatmap.set_xlabel(xlabel)
    if not ylabel:
        clustermap.ax_heatmap.set_ylabel('')
    else:
        if ylabel != True:
            clustermap.ax_heatmap.set_ylabel(ylabel)

    if highlight is not None:
        arr = n_tp_lri.index.to_list()
        if row_cluster:
            # Reorganize the index labels based on the cluster order
            reordered_index = [arr[i] for i in clustermap.dendrogram_row.reordered_ind]
            # Customize the ytick color and font weight
            yticks, _ = plt.yticks()
            ytick_labels = clustermap.ax_heatmap.get_yticklabels()
            for index, ytick_label in enumerate(ytick_labels):
                if reordered_index[index] in highlight:
                    ytick_label.set_color('red')
                    ytick_label.set_weight('bold')
        else:
            highlighted_ytick = np.where(np.isin(arr, highlight))[0]
            print(highlighted_ytick) # The ytick to be highlighted
            # Customize the ytick color
            _, yticks = plt.yticks()
            print(yticks)
            ytick_labels = clustermap.ax_heatmap.get_yticklabels()
            for index, ytick_label in enumerate(ytick_labels):
                if arr[index] in highlight:
                    ytick_label.set_color('red')
                    ytick_label.set_weight('bold')
    if title:
        clustermap.ax_heatmap.set_title(title,fontsize=18, y = 1.05) 

    if savefig:
        plt.savefig(f'{savefig}')

    # plt.xticks(fontsize=16)
    # plt.yticks(fontsize=16)

    if rotate_x:
        # print('r')
        plt.xticks(fontsize=16, rotation=90)
    plt.show()






def regplot(x, y, hue=None, palette_dict = None, hue_values=None, show_corr=True, legend_on=True, out = False,
            **kwargs):
    '''
    Parameters
    ----------
    x : array-like
        x-axis data
    y : array-like
        y-axis data
    hue : array-like
        hue data
    palette_dict : dict 
        color palette
    hue_values : array-like 
        unique values of hue
    show_corr : bool
        show correlation coefficient
    legend_on : bool
        show legend
    kwargs : dict
        other parameters for seaborn
    '''
    import seaborn
    if hue is None:
        hue_cor = st.pearsonr(x, y)[0]
        if show_corr:
            _label = "R=%.2f" %(hue_cor)
        else:
            _label = None
        ax = seaborn.regplot(x, y, label=_label, **kwargs)
    else:
        hue_cor = {}
        if hue_values is None:
            hue_values = np.unique(hue)
        for hue_val in hue_values:
            _idx = hue == hue_val
            cor = st.pearsonr(x[_idx], y[_idx])[0]
            hue_cor[hue_val] = cor
            if show_corr:
                _label = str(hue_val) + ": R=%.2f" %(
                    cor)
            else:
                _label = None
            
            ax = seaborn.regplot(x[_idx], y[_idx], label=_label, color = palette_dict[hue_val], **kwargs)
            # ax = seaborn.lmplot(x = 'ST', y = 'X', hue = 'hue',data = df, label=_label, palette=palette_dict)
    
    if legend_on:
        plt.legend()
    if out:
        return hue_cor



##################################################
############## FR vs Stage boxplot ###############
##################################################

def plot_stage_vs_fr_with_significance(valid_data, col='Stage', fr_col='FR', type_col='Type', 
                                     figsize=(6, 3), title = 'Cohort 1', savefig=''):
    from scipy.stats import mannwhitneyu
    
    # Set up color palette
    # palette = {'Early': '#63C1A3', 'Late': '#E88AC2'}
    palette = {'Early': '#bcbddc', 'Late': '#756bb1'}
    # Get unique types
    types = valid_data[type_col].unique()
    
    # Create subplot figure
    fig, axes = plt.subplots(1, len(types), figsize=figsize, sharey=True)
    
    if len(types) == 1:
        axes = [axes]
    
    # Get overall y_max for consistent significance bar positioning
    y_max = valid_data[fr_col].max()
    y_increment = y_max * 0.03
    
    # Loop through each type and create subplot
    for i, type_val in enumerate(types):
        # Filter data for this type
        type_data = valid_data[valid_data[type_col] == type_val]
        
        # Create the main boxplot with custom palette
        box = sns.boxplot(
            x=col, 
            y=fr_col, 
            data=type_data,
            palette=palette,
            width=0.6,
            boxprops={'alpha': 0.8, 'edgecolor': 'black', 'linewidth': 1},
            ax=axes[i],
            showfliers=False,  # Hide outliers
        )
        
        # Significance testing
        stages = type_data[col].unique()
        early_data = type_data[type_data[col] == stages[0]][fr_col].dropna()
        late_data = type_data[type_data[col] == stages[-1]][fr_col].dropna()
        
        if len(early_data) > 0 and len(late_data) > 0:  # Check if we have data to compare
            stat, p_value = mannwhitneyu(early_data.values, late_data.values)
            print(f'{type_val} - {stages[0]} vs {stages[-1]}: p-value = {p_value}')
            
            if p_value < 0.05:
                # Calculate x positions for significance bar
                x1 = 0 - 0.2  # Position for early stage
                x2 = 1 + 0.2  # Position for late stage
                
                # Calculate y position for significance bar
                y_pos = y_max + y_increment
                
                # Draw the significance bar
                axes[i].plot([x1, x1, x2, x2], 
                        [y_pos, y_pos + y_increment, y_pos + y_increment, y_pos], 
                        lw=1.5, c='black')
                
                # Add significance annotation
                if p_value < 0.0001:
                    sig_symbol = '****'
                elif p_value < 0.001:
                    sig_symbol = '***'
                elif p_value < 0.01:
                    sig_symbol = '**'
                elif p_value < 0.05:
                    sig_symbol = '*'
                
                axes[i].text((x1 + x2) * 0.5, y_pos + y_increment, 
                        sig_symbol, ha='center', va='bottom')
        
        # Styling
        axes[i].grid(False)
        for spine in axes[i].spines.values():
            spine.set_edgecolor('black')
            spine.set_linewidth(1)
        
        # Set titles and labels
        # axes[i].set_title(f"{type_val}", fontsize=14)
        axes[i].set_title(f"{title}", fontsize=14)
        axes[i].set_xlabel("")
        if i == 0:
            axes[i].set_ylabel(f"{fr_col}", fontsize=14)
        else:
            axes[i].set_ylabel("")
        axes[i].tick_params(axis='x', labelsize=12)
        axes[i].tick_params(axis='y', labelsize=12)
        
        # Set y-limits to show significance bars
        axes[i].set_ylim(0, y_max * 1.2)

    plt.tight_layout()
    fig.subplots_adjust(top=0.85)
    if savefig:
        plt.savefig(savefig, dpi=300, bbox_inches='tight')
    
    return fig, axes


def plot_paired_FR_TD(df, metrics, cell_types, condition_col, patient_col, class_col,
                       output_dir, cohort, condition_colors=None, figsize=None, alpha=0.4, 
                       marker_size=80, line_width=1.5):
    """
    Plot paired comparisons of metrics between normal and tumor conditions for specific cell types.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The data frame containing the metrics and metadata
    metrics : list
        List of metric names to plot (e.g. ['FR', 'TD'])
    cell_types : list
        List of cell types to plot
    condition_col : str
        Column name for cell type identification
    patient_col : str
        Column name for patient ID
    class_col : str
        Column name for sample class (Normal/Tumor)
    output_dir : str
        Directory to save the output figure
    cohort : str
        Cohort name to include in title and filename
    condition_colors : dict, optional
        Dictionary mapping condition names to colors (e.g. {'Normal': '#3498DB', 'Tumor': '#FB8E68'})
    figsize : tuple, optional
        Figure size (width, height) in inches
    alpha : float, optional
        Transparency of the connecting lines
    marker_size : int, optional
        Size of markers
    line_width : float, optional
        Width of connecting lines
    """
    import matplotlib.pyplot as plt
    from scipy import stats
    from statsmodels.stats.multitest import multipletests
    import numpy as np
    
    if condition_colors is None:
        condition_colors = {'Tumor': '#FB8E68', 'Normal': '#3498DB'}
        
    # Set default figure size if not provided
    if figsize is None:
        col_length = 2.6
        row_length = 3.3
        figsize = (col_length * len(cell_types), row_length * len(metrics))
    
    # Prepare data
    target_meta = df[df[condition_col].isin(cell_types)].copy()
    target_tmp = target_meta.groupby([patient_col, condition_col, class_col]).mean(numeric_only=True).reset_index()
    target_tmp = target_tmp.melt(id_vars=[patient_col, condition_col, class_col], 
                                value_vars=metrics)
    target_tmp['color'] = target_tmp[class_col].map(condition_colors)
    
    # Collect all p-values for multiple testing correction
    all_p_values = []
    all_p_indices = []
    
    # Create figure
    plt.figure(figsize=figsize)
    
    # First loop - calculate all p-values
    for i, metric in enumerate(metrics):
        for j, cell_type in enumerate(cell_types):
            draw_df = target_tmp[(target_tmp['variable'] == metric) & 
                               (target_tmp[condition_col] == cell_type)].copy()
            
            normal_df = draw_df[draw_df[class_col] == 'Normal'].copy()
            tumor_df = draw_df[draw_df[class_col] == 'Tumor'].copy()
            
            y1 = normal_df['value'].values
            y2 = tumor_df['value'].values
            
            # Perform Mann-Whitney U test
            if len(y1) > 0 and len(y2) > 0:
                u_stat, p_value = stats.mannwhitneyu(y1, y2, alternative='two-sided')
                all_p_values.append(p_value)
                all_p_indices.append((i, j))
    
    # Apply Benjamini-Hochberg correction
    if all_p_values:
        rejected, p_corrected, _, _ = multipletests(all_p_values, method='fdr_bh')
    
    # Plot each metric for each cell type
    plot_idx = 1
    for i, metric in enumerate(metrics):
        for j, cell_type in enumerate(cell_types):   
            draw_df = target_tmp[(target_tmp['variable'] == metric) & 
                                (target_tmp[condition_col] == cell_type)].copy()
            
            normal_df = draw_df[draw_df[class_col] == 'Normal'].copy()
            tumor_df = draw_df[draw_df[class_col] == 'Tumor'].copy()
            
            plt.subplot(len(metrics), len(cell_types), plot_idx)
            
            # Line color
            line_color = 'gray'
            
            # Create x and y values
            x1 = ['Normal'] * len(normal_df)
            y1 = normal_df['value'].values
            x2 = ['Tumor'] * len(tumor_df)
            y2 = tumor_df['value'].values
            
            # Draw connecting lines for matched patients
            for k in range(len(normal_df)):
                patient_id = normal_df[patient_col].iloc[k]
                # Find matching tumor sample for the same patient
                tumor_match = tumor_df[tumor_df[patient_col] == patient_id]
                if not tumor_match.empty:
                    plt.plot(['Normal', 'Tumor'], 
                           [normal_df['value'].iloc[k], tumor_match['value'].iloc[0]], 
                           '-', fillstyle='bottom', lw=line_width, 
                           color=line_color, alpha=alpha, markersize=0, zorder=1)
            
            # Plot points AFTER lines (with higher zorder to ensure they appear on top)
            plt.scatter(x1, y1, c=normal_df['color'].values, s=marker_size, 
                        marker='o', alpha=1, edgecolors='none', zorder=2)
            plt.scatter(x2, y2, c=tumor_df['color'].values, s=marker_size, 
                        marker='o', alpha=1, edgecolors='None', zorder=2)
            
            # Add statistical test results
            if (i, j) in all_p_indices:
                idx = all_p_indices.index((i, j))
                p_value = all_p_values[idx]
                adj_p = p_corrected[idx]
                
                # Determine significance marker based on adjusted p-value
                if adj_p < 0.0001:
                    sig_symbol = '****'
                elif adj_p < 0.001:
                    sig_symbol = '***'
                elif adj_p < 0.01:
                    sig_symbol = '**'
                elif adj_p < 0.05:
                    sig_symbol = '*'
                else:
                    sig_symbol = 'ns'
                
                # Get current axis
                ax = plt.gca()
                
                # Calculate position for significance bar (above the max value)
                y_min = min(min(y1) if len(y1) > 0 else 0, min(y2) if len(y2) > 0 else 0)
                y_max = max(max(y1) if len(y1) > 0 else 0, max(y2) if len(y2) > 0 else 0)
                y_range = y_max - y_min
                
                # Calculate position for bracket
                x1_pos = 0 - 0.2  # Position for Normal (left side)
                x2_pos = 1 + 0.2  # Position for Tumor (right side)
                y_pos = y_max + 0.08 * y_range  # Height of significance bar
                y_increment = y_range * 0.02  # Vertical increment
                
                # Draw bracket-shaped significance bar similar to reference function
                ax.plot([x1_pos, x1_pos, x2_pos, x2_pos], 
                       [y_pos, y_pos + y_increment, y_pos + y_increment, y_pos], 
                       lw=1.5, c='black')
                
                # Add significance annotation
                ax.text((x1_pos + x2_pos) * 0.5, y_pos + y_increment-0.01 * y_range, 
                       sig_symbol, ha='center', va='bottom', fontsize=12)
                
                # Add p-value at the bottom
                ax.text((x1_pos + x2_pos) * 0.5, y_pos - y_increment*4, f'adj.p={adj_p:.3f}', 
                       ha='center', va='bottom', fontsize=10)
                
                # Set y-limits to show significance bars properly
                ax.set_ylim(y_min - 0.1 * y_range, y_max + 0.2 * y_range)
            
            # Formatting
            plt.xticks(fontsize=12)
            plt.yticks(fontsize=12)
            plt.xlabel('', size=14)
            plt.title(f'{cohort}\nEpithelial cells {metric}', size=14)
            plt.ylabel(metric, size=14)
            
            # Remove grid and clean up spines
            plt.grid(False)
            for spine in plt.gca().spines.values():
                spine.set_edgecolor('black')
                spine.set_linewidth(1)
            
            plot_idx += 1
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/{cohort}_{cell_type}_FR_TD.pdf', bbox_inches='tight')
    plt.show()
    plt.close()

    
    
def plot_paired_FR_TD_old(df, metrics, cell_types, condition_col, patient_col, class_col,
                                    output_dir, cohort,condition_colors = None, figsize=None, alpha=0.4, 
                                    marker_size=80, line_width=1.5):
    """
    Plot paired comparisons of metrics between normal and tumor conditions for specific cell types.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The data frame containing the metrics and metadata
    metrics : list
        List of metric names to plot (e.g. ['FR', 'TD'])
    cell_types : list
        List of cell types to plot
    condition_col : str
        Column name for cell type identification
    patient_col : str
        Column name for patient ID
    class_col : str
        Column name for sample class (Normal/Tumor)
    output_dir : str
        Directory to save the output figure
    cohort : str
        Cohort name to include in title and filename
    condition_colors : dict, optional
        Dictionary mapping condition names to colors (e.g. {'Normal': '#3498DB', 'Tumor': '#FB8E68'})
    figsize : tuple, optional
        Figure size (width, height) in inches
    alpha : float, optional
        Transparency of the connecting lines
    marker_size : int, optional
        Size of markers
    line_width : float, optional
        Width of connecting lines
    """
    if condition_colors is None:
        condition_colors = {'Tumor': '#FB8E68', 'Normal': '#3498DB'}
        
    # Set default figure size if not provided
    if figsize is None:
        col_length = 2.4
        row_length = 2.6
        figsize = (col_length * len(cell_types), row_length * len(metrics))
    
    # Prepare data
    target_meta = df[df[condition_col].isin(cell_types)].copy()
    target_tmp = target_meta.groupby([patient_col, condition_col, class_col]).mean(numeric_only = True).reset_index()
    target_tmp = target_tmp.melt(id_vars=[patient_col, condition_col, class_col], 
                                value_vars=metrics)
    target_tmp['color'] = target_tmp[class_col].map(condition_colors)
    
    # Create figure
    plt.figure(figsize=figsize)
    
    # Plot each metric for each cell type
    plot_idx = 1
    for metric in metrics:
        for cell_type in cell_types:   
            draw_df = target_tmp[(target_tmp['variable'] == metric) & 
                                (target_tmp[condition_col] == cell_type)].copy()
            
            normal_df = draw_df[draw_df[class_col] == 'Normal'].copy()
            tumor_df = draw_df[draw_df[class_col] == 'Tumor'].copy()
            
            plt.subplot(len(metrics), len(cell_types), plot_idx)
            
            # Line color
            line_color = 'gray'
            
            # Create x and y values
            x1 = ['Normal'] * len(normal_df)
            y1 = normal_df['value'].values
            x2 = ['Tumor'] * len(tumor_df)
            y2 = tumor_df['value'].values
            
            # Draw connecting lines FIRST (so they appear below the dots)
            for i in range(len(x1)):
                plt.plot([x1[i], x2[i]], [y1[i], y2[i]], '-', 
                        fillstyle='bottom', lw=line_width, 
                        color=line_color, alpha=alpha, markersize=0, zorder=1)
            
            # Plot points AFTER lines (with higher zorder to ensure they appear on top)
            plt.scatter(x1, y1, c=normal_df['color'].values, s=marker_size, 
                        marker='o', alpha=1, edgecolors='none', zorder=2)
            plt.scatter(x2, y2, c=tumor_df['color'].values, s=marker_size, 
                        marker='o', alpha=1, edgecolors='None', zorder=2)
            
            # Formatting
            plt.xticks(fontsize=12)
            plt.yticks(fontsize=12)
            plt.xlabel('', size=14)
            plt.title(f'{cohort}\nEpithelial cells {metric}', size=14)
            plt.ylabel(metric, size=14)
            plt.margins(x=0.1)
            
            plot_idx += 1
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/{cohort}_{cell_type}_FR_TD.pdf', bbox_inches='tight')
    plt.show()
    plt.close()

# Example usage:
# plot_paired_FR_TD(
#     df=sc_big_meta1,
#     metrics=['FR', 'TD'],
#     cell_types=[tp1],
#     condition_col=tp_key1,
#     patient_col=patient_col1,
#     class_col=class_col1,
#     output_dir=outDir1,
#     cohort='Cohort1',
#     condition_colors=palette_dict,
# )

############ PageRank ############

def run_pagerank(fr_df, cut_off=0):
    '''
    This function runs the pagerank algorithm on the given dataframe and returns the dataframe with the centrality values.
    input: fr_df: dataframe with the gene-gene similarity values
    output: pr_df: dataframe with the gene and centrality values
    '''
    tmp = fr_df.reset_index()
    tmp.rename(columns={'index': 'Gene'}, inplace=True)
    melt_df = tmp.melt(id_vars='Gene')
    melt_df.columns = ['gene1','gene2','weight']
    melt_df = melt_df[melt_df['weight'] > cut_off]
    sorted_pr = cal_pagerank(melt_df)
    pr_df = pd.DataFrame(sorted_pr, columns = ['gene','centrality'])
    return pr_df


def cal_pagerank(uniq_celltype_df):
    import networkx as nx
    G = nx.Graph()
    # Add edges to the graph with weights
    for _, row in uniq_celltype_df.iterrows():
        G.add_edge(row['gene1'], row['gene2'], weight=row['weight'])
    # Calculate PageRank centrality with weighted edges
    pr = nx.pagerank(G, weight='weight')
    # Sort the nodes by PageRank centrality
    sorted_pr = sorted(pr.items(), key=lambda x: x[1], reverse=True)
    # print("PageRank Centrality:")
    # i = 0
    # for node, centrality in sorted_pr:
    #     if i <= 10:
    #         print(f"{node}: {centrality:.3f}")
    #         i += 1
    return sorted_pr


def pageRankCentral(uniq_celltype_df, title = '', outDir = ''):
    '''
    PageRank centrality with weighted edges
    Parameters
    ----------
    uniq_celltype_df : pd.DataFrame
        A dataframe with columns 'gene1', 'gene2', 'weight'
    title : str
        The title of the plot
    '''
    import networkx as nx
    import pandas as pd
    import matplotlib.pyplot as plt
    G = nx.Graph()
    # Add edges to the graph with weights
    for _, row in uniq_celltype_df.iterrows():
        G.add_edge(row['gene1'], row['gene2'], weight=row['weight'])
    # Calculate PageRank centrality with weighted edges
    pr = nx.pagerank(G, weight='weight')
    # Sort the nodes by PageRank centrality
    sorted_pr = sorted(pr.items(), key=lambda x: x[1], reverse=True)
    print("PageRank Centrality:")
    i = 0
    for node, centrality in sorted_pr:
        if i <= 10:
            print(f"{node}: {centrality:.3f}")
            i += 1
    # Plot 
    if len(uniq_celltype_df) >100:
        top_links = uniq_celltype_df.nlargest(int(np.round(len(uniq_celltype_df)*0.1)), 'weight')
    else:
        top_links = uniq_celltype_df
    G = nx.Graph()
    for _, row in top_links.iterrows():
        G.add_edge(row['gene1'], row['gene2'], weight=row['weight'])
    node_sizes = []
    node_colors = []
    for node in G.nodes():
        # print(node, pr[node])
        node_sizes.append(pr[node] * 5000)  # Scale PageRank for better visibility
        node_colors.append(pr[node])
    # print(pr.values())
    # Get the node positions using spring layout
    pos = nx.spring_layout(G)
    # Create the figure
    fig, ax = plt.subplots(figsize=(12, 8))
    # Draw the nodes
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, cmap='Blues', node_size=node_sizes, ax=ax)
    # Draw the edges
    nx.draw_networkx_edges(G, pos, edge_color='lightgray', width=2, ax=ax)
    # Draw the node labels
    nx.draw_networkx_labels(G, pos, ax=ax)
    # Add a colorbar for the PageRank values
    sm = plt.cm.ScalarMappable(cmap='Blues', norm=plt.Normalize(vmin=min(node_colors), vmax=max(node_colors)))
    cbar = fig.colorbar(sm, ax=ax)
    cbar.set_label('PageRank Centrality')
    # Adjust the layout and show the plot
    plt.axis('off')
    plt.title(title)
    if outDir != '':
        plt.savefig(f'{outDir}/{title}.pdf')
    plt.show()
    return sorted_pr




##################################################
########## Page Rank Pathway Analysis ############
##################################################

def get_top_pr_df(pr_res, tp_key = 'celltype', tp = 'Epithelium', topk = 10, class_col = 'Class', palette_dict = None):
    top_pr = pr_res[pr_res[tp_key] == tp].groupby(
        ['sample', class_col, tp_key]
    ).apply(lambda x: x.nlargest(topk, 'centrality')).reset_index(drop=True)
    graph_input = pd.DataFrame(index=top_pr['gene'].unique(), columns=['color', 'class'])
    patients = top_pr['sample'].unique()
    min_count = np.ceil(len(patients) * 0.5)
    max_count = 1
    for gene in top_pr['gene'].unique():
        tmp = top_pr[top_pr['gene'] == gene].groupby(class_col).count()
        if len(tmp) == 2:
            if (tmp.loc['Tumor','sample'] >= min_count) and (tmp.loc['Normal','sample'] <= max_count):
                graph_input.loc[gene, 'color'] = palette_dict['Tumor']
                graph_input.loc[gene, 'class'] = 'Tumor'

            elif (tmp.loc['Normal','sample'] >= min_count) and (tmp.loc['Tumor','sample'] <= max_count):
                graph_input.loc[gene, 'color'] = palette_dict['Normal']
                graph_input.loc[gene, 'class'] = 'Normal'
            else:
                graph_input.loc[gene, 'color'] = palette_dict['Shared']
                graph_input.loc[gene, 'class'] = 'Shared'
        elif len(tmp) == 1:
            class_type = 'Tumor' if tmp.index[0] == 'Tumor' else 'Normal'
            graph_input.loc[gene, 'color'] = palette_dict[class_type]
            graph_input.loc[gene, 'class'] = class_type
    return graph_input


def get_top_pr_pathway(pr_top, gene_sets = 'KEGG_2019_Human'):
    # 'MSigDB_Hallmark_2020'
    # ['KEGG_2021_Human','GO_Biological_Process_2021', 'GO_Molecular_Function_2021'(too small), 'GO_Cellular_Component_2021'(focus on memberane)]
    import gseapy as gp
    kegg_result = pd.DataFrame()
    for cla in ['Normal', 'Tumor']:
        tmp = pr_top[(pr_top['class'] == cla) | (pr_top['class'] == 'Shared') ].copy()
        genes = tmp.index.tolist()
        enr_up = gp.enrichr(gene_list = genes,
                        gene_sets = gene_sets,
                        organism = 'Human',
                        cutoff = 0.05)
        enr_up.res2d.Term = enr_up.res2d.Term.str.split(" \(GO").str[0]
        
        tmp = enr_up.res2d.copy()
        tmp['count'] = tmp['Overlap'].str.split('/').str[0].astype(int)
        tmp['class'] = cla
        kegg_result = pd.concat([kegg_result, tmp])
    # break
    return kegg_result


def get_pathway_flow(kegg_result, pr_top, topk=5, palette_dict = None):
    kegg_result.index = range(len(kegg_result))
    kegg_enrich = kegg_result.groupby(
        ['class']
    ).apply(lambda x: x.nlargest(topk, 'count')).reset_index(drop=True)
    # add group to pathway term if it is shared
    # 
    for term in kegg_enrich['Term'].unique():
        tmp = kegg_enrich[kegg_enrich['Term'] == term].copy()
        if len(tmp) == 2:
            kegg_enrich.loc[kegg_enrich['Term'] == term, 'path_class'] = 'Shared'
        elif len(tmp) == 1:
            # print(term, tmp)
            if tmp['class'].values[0] == 'Tumor':
                kegg_enrich.loc[kegg_enrich['Term'] == term, 'path_class'] = 'Tumor'
            elif tmp['class'].values[0] == 'Normal':
                kegg_enrich.loc[kegg_enrich['Term'] == term, 'path_class'] = 'Normal'
            else:
                kegg_enrich.loc[kegg_enrich['Term'] == term, 'path_class'] = 'Shared'
    print(kegg_enrich)
    # save the gene - pathway relationships
    nt_pathway = {}
    for cla in ['Normal', 'Tumor', 'Shared']:
        tmp = kegg_enrich[kegg_enrich['class'] == cla].copy()
        pathway_dict = {}
        for idx, row in tmp.iterrows():
            path = row['Term']
            genes = row['Genes'].split(';')
            # print(genes)
            for gene in genes:
                if gene in pathway_dict:
                    pathway_dict[gene].append(path)
                else:
                    pathway_dict[gene] = [path]
        nt_pathway[cla] = pathway_dict
    print(nt_pathway)
    # form a DataFrame for receptor-pathway relationships with class
    lr_path_df = pd.DataFrame()
    for cla in ['Normal', 'Tumor', 'Shared']:
        pathway_dict = nt_pathway[cla]
        for gene, paths in pathway_dict.items():
            for path in paths:
                path_class = kegg_enrich.loc[kegg_enrich['Term'] == path, 'path_class'].values[0]
                path_color = palette_dict[path_class]
                lr_path_df = pd.concat([lr_path_df, pd.DataFrame({'receptor':[gene], 'pathway':[path], 'rec_color':[pr_top.loc[gene]['color']],
                                                                'path_color':[path_color]})], ignore_index=True)
    return lr_path_df, kegg_enrich




def draw_lr_flow(input_df, left_panel = 'ligand', right_panel = 'receptor',
                  left_color_col = 'rec_color', right_color_col = 'path_color', 
                 figsize = (10,10), savefig = ''):
    df = input_df.copy()
    import plotly.graph_objects as go
    source = df[left_panel].astype('category').cat.codes.tolist()
    target = df[right_panel].astype('category').cat.codes.tolist()
    target = [x + len(set(source)) for x in target]
    value = [np.random.randint(1, 2) for _ in range((len(df)))]
    df['source'] = source
    df['target'] = target
    
    # sort_source = df
    sort_source = df.sort_values(by=['source'])
    labels = list(sort_source[left_panel].unique())
    left_color = list(sort_source[[left_panel, left_color_col]].drop_duplicates()[left_color_col])
    # print(labels)

    # sort_rec = df
    sort_rec = df.sort_values(by=['target'])
    label_rec = list(sort_rec[right_panel].unique())
    right_color = list(sort_rec[[right_panel, right_color_col]].drop_duplicates()[right_color_col])
    # print(label_rec)
    labels.extend(label_rec)
    # define source and target indices for each link
    trace = go.Sankey(
        node=dict(
            pad=5,
            thickness=20,
            line=dict(color='black', width=0.1),
            label=labels,
            color=left_color + right_color
        ),
        link=dict(
            source=source, # indices correspond to labels, eg A1, A2, A1, B1 
            target=target, 
            value=value,
            # color=['#ccc' for _ in range(len(df))]  # Set link color to semi-transparent black
        )
    )
    # create layout
    layout = go.Layout(
        title='',
        font=dict(size=26)
    )
    # create figure
    fig = go.Figure(data=[trace], layout=layout)
    width = figsize[0]*100
    height = figsize[1]*100
    fig.update_layout(width=width, height=height)
    fig.write_image(savefig) 
    fig.show()



#######################
def plot_cellpair(cellpair, sc_meta, sender, receiver, cols = ['adj_UMAP1', 'adj_UMAP2'], 
                figsize = (6,6), size = 40, arrow_length = 0.015,
                title = None, legend = True, savefig = None,
                palette = None, tp_key = 'celltype'):
    """
    Plot cell pairs with arrows indicating connections between sender and receiver cell types.
    Parameters:
    - cellpair: DataFrame containing cell pair information.
    - sc_meta: DataFrame containing spatial coordinates and cell type information.
    - sender: Cell type of the sender cells.
    - receiver: Cell type of the receiver cells.
    - cols: List of column names for x and y coordinates.
    - figsize: Size of the figure.
    - size: Size of the points in the scatter plot.
    - arrow_length: Length of the arrows indicating connections.
    """
    
    meta = sc_meta.copy()
    draw_bg = meta
    meta[tp_key] = meta[tp_key].astype(object)    
    celltype_df = draw_bg[draw_bg[tp_key].isin([sender,receiver])].copy()

    target_cellpair = cellpair[(cellpair['sender_type'] == sender)&(cellpair['receiver_type'] == receiver)].copy()

    plt.figure(figsize=figsize)
    sns.scatterplot(data = draw_bg, x = cols[0], y=cols[1], 
                    s = 10, alpha = 0.4,c=['#ccc'],edgecolor = None)

    sns.scatterplot(data = celltype_df, x=cols[0], y=cols[1],hue = tp_key, 
                    s = size,alpha = 1, palette=palette, edgecolor = None)   

    for _,row in target_cellpair.iterrows():
        start = meta.loc[row['sender_cell']][cols]
        end = meta.loc[row['receiver_cell']][cols]
        color = 'black'
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        plt.arrow(start[0], start[1], dx, dy,
                color=color, width=0.001, length_includes_head=True,
                # head_length=arrow_length, head_width=arrow_length, 
            head_width=arrow_length/2, head_length=arrow_length,
            overhang = 0.2, alpha = 0.8,
            head_starts_at_zero=False)
        
    if not title:
        if figsize[0] > figsize[1]:
            # landscape
            plt.title(f'{sender} to {receiver}',fontsize=16)
        else:
            # portrait
            plt.title(f'{sender}to \n {receiver}',fontsize=16)
    else:
        plt.title(title,fontsize=16)
    if legend:
        leg = plt.legend(loc='center left', bbox_to_anchor=(0.99, 0.5),
                                ncol=1, handletextpad=0.5,columnspacing=0.4,labelspacing=0.5,
                                fontsize = 16,markerscale = 2,handlelength = 0.5)
        leg.get_frame().set_linewidth(0.0)  # Remove legend frame
    else:
        plt.legend([],[], frameon=False)
    plt.xlabel('',fontsize=16)
    plt.ylabel('',fontsize=16)
    plt.xticks([],fontsize=14)
    plt.yticks([],fontsize=14)
    plt.axis('equal')
    if savefig:
        plt.savefig(f'{savefig}', dpi=300, bbox_inches='tight')
        print(f'Figure saved {savefig}')