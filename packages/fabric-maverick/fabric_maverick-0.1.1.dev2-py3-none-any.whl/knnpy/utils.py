from typing import List, Tuple
import pandas as pd
from IPython.display import HTML, display
from notebookutils import mssparkutils
from .config import config
from pyspark.sql import SparkSession
import logging 
logger = logging.getLogger(__name__)

def get_run_details(comparison_obj):
    """
    Generates a summary DataFrame about the comparison run.
    """
    try:
        data = {
            "run_id": [comparison_obj.run_id],
            "Stream": [comparison_obj.stream],
            "new_model_workspace": [f"{comparison_obj.model_new.model_name}_workspace_{comparison_obj.model_new.workspace_name}"],
            "old_model_workspace": [f"{comparison_obj.model_old.model_name}_workspace_{comparison_obj.model_old.workspace_name}"],
            "new_model_refresh_date": [str(comparison_obj.model_new.last_modified_date)],
            "old_model_refresh_date": [str(comparison_obj.model_old.last_modified_date)]
        }
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error generating run details: {e}")
        return pd.DataFrame()

def get_raw_table_details(comparison_obj):
    """
    Returns all table comparison details with a run ID.
    """
    try:
        df = comparison_obj._all_tables.copy()
        df["run_id"] = comparison_obj.run_id
        return df
    except Exception as e:
        print(f"Error retrieving raw table details: {e}")
        return pd.DataFrame()

def get_raw_measure_details(comparison_obj):
    """
    Returns all measure comparison details with a run ID.
    """
    try:
        df = comparison_obj._all_measures.copy()
        df["run_id"] = comparison_obj.run_id
        return df
    except Exception as e:
        print(f"Error retrieving raw measure details: {e}")
        return pd.DataFrame()

def render_dataframe_tabs(df_list: List[Tuple[str, pd.DataFrame]]) -> HTML:
    """
    Render multiple DataFrames as scrollable tabs in Fabric notebook.
    Adds green/red dot icons in 'is_value_similar' column.

    Parameters:
    - df_list: List of (title, DataFrame) tuples

    Returns:
    - HTML display or raw string
    """
    style = """
    <style>
        .tab { overflow: hidden; border: 1px solid #ccc; background-color: #f1f1f1; }
        .tab button { background-color: inherit; float: left; border: none; outline: none;
                      cursor: pointer; padding: 10px 14px; transition: 0.3s; }
        .tab button:hover { background-color: #ddd; }
        .tab button.active { background-color: #ccc; }
        .tabcontent { display: none; border: 1px solid #ccc; border-top: none;
                      padding: 10px; overflow: auto; max-height: 500px; }
        .tabcontent.active { display: block; }
        table { border-collapse: collapse; width: 100%; }
        th, td { text-align: center; padding: 8px; border: 1px solid #ddd; }
    </style>
    """

    script = """
    <script>
    function openTab(evt, tabName) {
        var i, tabcontent, tablinks;
        tabcontent = document.getElementsByClassName("tabcontent");
        for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
        }
        tablinks = document.getElementsByClassName("tablinks");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }
        document.getElementById(tabName).style.display = "block";
        evt.currentTarget.className += " active";
    }
    </script>
    """

    tab_buttons = '<div class="tab">'
    tab_contents = ''

    greenSymbol = '🟢'
    redSymbol = '🔴'

    for i, (title, df) in enumerate(df_list):
        tab_id = f"tab{i}"
        active_class = "active" if i == 0 else ""
        df = df.copy()

        if title == "Measure Validation results":
            df['Pass_Fail'] = df.apply(
                lambda row: greenSymbol if row['is_value_similar'] and row['is_data_type_same'] and row['is_expression_same'] else redSymbol,
                axis=1
            )
        elif title == "Table Validation results":
            df['Pass_Fail'] = df['is_value_similar'].apply(lambda x: greenSymbol if x else redSymbol)

        elif title == "Column Validation results":
            df['Pass_Fail'] = df.apply(
                lambda row: greenSymbol if row['is_value_similar'] and row['is_data_type_same'] else redSymbol,
                axis=1
            )
        elif title == "Relationship Validation results":
            df['Pass_Fail'] = df.apply(
                lambda row: greenSymbol if row['is_cross_filtering_behavior_match'] and row['is_active_status_match'] and row['is_multiplicity_match'] and row['data_type_match'] and row['is_column_name_exactly_matched'] else redSymbol,
                axis=1
            )

        tab_buttons += f'<button class="tablinks {active_class}" onclick="openTab(event, \'{tab_id}\')">{title}</button>'
        df_html = df.to_html(escape=False, index=False)
        tab_contents += f'<div id="{tab_id}" class="tabcontent {active_class}">{df_html}</div>'
        
    tab_buttons += '</div>'
    html = style + tab_buttons + tab_contents + script
    return display(HTML(html))

