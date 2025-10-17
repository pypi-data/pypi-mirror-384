from delta.manifest.parser import (
    Copyright, Input, License, Manifest, ManifestParser, Model, Output,
    Resource
)


class ManifestParserV1v0(ManifestParser):
    @classmethod
    def parse_license(cls, data: dict) -> License:
        return License(
            name=data["name"],
            url=data['url'],
            description=data.get("description"),
            copyrights=[Copyright(**e) for e in data["copyrights"]]
        )

    @classmethod
    def parse_resource(cls, data: dict) -> Resource:
        return Resource(
            name=data["name"],
            type="url",
            value=data["source_url"]
        )

    @classmethod
    def parse_input(cls, data: dict) -> Input:
        raise NotImplementedError

    @classmethod
    def parse_output(cls, data: dict) -> Output:
        raise NotImplementedError

    @classmethod
    def parse_model(cls, data: dict) -> Model:
        return Model(
            path=data["path"],
            type=data["type"],
            parameters=data["parameters"]
        )

    @classmethod
    def parse(cls, data: dict) -> Manifest:
        resources = {}
        if "resources" in data:
            for resource in data["resources"]["items"]:
                resources[resource['name']] = cls.parse_resource(resource)

        models = {}
        if "models" in data:
            models["single_model"] = cls.parse_model(data["models"])

        return Manifest(
            name=data["name"],
            description=data["description"],
            license=cls.parse_license(data["license"]),
            resources=resources,
            models=models
        )
