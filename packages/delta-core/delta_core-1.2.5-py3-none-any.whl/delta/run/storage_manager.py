import glob
import hashlib
import json
import logging
import os
import shutil
import urllib.request
import uuid
from abc import ABC, abstractmethod
from typing import IO, AnyStr, Dict, List

import boto3
import s3fs
import yaml
from aiohttp import ClientError

from delta.manifest.parser import Manifest, parse


class DeltaStorageManager(ABC):
    @abstractmethod
    def add_run_directory(self, run_id: uuid.UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_full_path(self, path):
        raise NotImplementedError

    @abstractmethod
    def get_models_filepaths(self, name, version, model_path):
        raise NotImplementedError

    @abstractmethod
    def get_deltatwin_manifest(self, name: str, version: str) -> Manifest:
        raise NotImplementedError

    @abstractmethod
    def get_deltatwin_workflow(self, name: str, version: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_data(self, run_id: uuid.UUID, job_id: str, basename: str) -> IO:
        raise NotImplementedError

    @abstractmethod
    def set_data(
        self, run_id: uuid.UUID, job_id: str, basename: str, stream: IO
    ):
        raise NotImplementedError

    @abstractmethod
    def find_data(
        self, run_id: uuid.UUID, job_id: str, _glob: str
    ) -> List[AnyStr]:
        raise NotImplementedError

    def get_data_info(self, data_path) -> Dict:
        return NotImplementedError

    @abstractmethod
    def remove_run(self, run_id: uuid.UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    def push_deltatwin(self, directory, name: str, version: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove_deltatwin(self, name: str, version: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def has_deltatwin(self, name: str, version: str) -> bool:
        raise NotImplementedError


class DeltaLocalStorageManager(DeltaStorageManager):
    DEFAULT_DIRECTORY = os.path.join(os.getenv("HOME"), ".delta")
    LOGGER = logging.getLogger("LocalStorageManager")

    def __init__(self, base_dir: str = None) -> None:
        self._base_dir = base_dir or self.DEFAULT_DIRECTORY

        if not os.path.isdir(self._base_dir):
            self.LOGGER.info("Creating base storage")
            os.makedirs(self._base_dir)

        self._deltatwin_dir = os.path.join(self._base_dir, "deltatwins")
        if not os.path.isdir(self._deltatwin_dir):
            self.LOGGER.info("Creating deltatwin storage")
            os.makedirs(self._deltatwin_dir)

        self._run_dir = os.path.join(self._base_dir, "runs")
        if not os.path.isdir(self._run_dir):
            self.LOGGER.info(f"Creating run storage")
            os.makedirs(self._run_dir)

    def get_full_path(self, path):
        return os.path.join(self._base_dir, path)

    def get_models_filepaths(self, name, version, model_path):
        return os.path.join(self._deltatwin_dir, name, version, model_path)

    def add_run_directory(self, run_id: uuid.UUID) -> None:
        path = os.path.join(self._run_dir, str(run_id))
        if not os.path.isdir(path):
            os.makedirs(path)

    def get_deltatwin_manifest(self, name: str, version: str) -> Manifest:
        path = os.path.join(
            self._deltatwin_dir, name, version, "manifest.json")
        if not os.path.isfile(path):
            raise FileNotFoundError(
                f"No manifest found for deltatwin: {name} version {version}")
        return parse(path)

    def get_deltatwin_workflow(self, name: str, version: str) -> dict:
        path = glob.glob(f"{self._deltatwin_dir}/{name}/{version}/workflow.*")
        if not path:
            raise FileNotFoundError(
                f"No workflow found for deltatwin: "
                f"{name} version {version}"
            )
        workflow = path[0]
        with open(workflow) as workflow_file:
            if workflow.endswith(".json"):
                return json.load(workflow_file)
            if workflow.endswith(".yaml") or workflow.endswith(".yml"):
                return yaml.safe_load(workflow_file)
        raise RuntimeError(f"Unsupported workflow: {workflow}")

    def get_data(self, run_id: uuid.UUID, job_id: str, basename: str) -> IO:
        path = os.path.join(self._run_dir, str(run_id), job_id, basename)
        return open(path, "rb")

    def set_data(
        self, run_id: uuid.UUID, job_id: str, basename: str, stream: IO
    ) -> str:
        path = os.path.join(self._run_dir, str(run_id), job_id, basename)
        os.makedirs(os.path.dirname(path))
        buf_size = 16 * 1024
        with open(path, "wb") as f:
            buf = stream.read(buf_size)
            while buf:
                f.write(buf)
                buf = stream.read(buf_size)
        return f"runs/{str(run_id)}/{job_id}/{basename}"

    def get_data_info(self, data_path) -> Dict:
        infos = {}
        path = os.path.join(self._base_dir, data_path)
        with open(path, "rb") as f:
            digest = hashlib.file_digest(f, "md5")
        infos["size"] = os.stat(path).st_size
        infos["checksum"] = f"md5@{digest.hexdigest()}"
        return infos

    def find_data(
        self, run_id: uuid.UUID, job_id: str, _glob: str
    ) -> List[AnyStr]:
        pattern = f"{self._run_dir}/{str(run_id)}/{job_id}/{_glob}"
        return [os.path.relpath(p, self._base_dir) for p in glob.glob(pattern)]

    def remove_run(self, run_id: uuid.UUID) -> None:
        path = os.path.join(self._run_dir, str(run_id))
        shutil.rmtree(path, ignore_errors=True)

    def push_deltatwin(self, directory, name: str, version: str) -> None:
        path = os.path.join(self._deltatwin_dir, name, version)
        self.LOGGER.info(f"pushing delta twin {name} version"
                         f" {version} into {path}")
        if not os.path.isdir(path):
            shutil.copytree(directory, path)

    def remove_deltatwin(self, name: str, version: str) -> None:
        path = os.path.join(self._deltatwin_dir, name, version)
        shutil.rmtree(path, ignore_errors=True)

    def has_deltatwin(self, name: str, version: str) -> bool:
        path = os.path.join(self._deltatwin_dir, name, version)
        return os.path.isdir(path)


class S3StorageManager(DeltaStorageManager):
    LOGGER = logging.Logger("S3StorageManager")

    def __init__(self, entry_point: str, key: str, secret: str, bucket: str):
        self._s3fs = s3fs.S3FileSystem(
            anon=False, endpoint_url=entry_point, key=key, secret=secret
        )
        self._s3 = boto3.client("s3",
                                endpoint_url=entry_point,
                                aws_access_key_id=key,
                                aws_secret_access_key=secret)
        self._bucket = bucket

    def get_full_path(self, path):
        return os.path.join("s3://", self._bucket, path)

    def get_models_filepaths(self, name, version, model_path):
        path = os.path.join("deltatwins", name, version, model_path)
        return self.get_full_path(path)

    def add_run_directory(self, run_id: uuid.UUID) -> None:
        directory = f"{self._bucket}/runs/{run_id}"
        if not self._s3fs.isdir(directory):
            self._s3fs.mkdirs(directory)

    def get_deltatwin_manifest(self, name: str, version: str) -> Manifest:
        manifest_path = f"{self._bucket}/deltatwins/{name}/{version}"
        if not self._s3fs.isdir(manifest_path):
            raise FileNotFoundError(f"Deltatwin {name} version "
                                    f"{version} not found")
        paths = self._s3fs.glob(os.path.join(manifest_path, "manifest.*"))
        with self._s3fs.open(paths[0], mode="rb") as manifest_file:
            return parse(manifest_file)

    def get_deltatwin_workflow(self, name: str, version: str) -> dict:
        glob_pattern = f"{self._bucket}/deltatwins/{name}/{version}/workflow.*"
        workflow_glob = self._s3fs.glob(glob_pattern)
        if not workflow_glob:
            raise FileNotFoundError(
                "No workflow found for deltatwin" f"{name} version {version}"
            )
        workflow = workflow_glob[0]
        with self._s3fs.open(workflow, mode="rb") as workflow_file:
            if workflow.endswith(".json"):
                return json.load(workflow_file)
            if workflow.endswith(".yml") or workflow.endswith(".yaml"):
                return yaml.safe_load(workflow_file)
        raise RuntimeError(
            "Invalid workflow file:" f"{os.path.basename(workflow)}"
        )

    def get_data(self, run_id: uuid.UUID, job_id: str, basename: str) -> IO:
        path = f"runs/{str(run_id)}/{job_id}/{basename}"
        try:
            params = {"Bucket": self._bucket, "Key": path}
            url = self._s3.generate_presigned_url(
                'get_object', Params=params, ExpiresIn=15
            )
            return urllib.request.urlopen(url)
        except ClientError as e:
            self.LOGGER.error(f'Download error: {e}')
            raise FileNotFoundError(f"No object found at: {path}")

    def set_data(
        self, run_id: uuid.UUID, job_id: str, basename: str, stream: IO
    ):
        rel_path = f"runs/{str(run_id)}/{job_id}/{basename}"
        self._s3.put_object(
            Bucket=self._bucket, Body=stream.read(), Key=rel_path
        )
        return rel_path

    def find_data(
        self, run_id: uuid.UUID, job_id: str, _glob: str
    ) -> List[AnyStr]:
        pattern = f"{self._bucket}/runs/{str(run_id)}/{job_id}/{_glob}"
        globs = self._s3fs.glob(pattern)
        return [os.path.relpath(p, start=self._bucket) for p in globs]

    def get_data_info(self, data_path) -> Dict:
        infos = {}
        response = self._s3.head_object(
            Bucket=self._bucket, Key=data_path, ChecksumMode="ENABLED"
        )
        infos["size"] = response["ContentLength"]
        # Checksum is stored in the Etag entry, surrounded by '"', hence [1:-1]
        infos["checksum"] = f"md5@{response['ETag'][1:-1]}"
        return infos

    def remove_run(self, run_id: uuid.UUID) -> None:
        directory = f"{self._bucket}/runs/{str(run_id)}"
        if self._s3fs.isdir(directory):
            self.LOGGER.info(f"Deleting run: {run_id}")
            self._s3fs.delete(directory, recursive=True)

    def push_deltatwin(self, directory, name: str, version: str) -> None:
        dest_dir = f"deltatwins/{name}/{version}"
        self.LOGGER.warning(f"Fetching deltatwin: {name} version {version}")
        for file in os.listdir(directory):
            self._s3.upload_file(
                Filename=os.path.join(directory, file),
                Bucket=self._bucket,
                Key=os.path.join(dest_dir, file),
            )

    def remove_deltatwin(self, name: str, version: str) -> None:
        directory = f"{self._bucket}/deltatwins/{name}/{version}"
        if not self._s3fs.isdir(directory):
            self.LOGGER.warning(f"Deleting deltatwin: "
                                f"{name} version {version}")
            self._s3fs.delete(directory, recursive=True)

    def has_deltatwin(self, name: str, version: str) -> bool:
        prefix = f"deltatwins/{name}/{version}"
        result = self._s3.list_objects_v2(Bucket=self._bucket, Prefix=prefix)
        return result.get('KeyCount', 0) > 0
