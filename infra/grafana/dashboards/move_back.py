import sys

with open(r"E:\NexPulse\infra\grafana\dashboards\generate_dashboard.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the start of the Web Vitals section
start_idx = -1
for i, line in enumerate(lines):
    if 'add_row("Frontend Web Vitals & API Analytics")' in line:
        start_idx = i
        break

if start_idx == -1:
    print("Could not find section!")
    sys.exit(1)

# Find the end of the Web Vitals section
# It ends when we see the next "# ROW " or the `with open` block
end_idx = -1
for i in range(start_idx + 1, len(lines)):
    if lines[i].strip().startswith("# ROW ") or "with open(" in lines[i]:
        end_idx = i
        break

if end_idx == -1:
    print("Could not find end of section!")
    sys.exit(1)

# Extract the block
web_vitals_block = lines[start_idx:end_idx]

# Remove the block
del lines[start_idx:end_idx]

# Find the very end of all panels to append it
# The end of all panels is right before `with open(`
insert_idx = -1
for i, line in enumerate(lines):
    if "with open(" in line:
        insert_idx = i
        break

# We want to insert it right before the `with open(` line
# Let's add a newline before appending
if insert_idx != -1:
    lines = lines[:insert_idx] + ["\n    # ROW 7: Web Vitals & Page Performance\n"] + web_vitals_block + lines[insert_idx:]
else:
    print("Could not find insertion point!")
    sys.exit(1)

with open(r"E:\NexPulse\infra\grafana\dashboards\generate_dashboard.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Moved section back to the bottom!")
