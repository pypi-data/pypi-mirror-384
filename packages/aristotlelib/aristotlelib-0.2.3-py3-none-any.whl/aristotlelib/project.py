import asyncio
import logging
import pydantic  # type: ignore
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import cast, overload, Literal

from aristotlelib import api_request, local_file_utils

# Set up logger for this module
logger = logging.getLogger("aristotle")

MAX_FILES_PER_REQUEST = 10


class ProjectStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class Project(pydantic.BaseModel):
    project_id: str
    status: ProjectStatus
    created_at: datetime

    @classmethod
    async def from_id(cls, project_id: str) -> "Project":
        project = Project(
            project_id=project_id,
            status=ProjectStatus.NOT_STARTED,
            created_at=datetime.now(),
        )
        await project.refresh()
        return project

    @classmethod
    async def create(
        cls,
        context_file_paths: list[Path] | list[str] | None = None,
        validate_lean_project_root: bool = True,
    ) -> "Project":
        """Create a new project.

        Args:
            context_file_paths: List of file paths to include in the project as context.
            validate_lean_project_root: Whether to validate that these files are part of a valid Lean project.
               Strongly recommended to set to True, but not required if you just want to reference a small number of
               other imported files but don't have a working Lean project.
        """
        context_file_paths = context_file_paths or []
        if len(context_file_paths) > MAX_FILES_PER_REQUEST:
            raise ValueError(
                f"Maximum number of files to upload per request is {MAX_FILES_PER_REQUEST}"
            )

        file_paths = local_file_utils.normalize_and_dedupe_paths(context_file_paths)
        project_root = None
        if validate_lean_project_root and file_paths:
            example_file = file_paths[0]
            project_root = local_file_utils.find_lean_project_root(example_file)

        local_file_utils.validate_local_file_paths(
            file_paths, project_root=project_root
        )

        files_for_upload = local_file_utils.get_files_for_upload(
            file_paths, project_root=project_root
        )
        async with api_request.AristotleRequestClient() as client:
            response = await client.post(
                "/project",
                files=[("context", file) for file in files_for_upload],
            )
            return cls.model_validate(response.json())

    async def add_context(
        self,
        context_file_paths: list[Path] | list[str],
        batch_size: int = MAX_FILES_PER_REQUEST,
        validate_lean_project_root: bool = True,
    ) -> None:
        assert len(context_file_paths) > 0, "No context files provided"
        file_paths = local_file_utils.normalize_and_dedupe_paths(context_file_paths)

        project_root = None
        if validate_lean_project_root:
            example_file = file_paths[0]
            project_root = local_file_utils.find_lean_project_root(example_file)

        local_file_utils.validate_local_file_paths(
            file_paths, project_root=project_root
        )

        async with api_request.AristotleRequestClient() as client:
            for i in range(0, len(file_paths), batch_size):
                batch = file_paths[i : i + batch_size]
                await self._add_context(client, batch, project_root=project_root)
                num_complete = min(i + batch_size, len(file_paths))
                logger.info(
                    f"{num_complete} of {len(file_paths)} context files uploaded"
                )

    async def _add_context(
        self,
        client: api_request.AristotleRequestClient,
        context_file_paths: list[Path],
        project_root: Path | None = None,
    ) -> None:
        if len(context_file_paths) > MAX_FILES_PER_REQUEST:
            raise ValueError(
                f"Cannot upload more than {MAX_FILES_PER_REQUEST} files at once. Got {len(context_file_paths)}"
            )
        if len(context_file_paths) == 0:
            logger.warning(f"No context files provided for project {self.project_id}")
            return

        local_file_utils.validate_local_file_paths(
            context_file_paths, project_root=project_root
        )

        files_for_upload = local_file_utils.get_files_for_upload(
            context_file_paths, project_root=project_root
        )

        response = await client.post(
            f"/project/{self.project_id}/context",
            files=[("context", file) for file in files_for_upload],
        )
        self._update_from_response(response.json())

    @overload
    async def solve(self, *, input_file_path: Path | str) -> None: ...

    @overload
    async def solve(self, *, input_content: str) -> None: ...

    async def solve(
        self,
        input_file_path: Path | str | None = None,
        input_content: str | None = None,
    ) -> None:
        """Solve the project with either an input file or input text.

        Args:
            input_file_path: Path to a file to upload as input
            input_content: Text content to send as input

        """
        assert self.status == ProjectStatus.NOT_STARTED, (
            "This project has already been attempted; create a new project instead."
        )
        assert input_file_path is not None or input_content is not None, (
            "Either input_file_path or input_content must be provided."
        )
        assert input_file_path is None or input_content is None, (
            "Only one of input_file_path or input_content must be provided."
        )

        async with api_request.AristotleRequestClient() as client:
            if input_file_path is not None:
                # Handle file upload case
                file_path = Path(input_file_path)
                file_content = local_file_utils.read_file_safely(file_path)
                files = [("input_file", (str(file_path), file_content, "text/plain"))]
                params = None
            else:
                # Handle text input case
                params = {"input_text": input_content}
                files = None

            response = await client.post(
                f"/project/{self.project_id}/solve",
                params=params,
                files=files,
            )

            response_data = response.json()
            self._update_from_response(response_data)

    async def get_solution(self, output_path: Path | str | None = None) -> Path:
        """Download the solution file from the project result endpoint.

        Args:
            output_path: Path where to save the downloaded file. If None, uses filename from response headers.

        Returns:
            Path to the downloaded file
        """
        async with api_request.AristotleRequestClient() as client:
            response = await client.get(f"/project/{self.project_id}/result")

            if output_path is None:
                # Try to get filename from Content-Disposition header
                content_disposition = response.headers.get("content-disposition", "")
                if "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[1].strip('"')
                    output_path = Path(filename)
                else:
                    output_path = Path(f"{self.project_id}_solution.lean")
            else:
                output_path = Path(output_path)

            output_path.write_bytes(response.content)
            return output_path

    async def refresh(self) -> None:
        async with api_request.AristotleRequestClient() as client:
            response = await client.get(f"/project/{self.project_id}")
            response_data = response.json()
            self._update_from_response(response_data)

    def _update_from_response(self, response_data: dict) -> None:
        updated_project = cast(Project, self.model_validate(response_data))
        for field_name, field_value in updated_project.model_dump().items():
            setattr(self, field_name, field_value)

    @classmethod
    async def list_projects(
        cls, pagination_key: str | None = None, limit: int = 30
    ) -> tuple[list["Project"], str | None]:
        """List projects, ordered by creation date (most recent first).

        Args:
            pagination_key: Key to start from when paginating through projects.
            limit: Maximum number of projects to return. Must be between 1 and 100.

        Returns:
            Tuple of list of projects and the new pagination key.
        """
        assert 1 <= limit <= 100, "Limit must be between 1 and 100"

        async with api_request.AristotleRequestClient() as client:
            response = await client.get(
                "/project", params={"pagination_key": pagination_key, "limit": limit}
            )
            response_data = response.json()
            projects: list["Project"] = [
                cast("Project", cls.model_validate(project))
                for project in response_data["projects"]
            ]
            pagination_key = response_data.get("pagination_key")
            assert pagination_key is None or isinstance(pagination_key, str)
            return projects, pagination_key

    @overload
    @classmethod
    async def prove_from_file(
        cls,
        input_file_path: Path | str,
        *,
        auto_add_imports: Literal[True],
        validate_lean_project: Literal[True] = True,
        polling_interval_seconds: int = 30,
        max_polling_failures: int = 3,
    ) -> str: ...

    @overload
    @classmethod
    async def prove_from_file(
        cls,
        input_file_path: Path | str,
        *,
        auto_add_imports: Literal[False] = False,
        context_file_paths: list[Path] | list[str] | None = None,
        validate_lean_project: bool = True,
        polling_interval_seconds: int = 30,
        max_polling_failures: int = 3,
    ) -> str: ...

    @classmethod
    async def prove_from_file(
        cls,
        input_file_path: Path | str,
        auto_add_imports: bool = True,
        context_file_paths: list[Path] | list[str] | None = None,
        validate_lean_project: bool = True,
        wait_for_completion: bool = True,
        polling_interval_seconds: int = 30,
        max_polling_failures: int = 3,
    ) -> str:
        """Proves the input content.

        Args:
            input_file_path: Path to the input file
            auto_add_imports: Whether to automatically add imports from the input file as context to the project.
                              Requires that the input file is part of a valid Lean project.
            context_file_paths: List of file paths to add as context to the project, manually.
            validate_lean_project: Whether to validate that the input file is part of a valid Lean project.
            wait_for_completion: Whether to wait for the project to complete before returning. If False, the project id is returned.
            polling_interval_seconds: Interval in seconds to poll for the project status.
            max_polling_failures: Maximum number of polling failures before raising an error.

        Returns:
            The file path to the solution, or the project id if wait_for_completion is False
        """
        logger.info("Validating input...")
        input_file_path = Path(input_file_path)
        if validate_lean_project:
            project_root = local_file_utils.find_lean_project_root(input_file_path)
        else:
            project_root = None
        local_file_utils.validate_local_file_path(
            input_file_path, project_root=project_root
        )
        logger.info("Input Validated.")

        logger.info("Creating project...")
        project = await cls.create(validate_lean_project_root=validate_lean_project)
        logger.info(f"Created project {project.project_id}")

        try:
            if auto_add_imports:
                logger.info("Adding imports to project...")
                assert context_file_paths is None, (
                    "context_file_paths cannot be provided when auto_add_imports is True"
                )
                assert validate_lean_project, (
                    "validate_lean_project must be True when auto_add_imports is True"
                )
                assert project_root is not None
                context_file_paths = list(
                    local_file_utils.gather_file_imports(input_file_path, project_root)
                )
                if context_file_paths:
                    await project.add_context(
                        context_file_paths, validate_lean_project_root=True
                    )
                logger.info(f"Added {len(context_file_paths)} imports to project")
            elif context_file_paths is not None and len(context_file_paths) > 0:
                logger.info("Adding context files to project...")
                await project.add_context(
                    context_file_paths, validate_lean_project_root=validate_lean_project
                )
                logger.info(f"Added {len(context_file_paths)} context files to project")

            await project.solve(input_file_path=input_file_path)

            if not wait_for_completion:
                logger.info(
                    "Not waiting for completion. Returning project id. You can manually check on it any time with Project.from_id('{project.project_id}')"
                )
                return project.project_id

            num_polling_failures = 0
            while project.status not in (ProjectStatus.COMPLETE, ProjectStatus.FAILED):
                try:
                    logger.info(
                        f"Project status: {project.status} - sleeping for {polling_interval_seconds} seconds..."
                    )
                    await asyncio.sleep(polling_interval_seconds)
                    await project.refresh()
                except api_request.AristotleAPIError:
                    num_polling_failures += 1
                    if num_polling_failures >= max_polling_failures:
                        logger.error(
                            "Too many errors polling for project status. Your project might still be running; try checking on it later with project id {project.project_id}."
                        )
                        raise
                    logger.warning(
                        f"Error polling for project status. {num_polling_failures} failures so far. Sleeping for {polling_interval_seconds * num_polling_failures} seconds."
                    )
                    await asyncio.sleep(polling_interval_seconds * num_polling_failures)

            if project.status != ProjectStatus.COMPLETE:
                raise api_request.AristotleAPIError(
                    "Project failed due to an internal error. The team at Harmonic has been notified; please try again."
                )

            logger.info("Solve complete! Getting solution...")
            if "/" in str(input_file_path):
                output_file_name = str(input_file_path).split("/")[-1]
            else:
                output_file_name = str(input_file_path).split("\\")[-1]

            output_file_name = output_file_name.split(".")[0] + "_aristotle.lean"
            solution_file_path = await project.get_solution(output_file_name)
            logger.info(f"Solution saved to {solution_file_path}")
            return str(solution_file_path)
        finally:
            if project.status in (ProjectStatus.QUEUED, ProjectStatus.IN_PROGRESS):
                logger.info(
                    f"Project {project.project_id} is still running. You can manually check on it any time with Project.from_id('{project.project_id}')"
                )
