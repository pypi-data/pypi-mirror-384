from typing import List

class Artifacts:
    id: str

    @classmethod
    def get_datasets(cls, _transport) -> List[dict]:
        return _transport.get_datasets()

    @classmethod
    def get_models(cls, _transport) -> List[dict]:
        return _transport.get_model()
