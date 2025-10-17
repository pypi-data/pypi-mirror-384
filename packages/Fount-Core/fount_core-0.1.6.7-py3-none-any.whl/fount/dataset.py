from dataclasses import dataclass
import sys


@dataclass
class Dataset:
    id: str

    @classmethod
    def upload_dataframe(cls, _transport, dataframe, name):
        try:
            _r = _transport.upload_dataframe(dataframe, name)
            return cls(_r)
        except Exception as e:
            sys.stderr.write(str(e))
            return None


    @classmethod
    def upload_csv(cls, _transport, pathname, name):
        try:
            _r = _transport.upload_csv(pathname, name)
            return cls(_r)
        except Exception as e:
            sys.stderr.write(str(e))
            return None

    @classmethod
    def upload_excel(cls, _transport, pathname, sheet_name, name):
        try:
            _r = _transport.upload_excel(pathname, sheet_name, name)
            return cls(_r)
        except Exception as e:
            sys.stderr.write(str(e))
            return None
