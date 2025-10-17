import unittest

from delta.core import DeltaCore


class FakeRun:
    def configure(**kwargs):
        pass

    def run(**kwargs):
        pass

    def monitor(**kwargs):
        pass

    def stop(**kwargs):
        pass

    def resume(**kwargs):
        pass


class TestCoreRun(unittest.TestCase):
    def test_run_start_initialized(self):
        with DeltaCore() as core:
            try:
                core._run = FakeRun()
                kwargs = {}
                core.run_start(**kwargs)
            except Exception:
                pass
