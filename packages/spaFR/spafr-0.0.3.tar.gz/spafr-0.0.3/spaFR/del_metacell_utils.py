import anndata
import scanpy as sc
import pandas as pd
import metacells as mc

LATERAL_GENE_NAMES = [
    "ACSM3", "ANP32B", "APOE", "AURKA", "B2M", "BIRC5", "BTG2", "CALM1", "CD63", "CD69", "CDK4",
    "CENPF", "CENPU", "CENPW", "CH17-373J23.1", "CKS1B", "CKS2", "COX4I1", "CXCR4", "DNAJB1",
    "DONSON", "DUSP1", "DUT", "EEF1A1", "EEF1B2", "EIF3E", "EMP3", "FKBP4", "FOS", "FOSB", "FTH1",
    "G0S2", "GGH", "GLTSCR2", "GMNN", "GNB2L1", "GPR183", "H2AFZ", "H3F3B", "HBM", "HIST1H1C",
    "HIST1H2AC", "HIST1H2BG", "HIST1H4C", "HLA-A", "HLA-B", "HLA-C", "HLA-DMA", "HLA-DMB",
    "HLA-DPA1", "HLA-DPB1", "HLA-DQA1", "HLA-DQB1", "HLA-DRA", "HLA-DRB1", "HLA-E", "HLA-F", "HMGA1",
    "HMGB1", "HMGB2", "HMGB3", "HMGN2", "HNRNPAB", "HSP90AA1", "HSP90AB1", "HSPA1A", "HSPA1B",
    "HSPA6", "HSPD1", "HSPE1", "HSPH1", "ID2", "IER2", "IGHA1", "IGHA2", "IGHD", "IGHG1", "IGHG2",
    "IGHG3", "IGHG4", "IGHM", "IGKC", "IGKV1-12", "IGKV1-39", "IGKV1-5", "IGKV3-15", "IGKV4-1",
    "IGLC2", "IGLC3", "IGLC6", "IGLC7", "IGLL1", "IGLL5", "IGLV2-34", "JUN", "JUNB", "KIAA0101",
    "LEPROTL1", "LGALS1", "LINC01206", "LTB", "MCM3", "MCM4", "MCM7", "MKI67", "MT2A", "MYL12A",
    "MYL6", "NASP", "NFKBIA", "NUSAP1", "PA2G4", "PCNA", "PDLIM1", "PLK3", "PPP1R15A", "PTMA",
    "PTTG1", "RAN", "RANBP1", "RGCC", "RGS1", "RGS2", "RGS3", "RP11-1143G9.4", "RP11-160E2.6",
    "RP11-53B5.1", "RP11-620J15.3", "RP5-1025A1.3", "RP5-1171I10.5", "RPS10", "RPS10-NUDT3", "RPS11",
    "RPS12", "RPS13", "RPS14", "RPS15", "RPS15A", "RPS16", "RPS17", "RPS18", "RPS19", "RPS19BP1",
    "RPS2", "RPS20", "RPS21", "RPS23", "RPS24", "RPS25", "RPS26", "RPS27", "RPS27A", "RPS27L",
    "RPS28", "RPS29", "RPS3", "RPS3A", "RPS4X", "RPS4Y1", "RPS4Y2", "RPS5", "RPS6", "RPS6KA1",
    "RPS6KA2", "RPS6KA2-AS1", "RPS6KA3", "RPS6KA4", "RPS6KA5", "RPS6KA6", "RPS6KB1", "RPS6KB2",
    "RPS6KC1", "RPS6KL1", "RPS7", "RPS8", "RPS9", "RPSA", "RRM2", "SMC4", "SRGN", "SRSF7", "STMN1",
    "TK1", "TMSB4X", "TOP2A", "TPX2", "TSC22D3", "TUBA1A", "TUBA1B", "TUBB", "TUBB4B", "TXN", "TYMS",
    "UBA52", "UBC", "UBE2C", "UHRF1", "YBX1", "YPEL5", "ZFP36", "ZWINT"
]

LATERAL_GENE_PATTERNS = ["RP[LS].*"]  # Ribosomal

NOISY_GENE_NAMES = [
    "CCL3", "CCL4", "CCL5", "CXCL8", "DUSP1", "FOS", "G0S2", "HBB", "HIST1H4C", "IER2", "IGKC",
    "IGLC2", "JUN", "JUNB", "KLRB1", "MT2A", "RPS26", "RPS4Y1", "TRBC1", "TUBA1B", "TUBB"
]


def make_adata(mat = None,meta = None, species = 'Human', filter = False):
    # mat: exp matrix, should be cells x genes
    # index should be strictly set as strings
    meta.index = meta.index.map(str)
    mat.index = mat.index.map(str)
    mat = mat.loc[meta.index]
    adata = anndata.AnnData(mat, dtype='float32')
    adata.obs = meta
    adata.var = pd.DataFrame(mat.columns.tolist(), columns=['symbol'])
    adata.var_names = adata.var['symbol'].copy()
    if filter:
        sc.pp.filter_cells(adata, min_genes=200)
        sc.pp.filter_genes(adata, min_cells=3)
    # remove MT genes for spatial mapping (keeping their counts in the object)
    if species == 'Mouse':
        adata.var['MT_gene'] = [gene.startswith('mt-') for gene in adata.var['symbol']]
    if species == 'Human':
        adata.var['MT_gene'] = [gene.startswith('MT-') for gene in adata.var['symbol']]
    adata.obsm['MT'] = adata[:, adata.var['MT_gene'].values].X.toarray()
    adata = adata[:, ~adata.var['MT_gene'].values]
    return adata


def mc_filter(adata):
    # This will mark as "lateral_gene" any genes that match the above, if they exist in the clean dataset.
    mc.pl.mark_lateral_genes(
        adata,
        lateral_gene_names=LATERAL_GENE_NAMES,
        lateral_gene_patterns=LATERAL_GENE_PATTERNS,
    )
    mc.pl.mark_noisy_genes(adata, noisy_gene_names=NOISY_GENE_NAMES)
    mc.pl.set_max_parallel_piles(4)

def mc_run(adata):
    with mc.ut.progress_bar():
        mc.pl.divide_and_conquer_pipeline(adata, random_seed=123456)
    metacells = mc.pl.collect_metacells(adata, name="metacells", random_seed=123456)
    print(f"Preliminary: {metacells.n_obs} metacells, {metacells.n_vars} genes")
    return metacells

def mc_annot(adata = None, metacells = None, property_name = 'celltype'):
    mc.tl.convey_obs_to_group(
    adata=adata, gdata=metacells,
    property_name=property_name, to_property_name=property_name,
    method=mc.ut.most_frequent
    )