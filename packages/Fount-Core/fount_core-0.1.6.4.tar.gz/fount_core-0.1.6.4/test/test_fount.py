"""Test suite for Fount SDK.

This module contains unit tests for all Fount SDK functionality including
client initialization, data upload, model training, tuning, and inference.
"""

import os
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock, mock_open
import httpx

# Import Fount SDK components
from fount import Fount
from fount.dataset import Dataset
from fount.jobs import TrainingJob, TuningJob, InferenceJob
from fount.transport import HTTPTransport
from fount.models import Config


class TestFountClient:
    """Test cases for Fount client initialization and configuration."""

    def test_init_default(self):
        """Test default client initialization."""
        with patch.dict(os.environ, {"FOUNT_API_KEY": "test-key"}):
            client = Fount()
            assert client.config is not None
            assert isinstance(client.client, HTTPTransport)

    def test_init_with_custom_transport(self):
        """Test client initialization with custom transport."""
        mock_transport = Mock(spec=httpx.Client)
        client = Fount(transport=mock_transport)
        assert client.client == mock_transport

    def test_init_with_logs(self):
        """Test client initialization with logs parameter."""
        with patch.dict(os.environ, {"FOUNT_API_KEY": "test-key"}):
            client = Fount(logs="debug")
            assert client.config is not None

    def test_close(self):
        """Test client close method."""
        mock_transport = Mock(spec=httpx.Client)
        mock_transport.close = Mock()
        client = Fount(transport=mock_transport)
        client.close()
        mock_transport.close.assert_called_once()


