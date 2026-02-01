import pandas as pd
import sys
import os
from datetime import datetime
from smolagents import MultiStepAgent, OpenAIServerModel
from xarp.agents import run_xr_agent
from xarp.express import SyncXR
from xarp.server import show_qrcode_link

api_key = os.getenv('OPENAI_API_KEY')
lm_studio = os.getenv('LM_STUDIO_KEY')

# hardcoded, unused
# model_id = "mistralai/devstral-small-2-2512"
# model = OpenAIServerModel(
#     model_id=model_id,
#     api_key=lm_studio,
#     api_base="http://128.111.28.74:1234/v1"
# )

def getModel(current_model):
    return OpenAIServerModel(
        model_id=current_model,
        api_key=lm_studio,
        api_base="http://128.111.28.74:1234/v1"
    )


# Global variables to track current scenario
start_pk = 4  # starting pk value (not row index)
num_rows = 2  # automated workflow only processes start + n scenarios

current_request = ""
current_mode = ""
current_model = ""
current_log_file = ""
current_timestamp = ""

# ======================== PROMPTS ========================
xarp_system_prompt = """
You are an agent with extended reality tools. You can sense the environment and display information.
Before asking me about for extra information, use your tools to understand the context.
The user cannot read the output of "print" functions, use the "write" or "say" tools instead.

When you have successfully completed the user's request by calling the appropriate tools,
immediately return your final answer. Do not wait for confirmation or try to verify the results.
"""
baseline_system_prompt = """
You are an agent with extended reality tools. You can sense the environment and display information.
Before asking me about for extra information, use your tools to understand the context.
The user cannot read the output of "print" functions, use the "write" or "say" tools instead.

CRITICAL OUTPUT FORMAT (CodeAgent):
- Respond with a single Python tool call only (no prose, no lists, no explanations).
- Always call baseline_code(...) exactly once.
- The response must be valid Python that CodeAgent can parse.
- Wrap the full C# source inside triple-quoted string literals within baseline_code(...).
"""

PROMPTS_BY_MODE = {
    "xarp": xarp_system_prompt,
    "base": baseline_system_prompt,
}

def log_step_immediately(step_log):
    """Log a step to CSV as soon as it completes - uses step_callbacks"""
    global current_pk, current_request, current_mode, current_model, current_log_file, current_timestamp
    
    results_path = 'demos/results.csv'
    needs_header = not os.path.exists(results_path)
    
    # Extract data from step log object
    step_number = getattr(step_log, 'step_number', '?')
    
    # Get token usage and timing info
    token_usage = getattr(step_log, 'token_usage', None)
    timing = getattr(step_log, 'timing', None)
    
    print(f"\n[LOGGING] Step {step_number} - Type: {type(step_log).__name__}")
    print(f"[LOGGING] Has token_usage: {token_usage is not None}")
    print(f"[LOGGING] Has timing: {timing is not None}")
    
    if token_usage and timing:
        row = {
            'id': f"{current_pk}_{current_mode}_{current_timestamp}",
            'pk': current_pk,
            'mode': current_mode,
            'model': current_model,
            'request': current_request[:20] if len(current_request) > 20 else current_request,
            'step_number': step_number,
            'input_tokens': token_usage.get('input_tokens', 0) if isinstance(token_usage, dict) else getattr(token_usage, 'input_tokens', 0),
            'output_tokens': token_usage.get('output_tokens', 0) if isinstance(token_usage, dict) else getattr(token_usage, 'output_tokens', 0),
            'duration': timing.get('duration', 0) if isinstance(timing, dict) else getattr(timing, 'duration', 0),
            'log_file': current_log_file
        }
        pd.DataFrame([row]).to_csv(
            results_path,
            mode='a',
            header=needs_header,
            index=False
        )
        print(f"✓✓✓ Step {step_number} LOGGED to {results_path}")
    else:
        print(f"[LOGGING] Step {step_number} skipped - missing token_usage or timing")


