import pandas as pd
import numpy as np
import sempy.fabric as sfabric
from thefuzz import fuzz
from .report import FabricAnalyticsModel
from .config import config
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
logger = logging.getLogger(__name__)

class BaseValidator:
    def __init__(
            self, 
            model_new: FabricAnalyticsModel, 
            model_old: FabricAnalyticsModel, 
            all_items: pd.DataFrame, 
            run_id: str, 
            stream: str
        ):
        self.model_new = model_new
        self.model_old = model_old
        self.all_items = all_items
        self.run_id = run_id
        self.stream = stream

    def _validate_value(self, new_val, old_val, margin_of_error=config.margin_of_error) -> bool:
        if pd.isna(new_val) or pd.isna(old_val):
            return False 
        
        # Case 1: Fuzzy match if both values are strings
        if isinstance(new_val, str) and isinstance(old_val, str):
            # similarity_score = fuzz.ratio(new_val.strip(), old_val.strip())
            # return similarity_score >= 100 - margin_of_error
            return new_val.strip() == old_val.strip()

        # Case 2: Numeric comparison if both values are numbers
        try:
            new_val_float = float(new_val)
            old_val_float = float(old_val)
            lower_bound = old_val_float * (1 - margin_of_error / 100)
            upper_bound = old_val_float * (1 + margin_of_error / 100)
            return lower_bound <= new_val_float <= upper_bound
        except (ValueError, TypeError):
            return False  # Incompatible types for numeric comparison
    
class MeasureValidator(BaseValidator):

    def get_measure_values( self, dataset, workspace, measurelist, max_workers=config.max_workers):
        """
            Evaluates a list of measures in batches using parallel processing.

            Args:
                self: The instance of the class the function belongs to (if any).
                dataset: The dataset to evaluate against.
                workspace: The workspace to use.
                measurelist: A list of measures to evaluate.
                max_workers

            Returns:
                A pandas DataFrame with a single row, where columns are measures and values are their evaluations.
        """

        def evaluate(measure):
            try:
                df_eval = sfabric.evaluate_measure(
                    dataset=dataset,
                    workspace=workspace,
                    measure=measure
                )
                value = df_eval.iloc[0, 0] if not df_eval.empty else None
                return measure, value
            except Exception as e:
                logger.warning(f"Failed to evaluate measure '{measure}': {e}", exc_info=True)
                return measure, None

        
        try : 
            return sfabric.evaluate_measure(
                dataset=self.model_new.datasetid,
                workspace=self.model_new.workspaceid,
                measure=measurelist)
        except Exception as e:
            logger.warning('Could not retrive all measures in a go, trying one by one will take time', exc_info=True)
            pass

        if not isinstance(max_workers, int) or max_workers <= 0:
            raise ValueError(f"max_workers must be a positive integer. Got: {max_workers}")
        
        result = {}

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(evaluate, measure): measure for measure in measurelist}
                for future in as_completed(futures):
                    measure, value = future.result()
                    result[measure] = value
        except Exception as e:
            logger.error(f"Failed during threaded measure evaluation: {e}")
            return pd.DataFrame()

        return pd.DataFrame([result])

    def validate_measure_values(self, margin_of_error=config.margin_of_error):

        matched_measures = self.all_items[
            (self.all_items['origin'] == 'both') &
            (self.all_items['data_type_new'].str.strip().str.lower() != 'variant') &
            (self.all_items['data_type_old'].str.strip().str.lower() != 'variant')
        ][[
            'table_name_new',
            'field_name_new',
            'field_name_old',
            'data_type_new',
            'data_type_old',
            'expression_old',
            'expression_new',
            'origin',
            'best_score'
        ]].dropna(subset=['field_name_new', 'field_name_old'])

        if matched_measures.empty:
            return pd.DataFrame()

        try:
            new_eval = self.get_measure_values(
                dataset=self.model_new.datasetid,
                workspace=self.model_new.workspaceid,
                measurelist=list(matched_measures['field_name_new'])
            )
            old_eval = self.get_measure_values(
                dataset=self.model_old.datasetid,
                workspace=self.model_old.workspaceid,
                measurelist=list(matched_measures['field_name_old'])
            )
            new_eval_pivot = new_eval.melt(var_name='field_name_new', value_name='new_model_value')
            old_eval_pivot = old_eval.melt(var_name='field_name_old', value_name='old_model_value')

            merged = pd.merge(matched_measures, new_eval_pivot, on='field_name_new', how='left')
            merged = pd.merge(merged, old_eval_pivot, on='field_name_old', how='left')

            merged['new_val_numeric'] = pd.to_numeric(merged['new_model_value'], errors='coerce')
            merged['old_val_numeric'] = pd.to_numeric(merged['old_model_value'], errors='coerce')
            
            merged['value_difference'] = merged['new_val_numeric'] - merged['old_val_numeric']
            merged['value_difference_percent'] = np.where(
                (merged['old_val_numeric'] == 0) |
                (merged['old_val_numeric'].isna()) |
                (merged['new_val_numeric'].isna()),
                '<NA>',
                (((merged['new_val_numeric'] - merged['old_val_numeric']) * 100) / merged['old_val_numeric'])
                .round(2).astype(str) + '%'
            )
            merged.loc[(merged['value_difference'] == 0) & (merged['value_difference_percent'] == '<NA>'),'value_difference_percent'] = '0.0%'
            merged['is_value_similar'] = merged.apply(
                lambda row: self._validate_value(row['new_model_value'], row['old_model_value'], margin_of_error), axis=1
            )
            merged['is_data_type_same'] = merged['data_type_new'] == merged['data_type_old']
            merged['is_expression_same'] = merged['expression_new'] == merged['expression_old']
            merged['run_id'] = self.run_id
            merged['Stream'] = self.stream

            final_cols = [
                'run_id',
                'Stream',
                'table_name_new',
                'field_name_new',
                'field_name_old',
                'best_score',
                'origin',
                'new_model_value',
                'old_model_value',
                'value_difference', 
                'value_difference_percent',
                'is_value_similar', 
                'is_data_type_same', 
                'is_expression_same'
            ]
            return merged[final_cols]
        except Exception as e:
            print(f"Error in measure validation: {e}")
            return pd.DataFrame()

