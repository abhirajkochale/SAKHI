# -*- coding: utf-8 -*-
import os
import subprocess

out_dir_docs = r"C:\GitHub\SAKHI\docs\flowcharts"
out_dir_artifacts = r"C:\Users\abhir\.gemini\antigravity\brain\0b23f962-4bf9-44d4-9fd5-caaeedac01c8\artifacts"
os.makedirs(out_dir_docs, exist_ok=True)
os.makedirs(out_dir_artifacts, exist_ok=True)

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def render_svg_to_png(svg_path, png_path, width, height):
    file_uri = f"file:///{svg_path.replace('\\', '/')}"
    cmd = [
        EDGE_PATH,
        "--headless",
        "--disable-gpu",
        f"--window-size={width},{height}",
        f"--screenshot={png_path}",
        file_uri
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("Setup completed successfully.")