def xr_agent_app(xr: SyncXR, agent: MultiStepAgent, params):
    global current_pk, current_request, current_mode, current_model, current_log_file, current_timestamp
    mode = params.get('mode') if isinstance(params, dict) else None
    mode = mode or current_mode or "xarp"
    custom_system_prompt = PROMPTS_BY_MODE.get(mode, xarp_system_prompt)
    agent.prompt_templates["system_prompt"] = custom_system_prompt + agent.prompt_templates["system_prompt"]
    
    # Register callback to log each step DURING execution
    print(f"[SETUP] Registering step callback for immediate logging")
    from smolagents import ActionStep
    
    # Register the callback - this will be called after each step
    agent.step_callbacks.register(ActionStep, log_step_immediately)
    
    xr.say("Starting scenario...")
    
    # Run the agent - steps will be logged in real-time via callback
    answer = agent.run(current_request, return_full_result=True)
    
    xr.write(f"Scenario {current_pk} completed!")
    
    print(f"Scenario {current_pk} execution complete.")
    # sys.exit(0)


def run_scenario(pk, scenario_text, mode, model_name):
    global current_pk, current_request, current_mode, current_model, current_log_file, current_timestamp
    current_pk = pk
    current_request = scenario_text
    current_mode = mode
    current_model = model_name
    
    # Create log directory if it doesn't exist
    os.makedirs('demos/logs', exist_ok=True)
    
    # Create log file for this scenario
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_timestamp = timestamp
    log_file = f'demos/logs/{current_pk}_{current_mode}_{timestamp}.txt'
    current_log_file = log_file
    
    # Redirect stdout and stderr to both console and file
    class TeeOutput:
        def __init__(self, *files):
            self.files = files
        def write(self, data):
            for f in self.files:
                f.write(data)
                f.flush()
        def flush(self):
            for f in self.files:
                f.flush()
        def isatty(self):
            return False
        def fileno(self):
            return self.files[0].fileno() if self.files else 0
    
    with open(log_file, 'w') as f:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = TeeOutput(original_stdout, f)
        sys.stderr = TeeOutput(original_stderr, f)
        try:
            print(f"=== Scenario {current_pk} started at {datetime.now()} ===")
            print(f"Request: {scenario_text[:100]}...")
            print("="*80)

            print(current_mode)
            if current_mode == "xarp":
                # show_qrcode_link()
                run_xr_agent(
                    xr_agent_app,
                    getModel(current_model=current_model),
                    allowed_tools=[
                        "info",
                        "write",
                        "say",
                        "read",
                        "passthrough",
                        "image",
                        "virtual_image",
                        "depth",
                        "eye",
                        "head",
                        "hands",
                        "list_assets",
                        "list_elements",
                        "destroy_element",
                        "create_or_update_glb",
                        "create_or_update_label",
                        "create_or_update_cube",
                        "create_or_update_sphere",
                        "create_or_update_image"
                    ],
                )
            else:
                run_xr_agent(
                    xr_agent_app,
                    getModel(current_model=current_model),
                    allowed_tools=["baseline_code"],
                )
        except SystemExit:
            pass  # Normal exit from xr_agent_app
        finally:
            print("="*80)
            print(f"=== Scenario {current_pk} ended at {datetime.now()} ===")
            print(f"Log saved to: {log_file}")
            sys.stdout = original_stdout
            sys.stderr = original_stderr



if __name__ == '__main__':
    # Read CSV with scenarios
    df = pd.read_csv("demos/xarp_inputs.csv", skipinitialspace=True)
    df.columns = df.columns.str.strip()
    
    # Clean up the Scenario column (remove leading/trailing spaces)
    df['Scenario'] = df['Scenario'].str.strip()
    df['Mode'] = df['Mode'].astype(str).str.strip()
    
    # Iterate through pk-based slice
    slice_df = df[df['pk'].astype(int) >= int(start_pk)].head(num_rows)
    for i, (idx, row) in enumerate(slice_df.iterrows()):
        pk_value = row.get('pk')
        if pk_value is None or (isinstance(pk_value, float) and pd.isna(pk_value)):
            raise ValueError("Missing pk value for scenario row; cannot map output without pk.")
        pk = int(pk_value)
        scenario_text = row['Scenario']
        mode = row['Mode']
        model_name = row['Model']
        
        
        print(f"\n{'='*80}")
        print(f"Starting Scenario {i + 1}/{len(slice_df)} (pk={pk})")
        print(f"Mode: {mode}, Model: {model_name}")
        print(f"{'='*80}\n")
        
        # Run the scenario
        run_scenario(pk, scenario_text, mode, model_name)
        
        # Clear terminal for next scenario
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print(f"Scenario {pk} completed. Ready for next scenario...")
        input("Press Enter to continue to the next scenario...")
        os.system('clear' if os.name == 'posix' else 'cls')
