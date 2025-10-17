from delta.manifest.parser import (
    Dependency,
    Input,
    License,
    Manifest,
    ManifestParser,
    Model,
    Output,
    Resource,
)
from delta.manifest.v1_1 import ManifestParserV1v1


class ManifestParserV1v2(ManifestParser):
    @classmethod
    def parse_license(cls, data: dict) -> License:
        return ManifestParserV1v1.parse_license(data)

    @classmethod
    def parse_resource(cls, data: dict) -> Resource:
        return ManifestParserV1v1.parse_resource(data)

    @classmethod
    def parse_input(cls, data: dict) -> Input:
        return ManifestParserV1v1.parse_input(data)

    @classmethod
    def parse_output(cls, data: dict) -> Output:
        return ManifestParserV1v1.parse_output(data)

    @classmethod
    def parse_model(cls, data: dict) -> Model:
        return ManifestParserV1v1.parse_model(data)

    @classmethod
    def parse_dependency(cls, data: dict) -> Dependency:
        return Dependency(**data)

    @classmethod
    def parse(cls, data: dict) -> Manifest:
        return Manifest(
            name=data["name"],
            owner=data["owner"],
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
            dependencies={
                k: cls.parse_dependency(v)
                for k, v in data.get("dependencies", {}).items()
            },
        )
