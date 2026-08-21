"""ADK Agent entrypoint for omnimeme deployment."""

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from omnimeme.prompts import OMNI_FLASH_DIRECTING_INSTR
from omnimeme.tools import enhance_video_prompt, generate_video_config

MODEL = "gemini-2.5-flash"


root_agent = Agent(
    name="omni_director",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=OMNI_FLASH_DIRECTING_INSTR,
    tools=[enhance_video_prompt, generate_video_config],
)

app = App(
    root_agent=root_agent,
    name="app",
)
