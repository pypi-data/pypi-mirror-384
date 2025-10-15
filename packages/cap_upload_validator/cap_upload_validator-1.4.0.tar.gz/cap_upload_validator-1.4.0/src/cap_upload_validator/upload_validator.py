import pandas as pd
import numpy as np
from scipy.sparse import issparse
from cap_anndata import CapAnnData, read_h5ad
import logging
from h5py import Dataset

from .gene_mapping import (
    GeneMap,
    HomoSapiens,
    MusMusculus,
    MultiSpecies,
    Organism,
    str_to_organism,
    ontology_id_to_organism,
)
from .errors import (
    CapMultiException,
    AnnDataFileMissingCountMatrix,
    AnnDataMissingEmbeddings,
    AnnDataMissingObsColumns,
    AnnDataNonStandardVarError,
    BadAnnDataFile,
    AnnDataNoneInGeneralMetadata,
)

logger = logging.getLogger(__name__)

MAX_OBS_ROWS_TO_CHECK = 100
EMBEDDING_PREFIX = "X_"
ORGANISM_COLUMN = "organism"
ORGANISM_ONT_ID_COLUMN = f"{ORGANISM_COLUMN}_ontology_term_id"
GENERAL_METADATA = ["assay", "disease", ORGANISM_COLUMN, "tissue"]

