import aiofiles
import base64
import hashlib
from abc import abstractmethod
from pathlib import Path
from typing import Generator, Union

__all__ = [
    "ChecksumAlgorithm",
    "AlgorithmMD5",
    "AlgorithmGA4GH",
]

DEFAULT_CHUNK_SIZE = 128 * 1024  # 128 KB
DEFAULT_GA4GH_OFFSET = 24


class ChecksumAlgorithm(type):
    # https://stackoverflow.com/questions/13762231/how-to-pass-arguments-to-the-metaclass-from-the-class-definition

    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        return super().__prepare__(name, bases, **kwargs)

    def __new__(mcs, name, bases, namespace, **kwargs):
        return super().__new__(mcs, name, bases, namespace)

    def __init__(cls, name, bases, namespace, algorithm_name=""):
        super().__init__(name, bases, namespace)
        cls.algorithm_name = algorithm_name

    def __str__(self):
        return self.algorithm_name

    @staticmethod
    async def update_hash_from_file(h, file: Union[Path, str], chunk_size: int):
        async with aiofiles.open(file, "rb") as fh:
            while data := (await fh.read(chunk_size)):
                h.update(data)
        return h

    @staticmethod
    def update_hash_from_sequence(h, sequence: Generator[bytes, None, None]):
        while data := next(sequence, None):
            h.update(data)
        return h

    @classmethod
    @abstractmethod
    async def checksum_file(
        mcs,
        file: Union[Path, str],
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        **kwargs,
    ) -> str:  # pragma: no cover
        pass

    @classmethod
    @abstractmethod
    async def checksum_sequence(mcs, sequence: Generator[bytes, None, None]) -> str:  # pragma: no cover
        pass


class AlgorithmMD5(metaclass=ChecksumAlgorithm, algorithm_name="md5"):
    @classmethod
    async def checksum_file(cls, file: Union[Path, str], chunk_size: int = DEFAULT_CHUNK_SIZE, **_kwargs) -> str:
        return (await ChecksumAlgorithm.update_hash_from_file(hashlib.md5(), file, chunk_size)).hexdigest()

    @classmethod
    async def checksum_sequence(cls, sequence: Generator[bytes, None, None], **_kwargs) -> str:
        return ChecksumAlgorithm.update_hash_from_sequence(hashlib.md5(), sequence).hexdigest()


class AlgorithmGA4GH(metaclass=ChecksumAlgorithm, algorithm_name="ga4gh"):
    @staticmethod
    def _ga4gh_of_hash(h, offset: int) -> str:
        b64_enc = base64.urlsafe_b64encode(h.digest()[:offset]).decode("ascii")
        return f"SQ.{b64_enc}"

    @classmethod
    async def checksum_file(cls, file: Union[Path, str], chunk_size: int = DEFAULT_CHUNK_SIZE, **kwargs):
        return cls._ga4gh_of_hash(
            h=await cls.update_hash_from_file(hashlib.sha512(), file, chunk_size),
            offset=kwargs.pop("offset", DEFAULT_GA4GH_OFFSET),
        )

    @classmethod
    async def checksum_sequence(cls, sequence: Generator[bytes, None, None], **kwargs) -> str:
        return cls._ga4gh_of_hash(
            h=cls.update_hash_from_sequence(hashlib.sha512(), sequence),
            offset=kwargs.pop("offset", DEFAULT_GA4GH_OFFSET),
        )