def export_validation_results(comparison_obj=None, results: List[Tuple[str, pd.DataFrame]] = None, lakehouse_config: dict = config.get_lakehouse_config()):
    """
    Exports validation results to a specified location (e.g., lakehouse).

    Args:
        comparison_obj (ModelComparison, optional): The ModelComparison object to extract results from.
        results (List[Tuple[str, pd.DataFrame]], optional): The validation results to export. 
                                                           If None and comparison_obj provided, will extract all available results.
        lakehouse_config (dict, optional): Configuration for lakehouse export.
    """
    # If no results provided, try to extract from comparison_obj
    if results is None:
        if comparison_obj is None:
            logger.warning("No results or comparison object provided for export. Please provide either results or a ModelComparison object.")
            return
        
        # Extract all available results from comparison_obj
        results = []
        
        # Add Run Details
        if hasattr(comparison_obj, 'RunDetails') and comparison_obj.RunDetails is not None:
            results.append(("Run Details", comparison_obj.RunDetails))
        
        # Add Raw Tables
        if hasattr(comparison_obj, 'RawTables') and comparison_obj.RawTables is not None:
            results.append(("Raw Tables", comparison_obj.RawTables))
            
        # Add Raw Measures
        if hasattr(comparison_obj, 'RawMeasures') and comparison_obj.RawMeasures is not None:
            results.append(("Raw Measures", comparison_obj.RawMeasures))
            
        # Add Table Validation Results
        if hasattr(comparison_obj, 'TableValidationResults') and comparison_obj.TableValidationResults is not None:
            results.append(("Table Validation results", comparison_obj.TableValidationResults))
            
        # Add Column Validation Results
        if hasattr(comparison_obj, 'ColumnValidationResults') and comparison_obj.ColumnValidationResults is not None:
            results.append(("Column Validation results", comparison_obj.ColumnValidationResults))
            
        # Add Measure Validation Results
        if hasattr(comparison_obj, 'MeasureValidationResults') and comparison_obj.MeasureValidationResults is not None:
            results.append(("Measure Validation results", comparison_obj.MeasureValidationResults))
            
        # Add Relationship Validation Results
        if hasattr(comparison_obj, 'RelationshipValidationResults') and comparison_obj.RelationshipValidationResults is not None:
            results.append(("Relationship Validation results", comparison_obj.RelationshipValidationResults))
        
        if not results:
            logger.warning("No validation results found in the comparison object. Please run validations first.")
            return
            
        logger.info(f"Extracted {len(results)} result sets from comparison object for export.")
    try:
        logger.info("Starting export process...")
        spark = SparkSession.builder.getOrCreate()

        # Get lakehouse configuration
        if lakehouse_config and "lakehouse_id" in lakehouse_config and "workspace_id" in lakehouse_config:
            lakehouse_id = lakehouse_config["lakehouse_id"]
            workspace_id = lakehouse_config["workspace_id"]
            print(f"Exporting using provided lakehouse_config: workspace_id={workspace_id}, lakehouse_id={lakehouse_id}")
        else:
            try:
                mounts = mssparkutils.fs.mounts()
                default_mount = next((m for m in mounts if m.mountPoint == "/default"), None)
                if not default_mount:
                    logger.error("Export requested but no lakehouse_config provided and no attached Lakehouse found.")
                    return 
                # Use the full mount source path directly
                base_lakehouse_path = default_mount.source
                print(f"Exporting using attached Lakehouse: source={default_mount.source}")
            except Exception as e:
                logger.error(f"Error while accessing attached Lakehouse mounts: {e}")
                return  # Exit early on error

        # Write each result to Lakehouse as managed tables
        for name, result in results:
            try:
                logger.info(f"Exporting result: {name}")
                df = pd.DataFrame(result)
                
                # Handle data type issues before creating Spark DataFrame
                # Convert boolean columns to string to avoid Spark type inference issues
                for col in df.columns:
                    if df[col].dtype == 'bool':
                        df[col] = df[col].astype(str)
                    # Convert numpy bool_ to regular bool then to string
                    elif df[col].dtype.name == 'bool_':
                        df[col] = df[col].astype(bool).astype(str)
                
                # Replace 'NA' with None BEFORE creating Spark DataFrame
                df.replace('NA', None, inplace=True)
                df.replace('nan', None, inplace=True)
                df.replace('NaN', None, inplace=True)
                
                # Convert mixed numeric columns to string to avoid type merge issues
                for col in df.columns:
                    if df[col].dtype == 'object':
                        # Check if column contains mixed numeric types
                        sample_vals = df[col].dropna().head(10)
                        if len(sample_vals) > 0:
                            has_int = any(isinstance(x, (int, float)) and float(x).is_integer() for x in sample_vals if x is not None)
                            has_float = any(isinstance(x, (int, float)) and not float(x).is_integer() for x in sample_vals if x is not None)
                            if has_int and has_float:
                                df[col] = df[col].astype(str)
                
                spark_df = spark.createDataFrame(df)
                table_name = name.replace(" ", "_").lower()
                
                # Create temporary table first
                temp_table_name = f"temp_{table_name}"
                spark_df.createOrReplaceTempView(temp_table_name)
                
                # Define the lakehouse path for the table using the appropriate base path
                if lakehouse_config and "lakehouse_id" in lakehouse_config and "workspace_id" in lakehouse_config:
                    # Use constructed path from lakehouse config
                    path = f"abfss://{workspace_id}@msit-onelake.dfs.fabric.microsoft.com/{lakehouse_id}/Tables/FabricMaverick/{table_name}"
                else:
                    # Use full mount source path directly
                    path = f"{base_lakehouse_path}/Tables/FabricMaverick/{table_name}"
                
                # Save the temporary table to the lakehouse path
                spark.table(temp_table_name).write.mode("overwrite").format("delta").option("mergeSchema", "true").save(path)
                
                print(f"Successfully exported '{name}' to table: FabricMaverick.{table_name}")
            except Exception as e:
                logger.error(f"Failed to export '{name}': {e}")
        # return render_dataframe_tabs(results)
    except Exception as e:
        logger.error(f"Unexpected error occurred during export process: {e}")