class UploadValidator:

    """The class perform the validation """
    def __init__(self, adata_path: str) -> None:
        self._adata_path = adata_path
        # Create container to raise a multiple errors for client
        self._multi_exception = CapMultiException()    
        self._organism: Organism = None  
        self._ensembl_ids = None

    @property
    def adata_path(self) -> str:
        return self._adata_path
    
    @property
    def organism(self) -> str:
        return self._organism

    @property
    def ensembl_ids(self) -> pd.Index:
        return self._ensembl_ids

    def validate(self, report_success: bool = True) -> None:
        """The method validates the input AnnData on the upload stage and raises exceptions if something wrong."""
        logger.debug("Begin anndata file validation...")

        if not str(self._adata_path).endswith(".h5ad"):
            raise BadAnnDataFile
        
        with read_h5ad(self._adata_path, edit=False) as cap_adata:
            cap_adata.read_obs(columns=GENERAL_METADATA)  # TODO: read all columns?
            cap_adata.read_var(columns=[])
            if cap_adata.raw is not None:
                cap_adata.raw.read_var(columns=[])

            self._check_X(cap_adata)
            self._check_obsm(cap_adata)
            self._check_obs(cap_adata)
            self._check_var_index(cap_adata)

        # Check any errors were during validation stage and raise them
        if self._multi_exception.have_errors():
            raise self._multi_exception
        if report_success:
            print("Validation passed!")
        logger.debug("Finish anndata file validation")

    def _check_X(self, cap_adata: CapAnnData) -> None:
        logger.debug("Begin checking X")
        X = cap_adata.raw.X if cap_adata.raw is not None else cap_adata.X
        if X is None or not self._check_is_positive_integers(cap_adata):
            self._multi_exception.append(AnnDataFileMissingCountMatrix())
        logger.debug("Finished checking X!")

    @staticmethod
    def has_only_integers(arr: np.ndarray) -> bool:
        return np.all((arr - arr.astype(int)) == 0)

    @staticmethod
    def has_negative_values(arr: np.ndarray) -> bool:
        return np.any(arr < 0)

    def _check_is_positive_integers(self, cap_adata: CapAnnData) -> bool:
        n_cells = cap_adata.shape[0]
        max_rows = min(n_cells, MAX_OBS_ROWS_TO_CHECK)

        X = cap_adata.raw.X if cap_adata.raw is not None else cap_adata.X

        is_sparse = issparse(X[0])
        logger.debug(f"Checking elements in X to be positive integers, with n_cells = {n_cells}, max_rows = {max_rows}, is_sparse = {is_sparse}!")

        arr = X[0:max_rows].data if is_sparse else X[0:max_rows]
        if not self.has_only_integers(arr) or self.has_negative_values(arr):
            logger.debug(f"There are not positive integers found in X!")
            return False

        return True

    def _check_obsm(self, cap_adata: CapAnnData) -> None:
        logger.debug("Begin checking obsm")
        if self._has_embeddings(cap_adata) is False:
            self._multi_exception.append(AnnDataMissingEmbeddings())
        logger.debug("Finished checking obsm!")

    def _has_embeddings(self, cap_adata: CapAnnData) -> bool:
        if cap_adata.obsm is None:
            logger.debug("Obsm is not found in anndata!")
            return False
        
        n_cells = cap_adata.shape[0]

        for field in cap_adata.obsm_keys():
            if field.startswith(EMBEDDING_PREFIX):
                entity = cap_adata.obsm[field]
                if isinstance(entity, Dataset) and entity.shape == (n_cells, 2):
                    # looking for dense matrix of N x 2 shape 
                    return True

        logger.debug(f"Embeddings not found in obsm_keys = {cap_adata.obsm_keys()}!")
        return False

    def _check_obs(self, cap_adata: CapAnnData) -> None:
        logger.debug("Start checking obs")
        obs_keys = cap_adata.obs_keys()
        logger.debug(f"Checking obs_columns = {obs_keys} for required {GENERAL_METADATA}!")
        
        if cap_adata.obs is None or not obs_keys:
            logger.warning(".obs is missing!")
            self._multi_exception.append(AnnDataMissingObsColumns())
            return

        for col in GENERAL_METADATA:
            ont_id_col = f"{col}_ontology_term_id"
            col_in_obs = col in obs_keys
            ont_id_col_in_obs = ont_id_col in obs_keys

            if not (col_in_obs or ont_id_col_in_obs):
                logger.debug(f"Column {col} is missing in .obs!")
                self._multi_exception.append(AnnDataMissingObsColumns(f"{col} column is missing in .obs!"))
                return
            else:
                if col_in_obs:
                    if not self._check_df_col_for_none(cap_adata.obs[col]):
                        logger.debug(f"Column {col} contains None or empty values in .obs!")
                        self._multi_exception.append(AnnDataNoneInGeneralMetadata(f"{col} column contains None or empty values in .obs!"))
                        return
                if ont_id_col_in_obs:
                    cap_adata.read_obs([ont_id_col])
                    if not self._check_df_col_for_none(cap_adata.obs[ont_id_col]):
                        logger.debug(f"Column {ont_id_col} contains None or empty values in .obs!")
                        self._multi_exception.append(AnnDataNoneInGeneralMetadata(f"{ont_id_col} column contains None or empty values in .obs!"))
                        return
        logger.debug("Finished checking obs!")

    @staticmethod
    def _check_df_col_for_none(series: pd.Series) -> bool:
        series = series.replace(r'^\s*$', np.nan, regex=True)
        return pd.notna(series).all()

    def _check_var_index(self, cap_adata: CapAnnData) -> None:
        logger.debug("Start checking var index...")
        index = cap_adata.var.index
        clean_index = self._remove_gene_version(index)
        self._ensembl_ids = clean_index

        if not clean_index.is_unique:
            logger.debug("There are non unique gene ids in .var.index!")
            self._multi_exception.append(AnnDataNonStandardVarError())
            return 

        # Check if the var.index is a subset of raw.var.index
        if cap_adata.raw is not None and cap_adata.raw.var is not None:
            logger.debug("As of raw exists, checking that var.index is a subset of raw.var.index!")
            if not index.isin(cap_adata.raw.var.index).all():
                self._multi_exception.append(AnnDataNonStandardVarError())
                return

        # Check the number of organisms in the dataset
        known_organisms = [HomoSapiens, MusMusculus] # Only Human and Mouse supported this moment
        known_organisms_values = {ko.name for ko in known_organisms}
        obs_keys = cap_adata.obs_keys()
        if ORGANISM_COLUMN in obs_keys:
            dataset_organisms = cap_adata.obs[ORGANISM_COLUMN].unique().tolist()
            if "" in dataset_organisms:
                dataset_organisms.remove("")
            dataset_organisms = list(map(str_to_organism, dataset_organisms))
        elif ORGANISM_ONT_ID_COLUMN in obs_keys:
            if ORGANISM_ONT_ID_COLUMN not in cap_adata.obs.columns:
                cap_adata.read_obs(columns=[ORGANISM_ONT_ID_COLUMN])
            org_ont_ids = cap_adata.obs[ORGANISM_ONT_ID_COLUMN].unique().tolist()
            if "" in org_ont_ids:
                org_ont_ids.remove("")
            dataset_organisms = list(map(ontology_id_to_organism, org_ont_ids))
        else:
            dataset_organisms = []
        logger.debug(f"Organism(s) in dataset = {dataset_organisms}, known organisms = {known_organisms_values}")
       
        # Check ENSEMBL ids for supported organism
        if len(dataset_organisms) == 1:
            organism = dataset_organisms[0]
            self._organism = organism
            if organism.name in known_organisms_values:
                logger.debug("There is the only known organisms in dataset, so we must check for Unsemble IDs in var.index!")
                self._validate_gene_ids(ens_ids=clean_index, organism=organism)
            else:
                logger.debug("Unknown organisms in dataset found, index var validation skipped!")
        elif len(dataset_organisms) > 1:
            logger.debug("There are multiple organisms in dataset")
            self._organism = MultiSpecies
            self._validate_gene_ids(
                ens_ids=clean_index,
                organism=self._organism,
                )
        logger.debug("Finished checking var index!")
    
    def _validate_gene_ids(
            self,
            ens_ids: pd.Series,
            organism: str,
        ) -> None:
        if not (ens_ids.empty or pd.api.types.is_any_real_numeric_dtype(ens_ids)) : 
            # Check genes with gene maps
            df = GeneMap.data_frame(organisms=organism)
            if not ens_ids.isin(df['ENSEMBL_gene']).all():
                # Gene names are non standard
                logger.debug("Gene names are not standard!")
                self._multi_exception.append(AnnDataNonStandardVarError())
        else:
            # Gene names are missed
            logger.debug("Gene names are missed!")
            self._multi_exception.append(AnnDataNonStandardVarError())

    @staticmethod
    def _remove_gene_version(ensemble_ids: pd.Index) -> pd.Index:
        """
        The static methods removes the version suffixes from the ensemble ids.
        Examples:
            ENSG0001.8 -> ENSG0001
            ENSG0001   -> ENSG0001
        """
        clean_index = ensemble_ids.to_series().apply(lambda x: x.split(".")[0])
        clean_index = pd.Index(clean_index)
        return clean_index
