import sys

with open(r"E:\NexPulse\infra\grafana\dashboards\generate_dashboard.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
for i, line in enumerate(lines):
    if "# ROW 1: KPIs" in line:
        start_idx = i
        break

end_idx = -1
for i, line in enumerate(lines):
    if "# ROW 2: HTTP Ingress" in line:
        end_idx = i
        break

new_block = """    # ROW 1: Overview & System Saturation
    add_row("Overview & System Saturation")
    
    def create_minimal_stat(title, expr, x, color, unit="none"):
        return {
            "type": "stat",
            "title": title,
            "gridPos": {"h": 5, "w": 3, "x": x, "y": y_pos},
            "id": len(panels) + 1,
            "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
            "targets": [{"expr": expr, "refId": "A"}],
            "options": {
                "colorMode": "value",
                "graphMode": "none",
                "justifyMode": "auto",
                "reduceOptions": {"calcs": ["lastNotNull"]},
                "textMode": "auto"
            },
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "fixed", "fixedColor": color},
                    "unit": unit
                }
            }
        }
        
    def create_horiz_gauge(title, expr, x, color, unit="none", max_val=100, invert_colors=False):
        steps = [
            {"color": "green", "value": None}, 
            {"color": "orange", "value": max_val * 0.7}, 
            {"color": "red", "value": max_val * 0.9}
        ]
        if invert_colors:
            steps = [
                {"color": "red", "value": None}, 
                {"color": "orange", "value": max_val * 0.1}, 
                {"color": "green", "value": max_val * 0.3}
            ]
            
        return {
            "type": "gauge",
            "title": title,
            "gridPos": {"h": 5, "w": 3, "x": x, "y": y_pos},
            "id": len(panels) + 1,
            "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
            "targets": [{"expr": expr, "refId": "A"}],
            "options": {
                "reduceOptions": {"calcs": ["lastNotNull"], "values": False},
                "orientation": "horizontal",
                "showThresholdLabels": False,
                "showThresholdMarkers": True
            },
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "thresholds"},
                    "max": max_val,
                    "min": 0,
                    "thresholds": {"mode": "absolute", "steps": steps},
                    "unit": unit
                }
            }
        }

    panels.append(create_minimal_stat("Requests", "sum(rate(gateway_events_ingested_total[30s]))", 0, "blue", "reqps"))
    panels.append(create_minimal_stat("Errors", "sum(rate(gateway_events_rejected_total[30s]))", 3, "red", "reqps"))
    panels.append(create_horiz_gauge("Gateway Load", "gateway_active_connections / 1000 * 100", 6, "red", "percent"))
    panels.append(create_horiz_gauge("Kafka Backpr.", "sum(kafka_consumergroup_lag{consumergroup=\\"aggregator-group\\"})", 9, "orange", "none", 1000))
    panels.append(create_horiz_gauge("Memory Util", "redis_memory_used_bytes / (1024*1024*1024) * 100", 12, "green", "percent"))
    panels.append(create_horiz_gauge("WebSockets", "query_websocket_connections_active / 5000 * 100", 15, "blue", "percent"))
    panels.append(create_horiz_gauge("Active Conn.", "gateway_active_connections / 1000 * 100", 18, "purple", "percent"))
    panels.append(create_horiz_gauge("Success Rate", "100 - (100 * sum(rate(gateway_events_rejected_total[30s])) / (sum(rate(gateway_events_ingested_total[30s])) + sum(rate(gateway_events_rejected_total[30s])) + 0.001))", 21, "green", "percent", 100, True))
    y_pos += 5

"""

lines = lines[:start_idx] + [new_block] + lines[end_idx:]

with open(r"E:\NexPulse\infra\grafana\dashboards\generate_dashboard.py", "w", encoding="utf-8") as f:
    f.writelines(lines)
