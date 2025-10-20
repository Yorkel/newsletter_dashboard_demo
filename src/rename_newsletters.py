#rename_newsletters.py

import os 
import re

folder_path = "/workspaces/ERP_Newsletter/data_raw/newsletters_15.10.2025"

for filename in os.listdir(folder_path): 
    if filename.lower().endswith(".html"):
        match = re.search(r'Newsletter\s*(\d+)', filename)
        if match: 
            number = int(match.group(1))
            new_name = f"newsletter_{number:02d}.html"
            old_path = os.path.join(folder_path, filename)
            new_path = os.path.join(folder_path, new_name)
            os.rename(old_path, new_path)
            print(f"Renamed: {filename} → {new_name}")

print("All newsletter files renamed successfully!")
