import dask.dataframe as dd
import dask.delayed as delayed
import pandas as pd
from sfn_blueprint.utils.logging import setup_logger
from sfn_blueprint.agents.base_agent import SFNAgent
import os
from pathlib import Path
from typing import Union, Optional

class SFNDataLoader(SFNAgent):
    def __init__(self):
        super().__init__(name="Data Loader", role="Data Loading Specialist")
        self.logger, _ = setup_logger(logger_name="SFNDataLoader")

        # Mapping file extensions to their respective loaders
        self.loader_map = {
            'csv': self.load_csv,
            'xlsx': self.load_excel,
            'json': self.load_json,
            'parquet': self.load_parquet,
        }
        
        # Mapping file extensions to their respective savers
        self.saver_map = {
            'csv': self.save_csv,
            'xlsx': self.save_excel,
            'json': self.save_json,
            'parquet': self.save_parquet,
        }

    def execute_task(self, task) -> dd.DataFrame:
        file_path = task.path

        # Check if the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get the file extension
        file_extension = os.path.splitext(file_path)[-1][1:].lower()
        self.logger.info(f"Received file with extension: {file_extension}")

        if file_extension in self.loader_map:
            self.logger.info(f"Loading file using {file_extension.upper()} loader")
            try:
                return self.loader_map[file_extension](file_path)
            except Exception as e:
                self.logger.error(f"Error loading {file_extension.upper()} file: {e}")
                raise
        else:
            self.logger.error(f"Unsupported file format: {file_extension}")
            raise ValueError("Unsupported file format. Please provide a CSV, Excel, JSON, or Parquet file.")

    def save_data(self, data: Union[pd.DataFrame, dd.DataFrame], output_path: str, 
                  format: Optional[str] = None, **kwargs) -> str:
        """
        Save data to file in the specified format.
        
        Args:
            data: DataFrame to save (pandas or dask)
            output_path: Path where to save the file
            format: Output format (csv, xlsx, json, parquet). If None, inferred from file extension
            **kwargs: Additional arguments for the save method
            
        Returns:
            Path to the saved file
        """
        # Ensure output_path is a Path object
        output_path = Path(output_path)
        
        # Determine format from file extension if not specified
        if format is None:
            format = output_path.suffix[1:].lower()
        
        # Ensure the output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert dask DataFrame to pandas if needed
        if isinstance(data, dd.DataFrame):
            data = data.compute()
        
        # Save using appropriate method
        if format in self.saver_map:
            self.logger.info(f"Saving data to {format.upper()} file: {output_path}")
            return self.saver_map[format](data, output_path, **kwargs)
        else:
            raise ValueError(f"Unsupported output format: {format}")

    def load_csv(self, file_path):
        self.logger.info("Loading CSV file")
        dask_df = dd.read_csv(file_path, assume_missing=True)
        pandas_df = dask_df.compute()
        return pandas_df
    """ PANDAS function no DASK"""

    def load_excel(self, file_path):
        self.logger.info("Loading Excel file")
        # Dask doesn't support Excel natively, so fallback to pandas
        # Use dask.delayed to load the Excel file with pandas
        delayed_df = delayed(pd.read_excel)(file_path, index_col=0)

        # Convert delayed pandas DataFrame to Dask DataFrame
        dask_df = dd.from_delayed([delayed_df])
        # Compute the Dask DataFrame to get a pandas DataFrame
        pandas_df = dask_df.compute()
        return pandas_df

    def load_json(self, file_path):
        self.logger.info("Loading JSON file")
        pandas_df = pd.read_json(file_path)
        return pandas_df

    def load_parquet(self, file_path):
        self.logger.info("Loading Parquet file")
        dask_df = dd.read_parquet(file_path)
        pandas_df = dask_df.compute()
        return pandas_df

    def save_csv(self, data: pd.DataFrame, output_path: Path, **kwargs) -> str:
        """Save DataFrame to CSV file."""
        try:
            data.to_csv(output_path, index=False, **kwargs)
            self.logger.info(f"Data saved to CSV: {output_path}")
            return str(output_path)
        except Exception as e:
            self.logger.error(f"Error saving CSV: {e}")
            raise

    def save_excel(self, data: pd.DataFrame, output_path: Path, **kwargs) -> str:
        """Save DataFrame to Excel file."""
        try:
            data.to_excel(output_path, index=False, **kwargs)
            self.logger.info(f"Data saved to Excel: {output_path}")
            return str(output_path)
        except Exception as e:
            self.logger.error(f"Error saving Excel: {e}")
            raise

    def save_json(self, data: pd.DataFrame, output_path: Path, **kwargs) -> str:
        """Save DataFrame to JSON file."""
        try:
            # Set default orient if not provided
            if 'orient' not in kwargs:
                kwargs['orient'] = 'records'
            if 'indent' not in kwargs:
                kwargs['indent'] = 2
                
            data.to_json(output_path, **kwargs)
            self.logger.info(f"Data saved to JSON: {output_path}")
            return str(output_path)
        except Exception as e:
            self.logger.error(f"Error saving JSON: {e}")
            raise

    def save_parquet(self, data: pd.DataFrame, output_path: Path, **kwargs) -> str:
        """Save DataFrame to Parquet file."""
        try:
            data.to_parquet(output_path, index=False, **kwargs)
            self.logger.info(f"Data saved to Parquet: {output_path}")
            return str(output_path)
        except Exception as e:
            self.logger.error(f"Error saving Parquet: {e}")
            raise

    def get_supported_formats(self) -> dict:
        """Get supported input and output formats."""
        return {
            "input_formats": list(self.loader_map.keys()),
            "output_formats": list(self.saver_map.keys())
        }