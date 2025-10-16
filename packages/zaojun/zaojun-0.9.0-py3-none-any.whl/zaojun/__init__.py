"""Main Code."""

from pathlib import Path
from typing import Annotated
from typing import Any

import httpx
import tomllib
import typer
from packaging.requirements import InvalidRequirement
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion
from packaging.version import parse as parse_version


def check(
    pyproject_toml: Annotated[
        Path,
        typer.Argument(help="Full path to pyproject.toml file to check."),
    ] = Path("./pyproject.toml"),
    short: Annotated[bool, typer.Option(help="Should only the shortest possible output be produced.")] = False,
    groups: Annotated[bool, typer.Option(help="Should dependencies in groups be checked.")] = False,
    compat_ok: Annotated[
        bool, typer.Option(help="Compatible versions are considered OK and won't cause and exit code of 1")
    ] = False,
) -> None:
    """Check listed dependencies against latest versions available on Pypi.org."""
    if not short:
        print(f"Checking dependencies in {pyproject_toml.resolve()}")
    with pyproject_toml.open("rb") as definitions:
        data = tomllib.load(definitions)

    exit_code: int = 0

    dependencies = data.get("project", {}).get("dependencies")

    client = httpx.Client()
    if process_dependencies(dependencies=dependencies, short=short, client=client, compat_ok=compat_ok):
        exit_code = 1

    if groups:
        dep_groups = data.get("dependency-groups", {})
        for group_name in dep_groups.keys():
            if not short:
                print(f"\nChecking dependency group [{group_name}]")

            dependencies = dep_groups.get(group_name)
            if process_dependencies(dependencies=dependencies, short=short, client=client, compat_ok=compat_ok):
                exit_code = 1

    client.close()
    raise typer.Exit(code=exit_code)


def process_dependencies(dependencies: list[Any], short: bool, compat_ok: bool, client: httpx.Client) -> bool:
    """Check all dependencies for updates.
    Return True if incompatible update is available or if compat_ok is False on any update available.
    """
    flag_update = False

    if not dependencies:
        dependencies = []

    for dep in dependencies:
        if is_local_dependency(dependency=dep):
            continue

        flag_update |= check_dependency(dependency=dep, short=short, compat_ok=compat_ok, client=client)

    return flag_update


def parse_dependency(dependency: str) -> tuple[str, str, str | None]:
    """Parse a dependency string into (package_name, version_constraint, environment_marker)."""
    try:
        req = Requirement(dependency)
        return (req.name, str(req.specifier) if req.specifier else "", str(req.marker) if req.marker else None)
    except InvalidRequirement as e:
        raise ValueError(f"Invalid dependency format '{dependency}'") from e


def is_version_compatible(current_spec: str, latest_version: str) -> bool:
    """Check if the latest version satisfies the current version constraints."""
    if not current_spec:
        return True  # No constraints means any version is acceptable

    try:
        specifier = SpecifierSet(current_spec)
        return parse_version(latest_version) in specifier
    except InvalidVersion:
        return False


def is_latest_version(current_spec: str, latest_version: str) -> bool:
    """Check if the latest version has been specified."""
    if not current_spec:
        return True  # No constraints means any version is acceptable

    try:
        specifier = SpecifierSet(current_spec)
        latest_spcecified = False
        for spec in specifier:
            if latest_version == spec.version:
                latest_spcecified = True
        return latest_spcecified
    except InvalidVersion:
        return False


def check_dependency(dependency: str, short: bool, compat_ok: bool, client: httpx.Client) -> bool:
    """Check if a dependency is needs an update.
    Returns true if newer version of dependency is available and that version is outside version spec or compat_ok is
    set to false and newer version is within version spec.
    """
    try:
        package_name, version_spec, _ = parse_dependency(dependency)
        latest_version = get_latest_pypi_version(package_name=package_name, client=client)

        flag_update_available = False

        if not version_spec:
            return flag_update_available

        is_compatible = is_version_compatible(version_spec, latest_version)
        is_latest = is_latest_version(current_spec=version_spec, latest_version=latest_version)

        if not is_compatible:
            print(f"\u274c {package_name}: {version_spec} \u2192 Latest: {latest_version}")
            flag_update_available = True

        elif not is_latest:
            print(f"\u26a0\ufe0f {package_name}: {version_spec} \u2192 Latest: {latest_version}")
            if not compat_ok:
                flag_update_available = True

        elif not short:
            print(f"\u2705\ufe0f {package_name}{version_spec} is up to date")

        return flag_update_available

    except ValueError as e:
        print(f"❌ Error checking {dependency}: {e.__repr__()}")
        return False
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        print(f"❌ Network error for {package_name}: {e.__repr__}")
        return False


def is_local_dependency(dependency: str) -> bool:
    """Check if dependency is a local path or URL."""
    if not dependency:
        return True

    return " @" in dependency or any(
        dependency.startswith(prefix) for prefix in ["file://", "https://", "http://", "git+https://", "./", "../"]
    )


def get_latest_pypi_version(package_name: str, client: httpx.Client) -> str:
    """Get latest version number of a package on Pypi.org."""
    response = client.get(f"https://pypi.org/pypi/{package_name}/json")
    response.raise_for_status()
    return str(response.json()["info"]["version"])


def main() -> None:
    """Run actual processing."""
    typer.run(check)
