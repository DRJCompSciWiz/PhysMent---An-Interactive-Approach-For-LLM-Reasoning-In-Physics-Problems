from inspect import Traceback
import os
import json
import logging

from AgentClass import (
    GLMAgent,
    KimiAgent,
    OpenAIAgent,
    LlamaAgent,
    Llama3370BAgent,
    GemmaAgent,
    GeminiAgent,
    AnthropicAgent,
    DeepSeekAgent,
    QwenAgent,
    MixtralAgent,
)
from Experiment import Experiment
from Data import Data
import argparse
import random
import threading
import config
from rich.progress import Progress
import time


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
    # OpenAI Models
    # ridiculous implementation of agent switching...preserving this for LEGACY code purposes
    # NOTE: FOR ALL NEW EXPERIMENTS, PLEASE JUST PUT "XXXAgent" in the [] and change the model via the config
    if agent_type == "OpenAIAgent":
        return OpenAIAgent()
    elif agent_type == "OpenAIAgentGPT4o":
        return OpenAIAgent(model="gpt-4o")
    elif agent_type == "OpenAIAgentGPT4omini":
        return OpenAIAgent(model="gpt-4o-mini")
    elif agent_type == "OpenAIAgentGPT4turbo":
        return OpenAIAgent(model="gpt-4-turbo")
    elif agent_type == "OpenAIAgentO1":
        return OpenAIAgent(model="o1")
    elif agent_type == "OpenAIAgentO1mini":
        return OpenAIAgent(model="o1-mini")
    elif agent_type == "OpenAIAgentGPT4.1mini":
        return OpenAIAgent(model="gpt-4.1-mini")
    elif agent_type == "OpenAIAgentGPT4.1":
        return OpenAIAgent(model="gpt-4.1")
    elif agent_type == "OpenAIAgentGPT5mini":
        return OpenAIAgent(model="gpt-5-mini")

    # Anthropic Models
    elif agent_type == "AnthropicAgentClaude35Sonnet":
        return AnthropicAgent(model="claude-3-5-sonnet-20241022")
    elif agent_type == "AnthropicAgentClaude35Haiku":
        return AnthropicAgent(model="claude-3-5-haiku-20241022")
    elif agent_type == "AnthropicAgentClaude37Sonnet":
        return AnthropicAgent(model="claude-3-7-sonnet-20250219")
    elif agent_type == "AnthropicAgentClaude4Sonnet":
        return AnthropicAgent(model="claude-sonnet-4-20250514")
    elif agent_type == "AnthropicAgentClaudeOpus4":
        return AnthropicAgent(model="claude-opus-4-6")
    elif agent_type == "AnthropicAgent":
        return AnthropicAgent()

    # Google Gemini Models
    elif agent_type == "GeminiAgent2Flash":
        return GeminiAgent(model_name="gemini-2.0-flash-exp")
    elif agent_type == "GeminiAgent25Pro":
        return GeminiAgent(model_name="gemini-2.5-pro")
    elif agent_type == "GeminiAgent25Flash":
        return GeminiAgent(model_name="gemini-2.5-flash")
    elif agent_type == "GeminiAgent":
        return GeminiAgent()

    # Together.ai Open Source Models
    elif agent_type == "LlamaAgent":
        return LlamaAgent()
    elif agent_type == "Llama3370BAgent":
        return Llama3370BAgent()
    elif agent_type == "GemmaAgent":
        return GemmaAgent()
    elif agent_type == "DeepSeekAgent":
        return DeepSeekAgent()
    elif agent_type == "QwenAgent":
        return QwenAgent()
    elif agent_type == "MixtralAgent":
        return MixtralAgent()
    elif agent_type == "KimiAgent":
        return KimiAgent()
    elif agent_type == "GLMAgent":
        return GLMAgent()
    # elif agent_type == "OpenRouterAgent":
    #     return OpenRouterAgent()

    else:
        raise ValueError(
            f"Unknown agent type: {agent_type}"
        )  # You can edit this part by adding more elif statements for other agents