class TableValidator(BaseValidator):

    def _get_table_row_count(self, model, table_name) -> int:
        query = f'EVALUATE ROW("RowCount", COUNTROWS(\'{table_name}\'))'
        try:
            df = sfabric.evaluate_dax(dataset=model.datasetid, workspace=model.workspaceid, dax_string=query)
            colname = df.columns[0]
            value = df[colname].iloc[0]
            return 0 if pd.isna(value) else int(value)
        except Exception as e:
            logger.error(f"Error fetching row count for table : {e}")
            return -1

    def validate_row_counts(self, margin_of_error=config.margin_of_error) -> pd.DataFrame:
        results = []
        matched_tables = self.all_items

        for _, row in matched_tables.iterrows():
            table_new = row['table_name_new']
            table_old = row['table_name_old']

            count_new = self._get_table_row_count(self.model_new, table_new)
            count_old = self._get_table_row_count(self.model_old, table_old)
            
            diff = count_new - count_old
            diff_pct = f"{((diff) / count_old * 100):.2f}%" if count_old != 0 else "∞%"
            is_value_similar = self._validate_value(count_new, count_old, margin_of_error)
            results.append({
                'run_id': self.run_id,
                'Stream': self.stream,
                'table_name_new': table_new,
                'table_name_old': table_old,
                'best_score': row['best_score'],
                'origin': 'both',
                'row_count_new': count_new,
                'row_count_old': count_old,
                'row_count_difference': diff,
                'row_count_diff_percentage': diff_pct,
                'is_value_similar': is_value_similar
            })
        
        return pd.DataFrame(results)

