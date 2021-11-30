# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.13.1
#   kernelspec:
#     display_name: Python [conda env:.conda-pircher-sc-integrate2]
#     language: python
#     name: conda-env-.conda-pircher-sc-integrate2-py
# ---

# %%
# %load_ext autoreload
# %autoreload 2

# %%
import scanpy as sc
from nxfvars import nxfvars
import infercnvpy as cnv
from scanpy_helpers.annotation import AnnotationHelper
from scanpy_helpers import de
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from natsort import natsorted
import dorothea
import progeny
import hierarchical_bootstrapping as hb
from natsort import natsorted
import itertools
from threadpoolctl import threadpool_limits

# %%
ah = AnnotationHelper()

# %%
sc.set_figure_params(figsize=(4, 4))

# %%
input_adata = nxfvars.get(
    "input_adata",
    "../../data/20_integrate_scrnaseq_data/annotate_datasets/31_cell_types_coarse/by_cell_type/adata_cell_type_coarse_epithelial_cell.umap_leiden.h5ad",
)
threadpool_limits(nxfvars.get("cpus", 32))
artifact_dir = nxfvars.get(
    "artifact_dir", "../../data/20_integrate_scrnaseq_data/zz_epi"
)

# %%
adata = sc.read_h5ad(input_adata)

# %%
adata.obs["leiden"] = adata.obs["leiden_0.50"]

# %%
sc.pl.umap(adata, color="leiden")

# %% [markdown]
# ### Redo UMAP with PAGA

# %%
sc.tl.paga(adata, groups="leiden")

# %%
sc.pl.paga(adata, color="leiden", threshold=0.2)

# %%
sc.tl.umap(adata, init_pos="paga")

# %%
sc.pl.umap(adata, color="dataset")

# %%
with plt.rc_context({"figure.figsize": (6, 6)}):
    fig = sc.pl.umap(
        adata,
        color=["cell_type", "EPCAM", "dataset", "condition", "origin"],
        cmap="inferno",
        size=2,
        ncols=3,
        return_fig=True,
    )
    fig.savefig(f"{artifact_dir}/overview_epithelial_cluster.pdf", bbox_inches="tight")

# %% [markdown]
# ## Annotation

# %%
with plt.rc_context({"figure.figsize": (4, 4)}):
    ah.plot_umap(
        adata,
        filter_cell_type=[
            "Ciliated",
            "Alevolar",
            "Basal",
            "Club",
            "Dividing",
            "Goblet",
            "Ionocyte",
            "Mesothelial",
            "Suprabasal",
        ],
        cmap="inferno",
    )

# %%
ah.plot_dotplot(adata)

# %%
with plt.rc_context({"figure.figsize": (6, 6)}):
    sc.pl.umap(adata, color="leiden", legend_loc="on data", legend_fontoutline=2)

# %%
from toolz.functoolz import reduce
from operator import or_

# %%
cell_type_map = {
    "Alevolar cell type 1": [10],
    "Alevolar cell type 2": [0],
    "Ciliated": [7],
    "Club": [1],
}
cell_type_map.update(
    {
        str(k): [k]
        for k in set(map(int, adata.obs["leiden"].values))
        - reduce(or_, map(set, cell_type_map.values()))
    }
)

# %%
ah.annotate_cell_types(adata, cell_type_map)

# %% [markdown]
# ### Subcluster 15, contains alevolar 2

# %%
adata_15 = adata[adata.obs["cell_type"] == "15", :]

# %%
ah.reprocess_adata_subset_scvi(adata_15, leiden_res=0.5)

# %%
sc.pl.umap(adata_15, color="leiden", legend_loc="on data", legend_fontoutline=2)

# %%
sc.pl.umap(adata_15, color="dataset")

# %%
ah.plot_umap(adata_15, filter_cell_type=["Alev", "Goblet", "Club"])

# %%
ah.plot_dotplot(adata_15)

# %%
ah.annotate_cell_types(
    adata_15,
    {"Alevolar cell type 2": [0, 1, 2, 4], "Alevolar cell type 1": [5], "Club": [3]},
)

# %%
ah.integrate_back(adata, adata_15)

# %% [markdown]
# ### Subcluster 9, contains alevolar 2

# %%
adata_9 = adata[adata.obs["cell_type"] == "9", :]

# %%
ah.reprocess_adata_subset_scvi(adata_9, leiden_res=0.5)

# %%
sc.pl.umap(adata_9, color="leiden", legend_loc="on data", legend_fontoutline=2)

# %%
sc.pl.umap(adata_9, color=["origin", "dataset"], wspace=0.5)

# %%
ah.plot_umap(adata_9, filter_cell_type=["Alev", "Goblet", "Club", "Epi"])

