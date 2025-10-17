import datetime as dt
import uuid

import docker.errors

from delta.run.db.orm import RunStatus
from delta.run.job import Job, JobService


class DockerJobService(JobService):
    def __init__(self, registry: str, keep_container: bool = False):
        super().__init__()
        self._registry = registry
        self._cli = docker.from_env()
        self._keep_container = not keep_container
        self._last_check = int(dt.datetime.now(dt.timezone.utc).timestamp())

    async def execute_job(self, job: Job):
        tag = f"{self._registry}/{job.image.tag}"
        volumes = {e.src: {"bind": e.dest, "mode": "ro"} for e in job.inputs}
        if job.outputs:
            path = job.outputs[0].dest
            volumes[path] = {"bind": f"/outputs/{str(job.id)}", "mode": "rw"}
        try:
            outputs = " ".join([e.src for e in job.outputs])
            final_command = job.command
            if outputs:
                final_command += f" && cp {outputs} /outputs/{str(job.id)}"
            cmd = [
                "/bin/bash",
                "-c",
                final_command
            ]
            self._cli.containers.run(
                image=tag,
                command=cmd,
                volumes=volumes,
                detach=True,
                labels={"app": "delta-run", "jobId": str(job.id)},
                remove=self._keep_container
            )
            self._jobs[job.id] = job
        except Exception as ex:
            self._logger.error(
                "Failed to execute job %s: %s", str(job.id), str(ex)
            )
            job.status = RunStatus.ERROR

    def check_jobs(self) -> None:
        now = int(dt.datetime.now(dt.timezone.utc).timestamp())

        for event in self._cli.events(
            since=self._last_check,
            until=now,
            decode=True,
            filters={"label": "app=delta-run"}
        ):
            attributes = event["Actor"]["Attributes"]
            # retrieve associated job
            job_id = uuid.UUID(attributes["jobId"])
            job = self._jobs.get(job_id)
            if job is None:
                self._logger.warning("Unknown job %s", job_id)
            # check event
            if event["status"] == "die":
                rc = int(attributes["exitCode"])
                job.status = RunStatus.SUCCESS if rc == 0 else RunStatus.ERROR
                del self._jobs[job_id]

        # update last check time
        self._last_check = now

    def shutdown(self):
        self._cli.close()
