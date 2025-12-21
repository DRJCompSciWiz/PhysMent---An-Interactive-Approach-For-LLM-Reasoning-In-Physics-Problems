import os
import sys

def main(input_file):
    # Determine file type and extension
    if input_file.endswith('.txt'):
        if 'json' in input_file:
            ext = '.json'
        elif 'xml' in input_file:
            ext = '.xml'
        else:
            print("Input file must contain 'json' or 'xml' in its name.")
            return
    else:
        print("Input file must be a .txt file.")
        return

    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by marker
    blocks = [b for b in content.split('---#') if b.strip()]
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scenes_dir = os.path.join(base_dir, 'Scenes')

    for block in blocks:
        # The first line is the float (e.g., 15.1)
        lines = block.strip().splitlines()
        if not lines:
            continue
        float_id = lines[0].strip()
        try:
            scene_number, sub_number = float_id.split('.')
        except ValueError:
            print(f"Invalid scene marker: {float_id}")
            continue
        folder = os.path.join(scenes_dir, f"Scene{scene_number}", f"Scene{scene_number}.{sub_number}")
        os.makedirs(folder, exist_ok=True)
        filename = f"Scene{scene_number}.{sub_number}{ext}"
        filepath = os.path.join(folder, filename)
        # The rest of the block is the code
        code = '\n'.join(lines[1:]).strip()
        with open(filepath, 'w', encoding='utf-8') as out:
            out.write(code + '\n')
        print(f"Wrote {filepath}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scenesorter.py scene_json.txt")
    else:
        main(sys.argv[1])