"""Small Camunda 8.10 Orchestration Cluster REST client.

Endpoint/body shapes were checked against the official 8.10.16 docs tag,
api/camunda/version-8.10/{jobs,messages,process-instances,user-tasks,deployments}.yaml:
https://github.com/camunda/camunda-docs/tree/8.10.16/api/camunda/version-8.10
Schema agreement is not proof of a successful engine integration run.
"""

import base64
import json
import mimetypes
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import uuid


class CamundaError(RuntimeError):
    def __init__(self, status, detail):
        self.status = status
        self.detail = detail
        super().__init__(f"Camunda HTTP {status}: {detail}")


class CamundaClient:
    def __init__(self, base_url="http://localhost:8080/v2", *, token=None,
                 username=None, password=None, timeout=30, tenant_id=None):
        parsed = urllib.parse.urlparse(base_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username:
            raise ValueError("Use an http(s) REST base URL without embedded credentials")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.tenant_id = tenant_id
        self.headers = {"Accept": "application/json"}
        if token:
            self.headers["Authorization"] = "Bearer " + token
        elif username is not None and password is not None:
            value = base64.b64encode(f"{username}:{password}".encode()).decode()
            self.headers["Authorization"] = "Basic " + value

    @classmethod
    def from_env(cls, base_url=None):
        return cls(base_url or os.environ.get("CAMUNDA_REST_URL", "http://localhost:8080/v2"),
                   token=os.environ.get("CAMUNDA_TOKEN"),
                   username=os.environ.get("CAMUNDA_USERNAME"),
                   password=os.environ.get("CAMUNDA_PASSWORD"),
                   tenant_id=os.environ.get("CAMUNDA_TENANT_ID"))

    def request(self, method, path, body=None, *, content_type="application/json"):
        data = body if isinstance(body, bytes) else (
            json.dumps(body, allow_nan=False).encode() if body is not None else None)
        headers = dict(self.headers)
        if data is not None:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                value = response.read()
                return json.loads(value) if value else {}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                problem = json.loads(raw)
                detail = problem.get("detail") or problem.get("title") or str(exc.reason)
            except (ValueError, AttributeError):
                detail = str(exc.reason)
            raise CamundaError(exc.code, detail) from None

    def activate(self, job_type, *, worker="desd-sprint2", max_jobs=10):
        body = {"type": job_type, "worker": worker, "timeout": 60000,
                "maxJobsToActivate": max_jobs, "requestTimeout": -1}
        if self.tenant_id:
            body["tenantIds"] = [self.tenant_id]
        return self.request("POST", "/jobs/activation", body).get("jobs", [])

    def complete(self, job_key, variables):
        return self.request("POST", f"/jobs/{job_key}/completion", {"variables": variables})

    def fail(self, job_key, retries, error):
        return self.request("POST", f"/jobs/{job_key}/failure",
                            {"retries": max(0, retries), "errorMessage": str(error)[:2000], "retryBackOff": 1000})

    def publish(self, name, request_id, variables, message_id):
        body = {"name": name, "correlationKey": request_id, "variables": variables,
                "timeToLive": 3600000, "messageId": str(message_id)}
        if self.tenant_id:
            body["tenantId"] = self.tenant_id
        return self.request("POST", "/messages/publication", body)

    def start(self, process_id, variables):
        body = {"processDefinitionId": process_id, "processDefinitionVersion": -1, "variables": variables}
        if self.tenant_id:
            body["tenantId"] = self.tenant_id
        return self.request("POST", "/process-instances", body)

    def complete_user_task(self, task_key, variables):
        return self.request("POST", f"/user-tasks/{task_key}/completion", {"variables": variables})

    def deploy(self, paths):
        boundary = "desd-" + uuid.uuid4().hex
        pieces = []
        for filename in paths:
            path = Path(filename)
            name = path.name.replace('"', "")
            mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
            pieces.extend([f'--{boundary}\r\nContent-Disposition: form-data; name="resources"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n'.encode(), path.read_bytes(), b"\r\n"])
        if self.tenant_id:
            pieces.append(f'--{boundary}\r\nContent-Disposition: form-data; name="tenantId"\r\n\r\n{self.tenant_id}\r\n'.encode())
        pieces.append(f"--{boundary}--\r\n".encode())
        return self.request("POST", "/deployments", b"".join(pieces), content_type=f"multipart/form-data; boundary={boundary}")
