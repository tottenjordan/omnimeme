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
