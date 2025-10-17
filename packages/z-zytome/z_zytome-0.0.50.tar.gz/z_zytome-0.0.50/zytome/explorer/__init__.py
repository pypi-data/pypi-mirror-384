import logging
import os
from functools import partial
from typing import Callable
from typing import List
from typing import Optional

import anndata as ad
import numpy as np
import pandas as pd
import requests
from scipy import sparse as sp

from zytome.explorer.download import download_with_progress
from zytome.portal._interfaces.dataset import DatasetInterface
from zytome.portal._interfaces.dataset import Handler
from zytome.portal.gtex.base import GTExBulkInterface


logger = logging.getLogger(__name__)

Filter = Callable[[ad.AnnData], ad.AnnData]


class Dataset(DatasetInterface):
    def __init__(
        self, adata: ad.AnnData, dataset: DatasetInterface, filters: List[Filter]
    ):
        self._adata = adata
        self._dataset = dataset
        self._filters = filters
        self._raw = None
        self._raw_normalized_by_feature_length = None

    @property
    def short_name(self) -> str:
        return self._dataset.short_name

    @property
    def long_name(self) -> str:
        return self._dataset.long_name

    @property
    def tissues(self) -> list[str]:
        return self._dataset.tissues

    @property
    def diseases(self) -> list[str]:
        return self._dataset.diseases

    @property
    def assays(self) -> list[str]:
        return self._dataset.assays

    @property
    def organism(self) -> str:
        return self._dataset.organism

    @property
    def num_cells(self) -> int:
        return self._dataset.num_cells

    @property
    def download_link(self) -> str:
        return self._dataset.download_link

    @property
    def handler(self) -> Handler:
        return self._dataset.handler

    @property
    def adata(self) -> ad.AnnData:
        self._apply_filters()
        return self._adata

    @property
    def cell_types(self) -> list[str]:
        return list(self.adata.obs["cell_types"].unique())

    def _apply_filters(self):
        adata = self._adata

        for filter_fn in self._filters:
            adata = filter_fn(adata)

        self._filters = []
        self._adata = adata

    @property
    def raw(self) -> np.ndarray:
        X = self.adata.raw.X
        if sp.issparse(X):
            return X.toarray()
        elif isinstance(X, np.ndarray):
            return X
        else:
            raise TypeError(f"type of X {type(X)} is unsupported.")

    def to_tpm(self) -> "Dataset":
        """
        Normalize raw counts to TPM (transcripts per million) using feature-length-normalized raw data.
        Returns a new Dataset without mutating the original.
        Raises ValueError if resulting TPM contains NaNs or Infs.
        """
        new_adata = self.adata.copy()
        normalized_X = self.raw_normalized_by_feature_length
        raw_X = self.values  # raw counts

        # --- helper for nan/inf detection ---
        def has_nan_inf(mat):
            if sp.issparse(mat):
                data = mat.data
                return np.isnan(data).any(), np.isinf(data).any()
            else:
                return np.isnan(mat).any(), np.isinf(mat).any()

        # --- check normalized_X first ---
        norm_has_nan, norm_has_inf = has_nan_inf(normalized_X)
        if norm_has_nan or norm_has_inf:
            # backtrack to raw counts
            raw_has_nan, raw_has_inf = has_nan_inf(raw_X)
            if raw_has_nan or raw_has_inf:
                msg = (
                    "Feature-length-normalized values contain NaN/Inf.\n"
                    "Backtracking shows raw counts (self.X) also contain "
                    f"{'NaN ' if raw_has_nan else ''}{'Inf' if raw_has_inf else ''}.\n"
                    "Please fix raw input before normalization."
                )
            else:
                msg = (
                    "Feature-length-normalized values contain NaN/Inf.\n"
                    "Raw counts (self.X) look clean, so the issue was introduced "
                    "during feature-length normalization."
                )
            logger.error(msg)
            raise ValueError(msg)

        # --- normalization to TPM ---
        if sp.issparse(normalized_X):
            row_sums = np.array(normalized_X.sum(axis=1)).ravel()
            row_sums[row_sums == 0] = 1.0
            inv_row_sums = 1.0 / row_sums
            D_inv = sp.diags(inv_row_sums)
            sum_normalized_X = D_inv.dot(normalized_X)
        else:
            row_sums = normalized_X.sum(axis=-1, keepdims=True)
            row_sums[row_sums == 0] = 1.0
            sum_normalized_X = normalized_X / row_sums

        tpm_X = sum_normalized_X * 1_000_000

        # --- final NaN check ---
        tpm_has_nan, tpm_has_inf = has_nan_inf(tpm_X)
        if tpm_has_nan or tpm_has_inf:
            msg = (
                "TPM normalization resulted in NaN/Inf values, "
                "even though input matrices were clean. "
                "This suggests division/scaling instability."
            )
            logger.error(msg)
            raise ValueError(msg)

        new_adata.X = tpm_X
        return Dataset(new_adata, self._dataset, [])

    @property
    def raw_normalized_by_feature_length(self):
        fl = self.feature_lengths  # shape (num_features,)

        # Replace zeros and NaNs with 1.0 to avoid division issues
        safe_fl = np.where(np.isnan(fl) | (fl == 0), 1.0, fl)

        if sp.issparse(self.raw):
            inv_fl = 1.0 / safe_fl
            return self.raw.multiply(inv_fl)
        else:
            return self.raw / safe_fl[None, :]

    @property
    def values(self) -> np.ndarray:
        X = self.adata.X
        if sp.issparse(X):
            return X.toarray()
        elif isinstance(X, np.ndarray):
            return X
        else:
            raise TypeError(f"type of X {type(X)} is unsupported.")

    @property
    def feature_lengths(self):
        return np.array(self.adata.var["feature_length"].values)

    @property
    def feature_names(self):
        return list(self.adata.var["feature_name"].index)

    @property
    def feature_name_name(self):
        """Returns the name of the index column of the feature name series. Example: 'ensembl_id'. This is useful in identifying gene name convetion"""
        return self.adata.var["feature_name"].index.name

    @property
    def feature_types(self):
        return self.adata.var["feature_type"]

    def filter(self, filter_fn: Filter) -> "Dataset":
        return Dataset(self._adata, self._dataset, self._filters + [filter_fn])

    def arrange_by_chromosome(
        self, put_genes_with_unknown_chromosome_at_the_end: bool = False
    ) -> tuple["Dataset", list[int]]:
        """
        Arrange genes by chromosome order (chr1-22, chrX, chrY, chrMT) and genomic position.
        Currently only supports GTEx datasets.

        Genes without chromosome annotations are discarded by default.

        Parameters
        ----------
        put_genes_with_unknown_chromosome_at_the_end : bool, default False
            If True, raises NotImplementedError (reserved for future use).
            If False, discards genes without valid chromosome annotations.

        Returns
        -------
        tuple[Dataset, list[int]]
            - Dataset with genes arranged by chromosome and position
            - List of 25 integers: gene counts per chromosome (chr1-22, X, Y, MT)
              Returns 0 for chromosomes with no genes present.

        Raises
        ------
        NotImplementedError
            If put_genes_with_unknown_chromosome_at_the_end is True.
        ValueError
            If dataset is not from GTEx handler.

        Examples
        --------
        >>> dx_sorted, counts = dx.arrange_by_chromosome()
        >>> print(counts)  # [1523, 1189, ..., 45, 37, 13]  # genes per chr1-22, X, Y, MT
        """
        if self.handler != "GTEx":
            raise ValueError(
                f"arrange_by_chromosome currently only supports GTEx datasets. "
                f"Got handler: {self.handler}"
            )

        if put_genes_with_unknown_chromosome_at_the_end:
            raise NotImplementedError(
                "put_genes_with_unknown_chromosome_at_the_end=True is not yet implemented"
            )

        self._apply_filters()

        # Define standard chromosome order
        STANDARD_CHR_ORDER = [f"chr{i}" for i in range(1, 23)] + [
            "chrX",
            "chrY",
            "chrMT",
        ]

        if "chromosome" not in self._adata.var.columns:
            raise ValueError(
                "Chromosome information not found in adata.var. "
                "This should have been added during GTEx data loading."
            )

        valid_chr_mask = self._adata.var["chromosome"].isin(STANDARD_CHR_ORDER)

        if not valid_chr_mask.all():
            logger.info("Discarding genes without valid chromosome annotations")

        filtered_adata = self._adata[:, valid_chr_mask].copy()

        chr_indices = filtered_adata.var["chromosome"].map(
            {chr_name: idx for idx, chr_name in enumerate(STANDARD_CHR_ORDER)}
        )
        start_positions = filtered_adata.var["start_position"].fillna(0).astype(int)

        sort_order = np.lexsort((start_positions, chr_indices))

        sorted_adata = filtered_adata[:, sort_order].copy()

        chr_counts = [
            int((sorted_adata.var["chromosome"] == chr_name).sum())
            for chr_name in STANDARD_CHR_ORDER
        ]

        new_dataset = Dataset(sorted_adata, self._dataset, [])

        return new_dataset, chr_counts


