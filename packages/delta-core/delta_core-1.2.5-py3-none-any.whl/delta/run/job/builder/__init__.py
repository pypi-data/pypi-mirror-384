import abc
import os
from typing import Any

from delta.manifest.parser import InputModel
from delta.run.api.model import PrimitiveParameterModel, DataParameterModel
from delta.run.utils import decrypt_with_rsa
from delta.run.config import Settings

_settings: Settings = None


def _get_private_key():
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings.private_key


class Placeholder(abc.ABC):
    @abc.abstractmethod
    def evaluate(self, secure: bool = False) -> Any:
        raise NotImplementedError


class InputModelPlaceholder(Placeholder):
    _separator: str = " "

    def __init__(self, input_model: InputModel, value: Any):
        super().__init__()
        self._input = input_model
        self._value = value
        self._factory = {
            "boolean": self.__evaluate_boolean,
            "integer": self.__evaluate_number,
            "number": self.__evaluate_number,
            "string": self.__evaluate_string,
            "secret": self.__evaluate_secret,
            "Data": self.__evaluate_data,
            "stdout": self.__evaluate_data,
        }

    def __evaluate_boolean(self) -> str:
        param: PrimitiveParameterModel | InputModel = (
                self._value or self._input
        )
        if param is not None and param.value is not None:
            value: bool | None = None
            if isinstance(param, InputModel):
                value = bool(param.value)
            if isinstance(param, PrimitiveParameterModel):
                value = param.value
            if self._input.prefix and value:
                return f"{self._input.prefix}"
        return ""

    def __evaluate_number(self) -> str:
        param: PrimitiveParameterModel | InputModel = (
                self._value or self._input
        )
        if param is not None and param.value is not None:
            if self._input.type == 'integer':
                value = int(param.value)
            else:
                value = float(param.value)
            if self._input.prefix:
                return f"{self._input.prefix}{self._separator}{value}"
            return str(value)
        return ""

    def __evaluate_string(self) -> str:
        param: PrimitiveParameterModel | InputModel = (
                self._value or self._input
        )
        if param is not None and param.value:
            if self._input.prefix:
                return f"{self._input.prefix}{self._separator}{param.value}"
            return param.value
        return ""

    def __evaluate_secret(self, secure: bool = False) -> str:
        value = self._value or self._input.value

        if value:
            decrypted_value = decrypt_with_rsa(
                value.secret_value, private_key=_get_private_key()
            )

            if secure:
                if self._input.prefix:
                    return f"{self._input.prefix}{self._separator}***"
                return "***"

            if self._input.prefix:
                return (
                    f"{self._input.prefix}"
                    f"{self._separator}"
                    f"{decrypted_value}"
                )

            return decrypted_value

        return ""

    def __evaluate_data(self) -> str:
        param: DataParameterModel | InputModel = self._value or self._input
        value: DataParameterModel | None = None
        if isinstance(param, DataParameterModel):
            value = param
        if isinstance(param, InputModel) and param.value is not None:
            value = DataParameterModel(**param.value)

        if value is not None:
            path = os.path.join('/s3', value.path)
            if self._input.prefix:
                return f"{self._input.prefix}{self._separator}{path}"
            return path

        return ""

    def evaluate(self, secure: bool = False) -> str:
        try:
            if self._input.type == 'secret':
                return self._factory[self._input.type](secure)
            return self._factory[self._input.type]()
        except KeyError:
            return ""


class JobBuilder(abc.ABC):
    @staticmethod
    def placeholder_factory(model_part: InputModel, value: Any) -> Placeholder:
        if isinstance(model_part, InputModel):
            return InputModelPlaceholder(model_part, value)
        raise NotImplementedError

    @abc.abstractmethod
    def generate_dockerfile(self) -> str:
        raise NotImplementedError

    @staticmethod
    def generate_dockerfile_ctx() -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def build_command(self):
        raise NotImplementedError
