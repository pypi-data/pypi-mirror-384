from sfn_blueprint.utils.logging import setup_logger
import pandas as pd

class SFNDataPostProcessor:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.logger, _ = setup_logger(logger_name="SFNDataPostProcessor")

    def view_data(self, num_rows: int = 5) -> pd.DataFrame:
        """Returns a preview of the modified data."""
        self.logger.info(f"Viewing first {num_rows} rows of the data")
        return self.data.head(num_rows)

    def download_data(self, file_format: str = 'csv', file_name: str = 'modified_data'):
        """Generates a downloadable file in the specified format."""
        self.logger.info(f"Downloading data in {file_format.upper()} format with file name {file_name}")

        if file_format == 'csv':
            self.logger.info("Converting data to CSV format")
            return self.data.to_csv(index=False).encode('utf-8')
        elif file_format == 'excel':
            self.logger.info("Converting data to Excel format")
            output = pd.ExcelWriter(f'{file_name}.xlsx', engine='xlsxwriter')
            self.data.to_excel(output, index=False, sheet_name='Sheet1')
            output.save()
            return output.getvalue()
        else:
            self.logger.error(f"Unsupported file format: {file_format}")
            raise ValueError("Unsupported file format. Choose 'csv' or 'excel'.")

    def summarize_data(self) -> pd.DataFrame:
        """Returns summary statistics of the data."""
        self.logger.info("Generating summary statistics of the data")
        return self.data.describe()

    def reset_data(self, original_data: pd.DataFrame):
        """Resets the modified data to the original state."""
        self.logger.info("Resetting data to the original state")
        self.data = original_data

    def export_to_database(self, connection, table_name: str):
        """Exports the modified data to a specified database table."""
        self.logger.info(f"Exporting data to the {table_name} table in the database")
        self.data.to_sql(table_name, connection, if_exists='replace', index=False)
        self.logger.info(f"Data successfully exported to {table_name} table")
        return f"Data exported to {table_name} table in the database."
