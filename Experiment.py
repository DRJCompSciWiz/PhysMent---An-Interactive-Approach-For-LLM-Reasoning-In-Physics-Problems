"""Experiment orchestration for the LLM-simulator interaction loop."""

import json
import os
import time
import logging
from dotenv import load_dotenv
from Simulator import Simulator
from Scene import Scene
from AgentClass import OpenAIAgent, OpenRouterAgent, LlamaAgent, GemmaAgent, GeminiAgent, AnthropicAgent, DeepSeekAgent, BaseTogetherAgent
from typing import Any, Dict, List
from datetime import datetime
import re

# Load environment variables from the .env file
load_dotenv()

# API Key loaded once globally
api_key = os.getenv('OPENAI_API_KEY')

class Experiment:
    """Coordinate one scene, simulator, and LLM agent run."""
    def __init__(self, scene_id: str, agent, max_iterations: int, enable_python_tool: bool = False, agent_label: str | None = None):
        """
        Initialize the Experimental class with a Scene ID and set up the necessary components.
        
        Args:
            scene_id (str): The unique identifier for the simulation scene.
            max_iterations (int): The maximum number of iterations allowed for the experiment (default is 5).
            enable_python_tool (bool): Whether to enable the Python evaluation tool (default is False).
        """
        self.max_iterations = max_iterations
        self.enable_python_tool = enable_python_tool
        self.name_of_agent = agent_label or agent.__class__.__name__
        self.simulator = Simulator(scene_id, agent.__class__.__name__)  # Create the Simulator object
        self.scene = Scene(scene_id, enable_python_tool=self.enable_python_tool, simulator=self.simulator)  # Initialize Scene with the simulator
        self.agent = agent if isinstance(agent, (OpenAIAgent, OpenRouterAgent, LlamaAgent, GemmaAgent, GeminiAgent, AnthropicAgent, DeepSeekAgent, BaseTogetherAgent)) else OpenAIAgent(model="gpt-4o-mini", api_key=api_key) # Initialize AI agent with the API key
        self.timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        log_filename = f"summary_{self.timestamp}.txt"
        self.log_dir = os.path.join(os.getcwd(), "TestResults", self.name_of_agent, f"{self.scene.scene_number}")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file_path = os.path.join(self.log_dir, log_filename)
        self.correct_answer_found = False  # Flag to track if the correct answer was found
        self.elapsed_seconds = 0  # Initialize elapsed seconds for the experiment

        # Create or clear the file at the beginning of the run
        with open(self.log_file_path, "w") as f:
            f.write(f"=== Experiment Log for {self.scene.scene_id} ===\n\n")

        # Tool mapping to bind methods from the simulator to be called dynamically
        self.tool_mapping = {
            "get_parameters": self.simulator.get_parameters,
            "get_displacement": self.simulator.get_displacement,
            "compute_force": self.simulator.compute_force,
            "set_velocity": self.simulator.set_velocity,
            "apply_force": self.simulator.apply_force,
            "apply_torque": self.simulator.apply_torque,
            "get_velocity": self.simulator.get_velocity,
            "detect_collision": self.simulator.detect_collision,
            "move_object": self.simulator.move_object,
            "get_position": self.simulator.get_position,
            "get_torque": self.simulator.get_torque,
            "get_center_of_mass": self.simulator.get_center_of_mass,
            "get_angular_momentum": self.simulator.get_angular_momentum,
            "get_momentum": self.simulator.get_momentum,
            "get_acceleration": self.simulator.get_acceleration,
            "get_kinetic_energy": self.simulator.get_kinetic_energy,
            "get_potential_energy": self.simulator.get_potential_energy,
            "get_rotational_energy": self.simulator.get_rotational_energy,
            "change_position": self.simulator.change_position,
            "quat_to_rot_matrix": self.simulator.quat_to_rot_matrix,
            "create_objects": self.simulator.create_objects,
            "find_objects": self.simulator.find_objects,
            "attach_objects": self.simulator.attach_objects,
            "delete_objects": self.simulator.delete_objects,
            "step": self.simulator.step,
            "answer": lambda answer: {"acknowledged": True},
            "reset_sim": self.simulator.reset_sim
        }

    def python_tool(self, code: str):
        """Evaluate a small Python expression for optional computation support."""
        try:
            # Using eval() to execute the Python code
            result = eval(code)
            return result
        except Exception as e:
            return f"Error executing code: {str(e)}"
        
    @staticmethod
    def _normalize_answer(answer) -> str:
        """Normalize an answer string for comparison.

        Strips whitespace, units, 'object_' prefixes, brackets, and lowercases.
        """
        if answer is None:
            return ""
        s = str(answer).strip()
        # Remove surrounding brackets / parentheses
        s = re.sub(r'^[\[\(]+', '', s)
        s = re.sub(r'[\]\)]+$', '', s)
        # Remove common unit suffixes (m/s, m/s², N, kg, J, W, m, s, rad, rad/s, etc.)
        s = re.sub(r'\s*(m/s²|m/s2|m/s|rad/s|kg·m/s|kg\*m/s|N·m|N\*m|rad|kg|m|N|J|W|s)\s*$', '', s, flags=re.IGNORECASE)
        # Remove 'object_' prefix (e.g., "object_2" -> "2")
        s = re.sub(r'\bobject_', '', s, flags=re.IGNORECASE)
        s = s.strip()
        return s

    def _check_answer(self, final_answer, correct_answer) -> bool:
        """Robustly compare the LLM's answer against the correct answer.

        Handles: exact match, single numeric, multi-value CSV, bidirectional
        substring containment, and keyword extraction.
        """
        if final_answer is None or correct_answer is None:
            return False

        norm_final = self._normalize_answer(final_answer)
        norm_correct = self._normalize_answer(correct_answer)

        # --- Step 1: Exact match after normalization ---
        if norm_final.lower() == norm_correct.lower():
            return True

        # --- Step 2: Single numeric comparison (tolerance 0.1) ---
        try:
            final_float = float(norm_final)
            correct_float = float(norm_correct)
            if abs(final_float - correct_float) < 0.1:
                return True
        except (ValueError, TypeError):
            pass

        # --- Step 3: Multi-value CSV comparison ---
        if ',' in str(correct_answer):
            try:
                correct_parts = [p.strip() for p in norm_correct.split(',')]
                final_parts = [p.strip() for p in norm_final.split(',')]
                if len(correct_parts) == len(final_parts):
                    all_match = True
                    for cp, fp in zip(correct_parts, final_parts):
                        try:
                            if abs(float(fp) - float(cp)) >= 0.1:
                                all_match = False
                                break
                        except (ValueError, TypeError):
                            if fp.lower() != cp.lower():
                                all_match = False
                                break
                    if all_match:
                        return True
            except Exception:
                pass

        # --- Step 4: Bidirectional substring containment ---
        final_lower = norm_final.lower()
        correct_lower = norm_correct.lower()
        if final_lower and correct_lower:
            if final_lower in correct_lower or correct_lower in final_lower:
                return True

        # --- Step 5: Keyword extraction for conceptual answers ---
        # Extract all numbers from both answers and compare
        final_nums = re.findall(r'-?\d+\.?\d*', norm_final)
        correct_nums = re.findall(r'-?\d+\.?\d*', norm_correct)
        if final_nums and correct_nums and len(final_nums) == len(correct_nums):
            try:
                all_nums_match = all(
                    abs(float(fn) - float(cn)) < 0.1
                    for fn, cn in zip(final_nums, correct_nums)
                )
                if all_nums_match:
                    return True
            except (ValueError, TypeError):
                pass

        return False

    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Compact tool results into a concise string for the LLM prompt."""
        lines = []
        last_time = None
        for r in results:
            tool = r["tool"]
            params = r.get("parameters", {})
            result = r.get("result")
            last_time = r.get("sim_time", last_time)
            params_str = ", ".join(f'{k}={json.dumps(v)}' for k, v in params.items())
            if result is None:
                result_str = "ok"
            elif isinstance(result, dict) and "error" in result:
                result_str = f"ERROR: {result['error']}"
            else:
                result_str = json.dumps(result) if not isinstance(result, str) else result
            lines.append(f"{tool}({params_str}) -> {result_str}")
        if last_time is not None:
            lines.append(f"[sim_time={last_time}]")
        return "\n".join(lines)

    def execute_tool_calls(self, tool_calls_json: str) -> tuple[List[Dict[str, Any]], int, int]:
        """
        Execute the provided tool calls, log the results, and return them along with success/error counts.

        Args:
            tool_calls_json (str): A JSON string representing the tool calls to be executed.

        Returns:
            tuple: A tuple containing:
                - List[Dict[str, Any]]: A list of dictionaries containing the results of each tool call
                - int: Number of successful tool calls
                - int: Number of failed tool calls
        """
        tool_calls = json.loads(tool_calls_json)  # Parse the JSON string into a list of tool calls
        aggregated_results = []  # Initialize a list to store the results of the tool calls
        successful_calls = 0
        failed_calls = 0

        for call in tool_calls:
            tool = call['tool']
            params = call['parameters']
            result = None

            try:
                # Attempt to find and execute the tool if it exists in the mapping
                if tool in self.tool_mapping:
                    func = self.tool_mapping[tool]
                    result = func(**params)  # Execute the function dynamically with the parameters
                    successful_calls += 1
                else:
                    raise ValueError(f"Unknown tool '{tool}'")
            except Exception as e:
                # If an exception occurs during the execution of a tool, log it and return an error result
                logging.error(f"Exception during '{tool}': {str(e)}")
                result = {"error": str(e)}
                failed_calls += 1

            # Append the result, including the tool name, parameters, and result to the aggregated results
            aggregated_results.append({
                "tool": tool,
                "parameters": params,
                "result": result,
                "sim_time": self.simulator.time  # Record the simulation time during this call
            })

        return aggregated_results, successful_calls, failed_calls

    def extract_json_response(self, llm_output: str) -> str:
        """
        Extract a JSON response from the output of the LLM (Large Language Model).

        Args:
        llm_output (str): The raw output string from the LLM.

        Returns:
            str: A valid JSON string representing the response extracted from the LLM output.

        Raises:
        ValueError: If the LLM output is not in valid JSON format.

        """
        def _extract_fenced_blocks(text: str) -> list[str]:
            """Extract fenced code blocks from model output."""
            blocks = []
            start = 0
            while True:
                fence_start = text.find("```", start)
                if fence_start == -1:
                    break
                fence_end = text.find("```", fence_start + 3)
                if fence_end == -1:
                    break
                block = text[fence_start + 3:fence_end].strip()
                lines = block.splitlines()
                if lines and lines[0].strip().isalpha():
                    block = "\n".join(lines[1:]).strip()
                blocks.append(block)
                start = fence_end + 3
            return blocks

        def _extract_json_candidate(text: str, start_idx: int) -> str | None:
            """Return a balanced JSON object or array candidate from text."""
            start = None
            stack = []
            in_string = False
            escape = False
            for idx in range(start_idx, len(text)):
                ch = text[idx]
                if start is None:
                    if ch in "[{":
                        start = idx
                        stack.append(ch)
                    continue
                if in_string:
                    if escape:
                        escape = False
                    elif ch == "\\":
                        escape = True
                    elif ch == "\"":
                        in_string = False
                    continue
                if ch == "\"":
                    in_string = True
                    continue
                if ch in "[{":
                    stack.append(ch)
                    continue
                if ch in "]}":
                    if not stack:
                        break
                    open_ch = stack.pop()
                    if (open_ch == "[" and ch != "]") or (open_ch == "{" and ch != "}"):
                        break
                    if not stack:
                        return text[start:idx + 1]
            return None

        try:
            for block in _extract_fenced_blocks(llm_output):
                try:
                    json_obj = json.loads(block)
                    if isinstance(json_obj, list):
                        return json.dumps(json_obj)
                    return json.dumps([json_obj])
                except Exception:
                    continue

            text = llm_output
            for idx, ch in enumerate(text):
                if ch not in "[{":
                    continue
                candidate = _extract_json_candidate(text, idx)
                if candidate is None:
                    continue
                try:
                    json_obj = json.loads(candidate)
                    if isinstance(json_obj, list):
                        return json.dumps(json_obj)
                    return json.dumps([json_obj])
                except Exception:
                    continue

            raise ValueError("No JSON object or array found in response.")
        except Exception as e:
            logging.warning(f"JSON parsing error: {e}, response: {llm_output}")
            raise ValueError(f"Invalid JSON syntax. Error: {e}")


    def run_experiment(self) -> Dict[str, Any]:
        """
        Run the experiment using the simulator and AI agent. This method orchestrates the experiment by
        interacting with the simulation and utilizing the AI agent to decide the next steps.
        The loop will continue until the correct answer is found or the maximum number of iterations is reached.

        Returns:
            Dict[str, Any]: A dictionary containing the results of the experiment, including whether the
            correct answer was found, if a timeout occurred, the number of tool calls made,
            and the number of iterations performed.
        """
        start_time = time.time()  # Record the start time of the experiment
        self.simulator.reset_sim()  # Reset the simulator to its initial state
        correct_answer_found = False  # Flag to track if the correct answer was found
        timeout_occurred = False  # Flag to track if the maximum number of iterations was reached
        llm_final_answer = None  # Add this line to store the LLM's answer
        correct_answer_value = None  # Add this line to store the correct answer    
        
        # Get the scene prompt and tool descriptions from the Scene object
        scene_prompt = self.scene.generate_prompt()
        results = []  # List to store the results of tool calls during each iteration
        all_results = []  # Accumulate tool call results across iterations for logging
        num_tool_calls = 0  # Counter to track the number of tool calls made during the experiment
        tool_history = []  # Track tool calls to detect loops
        tool_usage = {}
        successful_tool_calls = 0  # Track successful tool executions
        failed_tool_calls = 0  # Track failed tool executions
        llm_input_prompt = scene_prompt
        itr = 0  # Initialize iteration counter to 0 before the loop starts

        while itr < self.max_iterations:
            remaining = self.max_iterations - itr - 2  # Correct remaining iterations

            logging.info(f"STEP: {itr + 1}")
            logging.info(f"Input to model: {llm_input_prompt}")

            llm_response = self.agent.interact(llm_input_prompt)

            with open(self.log_file_path, "a", encoding='utf-8') as f:
                f.write(f"\n--- Iteration {itr + 1} ---\n")
                f.write(f"LLM Input Prompt Below:\n{llm_input_prompt}\n\n")
                f.write(f"LLM Response Below:\n{llm_response}\n")

            logging.info(f"Output from model: {llm_response}")

            try:
                tool_calls_json_str = self.extract_json_response(str(llm_response))
                tool_calls_json_obj = json.loads(tool_calls_json_str)
                tool_history.append(tool_calls_json_str)
            except ValueError:
                # Construct the error message listing the tools that caused invalid JSON
                error_msg = f"Error: Invalid JSON syntax for tool(s). Please try again with proper syntax."
                
                # Update the LLM input prompt with the error message
                llm_input_prompt = (f"Previous results: {error_msg}\n"
                                    f"IMPORTANT: You have {remaining} iterations remaining to use the 'answer' tool.\n"
                                    f"What should I do next?")

                # Increment iteration number and proceed to the next iteration
                itr += 1  # Move to the next iteration after an invalid JSON error
                continue  # Proceed to the next iteration of the loop

            logging.info(f"\n=== Executing Tool Calls (Iteration {itr + 1}) ===")

            # Answer logic: Check if any tool call contains an answer and check if it's correct
            answer_found = False
            correct_answer_found = False

            for call in tool_calls_json_obj:  # Use the parsed object, not the string
                if call['tool'] == 'answer':
                    final_answer = call['parameters'].get('answer')  # Get the answer from parameters
                    correct_answer = self.scene.get_correct_answer()  # Retrieve correct answer from scene
                    
                    # Mark the answer as found
                    if final_answer is not None:
                        answer_found = True

                        # Store answers for reporting
                        llm_final_answer = final_answer
                        correct_answer_value = correct_answer

                        tool_usage['answer'] = tool_usage.get('answer', 0) + 1
                        num_tool_calls += 1
                        successful_tool_calls += 1  # Count answer as successful tool call
                    else:
                        # Log warning and provide feedback when null answer is given
                        logging.warning("LLM provided a null answer value")
                        results.append({
                            "tool": "answer",
                            "error": "Null answer provided. Please call the answer tool with a valid value."
                        })
                        num_tool_calls += 1
                        failed_tool_calls += 1  # Count null answer as failed tool call
                        # Do not mark as found when answer is null
                        answer_found = False
                    # Robust answer validation using _check_answer
                    correct_answer_found = self._check_answer(final_answer, correct_answer)
                    
                    break  # Stop the experiment as soon as we get an answer (whether correct or not)
            
            # If an answer is found (correct or not), exit the loop early
            if answer_found:
                break  # Stop looping once an answer is provided by the LLM
            
            # If no answer is found, execute the tool calls as planned
            if not answer_found:
                results, success_count, error_count = self.execute_tool_calls(tool_calls_json_str)  # Execute tool calls and get results
                all_results.extend(results)
                successful_tool_calls += success_count
                failed_tool_calls += error_count
                for result in results:
                    tool_name = result['tool']
                    tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
                num_tool_calls += len(results)  # Increment the tool call count after execution

                llm_input_prompt = (f"Previous Results:\n{self._format_results(results)}\n"
                                    f"IMPORTANT: You have {remaining} iterations remaining to use the 'answer' tool.\n"
                                    f"What should I do next?")

            itr += 1  # Increment the iteration counter only when iteration completes successfully
   
                
        # If the loop completes without finding the answer, set the timeout flag
        if itr == self.max_iterations - 1 and not answer_found:
            timeout_occurred = True

        logging.info("\n=== Tool Usage Statistics ===")
        logging.info(f"Total number of tool calls: {num_tool_calls}")
        logging.info("Tools used:")
        for tool, count in sorted(tool_usage.items()):
            logging.info(f"  - {tool}: {count} times")

        # Write final experiment summary to experimentslog{scene_id}.txt
        with open(self.log_file_path, "a") as f:
            f.write("\n=== Final Experiment Summary ===\n")
            f.write("\n--- Final Answer Submitted ---\n")
            f.write(f"LLM's Final Answer: {llm_final_answer}\n")
            f.write(f"Correct Answer: {correct_answer_value}\n")
            f.write(f"Is Correct: {correct_answer_found}\n")
            f.write(f"Answer Found: {answer_found}\n")
            f.write(f"Timeout Occurred: {timeout_occurred}\n")
            
            f.write("\n--- Tool Usage Statistics ---\n")
            f.write(f"Total number of tool calls: {num_tool_calls}\n")
            f.write(f"Successful tool calls: {successful_tool_calls}\n")
            f.write(f"Failed tool calls: {failed_tool_calls}\n")
            f.write(f"Success rate: {successful_tool_calls / max(num_tool_calls, 1) * 100:.1f}%\n")
            f.write("Tools used:\n")
            for tool, count in sorted(tool_usage.items()):
                f.write(f"  - {tool}: {count} times\n")

            f.write("\n--- Tool Call History ---\n")
            for i, call in enumerate(tool_history, 1):
                f.write(f"  [{i}] {call}\n")

            f.write("\n--- Tool Call Results ---\n")
            for i, result in enumerate(all_results, 1):
                f.write(f"  [{i}] {result}\n")

            # Append Python tool status
            f.write(f"\n--- Python Tool Status ---\n")
            f.write(f"Python Tool Enabled: {self.enable_python_tool}\n")

            total_iterations = self.max_iterations if timeout_occurred else itr + 1  # Increment by 1 if answer is found, or not completed by max iterations
            f.write(f"\nTotal number of iterations: {total_iterations}\n")
        
        # Return the results of the experiment, including whether the correct answer was found and other statistics
        experiment_results = {
            'correct': correct_answer_found,  # Whether the correct answer was found
            'timeout': timeout_occurred,  # Whether the experiment timed out after max iterations
            'num_tool_calls': num_tool_calls,  # Total number of tool calls made
            'iterations': itr + 1 if not timeout_occurred else self.max_iterations,  # Total iterations performed
            'answer_found': answer_found,  # Whether any answer was provided (regardless of correctness)
            'tool_usage': tool_usage,
            'llm_answer': llm_final_answer,
            'correct_answer': correct_answer_value,
            'successful_calls': successful_tool_calls,  # Number of successful tool executions
            'failed_calls': failed_tool_calls  # Number of failed tool executions
        } 

        end_time = time.time()
        self.elapsed_seconds = end_time - start_time

        return experiment_results  # Return the results of the experiment
    
