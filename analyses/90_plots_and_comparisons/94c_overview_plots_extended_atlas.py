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
from scanpy_helpers.annotation import AnnotationHelper
from nxfvars import nxfvars
import altair as alt
from toolz.functoolz import pipe
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import scanpy_helpers as sh
import statsmodels.formula.api as smf
from tqdm.contrib.concurrent import process_map
import itertools
import progeny
import dorothea
from threadpoolctl import threadpool_limits
from matplotlib_venn import venn3

# %%
alt.data_transformers.disable_max_rows()

# %%
sc.set_figure_params(figsize=(5, 5))

# %%
ah = AnnotationHelper()

# %%
main_adata = nxfvars.get(
    "main_adata",
    "../../data/20_build_atlas/add_additional_datasets/03_update_annotation/artifacts/full_atlas_merged.h5ad",
)
epithelial_adata = nxfvars.get(
    "epithelial_adata",
    "../../data/20_build_atlas/annotate_datasets/35_final_atlas/artifacts/epithelial_cells_annotated.h5ad",
)
tumor_adata = nxfvars.get(
    "tumor_adata",
    "../../data/20_build_atlas/annotate_datasets/33_cell_types_epi/artifacts/adata_tumor.h5ad",
)
threadpool_limits(nxfvars.get("cpus", 16))
artifact_dir = nxfvars.get("artifact_dir", "/home/sturm/Downloads/")

# %%
adata = sc.read_h5ad(main_adata)

# %%
adata_core_tumor = sc.read_h5ad(epithelial_adata)

# %%
adata_core_epi = sc.read_h5ad(tumor_adata)

# %% [markdown]
# # Stats and metadata

# %%
adata.X.data.size

# %%
adata.shape[0]

# %%
adata.obs["sample"].nunique()

# %%
adata.obs["platform"].nunique()

# %%
adata.obs["cell_type"].nunique()

# %%
adata.obs["patient"].nunique()

# %%
adata.obs["dataset"].nunique()

# %%
adata.obs["study"].nunique()

# %%
adata.obs.columns

# %%
adata.obs.loc[:, ["patient", "condition"]].drop_duplicates()["condition"].value_counts()

# %%
adata.obs["study"].value_counts().sort_index()

# %%
adata.obs.loc[lambda x: x["origin"].str.contains("tumor")]["patient"].nunique()

# %% [markdown]
# # Overview bar charts

# %%
df = (
    adata.obs.loc[lambda x: x["origin"].str.contains("tumor_primary")]
    .groupby(["study"])
    .apply(lambda x: x["patient"].nunique())
    .reset_index(name="# patients with primary tumor samples")
    .loc[lambda x: x["# patients with primary tumor samples"] > 0]
    .sort_values("# patients with primary tumor samples")
)
ch = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x="# patients with primary tumor samples",
        y=alt.Y("study", sort="x"),
        color=alt.Color(
            "# patients with primary tumor samples",
            scale=alt.Scale(scheme="viridis"),
            legend=None,
        ),
    )
)
ch + (ch).mark_text(align="left", dx=3).encode(
    text="# patients with primary tumor samples", color=alt.value("black")
)

# %% [markdown]
# ## study by cell-type

# %%
count_by_cell_type = adata.obs.groupby(["study", "cell_type_coarse"]).agg(
    n_cells=pd.NamedAgg("cell_type_coarse", "count")
)
count_by_cell_type["frac_cells"] = adata.obs.groupby("study")[
    "cell_type_coarse"
].value_counts(normalize=True)
count_by_cell_type.reset_index(inplace=True)
# count_by_cell_type.to_csv(f"{artifact_dir}/cell_type_coarse_per_dataset.tsv", sep="\t")

# %%
c1 = (
    alt.Chart(count_by_cell_type)
    .mark_bar()
    .encode(
        x="n_cells",
        color=alt.Color(
            "cell_type_coarse", scale=sh.colors.altair_scale("cell_type_coarse")
        ),
        y=alt.Y("study", sort="x"),
    )
)
s1 = (
    alt.Chart(count_by_cell_type)
    .mark_bar()
    .encode(
        x=alt.X("n_cells", scale=alt.Scale(nice=False)),
        color=alt.Color(
            "cell_type_coarse", scale=sh.colors.altair_scale("cell_type_coarse")
        ),
    )
)
c1


# %%
c1.encode(x=alt.X("n_cells", title="n_cells", stack="normalize"), y=alt.Y("study"))

