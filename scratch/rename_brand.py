import os
import re

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

REPLACEMENTS = [
    ('SmartKCET <span class="brand-ai">Prep</span>', 'Mr.<span class="brand-ai">E</span>'),
    ('SmartKCET<span class="brand-ai">Prep</span>', 'Mr.<span class="brand-ai">E</span>'),
    ('SmartKCET<span class="brand-ai"> AI</span>', 'Mr.<span class="brand-ai">E</span>'),
    ('SmartKCET <span class="brand-ai">AI</span>', 'Mr.<span class="brand-ai">E</span>'),
    ('SmartKCET Prep', 'Mr.E'),
    ('SmartKCET-Prep', 'Mr.E'),
    ('SmartKCETPrep', 'Mr.E'),
    ('SmartKCET', 'Mr.E'),
]

def main():
    total_files = 0
    total_replacements = 0

    for root, dirs, files in os.walk(FRONTEND_DIR):
        for fname in files:
            if fname.endswith(('.html', '.js', '.css')):
                fpath = os.path.join(root, fname)
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()

                orig_content = content
                file_replacements = 0
                for old_str, new_str in REPLACEMENTS:
                    count = content.count(old_str)
                    if count > 0:
                        content = content.replace(old_str, new_str)
                        file_replacements += count

                if content != orig_content:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Updated {fname}: {file_replacements} replacements")
                    total_files += 1
                    total_replacements += file_replacements

    print(f"Done! Modified {total_files} files with {total_replacements} total replacements.")

if __name__ == "__main__":
    main()
