"""Experiment metric aggregation and result-summary helpers."""

import os
import json
from Scene import Scene
from Experiment import Experiment


class Data:
    """
    A class responsible for storing and processing data related to a scene and its experiment.

    Attributes:
        scene_id (str): The identifier for the scene.
        log_json_path (str): The path where the log data will be saved.
        scene (Scene): The Scene object associated with the experiment.
        experiment (Experiment): The Experiment object that defines the experiment details.
        summary (list): A list that holds summaries of the experiment.
        agent_type (str): The agent type, which is extracted from the experiment.
        base_dir (str): The base directory where the test results are saved.
    
    Methods:
        append_summary_to_log(summary):
            Appends a summary of the experiment to the log file in JSON format.
        
        summarize_scenes():
            Creates a summary of the scene based on various scores and experiment results, and appends it to the log.

        whole_scene_summary():
            Collects data from multiple variations of a scene and writes an overall summary to a .txt file.
    """
    def __init__(self, scene_id, log_json_path, scene: Scene, experiment: Experiment, iteration: int, results=None):
        """
        Initializes the Data object with the provided scene, log path, and experiment details.

        Parameters:
            scene_id (str): The unique identifier for the scene.
            log_json_path (str): The path where the log data will be saved.
            scene (Scene): The Scene object associated with the experiment.
            experiment (Experiment): The Experiment object that defines the experiment details.
        """
        self.scene_id = scene_id
        self.scene_number = self.scene_id.split(".")[1] if "." in self.scene_id else self.scene_id
        self.log_json_path = log_json_path
        self.scene = scene
        self.experiment = experiment
        self.iteration = iteration
        self.results = results
        self.summary = []  # Initialize an empty list to store summaries
        self.agent_type = self.experiment.name_of_agent  # Get the agent type from the experiment
        full_path = os.path.abspath(__file__)
        directory = os.path.dirname(full_path)
        self.base_dir = os.path.join(directory, "TestResults")

    def append_summary_to_log(self, summary):
        """
        Appends a summary of the experiment to the log file in JSON format.

        Parameters:
            summary (dict): A dictionary containing the summary data to append to the log.

        Returns:
            None
        """

        # Load existing log entries
        if os.path.exists(self.log_json_path):
            try:
                with open(self.log_json_path, "r", encoding="utf-8") as f:
                    entries = json.load(f)
            except Exception:
                entries = []
        else:
            entries = []
        # Append the summary as a new entry
        entries.insert(0, {"summary": summary})
        # Write back to the log file
        with open(self.log_json_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)

    def compute_auto_scores(self):
        """
        Automatically computes all research metrics based on experiment results.

        Returns:
            dict: Dictionary containing all computed scores (0-1 scale)
        """
        if self.results is None:
            raise ValueError("Experiment results not provided; cannot compute scores.")

        results = self.results
        num_tool_calls = results['num_tool_calls']
        tool_usage = results['tool_usage']
        iterations = results['iterations']
        successful_calls = results.get('successful_calls', num_tool_calls)  # Default to all successful if not tracked
        failed_calls = results.get('failed_calls', 0)

        # 1. Correctness Score (use results dict instead of experiment attribute)
        correctness_score = 1.0 if results.get('correct', False) else 0.0

        # 2. Efficiency Score - measures resource usage efficiency
        iteration_efficiency = 1.0 - (iterations / max(self.experiment.max_iterations, 1))
        tool_call_efficiency = 1.0 - min(num_tool_calls / 20.0, 1.0)  # Cap at 20 calls
        time_efficiency = 1.0 - min(self.experiment.elapsed_seconds / 120.0, 1.0)  # Cap at 2 minutes
        efficiency_score = (iteration_efficiency + tool_call_efficiency + time_efficiency) / 3.0

        # 3. Groundedness Score - measures reliance on simulation data
        query_tools = ['get_velocity', 'get_position', 'get_parameters', 'get_displacement',
                       'get_acceleration', 'get_torque', 'get_center_of_mass', 'get_potential_energy',
                       'get_kinetic_energy', 'get_rotational_energy', 'get_momentum',
                       'get_angular_momentum', 'detect_collision', 'find_objects']

        query_count = sum(tool_usage.get(tool, 0) for tool in query_tools)
        total_non_answer_calls = num_tool_calls - tool_usage.get('answer', 0)
        groundedness_score = query_count / max(total_non_answer_calls, 1)
        groundedness_score = min(groundedness_score, 1.0)  # Cap at 1.0

        # 4. Action Validity Score - measures success rate of tool executions
        action_validity_score = successful_calls / max(successful_calls + failed_calls, 1)

        # 5. Reasoning Score - heuristic-based problem-solving quality
        # Tool diversity: how many unique tools used
        tool_diversity = len(tool_usage) / 26.0  # 26 total tools available

        # Appropriate tool usage for computation problems
        has_step = 'step' in tool_usage
        has_queries = any(tool in tool_usage for tool in query_tools)
        appropriate_tools = 1.0 if (has_step and has_queries) else 0.5

        # No excessive repetition: penalize if one tool dominates
        max_tool_usage = max(tool_usage.values()) if tool_usage else 0
        repetition_penalty = min(max_tool_usage / max(num_tool_calls, 1), 1.0)
        balance_score = 1.0 - (repetition_penalty * 0.5)  # 50% penalty for full repetition

        reasoning_score = (tool_diversity + appropriate_tools + balance_score) / 3.0

        # 6. Generalization Score - tool diversity proxy
        unique_tool_ratio = len(tool_usage) / max(num_tool_calls, 1)
        generalization_score = unique_tool_ratio

        return {
            'correctness': correctness_score,
            'efficiency': efficiency_score,
            'groundedness': groundedness_score,
            'action_validity': action_validity_score,
            'reasoning': reasoning_score,
            'generalization': generalization_score,
            'query_tool_ratio': query_count / max(total_non_answer_calls, 1),
            'tool_diversity_ratio': tool_diversity,
            'success_rate': action_validity_score
        }

    def summarize_scenes(self):
        """
        Creates a summary for the experiment based on the scene type and scores, and appends it to the log.

        This method categorizes the scene type into different categories (e.g., Easy, Hard, Multi-Physics Concepts) based on 
        the scene number, and calculates corresponding scores (reasoning, groundedness, action validity, and generalization) 
        for the experiment. The results from the experiment are incorporated into the summary.

        Returns:
            None
        """
        try:
            scene_num = int(self.scene_number)
        except (TypeError, ValueError):
            scene_num = -1

        if scene_num in range (1, 16):
            self.scene_type = "Easy Single Physics Concepts"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.2, 0.4, 0.3, 0.1
        elif scene_num in range(16, 21):
            self.scene_type = "Easy Single Physics Concepts With Focus On Creating Objects"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.3, 0.3, 0.3, 0.1
        elif scene_num in range(21, 26):
            self.scene_type = "Easy Single Physics Concepts With Focus On Finding Hidden Objects"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.35, 0.3, 0.25, 0.1
        elif scene_num in range(26, 41):
            self.scene_type = "Hard Single Physics Concepts"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.45, 0.25, 0.2, 0.1
        elif scene_num in range(41, 46):
            self.scene_type = "Hard Single Physics Concepts With Focus On Creating Objects"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.4, 0.25, 0.25, 0.1
        elif scene_num in range(46, 51):
            self.scene_type = "Hard Single Physics Concepts With Focus On Finding Hidden Objects"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.45, 0.3, 0.15, 0.1
        elif scene_num in range(51, 66):
            self.scene_type = "Easy Multi Physics Concepts"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.35, 0.3, 0.25, 0.1
        elif scene_num in range(66, 71):
            self.scene_type = "Easy Multi Physics Concepts With Focus On Creating Objects"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.4, 0.25, 0.25, 0.1
        elif scene_num in range(71, 76):
            self.scene_type = "Easy Multi Physics Concepts With Focus On Finding Hidden Objects"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.45, 0.3, 0.15, 0.1
        elif scene_num in range(76, 91):
            self.scene_type = "Hard Multi Physics Concepts"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.5, 0.2, 0.15, 0.15
        elif scene_num in range(91, 96):
            self.scene_type = "Hard Multi Physics Concepts With Focus On Creating Objects"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.45, 0.2, 0.2, 0.15
        elif scene_num in range(96, 101):
            self.scene_type = "Hard Multi Physics Concepts With Focus On Finding Hidden Objects"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.5, 0.25, 0.1, 0.15
        elif scene_num in range(101, 126):
            self.scene_type = "Creating/Deleting Objects"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.2, 0.3, 0.4, 0.1
        elif scene_num in range(126, 151):
            self.scene_type = "Finding Hidden Objects"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.4, 0.35, 0.15, 0.1
        elif scene_num in range(151, 159):
            self.scene_type = "Toy Scene: Checking Simulator's and Overall Pipeline Functionality"
            reasoning_score, groundedness_score, action_validity_score, generalization_score = 0.25, 0.25, 0.25, 0.25
        else:
            self.scene_type = "Unknown"
            reasoning_score = groundedness_score = action_validity_score = generalization_score = 0.0
        
        if self.results is None:
            raise ValueError("Experiment results not provided; pass results to Data to avoid re-running.")
        results = self.results
        num_tool_calls = results['num_tool_calls']
        tool_usage = results['tool_usage']

        # Compute all auto-scores
        scores = self.compute_auto_scores()

        # Calculate final weighted score using scene-type coefficients
        correctness_weight = 1.0  # Always most important
        final_score_raw = (
            scores['correctness'] * correctness_weight +
            scores['reasoning'] * reasoning_score +
            scores['groundedness'] * groundedness_score +
            scores['action_validity'] * action_validity_score +
            scores['generalization'] * generalization_score
        )

        # Normalize to 0-100 scale
        total_weight = correctness_weight + reasoning_score + groundedness_score + action_validity_score + generalization_score
        final_score_normalized = (final_score_raw / total_weight) * 100

        summary = {
            "Agent": self.experiment.name_of_agent,
            "Scene ID": self.scene_id,
            "Task": self.scene.scene_task,
            "Description": self.scene.scene_desc,
            "# Interactions": num_tool_calls,
            "Interaction Types": tool_usage,
            "Scene Type": self.scene_type,
            "Problem Type": self.scene.problem_type,
            "Scene Variation": self.scene.scene_variation if self.scene.scene_variation else None,
            "Prompt Method": self.scene.prompt_method,
            "Iterations Given": self.experiment.max_iterations,
            "Python Eval Tool Enabled": self.experiment.enable_python_tool,
            "Time for Experimentation (s)": self.experiment.elapsed_seconds,
            "Correctness (Outcome Success Score)": scores['correctness'],

            # Component scores with coefficients
            f"Generalization Score (weight={generalization_score})": round(scores['generalization'], 4),
            f"Reasoning Score (weight={reasoning_score})": round(scores['reasoning'], 4),
            f"Groundedness Score (weight={groundedness_score})": round(scores['groundedness'], 4),
            f"Action Validity Score (weight={action_validity_score})": round(scores['action_validity'], 4),

            # Final weighted score
            "Final Score (0-100)": round(final_score_normalized, 2),

            # Additional research metrics
            "Efficiency Score": round(scores['efficiency'], 4),
            "Tool Diversity Ratio": round(scores['tool_diversity_ratio'], 4),
            "Query-to-Action Ratio": round(scores['query_tool_ratio'], 4),
            "Tool Success Rate": round(scores['success_rate'], 4),
            "Successful Tool Calls": results.get('successful_calls', num_tool_calls),
            "Failed Tool Calls": results.get('failed_calls', 0),

            # Optional comments field
            "Comments": ""
        }

        # Append to shared log file
        return self.append_summary_to_log(summary)
    
    def whole_scene_summary(self):
        """
        Collects data from multiple variations of a scene and writes an overall summary to a .txt file.

        This method iterates over all variations of a given scene, loads the summary JSON files, extracts the necessary 
        data (interactions, times, final scores), computes averages, and writes the summary to a text file in the correct 
        directory structure.

        Returns:
            None
        """
        # 1) Initialize .txt file in the correct directory
        txt_dir = os.path.join(self.base_dir, f"{self.agent_type}", f"{self.scene_number}")
        os.makedirs(txt_dir, exist_ok=True)
        txt_path = os.path.join(txt_dir, f"whole_scene_summary_{self.agent_type}_scene{self.scene_number}.txt")

        # 2) Prepare to collect values from JSONs
        interactions = []
        times = []
        final_scores = []

        # Determine the number of variations
        scene_number_int = int(self.scene_number)
        if 1 <= scene_number_int <= 50:
            num_variations = 6
        elif 51 <= scene_number_int <= 100:
            num_variations = 4
        elif 101 <= scene_number_int <= 150:
            num_variations = 3
        else:
            num_variations = 0

        # For each variation, read the JSON and collect values
        for i in range(1, num_variations + 1):
            scene_id = f"{self.scene_number}.{i}"
            json_name = f"summary_and_error_analysis_of_{self.agent_type}_for_{scene_id}.json"
            json_path = os.path.join(self.base_dir, f"{self.agent_type}", f"{self.scene_number}", json_name)
            if not os.path.exists(json_path):
                continue
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # If the JSON is a list, take the first element
                if isinstance(data, list):
                    data = data[0].get("summary", data[0]) if data else {}
                # Extract values
                interactions.append(data.get("# Interactions", 0))
                times.append(data.get("Time for Experimentation (s)", 0.0))
                # Try both "Final Score" and possible variants
                final_score = data.get("Final Score", 0.0)
                if isinstance(final_score, str):
                    try:
                        final_score = float(final_score)
                    except Exception:
                        final_score = 0.0
                final_scores.append(final_score)

        # 3) Compute averages
        avg_interactions = sum(interactions) / len(interactions) if interactions else 0
        avg_time = sum(times) / len(times) if times else 0
        avg_final_score = sum(final_scores) / len(final_scores) if final_scores else 0

        # Write results to the .txt file
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("Scene Task: " + self.scene.scene_task + "\n")
            f.write(f"Average # of Interactions: {avg_interactions:.2f}\n")
            f.write(f"Average Time for Experimentation (s): {avg_time:.2f}\n")
            f.write(f"Average Final Score: {avg_final_score:.2f}\n")
