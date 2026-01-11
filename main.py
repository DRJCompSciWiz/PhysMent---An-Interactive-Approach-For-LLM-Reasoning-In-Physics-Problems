import os
import json
import logging
from AgentClass import (
    OpenAIAgent,
    LlamaAgent,
    GemmaAgent,
    GeminiAgent,
    AnthropicAgent,
    DeepSeekAgent
)
from Experiment import Experiment
from Data import Data
import argparse
import random
import threading

class JsonLogger:
    def __init__(self, json_path):
        self.json_path = json_path
        self.lock = threading.Lock()
        self.entries = []
        # Try to load existing entries if file exists
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    self.entries = json.load(f)
            except Exception:
                self.entries = []
        else:
        # Create an empty JSON file if it doesn't exist
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, indent=2, ensure_ascii=False)

    def log(self, kind, message):
        with self.lock:
            self.entries.append({kind: message})
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, indent=2, ensure_ascii=False)

class Tee:
    def __init__(self, *streams, json_logger=None):
        self.streams = streams
        self.json_logger = json_logger

    def write(self, message):
        for s in self.streams:
            s.write(message)
            s.flush()
        if self.json_logger and message.strip():
            self.json_logger.log("print", message.rstrip("\n"))

    def flush(self):
        for s in self.streams:
            s.flush()

class JsonLoggingHandler(logging.Handler):
    def __init__(self, json_logger):
        super().__init__()
        self.json_logger = json_logger

    def emit(self, record):
        msg = self.format(record)
        if record.levelno >= logging.ERROR:
            kind = "error"
        else:
            kind = "logging"
        self.json_logger.log(kind, msg)


def initialize_agent(agent_type: str):
    """
    Initialize the correct agent based on the provided agent_type string.
    """
    if agent_type == "OpenAIAgentGPT4omini":
        return OpenAIAgent(model="gpt-4o-mini")
    
    elif agent_type == "OpenAIAgentGPT4.1mini":
        return OpenAIAgent(model="gpt-4.1-mini")
    
    elif agent_type == "OpenAIAgentGPT4.1":
        return OpenAIAgent(model="gpt-4.1")

    elif agent_type == "LlamaAgent":
        return LlamaAgent()
    
    elif agent_type == "GemmaAgent":
        return GemmaAgent()
    
    elif agent_type == "GeminiAgent":
        return GeminiAgent()
    
    elif agent_type == "AnthropicAgent":
        return AnthropicAgent()
    
    elif agent_type == "DeepSeekAgent":
        return DeepSeekAgent()
    
    else:
        raise ValueError(f"Unknown agent type: {agent_type}") # You can edit this part by adding more elif statements for other agents
    
def main():
    """
    Executes experiments for predefined scene IDs, collects results, 
    and saves them to a JSON file.
    """
    parser = argparse.ArgumentParser()
    # TODO: This enable_python_tool is randomly set twice (once here once in Scene). WTF?? Fix this. For now, fixing this to False
    parser.add_argument("--enable-python-tool", action="store_true", help="Enable the Python evaluation tool")
    args = parser.parse_args()
    # args.enable_python_tool = random.choice([True, False])
    args.enable_python_tool = False
    if args.enable_python_tool:
        print("✅ Python tool enabled")
        # Pass this flag into Experiment or wherever tool setup happens
        # e.g., Experiment(enable_python_tool=True)
    else:
        print("❌ Python tool disabled")

    # Predefined list of scene IDs to iterate through
    scene_ids = ["151"]  # Replace with actual scene IDs

    # Set the agent type (You can modify this to initialize different agents)
    agent_types = ["OpenAIAgentGPT4omini"]  # Example: you can change this dynamically to switch agents

    iterations = [5]  # Example iterations, can be modified as needed

    # Set the base directory for test results
    base_dir = os.path.join(os.getcwd(), "TestResults")
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # Define scene groups (6 blocks of 25 scenes)
    scene_groups = [list(map(str, range(i, i + 25))) for i in range(1, 151, 25)]

    # Store the assigned methods per scene variation
    scene_to_method = {}

    # Define ablation methods
    methods = ["zero_shot", "one_shot", "one_shot_cot", "few_shot", "few_shot_cot"]

    for group in scene_groups:
        selected = random.sample(group, 25)
        for i, method in enumerate(methods):
            for scene_id in selected[i * 5:(i + 1) * 5]:
                scene_num = int(scene_id)
                # Determine number of variations
                if 1 <= scene_num <= 50:
                    num_variations = 6
                elif 51 <= scene_num <= 100:
                    num_variations = 4
                elif 101 <= scene_num <= 150:
                    num_variations = 3
                else:
                    continue  # skip if out of range
                # Assign method to all variations
                for v in range(1, num_variations + 1):
                    variation_id = f"{scene_num}.{v}"
                    scene_to_method[variation_id] = method

    for agent_type in agent_types:
        # Initialize the agent based on the string (this part is your new dynamic agent initialization)
        agent = initialize_agent(agent_type)
        for iteration in iterations:
            for scene_id in scene_ids:
                # Run the experiment by first building experiment.py which initializes the scene and simulator
                experiment = Experiment(scene_id, agent=agent, max_iterations=iteration, enable_python_tool=args.enable_python_tool, agent_label=agent_type)
                scene = experiment.scene  # Initialize the scene from experiments
                method = scene_to_method.get(scene_id, "zero_shot")
                scene.set_prompt_method(method)
                scene_number = scene.scene_number
                json_logger = JsonLogger(os.path.join(base_dir, f"{agent_type}", f"{scene_number}", f"log_{experiment.timestamp}.json"))


                try:
                    results = experiment.run_experiment()
                except Exception as e:
                    error_msg = str(e).lower()
                    if "rate limit" in error_msg or "quota" in error_msg or "maximum context length" in error_msg:
                        print(f"🚫 Rate limit or quota exceeded for {agent_type}. Skipping remaining scenes.\nError: {e}")
                        break  # Break out of scene loop and move on to the next model
                    else:
                        print(f"⚠️ Unexpected error in scene {scene_id}: {e}")
                        continue  # Skip this scene but continue with others

                # Process results
                if results['answer_found']:
                    print("\n=== Answer Summary ===")
                    print(f"LLM's Answer: {results['llm_answer']}")
                    print(f"Correct Answer: {results['correct_answer']}")
                    print(f"Answer Correct: {results['correct']}")
                else:
                    print("\nNo answer was provided by the LLM.")
                
                # Reset the simulator after the run
                experiment.simulator.reset_sim()

                data = Data(scene_id, log_json_path=json_logger.json_path, scene=scene, experiment=experiment, iteration=iteration, results=results)
                data.summarize_scenes()

if __name__ == "__main__":
    main()