# %%
data = (
    adata.obs.groupby(["study", "sample", "origin"], observed=True)
    .size()
    .reset_index(name="n_cells")
)
c2 = (
    alt.Chart(data)
    .mark_bar()
    .encode(
        x=alt.X("count(sample)", title="n_samples"),
        color=alt.Color(
            "origin",
            scale=sh.colors.altair_scale("origin", data=data, data_col="origin"),
        ),
        y=alt.Y("study", axis=None),
    )
)
s2 = (
    alt.Chart(data)
    .mark_bar()
    .encode(
        x=alt.X("count(sample)", title="n_samples", scale=alt.Scale(nice=False)),
        color=alt.Color(
            "origin",
            scale=sh.colors.altair_scale("origin", data=data, data_col="origin"),
        ),
    )
)

# %% [markdown]
# ### By patients

# %%
data = (
    adata.obs.groupby(["study", "patient", "condition"], observed=True)
    .size()
    .reset_index(name="n_cells")
)
c3 = (
    alt.Chart(data)
    .mark_bar()
    .encode(
        x=alt.X("count(patient)", title="n_patients"),
        color=alt.Color(
            "condition",
            scale=sh.colors.altair_scale("condition", data=data, data_col="condition"),
        ),
        y=alt.Y("study", axis=None),
    )
)
s3 = (
    alt.Chart(data)
    .mark_bar()
    .encode(
        x=alt.X("count(patient)", title="n_patients", scale=alt.Scale(nice=False)),
        color=alt.Color(
            "condition",
            scale=sh.colors.altair_scale("condition", data=data, data_col="condition"),
        ),
    )
)


# %%
(
    s1.properties(width=200) | s2.properties(width=200) | s3.properties(width=200)
).resolve_scale(color="independent")

# %%
(
    c1.encode(x=alt.X("n_cells", title="n_cells", stack="normalize")).properties(
        width=200
    )
    | c2.encode(x=alt.X("n_cells", title="n_cells", stack="normalize")).properties(
        width=200
    )
    | c3.encode(x=alt.X("n_cells", title="n_cells", stack="normalize")).properties(
        width=200
    )
).resolve_scale(color="independent", y="shared")

# %%
(
    c1.properties(width=200) | c2.properties(width=200) | c3.properties(width=200)
).resolve_scale(color="independent", y="shared")

# %% [markdown]
# ## Sample types per patient

# %%
data = (
    adata.obs.groupby(["study", "patient", "origin"], observed=True)
    .size()
    .reset_index(name="n_cells")
)

# %%
alt.Chart(data).mark_bar().encode(
    x=alt.X("count(patient)", title="# patients"),
    y="origin",
    color=alt.Color(
        "origin", scale=sh.colors.altair_scale("origin", data=data, data_col="origin")
    ),
)

# %%
venn_labels = {
    "normal": ["normal_adjacent", "normal"],
    "primary\ntumor": ["tumor_primary"],
    "metastases": ["tumor_metastasis"],
}
venn_sets = {
    key: set(data.loc[lambda x: x["origin"].isin(labels), "patient"].values)
    for key, labels in venn_labels.items()
}

# %%
with plt.rc_context({"font.size": 16, "figure.figsize": (10, 6)}):
    venn3(
        venn_sets.values(),
        set_labels=venn_sets.keys(),
        set_colors=[
            sh.colors.COLORS.origin[x]
            for x in ["normal", "tumor_primary", "tumor_metastasis"]
        ],
        alpha=0.6,
    )
    plt.show()

# %% [markdown]
# ## cell-type fractions by origin

# %%
plot_df = (
    adata.obs.loc[lambda x: x["origin"].isin(["normal_adjacent", "tumor_primary"]), :]
    .groupby(["patient", "origin"])
    .apply(lambda x: x["cell_type_major"].value_counts(normalize=True).fillna(0))
    .reset_index()
    .rename(columns={"level_2": "cell_type", "cell_type_major": "fraction"})
    .groupby(["origin", "cell_type"])
    .apply(lambda x: x["fraction"].mean())
    .reset_index(name="fraction")
)

# %%
ch = (
    alt.Chart(plot_df)
    .encode(
        x="fraction",
        y="origin",
        color=alt.Color("cell_type", scale=sh.colors.altair_scale("cell_type_major")),
    )
    .mark_bar()
)
ch.save(f"{artifact_dir}/cell_type_fractions_by_origin.svg")
ch.display()


# %% [markdown]
# # Patients per cell-type

