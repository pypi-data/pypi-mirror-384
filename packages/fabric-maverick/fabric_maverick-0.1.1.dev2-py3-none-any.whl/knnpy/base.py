import time
import pandas as pd
from .comparers import TableComparer, MeasureComparer, ColumnComparer
from .validators import TableValidator, MeasureValidator, ColumnValidator, RelationshipValidator
from .utils import export_validation_results, get_run_details, get_raw_table_details, get_raw_measure_details, render_dataframe_tabs
from .report import FabricAnalyticsModel 
from .config import config
from sempy import fabric as sfabric
from .token_provider import UserCredAuth
import re
from notebookutils import mssparkutils
from pyspark.sql import SparkSession
import logging 
import threading
logger = logging.getLogger(__name__)

class ModelComparison:
    """
    Orchestrates the comparison and validation of two FabricAnalyticsModel objects.
    """

    def __init__(
            self, 
            model_new : FabricAnalyticsModel, 
            model_old : FabricAnalyticsModel, 
            stream: str, 
            threshold_score: float = 80.0
            ):
        """
        Initializes the ModelComparison object.

        Args:
            model_new (FabricAnalyticsModel): The new version of the model.
            model_old (FabricAnalyticsModel): The old version of the model.
            stream (str): A label for the comparison stream.
            threshold_score (float, optional): The fuzzy matching threshold. Defaults to 90.0.
        """
        self.model_new = model_new
        self.model_old = model_old
        self.stream = str.lower(str.strip(stream))
        self.threshold_score = threshold_score
        self.run_id = str(int(time.time()))

        # Comparers
        self._table_comparer = TableComparer(self.model_new.tables, self.model_old.tables, self.threshold_score)
        self._all_tables = self._table_comparer.compare()
        self.common_tables = self._all_tables[self._all_tables['origin'] == 'both']
        if self.common_tables is None or self.common_tables.empty:
            self._column_comparer = None
            self._all_columns = None
            self.common_columns = None
        else:
            self._column_comparer = ColumnComparer(self.model_new.columns, self.model_old.columns, self.common_tables, self.threshold_score)
            self._all_columns = self._column_comparer.compare()
            self.common_columns = self._all_columns[self._all_columns['origin'] == 'both']
        
        self._measure_comparer = MeasureComparer(self.model_new.measures, self.model_old.measures, self.threshold_score)
        self._all_measures = self._measure_comparer.compare()
        self.common_measures = self._all_measures[self._all_measures['origin'] == 'both']

        if self.common_tables is None or self.common_columns is None or self.common_measures is None or self.common_tables.empty or self.common_columns.empty or self.common_measures.empty:
            missing_parts = []
            if self.common_tables is None or self.common_tables.empty:
                missing_parts.append("table validation")
            if self.common_columns is None or self.common_columns.empty:
                missing_parts.append("column validation")
            if self.common_measures is None or self.common_measures.empty:
                missing_parts.append("measure validation")

            logger.warning(f"Cannot perform {', '.join(missing_parts)} due to missing common items. "
                        f"You may try decreasing the fuzzy match threshold.")
        # Results initialized to None
        self.TableValidationResults = None
        self.MeasureValidationResults = None
        self.ColumnValidationResults = None
        self.RelationshipValidationResults = None
        self.RunDetails = get_run_details(self)
        self.RawTables = None
        self.RawMeasures = None

    def run_table_validation(self, margin_of_error: float = config.margin_of_error, export: bool = False, lakehouse_config: dict = None):
        """
        Runs table row count validation.
        
        Args:
            margin_of_error (float, optional): Allowed percentage difference. Defaults to 5.0.
            export (bool, optional): If True, exports validation results to a lakehouse or external storage. Defaults to False.
            lakehouse_config (dict, optional): Configuration dictionary for exporting data to the lakehouse. 
                                               Should contain keys like 'workspace_id' and 'lakehouse_id'.
        """
        if self.common_tables is None or self.common_tables.empty:
            logger.warning("Table validation skipped: No common tables found. You may try decreasing the fuzzy match threshold.")
            return
        try:
            logger.info("Starting table validation...")
            start_time = time.time()
            self.table_validator = TableValidator(self.model_new, self.model_old, self.common_tables, self.run_id, self.stream)
            self.TableValidationResults = self.table_validator.validate_row_counts(margin_of_error)
            self.RawTables = get_raw_table_details(self)
            end_time = time.time()
            logger.info(f"Table validation completed in {end_time - start_time:.2f} seconds")
            if export:
                try:
                    results_to_export = [
                        ("Table Validation results", self.TableValidationResults)
                    ]
                    if lakehouse_config is None:
                        export_validation_results(self, results_to_export)
                    else:
                        export_validation_results(self, results_to_export, lakehouse_config)
                    logger.info("Table validation results exported successfully.")
                except Exception:
                    logger.error("Export failed during table validation.", exc_info=True)
        except Exception as e:
            logger.error(f"Error in table row count validation: {str(e)}")
            self.TableValidationResults = self.RawTables = pd.DataFrame()

    def run_column_validation(self, margin_of_error: float = config.margin_of_error, export: bool = False, lakehouse_config: dict = None):
        """
        Runs column level validations.
        
        Args:
            margin_of_error (float, optional): Allowed percentage difference. Defaults to 5.0.
            export (bool, optional): If True, exports validation results to a lakehouse or external storage. Defaults to False.
            lakehouse_config (dict, optional): Configuration dictionary for exporting data to the lakehouse. 
                                               Should contain keys like 'workspace_id' and 'lakehouse_id'.
        """
        if self.common_columns is None or self.common_columns.empty:
            logger.warning("Column validation skipped: No common columns found. You may try decreasing the fuzzy match threshold.")
            return
        try:
            logger.info("Starting column validation...")
            start_time = time.time()
            self.column_validator = ColumnValidator(self.model_new, self.model_old, self.common_columns, self.run_id, self.stream)
            self.ColumnValidationResults = self.column_validator.validate_distinct_counts(margin_of_error)
            end_time = time.time()
            logger.info(f"Column validation completed in {end_time - start_time:.2f} seconds")
            if export:
                try:
                    results_to_export = [
                        ("Column Validation results", self.ColumnValidationResults)
                    ]
                    if lakehouse_config is None:
                        export_validation_results(self, results_to_export)
                    else:
                        export_validation_results(self, results_to_export, lakehouse_config)
                    logger.info("Column validation results exported successfully.")
                except Exception:
                    logger.error("Export failed during column validation.", exc_info=True)
        except Exception as e:
            logger.error(f"Error in column validation: {str(e)}")
            self.ColumnValidationResults = pd.DataFrame()

    def run_measure_validation(self, margin_of_error: float = config.margin_of_error, export: bool = False, lakehouse_config: dict = None):
        """
        Runs measure level validation.
        
        Args:
            margin_of_error (float, optional): Allowed percentage difference. Defaults to 5.0.
            export (bool, optional): If True, exports validation results to a lakehouse or external storage. Defaults to False.
            lakehouse_config (dict, optional): Configuration dictionary for exporting data to the lakehouse. 
                                               Should contain keys like 'workspace_id' and 'lakehouse_id'.
        """
        if self.common_measures is None or self.common_measures.empty:
            logger.warning("Measure validation skipped: No common measures found. You may try decreasing the fuzzy match threshold.")
            return
        try:
            logger.info("Starting measure validation...")
            start_time = time.time()
            self.measure_validator = MeasureValidator(self.model_new, self.model_old, self.common_measures, self.run_id, self.stream)
            self.MeasureValidationResults = self.measure_validator.validate_measure_values(margin_of_error)
            self.RawMeasures = get_raw_measure_details(self)
            end_time = time.time()
            logger.info(f"Measure validation completed in {end_time - start_time:.2f} seconds")
            if export:
                try:
                    results_to_export = [
                        ("Raw Measures", self.RawMeasures),
                        ("Measure Validation results", self.MeasureValidationResults)
                    ]
                    if lakehouse_config is None:
                        export_validation_results(self, results_to_export)
                    else:
                        export_validation_results(self, results_to_export, lakehouse_config)
                    logger.info("Measure validation results exported successfully.")
                except Exception:
                    logger.error("Export failed during measure validation.", exc_info=True)
        except Exception as e:
            logger.error(f"Error in measure validation: {str(e)}")
            self.MeasureValidationResults = self.RawMeasures = pd.DataFrame()

    def run_relationship_validation(self, export: bool = False, lakehouse_config: dict = None):
        """
        Runs relationship validation between tables.

        Args:
            export (bool, optional): If True, exports validation results to a lakehouse or external storage. Defaults to False.
            lakehouse_config (dict, optional): Configuration dictionary for exporting data to the lakehouse. 
                                               Should contain keys like 'workspace_id' and 'lakehouse_id'.
        """
        if self.model_new.relationships is None or self.model_new.relationships.empty or self.model_old.relationships is None or self.model_old.relationships.empty:
            logger.warning("Relationship validation skipped: Relationships could not be fetched from one of the models.")
            return
    
        if self.common_tables is None or self.common_tables.empty:
            logger.warning("Relationship validation skipped: No common tables found. You may try decreasing the fuzzy match threshold.")
            return
        
        try:
            logger.info("Starting relationship validation...")
            start_time = time.time()
            self.relationship_validator = RelationshipValidator(self.model_new, self.model_old, self.common_columns, self.run_id, self.stream)
            self.RelationshipValidationResults = self.relationship_validator.validate_relationships()
            end_time = time.time()
            logger.info(f"Relationship validation completed in {end_time - start_time:.2f} seconds")
            
            if export:
                try:
                    results_to_export = [
                        ("Relationship Validation results", self.RelationshipValidationResults)
                    ]
                    if lakehouse_config is None:
                        export_validation_results(self, results_to_export)
                    else:
                        export_validation_results(self, results_to_export, lakehouse_config)
                    logger.info("Relationship validation results exported successfully.")
                except Exception:
                    logger.error("Export failed during relationship validation.", exc_info=True)
        except Exception as e:
            logger.error(f"Error in relationship validation: {str(e)}")
            self.RelationshipValidationResults = pd.DataFrame()

    def run_all_validations(self, margin_of_error: float = config.margin_of_error, export: bool = False, lakehouse_config: dict = None):
        """
        Runs all validation functions (table, column, measure, relationship).

        Args:
            margin_of_error (float, optional): Allowed percentage difference when comparing metrics. Defaults to 5.0.
            export (bool, optional): If True, exports validation results to a lakehouse or external storage. Defaults to False.
            lakehouse_config (dict, optional): Configuration dictionary for exporting data to the lakehouse. 
                                               Should contain keys like 'workspace_id' and 'lakehouse_id'.

        """
        logger.info("Starting all validations ...")
        start_time_parallel = time.time()
        threads = []

        # Creating a thread for each validation function
        table_thread = threading.Thread(target=self.run_table_validation, args=(margin_of_error,))
        column_thread = threading.Thread(target=self.run_column_validation, args=(margin_of_error,))
        measure_thread = threading.Thread(target=self.run_measure_validation, args=(margin_of_error,))
        relationship_thread = threading.Thread(target=self.run_relationship_validation)

        # Adding threads to a list
        threads.append(table_thread)
        threads.append(column_thread)
        threads.append(measure_thread)
        threads.append(relationship_thread)

        # Starting all threads
        for thread in threads:
            thread.start()

        # Waiting for all threads to complete
        for thread in threads:
            thread.join()
        end_time_parallel = time.time()
        logger.info(f"All validations completed in {end_time_parallel - start_time_parallel:.2f} seconds")
        
        results = [
            ("Measure Validation results",self.MeasureValidationResults),
            ("Table Validation results", self.TableValidationResults),
            ("Column Validation results", self.ColumnValidationResults),
            ("Relationship Validation results", self.RelationshipValidationResults)
        ]
        
        if export:
            try:
                results_to_export = [
                    ("Run Details", self.RunDetails),
                    ("Raw Measures", self.RawMeasures),
                    ("Measure Validation results",self.MeasureValidationResults),
                    ("Raw Tables", self.RawTables),
                    ("Table Validation results", self.TableValidationResults),
                    ("Column Validation results", self.ColumnValidationResults),
                    ("Relationship Validation results", self.RelationshipValidationResults)
                ]
                if lakehouse_config is None:
                    export_validation_results(self, results_to_export)
                else:
                    export_validation_results(self, results_to_export, lakehouse_config)
                logger.info("All validation results exported successfully.")
            except Exception as e:
                logger.error(f"Export failed: {str(e)}")
        
        return render_dataframe_tabs(results)
    
