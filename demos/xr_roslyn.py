from smolagents import MultiStepAgent, OpenAIServerModel

from xarp.agents import run_xr_agent
from xarp.express import SyncXR
from xarp.server import show_qrcode_link

import os
api_key = os.getenv('OPENAI_API_KEY')
lm_studio = os.getenv('LM_STUDIO_KEY')
model_id = "mistralai/devstral-small-2-2512"

model = OpenAIServerModel(
    model_id=model_id,
    # api_key=api_key
    api_key=lm_studio,
    api_base="http://128.111.28.74:1234/v1"
)

custom_system_prompt = """
You are an agent with extended reality tools. You can sense the environment and display information.
Before asking me about for extra information, use your tools to understand the context.
The user cannot read the output of "print" functions, use the "write" or "say" tools instead.

CRITICAL OUTPUT FORMAT (CodeAgent):
- Respond with a single Python tool call only (no prose, no lists, no explanations).
- Always call baseline_code(...) exactly once.
- The response must be valid Python that CodeAgent can parse.
- Wrap the full C# source inside triple-quoted string literals within baseline_code(...).
"""

def xr_agent_app(xr: SyncXR, agent: MultiStepAgent, params):
    agent.prompt_templates["system_prompt"] = custom_system_prompt + agent.prompt_templates["system_prompt"]
    # xr.image().obj.show()
    while True:
        xr.say("How can I help you?")
        # xr.depth().obj.show()
        request = xr.read()

        # request = """Place 2 rotating gray cubes in front of me."""
        # request = """Anchor a box to the floor in front of me, and one to the ceiling."""
        request = """
        Place a medicine bottle and an everyday portable object such as a backpack in the user's environment
        and start continuous sensing of RGB, depth, head pose, and hand pose. The system detects and labels
        both objects and overlays anchored prompts reading "Medicine bottle detected. Select for guidance." and
        "Backpack detected. Select for assistance." When the user selects the medicine bottle, the system displays
        context-aware text anchored to the bottle such as "Check dosage and timing before use," followed by an option
        to step through dosage instructions. When the user selects the backpack, the system displays an anchored message
        like "Need help preparing this item?" and, upon selection, shows task-oriented guidance such as "Suggested items
        based on context: laptop, charger, notebook." Successful execution demonstrates multi-object detection, object-specific
        semantic reasoning, context-dependent instruction generation, and dynamic updating of AR text anchored to different
        physical objects. You can choose different objects as long as you show case at least two.
        """

        answer = agent.run(request)
        xr.write(answer)


if __name__ == '__main__':
    # show_qrcode_link()
    run_xr_agent(xr_agent_app, model, allowed_tools=["baseline_code"])
    # run_xr_agent(xr_agent_app, model)
