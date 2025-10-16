import os
from pathlib import Path

import nox

nox.options.reuse_existing_virtualenvs = True
nox.options.sessions = "lint", "tests"
nox.options.default_venv_backend = "uv"
locations = "src", "tests"

versions = [
    "3.12",
    "3.11",
    "3.10",
    "3.9",
]


def install_vllm_if_overridden(session: nox.Session) -> None:
    if vllm_wheel_path := os.getenv("VLLM_VERSION_OVERRIDE"):
        session.install(vllm_wheel_path)


@nox.session(python=versions)
def tests(session: nox.Session) -> None:
    install_vllm_if_overridden(session)

    deps = [".[tests]"]
    if os.getenv("CI"):
        deps.append("pytest-github-actions-annotate-failures")

    session.install(*deps)

    # Re-install vllm since `.[tests]` brings in
    # overrides that may bring the vllm version down.
    # Should be a no-op most of the time.
    install_vllm_if_overridden(session)

    session.run(
        "pytest",
        "--cov",
        "--cov-config=pyproject.toml",
        "--no-cov-on-fail",
        "tests",
        *session.posargs,
        env={"COVERAGE_FILE": f".coverage.{session.python}"},
    )


@nox.session(python=versions)
def lint(session: nox.Session) -> None:
    session.install("pre-commit")

    if run_mypy := "--mypy" in session.posargs:
        session.posargs.remove("--mypy")

    args = *(session.posargs or ("--show-diff-on-failure",)), "--all-files"
    session.run("pre-commit", "run", *args)

    if run_mypy:
        session.run("python", "-m", "mypy")


@nox.session(python=versions)
def build(session: nox.Session) -> None:
    session.install("build", "setuptools", "twine")

    session.run("python", "-m", "build")

    dists = Path("dist").glob("*")
    session.run("twine", "check", *dists, silent=True)


@nox.session(python=versions)
def dev(session: nox.Session) -> None:
    """Set up a python development environment for the project."""
    args = session.posargs or ("venv",)
    venv_dir = Path(args[0])

    session.log(f"Setting up virtual environment in {venv_dir}")
    session.install("uv")
    session.run("uv", "venv", venv_dir, silent=True)

    python = venv_dir / "bin/python"
    session.run(
        *f"{python} -m uv pip install -e .[dev]".split(),
        external=True,
    )