def ModelCompare(
        OldModel: str, 
        OldModelWorkspace: str, 
        NewModel: str, 
        NewModelWorkspace: str,
        Stream : str|None = None, 
        ExplicitToken: str|None = None,
        Threshold: float = config.threshold,
    ) -> ModelComparison:
    """
    Compare two models across workspaces.

    Args:
       'old_model' (str): Name of the old model.
       'old_model_workspace' (str): Workspace Name of the old model.
       'new_model' (str): Name of the new model.
       'new_model_workspace' (str): Workspace Name of the new model.
        Stream (str): A label or stream name used for tagging the comparison run.
        ExplicitToken (optional): A token to use for authentication. If None, a default token provider is used.
        Threshold (optional): A fuzzy matching threshold that determines when name comparisons between entities are considered a match.
    Returns:
        ModelComparison Object: This can be futher used to run data validations.
    """    
    if ExplicitToken:
        sfabric._token_provider._get_token = UserCredAuth(ExplicitToken) # type: ignore
    
    Stream = Stream or f"{OldModel}@{OldModelWorkspace}__{NewModel}@{NewModelWorkspace}"
    old_model = FabricAnalyticsModel(OldModel,OldModelWorkspace)
    new_model = FabricAnalyticsModel(NewModel,NewModelWorkspace)

    Compare = ModelComparison(model_new = new_model, model_old= old_model, stream=Stream,threshold_score=Threshold)
    return Compare