# %%
def get_patients_per_cell_type(
    adata, cell_type_col="cell_type", *, cutoffs=[5, 10, 30], patient_col="patient"
):
    cell_type_matrix = (
        adata.obs.groupby([patient_col, cell_type_col], observed=False)
        .size()
        .reset_index(name="n_cells")
        .pivot_table(values="n_cells", columns=cell_type_col, index=patient_col)
    )
    return pd.DataFrame(
        {cutoff: np.sum(cell_type_matrix >= cutoff, axis=0) for cutoff in cutoffs}
    )


# %%
for cell_type_col in [
    "cell_type_tumor",
    "cell_type",
    "cell_type_major",
    "cell_type_coarse",
]:
    get_patients_per_cell_type(adata, cell_type_col).to_csv(
        f"{artifact_dir}/patients_per_{cell_type_col}.csv"
    )

# %% [markdown]
# ## Export patient table

# %%
## Export patient table
patient_metadata = (
    adata.obs.loc[
        :,
        [
            "study",
            "dataset",
            "patient",
            "uicc_stage",
            "tumor_stage",
            "sex",
            "ever_smoker",
            "driver_genes",
            "condition",
            "age",
            "platform",
            "platform_fine",
        ],
    ]
    .drop_duplicates()
    .sort_values(
        [
            "study",
            "dataset",
            "patient",
        ]
    )
    .reset_index(drop=True)
)

patient_metadata.to_csv(f"{artifact_dir}/patient_table.csv")

# get rid of duplicated patients (that occur in multiple datasets)
patient_metadata = patient_metadata.drop(columns=["dataset", "platform_fine"]).drop_duplicates()
assert patient_metadata.shape[0] == patient_metadata["patient"].nunique()

# %%
patient_metadata["condition"].value_counts()

# %%
patient_metadata

# %%
patient_metadata["group"] = patient_metadata["condition"].map(
    {
        "LUAD": "NSCLC",
        "non-cancer": "control",
        "LUSC": "NSCLC",
        "COPD": "control",
        "NSCLC NOS": "NSCLC",
    }
)

# %%
for c in [
    "sex",
    "uicc_stage",
    "tumor_stage",
    "ever_smoker",
    "condition",
    "platform",
]:
    patient_metadata[c] = (
        patient_metadata[c].astype(str).map(lambda x: np.nan if x == "None" else x)
    )

# %%
patient_metadata.groupby("group").size().reset_index(name="n")

# %%
patient_metadata.groupby("group")["age"].agg(median=np.median, min=np.min, max=np.max)

# %%
patient_metadata.groupby("group")["sex"].value_counts(
    dropna=False, normalize=True
).unstack()

# %%
patient_metadata.groupby("group")["condition"].value_counts(
    dropna=False, normalize=True
).unstack()

# %%
patient_metadata.groupby("group")["ever_smoker"].value_counts(
    dropna=False, normalize=True
).unstack()

# %%
patient_metadata.groupby("group")["tumor_stage"].value_counts(
    dropna=False, normalize=True
).unstack()

# %%
patient_metadata.groupby("group")["uicc_stage"].value_counts(
    dropna=False, normalize=True
).unstack()

# %% [markdown]
# # UMAP plots
#
# UMAP overview plots of the "core" atlas (without projected datasets)

# %%
with plt.rc_context({"figure.figsize": (5, 5), "figure.dpi": 300}):
    fig = sc.pl.umap(
        adata,
        color="cell_type_coarse",
        legend_loc="on data",
        legend_fontsize=8,
        legend_fontoutline=2,
        frameon=False,
        # add_outline=True,
        # size=1,
        return_fig=True,
        title="",
    )
    fig.savefig(f"{artifact_dir}/umap_extended_atlas.pdf", dpi=1200)

# %%
with plt.rc_context({"figure.figsize": (5, 5), "figure.dpi": 300}):
    fig = sc.pl.umap(
        adata,
        color="cell_type_coarse",
        legend_loc=None,
        legend_fontsize=8,
        legend_fontoutline=2,
        frameon=False,
        # add_outline=True,
        # size=1,
        return_fig=True,
        title="",
    )
    fig.savefig(
        f"{artifact_dir}/umap_extended_atlas_no_legend.pdf",
        dpi=1200,
        bbox_inches="tight",
    )

# %%
sh.colors.set_scale_anndata(adata, "cell_type_major")
with plt.rc_context({"figure.figsize": (5, 5), "figure.dpi": 300}):
    fig = sc.pl.umap(
        adata,
        color="cell_type_major",
        groups=[x for x in adata.obs["cell_type_major"].unique() if x != "other"],
        legend_loc="on data",
        legend_fontsize=6,
        legend_fontoutline=2,
        na_in_legend=False,
        frameon=False,
        # add_outline=True,
        # size=1,
        return_fig=True,
        title="",
    )
    fig.savefig(
        f"{artifact_dir}/umap_extended_atlas_cell_type_major.pdf",
        dpi=1200,
        bbox_inches="tight",
    )

