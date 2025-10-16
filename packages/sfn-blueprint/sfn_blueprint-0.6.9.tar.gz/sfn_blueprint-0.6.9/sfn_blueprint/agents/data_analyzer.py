from sfn_blueprint.utils.logging import setup_logger
from .base_agent import SFNAgent

class SFNDataAnalyzerAgent(SFNAgent):
    """
    This agent analyzes the data and returns a summary of the data.
    """
    def __init__(self):
        super().__init__(name="Data Analyzer", role="Data Analysis Specialist")
        self.logger, _ = setup_logger(logger_name="SFNDataAnalyzerAgent")

    def execute_task(self, task):
        """
        Analyze the provided data and return a summary.
        
        :param task: Task object containing the data (a DataFrame)
        :return: A dictionary containing various summaries of the data
        """
        df = task.data
        self.logger.info("Starting data analysis...")
        
        try:
            # Log the shape and column names
            self.logger.info(f"DataFrame shape: {df.shape}")
            self.logger.info(f"Columns: {df.columns.tolist()}")

            # Generate summaries
            data_summary = {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.to_dict(),
                "missing_values": df.isnull().sum().to_dict(),
                "duplicates": df.duplicated().sum(),
                "numeric_summary": df.describe().to_dict()
            }

            # Handle categorical columns
            categorical_columns = df.select_dtypes(include=['object'])
            if not categorical_columns.empty:
                data_summary["categorical_summary"] = categorical_columns.describe().to_dict()
            else:
                self.logger.info("No categorical columns to describe.")
                data_summary["categorical_summary"] = {}

            self.logger.info("Data analysis completed successfully.")
            return data_summary
        except Exception as e:
            self.logger.error(f"Error during data analysis: {str(e)}")
            raise e
