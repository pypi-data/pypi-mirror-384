from delta.manifest.parser import (
    Input, InputModel, License, Manifest, ManifestParser, Model, Output,
    OutputModel, Resource
)
from delta.manifest.v1_0 import ManifestParserV1v0


class ManifestParserV1v1(ManifestParser):
    @classmethod
    def parse_license(cls, data: dict) -> License:
        return ManifestParserV1v0.parse_license(data)

    @classmethod
    def parse_resource(cls, data: dict) -> Resource:
        return Resource(**data)

    @classmethod
    def parse_input(cls, data: dict) -> Input:
        return Input(**data)

    @classmethod
    def parse_output(cls, data: dict) -> Output:
        return Output(**data)

    @classmethod
    def parse_model(cls, data: dict) -> Model:
        return Model(
            path=data["path"],
            type=data["type"],
            parameters=data["parameters"],
            inputs={
                k: InputModel(**{"name": k, **v})
                for k, v in data.get("inputs", {}).items()
            },
            outputs={
                k: OutputModel(**{"name": k, **v})
                for k, v in data.get("outputs", {}).items()
            }
        )

    @classmethod
    def parse(cls, data: dict) -> Manifest:
        return Manifest(
            name=data["name"],
            description=data["description"],
            license=cls.parse_license(data["license"]),
            resources={
                k: cls.parse_resource({"name": k, **v})
                for k, v in data.get("resources", {}).items()
            },
            inputs={
                k: cls.parse_input({"name": k, **v})
                for k, v in data.get("inputs", {}).items()
            },
            outputs={
                k: cls.parse_output({"name": k, **v})
                for k, v in data.get("outputs", {}).items()
            },
            models={
                k: cls.parse_model(v)
                for k, v in data.get("models", {}).items()
            },
            dependencies=data.get("dependencies", [])
        )
