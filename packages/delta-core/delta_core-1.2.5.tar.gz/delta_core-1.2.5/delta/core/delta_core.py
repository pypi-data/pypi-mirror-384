import logging
import os
from typing import Any

from delta.drive import DeltaDrive
from delta.manifest.manifest import read_manifest
from delta.runners.factory import create

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Delta")


class DeltaCore:
    def __init__(self):
        """
        TODO: Need to change IDrive and IRun
        => Need a real instance.
        """
        self._drive = DeltaDrive()
        self._run = None

    def run_start(self, **kwargs):
        if self._run is None:
            _manifest = read_manifest(
                os.path.join(self._drive.repo_directory, "manifest.json")
            )
            self._run = create(_manifest["models"])
            kwargs["resources"] = _manifest["resources"]
        logger.info("Job runner is starting...")
        self._run.start(**kwargs)
        logger.info("Done.")

    def drive_build(self, version, registry, no_cache=False):
        self._drive.docker_build(
            version=version, registry=registry, no_cache=no_cache
        )

    def set_verbosity_level(self, verbose_level):
        logger.setLevel(verbose_level)

    def close(self):
        pass

    def __enter__(self) -> "DeltaCore":
        return self

    def __exit__(self, *args: Any, **kwargs) -> None:
        self.close()