class TestDatasetUpload:
    """Test cases for dataset upload functionality."""

    @pytest.fixture
    def client(self):
        """Create a Fount client with mocked transport."""
        mock_transport = Mock()
        return Fount(transport=mock_transport)

    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample pandas DataFrame."""
        return pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=5),
                "value": [10, 20, 30, 40, 50],
                "category": ["A", "B", "A", "B", "C"],
            }
        )

    def test_upload_dataframe_success(self, client, sample_dataframe):
        """Test successful DataFrame upload."""
        # Mock the transport response
        client.client.upload_dataframe = Mock(return_value="dataset-123")

        with patch("fount.dataset.Dataset.upload_dataframe") as mock_upload:
            mock_upload.return_value = Dataset(id="dataset-123")

            result = client.upload_dataframe(sample_dataframe, name="test_dataset")

            assert isinstance(result, Dataset)
            assert result.id == "dataset-123"
            mock_upload.assert_called_once_with(
                client.client, sample_dataframe, "test_dataset"
            )

    def test_upload_empty_dataframe(self, client):
        """Test uploading empty DataFrame raises ValueError."""
        empty_df = pd.DataFrame()

        with pytest.raises(ValueError, match="Dataframe is empty"):
            client.upload_dataframe(empty_df)

    def test_upload_csv_success(self, client):
        """Test successful CSV file upload."""
        csv_content = "col1,col2\n1,2\n3,4"

        with patch("builtins.open", mock_open(read_data=csv_content)):
            with patch("os.path.exists", return_value=True):
                with patch("fount.dataset.Dataset.upload_dataframe") as mock_upload:
                    mock_upload.return_value = Dataset(id="dataset-456")

                    result = client.upload_csv("test.csv", name="csv_dataset")

                    assert isinstance(result, Dataset)
                    assert result.id == "dataset-456"

    def test_upload_csv_file_not_found(self, client):
        """Test CSV upload with non-existent file."""
        with patch("os.path.exists", return_value=False):
            with pytest.raises(FileNotFoundError, match="File does not exists"):
                client.upload_csv("nonexistent.csv", name="test")

    def test_upload_excel_not_implemented(self, client):
        """Test Excel upload (currently not implemented)."""
        # This should not raise an error but does nothing
        result = client.upload_excel("test.xlsx", "Sheet1", "excel_dataset")
        assert result is None


class TestTraining:
    """Test cases for model training functionality."""

    @pytest.fixture
    def client(self):
        """Create a Fount client with mocked transport."""
        mock_transport = Mock()
        return Fount(transport=mock_transport)

    @pytest.fixture
    def dataset(self):
        """Create a mock dataset."""
        return Dataset(id="dataset-123")

    def test_train_success(self, client, dataset):
        """Test successful model training job creation."""
        # Mock the transport response
        client.client.start_job = Mock(return_value={"id": "job-789"})

        with patch("fount.jobs.TrainingJob.run") as mock_run:
            mock_job = TrainingJob(id="job-789", _transport=client.client)
            mock_run.return_value = mock_job

            result = client.train(
                dataset=dataset,
                model_name="sales_forecast_model",
                categorical_cols=["category", "region"],
                date_column="date",
                target_columns=["sales"],
                validation_data_required=True,
                validation_split=0.2,
                time_granularity="daily",
            )

            assert isinstance(result, TrainingJob)
            assert result.id == "job-789"

            # Verify the payload
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][0] == client.client
            assert call_args[0][1] == "training"

            payload = call_args[0][2]
            assert payload["dataset"] == "dataset-123"
            assert payload["model_name"] == "sales_forecast_model"
            assert payload["categorical_cols"] == ["category", "region"]
            assert payload["date_col"] == "date"
            assert payload["target_col"] == ["sales"]
            assert payload["validation_data_required"] is True
            assert payload["validation_split"] == 0.2
            assert payload["time_granularity"] == "daily"

    def test_train_with_additional_params(self, client, dataset):
        """Test training with additional parameters."""
        client.client.start_job = Mock(return_value={"id": "job-999"})

        with patch("fount.jobs.TrainingJob.run") as mock_run:
            mock_job = TrainingJob(id="job-999", _transport=client.client)
            mock_run.return_value = mock_job

            result = client.train(
                dataset=dataset,
                model_name="advanced_model",
                categorical_cols=["cat1"],
                date_column="timestamp",
                target_columns=["target1", "target2"],
                validation_data_required=False,
                validation_split=0.0,
                time_granularity="hourly",
                epochs=100,
                batch_size=64,
            )

            # Check additional params were passed
            payload = mock_run.call_args[0][2]
            assert payload["epochs"] == 100
            assert payload["batch_size"] == 64


class TestTuning:
    """Test cases for model tuning functionality."""

    @pytest.fixture
    def client(self):
        """Create a Fount client with mocked transport."""
        mock_transport = Mock()
        return Fount(transport=mock_transport)

    @pytest.fixture
    def dataset(self):
        """Create a mock dataset."""
        return Dataset(id="dataset-456")

    @pytest.fixture
    def training_job(self, client):
        """Create a mock training job."""
        return TrainingJob(id="training-123", _transport=client.client)

    def test_tune_without_training(self, client, dataset):
        """Test tuning without prior training job."""
        with patch("fount.jobs.TuningJob.run") as mock_run:
            mock_job = TuningJob(id="tune-111", _transport=client.client)
            mock_run.return_value = mock_job

            result = client.tune(
                dataset=dataset,
                training=None,
                categorical_cols=["cat1", "cat2"],
                date_column="date",
                model_name="tuned_model",
                target_columns=["target"],
                validation_data_required=True,
                validation_split=0.2,
                time_granularity="daily",
            )

            assert isinstance(result, TuningJob)
            assert result.id == "tune-111"

            # Verify training_id not in payload
            payload = mock_run.call_args[0][2]
            assert "training_id" not in payload

    def test_tune_with_training(self, client, dataset, training_job):
        """Test tuning with prior training job."""
        with patch("fount.jobs.TuningJob.run") as mock_run:
            mock_job = TuningJob(id="tune-222", _transport=client.client)
            mock_run.return_value = mock_job

            result = client.tune(
                dataset=dataset,
                training=training_job,
                categorical_cols=["cat1"],
                date_column="date",
                model_name="tuned_model_v2",
                target_columns=["sales"],
                validation_data_required=True,
                validation_split=0.3,
                time_granularity="weekly",
            )

            # Verify training_id in payload
            payload = mock_run.call_args[0][2]
            assert payload["training_id"] == "training-123"
            assert payload["dataset"] == "dataset-456"
            assert payload["model_name"] == "tuned_model_v2"


class TestInference:
    """Test cases for inference functionality."""

    @pytest.fixture
    def client(self):
        """Create a Fount client with mocked transport."""
        mock_transport = Mock()
        return Fount(transport=mock_transport)

    @pytest.fixture
    def dataset(self):
        """Create a mock dataset."""
        return Dataset(id="dataset-789")

    def test_inference_success(self, client, dataset):
        """Test successful inference job creation."""
        with patch("fount.jobs.InferenceJob.run") as mock_run:
            mock_job = InferenceJob(id="inf-333", _transport=client.client)
            mock_run.return_value = mock_job

            result = client.inference(
                dataset=dataset, model_name="production_model", batch_size=1000
            )

            assert isinstance(result, InferenceJob)
            assert result.id == "inf-333"

            # Verify payload
            payload = mock_run.call_args[0][2]
            assert payload["dataset"] == "dataset-789"
            assert payload["model_name"] == "production_model"
            assert payload["batch_size"] == 1000

    def test_inference_with_kwargs(self, client, dataset):
        """Test inference with additional parameters."""
        with patch("fount.jobs.InferenceJob.run") as mock_run:
            mock_job = InferenceJob(id="inf-444", _transport=client.client)
            mock_run.return_value = mock_job

            result = client.inference(
                dataset=dataset,
                model_name="model_v2",
                batch_size=500,
                output_format="parquet",
                include_confidence=True,
            )

            # Check additional params
            payload = mock_run.call_args[0][2]
            assert payload["output_format"] == "parquet"
            assert payload["include_confidence"] is True


class TestJobs:
    """Test cases for job status and metrics functionality."""

    @pytest.fixture
    def mock_transport(self):
        """Create a mock transport."""
        return Mock()

    def test_training_job_status(self, mock_transport):
        """Test TrainingJob status method."""
        job = TrainingJob(id="job-123", _transport=mock_transport)
        mock_transport.get_job_status.return_value = {
            "state": "running",
            "progress": 45,
            "message": "Training in progress",
        }

        status = job.status()

        assert status["state"] == "running"
        assert status["progress"] == 45
        mock_transport.get_job_status.assert_called_once_with("job-123")

    def test_training_job_metrics(self, mock_transport):
        """Test TrainingJob metrics method."""
        job = TrainingJob(id="job-123", _transport=mock_transport)
        mock_transport.get_job_metrics.return_value = {
            "accuracy": 0.95,
            "loss": 0.05,
            "model_name": "model_v1",
        }

        metrics = job.metrics()

        assert metrics["accuracy"] == 0.95
        assert metrics["model_name"] == "model_v1"
        mock_transport.get_job_metrics.assert_called_once_with("job-123")

    def test_tuning_job_methods(self, mock_transport):
        """Test TuningJob status and metrics methods."""
        job = TuningJob(id="tune-456", _transport=mock_transport)

        # Test status
        mock_transport.get_job_status.return_value = {"state": "completed"}
        status = job.status()
        assert status["state"] == "completed"

        # Test metrics
        mock_transport.get_job_metrics.return_value = {
            "best_params": {"learning_rate": 0.01},
            "best_score": 0.98,
        }
        metrics = job.metrics()
        assert metrics["best_score"] == 0.98

    def test_inference_job_methods(self, mock_transport):
        """Test InferenceJob status and metrics methods."""
        job = InferenceJob(id="inf-789", _transport=mock_transport)

        # Test status
        mock_transport.get_job_status.return_value = {
            "state": "completed",
            "progress": 100,
        }
        status = job.status()
        assert status["progress"] == 100

        # Test metrics
        mock_transport.get_job_metrics.return_value = {
            "predictions": [0.1, 0.9, 0.3],
            "processing_time": 2.5,
        }
        metrics = job.metrics()
        assert len(metrics["predictions"]) == 3


class TestHTTPTransport:
    """Test cases for HTTPTransport functionality."""

    @pytest.fixture
    def transport(self):
        """Create HTTPTransport with mocked client."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            transport = HTTPTransport(
                base_url="https://api.example.com", timeout=30.0, api_key="test-key"
            )
            transport.client = mock_client
            return transport

    def test_upload_dataframe(self, transport):
        """Test dataframe upload through transport."""
        df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})

        # Mock streaming response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.iter_text.return_value = [
            '{"status": "Uploading..."}',
            '{"status": "Processing...", "job_id": "job-123"}',
        ]

        transport.client.stream.return_value.__enter__.return_value = mock_response

        result = transport.upload_dataframe(df)

        assert result == "job-123"

    def test_start_job_success(self, transport):
        """Test successful job start."""
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {"id": "job-456", "status": "started"}
        transport.client.post.return_value = mock_response

        result = transport.start_job("training", {"model": "test"})

        assert result["id"] == "job-456"
        transport.client.post.assert_called_once_with(
            "training", json={"model": "test"}
        )

    def test_start_job_client_error(self, transport):
        """Test job start with client error."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.is_client_error = True
        mock_response.is_server_error = False
        transport.client.post.return_value = mock_response

        result = transport.start_job("training", {})

        assert result["error"] == "Client error"

    def test_get_job_status(self, transport):
        """Test getting job status."""
        mock_response = Mock()
        mock_response.json.return_value = {"state": "running", "progress": 75}
        transport.client.get.return_value = mock_response

        result = transport.get_job_status("job-123")

        assert result["progress"] == 75
        transport.client.get.assert_called_once_with(
            "status", params={"task_id": "job-123"}
        )

    def test_close(self, transport):
        """Test transport close method."""
        result = transport.close()
        assert result is None


class TestErrorHandling:
    """Test cases for error handling scenarios."""

    @pytest.fixture
    def client(self):
        """Create a Fount client with mocked transport."""
        mock_transport = Mock()
        return Fount(transport=mock_transport)

    def test_upload_network_error(self, client):
        """Test upload with network error."""
        client.client.upload_dataframe = Mock(
            side_effect=httpx.RequestError("Network error")
        )

        df = pd.DataFrame({"col": [1, 2, 3]})
        with patch("fount.dataset.Dataset.upload_dataframe") as mock_upload:
            mock_upload.side_effect = UploadError("Upload failed")

            with pytest.raises(UploadError):
                client.upload_dataframe(df)

    def test_training_server_error(self, client):
        """Test training with server error."""
        dataset = Dataset(id="dataset-123")

        with patch("fount.jobs.TrainingJob.run") as mock_run:
            mock_run.side_effect = TrainingError("Server error during training")

            with pytest.raises(TrainingError):
                client.train(
                    dataset=dataset,
                    model_name="test",
                    categorical_cols=["cat"],
                    date_column="date",
                    target_columns=["target"],
                    validation_data_required=True,
                    validation_split=0.2,
                    time_granularity="daily",
                )


class TestConfig:
    """Test cases for Config model."""

    def test_config_from_env(self):
        """Test Config initialization from environment variables."""
        with patch.dict(
            os.environ,
            {
                "FOUNT_API_KEY": "env-api-key",
                "FOUNT_BASE_URL": "https://custom.api.com",
            },
        ):
            config = Config()
            assert config.fount_api_key.get_secret_value() == "env-api-key"
            assert config.fount_base_url == "https://custom.api.com"

    def test_config_defaults(self):
        """Test Config with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.fount_base_url == "https://fountondev.datapoem.ai/api/v1/"
            assert config.timeout == 200.0


# Integration test example (requires mock server or test environment)
class TestIntegration:
    """Integration tests for end-to-end workflows."""

    @pytest.mark.integration
    def test_full_workflow(self):
        """Test complete workflow from upload to inference."""
        # This would require a test server or extensive mocking
        # Placeholder for integration testing
        pass


if __name__ == "__main__":
    pytest.main([__file__])
