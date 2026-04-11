#!/usr/bin/env python3
"""
Script to migrate OldScenes to the Scenes directory with proper structure and permissions.
"""

import os
import json
import shutil
import re


def extract_scene_number(dirname):
    """Extract the scene number from a directory name."""
    # Remove spaces and "Scene" prefix, extract number
    match = re.search(r'(\d+)', dirname)
    if match:
        return int(match.group(1))
    return None


def simplify_permissions(permissions):
    """
    Simplify old permission format to new format.
    Old format had: type, density, mass, radius, name, pos, quat, size
    New format only has: type, density, size (and hidden for special cases)
    """
    simplified = {}
    for obj_key, obj_perms in permissions.items():
        # Start with basic permissions
        new_perms = {
            "type": obj_perms.get("type", True),
            "density": obj_perms.get("density", True),
            "size": obj_perms.get("size", obj_perms.get("radius", True))  # Map radius to size
        }

        # Keep hidden if it exists
        if "hidden" in obj_perms:
            new_perms["hidden"] = obj_perms["hidden"]

        simplified[obj_key] = new_perms

    return simplified


def update_permissions_to_granular(permissions):
    """
    Convert simplified permissions (type, density, size) to granular XML attribute permissions.
    Based on the current Scene.py implementation.
    """
    granular_permissions = {}

    for obj_key, obj_perms in permissions.items():
        granular = {}

        # Map high-level permissions to specific XML attributes
        if obj_perms.get("type", False):
            granular["geom_type"] = True

        if obj_perms.get("density", False):
            granular["geom_density"] = True
            granular["body_mass"] = True

        if obj_perms.get("size", False):
            granular["geom_size"] = True
            granular["geom_radius"] = True

        # Position is commonly needed
        granular["body_pos"] = True

        # Quaternion for rotation
        granular["body_quat"] = True

        # Keep hidden if it exists
        if "hidden" in obj_perms:
            granular["hidden"] = obj_perms["hidden"]

        granular_permissions[obj_key] = granular

    return granular_permissions


def migrate_scene(old_scene_path, scene_number, scenes_base_dir):
    """Migrate a single scene from OldScenes to Scenes."""
    # Find the JSON and XML files
    json_files = []
    xml_files = []

    for root, dirs, files in os.walk(old_scene_path):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
            elif file.endswith('.xml') and 'answer' not in file.lower():
                # Skip answer files and other non-primary XML files
                xml_files.append(os.path.join(root, file))

    # Find the primary scene files (scene{number}.json and scene{number}.xml)
    primary_json = None
    primary_xml = None

    for json_file in json_files:
        if f'scene{scene_number}.json' in os.path.basename(json_file).lower():
            primary_json = json_file
            break

    for xml_file in xml_files:
        basename = os.path.basename(xml_file).lower()
        if f'scene{scene_number}.xml' in basename and 'mass' not in basename and 'spring' not in basename:
            primary_xml = xml_file
            break

    if not primary_json:
        print(f"  ⚠️  No JSON file found for scene {scene_number}")
        return False

    if not primary_xml:
        print(f"  ⚠️  No XML file found for scene {scene_number}")
        return False

    # Create the new scene directory
    new_scene_dir = os.path.join(scenes_base_dir, f"Scene{scene_number}")
    os.makedirs(new_scene_dir, exist_ok=True)

    # Load and update the JSON file
    try:
        with open(primary_json, 'r') as f:
            scene_data = json.load(f)

        # Update permissions to granular format
        if "object_permissions" in scene_data:
            old_perms = scene_data["object_permissions"]
            # First simplify to basic format
            simple_perms = simplify_permissions(old_perms)
            # Then convert to granular format
            scene_data["object_permissions"] = update_permissions_to_granular(simple_perms)

        # Write the updated JSON file
        new_json_path = os.path.join(new_scene_dir, f"scene{scene_number}.json")
        with open(new_json_path, 'w') as f:
            json.dump(scene_data, f, indent=2)

        # Copy the XML file
        new_xml_path = os.path.join(new_scene_dir, f"scene{scene_number}.xml")
        shutil.copy2(primary_xml, new_xml_path)

        print(f"  ✅ Migrated scene {scene_number}")
        return True

    except Exception as e:
        print(f"  ❌ Error migrating scene {scene_number}: {e}")
        return False


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    old_scenes_dir = os.path.join(script_dir, "OldScenes")
    scenes_dir = os.path.join(script_dir, "Scenes")

    if not os.path.exists(old_scenes_dir):
        print(f"❌ OldScenes directory not found at {old_scenes_dir}")
        return

    # Get all scene directories
    scene_dirs = []
    for item in os.listdir(old_scenes_dir):
        item_path = os.path.join(old_scenes_dir, item)
        if os.path.isdir(item_path):
            scene_num = extract_scene_number(item)
            if scene_num is not None:
                scene_dirs.append((scene_num, item_path))

    # Sort by scene number
    scene_dirs.sort(key=lambda x: x[0])

    print(f"Found {len(scene_dirs)} scenes to migrate\n")

    success_count = 0
    for scene_num, scene_path in scene_dirs:
        print(f"Migrating scene {scene_num}...")
        if migrate_scene(scene_path, scene_num, scenes_dir):
            success_count += 1

    print(f"\n✅ Successfully migrated {success_count}/{len(scene_dirs)} scenes")


if __name__ == "__main__":
    main()
