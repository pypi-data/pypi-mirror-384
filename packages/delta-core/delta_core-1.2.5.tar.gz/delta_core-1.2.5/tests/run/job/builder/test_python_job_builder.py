import os
import unittest

from delta.manifest.parser import Model, InputModel
from delta.run.api.model import PrimitiveParameterModel, DataParameterModel
from delta.run.job.builder.python_builder import PythonRunner, SoftwarePackage


class TestPythonJobBuilder(unittest.TestCase):
    _model: Model = None

    @classmethod
    def setUpClass(cls):
        cls._model = Model(
            path="models/fake_model",
            type="python",
            parameters={},
            inputs={}
        )

    def test_build_command_bool(self):
        self._model.inputs = {
            "flag1": InputModel(
                name="flag1", type="boolean", value=True, prefix='-f1'),
            "flag2": InputModel(
                name="flag2", type="boolean", value=False, prefix='-f2'),
            "flag3": InputModel(
                name="flag3", type="boolean", prefix='-f3'),
        }
        self._model.parameters["command"] = (
            "test $(inputs.flag1) $(inputs.flag2) $(inputs.flag3)"
        )
        builder = PythonRunner(self._model)

        # not input provided
        params = {"inputs": {}}
        actual = builder.build_command(**params)
        self.assertEqual("test -f1", actual)

        # input flag1 set to False
        params["inputs"]["flag1"] = PrimitiveParameterModel(
            name="flag1", type="boolean", value=False
        )
        actual = builder.build_command(**params)
        self.assertEqual("test", actual)
        del params["inputs"]["flag1"]

        # intput flag2 set to True
        params["inputs"]["flag2"] = PrimitiveParameterModel(
            name="flag2", type="boolean", value=True
        )
        actual = builder.build_command(**params)
        self.assertEqual("test -f1 -f2", actual)
        del params["inputs"]["flag2"]

        # intput flag3 set to False
        params["inputs"]["flag3"] = PrimitiveParameterModel(
            name="flag2", type="boolean", value=False
        )
        actual = builder.build_command(**params)
        self.assertEqual("test -f1", actual)
        del params["inputs"]["flag3"]

        # intput flag3 set to True
        params["inputs"]["flag3"] = PrimitiveParameterModel(
            name="flag2", type="boolean", value=True
        )
        actual = builder.build_command(**params)
        self.assertEqual("test -f1 -f3", actual)
        del params["inputs"]["flag3"]

    def test_build_command_int(self):
        self._model.inputs = {
            "n": InputModel(name="n", type="integer", value=3, prefix='-n'),
            "i": InputModel(name="i", type="integer", prefix='-i'),
            "x": InputModel(name="x", type="integer"),
        }
        self._model.parameters["command"] = (
            "test $(inputs.n) $(inputs.i) $(inputs.x)"
        )
        builder = PythonRunner(self._model)

        params = {"inputs": {}}
        expected = "test -n 3"
        actual = builder.build_command(**params)
        self.assertEqual(expected, actual)

        params = {"inputs": {
            "n": PrimitiveParameterModel(name="n", type="integer", value=42)
        }}
        expected = "test -n 42"
        actual = builder.build_command(**params)
        self.assertEqual(expected, actual)

        params = {"inputs": {
            "n": PrimitiveParameterModel(name="n", type="integer", value=5),
            "i": PrimitiveParameterModel(name="i", type="integer", value=7)
        }}
        expected = "test -n 5 -i 7"
        actual = builder.build_command(**params)
        self.assertEqual(expected, actual)

        params = {"inputs": {
            "x": PrimitiveParameterModel(name="x", type="integer", value=31),
        }}
        expected = "test -n 3 31"
        actual = builder.build_command(**params)
        self.assertEqual(expected, actual)

    def test_build_command_string(self):
        self._model.inputs = {
            "t": InputModel(name="a", type="string", value="tab", prefix='-t'),
            "o": InputModel(name="b", type="string", prefix='-o'),
            "f": InputModel(name="b", type="string"),
        }
        self._model.parameters["command"] = (
            "test $(inputs.t) $(inputs.o) $(inputs.f)"
        )
        builder = PythonRunner(self._model)

        params = {"inputs": {}}
        expected = "test -t tab"
        actual = builder.build_command(**params)
        self.assertEqual(expected, actual)

        params = {"inputs": {
            "t": PrimitiveParameterModel(
                name="t", type="string", value="space"
            ),
        }}
        expected = "test -t space"
        actual = builder.build_command(**params)
        self.assertEqual(expected, actual)

        params = {"inputs": {
            "o": PrimitiveParameterModel(
                name="o", type="string", value="stdout"
            ),
        }}
        expected = "test -t tab -o stdout"
        actual = builder.build_command(**params)
        self.assertEqual(expected, actual)

        params = {"inputs": {
            "f": PrimitiveParameterModel(
                name="f", type="string", value="filename"
            ),
        }}
        expected = "test -t tab filename"
        actual = builder.build_command(**params)
        self.assertEqual(expected, actual)

    def test_build_command_data(self):
        self._model.inputs = {
            "d": InputModel(name="d", type="Data", prefix='-d'),
            "e": InputModel(name="e", type="Data", prefix='-e', value={
                "name": "e",
                "url": "/path/to/.env",
                "path": ".env"
            }),
            "f": InputModel(name="f", type="Data"),
        }
        self._model.parameters["command"] = (
            "test $(inputs.d) $(inputs.e) $(inputs.f)"
        )
        dir_path = 'path/to/dirname'
        file_path = 'path/to/filename'
        env_path = 'path/to/file.env'
        builder = PythonRunner(self._model)

        params = {"inputs": {}}
        expected = f"test -e /s3/.env"
        actual = builder.build_command(**params)
        self.assertEqual(expected, actual)

        params = {"inputs": {
            "d": DataParameterModel(
                name="d", url=f'http://test.net', path=dir_path
            ),
            "e": DataParameterModel(
                name="e", url=f'http://test.net', path=env_path
            ),
            "f": DataParameterModel(
                name="f", url=f'http://test.net', path=file_path
            ),
        }}
        expected = f"test -d /s3/{dir_path} -e /s3/{env_path} /s3/{file_path}"
        actual = builder.build_command(**params)
        self.assertEqual(expected, actual)

    def test_build_dockerfile(self):
        expected = (
            "FROM --platform=linux/amd64 python:3.13-slim-trixie\n"
            "COPY requirements.txt /root/\n"
            "ENV MY_ENV=test\n"
            "RUN apt-get update &&\\\n"
            "\tapt-get install --no-install-recommends -y g++=4:12.2.0-3 "
            "gdal-bin libgdal-dev &&\\\n"
            "\tapt-get clean &&\\\n"
            "\trm -rf /var/apt/lists/* &&\\\n"
            "\tpip install --no-cache-dir -r /root/requirements.txt &&\\\n"
            "\tpip install --no-cache-dir drb-image-sentinel2==1.0.0 "
            "numpy awscli==1.32.20\n"
            "COPY . /delta\n"
            "WORKDIR /delta\n"
        )
        self._model.parameters["pythonVersion"] = "3.13"
        self._model.parameters["aptRequirements"] = [
            {"name": "g++", "version": "4:12.2.0-3"},
            {"name": "gdal-bin"},
            {"name": "libgdal-dev"},
        ]
        self._model.parameters["pipRequirementFiles"] = [
            "requirements.txt",
        ]
        self._model.parameters["pipRequirements"] = [
            {"name": "drb-image-sentinel2", "version": "1.0.0"},
            {"name": "numpy"},
        ]
        self._model.parameters["environment"] = {
            "MY_ENV": "test",
        }
        builder = PythonRunner(self._model)
        actual = builder.generate_dockerfile()
        self.assertEqual(expected, actual)
