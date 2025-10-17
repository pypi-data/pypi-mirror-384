import sys
import os
import json
import jsonschema
from delta.manifest.constants import manifest_version
from delta.manifest.constants import manifest_schema_filename

manifest_minimum_sample = "minimum.json"


class ManifestException(Exception):
    """Raised when Error caught in manifest."""
    pass


def _schema_path(version=manifest_version):
    version = 'v' + version.replace('.', "_")
    return os.path.join(os.path.dirname(__file__), version)


def _find_schema_path(version=manifest_version,
                      schema_filename=manifest_schema_filename) -> str:
    f"""
    Build the schema path according to its version.
    The file presence is not checked here.
    :param version: the version of the schema (default :{manifest_version})
    :param schema_filename: the filename retrieved form this package
      (default: {manifest_schema_filename})
    :return: the full path to the schema file
    """
    # retrieve the schema source path
    # Expected schemas are stored into their version folders.
    if version is None:
        version = manifest_version
    if schema_filename is None:
        schema_filename = manifest_schema_filename

    return os.path.join(_schema_path(version), schema_filename)


def _read_json_file(path):
    with open(path) as fp:
        return json.load(fp)


def read_manifest(path='manifest.json'):
    """
    Read the manifest json file to return dict instance of the decoded file.
    :param path: the path to the manifest
    :return: the json dict instance
    """
    # read the given manifest
    return _read_json_file(path)


def write_manifest(path='manifest.json', content=None,
                   version=manifest_version):
    """
    Write the manifest into path destination.
    :param path: the path to the manifest. If the path already exist, file is
       overwritten.
    :param content: the manifest content dict (if provided, this content is
       not checked before written)
    :param version: the version of the manifest to be written (ignored if
       content is provided).
    :return: the generated manifest path
    """
    if not content:
        try:
            content = _read_json_file(
                os.path.join(os.path.dirname(
                    _find_schema_path(version=version)),
                    manifest_minimum_sample))
        except FileNotFoundError as e:
            raise ManifestException(
                f"Minimum manifest content not found for "
                f"version \"{version}\"") from e
    # read the given manifest
    with open(path, "w") as outfile:
        json.dump(content, outfile)

    return path


def check_manifest(data: dict, verbose=False, schema=None, version=None) \
        -> bool:
    f"""
    Silently or verbosely check the manifest. The schema used for validation
     is the default defined into constants.current_version module
     ({manifest_version}).

    :param data: content to validate.
    :param verbose: verbose check if true, no output otherwise.
    :param schema: provide an other json schema to check the manifest.
    :param version: define the schema version for validation (ignored if
       schema is provided).
    :return: True if manifest of valid, false otherwise.
    """
    if schema is None:
        schema = _read_json_file(_find_schema_path(version=version))

    validator = jsonschema.validators.validator_for(schema)(schema)
    if verbose:
        errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
        for error in errors:
            print(f"- {error.message}")
        return not errors
    else:
        return validator.is_valid(data)


if __name__ == '__main__':
    globals()[sys.argv[1]]()
