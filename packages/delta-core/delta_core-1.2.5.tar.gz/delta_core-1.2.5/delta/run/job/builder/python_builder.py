import dataclasses
import io
import re
from typing import List

from delta.manifest.parser import Model
from delta.run.job.builder import JobBuilder


@dataclasses.dataclass
class SoftwarePackage:
    name: str
    version: str | None = None

    def render(self, sep: str = "=") -> str:
        return f"{self.name}{sep}{self.version}" if self.version else self.name


class PythonRunner(JobBuilder):
    def __init__(self, model: Model):
        self.model = model

    @staticmethod
    def __build_run_command(
            apt_requirements: List[SoftwarePackage],
            pip_requirements: List[SoftwarePackage],
            pip_requirement_files: List[str],
    ) -> str:
        run = []
        if apt_requirements:
            segment = " ".join([x.render("=") for x in apt_requirements])
            run.append("apt-get update")
            run.append(f"apt-get install --no-install-recommends -y {segment}")
            run.append("apt-get clean")
            run.append("rm -rf /var/apt/lists/*")

        if pip_requirement_files:
            segment = [f"-r /root/{f}" for f in pip_requirement_files]
            run.append(f"pip install --no-cache-dir {' '.join(segment)}")

        if pip_requirements:
            segment = " ".join([x.render("==") for x in pip_requirements])
            run.append(f"pip install --no-cache-dir {segment}")
        return " &&\\\n\t".join(run)

    def generate_dockerfile(self) -> str:
        params = self.model.parameters
        python_version = params['pythonVersion'].split(".")
        if len(python_version) != 2:
            raise ValueError(
                "Parameter 'pythonVersion' must be in format 3.x and not 3.x.y"
            )
        major, minor = python_version
        if major != "3":
            raise ValueError("Only Python 3.x versions are supported")
        if int(minor) < 9:
            raise ValueError("Only Python3 version 9 and above are supported")

        with io.StringIO() as buf:
            buf.write(
                "FROM --platform=linux/amd64 "
                f"python:{major}.{minor}-slim-trixie\n"
            )
            # copying requirement files if necessary
            if params.get("pipRequirementFiles"):
                requirement_files = " ".join(params["pipRequirementFiles"])
                buf.write(f"COPY {requirement_files} /root/\n")
            # prepare command
            apt_requirements = [
                SoftwarePackage(**e) for e in params.get("aptRequirements", [])
            ]
            pip_requirements = [
                SoftwarePackage(**e) for e in params.get("pipRequirements", [])
            ]
            # FIXME remove this when no additional copy will no be necessary
            pip_requirements.append(SoftwarePackage(
                name="awscli", version="1.32.20"
            ))
            if params.get("environment"):
                for key, value in params.get("environment", {}).items():
                    buf.write(f'ENV {key}={value}\n')
            run_command = self.__build_run_command(
                apt_requirements=apt_requirements,
                pip_requirements=pip_requirements,
                pip_requirement_files=params.get("pipRequirementFiles", []),
            )
            if run_command:
                buf.write(f"RUN {run_command}\n")
            buf.write("COPY . /delta\n")
            buf.write("WORKDIR /delta\n")
            return buf.getvalue()

    def build_command(self, secure: bool = False, **kwargs) -> str:
        cmd_pattern = self.model.parameters["command"]
        evaluated_cmd = []
        for cmd_segment in cmd_pattern.split(" "):
            m = re.match(
                r"\$\(([a-z][A-Za-z0-9_-]*)(\.[a-z][A-Za-z0-9_-]*)*\)",
                cmd_segment
            )
            if m:
                keys = m.group()[2:-1].split(".")
                model_part = getattr(self.model, keys[0])
                model_part = model_part[keys[1]]
                value = kwargs[keys[0]].get(keys[1])
                placeholder = self.placeholder_factory(model_part, value)
                evaluated_cmd.append(placeholder.evaluate(secure))
            else:
                evaluated_cmd.append(cmd_segment)
        return " ".join(evaluated_cmd).strip().replace("  ", " ")