# %%
ah.annotate_cell_types(
    adata_9,
    {
        "Alevolar cell type 2": [0, 6, 2, 7, 5],
        "Club": [4, 3, 8],
        "ROS1+ normal epithelial": [1],
    },
)

# %%
ah.integrate_back(adata, adata_9)

# %% [markdown]
# ### Subcluster 11, contains goblet

# %%
adata_11 = adata[adata.obs["cell_type"] == "11", :]

# %%
ah.reprocess_adata_subset_scvi(adata_11, leiden_res=0.5)

# %%
sc.pl.umap(adata_11, color="leiden", legend_loc="on data", legend_fontoutline=2)

# %%
sc.pl.umap(adata_11, color=["origin", "dataset"], wspace=0.5)

# %%
ah.plot_umap(adata_11, filter_cell_type=["Alev", "Goblet", "Club"])

# %%
ah.plot_dotplot(adata_11)

# %%
ah.annotate_cell_types(
    adata_11,
    {
        "Club": [9],
        "Goblet": [7, 3, 1, 0, 4, 5],
        "11-1": [2, 10, 6],
        "11-2": [8],
    },
)

# %%
ah.integrate_back(adata, adata_11)

# %% [markdown]
# ### Subcluster 5, contains some weird normal cells

# %%
adata_5 = adata[adata.obs["cell_type"] == "5", :]

# %%
ah.reprocess_adata_subset_scvi(adata_5, leiden_res=0.4)

# %%
sc.pl.umap(adata_5, color="leiden", legend_loc="on data", legend_fontoutline=2)

# %%
sc.pl.umap(adata_5, color=["origin", "dataset"], wspace=0.5)

# %%
ah.plot_dotplot(adata_5)

# %%
ah.annotate_cell_types(
    adata_5, {"Alevolar cell type 2": [7], "tumor cell": [0, 1, 2, 3, 4, 5, 6, 8, 9]}
)

# %%
ah.integrate_back(adata, adata_5)

# %% [markdown]
# ## Find markers for remaining clusters

# %%
with plt.rc_context({"figure.figsize": (8, 8)}):
    sc.pl.umap(adata, color="cell_type", size=0.6)

# %%
bdata = hb.tl.bootstrap(
    adata, groupby="cell_type", hierarchy=["dataset", "patient"], n=20, use_raw=True
)

# %%
gini_res = hb.tl.gini(bdata, groupby="cell_type")

# %%
hb.pl.gini_dotplot(adata, gini_res, groupby="cell_type", max_rank=2)

# %%
hb.pl.gini_matrixplot(bdata, gini_res, groupby="cell_type", cmap="Reds", max_rank=2)

# %% [markdown]
# ## Annotate remaining clusters

# %%
nrows = int(np.ceil(adata.obs["cell_type"].nunique() / 4))
fig, axs = plt.subplots(
    nrows, 4, figsize=(16, nrows * 4), gridspec_kw={"wspace": 0.35, "hspace": 0.35}
)
for c, ax in zip(natsorted(adata.obs["cell_type"].unique()), axs.flatten()):
    sc.pl.umap(adata, color="cell_type", groups=[str(c)], size=1, ax=ax, show=False)

# %%
sc.pl.umap(adata, color=["ALB", "GPM6B"], cmap="inferno")

# %%
adata2 = adata.copy()


# %%
adata2.obs["cell_type"] = adata.obs["cell_type"]

cell_type_map = {
    "Hemoglobin+": ["11-2"],
    "tumor cell": [2, 3, 8, 6, 5, 4, 16, 17, 18, 14, "11-1"],
    "Alevolar cell type 2": [12, 19, 13],
    "Neuronal cells": [17],
    "Hepatocytes": [20],
}
for ct in set(adata2.obs["cell_type"]) - set(
    map(str, itertools.chain.from_iterable(cell_type_map.values()))
):
    cell_type_map[ct] = cell_type_map.get(ct, []) + [ct]

ah.annotate_cell_types(
    adata2,
    cell_type_map,
    column="cell_type",
)

# %%
adata = adata2

# %% [markdown]
# ## Tumor cells

# %%
adata_tumor = adata[adata.obs["cell_type"] == "tumor cell", :].copy()

# %%
ah.reprocess_adata_subset_scvi(adata_tumor, leiden_res=0.5)

# %%
# if not removed, paga plotting fails
del adata_tumor.uns["leiden_colors"]

# %%
sc.tl.paga(adata_tumor, "leiden")

# %%
sc.pl.paga(adata_tumor, color="leiden", threshold=0.2)

# %%
sc.tl.umap(adata_tumor, init_pos="paga")

