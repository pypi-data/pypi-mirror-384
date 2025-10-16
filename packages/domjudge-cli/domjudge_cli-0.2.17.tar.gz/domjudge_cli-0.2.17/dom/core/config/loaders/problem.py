import sys
import tempfile
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Union

import yaml
from p2d import convert
from tqdm import tqdm

from dom.types.config.raw import RawProblem, RawProblemsConfig
from dom.types.problem import (
    OutputValidators,
    ProblemData,
    ProblemINI,
    ProblemPackage,
    ProblemYAML,
    Submissions,
)
from dom.utils.color import get_hex_color
from dom.utils.sys import load_folder_as_dict


def convert_and_load_problem(archive_path: Path, with_statement: bool) -> ProblemPackage:
    """
    Convert a Polygon archive to a DOMjudge package and load it (no caching).
    """
    assert archive_path.exists(), f"Archive not found: {archive_path}"

    # Always convert into a fresh temporary ZIP
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        # Path for the converted ZIP
        converted_zip = tmpdir_path / f"{archive_path.stem}.zip"

        # Perform conversion
        convert(
            str(archive_path),
            str(converted_zip),
            short_name="-".join(archive_path.stem.split("-")[:-1]),
            with_statement=with_statement,
        )

        # Work in a subdirectory for extraction
        extract_dir = tmpdir_path / "extracted"
        extract_dir.mkdir()

        # Extract the converted ZIP
        with zipfile.ZipFile(converted_zip, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # Load domjudge-problem.ini
        ini_path = extract_dir / "domjudge-problem.ini"
        if not ini_path.exists():
            raise FileNotFoundError("Missing domjudge-problem.ini")
        problem_ini = ProblemINI.parse(ini_path.read_text(encoding="utf-8"))

        # Load problem.yaml
        yaml_path = extract_dir / "problem.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError("Missing problem.yaml")
        problem_yaml = ProblemYAML(**yaml.safe_load(yaml_path.read_text(encoding="utf-8")))

        # Load data folders
        data = ProblemData(
            sample=load_folder_as_dict(extract_dir / "data" / "sample"),
            secret=load_folder_as_dict(extract_dir / "data" / "secret"),
        )

        # Load output validators
        output_validators = OutputValidators(
            checker=load_folder_as_dict(extract_dir / "output_validators" / "checker")
        )

        # Load submissions
        submissions_dir = extract_dir / "submissions"
        submissions_data = {}
        if submissions_dir.exists():
            for verdict_dir in submissions_dir.iterdir():
                if verdict_dir.is_dir():
                    submissions_data[verdict_dir.name] = load_folder_as_dict(verdict_dir)
        submissions = Submissions(**submissions_data)

        # Collect extra files
        tracked = {
            "domjudge-problem.ini",
            "problem.yaml",
            *[f"data/sample/{fn}" for fn in data.sample],
            *[f"data/secret/{fn}" for fn in data.secret],
            *[f"output_validators/checker/{fn}" for fn in output_validators.checker],
            *[
                f"submissions/{v}/{fn}"
                for v, fmap in submissions._verdicts().items()
                for fn in fmap
            ],
        }
        extra_files = {}
        for p in extract_dir.rglob("*"):
            if p.is_file():
                rel = p.relative_to(extract_dir).as_posix()
                if rel not in tracked:
                    extra_files[rel] = p.read_bytes()

        # Build package
        problem = ProblemPackage(
            ini=problem_ini,
            yaml=problem_yaml,
            data=data,
            output_validators=output_validators,
            submissions=submissions,
            extra_files=extra_files,
        )

        # Validation write/read
        extracted_files = {
            str(p.relative_to(extract_dir)) for p in extract_dir.rglob("*") if p.is_file()
        }
        with tempfile.TemporaryDirectory() as tmp_zip_dir:
            tmp_zip_path = Path(tmp_zip_dir) / "package.zip"
            written_files = problem.write_to_zip(tmp_zip_path)

        problem.validate_package(extracted_files, written_files)
        return problem


def load_domjudge_problem(archive_path: Path) -> ProblemPackage:
    """
    Load a DOMjudge problem archive and return a ProblemPackage.
    """
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        extract_dir = tmpdir / "extracted"
        extract_dir.mkdir()

        # Extract the ZIP
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # Load domjudge-problem.ini
        ini_path = extract_dir / "domjudge-problem.ini"
        if not ini_path.exists():
            raise FileNotFoundError("Missing domjudge-problem.ini")
        ini_content = ini_path.read_text(encoding="utf-8")
        problem_ini = ProblemINI.parse(ini_content)

        # Load problem.yaml
        yaml_path = extract_dir / "problem.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError("Missing problem.yaml")
        yaml_content = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        problem_yaml = ProblemYAML(**yaml_content)

        # Load sample/secret data
        data = ProblemData(
            sample=load_folder_as_dict(extract_dir / "data" / "sample"),
            secret=load_folder_as_dict(extract_dir / "data" / "secret"),
        )

        # Load output validators
        output_validators = OutputValidators(
            checker=load_folder_as_dict(extract_dir / "output_validators" / "checker")
        )

        # Load submissions
        submissions_dir = extract_dir / "submissions"
        submissions_data = {}
        if submissions_dir.exists():
            for verdict_dir in submissions_dir.iterdir():
                if verdict_dir.is_dir():
                    submissions_data[verdict_dir.name] = load_folder_as_dict(verdict_dir)

        submissions = Submissions(**submissions_data)

        # Build and return ProblemPackage
        return ProblemPackage(
            ini=problem_ini,
            yaml=problem_yaml,
            data=data,
            output_validators=output_validators,
            submissions=submissions,
        )


def load_problem(
    archive_path: Path, platform: str, color: str, with_statement: bool, idx: int
) -> tuple[ProblemPackage, int]:
    """
    Import a problem based on its format.
    - 'domjudge': load directly
    - 'polygon': convert and load
    - Else: raise exception
    """
    problem_format = (platform or "").strip().lower()

    if problem_format == "domjudge":
        problem_package = load_domjudge_problem(archive_path)
    elif problem_format == "polygon":
        problem_package = convert_and_load_problem(archive_path, with_statement=with_statement)
    else:
        raise ValueError(
            f"Unsupported problem platform: '{platform}' (must be 'domjudge' or 'polygon')"
        )

    problem_package.ini.color = get_hex_color(color)
    return problem_package, idx


def load_problems_from_config(
    problem_config: Union[RawProblemsConfig, list[RawProblem]],
    with_statement: bool,
    config_path: Path,
):
    if isinstance(problem_config, RawProblemsConfig):
        # Resolve file_path relative to the directory of config_path
        config_dir = config_path.resolve().parent
        file_path = config_dir / problem_config.from_

        if file_path.suffix.lower() not in (".yml", ".yaml"):
            print(
                f"[ERROR] Problems file '{file_path}' must be a .yml or .yaml file.",
                file=sys.stderr,
            )
            raise ValueError(f"Invalid file extension for problems file: {file_path}")

        if not file_path.exists():
            print(f"[ERROR] Problems file '{file_path}' does not exist.", file=sys.stderr)
            raise FileNotFoundError(f"Problems file not found: {file_path}")

        try:
            with file_path.open() as f:
                loaded_data = yaml.safe_load(f)
                if not isinstance(loaded_data, list):
                    print(
                        f"[ERROR] Problems file '{file_path}' must contain a list.", file=sys.stderr
                    )
                    raise ValueError(f"Problems file must contain a list of problems: {file_path}")
                problems = [RawProblem(**problem) for problem in loaded_data]
        except Exception as e:
            print(
                f"[ERROR] Failed to load problems from '{file_path}'. Error: {e!s}",
                file=sys.stderr,
            )
            raise e

    elif isinstance(problem_config, list) and all(
        isinstance(p, RawProblem) for p in problem_config
    ):
        problems = problem_config
    else:
        print("[ERROR] Invalid problem configuration.", file=sys.stderr)
        raise TypeError("Invalid problem configuration type.")

    # Validate archives are unique and convert to Path objects
    archive_paths = [Path(problem.archive).resolve() for problem in problems]
    archive_paths_str = [str(p) for p in archive_paths]
    if len(archive_paths_str) != len(set(archive_paths_str)):
        duplicates = {x for x in archive_paths_str if archive_paths_str.count(x) > 1}
        raise ValueError(f"Duplicate archives detected: {', '.join(duplicates)}")

    for archive_path in archive_paths:
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")

    # Load problems with progress bar
    with ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(
                load_problem, archive_path, problem.platform, problem.color, with_statement, i
            ): problem
            for i, (problem, archive_path) in enumerate(zip(problems, archive_paths, strict=False))
        }
        problem_packages = []
        for future in tqdm(as_completed(futures), total=len(futures), desc="Loading problems"):
            problem_packages.append(future.result())
        problem_packages = [package for package, _ in sorted(problem_packages, key=lambda x: x[1])]

    # Validate short_names are unique
    short_names = [problem_package.ini.short_name for problem_package in problem_packages]
    if len(short_names) != len(set(short_names)):
        duplicates = {x for x in short_names if short_names.count(x) > 1}
        raise ValueError(f"Duplicate problem short_names detected: {', '.join(duplicates)}")

    return problem_packages
