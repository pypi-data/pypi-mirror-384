import logging
import os
from pathlib import Path

# Set up logger for this module
logger = logging.getLogger("aristotle")


MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024

# These imports are included by default, and don't require importing any new file
STANDARD_LIBRARIES = [
    "Mathlib",
    "Lean",
    "Std",
    "Batteries",
    "Qq",
    "Aesop",
    "ProofWidgets",
    "ImportGraph",
    "LeanSearchClient",
    "Plausible",
]


class LeanProjectError(Exception):
    """Exception raised for Lean project-related errors."""

    pass


def find_lean_project_root(start_path: Path) -> Path:
    """
    Find the Lean project root by looking for project markers.

    Finds the OUTERMOST project root to handle cases where we're starting
    from within .lake/packages/ subdirectories.

    Searches upward from start_path for:
    - lakefile.lean (legacy Lean config for Lake build system)
    - lakefile.toml (toml config for Lake build system)
    - lean-toolchain file

    Args:
        start_path: Path to start searching from

    Returns:
        Path: Outermost project root directory

    Raises:
        ProjectAPIError: If no Lean project markers are found
    """
    current = start_path.parent if start_path.is_file() else start_path
    current = current.resolve()
    project_markers = ["lakefile.lean", "lakefile.toml", "lean-toolchain"]
    found_root = None

    # Search upward from the start path, keeping track of the outermost project root
    while current != current.parent:
        for marker in project_markers:
            if (current / marker).exists():
                logger.debug(f"Found project marker at {current} (marker: {marker})")
                found_root = current
                # Don't return immediately - keep searching for outer project roots
                break
        current = current.parent

    if found_root:
        logger.info(f"Found outermost project root at {found_root}")
        return found_root

    # No markers found - raise error
    raise LeanProjectError(
        f"No Lean project found. Could not find any of {project_markers} "
        f"in the directory tree starting from {start_path}. "
        "Please ensure you're running this from within a Lean project."
    )


def validate_local_file_path(file_path: Path, project_root: Path | None = None) -> None:
    """
    Validate that a file path is safe to use.

    Validates that this is a real file, and if provided, within the project root.

    Args:
        file_path: Path to validate
        project_root: Project root directory to ensure file is within (optional)

    Raises:
        ValueError: If path is invalid or outside project root
    """
    try:
        resolved_path = file_path.resolve(strict=True)
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Invalid file path {file_path}: {e}")

    if project_root is not None:
        project_root_resolved = project_root.resolve()
        try:
            resolved_path.relative_to(project_root_resolved)
        except ValueError:
            raise ValueError(
                f"File {resolved_path} is outside project root {project_root_resolved}"
            )

    if not resolved_path.is_file():
        raise ValueError(f"Path {resolved_path} is not a file")

    if resolved_path.suffix != ".lean":
        raise ValueError(f"File {resolved_path} is not a Lean file")


def validate_local_file_paths(
    file_paths: list[Path], project_root: Path | None = None
) -> None:
    """
    Validate that all paths in a list of local paths are safe to use.
    """
    for file_path in file_paths:
        validate_local_file_path(file_path, project_root)


def normalize_and_dedupe_paths(file_paths: list[Path] | list[str]) -> list[Path]:
    """
    Normalize and remove duplicate file paths based on their resolved absolute paths.

    Args:
        file_paths: List of file paths (can be strings or Path bojects) to normalize and deduplicate

    Returns:
        List of unique Path objects (with duplicates removed)
    """
    # Normalize to Path objects
    normalized_paths = [Path(p) for p in file_paths]

    seen: set[Path] = set()
    unique_paths: list[Path] = []

    for file_path in normalized_paths:
        resolved = file_path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_paths.append(file_path)

    return unique_paths


