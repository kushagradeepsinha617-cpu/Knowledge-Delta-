"""Download-free fixture workflow and constrained report exports."""
from pathlib import Path

from .diff import compare
from .evaluation import evaluate_run
from .fixture_replay import replay
from .metrics import summarize_metrics
from .reports import html_report, json_report
from .snapshots import load_snapshot
from .validation import ValidationError, read_json


def fixture_report(before, after, dataset_path, relations_path, *, simulate_judgments=False):
    snapshots = {"before": load_snapshot(before), "after": load_snapshot(after)}
    dataset, relations = read_json(dataset_path), read_json(relations_path)
    bundle = replay(dataset, snapshots, relations, simulate_judgments=simulate_judgments)
    evaluation = evaluate_run(bundle["run"], dataset, bundle["relations"], bundle["reviews"],
                               snapshots=snapshots, allow_fixture=True)
    evaluation["raw_run"] = bundle["run"]
    evaluation["review_records"] = bundle["reviews"]
    evaluation["relation_annotations"] = bundle["relations"]
    evaluation["snapshot_changes"] = compare(snapshots["before"], snapshots["after"])
    evaluation["fixture_notice"] = bundle["run"]["notice"]
    evaluation["metrics"] = summarize_metrics(evaluation)
    return evaluation


def export_report(project_root, directory, evaluation):
    root = Path(project_root).resolve()
    path = Path(directory)
    directory = (root / path).resolve() if not path.is_absolute() else path.resolve()
    if not directory.is_relative_to(root) or directory == root:
        raise ValidationError("Choose a report subdirectory inside the project")
    for name in ("knowledge_delta", "scripts", "tests", "examples", ".tools", ".venv", ".venv-ml", ".git"):
        source = (root / name).resolve()
        if directory == source or directory.is_relative_to(source):
            raise ValidationError("Reports must not overwrite source, environment, models or repository metadata")
    outputs = {"report.json": json_report(evaluation),
               "report.html": html_report(evaluation, snapshot_changes=evaluation.get("snapshot_changes"))}
    for name, content in outputs.items():
        target = directory / name
        if target.is_symlink() or not target.resolve().is_relative_to(root):
            raise ValidationError("Report target escapes the project or is a symlink")
        if target.exists() and (not target.is_file() or target.read_text(encoding="utf-8") != content):
            raise ValidationError("Report already exists with different content; choose a new output directory")
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        target = directory / name
        if not target.exists():
            with target.open("x", encoding="utf-8", newline="\n") as output:
                output.write(content)
    return {name: str(directory / name) for name in outputs}
