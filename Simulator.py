from __future__ import annotations
import mujoco
import mujoco.viewer
import numpy as np
import time
import os
import xml.etree.ElementTree as ET
import logging
import pywin 
import win32gui
import win32con
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | [%(levelname)s] | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

class Simulator:
    """
    A class responsible for interacting with the MuJoCo physics engine to simulate and manipulate objects in a scene.

    Attributes:
        scene_id (str): The identifier for the scene to be simulated.
        model_path (str): The file path to the MuJoCo model for the scene.
        model (MjModel): The MuJoCo model representing the scene.
        data (MjData): The MuJoCo data structure that holds the simulation state.
        viewer (Viewer): The viewer for rendering the simulation.
        start_pos (np.ndarray): The initial position of the objects in the scene.
        time (float): The current simulation time.
        prev_velocities (dict): A dictionary to store previous velocities of objects for acceleration calculations.

    Methods:
        get_model_path(scene_id: str) -> str:
            Returns the model path based on the provided scene ID.
        
        load_scene(scene_id: str):
            Loads the scene and initializes the simulation state.
        
        render():
            Renders the current simulation frame.
        
        get_body_id(object_id: str) -> int:
            Retrieves the body ID associated with the provided object ID.
        
        get_geom_id(object_id: str) -> int:
            Retrieves the geometry ID associated with the provided object ID.
        
        get_parameters(object_id: str) -> dict:
            Retrieves physical parameters like mass, bounding box, and type for a specific object.
        
        step(duration: float = 1.0):
            Advances the simulation by the specified duration.
        
        reset_sim():
            Resets the simulation to its initial state.
        
        minimize_viewer_window():
            Minimizes the MuJoCo viewer window for background operation.
        
        get_position(object_id: str) -> dict:
            Retrieves the position and time of a specific object in the simulation.
        
        move_object(object_id: str, x: float, y: float, z: float) -> dict:
            Moves an object to a new position in the simulation.
        
        apply_force(object_id: str, force_vector: list) -> dict:
            Applies a force vector to an object in the simulation.
        
        apply_torque(object_id: str, torque_vector: list) -> dict:
            Applies a torque to an object in the simulation.
        
        get_velocity(object_id: str) -> dict:
            Retrieves the velocity of an object in the simulation.
        
        get_acceleration(object_id: str) -> dict:
            Calculates and returns the current acceleration of an object.
        
        compute_force(object_id: str, mass: float) -> dict:
            Computes the force on an object using the formula F = ma.
        
        get_torque(object_id: str) -> dict:
            Retrieves the torque acting on an object.
        
        get_center_of_mass() -> dict:
            Retrieves the center of mass for the entire scene.
        
        get_angular_momentum(object_id: str, mass: float) -> dict:
            Retrieves the angular momentum of an object in the simulation.
        
        detect_collision(obj1_id: str, obj2_id: str) -> dict:
            Detects and handles a collision between two objects in the simulation.
        
        get_kinetic_energy(object_id: str, mass: float) -> dict:
            Calculates the kinetic energy of an object.
        
        get_potential_energy(object_id: str, mass: float, gravity: float = 9.81) -> dict:
            Calculates the potential energy of an object.
        
        get_rotational_energy(object_id: str, mass: float) -> dict:
            Calculates the rotational energy of an object.
        
        get_momentum(object_id: str, mass: float) -> dict:
            Calculates the linear momentum of an object.
    """
    def __init__(self, scene_id: str, agent_name: str = "default_agent"):
        """
        Initializes the Simulator object with the given scene and agent.

        Parameters:
            scene_id (str): The identifier for the scene to be loaded.
            experiment (Experiment): An instance of the Experiment class.
        """
        self.scene_id = scene_id
        self.model_path = self.get_model_path(scene_id)
        self.agent = agent_name

        try:
            # Load model with error handling
            self.model = mujoco.MjModel.from_xml_path(self.model_path) # type: ignore
            self.data = mujoco.MjData(self.model) # type: ignore
            
            # Initialize viewer
            self.viewer = mujoco.viewer.launch_passive(self.model, self.data)
            self.start_pos = np.copy(self.data.qpos)
            self.time = 0
            self.prev_velocities = {}  # Store previous velocities for acceleration calculations
            
            # Ensuring the initial velocity is zero
            self.data.qvel[:] = 0.0  # Setting all initial velocities to zero
            
        except Exception as e:
            logging.error(f"MuJoCo initialization failed: {e}")
            raise
    
    #These are functions that help set up the scene for the LLM to interact with

    def get_model_path(self, scene_id: str) -> str:
        """
        Constructs and returns the model path based on the provided scene ID.

        Parameters:
            scene_id (str): The unique identifier for the scene.

        Returns:
            str: The path to the model file for the given scene.
        """
        try:
            # Get the directory of the current script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            scenes_dir = os.path.join(script_dir, "Scenes")
            # Extract scene number and construct XML path
            scene_float = scene_id.split("_")[-1]
            scene_number = int(scene_float.split(".")[0])
            if scene_number < 150:
                xml_path = os.path.join(scenes_dir, f'Scene{scene_number}', f"scene{scene_float}", f"scene{scene_float}.xml")
            else:
                xml_path = os.path.join(scenes_dir, f'Scene{scene_number}', f"scene{scene_number}.xml")

            # Verify if the file exists
            if not os.path.exists(xml_path):
                raise FileNotFoundError(f"Scene XML not found at: {xml_path}")
            
            return xml_path.replace("\\", "/")
        except Exception as e:
            logging.error(f"Path construction failed: {e}")
            raise

    def load_scene(self, scene_id: str):
        """
        Loads the scene and initializes the simulation.

        Parameters:
            scene_id (str): The unique identifier for the scene.
        """
        try:
            if hasattr(self, 'viewer') and self.viewer is not None:
                self.viewer.close()

            scene_id = str(scene_id)  # ensure it's a string
            self.model_path = self.get_model_path(scene_id)
            logging.info(f"Loading model from: {self.model_path}")

            self.model = mujoco.MjModel.from_xml_path(self.model_path) # type: ignore
            self.data = mujoco.MjData(self.model) # type: ignore

            self.viewer = mujoco.viewer.launch_passive(self.model, self.data)
            self.start_pos = np.copy(self.data.qpos)
            self.time = 0

        except Exception as e:
            logging.error(f"Failed to load scene {scene_id}: {e}")

    def render(self):
        """
        Renders the current frame of the simulation.

        Returns:
            None
        """
        self.viewer.sync()
        return self.viewer.capture_frame() # type: ignore
        
    def get_body_id(self, object_id: str) -> int:
        """
        Retrieves the body ID associated with the given object ID.

        Parameters:
            object_id (str): The unique identifier for the object.

        Returns:
            int: The body ID for the object.
        """
        object_id = str(object_id)
        name = object_id
        body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, name) # type: ignore
        if body_id == -1:
            raise ValueError(f"Body with name '{name}' not found in the scene.")
        return body_id
    
    def get_geom_id(self, object_id: str) -> int:
        """
        Retrieves the geometry ID associated with the given object ID.

        Parameters:
            object_id (str): The unique identifier for the object.

        Returns:
            int: The geometry ID for the object.
        """
        try:
            # Assuming that object_id corresponds to a body or a specific geometry.
            body_id = self.get_body_id(object_id)
            geom_id = self.model.body_geomadr[body_id]
            return geom_id
        except Exception as e:
            logging.error(f"Error in get_geom_id for object_id='{object_id}': {str(e)}")
            raise

    def get_parameters(self, object_id: str) -> dict:
        """
        Retrieves the physical parameters (mass, bounding box, type) of the object.

        Parameters:
            object_id (str): The unique identifier for the object.

        Returns:
            dict: A dictionary containing the object's mass, bounding box, and type.
        """
        try:
            body_id = self.get_body_id(object_id)
            if body_id == -1:
                raise ValueError(f"Body with name '{object_id}' not found")
            return {
                "mass": float(self.model.body_mass[body_id]),
                "bounding_box": self.model.body_inertia[body_id].tolist(),
                "type": int(self.model.body_parentid[body_id])
            }
        except Exception as e:
            return {"error": str(e)}

    def step(self, duration: float = 1.0):
        """
        Steps the simulation forward by the specified duration.

        Parameters:
            duration (float): The duration for the simulation step.
        """
        num_steps = int(duration / self.model.opt.timestep)
        remaining_time = duration - (num_steps * self.model.opt.timestep)
        
        for _ in range(num_steps):
            # Perform the simulation step
            mujoco.mj_step(self.model, self.data) # type: ignore
            
            # Ensure the simulation state is updated
            mujoco.mj_forward(self.model, self.data) # type: ignore

            if self.viewer is not None:
                self.viewer.sync()

        if remaining_time > 0:
            # Final step for remaining time if any
            mujoco.mj_step(self.model, self.data) # type: ignore
            
            # Ensure the simulation state is updated
            mujoco.mj_forward(self.model, self.data) # type: ignore
            
            if self.viewer is not None:
                self.viewer.sync()

        self.time += duration
        logging.info(f"Simulation time: {self.time} seconds")

    def reset_sim(self):
        """
        Resets the simulation to its initial state.
        """
        self.data.qpos[:] = self.start_pos
        self.data.qvel[:] = 0
        mujoco.mj_forward(self.model, self.data) # type: ignore
        self.time = 0

    def __del__(self):
        """
        Clean up resources when the Simulator object is destroyed.
        """
        if hasattr(self, 'viewer') and self.viewer is not None:
            self.viewer.close()
    
    def minimize_viewer_window(self):
        """
        Minimizes the viewer window for background operation.

        Returns:
            dict: The status of the viewer window.
        """
        try:
            # Find the window by title (you may need to adjust the title if it differs)
            def enum_windows_callback(hwnd, result):
                title = win32gui.GetWindowText(hwnd)
                if "MuJoCo" in title:
                    result.append(hwnd)
            hwnds = []
            win32gui.EnumWindows(enum_windows_callback, hwnds)
            if hwnds:
                for hwnd in hwnds:
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                return {"status": "viewer_minimized"}
            else:
                return {"error": "MuJoCo viewer window not found"}
        except Exception as e:
            return {"error": f"Failed to minimize viewer window: {str(e)}"}

    #These are the actual functions that the LLM will use to interact with the scene

    def get_position(self, object_id: str) -> dict:
        """
        Retrieves the position of an object in the simulation.

        Parameters:
            object_id (str): The unique identifier for the object.

        Returns:
            dict: A dictionary containing the position of the object.
        """
        try:
            # Ensure object_id is a string
            object_id = str(object_id)
            
            # Get body ID based on the object_id
            body_id = self.get_body_id(object_id)
            
            # Ensure body_id is valid before proceeding
            if body_id < 0 or body_id >= len(self.data.xpos):
                raise IndexError(f"Invalid body_id {body_id}. Unable to fetch position.")
            
            # Get the position of the body (assuming xpos stores 3D position data)
            pos = self.data.xpos[body_id]  # [x, y, z]
            
            # Return the position along with the current simulation time
            return {"position": pos.tolist(), "time": self.data.time}

        except Exception as e:
            # Log error with more context for debugging
            logging.error(f"Error in get_position for object_id='{object_id}': {str(e)}")
            return {"error": str(e)}
        
    def change_position(self, object_id: str, dx: float, dy: float, dz: float, in_world_frame: bool) -> dict:
        """
        Changes the position of an object by the specified amounts.

        Parameters:
            object_id (str): The unique identifier for the object.
            dx (float): The change in the x position.
            dy (float): The change in the y position.
            dz (float): The change in the z position.
            in_world_frame (bool): Whether to apply the change in world coordinates.

        Returns:
            dict: The new position of the object.
        """
        try:
            object_id = str(object_id)  # Ensure object_id is a string
            body_id = self.get_body_id(object_id)  # Get body ID based on object_id
            joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, f"{object_id}_joint") # type: ignore
            if joint_id == -1:
                return {"error": f"No joint named {object_id}_joint"}
            
            joint_qpos_addr = self.model.jnt_qposadr[joint_id]
            if in_world_frame:
                self.data.qpos[joint_qpos_addr:joint_qpos_addr+3] += np.array([dx, dy, dz])
            else:
                self.data.qpos[joint_qpos_addr] += dx
                self.data.qpos[joint_qpos_addr+1] += dy
                self.data.qpos[joint_qpos_addr+2] += dz
            
            mujoco.mj_forward(self.model, self.data) # type: ignore
            return {"new_position": self.data.qpos[joint_qpos_addr:joint_qpos_addr+3].tolist()}
        except Exception as e:
            return {"error": str(e)}
        
    def get_displacement(self, object_id: str) -> dict:
        """
        Calculates the displacement of an object from its initial position.

        Parameters:
            object_id (str): The unique identifier for the object.

        Returns:
            dict: A dictionary containing the displacement of the object.
        """
        try:
            object_id = str(object_id)  # Ensure object_id is a string
            body_id = self.get_body_id(object_id)  # Get body ID based on object_id
            
            # Ensure xpos and start_pos are numpy arrays for element-wise operations
            current_pos = np.array(self.data.xpos[body_id])  # Current position
            if not hasattr(self, 'start_pos') or len(self.start_pos) < 3:
                raise ValueError("Start position (self.start_pos) has not been properly initialized.")
            
            start_pos = np.array(self.start_pos[:3])  # Ensure it's an array and use the first 3 components
            
            # Calculate displacement (distance between current and start position)
            displacement = np.linalg.norm(current_pos - start_pos)
            
            return {"displacement": float(displacement)}
        
        except Exception as e:
            logging.error(f"Error in get_displacement for object_id='{object_id}': {str(e)}")
            return {"error": str(e)}

    def move_object(self, object_id: str, x: float, y: float, z: float) -> dict:
        """
        Moves an object to the specified position in the simulation.

        Parameters:
            object_id (str): The unique identifier for the object.
            x (float): The x-coordinate for the new position.
            y (float): The y-coordinate for the new position.
            z (float): The z-coordinate for the new position.

        Returns:
            dict: A dictionary containing the new position of the object.
        """
        try:
            object_id = str(object_id)  # Ensure object_id is a string
            body_id = self.get_body_id(object_id)  # Get body ID based on the object name

            # Get the joint corresponding to the object and set its position
            joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, f"{object_id}_joint")  # type: ignore
            if joint_id == -1:
                return {"error": f"No joint named {object_id}_joint"}

            joint_qpos_addr = self.model.jnt_qposadr[joint_id]
            new_pos = np.array([x, y, z])

            # Optional: safety check
            if np.any(np.isnan(new_pos)) or np.any(np.isinf(new_pos)):
                return {"error": "Invalid position values (NaN or Inf)"}

            self.data.qpos[joint_qpos_addr:joint_qpos_addr+3] = new_pos
            mujoco.mj_forward(self.model, self.data) # type: ignore

            actual_position = self.data.qpos[joint_qpos_addr:joint_qpos_addr+3]
            logging.debug(f"Moved {object_id} to position: {actual_position}")
            return {"position": tuple(actual_position)}

        except Exception as e:
            return {"error": str(e)}
        
    def set_velocity(self, object_id: str, velocity_vector: list) -> dict:
        """
        Sets the velocity of an object in the simulation.

        Parameters:
            object_id (str): The unique identifier for the object.
            velocity_vector (list): The velocity vector [vx, vy, vz].

        Returns:
            dict: A dictionary indicating the status of the operation and the set velocity.
        """
        try:
            if not object_id.startswith("object_"):
                object_id = f"object_{object_id}"
            body_id = self.get_body_id(object_id)
            if body_id == -1:
                return {"error": f"Body named {object_id} not found."}
            if len(velocity_vector) != 3:
                raise ValueError("velocity_vector must be a list of 3 elements")
            # Map body_id to joint dof index (use model.jnt_qveladr for the joint)
            joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, f"{object_id}_joint") # type: ignore
            if joint_id == -1:
                return {"error": f"Joint named {object_id}_joint not found."}
            qvel_addr = self.model.jnt_dofadr[joint_id]  # address of dofs for this joint
            # qvel is flat array, set the 3 translation velocity components
            self.data.qvel[qvel_addr:qvel_addr+3] = velocity_vector
            mujoco.mj_forward(self.model, self.data) # type: ignore
            return {"status": "velocity_set", "object_id": object_id, "velocity": velocity_vector}
        except Exception as e:
            return {"error": f"Failed to set velocity: {str(e)}"}
                
    def get_velocity(self, object_id: str) -> dict:
        """
        Retrieves the velocity of an object in the simulation.

        Parameters:
            object_id (str): The unique identifier for the object.

        Returns:
            dict: A dictionary containing the velocity of the object.
        """
        try:
            if not object_id.startswith("object_"):
                object_id = f"object_{object_id}"
            joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, f"{object_id}_joint") # type: ignore
            if joint_id == -1:
                return {"error": f"Joint named {object_id}_joint not found."}
            qvel_addr = self.model.jnt_dofadr[joint_id]
            velocity = self.data.qvel[qvel_addr:qvel_addr+3]
            return {"velocity": velocity.tolist()}
        except Exception as e:
            return {"error": str(e)}
        
    def get_acceleration(self, object_id: str) -> dict:
        """
        Estimates the acceleration of an object using (v_final - v_initial) / timestep.

        Parameters:
            object_id (str): The unique identifier for the object.

        Returns:
            dict: A dictionary containing the acceleration of the object.
        """
        try:
            object_id = str(object_id)
            if not object_id.startswith("object_"):
                object_id = f"object_{object_id}"
            
            joint_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, f"{object_id}_joint") # type: ignore
            if joint_id == -1:
                return {"error": f"Joint named {object_id}_joint not found."}
            
            qvel_addr = self.model.jnt_dofadr[joint_id]
            current_velocity = np.array(self.data.qvel[qvel_addr:qvel_addr+3])
            
            if object_id not in self.prev_velocities:
                self.prev_velocities[object_id] = current_velocity
                return {"x": 0.0, "y": 0.0, "z": 0.0}  # First call, assume no acceleration
            
            previous_velocity = self.prev_velocities[object_id]
            acceleration = (current_velocity - previous_velocity) / self.model.opt.timestep
            self.prev_velocities[object_id] = current_velocity

            return {
                "x": float(acceleration[0]),
                "y": float(acceleration[1]),
                "z": float(acceleration[2])
            }
            
        except Exception as e:
            return {"error": str(e)}

    def compute_force(self, object_id: str, mass: float) -> dict:
        """
        Computes the force on an object using the equation F = ma.

        Parameters:
            object_id (str): The unique identifier for the object.
            mass (float): The mass of the object.

        Returns:
            dict: A dictionary containing the computed force on the object.
        """
        try:
            object_id = str(object_id)
            acceleration = self.get_acceleration(object_id) # type: ignore

            force = {
                "x": mass * acceleration["x"],
                "y": mass * acceleration["y"],
                "z": mass * acceleration["z"]
            }
            return force
        except Exception as e:
            return {"error": f"Failed to compute force: {str(e)}"}
        
    def get_torque(self, object_id: str):
        """
        Calculates the torque acting on an object in the simulation.

        Parameters:
            object_id (str): The unique identifier for the object.

        Returns:
            dict: A dictionary containing the torque acting on the object.
        """
        try:
            # Ensure object_id is a string, and handle conversion if it's an integer
            object_id = str(object_id)

            # Convert object_id to an integer if it's valid
            try:
                obj_index = int(object_id)
            except ValueError:
                raise ValueError(f"Invalid object_id format: {object_id}. Expected an integer ID.")
            
            # Ensure the index is within the bounds of the qfrc_applied array
            start_index = obj_index * 6 + 3
            end_index = obj_index * 6 + 6

            if start_index >= len(self.data.qfrc_applied) or end_index > len(self.data.qfrc_applied):
                raise IndexError(f"Index out of bounds: {start_index}-{end_index}.")
            
            # Extract the torque values
            torque = self.data.qfrc_applied[start_index:end_index]
            torque_dict = {"x": torque[0], "y": torque[1], "z": torque[2]}
            
            return {"torque": torque_dict}
        
        except Exception as e:
            logging.error(f"Error in get_torque for object_id='{object_id}': {str(e)}")
            return {"error": str(e)}
        
    def apply_force(self, object_id: str, force_vector: list) -> dict:
        """
        Applies a force to an object in the simulation.

        Parameters:
            object_id (str): The unique identifier for the object.
            force_vector (list): The force vector [fx, fy, fz].

        Returns:
            dict: A dictionary indicating the status of the operation and the applied force.
        """
        try:
            object_id = str(object_id)  # Ensure object_id is a string
            body_id = self.get_body_id(object_id)  # Get the body ID based on object_id
            
            # Ensure the force_vector has exactly 3 elements (x, y, z components)
            if len(force_vector) != 3:
                raise ValueError("force_vector must be a list of 3 elements: [fx, fy, fz]")

            # Apply the force to the object (set the force vector in the xfrc_applied array)
            self.data.xfrc_applied[body_id, :3] = force_vector  # Apply the force (first 3 elements)

            return {"status": "force_applied", "object_id": object_id, "force": force_vector}
        
        except ValueError as ve:
            return {"error": str(ve)}
        except Exception as e:
            return {"error": f"Failed to apply force to object '{object_id}': {str(e)}"}
        
    def apply_torque(self, object_id: str, torque_vector: list) -> dict:
        """
        Applies a torque to an object in the simulation.

        Parameters:
            object_id (str): The unique identifier for the object.
            torque_vector (list): The torque vector [tx, ty, tz].

        Returns:
            dict: A dictionary indicating the status of the operation and the applied torque.
        """
        try:
            object_id = str(object_id)  # Ensure object_id is a string
            body_id = self.get_body_id(object_id)  # Get the body ID based on object_id
            
            # Ensure the torque_vector has exactly 3 elements (torque around x, y, z axes)
            if len(torque_vector) != 3:
                raise ValueError("torque_vector must be a list of 3 elements: [tx, ty, tz]")

            # Apply the torque to the object (set the torque vector in the xfrc_applied array)
            self.data.xfrc_applied[body_id, 3:6] = torque_vector  # Apply the torque (last 3 elements)

            return {"status": "torque_applied", "object_id": object_id, "torque": torque_vector}
        
        except ValueError as ve:
            return {"error": str(ve)}
        except Exception as e:
            return {"error": f"Failed to apply torque to object '{object_id}': {str(e)}"}
        
    def get_kinetic_energy(self, object_id: str, mass: float) -> dict:
        """
        Calculates the kinetic energy of an object using the equation KE = 0.5 * m * v^2.

        Parameters:
            object_id (str): The unique identifier for the object.
            mass (float): The mass of the object.

        Returns:
            dict: A dictionary containing the kinetic energy of the object.
        """
        try:
            object_id = str(object_id)  # Ensure object_id is a string
            
            # Get velocity of the object
            velocity = self.get_velocity(object_id)
            
            if "velocity" not in velocity:
                raise ValueError(f"Could not retrieve velocity for object {object_id}.")
            
            # Ensure velocity is a numpy array for consistent behavior
            velocity_array = np.array(velocity["velocity"])
            
            # Calculate kinetic energy: 0.5 * mass * v^2
            kinetic_energy = 0.5 * mass * np.sum(velocity_array**2)
            
            return {"kinetic_energy": kinetic_energy}

        except Exception as e:
            # Log the error and provide more context for debugging
            logging.error(f"Error in get_kinetic_energy for object_id='{object_id}': {str(e)}")
            return {"error": str(e)}

    def get_potential_energy(self, object_id: str, mass: float, gravity: float = 9.81) -> dict:
        """
        Calculates the potential energy of an object using the equation PE = m * g * h.

        Parameters:
            object_id (str): The unique identifier for the object.
            mass (float): The mass of the object.
            gravity (float): The gravitational acceleration (default is 9.81 m/s^2).

        Returns:
            dict: A dictionary containing the potential energy of the object.
        """
        try:
            object_id = str(object_id)  # Ensure object_id is a string
            
            # Get position of the object
            position = self.get_position(object_id)
            
            if "position" not in position:
                raise ValueError(f"Could not retrieve position for object {object_id}.")
            
            pos = position["position"]
            
            # Ensure position has at least 3 components (x, y, z)
            if len(pos) < 3:
                raise ValueError(f"Position for object {object_id} is incomplete. Expected [x, y, z], got {pos}.")
            
            # Calculate potential energy: PE = mass * gravity * height (z-axis)
            potential_energy = mass * gravity * pos[2]  # Using z as height
            
            return {"potential_energy": potential_energy}

        except Exception as e:
            # Log the error and provide more context for debugging
            logging.error(f"Error in get_potential_energy for object_id='{object_id}': {str(e)}")
            return {"error": str(e)}
        
    def get_rotational_energy(self, object_id: str, mass: float) -> dict:
        """
        Calculates the rotational energy of an object.

        Parameters:
            object_id (str): The unique identifier for the object.
            mass (float): The mass of the object.

        Returns:
            dict: A dictionary containing the rotational energy of the object.
        """
        try:
            angular_velocity = self.get_angular_momentum(object_id, mass)["angular_momentum"]
            inertia = self.model.body_inertia[self.get_body_id(object_id)].tolist()
            rotational_energy = 0.5 * np.dot(angular_velocity, inertia)
            return {"rotational_energy": rotational_energy}
        except Exception as e:
            return {"error": str(e)}

    def get_momentum(self, object_id: str, mass: float):
        """
        Calculates the linear momentum of an object using the equation p = m * v.

        Parameters:
            object_id (str): The unique identifier for the object.
            mass (float): The mass of the object.

        Returns:
            dict: A dictionary containing the momentum of the object.
        """
        try:
            object_id = str(object_id)  # Ensure object_id is a string
            
            # Get the velocity of the object
            velocity = self.get_velocity(object_id)
            
            if "velocity" not in velocity:
                raise ValueError(f"Could not retrieve velocity for object {object_id}.")
            
            vel = velocity["velocity"]
            
            # Ensure velocity has at least 3 components (x, y, z)
            if len(vel) < 3:
                raise ValueError(f"Velocity for object {object_id} is incomplete. Expected [vx, vy, vz], got {vel}.")
            
            # Calculate momentum: p = m * v
            momentum = {
                "x": mass * vel[0],
                "y": mass * vel[1],
                "z": mass * vel[2]
            }
            
            return {"momentum": momentum}

        except Exception as e:
            # Log the error and provide more context for debugging
            logging.error(f"Error in get_momentum for object_id='{object_id}': {str(e)}")
            return {"error": str(e)}

    def get_angular_momentum(self, object_id: str, mass: float) -> dict:
        """
        Calculates the angular momentum of an object in the simulation.

        Parameters:
            object_id (str): The unique identifier for the object.
            mass (float): The mass of the object.

        Returns:
            dict: A dictionary containing the angular momentum of the object.
        """
        try:
            object_id = str(object_id)  # Ensure object_id is a string
            body_id = self.get_body_id(object_id)  # Get body ID based on object_id

            # Get the position vector of the body
            position = np.array(self.data.xpos[body_id])  # Assuming xpos holds the position (x, y, z)
            
            # Get the angular velocity components (the last 3 components)
            angvel = np.array(self.data.cvel[body_id][3:6])  # Angular velocity in (wx, wy, wz)
            
            # Calculate the angular momentum as cross product of position and momentum (mass * velocity)
            momentum = mass * np.array(self.data.qvel[body_id][:3])  # Linear momentum (mass * velocity)
            ang_momentum = np.cross(position, momentum)  # Cross product for angular momentum
            
            return {"angular_momentum": ang_momentum.tolist()}
        
        except Exception as e:
            return {"error": str(e)}
        
    def detect_collision(self, obj1_id: str, obj2_id: str) -> dict:
        """
        Detects a collision between two objects in the simulation and applies elastic forces.

        Parameters:
            obj1_id (str): The unique identifier for the first object.
            obj2_id (str): The unique identifier for the second object.

        Returns:
            dict: A dictionary indicating whether a collision was detected and the applied force.
        """
        try:
            obj1_id = str(obj1_id)
            obj2_id = str(obj2_id)
            
            # Convert object IDs to geometry indices (you may need a helper function for this)
            geom1_id = self.get_geom_id(obj1_id)
            geom2_id = self.get_geom_id(obj2_id)
            
            for contact in self.data.contact:
                # Check if the contact involves the two objects
                if (contact.geom1 == geom1_id and contact.geom2 == geom2_id) or \
                (contact.geom1 == geom2_id and contact.geom2 == geom1_id):
                    
                    # Apply simple elastic response based on contact normal and distance
                    normal_force = contact.frame[:3] * contact.dist
                    
                    # Apply force in the opposite direction to obj1 and the same direction to obj2
                    self.apply_force(obj1_id, -normal_force)
                    self.apply_force(obj2_id, normal_force)
                    
                    return {"collision_detected": True, "force_applied": normal_force.tolist()}
            
            # If no collision detected
            return {"collision_detected": False}
        
        except Exception as e:
            logging.error(f"Error in detect_collision: {str(e)}")
            return {"error": str(e)}
        
    def get_center_of_mass(self) -> dict:
        """
        Retrieves the center of mass for the entire simulation.

        Returns:
            dict: A dictionary containing the center of mass of the simulation.
        """
        try:
            com = self.data.subtree_com[0]  # Get center of mass from the first subtree
            return {"center_of_mass": {"x": com[0], "y": com[1], "z": com[2]}}
        except Exception as e:
            return {"error": f"Failed to retrieve center of mass: {str(e)}"}

    def quat_to_rot_matrix(self, q: list[float]) -> dict:
        """
        Converts a quaternion into a 3x3 rotation matrix.

        Parameters:
            q (list[float]): The quaternion representing the rotation.

        Returns:
            dict: A dictionary containing the resulting 3x3 rotation matrix.
        """
        try:
            q_np = np.array(q)
            mat = np.zeros((3, 3))
            mujoco.mju_matQuat(mat, q_np) # type: ignore
            return {"rotation_matrix": mat.tolist()}
        except Exception as e:
            return {"error": str(e)}
        
    def create_objects(self, name: str, pos: list, density: float, rgba: list):
        """
        Creates a new object in the simulation and adds it to the scene.

        Parameters:
            name (str): The name of the new object.
            pos (list): The position [x, y, z] of the new object.
            density (float): The density of the new object.
            rgba (list): The color and transparency (rgba values) of the new object.

        Returns:
            dict: A dictionary indicating the status of the operation and the details of the created object.
        """        
        # Parse the original scene XML
        tree = ET.parse(self.model_path)
        root = tree.getroot()

        # Create new body tag
        body = ET.Element("body", name=name)
        body.set("pos", f"{pos[0]} {pos[1]} {pos[2]}")
        
        # Create geometry for the object
        geom = ET.SubElement(body, "geom", type="sphere", size=str(density), rgba=" ".join(map(str, rgba)))
        
        # Add the new body tag to the XML
        root.append(body)
        
        # Save the updated XML to a new file

        updated_xml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "XMLFileCreation", f"{self.agent}",f"UpdatedXML/scene{self.scene_id}_updated.xml")
        if not os.path.exists(os.path.dirname(updated_xml_path)):
            os.makedirs(os.path.dirname(updated_xml_path))
        tree.write(updated_xml_path)
        
        # Reload the model with the updated XML
        self.load_scene(updated_xml_path)
        logging.info(f"Object {name} created at {pos} with density {density} and rgba {rgba}")
        return {"status": "object_created", "name": name, "position": pos, "density": density, "rgba": rgba}
    
    def delete_objects(self, object_id: str):
        """
        Deletes an object from the simulation by its ID.

        Parameters:
            object_id (str): The unique identifier for the object to be deleted.

        Returns:
            dict: A dictionary indicating the status of the deletion operation.
        """
        # Parse the XML
        tree = ET.parse(self.model_path)
        root = tree.getroot()

        # Find and remove the object with the given ID
        body = root.find(f".//body[@name='{object_id}']")
        if body is not None:
            root.remove(body)

        # Save the updated XML
        updated_xml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "XMLFileCreation", f"{self.agent}",f"UpdatedXML/scene{self.scene_id}_updated.xml")
        if not os.path.exists(os.path.dirname(updated_xml_path)):
            os.makedirs(os.path.dirname(updated_xml_path))
        tree.write(updated_xml_path)
        
        # Reload the model with the updated XML
        self.load_scene(updated_xml_path)
        logging.info(f"Object {object_id} deleted from the scene")
        return {"status": "object_deleted", "object_id": object_id}
    
    def find_objects(self):
        """
        Finds and updates all objects in the scene by modifying their rgba properties.

        Returns:
            dict: A dictionary indicating the status of the operation and the update.
        """
        # Parse the XML
        tree = ET.parse(self.model_path)
        root = tree.getroot()

        # Change the rgba for all geometries
        for geom in root.findall(".//geom"):
            geom.set("rgba", "0.7 0.7 0.7 1")

        # Save the updated XML
        updated_xml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "XMLFileCreation", f"{self.agent}",f"UpdatedXML/scene{self.scene_id}_updated.xml")
        if not os.path.exists(os.path.dirname(updated_xml_path)):
            os.makedirs(os.path.dirname(updated_xml_path))
        tree.write(updated_xml_path)

        # Reload the model with the updated XML
        self.load_scene(updated_xml_path)
        logging.info("All objects' rgba values have been updated to 0.7 0.7 0.7 1")
        return {"status": "rgba_updated and object permissions are as given"}
    
    def attach_objects(self, object1_id: str, object2_id: str):
        """
        Attaches two objects together in the simulation by creating a joint between them.

        Parameters:
            object1_id (str): The unique identifier for the first object.
            object2_id (str): The unique identifier for the second object.

        Returns:
            dict: A dictionary indicating the status of the attachment operation.
        """        
        # Parse the XML
        tree = ET.parse(self.model_path)
        root = tree.getroot()

        # Find the two bodies to attach
        body1 = root.find(f".//body[@name='{object1_id}']")
        body2 = root.find(f".//body[@name='{object2_id}']")
        
        if body1 is None or body2 is None:
            logging.error("One or both objects not found for attachment")
            return

        # Create a joint or tendon to attach them
        joint = ET.SubElement(root, "joint", name=f"joint_{object1_id}_{object2_id}", type="revolute")
        joint.set("body1", object1_id)
        joint.set("body2", object2_id)

        # Save the updated XML
        updated_xml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "XMLFileCreation", f"{self.agent}",f"UpdatedXML/scene{self.scene_id}_updated.xml")
        if not os.path.exists(os.path.dirname(updated_xml_path)):
            os.makedirs(os.path.dirname(updated_xml_path))
        tree.write(updated_xml_path)

        # Reload the model with the updated XML
        self.load_scene(updated_xml_path)
        logging.info(f"Objects {object1_id} and {object2_id} have been attached")
