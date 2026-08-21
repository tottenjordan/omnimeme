from omnimeme.main import run_workflow


def test_run_workflow_guided():
    res = run_workflow(mode="guided", raw_input="Dragon over castle")
    assert res["status"] == "success"


def test_run_workflow_freeform():
    res = run_workflow(mode="freeform", raw_input="A robot painting canvas")
    assert res["status"] == "success"
