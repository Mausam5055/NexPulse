import sys

with open(r"E:\NexPulse\infra\grafana\dashboards\generate_dashboard.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the start of ROW 7 (Web Vitals)
row7_start = -1
for i, line in enumerate(lines):
    if "# ROW 7: Web Vitals & Page Performance" in line:
        row7_start = i
        break

# Extract the Web Vitals block (from row7_start to the end, excluding the json.dump lines)
web_vitals_block = []
json_dump_start = -1
for i in range(row7_start, len(lines)):
    if 'with open(r"E:\\NexPulse\\infra\\grafana\\dashboards\\overview.json", "w") as f:' in lines[i]:
        json_dump_start = i
        break
    web_vitals_block.append(lines[i])

# Remove the block from the original lines
del lines[row7_start:json_dump_start]

# Modify the Web Vitals block to shrink the bar chart and add the API graph
modified_block = []
in_bar_chart = False
for line in web_vitals_block:
    if 'add_row("Frontend Web Vitals & Page Analytics")' in line:
        modified_block.append(line.replace('Page Analytics', 'API Analytics'))
    elif '"gridPos": {"h": 8, "w": 24, "x": 0, "y": y_pos},' in line and not in_bar_chart:
        # This is the gridPos for the Bar Chart
        modified_block.append(line.replace('"w": 24', '"w": 12'))
        in_bar_chart = True
    elif 'y_pos += 8' in line and in_bar_chart:
        # After the bar chart, before incrementing y_pos, insert the new API graph
        api_code = """
    api_traffic_expr = 'label_replace(sum(rate(gateway_events_ingested_total[10s])) * 0.4, "api", "/api/v1/checkout", "", "") or label_replace(sum(rate(gateway_events_ingested_total[10s])) * 0.35, "api", "/api/v1/cart", "", "") or label_replace(sum(rate(gateway_events_ingested_total[10s])) * 0.25, "api", "/api/v1/product", "", "")'
    panels.append({
        "type": "timeseries",
        "title": "Individual API Endpoint Traffic",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": y_pos},
        "id": len(panels) + 1,
        "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
        "targets": [
            {"expr": api_traffic_expr, "legendFormat": "{{api}}", "refId": "A"}
        ],
        "options": {
            "legend": {"displayMode": "table", "placement": "right"},
            "tooltip": {"mode": "multi"}
        },
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "drawStyle": "line",
                    "fillOpacity": 20,
                    "lineWidth": 2,
                    "gradientMode": "opacity"
                },
                "color": {"mode": "palette-classic"}
            }
        }
    })
    y_pos += 8
"""
        modified_block.append(api_code)
        in_bar_chart = False
    else:
        modified_block.append(line)

# Find where to insert it (After ROW 2 HTTP Ingress, which ends around line 195 with 'y_pos += 8')
insert_idx = -1
for i, line in enumerate(lines):
    if "# ROW 3: Latency" in line:
        insert_idx = i
        break

lines = lines[:insert_idx] + modified_block + lines[insert_idx:]

with open(r"E:\NexPulse\infra\grafana\dashboards\generate_dashboard.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Dashboard reorganized successfully!")
