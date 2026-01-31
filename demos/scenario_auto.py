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
model_id = "mistralai/devstral-small-2-2512"

model = OpenAIServerModel(
    model_id=model_id,
    api_key=lm_studio,
    api_base="http://128.111.28.74:1234/v1"
)

custom_system_prompt = """
You are an agent with extended reality tools. You can sense the environment and display information.
Before asking me about for extra information, use your tools to understand the context.
The user cannot read the output of "print" functions, use the "write" or "say" tools instead.

When you have successfully completed the user's request by calling the appropriate tools,
immediately return your final answer. Do not wait for confirmation or try to verify the results.
"""

# Set your starting index here (0-based)
input_csv_start_idx = 1  # starts from idx=0 CHANGE THIS IF NEEDED
num_rows = 2 # flow only lasts 2 scenarios

# Global variables to track current scenario
current_scenario_number = 0 
current_request = ""
current_mode = ""
current_model = ""

def xr_agent_app(xr: SyncXR, agent: MultiStepAgent, params):
    global current_scenario_number, current_request, current_mode, current_model
    
    agent.prompt_templates["system_prompt"] = custom_system_prompt + agent.prompt_templates["system_prompt"]
    # Disable periodic image display on screen
    # xr.image().obj.show()
    
    xr.say("Starting scenario...")
    answer = agent.run(current_request, return_full_result=True)
    
    # Create rows for each step
    step_rows = []
    for step_dict in answer.steps:
        if 'token_usage' in step_dict and step_dict['token_usage']:
            step_rows.append({
                'scenario_number': current_scenario_number,
                'mode': current_mode,
                'model': current_model,
                'request': current_request[:20],
                'step_number': step_dict.get('step_number', '?'),
                'input_tokens': step_dict['token_usage']['input_tokens'],
                'output_tokens': step_dict['token_usage']['output_tokens'],
                'duration': step_dict['timing']['duration']
            })
    
    # Create DataFrame and append to CSV
    if step_rows:
        results_df = pd.DataFrame(step_rows)
        results_df.to_csv('demos/results.csv', mode='a', header=not os.path.exists('demos/results.csv'), index=False)
    
    xr.write(f"Scenario {current_scenario_number} completed! {len(step_rows)} steps logged.")
    
    print(f"Scenario {current_scenario_number} execution complete.")
    sys.exit(0)


def run_scenario(scenario_number, scenario_text, mode, model_name):
    global current_scenario_number, current_request, current_mode, current_model
    current_scenario_number = scenario_number
    current_request = scenario_text
    current_mode = mode
    current_model = model_name
    
    # Create log directory if it doesn't exist
    os.makedirs('demos/logs', exist_ok=True)
    
    # Create log file for this scenario
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f'demos/logs/s{scenario_number}_{current_mode}_{timestamp}.txt'
    
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
            print(f"=== Scenario {scenario_number} started at {datetime.now()} ===")
            print(f"Request: {scenario_text[:100]}...")
            print("="*80)
            show_qrcode_link()
            run_xr_agent(xr_agent_app, model)
        except SystemExit:
            pass  # Normal exit from xr_agent_app
        finally:
            print("="*80)
            print(f"=== Scenario {scenario_number} ended at {datetime.now()} ===")
            print(f"Log saved to: {log_file}")
            sys.stdout = original_stdout
            sys.stderr = original_stderr


if __name__ == '__main__':
    # Read CSV with scenarios
    df = pd.read_csv("demos/xarp_inputs.csv")
    df.columns = df.columns.str.strip()
    
    # Clean up the Scenario column (remove leading/trailing spaces)
    df['Scenario'] = df['Scenario'].str.strip()
    

    
    # Iterate through the desired slice only
    for i, (idx, row) in enumerate(df.iloc[input_csv_start_idx:input_csv_start_idx+num_rows].iterrows()):
        scenario_number = i + 1
        scenario_text = row['Scenario']
        mode = row['Mode']
        model_name = row['Model']
        
        print(f"\n{'='*80}")
        print(f"Starting Scenario {scenario_number}/{len(df)}")
        print(f"Mode: {mode}, Model: {model_name}")
        print(f"{'='*80}\n")
        
        # Run the scenario
        run_scenario(scenario_number, scenario_text, mode, model_name)
        
        # Clear terminal for next scenario
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print(f"Scenario {scenario_number} completed. Ready for next scenario...")
        input("Press Enter to continue to the next scenario...")
        os.system('clear' if os.name == 'posix' else 'cls')