# %%
ah.plot_umap(
    adata_tumor, filter_cell_type=["Epi", "Alev", "Goblet", "Club"], cmap="inferno"
)

# %%
print("general")
sc.pl.umap(
    adata_tumor,
    color=["EPCAM", "CDK1", "NEAT1", "MSLN", "origin", "condition", "dataset"],
    cmap="inferno",
)

print("LUSC")
sc.pl.umap(
    adata_tumor,
    color=["NTRK2", "KRT5", "TP63", "SOX2"],
    cmap="inferno",
)

print("LUAD")
sc.pl.umap(
    adata_tumor,
    color=["MUC1", "NKX2-1", "KRT7", "SFTA2"],
    cmap="inferno",
)

print("EMT")
sc.pl.umap(
    adata_tumor,
    color=["VIM", "NME2", "MIF", "MSLN", "CHGA"],
    cmap="inferno",
)

# %%
sc.pl.umap(adata_tumor, color="leiden", legend_loc="on data", legend_fontoutline=2)

# %%
adata_tumor_copy = adata_tumor.copy()

# %%
ah.annotate_cell_types(
    adata_tumor,
    cell_type_map={
        "Tumor cells metastasic MSLN+": [13],
        "Tumor cells LSCC mitotic": [3],
        "Tumor cells LSCC": [0, 6, 16, 10],
        "Tumor cells LUAD mitotic": [14, 12],
        "Tumor cells LUAD": [2, 1, 7, 9],
        "Tumor cells EMT": [4, 15],
        "Tumor cells C8": [8],
        "Tumor cells C5": [5],
        "Tumor cells C11": [11],
        "Tumor cells C17": [17],
    },
)

# %%
ah.integrate_back(adata, adata_tumor)

# %% [markdown]
# ## In-depth characterization of tumor clusters

# %%
sc.tl.rank_genes_groups(adata_tumor, groupby="cell_type")

# %%
fig = sc.pl.rank_genes_groups_dotplot(adata_tumor, dendrogram=False, return_fig=True)
fig.savefig(f"{artifact_dir}/marker_dotplot_tumor.pdf", bbox_inches="tight")

# %% [markdown] tags=[]
# ### Dorothea/progeny

# %%
regulons = dorothea.load_regulons(
    [
        "A",
        "B",
    ],  # Which levels of confidence to use (A most confident, E least confident)
    organism="Human",  # If working with mouse, set to Mouse
)

# %%
dorothea.run(
    adata_tumor,  # Data to use
    regulons,  # Dorothea network
    center=True,  # Center gene expression by mean per cell
    num_perm=100,  # Simulate m random activities
    norm=True,  # Normalize by number of edges to correct for large regulons
    scale=True,  # Scale values per feature so that values can be compared across cells
    use_raw=True,  # Use raw adata, where we have the lognorm gene expression
    min_size=5,  # TF with less than 5 targets will be ignored
)

# %%
model = progeny.load_model(
    organism="Human",  # If working with mouse, set to Mouse
    top=1000,  # For sc we recommend ~1k target genes since there are dropouts
)

# %%
progeny.run(
    adata_tumor,  # Data to use
    model,  # PROGENy network
    center=True,  # Center gene expression by mean per cell
    num_perm=100,  # Simulate m random activities
    norm=True,  # Normalize by number of edges to correct for large regulons
    scale=True,  # Scale values per feature so that values can be compared across cells
    use_raw=True,  # Use raw adata, where we have the lognorm gene expression
)

# %%
adata_progeny = progeny.extract(adata_tumor)
adata_dorothea = dorothea.extract(adata_tumor)

# %%
fig =sc.pl.matrixplot(
    adata_progeny,
    var_names=adata_progeny.var_names,
    groupby="cell_type",
    cmap="coolwarm",
    vmax=2,
    vmin=-2,
    dendrogram=True,
    return_fig=True
)
fig.savefig(f"{artifact_dir}/progeny_tumor.pdf", bbox_inches="tight")

# %%
for i, var_names in enumerate(
    [
        adata_dorothea.var_names[:40],
        adata_dorothea.var_names[40:80],
        adata_dorothea.var_names[80:],
    ]
):
    fig = sc.pl.matrixplot(
        adata_dorothea,
        var_names=var_names,
        groupby="cell_type",
        cmap="coolwarm",
        vmax=2,
        vmin=-2,
        dendrogram=True,
        return_fig=True
    )
    fig.savefig(f"{artifact_dir}/dorothea_tumor_{i}.pdf", bbox_inches="tight")

# %% [markdown]
# ## Write output file

# %%
adata.write_h5ad(f"{artifact_dir}/adata_epithelial.h5ad")
adata.write_h5ad(f"{artifact_dir}/adata_tumor.h5ad")

# %%
