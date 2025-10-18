from __future__ import annotations

from typing import AsyncGenerator

import httpx

from codeapi.client._base import ClientBase
from codeapi.types import (
    CodeInfo,
    CodeType,
    CodeZip,
    Job,
    JobResult,
    JobStage,
    JobStatus,
    JsonData,
    ServerStatus,
    ServicesHealth,
    StreamOutput,
    TokenRequest,
    TokenResponse,
)

from ._app import AsyncAppClient
from ._cli import AsyncCliClient
from ._code import AsyncCodeClient
from ._jobs import AsyncJobsClient
from ._mcp import AsyncMcpClient
from ._web import AsyncWebClient


class AsyncClient(ClientBase):
    """Async CodeAPI Client"""

    def __init__(self, base_url: str, api_key: str = ""):
        """Initializes the async CodeAPI Client.

        Args:
            base_url (str): The base URL of the CodeAPI.
            api_key (str): The CodeAPI key.
        """
        super().__init__(base_url=base_url, api_key=api_key)

        self.code = AsyncCodeClient(self)
        self.jobs = AsyncJobsClient(self)
        self.mcp = AsyncMcpClient(self)
        self.cli = AsyncCliClient(self)
        self.app = AsyncAppClient(self)
        self.web = AsyncWebClient(self)

    async def is_healthy(self) -> bool:
        """Checks if the server is healthy.

        Returns:
            bool: True if the server is healthy, False otherwise.
        """
        url = f"{self.base_url}/server/status"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.api_key_header)
                response.raise_for_status()
                return ServerStatus(**response.json()).is_healthy
            except httpx.HTTPStatusError:
                return False

    async def get_services_health(self) -> ServicesHealth:
        """Gets the health of services.

        Returns:
            ServicesHealth: The health of services.

        Raises:
            HTTPException: If the request fails.
        """
        url = f"{self.base_url}/services/health"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.api_key_header)
                response.raise_for_status()
                return ServicesHealth(**response.json())
            except httpx.HTTPStatusError as e:
                raise self._get_http_exception(httpx_error=e)

    async def generate_token(
        self, user: str, ulid: str | None = None, ttl: int = -1
    ) -> str:
        """Generates a new API token

        Args:
            user (str): The unique identifier of the user.
            ulid (str | None, optional): The ULID for the token.
            ttl (int, optional): Time-to-live for the token in seconds.

        Returns:
            str: The generated API token.
        """
        url = f"{self.base_url}/api/token"
        async with httpx.AsyncClient() as client:
            try:
                token_request = TokenRequest(user=user, ulid=ulid, ttl=ttl)
                response = await client.post(
                    url,
                    headers=self.api_key_header,
                    json=token_request.model_dump(),
                )
                response.raise_for_status()
                token_response = TokenResponse(**response.json())
                return token_response.token
            except httpx.HTTPStatusError as e:
                raise self._get_http_exception(httpx_error=e)

    async def clear_db(self) -> None:
        """Clears the database.

        Raises:
            HTTPException: If the request fails.
        """
        url = f"{self.base_url}/db/clear"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=self.api_key_header)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise self._get_http_exception(httpx_error=e)

    async def get_job(self, job_id: str) -> Job:
        """Gets a job.

        Args:
            job_id (str): The ID of the job.

        Returns:
            Job: The job.
        """
        return await self.jobs.get(job_id)

    async def list_jobs(
        self, job_type=None, job_status=None, job_stage=None
    ) -> list[Job]:
        """Gets a list of jobs.

        Args:
            job_type: Filter by job type.
            job_status: Filter by job status.
            job_stage: Filter by job stage.

        Returns:
            list[Job]: List of jobs.
        """
        return await self.jobs.list(
            job_type=job_type, job_status=job_status, job_stage=job_stage
        )

    async def get_job_status(self, job_id: str) -> JobStatus:
        """Gets the status of a job.

        Args:
            job_id (str): The ID of the job.

        Returns:
            JobStatus: The status of the job.
        """
        return await self.jobs.get_status(job_id)

    async def get_job_stage(self, job_id: str) -> JobStage:
        """Gets the stage of a job.

        Args:
            job_id (str): The ID of the job.

        Returns:
            JobStatus: The status of the job.
        """
        return await self.jobs.get_stage(job_id)

    async def get_job_error(self, job_id: str) -> str | None:
        """Gets the error message of a job.

        Args:
            job_id (str): The ID of the job.

        Returns:
            str | None: The error message of the job, or None if no error.
        """
        return await self.jobs.get_error(job_id)

    async def get_job_code_id(self, job_id: str) -> str | None:
        """Gets the code ID associated with a job.

        Args:
            job_id (str): The ID of the job.

        Returns:
            str | None: The code ID associated with the job, or None if no code ID.
        """
        return await self.jobs.get_code_id(job_id)

    async def get_job_result(
        self, job_id: str, zip_path: str | None = None
    ) -> JobResult:
        """Gets the result of a job.

        Args:
            job_id (str): The ID of the job.
            zip_path: The path to save the result zip file.

        Returns:
            JobResult: The job result.
        """
        return await self.jobs.get_result(job_id, zip_path)

    async def terminate_job(self, job_id: str) -> None:
        """Terminates a job.

        Args:
            job_id (str): The ID of the job.
        """
        return await self.jobs.terminate(job_id)

    async def stream_job_output(
        self, job_id: str, read_timeout: int = 60
    ) -> AsyncGenerator[StreamOutput, None]:
        """Stream output of a job.

        Args:
            job_id (str): The ID of the job.
            read_timeout: Read timeout for the stream.

        Returns:
            AsyncGenerator[StreamOutput, None]: Stream output generator.
        """
        return self.jobs.stream_output(job_id, read_timeout)

    async def await_job_stage(
        self,
        job_id: str,
        stage: JobStage = JobStage.POST_RUNNING,
        timeout: int | None = None,
    ) -> Job:
        """Waits for a job to reach a specific stage.

        Args:
            job_id (str): The ID of the job.
            stage: The stage to wait for.
            timeout: Maximum time to wait in seconds.

        Returns:
            Job: The final job object.
        """
        return await self.jobs.await_stage(job_id, timeout, stage)

    async def upload_code(
        self,
        code_zip: CodeZip,
        code_name: str,
        code_type: CodeType,
        metadata: JsonData | dict | None = None,
    ) -> str:
        """Upload code.

        Args:
            code_zip (CodeZip): The code zip.
            code_name (str): The name of the code.
            code_type (CodeType): The type of the code.
            metadata (JsonData | dict | None): The JSON metadata of the code.

        Returns:
            str: The code ID.
        """
        return await self.code.upload(code_zip, code_name, code_type, metadata)

    async def download_code(self, code_id: str, zip_path: str | None = None) -> CodeZip:
        """Download code.

        Args:
            code_id (str): The code ID.
            zip_path: The path to save the code zip file to.

        Returns:
            CodeZip: The downloaded code zip.
        """
        return await self.code.download(code_id, zip_path)

    async def get_code_info(self, code_id: str) -> CodeInfo:
        """Gets the code info.

        Args:
            code_id (str): The code ID.

        Returns:
            CodeInfo: The code info.
        """
        return await self.code.get_info(code_id)

    async def list_code_info(self, code_type: CodeType | None = None) -> list[CodeInfo]:
        """Gets list of code infos.

        Args:
            code_type: The type of code to list.

        Returns:
            list[CodeInfo]: The list of code infos.
        """
        return await self.code.list_info(code_type)

    async def delete_code(self, code_id: str) -> str:
        """Deletes code by code_id.

        Args:
            code_id (str): The code ID.

        Returns:
            str: Confirmation message.
        """
        return await self.code.delete(code_id)

    async def get_code_metadata(self, code_id: str) -> JsonData:
        """Gets code metadata.

        Args:
            code_id (str): The ID of the code.

        Returns:
            JsonData: The metadata.
        """
        return await self.code.get_metadata(code_id)

    async def ingest_code(
        self,
        code_zip: CodeZip,
        code_name: str,
        code_type: CodeType,
        metadata: JsonData | dict | None = None,
        build_pexenv: bool = False,
        pexenv_python: str | None = None,
    ) -> Job:
        """Starts a code ingestion job.

        Args:
            code_zip: The code zip.
            code_name (str): The name of the code.
            code_type: The type of the code.
            metadata: The JSON metadata of the code.
            build_pexenv (bool): Whether to build the pex venv.
            pexenv_python: Python interpreter for the pex venv.

        Returns:
            Job: The code ingestion job.
        """
        return await self.code.ingest(
            code_zip, code_name, code_type, metadata, build_pexenv, pexenv_python
        )


__all__ = [
    "AsyncClient",
]
