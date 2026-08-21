"""Main CLI entrypoint for OmniMeme agentic workflow."""

from typing import Any

from omnimeme.agent import create_omni_director_agent
from omnimeme.ui.freeform_widget import FreeformInput, process_freeform_request
from omnimeme.ui.guided_experience import GuidedPromptInput, process_guided_request


def run_workflow(mode: str, raw_input: str) -> dict[str, Any]:
    agent = create_omni_director_agent()
    if mode == "guided":
        inp = GuidedPromptInput(subject=raw_input)
        return process_guided_request(inp, agent)
    elif mode == "freeform":
        inp = FreeformInput(raw_prompt=raw_input)
        return process_freeform_request(inp, agent)
    else:
        raise ValueError(f"Unknown mode: {mode}")


if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "freeform"
    text = (
        sys.argv[2] if len(sys.argv) > 2 else "A futuristic motorcycle racing down a neon highway"
    )
    result = run_workflow(mode, text)
    print("Workflow Result:")
    print(result)