# %%
adata.obs["study_extended"] = adata.obs.loc[
    lambda x: x["dataset"].str.contains("Leader")
    | x["dataset"].str.contains("UKIM-V-2"),
    "study",
].astype(str)

# %%
with plt.rc_context({"figure.figsize": (5, 5), "figure.dpi": 300}):
    fig = sc.pl.umap(
        adata,
        color="study_extended",
        frameon=False,
        # add_outline=True,
        size=1,
        return_fig=True,
        title="",
        alpha=0.5,
    )
    fig.savefig(
        f"{artifact_dir}/umap_extended_atlas_projected_data.pdf",
        dpi=1200,
        bbox_inches="tight",
    )


# %% [markdown]
# # Process subsets

# %%
def process_subset(mask):
    print(np.sum(mask))
    adata_sub = adata[mask, :].copy()
    sc.pp.neighbors(adata_sub, use_rep="X_scANVI")
    sc.tl.umap(adata_sub)
    return adata_sub


# %%
adatas = {
    label: process_subset(ct)
    for label, ct in {
        "immune": adata.obs["cell_type_coarse"].isin(
            [
                "T cell",
                "NK cell",
                "Neutrophils",
                "Plasma cell",
                "Mast cell",
                "B cell",
                "pDC",
                "cDC",
                "Macrophage/Monocyte",
            ]
        ),
        "structural": adata.obs["cell_type_coarse"].isin(
            ["Endothelial cell", "Stromal"]
        ),
        "UKIM-V": adata.obs["study"] == "UKIM-V",
    }.items()
}

# %%
# Initialize those with the positions from the core atlas.
adatas["epithelial"] = adata[
    adata.obs["cell_type_coarse"].isin(["Epithelial cell"]), :
].copy()
adatas["tumor"] = adata[adata.obs["cell_type_major"] == "Tumor cells", :].copy()

# %%
sh.colors.set_scale_anndata(adatas["tumor"], "cell_type_tumor")

# %%
for core_adata, tmp_adata in zip(
    [adata_core_tumor, adata_core_epi], [adatas[x] for x in ["tumor", "epithelial"]]
):
    # initalize umap with the original coordinates. Missing values (=query) are initialized with random values.
    init_pos_df = pd.DataFrame(
        core_adata.obsm["X_umap"], index=core_adata.obs_names
    ).reindex(tmp_adata.obs_names)
    for col in init_pos_df.columns:
        na_mask = init_pos_df[col].isnull()
        init_pos_df.loc[na_mask, col] = np.random.uniform(
            np.min(init_pos_df[col]), np.max(init_pos_df[col]), size=np.sum(na_mask)
        )
    sc.pp.neighbors(tmp_adata, use_rep="X_scANVI")
    sc.tl.umap(tmp_adata, init_pos=init_pos_df.values)

# %% [markdown]
# # Visualize subsets

# %%
adatas["UKIM-V"].obs["cell_type_coarse"].value_counts()

# %%
adatas["UKIM-V"].obs.loc[
    lambda x: x["origin"] == "tumor_primary", "cell_type_coarse"
].value_counts()

# %%
adatas["UKIM-V"].obs.loc[
    lambda x: x["origin"] == "normal_adjacent", "cell_type_coarse"
].value_counts()

# %%
np.sum(adata.obs["study"] == "UKIM-V")

# %%
with plt.rc_context({"figure.figsize": (5, 5), "figure.dpi": 300}):
    fig = sc.pl.umap(
        adatas["UKIM-V"],
        color="cell_type_coarse",
        legend_loc="on data",
        legend_fontsize=8,
        legend_fontoutline=2,
        frameon=False,
        # add_outline=True,
        size=2,
        return_fig=True,
        title="",
    )
    fig.savefig(f"{artifact_dir}/umap_ukim-v.pdf", dpi=1200, bbox_inches="tight")

# %%
np.median(
    adatas["UKIM-V"][
        (adatas["UKIM-V"].obs["cell_type_coarse"] == "Epithelial cell")
        & (adatas["UKIM-V"].obs["origin"] == "normal_adjacent"),
        :,
    ].obs["total_counts"]
)