def read_file_safely(file_path: Path, max_size: int = MAX_FILE_SIZE_BYTES) -> bytes:
    """
    Read a file safely, checking size before loading into memory.

    Args:
        file_path: Path to file to read
        max_size: Maximum allowed file size in bytes

    Returns:
        File contents as bytes

    Raises:
        FileSizeError: If file is too large
        OSError: If file cannot be read
    """
    file_size = file_path.stat().st_size
    if file_size > max_size:
        raise LeanProjectError(
            f"File {file_path} is too large ({file_size} bytes). Maximum allowed size is {max_size} bytes."
        )

    with open(file_path, "rb") as f:
        return f.read()


def _clean_dependency_path(relative_path: Path) -> Path:
    """
    Clean dependency paths by removing .lake/packages/PACKAGE_NAME/ prefix.

    This strips build infrastructure artifacts from paths to ensure dependencies
    are uploaded with the correct naming scheme.

    Args:
        relative_path: The relative path to clean

    Returns:
        Path: Cleaned path with package prefix removed if applicable
    """
    path_str = str(relative_path)

    if ".lake/packages/" not in path_str:
        return relative_path

    # handle nested packages
    package = path_str.split(".lake/packages/")[-1]
    package_and_path = package.split("/", 1)
    if len(package_and_path) != 2:
        raise ValueError(f"Invalid dependency path structure: {relative_path}")
    _package_name, path = package_and_path
    return Path(path)


def get_files_for_upload(
    file_paths: list[Path], project_root: Path | None = None
) -> list[tuple[str, bytes, str]]:
    """
    Get files for upload, reading them safely and returning a list of tuples with the file path, contents, and file type.
    """
    files: list[tuple[str, bytes, str]] = []
    for file_path in file_paths:
        file_content = read_file_safely(file_path)
        # Use relative path from project root
        if project_root is not None:
            file_path = file_path.resolve().relative_to(project_root)
        files.append(
            (str(_clean_dependency_path(file_path)), file_content, "text/plain")
        )

    return files


def _extract_imports(lean_file_path: Path) -> list[str]:
    """
    Extract local project import statements from a Lean file.
    Filters out Mathlib imports.

    Args:
        lean_file_path: Path to the Lean file

    Returns:
        list[str]: List of local project import paths
    """
    imports: list[str] = []
    try:
        with lean_file_path.open("r", encoding="utf-8") as f:
            for line in f:
                stripped_line = line.strip()
                import_split = stripped_line.split("import ")
                if len(import_split) != 2:
                    continue

                import_path = import_split[1].strip()

                if any(import_path.startswith(lib) for lib in STANDARD_LIBRARIES):
                    logger.debug(f"Skipping standard library import: {import_path}")
                    continue

                # Only include local project imports
                imports.append(import_path)

    except Exception as e:
        logger.error(f"Error reading file {lean_file_path}: {e}")

    return imports


def _is_within_project(file_path: Path, project_root: Path) -> bool:
    """
    Check if a file path is within the project directory.

    Args:
        file_path: Path to check
        project_root: Project root directory

    Returns:
        bool: True if file is within project
    """
    try:
        file_path.resolve().relative_to(project_root.resolve())
        return True
    except ValueError:
        return False


