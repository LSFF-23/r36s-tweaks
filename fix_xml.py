import os
import xml.etree.ElementTree as ET
from collections import defaultdict

def find_duplicates(directory_path):
    for filename in os.listdir(directory_path):
        if filename.endswith(".xml"):
            file_path = os.path.join(directory_path, filename)
            
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
                
                name_map = defaultdict(list)
                
                for game in root.findall('game'):
                    name_node = game.find('name')
                    if name_node is not None and name_node.text:
                        game_name = name_node.text.strip()
                        path_node = game.find('path')
                        game_path = path_node.text if path_node is not None else "Unknown path"
                        
                        name_map[game_name].append(game_path)

                duplicates = {name: paths for name, paths in name_map.items() if len(paths) > 1}

                if duplicates:
                    print(f"\n--- Duplicates found in: {filename} ---")
                    for name, paths in duplicates.items():
                        print(f"Name: {name} ({len(paths)} occurrences)")
                        for path in paths:
                            print(f"  - Path: {path}")
                
            except ET.ParseError:
                print(f"Error parsing file: {filename}")

find_duplicates("./")
