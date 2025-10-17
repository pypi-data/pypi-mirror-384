# Fount SDK API Reference

## Quick Reference

### Client Initialization

```python
from fount import Fount

# Basic usage
client = Fount()

# With custom transport
client = Fount(transport=custom_httpx_client)

# As context manager
with Fount() as client:
    # auto cleanup
    pass
```

### Environment Variables

- `FOUNT_API_KEY` - Your API key (required)
- `FOUNT_BASE_URL` - API base URL (default: https://fountondev.datapoem.ai/api/v1/)

## Class: `Fount`

### Methods

#### `upload_dataframe(dataframe, name=None) -> Dataset`

Upload a pandas DataFrame.

**Parameters:**

- `dataframe` (pd.DataFrame): DataFrame to upload
- `name` (str, optional): Dataset name

**Returns:** Dataset object with ID

---

#### `upload_csv(pathname, name) -> Dataset`

Upload a CSV file.

**Parameters:**

- `pathname` (str): Path to CSV file
- `name` (str, optional): Dataset name

**Returns:** Dataset object with ID

---

#### `upload_excel(pathname, sheet_name, name) -> Dataset`

Upload Excel file (not implemented).

**Parameters:**

- `pathname` (str): Path to Excel file
- `sheet_name` (str): Sheet to extract
- `name` (str, optional): Dataset name

---

#### `train(dataset, categorical_cols, date_column, target_columns, validation_data_required, validation_split, time_granularity, **kwargs) -> TrainingJob`

Train a model.

**Parameters:**

- `dataset` (Dataset): Training dataset
- `categorical_cols` (List[str]): Categorical column names
- `date_column` (str): Date column name
- `target_columns` (List[str]): Target column names
- `validation_data_required` (bool): Create validation set
- `validation_split` (float): Validation split ratio (0-1)
- `time_granularity` (str): Time interval or frequency
- `**kwargs`: Additional parameters (epochs, learning_rate, etc.)

**Returns:** TrainingJob object

---

#### `tune(categorical_cols, date_column, target_columns, validation_data_required, validation_split, time_granularity, **kwargs) -> TuningJob`

Hyperparameter tuning.

**Parameters:**

- `categorical_cols` (List[str]): Categorical column names
- `date_column` (str): Date column name
- `target_columns` (List[str]): Target column names
- `validation_data_required` (bool): Create validation set
- `validation_split` (float): Validation split ratio (0-1)
- `time_granularity` (str): Time interval or frequency
- `**kwargs`: Additional parameters (param_grid, n_trials, etc.)

**Returns:** TuningJob object

---

#### `inference(model_name, batch_size, **kwargs) -> InferenceJob`

Run batch inference.

**Parameters:**

- `model_name` (str): Model name/ID
- `batch_size` (int): Batch size
- `**kwargs`: Additional parameters (input_dataset, output_format, etc.)

**Returns:** InferenceJob object

---

#### `close() -> None`

Close client and release resources.

---

## Job Classes

All job classes (`TrainingJob`, `TuningJob`, `InferenceJob`) have:

### Methods

#### `status() -> Dict`

Get job status.

**Returns:** Dict with:

- `state`: Current state (pending, running, completed, failed)
- `progress`: Progress percentage
- `message`: Status message

#### `metrics() -> Dict`

Get job results/metrics.

**Returns:** Dict with job-specific metrics

## Exceptions

- `SDKError` - Base SDK exception
- `AuthenticationError` - Auth failures
- `RateLimitError` - Rate limit exceeded
- `UploadError` - Upload failures
- `TrainingError` - Training failures
- `InferenceError` - Inference failures
- `TuningError` - Tuning failures

## Common Patterns

### Training Pipeline

```python
# Upload data
df = pd.read_csv("data.csv")
dataset = client.upload_dataframe(df)

# Train model
job = client.train(
    dataset=dataset,
    categorical_cols=["cat1", "cat2"],
    date_column="date",
    target="target",
    validation_data_required=True,
    validation_split=0.2
)

# Monitor progress
while True:
    status = job.status()
    if status["state"] in ["completed", "failed"]:
        break
    time.sleep(30)

# Get results
if status["state"] == "completed":
    metrics = job.metrics()
```

### Batch Inference

```python
# Run inference
job = client.inference(
    model_name="my_model",
    batch_size=1000,
    input_dataset=dataset.id
)

# Get predictions
results = job.metrics()
predictions = results["predictions"]
```

### Error Handling

```python
from fount.errors import AuthenticationError, UploadError

try:
    dataset = client.upload_dataframe(df)
except AuthenticationError:
    print("Invalid API key")
except UploadError as e:
    print(f"Upload failed: {e}")
```
