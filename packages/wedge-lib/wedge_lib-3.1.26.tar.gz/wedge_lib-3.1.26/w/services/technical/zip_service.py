import zipfile
from io import BytesIO

from w.services.abstract_service import AbstractService


class ZipService(AbstractService):
    @classmethod
    def zip2memory(cls, files: dict[str, bytes]) -> bytes:
        """
        zip files to memory

        Args:
            files (dict[str, bytes]): {<zip_path:str>: <content:bytes>, ...}

        Return:
             bytes
        """
        archive = BytesIO()

        with zipfile.ZipFile(archive, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for filename, io_buffer in files.items():
                zf.writestr(filename, io_buffer)

        return archive.getvalue()