class ColumnValidator(BaseValidator):

    def _read_table(self,table_name) -> None:
        self._new_tables_data = {}
        try:
            self._new_tables_data[table_name] = sfabric.read_table(
                dataset=self.model_new.datasetid,
                workspace=self.model_new.workspaceid,
                table=table_name
            )
        except Exception as e:
            logger.warning(f"Error reading new table '{table_name}': {e}")
            self._new_tables_data[table_name] = pd.DataFrame()

    def _generate_distinct_count_dax(self,columns: list[str],table_name) -> str:
        rows = []
        for col in columns:
            row = f'ROW("ColumnName", "{col}", "DistinctCount", COUNTROWS(VALUES(\'{table_name}\'[{col}])))'
            rows.append(row)

        if not rows:
            return ""

        if len(rows) == 1:
            return f"EVALUATE\n{rows[0]}"
        else:
            return  "EVALUATE\nUNION(\n    " + ",\n    ".join(rows) + "\n)"

    def _get_column_distinct_counts(self, table_name: str, columns: list[str], model: FabricAnalyticsModel) -> pd.DataFrame | None:
        """
        Executes a DAX query to fetch distinct counts for the given columns and table.
        """
        if not columns:
            logging.warning(f"No columns provided for table '{table_name}' in dataset {model.datasetid}.")
            return None
            
        dax_query = self._generate_distinct_count_dax(columns=columns, table_name=table_name)
        if dax_query is None:
            return None
            
        try:
            df = sfabric.evaluate_dax(
                dataset=model.datasetid,
                workspace=model.workspaceid,
                dax_string=dax_query
            )
            df.columns = ["ColumnName", "DistinctCount"]
            if(len(df) == 0):
                logging.warning(f"No row count returned for columns in table '{table_name}'")
            return df
        except Exception as e:
            logging.error(f"Error fetching distinct row count for columns in table '{table_name}': {e}")
            return None
    
    def __get_distinct_values_dax(self, model: FabricAnalyticsModel, table: str, column: str) -> set:
        try:
            dax = f"""
            EVALUATE 
            SELECTCOLUMNS(
                VALUES('{table}'[{column}]),
                "Value", '{table}'[{column}]
            )
            """
            df = sfabric.evaluate_dax(dataset=model.datasetid, workspace=model.workspaceid, dax_string=dax)
            return set(df["[Value]"].dropna().unique()) if "[Value]" in df.columns else set()
        except Exception as e:
            logger.warning(f"DAX DISTINCT values failed for {table}.{column}: {e}")
            return set()

    def validate_distinct_counts(self, margin_of_error: float = config.margin_of_error) -> pd.DataFrame:
        """
        Validates the distinct count of values for all common columns across all common tables.

        Args:
            margin_of_error (float): The allowed percentage difference between old and new counts.

        Returns:
            pd.DataFrame: A dataframe containing the validation results for each column,
                          including new/old counts and whether the validation passed.
        """
        validation_results = []
        
        # Find common tables based on the mapping in all_items
        common_tables = self.all_items[['table_name_new', 'table_name_old']].drop_duplicates()

        for _, row in common_tables.iterrows():
            table_name_new = row['table_name_new']
            table_name_old = row['table_name_old']

            logging.info(f"Validating distinct counts for table: '{table_name_new}' (new) vs '{table_name_old}' (old)")

            # Filter columns for the current table pair
            table_columns_map = self.all_items[
                (self.all_items['table_name_new'] == table_name_new) &
                (self.all_items['table_name_old'] == table_name_old)
            ]

            cols_new = table_columns_map['field_name_new'].unique().tolist()
            cols_old = table_columns_map['field_name_old'].unique().tolist()

            # Fetch distinct counts for both new and old models
            df_new = self._get_column_distinct_counts(table_name_new, cols_new, self.model_new)
            df_old = self._get_column_distinct_counts(table_name_old, cols_old, self.model_old)

            if df_new is None or df_old is None:
                logging.warning(f"Could not retrieve data for one or both tables: {table_name_new}, {table_name_old}. Skipping.")
                continue

            # Rename columns for merging
            df_new = df_new.rename(columns={"ColumnName": "field_name_new", "DistinctCount": "distinct_count_new"})
            df_old = df_old.rename(columns={"ColumnName": "field_name_old", "DistinctCount": "distinct_count_old"})
            
            # Merge results based on the column mapping
            merged_df = pd.merge(table_columns_map, df_new, on="field_name_new")
            merged_df = pd.merge(merged_df, df_old, on="field_name_old")

            # Perform validation for each column
            merged_df['is_value_similar'] = merged_df.apply(
                lambda r: self._validate_value(r['distinct_count_new'], r['distinct_count_old'], margin_of_error),
                axis=1
            )
            merged_df['value_difference'] = merged_df['distinct_count_new'] - merged_df['distinct_count_old']
            merged_df['value_difference_percent'] = np.where(
                (merged_df['distinct_count_new'] == 0) |
                (merged_df['distinct_count_new'].isna()) |
                (merged_df['distinct_count_old'].isna()),
                '<NA>',
                (((merged_df['distinct_count_old'] - merged_df['distinct_count_new']) * 100) / merged_df['distinct_count_new'])
                .round(2).astype(str) + '%'
            )
            merged_df.loc[(merged_df['value_difference'] == 0) & (merged_df['value_difference_percent'] == '<NA>'),'value_difference_percent'] = '0.0%'

            merged_df['is_data_type_same'] = merged_df['data_type_new'] == merged_df['data_type_old']
            enriched_rows = []

            for _, r in merged_df.iterrows():
                column_new = r['field_name_new']
                column_old = r['field_name_old']
                enriched = r.to_dict()
                try:
                    if(r['distinct_count_new'] > config.distinct_value_limit or r['distinct_count_old'] > config.distinct_value_limit):
                        enriched.update({
                            "new_values": None,
                            "missing_values": None,
                            "new_values_count": None,
                            "missing_value_count": None,
                            "distinct_value_diff": None,
                            "value_missing_present": None
                        })
                        enriched_rows.append(enriched)
                        continue

                    enriched_rows.append(enriched)
                    values_new = self.__get_distinct_values_dax(self.model_new, table_name_new, column_new)
                    values_old = self.__get_distinct_values_dax(self.model_old, table_name_old, column_old)
                    new_values = sorted(values_new - values_old)
                    missing_values = sorted(values_old - values_new)
                    new_values_str = [str(v) for v in new_values]
                    missing_values_str = [str(v) for v in missing_values]
                    new_values_count = len(new_values)
                    missing_value_count = len(missing_values)
                    distinct_value_diff = len(new_values) + len(missing_values)
                    value_missing_present = ', '.join([f"+{str(v)}" for v in new_values] + [f"-{str(v)}" for v in missing_values])
                    enriched.update({
                        "new_values": ', '.join(new_values_str),
                        "missing_values": ', '.join(missing_values_str),
                        "new_values_count": f"+{new_values_count}",
                        "missing_value_count": f"-{missing_value_count}",
                        "distinct_value_diff": distinct_value_diff,
                        "value_missing_present": value_missing_present
                    })
                    enriched_rows.append(enriched)
                except Exception as e:
                    logger.error(f"Error comparing values for {table_name_new}.{column_new}: {e}")
                    enriched.update({
                        "new_values": None,
                        "missing_values": None,
                        "new_values_count": None,
                        "missing_value_count": None,
                        "distinct_value_diff": None,
                        "value_missing_present": None
                    })
                    enriched_rows.append(enriched)
                    continue
            if enriched_rows:
                validation_results.append(pd.DataFrame(enriched_rows))
    
        if not validation_results:
            logger.warning("No common columns found for validation. Skipping column validation.")
            return pd.DataFrame()
         
        result_df = pd.concat(validation_results, ignore_index=True)
        result_df["run_id"] = self.run_id
        result_df["Stream"] = self.stream
        if validation_results:
            # Get BPA descriptions for both models
            bpa_new_df = self.__get_bpa_column_descriptions(self.model_new, "new")
            bpa_old_df = self.__get_bpa_column_descriptions(self.model_old, "old")

            if bpa_new_df is None or bpa_new_df.empty:
                logger.warning("BPA descriptions for new model are empty!! Column Validation Results will not have BPA descriptions for new model.")
            else:
                result_df = result_df.merge(
                    bpa_new_df,
                    on=["table_name_new", "field_name_new"],
                    how="left"
                )

            if bpa_old_df is None or bpa_old_df.empty:
                logger.warning("BPA descriptions for old model are empty!! Column Validation Results will not have BPA descriptions for old model.")
            else:
                result_df = result_df.merge(
                    bpa_old_df,
                    on=["table_name_old", "field_name_old"],
                    how="left"
                )
        
        cols = ["run_id", "Stream"] + [col for col in result_df.columns if col not in ["run_id", "Stream"]]
        result_df = result_df[cols]

        return result_df
    
    def __get_bpa_column_descriptions(self,model: FabricAnalyticsModel, model_label: str) -> pd.DataFrame:
        """
        Runs BPA on a Fabric model and returns cleaned column descriptions merged by Category.

        Args:
            model: A FabricAnalyticsModel object (e.g., self.model_old or self.model_new)
            model_label: str - "old" or "new"

        Returns:
            pd.DataFrame with table_name, field_name, and combined description by category.
        """
        try:

            bpa_df = sfabric.run_model_bpa(
                dataset=model.datasetid,
                workspace=model.workspaceid,
                export="none",
                return_dataframe=True
            )
            if bpa_df is None or bpa_df.empty:
                logging.warning(f"BPA output is empty for dataset {model.datasetid}")
                return pd.DataFrame()

            bpa_df = bpa_df[bpa_df['Object Type'].str.lower() == 'column']

            if 'Object Name' not in bpa_df.columns or 'Description' not in bpa_df.columns:
                logging.warning("Expected 'Object Name' and 'Description' columns in BPA output. But Not Found.")
                return pd.DataFrame()

            # Extract table and field names
            def extract_table_and_column(obj_name: str) -> tuple:
                table_match = re.search(r"'([^']+)'", obj_name)
                column_match = re.search(r"\[([^\]]+)\]", obj_name)
                table_name = table_match.group(1) if table_match else None
                field_name = column_match.group(1) if column_match else None
                return pd.Series([table_name, field_name])

            table_col_extract = bpa_df['Object Name'].apply(extract_table_and_column)
            table_col_extract.columns = [f'table_name_{model_label}', f'field_name_{model_label}']
            bpa_df = pd.concat([bpa_df.reset_index(drop=True), table_col_extract.reset_index(drop=True)], axis=1)

            # Only needed columns
            bpa_df = bpa_df[[
                f'table_name_{model_label}',
                f'field_name_{model_label}',
                'Category',
                'Object Name',
                'Rule Name',
                'Severity',
                'Description'
            ]]

            bpa_df['Category'] = bpa_df['Category'].fillna("Unknown")

            bpa_df['RuleIndexLetter'] = (
                bpa_df.groupby([f'table_name_{model_label}', f'field_name_{model_label}', 'Category'])
                    .cumcount()
                    .apply(lambda x: chr(97 + int(x)) if pd.notnull(x) and x >= 0 else None)
            ) #  group by this 3 column and give a,b,c,...
            ordered_categories = ['Performance', 'Maintenance', 'Formatting']

            category_mapping = {
                cat: str(idx + 1)
                for idx, cat in enumerate(ordered_categories)
                if cat in bpa_df['Category'].unique()
            }

            bpa_df['RuleIndexNumber'] = bpa_df['Category'].map(category_mapping)
            bpa_df['RuleIndex'] = bpa_df['RuleIndexNumber'] + '.' + bpa_df['RuleIndexLetter']
            bpa_df['FormattedDescription'] = bpa_df['RuleIndex'] + ' ' + bpa_df['Description']
            # Aggregate descriptions by column
            agg_df = bpa_df.groupby([
                f'table_name_{model_label}',
                f'field_name_{model_label}'
            ])['FormattedDescription'].apply(lambda x: "\n\n".join(f"• {str(i).strip()}" for i in x if pd.notnull(i))).reset_index()
            agg_df.rename(columns={'FormattedDescription': f'bpa_description_{model_label}'}, inplace=True)
            return agg_df

        except Exception as e:
            logging.exception(f"Error occurred in get_bpa_column_descriptions for model {model_label}: {e}")
            return pd.DataFrame()

