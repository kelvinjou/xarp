from smolagents import MultiStepAgent, OpenAIServerModel

from xarp.agents import run_xr_agent
from xarp.express import SyncXR
from xarp.server import show_qrcode_link

import os
api_key = os.getenv('OPENAI_API_KEY')

model = OpenAIServerModel(
    # model_id="gpt-5-mini",
    model_id="glm-4.6v-flash",
    api_key=api_key,
    
    # api_key="lm-studio",
    # api_base="http://192.168.4.71:1234/v1" # api_base="http://169.254.167.39:1234/v1" # optional (use if custom endpoint)

)

custom_system_prompt = """
You are an agent with extended reality tools. You can sense the environment and display information.
Before asking me about for extra information, use your tools to understand the context.
The user cannot read the output of "print" functions, use the "write" or "say" tools instead.
"""

def xr_agent_app(xr: SyncXR, agent: MultiStepAgent, params):
    agent.prompt_templates["system_prompt"] = custom_system_prompt + agent.prompt_templates["system_prompt"]
    xr.image().obj.show()
    while True:
        xr.say("How can I help you?")
        # request = xr.read()
        request = """
        Place a medicine bottle and an everyday portable object such as a backpack in the user’s environment
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
    show_qrcode_link()
    run_xr_agent(xr_agent_app, model)
