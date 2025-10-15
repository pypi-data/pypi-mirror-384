from __future__ import annotations
from typing import Dict, List, Optional, Literal, TYPE_CHECKING
from .dataset import Dataset
from .artifact import Artifacts
from .jobs import InferenceJob, TrainingJob, TuningJob
from .transport import HTTPTransport
from .models import Config
import os

if TYPE_CHECKING:
    from pandas.core.frame import DataFrame
    import httpx

TIME_GRANULARITY = Literal[
    "second",
    "minute",
    "half_hour",
    "hour",
    "daily",
    "weekly",
    "monthly",
    "quarterly",
    "half_yearly",
    "yearly",
    "decade",
    "non-timeseries",
]


class Fount:
    api_key: str | None

    def __init__(self, transport: Optional["httpx.Client"] = None):
        """Main client for interacting with the Fount API.

            The Fount client provides a high-level interface for machine learning operations
            including dataset management, model training, fine-tuning, and inference on the
            Fount platform.

            Attributes:
                config (Config): Configuration object containing API settings
                client (httpx.Client): HTTP client for making API requests

            Examples:
                Basic initialization:

                >>> from fount import Fount
                >>> client = Fount()
                >>> jobs = client.list_all_jobs()

                With custom transport configuration:

                >>> import httpx
                >>> transport = httpx.Client(
                ...     timeout=30.0,
                ...     limits=httpx.Limits(max_keepalive_connections=5)
                ... )
                >>> client = Fount(
                ...     transport=transport,
                ... )

                Using context manager for automatic cleanup:

                >>> with Fount() as client:
                ...     result = client.train(config)

        Note:
            The client maintains a persistent HTTP connection pool for efficiency.
            Remember to close the client when done or use it as a context manager.

        See Also:
            - :func:`create_client`: Factory function for creating clients
            - :func:`from_env`: Create client from environment variables
            - :class:`Config`: Configuration class for client settings
        """
        self.config = Config()
        self.client = transport or HTTPTransport(
            base_url=self.config.fount_base_url,
            timeout=self.config.timeout,
            api_key=self.config.fount_api_key.get_secret_value(),
        )

    def upload_dataframe(
        self, dataframe: "DataFrame", name: str | None = None
    ) -> Dataset|None:
        """Upload a pandas DataFrame to the Fount platform.

        Args:
            dataframe (DataFrame): The pandas DataFrame to upload. Must not be empty.
            name (str, optional): A descriptive name for the dataset.

        Returns:
            Dataset: A Dataset object containing the ID of the uploaded dataset.

        Raises:
            ValueError: If the dataframe is empty.
            UploadError: If the upload fails due to network or server errors.

        Example:
            >>> df = pd.read_csv("sales_data.csv")
            >>> dataset = client.upload_dataframe(df, name="Q4_sales_2024")
            >>> print(f"Dataset ID: {dataset.id}")
        """
        if dataframe.empty:
            raise ValueError("Dataframe is empty. Cannot upload empty dataframe.")
        return Dataset.upload_dataframe(self.client, dataframe, name)

    def upload_csv(self, pathname: str, name: str | None) -> Dataset|None:
        """Upload a CSV file to the Fount platform.

        Args:
            pathname (str): Path to the CSV file to upload.
            name (str, optional): A descriptive name for the dataset.

        Returns:
            Dataset: A Dataset object containing the ID of the uploaded dataset.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            CSVParseError: If the CSV file cannot be parsed.
            UploadError: If the upload fails.

        Example:
            >>> dataset = client.upload_csv("data/sales_2024.csv", name="sales_data")
            >>> print(f"Uploaded dataset: {dataset.id}")
        """
        if not os.path.exists(pathname):
            raise FileNotFoundError("File does not exists")
        return Dataset.upload_csv(self.client, pathname, name)

    def upload_excel(self, pathname: str, sheet_name: str, name: str | None) -> Dataset|None:
        """Upload an Excel file to the Fount platform.

        Args:
            pathname (str): Path to the Excel file to upload.
            sheet_name (str): Name of the sheet to extract data from.
            name (str, optional): A descriptive name for the dataset.

        Returns:
            Dataset: A Dataset object containing the ID of the uploaded dataset.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the specified sheet does not exist.
            UploadError: If the upload fails.

        Note:
            This method is not yet implemented.
        """
        if not os.path.exists(pathname):
            raise FileNotFoundError("File does not exists")
        return Dataset.upload_excel(self.client, pathname, sheet_name, name)

    def train(
            self,
            dataset: Dataset,
            model_name: str,
            categorical_cols: List[str],
            date_column: str,
            target_columns: List[str],
            validation_data_required: bool,
            validation_split: float,
            time_granularity: TIME_GRANULARITY,
            **kwargs: Dict,
        ) -> TrainingJob:
        """Train a machine learning model on the Fount platform.

        Args:
            dataset (Dataset): The dataset to train on, obtained from upload methods.
            categorical_cols (List[str]): List of column names that contain categorical data.
            model_name (str): A descriptive name for the model to be generated.
            date_column (str): Name of the column containing date/time information.
            target_columns (List[str]): Name of the column to predict (target variable).
            validation_data_required (bool): Whether to split data for validation.
            validation_split (float): Proportion of data to use for validation (0.0 to 1.0).
            time_granularity (TIME_GRANULARITY): Time granularity of the dataset. Must be one of
                - second
                - minute
                - half_hour
                - hour
                - daily
                - weekly
                - monthly
                - quarterly
                - half_yearly
                - yearly
                - decade
                - non-timeseries
            wait (bool): If True, wait for job completion with KeyboardInterrupt handling (default: False)
            poll_interval (int): Seconds between status checks when waiting (default: 30)
            **kwargs: Additional training parameters

        Returns:
            TrainingJob: A job object to track training progress and retrieve results.

        Raises:
            TrainingError: If training initialization fails.
            ValueError: If validation_split is not between 0 and 1.

        Example:
            >>> job = client.train(
            ...     dataset=my_dataset,
            ...     categorical_cols=["product_type", "region"],
            ...     date_column="order_date",
            ...     target="revenue",
            ...     validation_data_required=True,
            ...     validation_split=0.2,
            ...     model_name="my_model_name",
            ... )
            >>> status = job.status()
            >>> print(f"Training status: {status['status']}")
        """
        payload = {
            "dataset": dataset.id,
            "categorical_cols": categorical_cols,
            "model_name": model_name,
            "date_col": date_column,
            "target_cols": target_columns,
            "validation_data_required": validation_data_required,
            "validation_split": validation_split,
            "time_granularity": time_granularity,
            **kwargs,
        }
        return TrainingJob.submit(self.client, "training", payload)

    def tune(
        self,
        dataset: Dataset,
        training: TrainingJob | None,
        categorical_cols: List[str],
        date_column: str,
        model_name: str,
        target_columns: List[str],
        validation_data_required: bool,
        validation_split: float,
        time_granularity: TIME_GRANULARITY,
        **kwargs: Dict,
    ) -> TuningJob:
        """Fine-tune a model with hyperparameter optimization.

        Args:
            dataset (Dataset): The dataset to train on, obtained from upload methods.
            training (TrainingJob): training object
            categorical_cols (List[str]): List of column names that contain categorical data.
            date_column (str): Name of the column containing date/time information.
            model_name (str): A descriptive name for the model to be generated.
            target_columns (List[str]): Name of the column to predict (target variable).
            validation_data_required (bool): Whether to split data for validation.
            validation_split (float): Proportion of data to use for validation (0.0 to 1.0).
            time_granularity (TIME_GRANULARITY): Time granularity of the dataset. Must be one of
                - second
                - minute
                - half_hour
                - hour
                - daily
                - weekly
                - monthly
                - quarterly
                - half_yearly
                - yearly
                - decade
                - non-timeseries
            **kwargs: Additional tuning parameters such as:

        Returns:
            TuningJob: A job object to track tuning progress and retrieve best parameters.

        Raises:
            TuningError: If tuning initialization fails.
            ValueError: If required parameters are invalid.

        Example:
            >>> job = client.tune(
            ...     categorical_cols=["category", "brand"],
            ...     date_column="timestamp",
            ...     target="sales",
            ...     validation_data_required=True,
            ...     validation_split=0.2,
            ... )
            >>> best_params = job.metrics()["best_parameters"]
        """
        payload = {
            "dataset": dataset.id,
            "categorical_cols": categorical_cols,
            "date_col": date_column,
            "model_name": model_name,
            "target_cols": target_columns,
            "validation_data_required": validation_data_required,
            "validation_split": validation_split,
            "time_granularity": time_granularity,
            **kwargs,
        }
        if training:
            payload["training_id"] = training.id
        return TuningJob.submit(self.client, "tuning", payload)

    def inference(
        self,
        dataset: Dataset,
        model_name: str,
        batch_size: int,
        **kwargs: Dict,
    ) -> InferenceJob:
        """Run inference using a trained model.

        Args:
            model_name (str): Name or ID of the trained model to use for predictions.
            batch_size (int): Number of samples to process in each batch.

        Returns:
            InferenceJob: A job object to track inference progress and retrieve predictions.

        Raises:
            InferenceError: If inference initialization fails.
            ValueError: If model_name is not found or batch_size is invalid.

        Example:
            >>> # Run batch inference on new data
            >>> inference_job = client.inference(
            ...     model_name="sales_forecast_v2",
            ...     batch_size=1000,
            ... )
            ...
            >>> # Wait for completion and get results
            >>> while inference_job.status()["state"] != "completed":
            ...     time.sleep(10)
            >>> predictions = inference_job.metrics()["predictions"]
        """
        payload = {
            "dataset": dataset.id,
            "model_name": model_name,
            "batch_size": batch_size,
            **kwargs,
        }
        return InferenceJob.submit(self.client, "inference", payload)

    def get_all_datasets(self) -> List[dict]:
        return Artifacts.get_datasets(self.client)


    def close(self) -> None:
        """Close the HTTP client and release resources.

        This method should be called when you're done using the client to ensure
        proper cleanup of network connections and resources. Alternatively, use
        the client as a context manager for automatic cleanup.

        Example:
            >>> client = Fount()
            >>> # ... use client ...
            >>> client.close()

            Or use context manager:
            >>> with Fount() as client:
            ...     # ... use client ...
            ...     pass  # Automatically closed
        """
        self.client.close()
