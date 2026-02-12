import json
import os
import random
import numpy as np
from Simulator import Simulator
import xml.etree.ElementTree as ET
import re
from typing import Dict, Any

class Scene:
    """
    A class representing a scene in the physics simulation, providing methods for scene configuration and interaction.

    Attributes:
        scene_id (str): The identifier for the scene.
        simulator (Simulator): The Simulator object associated with the scene.
        enable_python_tool (bool): Flag to enable Python tool for computation.
        scene_number (int): The numeric identifier for the scene.
        scene_data (dict): The scene's data loaded from the JSON file.
        object_permissions (dict): Permissions for the objects within the scene.
        scene_desc (str): A description of the scene.
        scene_task (str): The task associated with the scene.
        problem_type (str): The type of problem associated with the scene.
        objects (dict): A dictionary of objects in the scene.
        scene_variation (str): The variation of the scene.
        xml_data (Element): The XML data for the scene.

    Methods:
        set_prompt_method(method: str):
            Sets the method used for prompting in the scene.

        get_all_tagged_attributes(body):
            Retrieves all tagged attributes (e.g., geom, joint, site) for a specific body in the scene.

        generate_prompt() -> str:
            Generates and returns a prompt for solving the scene's task based on available tools and object information.

        get_correct_answer() -> str:
            Retrieves the correct answer for the scene.

        append_summary_to_log(summary):
            Appends a summary of the experiment to the log file in JSON format.

        summarize_scenes():
            Creates a summary for the experiment based on the scene type and scores, and appends it to the log.

        whole_scene_summary():
            Collects data from multiple variations of a scene and writes an overall summary to a .txt file.
    """
    def __init__(self, scene_id: str, enable_python_tool: bool, simulator: Simulator):
        """
        Initializes the Scene object. Loads the scene's metadata, objects, and XML data.

        Parameters:
            scene_id (str): The unique identifier for the scene.
            enable_python_tool (bool): Flag to enable the Python tool for computation.
            simulator (Simulator): An instance of the Simulator to interact with the scene.
        """
        self.scene_id = scene_id
        self.simulator = simulator
        self.enable_python_tool = enable_python_tool
        self.prompt_method = "one_shot_with_cot"  # Default method
        self.scene_number = int(self.scene_id)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.join(script_dir, "Scenes")
        # Use consistent structure for all scenes: Scenes/Scene{number}/scene{number}.json
        self.scene_data = os.path.join(base_dir, f"Scene{self.scene_number}", f"scene{self.scene_number}.json")
        self.scene_xml = os.path.join(base_dir, f"Scene{self.scene_number}", f"scene{self.scene_number}.xml")

        with open(self.scene_data, 'r') as file:
            scene_json_data = json.load(file)
        cleaned_permissions = {}
        for key, val in scene_json_data.get("object_permissions", {}).items():
            obj_key = key.replace("object_", "").replace("_permissions", "")
            cleaned_permissions[obj_key] = val
        self.object_permissions = cleaned_permissions
        self.scene_data = scene_json_data
        self.data = scene_json_data["metadata"]
        self.scene_desc = self.data.get("scene_name", "")
        self.scene_task = self.data.get("task", "")
        self.problem_type = self.data.get("problem_type", "")
        self.objects = scene_json_data["objects"]
        self.scene_variation = scene_json_data.get("variation", None)

        self.xml_data = ET.parse(self.scene_xml).getroot()

    def set_prompt_method(self, method):
        """
        Sets the method used for prompting.

        Parameters:
            method (str): The prompting method to be used.
        """
        self.prompt_method = method

    def get_all_tagged_attributes(self, body):
        """
        Retrieves all attributes of a given body, including child elements like geom, joint, site, and inertial.

        Parameters:
            body (Element): The body element to extract attributes from.

        Returns:
            dict: A dictionary of the attributes associated with the body.
        """
        tag_attributes = {}

        # Body-level attributes
        for attr in body.attrib:
            tag_attributes[f"body_{attr}"] = body.attrib[attr]

        # Child tags
        tags_to_check = ["geom", "joint", "site", "inertial"]
        for tag in tags_to_check:
            for elem in body.findall(tag):
                for attr in elem.attrib:
                    tag_attributes[f"{tag}_{attr}"] = elem.attrib[attr]

        return tag_attributes


    def generate_prompt(self):
        """
        Generates a prompt to be used by the simulator with available tools, object details, and scene metadata.

        Returns:
            str: The generated prompt.
        """
        objects_str = ""

        for obj_id, obj_data in self.objects.items():
            obj_name = obj_data.get("name", "unknown")
            obj_id_num = obj_data.get("object_id", None)
            obj_id_str = f"object_{obj_id_num}"
            permissions = self.object_permissions.get(obj_id_num, {})

            # 🚫 Skip object if it's hidden
            if permissions.get("hidden", False):
                continue

            # Find the corresponding <body> in XML
            body = None
            for b in self.xml_data.findall(".//body"):
                if b.get("name") == obj_id_str:
                    body = b
                    break

            if not body:
                continue

            all_attrs = self.get_all_tagged_attributes(body)
            attr_parts = []

            for full_attr_name, value in all_attrs.items():
                if full_attr_name.endswith("_name"):
                    continue

                # ✅ Now using full_attr_name to check fine-grained permissions
                if permissions.get(full_attr_name, False):
                    nums = re.findall(r"[-+]?\d*\.\d+|\d+", value)
                    display_val = [float(n) for n in nums] if nums else value
                    attr_parts.append(f"{full_attr_name}: {display_val}")


            if attr_parts:
                objects_str += f"Object id: {obj_id_str}, Object name: {obj_name}, " + ", ".join(attr_parts)
            else:
                objects_str += f"Object id: {obj_id_str}, Object name: {obj_name}"

            objects_str += "\n"
            
        objects_str += "Mass: The mass of the object is not given directly, but can be calculated using the object's size/radius and density if available.\n"
        objects_str += "\nQuaternion: A quaternion is used to represent rotation in 3D space. The four numbers represent rotations along the X, Y, Z axes and a scalar component.\n"
        objects_str += "\nIf an attribute has 'n/a' right beside it, that means you CANNOT access that attributes value, so keep that in mind when running through the experiment.\n"
        objects_str += "\n If there are multiple numbers in the attribute, note that they are in the form of an array to specify the different parameters of the attribute.\n"
        # Define the tool mapping string (as a literal string)
        tools = [
            {"name": "step", "description": "keeps on moving the simulator forward in time", "arguments": {"duration": "float"}, "return type": {"results" : None}},
            {"name": "apply_force", "description": "applies a force vector to an object", "arguments": {"object_id": "str", "force_vector": "list[float]"}, "return type": {"status": "str", "object_id": "int", "force": "list[float]"}},
            {"name": "get_velocity", "description": "retrieves the velocity vector of an object", "arguments": {"object_id": "str"}, "return type": {"velocity": "array"}},
            {"name": "detect_collision", "description": "checks if two objects have collided", "arguments": {"obj1_id": "str", "obj2_id": "str"}, "return type": {"collision_detected": "bool"}},
            {"name": "get_parameters", "description": "fetches physical parameters like mass, bounding box, and type", "arguments": {"object_id": "str // REMEMBER THAT YOU WRITE IT AS AN F-STRING THAT IS object_(object id), where object id is an integer"}, "return type": {"mass": "float", "bounding_box": "list[float]", "type": "int"}},
            {"name": "move_object", "description": "sets an object's position to a new coordinate", "arguments": {"object_id": "str", "x": "float", "y": "float", "z": "float"}, "return type": {"position": "tuple[float, float, float]"}},
            {"name": "get_position", "description": "gets the current position and time of an object", "arguments": {"object_id": "str"}, "return type": {"position": "tuple[float, float, float]", "time": "float"}},
            {"name": "get_displacement", "description": "gets how far an object has moved from its initial position", "arguments": {"object_id": "str"}, "return type": {"displacement": "float"}},
            {"name": "compute_force", "description": "calculates the force on an object using F = ma", "arguments": {"object_id": "str", "mass": "float"}, "return type": {"x": "float", "y": "float", "z": "float"}},
            {"name": "get_acceleration", "description": "returns the current acceleration vector of an object", "arguments": {"object_id": "str"}, "return type": {"x": "float", "y": "float", "z": "float"}},
            {"name": "set_velocity", "description": "sets the velocity vector of an object", "arguments": {"object_id": "str", "velocity_vector": "list[float]"}, "return type": {"status": "str", "object_id": "int", "velocity": "list[float]"}},
            {"name": "apply_torque", "description": "applies a torque to an object", "arguments": {"object_id": "str", "torque_vector": "list[float]"}, "return type": {"status": "str", "object_id": "int", "torque": "list[float]"}},
            {"name": "get_torque", "description": "returns the torque acting on an object", "arguments": {"object_id": "str"}, "return type": {"torque": {"x": "float", "y": "float", "z": "float"}}},
            {"name": "get_center_of_mass", "description": "gets the center of mass of the entire scene", "arguments": {}, "return type": {"center_of_mass": {"x": "float", "y": "float", "z": "float"}}},
            {"name": "get_potential_energy", "description": "calculates the potential energy of an object using PE = m * g * h", "arguments": {"object_id": "str", "mass": "float", "gravity": "float = 9.81"}, "return type": {"potential_energy": "float"}},
            {"name": "get_kinetic_energy", "description": "calculates the kinetic energy of an object using KE = 0.5 * m * v^2", "arguments": {"object_id": "str", "mass": "float"}, "return type": {"kinetic_energy": "float"}},
            {"name": "get_rotational_energy", "description": "calculates the rotational energy of an object", "arguments": {"object_id": "str", "mass": "float"}, "return type": {"rotational_energy": "float"}},
            {"name": "get_momentum", "description": "calculates the linear momentum of an object using p = m * v", "arguments": {"object_id": "str", "mass": "float"}, "return type": {"momentum": {"x": "float", "y": "float", "z": "float"}}},
            {"name": "get_angular_momentum", "description": "returns the angular momentum of an object", "arguments": {"object_id": "str", "mass": "float"}, "return type": {"angular_momentum": {"x": "float", "y": "float", "z": "float"}}},
            {"name": "change_position", "description": "translates an object by some delta in the local or world frame", "arguments": {"object_id": "str", "dx": "float", "dy": "float", "dz": "float", "in_world_frame": "bool"}, "return type": {"new_position": {"x": "float", "y": "float", "z": "float"}}},
            {"name": "quat_to_rot_matrix", "description": "converts a quaternion into a 3x3 rotation matrix", "arguments": {"q": "list[float]"}, "return type": {"rotation_matrix": "array[3][3]"}},
            {"name": "answer", "description": "submits an answer back to the system for checking or logging", "arguments": {"answer": "str or float"}, "return type": {"acknowledged": "bool"}},
            {"name": "create_objects", "description": "creates a new object in the simulation and adds it to the scene", "arguments": {"name": "str", "pos": "list", "density": "float", "rgba": "list"}, "return type": {"status": "str", "name": "str", "position": "list", "density": "float", "rgba": "list"}},
            {"name": "delete_objects", "description": "deletes an object from the simulation by its ID", "arguments": {"object_id": "str"}, "return type": {"status": "str", "object_id": "str"}},
            {"name": "find_objects", "description": "finds and updates all objects in the scene by modifying their rgba properties", "arguments": {}, "return type": {"status": "str"}},
            {"name": "attach_objects", "description": "attaches two objects together in the simulation by creating a joint between them", "arguments": {"object1_id": "str", "object2_id": "str"}, "return type": {"status": "str"}}
        ]

        tools_str = json.dumps(tools, indent=2)
        
        # Construct the final prompt using all information
        self.prompt = (
            f"You are trying to analyze a physics problem given by the scene_id. The goal is to interact with the environment to determine a correct numeric answer.\n"
            f"\nScene Description: {self.scene_desc}."
            f"\nTask: {self.scene_task}."
            f"\nAvailable Objects and Parameters:\n{objects_str}"
            f"\n\nYou may use the following tools along with their description to interact with the scene. These functions accept parameters given below, and return data or perform simulation updates:\n{tools_str}"
            f"\n\nEvery time you call a tool, you will receive a dictionary containing the outputs. For example, if you call `get_velocity` on `object_1`, the return might be:"
            f'\n{{"vx": 0.0, "vy": -3.2, "vz": 0.0}}'
            f"\n\nYou only have **one chance** to answer the question. When you're confident, submit your final answer using:"
            f'\n`{{"tool": "answer", "parameters": {{"answer": "<your_answer>"}}}}`\n'
        )
        # Add prompt method specific instructions
        if self.prompt_method == "zero_shot":
            self.prompt += ('\n')
        elif self.prompt_method == "one_shot":
            self.prompt += (
                f"\n<THIS IS AN EXAMPLE PROBLEM OF THE INPUTS(ASSISTANT) AND OUTPUTS(ENVIRONMENT) THAT SHOULD TAKE PLACE>"
                f"\nProblem: You are given a ball and a ground surface for reference. Drop the ball from a height of 10 units and figure out the velocity of the object after 0.5 seconds."
                f"\n<assistant>\n```json\n"
                f'[{{"tool": "move_object", "parameters": {{"object_id": "object_1", "x": 0, "y": 10, "z": 0}}}},'
                f'{{"tool": "step", "parameters": {{"duration": 0.5}}}},'
                f'{{"tool": "get_velocity", "parameters": {{"object_id": "object_1"}}}},'
                f'{{"tool": "answer", "parameters": {{"answer": "-4.9"}}}}]\n```\n<END EXAMPLE>\n'
            )
        elif self.prompt_method == "one_shot_cot":
            self.prompt += (
                f"\n<THIS IS AN EXAMPLE PROBLEM OF THE INPUTS(ASSISTANT) AND OUTPUTS(ENVIRONMENT) THAT SHOULD TAKE PLACE>"
                f"\nProblem: You are given a ball and a ground surface for reference. Drop the ball from a height of 10 units and figure out the velocity of the object after 0.5 seconds."
                f"\n<assistant>\nI see that I have to move the ball up 10 units so I will do that.\n```json\n"
                f'[{{"tool": "move_object", "parameters": {{"object_id": "object_1", "x": 0, "y": 10, "z": 0}}}}]\n```\n'
                f"\n<environment>\nResults: [{{\"tool\": \"move_object\", \"parameters\": {{...}}, \"result\": {{\"position\": [0, 10, 0]}}, \"sim_time\": 0}}] What will you do next\n"
                f"\n<assistant>\nNow I will simulate by using the step function to go 0.5 seconds forward.\n```json\n"
                f'[{{"tool": "step", "parameters": {{"duration": 0.5}}}}]\n```\n'
                f"\n<environment>\nResults: [{{\"tool\": \"step\", \"parameters\": {{...}}, \"result\": null, \"sim_time\": 0.5}}] What will you do next\n"
                f"\n<assistant>\nNow I will use the get velocity function to figure out what I should output as my answer.\n```json\n"
                f'[{{"tool": "get_velocity", "parameters": {{"object_id": "object_1"}}}}]\n```\n'
                f"\n<environment>\nResults: [{{\"tool\": \"get_velocity\", \"parameters\": {{...}}, \"result\": {{\"velocity\": [0, -4.9, 0]}}, \"sim_time\": 0.5}}] What will you do next\n"
                f"\n<assistant>\nNow I will call back the answer.\n```json\n"
                f'[{{"tool": "answer", "parameters": {{"answer": "-4.9"}}}}]\n```\n<END EXAMPLE>\n'
            )
        elif self.prompt_method == "few_shot":
            self.prompt += (
                f"\n<THIS IS EXAMPLE PROBLEM #1 OF THE INPUTS(ASSISTANT) AND OUTPUTS(ENVIRONMENT) THAT SHOULD TAKE PLACE>"
                f"\nProblem: You are given a ball and a ground surface for reference. Drop the ball from a height of 10 units and figure out the velocity of the object after 0.5 seconds."
                f"\n<assistant>\n```json\n"
                f'[{{"tool": "move_object", "parameters": {{"object_id": "object_1", "x": 0, "y": 10, "z": 0}}}},'
                f'{{"tool": "step", "parameters": {{"duration": 0.5}}}},'
                f'{{"tool": "get_velocity", "parameters": {{"object_id": "object_1"}}}},'
                f'{{"tool": "answer", "parameters": {{"answer": "-4.9"}}}}]\n```\n<END EXAMPLE>\n'
                f"\n\n<THIS IS EXAMPLE PROBLEM #2 OF THE INPUTS(ASSISTANT) AND OUTPUTS(ENVIRONMENT) THAT SHOULD TAKE PLACE>"
                f"\nProblem: There is a box on a table. Push the box along the x-axis with a force of 5 units for 1 second. What is the final position of the box?"
                f"\n<assistant>\n```json\n"
                f'[{{"tool": "apply_force", "parameters": {{"object_id": "object_1", "force": [5, 0, 0], "duration": 1.0}}}},'
                f'{{"tool": "get_position", "parameters": {{"object_id": "object_1"}}}},'
                f'{{"tool": "answer", "parameters": {{"answer": "[1.0, 0, 0]"}}}}]\n```\n<END EXAMPLE>\n'
                f"\n\n<THIS IS EXAMPLE PROBLEM #3 OF THE INPUTS(ASSISTANT) AND OUTPUTS(ENVIRONMENT) THAT SHOULD TAKE PLACE>"
                f"\nProblem: A ball is on a ramp inclined along the x-axis. Let the ball roll down for 2 seconds. What is its velocity?"
                f"\n<assistant>\n```json\n"
                f'[{{"tool": "step", "parameters": {{"duration": 2.0}}}},'
                f'{{"tool": "get_velocity", "parameters": {{"object_id": "object_1"}}}},'
                f'{{"tool": "answer", "parameters": {{"answer": "2.8"}}}}]\n```\n<END EXAMPLE>\n'
            )
        elif self.prompt_method == "few_shot_cot":
            self.prompt += (
                f"\n<THIS IS EXAMPLE PROBLEM #1 OF THE INPUTS(ASSISTANT) AND OUTPUTS(ENVIRONMENT) THAT SHOULD TAKE PLACE>"
                f"\nProblem: You are given a ball and a ground surface for reference. Drop the ball from a height of 10 units and figure out the velocity of the object after 0.5 seconds."
                f"\n<assistant>\nI see that I have to move the ball up 10 units so I will do that.\n```json\n"
                f'[{{"tool": "move_object", "parameters": {{"object_id": "object_1", "x": 0, "y": 10, "z": 0}}}}]\n```\n'
                f"\n<environment>\nResults: [{{\"tool\": \"move_object\", \"parameters\": {{...}}, \"result\": {{\"position\": [0, 10, 0]}}, \"sim_time\": 0}}] What will you do next\n"
                f"\n<assistant>\nNow I will simulate by using the step function to go 0.5 seconds forward.\n```json\n"
                f'[{{"tool": "step", "parameters": {{"duration": 0.5}}}}]\n```\n'
                f"\n<environment>\nResults: [{{\"tool\": \"step\", \"parameters\": {{...}}, \"result\": null, \"sim_time\": 0.5}}] What will you do next\n"
                f"\n<assistant>\nNow I will use the get velocity function to figure out what I should output as my answer.\n```json\n"
                f'[{{"tool": "get_velocity", "parameters": {{"object_id": "object_1"}}}}]\n```\n'
                f"\n<environment>\nResults: [{{\"tool\": \"get_velocity\", \"parameters\": {{...}}, \"result\": {{\"velocity\": [0, -4.9, 0]}}, \"sim_time\": 0.5}}] What will you do next\n"
                f"\n<assistant>\nNow I will call back the answer.\n```json\n"
                f'[{{"tool": "answer", "parameters": {{"answer": "-4.9"}}}}]\n```\n<END EXAMPLE>\n'
                f"\n\n<THIS IS EXAMPLE PROBLEM #2 OF THE INPUTS(ASSISTANT) AND OUTPUTS(ENVIRONMENT) THAT SHOULD TAKE PLACE>"
                f"\nProblem: There is a box on a table. Push the box along the x-axis with a force of 5 units for 1 second. What is the final position of the box?"
                f"\n<assistant>\nFirst, I will apply a force to the box.\n```json\n"
                f'[{{"tool": "apply_force", "parameters": {{"object_id": "object_1", "force": [5, 0, 0], "duration": 1.0}}}}]\n```\n'
                f"\n<environment>\nResults: [{{\"tool\": \"apply_force\", \"parameters\": {{...}}, \"result\": null, \"sim_time\": 1.0}}] What will you do next\n"
                f"\n<assistant>\nNow I will check the position of the box.\n```json\n"
                f'[{{"tool": "get_position", "parameters": {{"object_id": "object_1"}}}}]\n```\n'
                f"\n<environment>\nResults: [{{\"tool\": \"get_position\", \"parameters\": {{...}}, \"result\": {{\"position\": [1.0, 0, 0]}}, \"sim_time\": 1.0}}] What will you do next\n"
                f"\n<assistant>\nNow I will answer the question.\n```json\n"
                f'[{{"tool": "answer", "parameters": {{"answer": "[1.0, 0, 0]"}}}}]\n```\n<END EXAMPLE>\n'
                f"\n\n<THIS IS EXAMPLE PROBLEM #3 OF THE INPUTS(ASSISTANT) AND OUTPUTS(ENVIRONMENT) THAT SHOULD TAKE PLACE>"
                f"\nProblem: A ball is on a ramp inclined along the x-axis. Let the ball roll down for 2 seconds. What is its velocity?"
                f"\n<assistant>\nFirst, I will simulate the ball rolling by stepping 2 seconds ahead.\n```json\n"
                f'[{{"tool": "step", "parameters": {{"duration": 2.0}}}}]\n```\n'
                f"\n<environment>\nResults: [{{\"tool\": \"step\", \"parameters\": {{...}}, \"result\": null, \"sim_time\": 2.0}}] What will you do next\n"
                f"\n<assistant>\nNow I will get the velocity of the ball.\n```json\n"
                f'[{{"tool": "get_velocity", "parameters": {{"object_id": "object_1"}}}}]\n```\n'
                f"\n<environment>\nResults: [{{\"tool\": \"get_velocity\", \"parameters\": {{...}}, \"result\": {{\"velocity\": [2.8, 0, 0]}}, \"sim_time\": 2.0}}] What will you do next\n"
                f"\n<assistant>\nNow I will provide the final answer.\n```json\n"
                f'[{{"tool": "answer", "parameters": {{"answer": "2.8"}}}}]\n```\n<END EXAMPLE>\n'
            )

        if self.enable_python_tool:
            self.prompt += (
                f"\n\nYou have access to a Python tool that can be used to perform calculations or data manipulations."
                f"\nYou can use this tool to help you with computations that may be necessary for solving the problem."
                f"\nRemember to provide valid Python code in the format: `{{\"tool\": \"python\", \"parameters\": {{\"code\": \"<your_python_code>\"}}}}`"
            )
        # Append additional instructions based on problem type
        if self.problem_type == "comparison":
            self.prompt += (
                f"\n\nSince this problem is a comparison problem, your answer should be the object id number of the object that satisfies the task."
                f"\nIf all objects being compared to each other satisfy the task, output 0. "
                f"\nIf some satisfy the task, while other objects do not, output the object id's of the objects that satisfy the task, separated by commas."
            )
        elif self.problem_type == "computation" or "calculation" in self.problem_type:
            self.prompt += (
                f"\n\nSince the problem is a computation problem, your answer should be the calculated number that satisfies the task"
                f"\nrounded to the nearest thousandths place if applicable."
            )
        elif self.problem_type == "boolean":
            self.prompt += (
                f"\n\nSince the problem is a true or false question, output 0 for true, and 1 for false."
            )

        self.prompt += (
            f'\n\n***FINAL GUIDELINES***\n'
            f"\nYou must call `step` to simulate time progression.\n"
            f'\n1 simulation step is 0.005 real life seconds, and ALL problems are based off of real life time if seconds are mentioned in the task.\n'
            f'\nDo not make any assumptions about the positions or states of objects, if you are unsure you can use tools get this information.\n'
            f'\nThe z plane is the vertical plane, and the x and y planes are the horizontal planes.\n'
            f'\nWhen answering, use the world coordinate frame with signed values: +x, +y, +z are the positive directions; motion or quantities in the opposite directions must be negative. Report signed vectors and scalars accordingly.\n'
            f'\nUnderstand that you can use the tools to gather necessary information pertainig to all objects in the scene, not just the one you are trying to analyze.\n'
            f'\nIf your json format is incorrect - the environment will tell you and the simulator will remain in the same state. If one of your tool calls has incorrect formatting, the previous tool calls will successfully execute but the incorrect tool and subsequent tools will not execute. You will see how your tool call was incorrect and get a chance to retry in the next iteration.\n'
            f'\nRemember that YOU MUST PROVIDE YOUR REASONING FOR EVERY ACTION you take, and then make sure to add a valid JSON format of an array of tool calls.\n'
            f'\n***When you are trying to call functions, use a string that goes as object_{{object_id}} for the object id, and use the name of the function as the tool name.***\n'
            f'\n For example, if you were to try and call the function get_velocity on object_1, you would write it as:\n'
            f'```json\n'
            f'[{{"tool": "get_velocity", "parameters": {{"object_id": "object_1"}}}}]\n```\n'
            f'\n RATHER THAN WRITING IT AS:\n'
            f'```json\n'
            f'[{{"tool": "get_velocity", "parameters": {{"object_id": 1}}}}]\n```\n'
            f'\nRemember that when giving multiple tool calls, you must give them in ONE SINGLE GO, as shown below.\n'
            f'```json\n'
            f'[{{"tool": "get_velocity", "parameters": {{"object_id": "object_1"}}}},'
            f'{{"tool": "get_velocity", "parameters": {{"object_id": "object_2"}}}}]\n```\n'
            f'and so on and so forth.\n'
            f'\n As you input multiple tool calls, the simulator will run each of them sequentially, and then return the results of each tool call in the order they were called.\n'
            f'\n DO NOT GIVE MORE THAN ONE SET OF TOOL CALLS AT A TIME, OR THE SIMULATOR WILL NOT WORK, AND END UP GIVING YOU AN ERROR FOR JSON SYNTAX!!!\n'
        )
        return self.prompt

    def get_correct_answer(self):
        """
        Retrieves the correct answer for the scene.

        Returns:
            str: The correct answer for the scene.
        """
        if not self.scene_data:
            return ""
        if isinstance(self.scene_data, str):
            try:
                data = json.loads(self.scene_data)
            except json.JSONDecodeError:
                return ""
        else:
            data = self.scene_data
        return data.get("answer", "")
