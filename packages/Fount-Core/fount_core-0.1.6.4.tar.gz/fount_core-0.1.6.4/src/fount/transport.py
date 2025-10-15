from __future__ import annotations
from typing import Optional
from io import StringIO,BytesIO
import json
import sys
import httpx
from ._exceptions import (
    TrainingError,
    UnauthorizedError,
    TimedOutError,
    RequestError,
    EntityError,
    UploadError,
)

def loader(progress: float):
    bar_count = int(progress)
    dots = 100-bar_count
    bar_char = '\u2588'
    dots_char = '.'
    progress_bar = f"\r[ {bar_char * bar_count}{dots_char * dots} ] | {progress}%"
    sys.stdout.write(progress_bar)
    sys.stdout.flush()

class HTTPTransport:
    def __init__(
        self,
        base_url: httpx.URL | str,
        timeout: float,
        api_key: str,
        client: Optional[httpx.Client] = None,
    ):
        self.client = client or httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers={"X-API-Key": f"{api_key}"} if api_key else {},
        )

    def upload_dataframe(self, dataframe, name):
        csv_params = {"index": False, "encoding": "utf-8", "compression": None}
        buffer = BytesIO()
        try:
            dataframe.to_csv(buffer, **csv_params)
            files = {"file": ("dataframe.csv", buffer.getvalue(), "text/csv")}
            try:
                job_id = None
                sys.stdout.write("==> Preparing for upload\n")
                with self.client.stream(
                    method="POST",
                    params={"name": name},
                    url="upload",
                    files=files,
                ) as _stream_response:
                    _stream_response.raise_for_status()
                    for chunk in _stream_response.iter_text():
                        try:
                            data = json.loads(chunk)
                        except json.JSONDecodeError:
                            continue
                        loader(float(data.get('progress')))
                        if "job_id" in data:
                            sys.stdout.write(f"\n{data.get('status')}\n")
                            job_id = data.get("job_id")
                return job_id
            except httpx.TimeoutException:
                raise TimedOutError("Request timed out")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise UnauthorizedError("Check API key or credentials") from e
                elif e.response.status_code == 422:
                    raise EntityError("Params error") from e
                elif e.response.status_code == 500:
                    raise UploadError("Failed to upload file.\n")
                elif e.response.status_code == 400:
                    raise UploadError("Dataset already exists. Please supply a different dataset name.\n")
            except httpx.RequestError as e:
                raise RequestError(e)
        finally:
            buffer.close()

    def upload_csv(self, pathname, name):
        import csv
        with open(pathname, "r") as file:
            reader = csv.reader(file)
            buffer = StringIO()
            writer = csv.writer(buffer)
            for row in reader:
                writer.writerow(row)
            byte_buffer = BytesIO(buffer.getvalue().encode("utf-8"))
        files = {"file": ("dataframe.csv", byte_buffer.getvalue(), "text/csv")}
        return self.client.post("upload", files=files, params={"name": name})

    def upload_excel(self, pathname, sheet_name, name):
        import pandas
        with pandas.ExcelFile(path_or_buffer=pathname) as xls:
            df = pandas.read_excel(xls, sheet_name=sheet_name)
            buffer = BytesIO()
            df.to_csv(buffer)
            files = {"file": ("dataframe.csv", buffer.getvalue(), "text/csv")}
            files = {
                "file": (
                    "dataframe.csv",
                    buffer.getvalue(),
                    "text/csv",
                )
            }
        return self.client.post("upload", files=files, params={"name": name})

    def start_job(self, job_type, payload):
        _r = self.client.post(job_type, json=payload)
        if _r.status_code == 200:
            return _r.json()
        elif _r.status_code == 422:
            sys.stderr.write("Failed. Please check input parameters\n")
            sys.stderr.write(f"{_r.json()}\n")
            raise TrainingError("Unprocessable Entity")
        elif _r.status_code == 500:
            sys.stderr.write("Failed. Something went wrong\n")
            sys.stderr.write(f"{_r.json()}\n")
            raise TrainingError("Something went wrong")

    def get_model(self):
        req = self.client.get("models")
        return req.json()

    def get_datasets(self):
        req = self.client.get("datasets")
        return req.json()

    def get_job_status(self, _p):
        req = self.client.get("status", params={"task_id": _p})
        return req.json()

    def get_job_metrics(self, _p,job_type):
        return self.client.get("metrics", params={"task_id": _p,"task_type":job_type}).json()

    def get_artifacts(self, _p):
        return self.client.get("artifacts", params={"task_id": _p}).json()

    def get_predictions(self,job_name,t_type):
        return self.client.get("predictions",params={"job_name":job_name,"task_type":t_type}).json()

    def stop(self, _p):
        return self.client.get("stop", params={"task_id": _p}).json()

    def close(self):
        return None
