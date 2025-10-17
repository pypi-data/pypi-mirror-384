from typing import List


class Artifacts:
    id: str

    @classmethod
    def get_datasets(cls, _transport) -> List[dict]:
        return _transport.get_datasets()

    @classmethod
    def get_models(cls, _transport) -> List[dict]:
        return _transport.get_model()

    @classmethod
    def get_jobs(cls, _transport, job_type) -> List[dict]:
        return _transport.get_jobs(job_type)

    @classmethod
    def get_predictions(cls, _transport, job_id) -> List[dict]:
        t_type = job_id.split("-")[0]
        return _transport.get_predictions(job_id, t_type)
