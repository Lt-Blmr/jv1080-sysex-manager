import re

print("Reading YAML file...")
with open('roland_jv_1080_fixed.yaml', 'r', encoding='utf-8') as f:
    content = f.read()

print("Original file size:", len(content), "characters")

# Create backup
with open('roland_jv_1080_fixed_backup_fix.yaml', 'w', encoding='utf-8') as f:
    f.write(content)
print("Backup created: roland_jv_1080_fixed_backup_fix.yaml")

# Look for and fix line concatenation issues
print("Searching for line concatenation issues...")

# Fix common concatenation patterns
fixes_made = 0

# Pattern 1: bytes: 1[space/tab]- name:
pattern1 = re.compile(r'bytes:\s*1\s+(-\s*name:)')
matches1 = pattern1.findall(content)
if matches1:
    print(f"Found {len(matches1)} instances of bytes:1 concatenated with - name:")
    content = pattern1.sub(r'bytes: 1\n        \1', content)
    fixes_made += len(matches1)

# Pattern 2: Look for any case where a value is immediately followed by a dash
pattern2 = re.compile(r'(\w+:\s*\d+)\s+(-\s*name:)')
matches2 = pattern2.findall(content)
if matches2:
    print(f"Found {len(matches2)} instances of value concatenated with - name:")
    content = pattern2.sub(r'\1\n        \2', content)
    fixes_made += len(matches2)

# Pattern 3: Look for missing newlines before list items
pattern3 = re.compile(r'(\s+)(\w+):\s*(\w+|\d+)\s+(-\s*name:)')
matches3 = pattern3.findall(content)
if matches3:
    print(f"Found {len(matches3)} instances of property concatenated with list item:")
    content = pattern3.sub(r'\1\2: \3\n        \4', content)
    fixes_made += len(matches3)

# Fix negative numbers (quote them)
print("Fixing negative numbers...")
neg_fixes = 0
neg_pattern = re.compile(r'(min|max):\s*(-\d+)')
neg_matches = neg_pattern.findall(content)
if neg_matches:
    print(f"Found {len(neg_matches)} negative numbers to quote")
    content = neg_pattern.sub(r'\1: "\2"', content)
    neg_fixes = len(neg_matches)

print(f"Total line concatenation fixes made: {fixes_made}")
print(f"Total negative number fixes made: {neg_fixes}")

# Write fixed content
print("Writing fixed content...")
with open('roland_jv_1080_fixed.yaml', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed file size:", len(content), "characters")
print("✅ YAML fixing complete!")