def _resolve_import_to_file_path(
    import_path: str, source_file_path: Path, project_root: Path
) -> Path | None:
    """
    Resolve an import path to a local project file path.
    Only resolves imports to files within the same project.

    Args:
        import_path: The import path (e.g., "MyProject.Utils", "./LocalFile", or "../Other")
        source_file_path: Path to the file containing the import
        project_root: Project root directory

    Returns:
        Path | None: Resolved file path or None if not a local project file

    Raises:
        ImportResolutionError: If import resolution fails with detailed context
    """
    source_file_path = Path(source_file_path).resolve()
    source_dir = source_file_path.parent

    attempted_paths: list[Path] = []

    try:
        relative_source = source_file_path.relative_to(project_root)
        source_module_path = str(relative_source.with_suffix("")).replace("/", ".")

        if source_module_path == import_path:
            logger.debug(f"Skipping self-import: {import_path}")
            return None
    except ValueError:
        # source_file_path is not relative to project_root, so it can't be a self-import
        pass

    module_path = import_path.replace(".", "/") + ".lean"

    # 1. Try relative to project root
    candidate_path = (project_root / module_path).resolve()
    attempted_paths.append(candidate_path)
    if candidate_path.exists() and _is_within_project(candidate_path, project_root):
        return candidate_path

    # 2. Try in .lake/packages/ for third-party dependencies
    lake_packages_base = project_root / ".lake" / "packages"
    if lake_packages_base.exists():
        for package_dir in lake_packages_base.iterdir():
            if package_dir.is_dir():
                candidate_path = (package_dir / module_path).resolve()
                if candidate_path.exists():
                    return candidate_path

    # 3. Try relative to source file directory
    candidate_path = (source_dir / module_path).resolve()
    attempted_paths.append(candidate_path)
    if candidate_path.exists() and _is_within_project(candidate_path, project_root):
        return candidate_path

    if lake_packages_base.exists():
        logger.warning(
            f"Cannot find import '{import_path}' from {source_file_path}. Have you tried running `lake update` ?"
        )
    else:
        logger.warning(
            f"Cannot find import '{import_path}' from {source_file_path}. Did you forget to `lake build` ?"
        )

    return None


def _gather_all_lean_files_in_lean_package(package_dir: Path) -> set[Path]:
    """
    Gather all .lean files in a Lean package directory, excluding subpackages.

    A subpackage is identified by having its own lakefile.lean or being in .lake/packages/.

    Args:
        package_dir: Root directory of the Lean package

    Returns:
        set[Path]: Set of all .lean files in the package (excluding subpackages)
    """
    lean_files: set[Path] = set()
    if not package_dir.exists() or not package_dir.is_dir():
        return lean_files

    for root, dirs, files in os.walk(package_dir):
        root_path = Path(root)

        if ".lake" in dirs:
            dirs.remove(".lake")

        dirs_to_remove: list[str] = []
        for dir_name in dirs:
            dir_path = root_path / dir_name
            if (dir_path / "lakefile.lean").exists():
                dirs_to_remove.append(dir_name)

        for dir_name in dirs_to_remove:
            dirs.remove(dir_name)

        # Add all .lean files in the current directory
        for file_name in files:
            if file_name.endswith(".lean"):
                file_path = root_path / file_name
                lean_files.add(file_path.resolve())

    return lean_files


def gather_file_imports(
    input_file_path: Path, project_root: Path | None = None
) -> set[Path]:
    """
    Gather all files in the import tree starting from the given Lean file.

    Args:
        input_file_path: Path to the starting Lean file
        project_root: Project root directory

    Returns:
        set[Path]: Set of all files in the import tree
    """
    if project_root is None:
        project_root = find_lean_project_root(input_file_path)

    visited: set[Path] = set()
    original_path = Path(input_file_path).resolve()
    files_to_process: list[Path] = [original_path]

    while files_to_process:
        current_file = files_to_process.pop(0)

        if current_file in visited:
            continue

        visited.add(current_file)
        imports = _extract_imports(current_file)
        logger.debug(f"Found {len(imports)} imports in {current_file}")

        for import_path in imports:
            # Package imports
            if "." not in import_path:
                lake_packages_dir = project_root / ".lake" / "packages" / import_path
                if lake_packages_dir.exists() and lake_packages_dir.is_dir():
                    logger.info(
                        f"Found package import '{import_path}', adding all files from {lake_packages_dir}"
                    )
                    package_files = _gather_all_lean_files_in_lean_package(
                        lake_packages_dir
                    )
                    for pkg_file in package_files:
                        if pkg_file not in visited:
                            visited.add(pkg_file)
                    continue

            # Regular import resolution
            resolved_file_path = _resolve_import_to_file_path(
                import_path, current_file, project_root
            )
            if resolved_file_path and resolved_file_path.exists():
                if resolved_file_path not in visited:
                    files_to_process.append(resolved_file_path)
            else:
                logger.error(
                    f"Could not resolve import '{import_path}' from {current_file}"
                )

    if original_path in visited:
        # don't add the original path as context
        visited.remove(original_path)
    return visited
