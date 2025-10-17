import pandas as pd
from thefuzz import fuzz, process
import logging 
logger = logging.getLogger(__name__)

class BaseComparer:
    def __init__(self, new_df : pd.DataFrame, old_df : pd.DataFrame, threshold_score : float):
        self.new_df = new_df.copy()
        self.old_df = old_df.copy()
        self.threshold_score = threshold_score

    def _fuzzy_match(self, new_items: pd.DataFrame, old_items: pd.DataFrame, match_col: str) -> pd.DataFrame:
        """
        Performs a more efficient fuzzy match of new_items to old_items on a given column.
        
        Args:
            new_items (pd.DataFrame): DataFrame of new items to be matched.
            old_items (pd.DataFrame): DataFrame of old items to be matched against.
            match_col (str): The column name to perform the fuzzy match on.

        Returns:
            pd.DataFrame: A DataFrame with matched new and old items, plus any unmatched items.
        """
        matched_results = []
        
        # Create a temporary index for old_items to easily reference them
        old_items_indexed = old_items.reset_index(drop=True).copy()
        old_choices_list = old_items_indexed[match_col].astype(str).tolist()
        
        # Keep track of which old_items have been matched
        # Using a set of indices for efficient lookup
        matched_old_indices = set() 
        
        # Store all potential matches above threshold, then sort
        all_potential_matches = [] # (new_item_row, old_item_index, score)

        for new_idx, new_row in new_items.iterrows():
            query_string = str(new_row[match_col])
            
            # Use process.extract to get ALL matches above the score_cutoff
            # This returns a list of (match_string, score, index_in_choices_list)
            results = process.extractOne(
                query=query_string,
                choices=old_choices_list,
                scorer=fuzz.ratio, 
                score_cutoff=round(self.threshold_score)
            )
            if results is None:
                continue

            if len(results) == 3:
                match_str, score, old_list_idx  =results
            else:
                match_str, score = results
                old_list_idx = old_choices_list.index(match_str)

            all_potential_matches.append({
                    'new_idx': new_idx,
                    'old_list_idx': old_list_idx,
                    'score': score
                })

        # Sort potential matches by score in descending order
        # This ensures we prioritize the best possible match globally
        all_potential_matches.sort(key=lambda x: x['score'], reverse=True)

        matched_new_indices = set()

        for match_info in all_potential_matches:
            new_idx = match_info['new_idx']
            old_list_idx = match_info['old_list_idx']
            score = match_info['score']

            # If both the new item and the old item haven't been matched yet
            if new_idx not in matched_new_indices and old_list_idx not in matched_old_indices:
                new_row = new_items.loc[new_idx]
                old_row = old_items_indexed.loc[old_list_idx]
                
                combined = {f"{col}_new": new_row[col] for col in new_items.columns}
                combined.update({f"{col}_old": old_row[col] for col in old_items.columns})
                combined["best_score"] = score
                combined["origin"] = "both"
                matched_results.append(combined)
                
                matched_new_indices.add(new_idx)
                matched_old_indices.add(old_list_idx)
        
        # Add unmatched new items
        for new_idx, new_row in new_items.iterrows():
            if new_idx not in matched_new_indices:
                combined = {f"{col}_new": new_row[col] for col in new_items.columns}
                combined.update({f"{col}_old": None for col in old_items.columns}) # Use old_items.columns for consistent column names
                combined["best_score"] = 0
                combined["origin"] = "new"
                matched_results.append(combined)
                
        # Add unmatched old items
        for old_list_idx, old_row in old_items_indexed.iterrows():
            if old_list_idx not in matched_old_indices:
                combined = {f"{col}_new": None for col in new_items.columns} # Use new_items.columns for consistent column names
                combined.update({f"{col}_old": old_row[col] for col in old_items.columns})
                combined["best_score"] = 0 # type: ignore
                combined["origin"] = "old" # type: ignore
                matched_results.append(combined)

        result_df = pd.DataFrame(matched_results)
        if result_df.empty:
            logger.warning("No matching entries were found.")
        return result_df

class TableComparer(BaseComparer):
    def compare(self) -> pd.DataFrame:
        try:
            return self._fuzzy_match(self.new_df, self.old_df, 'table_name')
        except Exception as e:
            logger.error(f"Error in table name comparison: {str(e)}")
            self.TableValidationResults = self.RunDetails = self.RawTables = pd.DataFrame()
            return pd.DataFrame()
        
class MeasureComparer(BaseComparer):
    def compare(self) -> pd.DataFrame:
        try:
            return self._fuzzy_match(self.new_df, self.old_df, 'field_name')
        except Exception as e:
            logger.error(f"Error in measure name comparison: {str(e)}")
            return pd.DataFrame()

class ColumnComparer(BaseComparer):
    def __init__(self, 
                 new_df : pd.DataFrame, 
                 old_df : pd.DataFrame, 
                 matched_tables_both : pd.DataFrame, 
                 threshold_score : float
        ):
        super().__init__(new_df, old_df, threshold_score)
        self.matched_tables_both = matched_tables_both

    def compare(self) -> pd.DataFrame:
        all_matched_columns = []
        
        matched_tables_both = self.matched_tables_both.copy()
        
        for _, table_row in matched_tables_both.iterrows():
            new_table_name = table_row['table_name_new']
            old_table_name = table_row['table_name_old']
            
            new_cols = self.new_df[self.new_df['table_name'] == new_table_name]
            old_cols = self.old_df[self.old_df['table_name'] == old_table_name]
            
            matched_columns = self._fuzzy_match(new_cols, old_cols, 'field_name')
            matched_columns[matched_columns['origin'] == 'both'] 
            all_matched_columns.append(matched_columns)
            
        if not all_matched_columns:
            return pd.DataFrame()

        return pd.concat(all_matched_columns, ignore_index=True)
    
