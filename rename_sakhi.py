
import os
import re
from pathlib import Path

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'safhera' not in content.lower():
            return False

        # Case-preserving replace
        def replacer(match):
            word = match.group(0)
            if word.islower(): return 'sakhi'
            elif word.isupper(): return 'SAKHI'
            elif word.istitle(): return 'Sakhi'
            else: return 'sakhi'
            
        new_content = re.sub(r'(?i)safhera', replacer, content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Updated: {filepath}')
        return True
    except Exception as e:
        print(f'Error reading {filepath}: {e}')
        return False

search_dirs = ['backend/app', 'ml', 'docs']
for d in search_dirs:
    for root, dirs, files in os.walk(d):
        for file in files:
            if file.endswith(('.py', '.json', '.md')):
                replace_in_file(os.path.join(root, file))

# Rename files
files_to_rename = [
    'ml/models/safhera_xgboost_risk_model.json',
    'ml/models/safhera_model_metadata.json'
]
for f in files_to_rename:
    if os.path.exists(f):
        new_name = f.replace('safhera', 'sakhi')
        os.rename(f, new_name)
        print(f'Renamed: {f} -> {new_name}')

