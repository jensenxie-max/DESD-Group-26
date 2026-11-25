"""Reuse the checked Camunda REST contract with a separate worker identity."""

from sprint2_runtime.api import CamundaClient as Sprint2Client, CamundaError


class CamundaClient(Sprint2Client):
    def activate(self, job_type, *, worker="desd-sprint3", max_jobs=10):
        return super().activate(job_type, worker=worker, max_jobs=max_jobs)


__all__ = ["CamundaClient", "CamundaError"]
