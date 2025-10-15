# Aristotle SDK

The Aristotle SDK is a Python library that provides tools and utilities for interacting with the Aristotle API, enabling automated theorem proving for Lean projects.


## Installation

```bash
pip install aristotlelib
```

## Quick Start

### 1. Set up your API key

```python
import aristotlelib

# Set your API key
aristotlelib.set_api_key("your-api-key-here")

# Or set it via environment variable
# export ARISTOTLE_API_KEY="your-api-key-here"
```

### 2. Set up the correct Lean Toolchain and Mathlib versions

Aristotle uses the following versions of Lean and Mathlib:

- **Lean Toolchain version**: `leanprover/lean4:v4.20.0-rc5`
- **Mathlib version**: `d62eab0cc36ea522904895389c301cf8d844fd69` (May 9, 2025)

If your project uses a different version of either, it might run into compatibility issues.

### 3. Prove a theorem from a file

The simplest way to use Aristotle is to prove a theorem from a Lean file:

```python
import asyncio
import aristotlelib

async def main():
    # Prove a theorem from a Lean file
    solution_path = await aristotlelib.Project.prove_from_file("path/to/your/theorem.lean")
    print(f"Solution saved to: {solution_path}")

asyncio.run(main())
```

### 4. Manual project management

For more control, you can manage projects manually:

```python
import asyncio
import aristotlelib
from pathlib import Path

async def main():
    # Create a new project
    project = await aristotlelib.Project.create()
    print(f"Created project: {project.project_id}")

    # Add context files
    await project.add_context(["path/to/context1.lean", "path/to/context2.lean"])

    # Solve with input content
    await project.solve(input_content="theorem my_theorem : True := trivial")

    # Wait for completion and get solution
    while project.status not in [aristotlelib.ProjectStatus.COMPLETE, aristotlelib.ProjectStatus.FAILED]:
        await asyncio.sleep(30)  # Poll every 30 seconds
        await project.refresh()
        print(f"Status: {project.status}")

    if project.status == aristotlelib.ProjectStatus.COMPLETE:
        solution_path = await project.get_solution()
        print(f"Solution saved to: {solution_path}")

asyncio.run(main())
```

## API Reference

### Project Class

The main class for interacting with Aristotle projects.

#### `Project.create(context_file_paths=None, validate_lean_project_root=True)`

Create a new Aristotle project.

**Parameters:**
- `context_file_paths` (list[Path | str], optional): List of file paths to include as context
- `validate_lean_project_root` (bool): Whether to validate Lean project structure (recommended: True)

**Returns:** `Project` instance

#### `Project.prove_from_file(input_file_path, auto_add_imports=True, context_file_paths=None, validate_lean_project=True, wait_for_completion=True, polling_interval_seconds=30, max_polling_failures=3)`

Convenience method to prove a theorem from a file with automatic import resolution.

**Parameters:**
- `input_file_path` (Path | str): Path to the input Lean file
- `auto_add_imports` (bool): Automatically add imported files as context
- `context_file_paths` (list[Path | str], optional): Manual context files
- `validate_lean_project` (bool): Validate Lean project structure
- `wait_for_completion` (bool): Whether to wait for project completion before returning
- `polling_interval_seconds` (int): Seconds between status checks
- `max_polling_failures` (int): Max polling failures before giving up

**Returns:** `str` - Path to the solution file (as string), or the project id if wait_for_completion is False

#### `project.add_context(context_file_paths, batch_size=10, validate_lean_project_root=True)`

Add context files to an existing project.

**Parameters:**
- `context_file_paths` (list[Path | str]): Files to add as context
- `batch_size` (int): Files to upload per batch (max 10)
- `validate_lean_project_root` (bool): Validate project structure

#### `project.solve(input_file_path=None, input_content=None)`

Solve the project with either a file or text content.

**Parameters:**
- `input_file_path` (Path | str, optional): Path to input file
- `input_content` (str, optional): Text content to solve

**Note:** Exactly one of `input_file_path` or `input_content` must be provided.

#### `project.get_solution(output_path=None)`

Download the solution file, if one exists.

**Parameters:**
- `output_path` (Path | str, optional): Where to save the solution

**Returns:** `Path` to the downloaded solution file

#### `project.refresh()`

Refresh the project status from the API.

### Project Status

```python
class ProjectStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
```

### Error Handling

The SDK provides several exception types:

- `AristotleAPIError`: API-related errors
- `LeanProjectError`: Lean project validation errors

## Lean Project Requirements

Aristotle works best with properly structured Lean projects. Your project should have:

- A `lakefile.toml` configuration file or `lakefile.lean` (legacy)
- A `lean-toolchain` file
- Proper import structure

The SDK will automatically:
- Detect your project root
- Validate file paths are within the project
- Resolve imports to include dependencies
- Handle file size limits (100MB max per file)

## Examples

### Basic theorem proving

```python
import asyncio
import aristotlelib

async def prove_simple_theorem():
    # Set API key
    aristotlelib.set_api_key("your-key")

    # Prove a simple theorem
    solution = await aristotlelib.Project.prove_from_file("examples/simple.lean")
    print(f"Proof completed: {solution}")

asyncio.run(prove_simple_theorem())
```

### Working with existing projects

```python
import asyncio
import aristotlelib

async def work_with_existing_project():
    # Load an existing project
    project = await aristotlelib.Project.from_id("existing-project-id")

    # Check status
    print(f"Project status: {project.status}")

    if project.status == aristotlelib.ProjectStatus.COMPLETE:
        solution = await project.get_solution()
        print(f"Solution available at: {solution}")

asyncio.run(work_with_existing_project())
```

### Listing projects

```python
import asyncio
import aristotlelib

async def list_projects():
    projects, pagination_key = await aristotlelib.Project.list_projects(limit=10)

    for project in projects:
        print(f"Project {project.project_id}: {project.status}")

    # Get next page if available
    if pagination_key:
        more_projects, pagination_key = await aristotlelib.Project.list_projects(pagination_key=pagination_key)
        print(f"Found {len(more_projects)} more projects")

asyncio.run(list_projects())
```

## Logging

The SDK uses Python's standard logging module. To see debug and info messages from the SDK, configure logging in your application:

```python
import logging
import aristotlelib

# Configure logging to see SDK messages
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(name)s - %(message)s"
)

```

This will show helpful messages to track the current status.
