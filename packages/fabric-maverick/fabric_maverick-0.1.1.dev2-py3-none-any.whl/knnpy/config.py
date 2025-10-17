class ValidationConfig:
    """Configuration class for all validation settings in fabric_maverick.
    
    Attributes:
        threshold (float): Similarity threshold for fuzzy matching (0-100)
        margin_of_error (float): Margin of error for numeric comparisons
        max_workers (int): Maximum number of worker threads
        distinct_value_limit (int): Maximum distinct values to compare
        lakehouse_id (str): Default lakehouse ID for exports
        workspace_id (str): Default workspace ID for exports
    """
    def __init__(self):
        # Default values
        self._threshold = 80.0               # Fuzzy matching threshold
        self._margin_of_error = 5.0          # Default margin of error for numeric comparisons
        self._max_workers = 20               # Max threads for parallel processing
        self._distinct_value_limit = 50      # Limit for distinct value comparison in columns
        self._lakehouse_id = None            # Default lakehouse ID
        self._workspace_id = None            # Default workspace ID

    @property
    def threshold(self) -> float:
        """Similarity threshold for fuzzy matching (0-100)."""
        return self._threshold

    @threshold.setter
    def threshold(self, value: float):
        if not isinstance(value, (int, float)) or not 0 <= value <= 100:
            raise ValueError("Threshold must be a number between 0 and 100")
        self._threshold = float(value)

    @property
    def margin_of_error(self) -> float:
        """Margin of error for numeric comparisons (percentage)."""
        return self._margin_of_error

    @margin_of_error.setter
    def margin_of_error(self, value: float):
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("Margin of error must be a positive number")
        self._margin_of_error = float(value)

    @property
    def max_workers(self) -> int:
        """Maximum number of worker threads for parallel processing."""
        return self._max_workers

    @max_workers.setter
    def max_workers(self, value: int):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Max workers must be a positive integer")
        self._max_workers = value

    @property
    def distinct_value_limit(self) -> int:
        """Maximum number of distinct values to compare in column validation."""
        return self._distinct_value_limit

    @distinct_value_limit.setter
    def distinct_value_limit(self, value: int):
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Distinct value limit must be a positive integer")
        self._distinct_value_limit = value
        
    @property
    def lakehouse_id(self) -> str:
        """Default lakehouse ID for exports."""
        return self._lakehouse_id

    @lakehouse_id.setter
    def lakehouse_id(self, value: str):
        if value is not None and not isinstance(value, str):
            raise ValueError("Lakehouse ID must be a string or None")
        self._lakehouse_id = value

    @property
    def workspace_id(self) -> str:
        """Default workspace ID for exports."""
        return self._workspace_id

    @workspace_id.setter
    def workspace_id(self, value: str):
        if value is not None and not isinstance(value, str):
            raise ValueError("Workspace ID must be a string or None")
        self._workspace_id = value

    def get_lakehouse_config(self) -> dict:
        """Get the current lakehouse configuration as a dictionary."""
        if self._lakehouse_id and self._workspace_id:
            return {
                "lakehouse_id": self._lakehouse_id,
                "workspace_id": self._workspace_id
            }
        return None

    def set_lakehouse_config(self, lakehouse_id: str, workspace_id: str):
        """Set lakehouse configuration in one call."""
        self.lakehouse_id = lakehouse_id
        self.workspace_id = workspace_id

# Create a global instance
config = ValidationConfig()