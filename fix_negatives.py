import re

# Read the YAML file
with open('roland_jv_1080_fixed.yaml', 'r', encoding='utf-8') as f:
    content = f.read()

print("Fixing negative numbers...")

# Fix negative numbers by adding quotes
content = re.sub(r'min:\s*(-\d+)', r'min: "\1"', content)
content = re.sub(r'max:\s*(-\d+)', r'max: "\1"', content)

print("Writing fixed content...")

# Write back the fixed content
with open('roland_jv_1080_fixed.yaml', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Negative number formatting fixed!")
