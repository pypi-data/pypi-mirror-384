from ..config import PROMPTS_DIR
import os
    
def prompt_path(code_version, lang, basepath):
    folder_path = PROMPTS_DIR / code_version / lang
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"The method {code_version} has not yet been implemented in {lang}.")
    return folder_path / f'{basepath}.txt'

def load_prompt(code_version, lang, basepath):
    filepath = prompt_path(code_version, lang, basepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()