def add_scenes(scene_list: list[str]) -> None:
    for id in range(config.start_scene, config.end_scene + 1):
        scene_list.append(id.__str__())


scene_ids: list[str] = []


def main():
    """
    Executes experiments for predefined scene IDs, collects results,
    and saves them to a JSON file.
    """
    parser = argparse.ArgumentParser()
    # TODO: This enable_python_tool is randomly set twice (once here once in Scene). WTF?? Fix this. For now, fixing this to False
    parser.add_argument(
        "--enable-python-tool",
        action="store_true",
        help="Enable the Python evaluation tool",
    )
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
    add_scenes(scene_ids)
    # Set the agent type (You can modify this to initialize different agents)
    agent_types: list[str] = (
        config.agents
    )  # Example: you can change this dynamically to switch agents

    iterations = config.iterations  # Example iterations, can be modified as needed

    # Set the base directory for test results
    base_dir = os.path.join(os.getcwd(), "TestResults")
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    # Define ablation methods (kept for future experimentation)
    methods = ["zero_shot", "one_shot", "one_shot_cot", "few_shot", "few_shot_cot"]

    for agent_type in agent_types:
        for iteration in iterations:
            with Progress() as scene_prog:
                task = scene_prog.add_task(
                    "Testing...", total=config.end_scene - config.start_scene
                )
                while not scene_prog.finished:
                    for scene_id in scene_ids:
                        try:
                            scene_prog.update(task, advance=1)
                            print(f"ON SCENE: {scene_id} ---")

                            # Reinitialize agent for each scene to prevent token exhaustion
                            agent = initialize_agent(agent_type)

                            # Run the experiment by first building experiment.py which initializes the scene and simulator
                            experiment = Experiment(
                                scene_id,
                                agent=agent,
                                max_iterations=iteration,
                                enable_python_tool=args.enable_python_tool,
                                agent_label=agent_type,
                            )
                            scene = (
                                experiment.scene
                            )  # Initialize the scene from experiments
                            # Default to zero_shot for every scene.
                            scene.set_prompt_method("zero_shot")
                            # To iterate across all methods in the future, replace the single call
                            # above with a loop like this and adjust logging/output paths if needed:
                            # for method in methods:
                            #     scene.set_prompt_method(method)
                            #     results = experiment.run_experiment()
                            scene_number = scene.scene_number
                            json_logger = JsonLogger(
                                os.path.join(
                                    base_dir,
                                    f"{agent_type}",
                                    f"{scene_number}",
                                    f"log_{experiment.timestamp}.json",
                                )
                            )

                            try:
                                results = experiment.run_experiment()
                            except Exception as e:
                                error_msg = str(e).lower()
                                if (
                                    "rate limit" in error_msg
                                    or "quota" in error_msg
                                    or "maximum context length" in error_msg
                                ):
                                    print(
                                        f"🚫 Rate limit or quota exceeded for {agent_type}. Skipping remaining scenes.\nError: {e}"
                                    )
                                    break  # Break out of scene loop and move on to the next model
                                else:
                                    print(
                                        f"⚠️ Unexpected error in scene {scene_id}: {e}"
                                    )
                                    continue  # Skip this scene but continue with others

                            # Process results
                            if results["answer_found"]:
                                print("\n=== Answer Summary ===")
                                print(f"LLM's Answer: {results['llm_answer']}")
                                print(f"Correct Answer: {results['correct_answer']}")
                                print(f"Answer Correct: {results['correct']}")
                            else:
                                print("\nNo answer was provided by the LLM.")

                            # Reset the simulator after the run
                            experiment.simulator.reset_sim()

                            data = Data(
                                scene_id,
                                log_json_path=json_logger.json_path,
                                scene=scene,
                                experiment=experiment,
                                iteration=iteration,
                                results=results,
                            )
                            data.summarize_scenes()
                        except Exception as e:
                            print(
                                f"Error with loading scene {scene_id}, skipping this scene for now..."
                            )
                            continue


if __name__ == "__main__":
    main()
