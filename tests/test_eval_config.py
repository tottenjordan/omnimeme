import json
from pathlib import Path


def test_eval_dataset_valid_jsonl():
    dataset_path = Path("evals/dataset.jsonl")
    assert dataset_path.exists()
    lines = dataset_path.read_text().strip().split("\n")
    assert len(lines) >= 2
    for line in lines:
        data = json.loads(line)
        assert "input" in data
        assert "expected_elements" in data


def test_eval_config_yaml_valid():
    import yaml

    config_path = Path("evals/config.yaml")
    assert config_path.exists()
    content = yaml.safe_load(config_path.read_text())
    assert "metrics" in content
    assert "test_cases" in content
    test_cases = content["test_cases"]
    assert len(test_cases) >= 4
    case_ids = [tc["id"] for tc in test_cases]
    assert "draft_resolution_360p" in case_ids
    assert "keyframe_motion_orbital" in case_ids
    assert "theme_sanitization_celebrity" in case_ids