def load_data_from_portal(dataset: DatasetInterface):
    if dataset.handler == "CellXGene":
        adata = read_raw_h5ad(dataset)
        adata.X = adata.raw.X  # converts X back to the raw
        return Dataset(adata, dataset, [])
    elif dataset.handler == "GTEx":
        adata = read_gct_gz(dataset)
        return Dataset(adata, dataset, [])


def make_filter(
    *,
    assays: Optional[List[str]] = None,
    tissues: Optional[List[str]] = None,
    feature_types: Optional[List[str]] = None,
    cell_types: Optional[List[str]] = None,
    diseases: Optional[List[str]] = None,
    max_cells: Optional[int] = None,
    rng: Optional[np.random.Generator] = None,
):

    return partial(
        filter_adata,
        assays=assays,
        tissues=tissues,
        feature_types=feature_types,
        cell_types=cell_types,
        diseases=diseases,
        max_cells=max_cells,
        rng=rng,
    )


def get_zytome_dir() -> str:
    """This is where the datasets are stored"""
    return os.getenv("Z_ZYTOME_DIR", "./.zytome")


def read_gct_gz(dataset: GTExBulkInterface) -> ad.AnnData:
    import gzip

    assert dataset.handler == "GTEx"

    dir_name = dataset.long_name
    short_name = "dataset"
    download_link_gct_gz = dataset.download_link
    metadata_link = dataset.metadata_link
    gencode_link = dataset.gencode_link  # new field for GENCODE GTF

    base_dir = get_zytome_dir()
    dataset_dir = os.path.join(base_dir, dir_name)
    os.makedirs(dataset_dir, exist_ok=True)

    # --- GCT ---
    gct_path = os.path.join(dataset_dir, f"{short_name}.gct.gz")
    if not os.path.exists(gct_path):
        logger.info("GCT file not found, downloading from %s...", download_link_gct_gz)
        download_with_progress(download_link_gct_gz, gct_path)

    # Read GCT (skip first 2 lines: version + dimensions)
    df = pd.read_csv(gct_path, sep="\t", skiprows=2)
    gene_ids = df["Name"].values
    gene_symbols = df["Description"].values
    expr = df.drop(columns=["Name", "Description"]).T  # transpose: samples × genes

    # --- Metadata ---
    meta_path = os.path.join(dataset_dir, f"{short_name}_metadata.txt")
    if not os.path.exists(meta_path):
        logger.info("Metadata not found, downloading from %s...", metadata_link)
        download_with_progress(metadata_link, meta_path)

    # Parse metadata (skip comment lines)
    meta = pd.read_csv(meta_path, sep="\t", encoding="latin1", comment="#")
    if "SAMPID" in meta.columns:
        meta = meta.set_index("SAMPID")
    obs = meta.loc[expr.index].copy()

    # --- AnnData object ---
    adata = ad.AnnData(
        X=expr.values,
        obs=obs,
        var=pd.DataFrame(
            {
                "ensembl_id": gene_ids,
                "gene_symbol": gene_symbols,
                "feature_name": gene_ids,
            },
            index=gene_ids,
        ),
    )

    if "SMTSD" in obs.columns:
        adata.obs["tissue"] = obs["SMTSD"]

    # --- GENCODE annotations ---
    gtf_path = os.path.join(dataset_dir, os.path.basename(gencode_link))
    if not os.path.exists(gtf_path):
        logger.info("GENCODE GTF not found, downloading from %s...", gencode_link)
        download_with_progress(gencode_link, gtf_path)

    # Parse GTF for gene_type and feature_length
    gene_info = []
    open_func = gzip.open if gtf_path.endswith(".gz") else open
    with open_func(gtf_path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if parts[2] != "gene":
                continue
            chrom, start, end, attr_str = (
                parts[0],
                int(parts[3]),
                int(parts[4]),
                parts[8],
            )
            attrs = dict(
                item.strip().replace('"', "").split(" ")
                for item in attr_str.strip().split(";")
                if item
            )
            gene_info.append(
                {
                    "ensembl_id": attrs["gene_id"].split(".")[0],
                    "feature_type": attrs.get("gene_type"),
                    "feature_length": end - start + 1,
                    "chromosome": chrom,
                    "start_position": start,
                }
            )
    gtf_df = pd.DataFrame(gene_info).set_index("ensembl_id")

    # Merge GTF info into adata.var
    adata.var.index = adata.var["ensembl_id"].str.replace(r"\..*", "", regex=True)

    gtf_df.index = gtf_df.index.str.replace(r"\..", "", regex=True)

    gtf_df = gtf_df.groupby(gtf_df.index).agg(
        {
            "feature_type": "first",
            "feature_length": "first",
            "chromosome": "first",
            "start_position": "first",
        }
    )

    adata.var["feature_type"] = gtf_df["feature_type"].reindex(adata.var.index)
    adata.var["feature_length"] = gtf_df["feature_length"].reindex(adata.var.index)
    adata.var["chromosome"] = gtf_df["chromosome"].reindex(adata.var.index)
    adata.var["start_position"] = gtf_df["start_position"].reindex(adata.var.index)

    adata.raw = adata

    X = adata.X
    if sp.issparse(X):
        data = X.data
        has_nan_or_inf = np.isnan(data).any() or np.isinf(data).any()
        if has_nan_or_inf:
            logger.warning(
                "GCT read contains NaN or Inf values in adata.X (sparse). "
                "These values have been converted to 0 to ensure safe normalization."
            )
            data[np.isnan(data)] = 0.0
            data[np.isinf(data)] = 0.0
    else:
        has_nan_or_inf = np.isnan(X).any() or np.isinf(X).any()
        if has_nan_or_inf:
            logger.warning(
                "GCT read contains NaN or Inf values in adata.X (dense). "
                "These values have been converted to 0 to ensure safe normalization."
            )
            adata.X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    logger.info(f"{dataset.short_name} is loaded without any defects")
    return adata


def read_raw_h5ad(dataset: DatasetInterface) -> ad.AnnData:
    """
    This function reads the raw AnnData object for a given dataset.
    It first checks if the raw file exists locally. If not, it downloads
    it from the dataset's download link, saving it to a dataset-specific
    directory.  The directory structure is determined by the dataset's
    long name and the zytome directory obtained from `get_zytome_dir()`.
    Finally, it reads the AnnData object from the saved h5ad file.

    Parameters
    ----------
    dataset : DatasetInterface
        An object implementing the DatasetInterface, providing access to
        the dataset's long name and download link.

    Returns
    -------
    ad.AnnData
        The AnnData object read from the raw h5ad file.
    """
    dir_name = dataset.long_name
    short_name = "dataset"
    download_link = dataset.download_link

    base_dir = get_zytome_dir()
    dataset_dir = os.path.join(base_dir, dir_name)
    os.makedirs(dataset_dir, exist_ok=True)

    raw_path = os.path.join(dataset_dir, f"{short_name}_raw.h5ad")

    if not os.path.exists(raw_path):
        logger.info(f"[INFO] Raw file not found, downloading from {download_link}...")
        download_with_progress(download_link, raw_path)
        logger.info(f"[INFO] Saved raw data to {raw_path}")

    logger.info(f"[INFO] Reading AnnData from {raw_path}")
    return ad.read_h5ad(raw_path)


def filter_adata(
    adata: ad.AnnData,
    *,
    assays: Optional[List[str]] = None,
    tissues: Optional[List[str]] = None,
    cell_types: Optional[List[str]] = None,
    feature_types: Optional[List[str]] = None,
    diseases: Optional[List[str]] = None,
    max_cells: Optional[int] = None,
    rng: Optional[np.random.Generator] = None,
) -> ad.AnnData:
    """
    Filter AnnData object by cell-level metadata (assay, tissue),
    gene-level metadata (feature_type), and optionally cap the number
    of cells. Keeps .X sparse.

    Parameters
    ----------
    adata : AnnData
        Input AnnData object.
    assays : list[str], optional
        List of assay names to keep.
    tissues : list[str], optional
        List of tissue names to keep.
    feature_types : list[str], optional
        List of feature types to keep.
    max_cells : int, optional
        Maximum number of cells to retain after filtering.
    rng : np.random.Generator, optional
        NumPy random generator for sampling. If None, no shuffling,
        just take the first max_cells cells.

    Returns
    -------
    AnnData
        Filtered AnnData object.
    """
    mask_cells = np.ones(adata.n_obs, dtype=bool)
    mask_genes = np.ones(adata.n_vars, dtype=bool)

    if assays:
        mask_cells &= adata.obs["assay"].isin(assays)
    if tissues:
        mask_cells &= adata.obs["tissue"].isin(tissues)
    if diseases:
        mask_cells &= adata.obs["disease"].isin(diseases)
    if feature_types:
        mask_genes &= adata.var["feature_type"].isin(feature_types)
    if cell_types:
        mask_genes &= adata.var["cell_type"].isin(cell_types)

    adata_filtered = adata[mask_cells, mask_genes]

    if max_cells is not None and adata_filtered.n_obs > max_cells:
        if rng is not None:
            selected_idx = rng.choice(
                adata_filtered.n_obs, size=max_cells, replace=False
            )
        else:
            selected_idx = np.arange(max_cells)
        adata_filtered = adata_filtered[selected_idx, :]

    return adata_filtered