# %%
print(
    adatas["UKIM-V"]
    .obs.groupby("patient")
    .agg(
        median_n_counts=("total_counts", np.median),
        mean_n_counts=("total_counts", np.mean),
    )
    .to_string()
)

# %%
print(
    adatas["UKIM-V"][
        (adatas["UKIM-V"].obs["cell_type_coarse"] == "Epithelial cell")
        & (adatas["UKIM-V"].obs["origin"] == "normal_adjacent"),
        :,
    ]
    .obs.groupby("patient")
    .agg(
        median_n_counts=("total_counts", np.median),
        mean_n_counts=("total_counts", np.mean),
    )
    .to_string()
)

# %%
print(
    adatas["UKIM-V"][
        (adatas["UKIM-V"].obs["cell_type_coarse"] == "Neutrophils"),
        # & (adatas["UKIM-V"].obs["origin"] == "normal_adjacent"),
        :,
    ]
    .obs.groupby("patient")
    .agg(
        median_n_counts=("total_counts", np.median),
        mean_n_counts=("total_counts", np.mean),
    )
    .to_string()
)

# %%
adatas["UKIM-V"][
    adatas["UKIM-V"].obs["cell_type_coarse"] == "Neutrophils", :
].obs.groupby(["patient", "origin"]).size()

# %%
with plt.rc_context({"figure.figsize": (5, 5), "figure.dpi": 300}):
    fig = sc.pl.umap(
        adatas["structural"],
        color="cell_type",
        legend_loc="on data",
        legend_fontsize=8,
        legend_fontoutline=2,
        frameon=False,
        # add_outline=True,
        size=1,
        return_fig=True,
        title="",
    )
    fig.savefig(
        f"{artifact_dir}/umap_extended_atlas_structural.pdf",
        dpi=1200,
        bbox_inches="tight",
    )

# %%
with plt.rc_context({"figure.figsize": (5, 5), "figure.dpi": 300}):
    fig = sc.pl.umap(
        adatas["immune"],
        color="cell_type",
        legend_loc="on data",
        legend_fontsize=6,
        legend_fontoutline=2,
        frameon=False,
        # add_outline=True,
        size=None,
        return_fig=True,
        title="",
    )
    fig.savefig(
        f"{artifact_dir}/umap_extended_atlas_immune.pdf", dpi=1200, bbox_inches="tight"
    )

# %%
with plt.rc_context({"figure.figsize": (5, 5), "figure.dpi": 300}):
    fig = sc.pl.umap(
        adatas["epithelial"],
        color="cell_type",
        legend_loc="on data",
        legend_fontsize=8,
        legend_fontoutline=2,
        frameon=False,
        # add_outline=True,
        size=1,
        return_fig=True,
        title="",
    )
    fig.savefig(
        f"{artifact_dir}/umap_extended_atlas_epithelial.pdf",
        dpi=1200,
        bbox_inches="tight",
    )

# %%
with plt.rc_context({"figure.figsize": (3, 3), "figure.dpi": 300}):
    fig = sc.pl.umap(
        adatas["tumor"],
        color="cell_type_tumor",
        legend_loc="right margin",
        legend_fontsize=8,
        legend_fontoutline=2,
        frameon=False,
        # add_outline=True,
        size=1,
        return_fig=True,
        title="",
    )
    fig.savefig(
        f"{artifact_dir}/umap_extended_atlas_tumor.pdf", dpi=1200, bbox_inches="tight"
    )

# %%
adatas["tumor"].shape

# %%
tumor_markers = {
    "Epithelial": ["EPCAM", "B2M"],
    "Alveolar cell type 1": ["AGER", "CLDN18"],
    "Alveolar cell type 2": ["SFTPC", "SFTPB", "SFTPA1"],
    "Ciliated": ["PIFO", "FOXJ1", "HYDIN", "CFAP299"],
    "Club": ["SCGB3A1", "SCGB3A2"],
    "LUAD": ["CD24", "MUC1", "NAPSA", "NKX2-1", "KRT7", "MSLN"],
    "LUSC": ["KRT5", "KRT6A", "TP63", "NTRK2", "SOX2", "KRT17"],
    "NE": ["CHGA", "SYP", "NCAM1", "TUBA1A"],
    "EMT": ["VIM", "SERPINE1", "CDH1"],
    "non-coding": ["MALAT1", "NEAT1"],
    "mitotic": ["MKI67", "TOP2A"],
    "undifferentiated": ["TACSTD2", "AGR2"],
}

# %%
sc.pl.dotplot(adatas["tumor"], groupby="cell_type_tumor", var_names=tumor_markers)
