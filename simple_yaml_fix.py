import re

# Read the file
with open('roland_jv_1080_fixed.yaml', 'r', encoding='utf-8') as f:
    content = f.read()

print("Fixing YAML issues...")

# Fix line breaks where bytes: N and - name: are on same line
original_content = content
content = re.sub(r'(\s+bytes:\s*\d+)\s+(-\s+name:)', r'\1\n        \2', content)
line_break_fixes = len(re.findall(r'(\s+bytes:\s*\d+)\s+(-\s+name:)', original_content))
print(f"Fixed {line_break_fixes} line break issues")

# Split into lines for detailed processing
lines = content.split('\n')
fixed_lines = []

for i, line in enumerate(lines):
    stripped = line.strip()
    
    # Fix indentation for parameter properties that are misaligned
    if stripped.startswith(('offset_hex:', 'min:', 'max:', 'bytes:')):
        # Check if we're in a parameter list context
        in_param_context = False
        for j in range(max(0, i-5), i):
            if '- name:' in lines[j]:
                in_param_context = True
                break
        
        if in_param_context and not line.startswith('          '):
            line = '          ' + stripped
            
    fixed_lines.append(line)

content = '\n'.join(fixed_lines)

# Fix missing quotes around names
def fix_name_quotes(match):
    full_match = match.group(0)
    if '- name:' in full_match and '"' not in full_match.split('name:')[1]:
        # Extract the name part and add quotes
        name_part = full_match.split('name:')[1].strip()
        return full_match.replace(name_part, f'"{name_part}"')
    return full_match

# Apply the name quote fixes
quote_pattern = r'- name:[^\n"]*[^\n"]'
quote_fixes = len(re.findall(quote_pattern, content))
content = re.sub(quote_pattern, fix_name_quotes, content)
print(f"Fixed {quote_fixes} quote issues")

# Write back
with open('roland_jv_1080_fixed.yaml', 'w', encoding='utf-8') as f:
    f.write(content)

print("YAML fixes completed!")