class RelationshipValidator(BaseValidator):

    def validate_relationships(self) -> pd.DataFrame:
        """
        Checks if old relationships exist in new using fuzzy matched columns from self.common_columns,
        and compares data types between mapped columns.
        """
        old_relationships = self.model_old.relationships.copy()
        new_relationships = self.model_new.relationships.copy()

        if old_relationships is None or old_relationships.empty:
            logger.warning("No relationships found in old model. Validation cannot proceed.")
            return pd.DataFrame()
        if new_relationships is None or new_relationships.empty:
            logger.warning("No relationships found in new model. Validation cannot proceed.")
            return pd.DataFrame()
        results = []
        
        relevant_common_columns = self.all_items
        column_map = {
            (c['table_name_old'], c['field_name_old']): (c['table_name_new'], c['field_name_new'])
            for _, c in relevant_common_columns.iterrows()
        }

        reverse_column_map = {
            (c['table_name_new'], c['field_name_new']): (c['table_name_old'], c['field_name_old'])
            for _, c in relevant_common_columns.iterrows()
        }

        data_type_lookup = {
            (c['table_name_old'], c['field_name_old']): c['data_type_old']
            for _, c in relevant_common_columns.iterrows()
        }
        data_type_lookup_new = {
            (c['table_name_new'], c['field_name_new']): c['data_type_new']
            for _, c in relevant_common_columns.iterrows()
        }
        best_score_lookup ={
            (c['table_name_new'], c['field_name_new'], c['table_name_old'], c['field_name_old']): c['best_score']
            for _,c in relevant_common_columns.iterrows()
        }
        def relationship_exists(df, from_tbl, from_col, to_tbl, to_col):
            return df.apply(lambda r:
                ((r['from_table'], r['from_column'], r['to_table'], r['to_column']) == (from_tbl, from_col, to_tbl, to_col)) or
                ((r['from_table'], r['from_column'], r['to_table'], r['to_column']) == (to_tbl, to_col, from_tbl, from_col)),
                axis=1).any()

        def format_multiplicity(multi: str, behavior: str) -> str:
            multi = multi.replace("m", "*")
            if behavior == "BothDirections":
                return multi.replace(":", "<->")
            if multi == "*:*":
                return multi
            return multi.replace(":", "<-")

        for _, rel in old_relationships.iterrows():
            old_from = (rel['from_table'], rel['from_column'])
            old_to = (rel['to_table'], rel['to_column'])

            new_from = column_map.get(old_from)
            new_to = column_map.get(old_to)

            old_multiplicity = format_multiplicity(rel.get("multiplicity", "NA"), rel.get("cross_filtering_behavior", "NA"))
            old_is_active = rel.get("active", "NA")
            old_cross_filtering_behavior = rel.get("cross_filtering_behavior", "NA")
            old_arrow = "<->" if "<->" in old_multiplicity else "<-"
            old_dtype = f"{data_type_lookup.get(old_from, 'NA')} {old_arrow} {data_type_lookup.get(old_to, 'NA')}"
            if new_from and new_to:
                exists = relationship_exists(new_relationships, new_from[0], new_from[1], new_to[0], new_to[1])
                
                new_rel = new_relationships[
                    ((new_relationships['from_table'] == new_from[0]) & (new_relationships['from_column'] == new_from[1]) &
                    (new_relationships['to_table'] == new_to[0]) & (new_relationships['to_column'] == new_to[1])) |
                    ((new_relationships['from_table'] == new_to[0]) & (new_relationships['from_column'] == new_to[1]) &
                    (new_relationships['to_table'] == new_from[0]) & (new_relationships['to_column'] == new_from[1]))
                ]

                if not new_rel.empty:
                    new_rel = new_rel.iloc[0]
                    new_multiplicity = format_multiplicity(new_rel.get("multiplicity", "NA"), new_rel.get("cross_filtering_behavior", "NA"))
                    new_arrow = "<->" if "<->" in new_multiplicity else "<-"
                    new_is_active = new_rel.get("active", "NA")
                    new_cross_filtering_behavior = new_rel.get("cross_filtering_behavior", "NA")
                else:
                    new_multiplicity = "NA"
                    new_arrow = "NA"
                    new_is_active = "NA"
                    new_cross_filtering_behavior = "NA"
                    
                new_dtype = f"{data_type_lookup_new.get(new_from, 'NA')} {new_arrow} {data_type_lookup_new.get(new_to, 'NA')}"
                dtype_match = old_dtype == new_dtype
                if exists:
                    is_active_status_match = old_is_active == new_is_active
                    is_cross_filtering_behavior_match = old_cross_filtering_behavior == new_cross_filtering_behavior
                    is_multiplicity_match = old_multiplicity == new_multiplicity
                    best_score_right = best_score_lookup.get((new_to[0],new_to[1],old_to[0],old_to[1]),'NA')
                    best_score_left = best_score_lookup.get((new_from[0],new_from[1],old_from[0],old_from[1]),'NA')
                    is_column_name_exactly_matched = best_score_left ==  best_score_right == 100

                    results.append({
                        'old_relationship': f"'{old_from[0]}'[{old_from[1]}]  {old_arrow}  '{old_to[0]}'[{old_to[1]}]",
                        'mapped_new_relationship': f"'{new_from[0]}'[{new_from[1]}]  {new_arrow}  '{new_to[0]}'[{new_to[1]}]",
                        'old_data_type': old_dtype,
                        'new_data_type': new_dtype,
                        'data_type_match': dtype_match,
                        'old_multiplicity': old_multiplicity,
                        'new_multiplicity': new_multiplicity,
                        'is_multiplicity_match' : is_multiplicity_match,
                        'old_active': old_is_active,
                        'new_active': new_is_active,
                        'is_active_status_match': is_active_status_match,
                        'score': f"{best_score_left} : {best_score_right}", 
                        'is_column_name_exactly_matched': is_column_name_exactly_matched,
                        'old_cross_filtering_behavior': old_cross_filtering_behavior,
                        'new_cross_filtering_behavior': new_cross_filtering_behavior,
                        'is_cross_filtering_behavior_match': is_cross_filtering_behavior_match,
                        'origin': 'both'
                    })
                else:
                    old_dtype = f"{data_type_lookup.get(old_from, 'NA')} {old_arrow} {data_type_lookup.get(old_to, 'NA')}"
                    results.append({
                        'old_relationship': f"'{old_from[0]}'[{old_from[1]}]  {old_arrow}  '{old_to[0]}'[{old_to[1]}]",
                        'mapped_new_relationship': None,
                        'old_data_type': old_dtype,
                        'new_data_type': 'NA',
                        'data_type_match': False,
                        'old_multiplicity': old_multiplicity,
                        'new_multiplicity': 'NA',
                        'is_multiplicity_match' : False,
                        'old_active': old_is_active,
                        'new_active': 'NA',
                        'is_active_status_match': False,
                        'score': "NA", 
                        'is_column_name_exactly_matched': False,
                        'old_cross_filtering_behavior': old_cross_filtering_behavior,
                        'new_cross_filtering_behavior': 'NA',
                        'is_cross_filtering_behavior_match': False,
                        'origin': 'old'
                    })
            else:
                old_dtype = f"{data_type_lookup.get(old_from, 'NA')} {old_arrow} {data_type_lookup.get(old_to, 'NA')}"
                results.append({
                    'old_relationship': f"'{old_from[0]}'[{old_from[1]}] {old_arrow} '{old_to[0]}'[{old_to[1]}]",
                    'mapped_new_relationship': None,
                    'old_data_type': old_dtype,
                    'new_data_type': 'NA',
                    'data_type_match': False,
                    'old_multiplicity': old_multiplicity,
                    'new_multiplicity': 'NA',
                    'is_multiplicity_match' : False,
                    'old_active': old_is_active,
                    'new_active': 'NA',
                    'is_active_status_match': False,
                    'score': "NA", 
                    'is_column_name_exactly_matched': False,
                    'old_cross_filtering_behavior': old_cross_filtering_behavior,
                    'new_cross_filtering_behavior': 'NA',
                    'is_cross_filtering_behavior_match': False,
                    'origin': 'old'
                })

        for _, rel in new_relationships.iterrows():
            new_from = (rel['from_table'], rel['from_column'])
            new_to = (rel['to_table'], rel['to_column'])

            old_from = reverse_column_map.get(new_from)
            old_to = reverse_column_map.get(new_to)

            if not old_from or not old_to:
                new_multiplicity = format_multiplicity(rel.get("multiplicity", "NA"), rel.get("cross_filtering_behavior", "NA"))
                new_arrow = "<->" if "<->" in new_multiplicity else "<-"
                new_dtype = f"{data_type_lookup_new.get(new_from, 'NA')} {new_arrow} {data_type_lookup_new.get(new_to, 'NA')}"
                new_is_active = rel.get("active", "NA")
                new_cross_filtering_behavior = rel.get("cross_filtering_behavior", "NA")

                results.append({
                    'old_relationship': None,
                    'mapped_new_relationship': f"'{new_from[0]}'[{new_from[1]}] {new_arrow} '{new_to[0]}'[{new_to[1]}]",
                    'old_data_type': 'NA',
                    'new_data_type': new_dtype,
                    'data_type_match': False,
                    'old_multiplicity': 'NA',
                    'new_multiplicity': new_multiplicity,
                    'is_multiplicity_match' : False,
                    'old_active': 'NA',
                    'new_active': new_is_active,
                    'is_active_status_match': False,
                    'score': "NA", 
                    'is_column_name_exactly_matched': False,
                    'old_cross_filtering_behavior': 'NA',
                    'new_cross_filtering_behavior': new_cross_filtering_behavior,
                    'is_cross_filtering_behavior_match': False,
                    'origin': 'new'
                })

        df = pd.DataFrame(results)
        if df.empty:
            logger.warning("No relationships found for validation. Skipping relationship validation.")
            return pd.DataFrame()
        df["run_id"] = self.run_id
        df["Stream"] = self.stream
        # Reorder columns for better readability
        cols = ["run_id", "Stream"] + [col for col in df.columns if col not in ["run_id", "Stream"]]
        df = df[cols]
        return df
