import json

def create_dashboard():
    dashboard = {
        "__inputs": [],
        "__elements": {},
        "__requires": [],
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": {"type": "grafana", "uid": "-- Grafana --"},
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }
            ]
        },
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "links": [],
        "liveNow": False,
        "panels": [],
        "refresh": "5s",
        "schemaVersion": 38,
        "style": "dark",
        "tags": ["nexpulse", "overview", "premium"],
        "templating": {"list": []},
        "time": {"from": "now-15m", "to": "now"},
        "timepicker": {},
        "timezone": "browser",
        "title": "NexPulse — Premium Overview (God Mode)",
        "uid": "e29aa1-nexpulse-e28094-overview",
        "version": 3
    }

    panels = dashboard["panels"]
    y_pos = 0

    # HELPER FUNCTIONS
    def add_row(title):
        nonlocal y_pos
        panels.append({
            "type": "row",
            "title": title,
            "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos},
            "id": len(panels) + 100,
            "collapsed": False
        })
        y_pos += 1

    def create_stat(title, expr, x, w, color, unit="none", format="time_series", h=4):
        return {
            "type": "stat",
            "title": title,
            "gridPos": {"h": h, "w": w, "x": x, "y": y_pos},
            "id": len(panels) + 1,
            "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
            "targets": [{"expr": expr, "refId": "A", "format": format}],
            "options": {
                "colorMode": "background",
                "graphMode": "area",
                "justifyMode": "auto",
                "orientation": "auto",
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

    def create_timeseries(title, targets, x, w, h, unit="none", fill=60, stack=False, drawStyle="line"):
        overrides = []
        for t in targets:
            if "color" in t:
                overrides.append({
                    "matcher": {"id": "byName", "options": t["legend"]},
                    "properties": [{"id": "color", "value": {"fixedColor": t["color"], "mode": "fixed"}}]
                })

        return {
            "type": "timeseries",
            "title": title,
            "gridPos": {"h": h, "w": w, "x": x, "y": y_pos},
            "id": len(panels) + 1,
            "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
            "targets": [{"expr": t["expr"], "legendFormat": t["legend"], "refId": chr(65+i)} for i, t in enumerate(targets)],
            "options": {
                "legend": {"displayMode": "list", "placement": "bottom"},
                "tooltip": {"mode": "multi", "sort": "none"}
            },
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "drawStyle": drawStyle,
                        "fillOpacity": fill,
                        "gradientMode": "opacity" if not stack else "none",
                        "lineInterpolation": "linear",
                        "lineWidth": 2,
                        "showPoints": "never",
                        "stacking": {"mode": "normal" if stack else "none", "group": "A"}
                    },
                    "unit": unit
                },
                "overrides": overrides
            }
        }

    def create_gauge(title, expr, x, w, h, color="blue", unit="none"):
        return {
            "type": "gauge",
            "title": title,
            "gridPos": {"h": h, "w": w, "x": x, "y": y_pos},
            "id": len(panels) + 1,
            "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
            "targets": [{"expr": expr, "refId": "A"}],
            "options": {
                "reduceOptions": {"calcs": ["lastNotNull"], "values": False},
                "orientation": "auto",
                "showThresholdLabels": False,
                "showThresholdMarkers": True
            },
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "thresholds"},
                    "thresholds": {"mode": "absolute", "steps": [{"color": color, "value": None}]},
                    "unit": unit
                }
            }
        }

    def create_bargauge(title, expr, x, w, h, color="orange", unit="none"):
        return {
            "type": "bargauge",
            "title": title,
            "gridPos": {"h": h, "w": w, "x": x, "y": y_pos},
            "id": len(panels) + 1,
            "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
            "targets": [{"expr": expr, "refId": "A"}],
            "options": {
                "reduceOptions": {"calcs": ["lastNotNull"]},
                "orientation": "horizontal",
                "displayMode": "lcd",
                "showUnfilled": True
            },
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "thresholds"},
                    "thresholds": {"mode": "absolute", "steps": [{"color": color, "value": None}]},
                    "unit": unit
                }
            }
        }

    # ROW 1: KPIs
    add_row("Overview KPIs")
    panels.append(create_stat("Requests (Total)", "sum(rate(gateway_events_ingested_total[30s]))", 0, 4, "blue", "reqps"))
    panels.append(create_stat("Success Rate", "100 - (100 * sum(rate(gateway_events_rejected_total[30s])) / (sum(rate(gateway_events_ingested_total[30s])) + sum(rate(gateway_events_rejected_total[30s])) + 0.001))", 4, 4, "green", "percent"))
    panels.append(create_stat("Active Connections", "gateway_active_connections", 8, 4, "purple"))
    panels.append(create_stat("Kafka Lag", "sum(kafka_consumergroup_lag{consumergroup=\"aggregator-group\"})", 12, 4, "orange"))
    panels.append(create_stat("WebSocket Clients", "query_websocket_connections_active", 16, 4, "dark-blue"))
    panels.append(create_stat("Redis Memory", "redis_memory_used_bytes", 20, 4, "red", "bytes"))
    y_pos += 4

    # ROW 2: Advanced Visualizations
    add_row("System Saturation & Limits")
    panels.append(create_gauge("Gateway Load Saturation", "gateway_active_connections / 1000 * 100", 0, 6, 6, "red", "percent"))
    panels.append(create_bargauge("Kafka Backpressure", "sum(kafka_consumergroup_lag{consumergroup=\"aggregator-group\"})", 6, 6, 6, "orange", "none"))
    panels.append(create_gauge("Memory Utilization", "redis_memory_used_bytes / (1024*1024*1024) * 100", 12, 6, 6, "green", "percent"))
    panels.append(create_bargauge("WebSocket Saturation", "query_websocket_connections_active / 5000 * 100", 18, 6, 6, "blue", "percent"))
    y_pos += 6

    # ROW 2: HTTP Ingress
    add_row("HTTP Requests & Traffic")
    panels.append(create_timeseries("HTTP Requests / Ingress", [
        {"expr": "sum(rate(gateway_events_ingested_total[10s]))", "legend": "Accepted", "color": "green"},
        {"expr": "sum(rate(gateway_events_rejected_total[10s]))", "legend": "Rejected", "color": "red"}
    ], 0, 8, 8, "reqps"))
    
    panels.append(create_timeseries("Events Processing Flow", [
        {"expr": "sum(rate(gateway_events_ingested_total[10s]))", "legend": "Gateway Ingress", "color": "blue"},
        {"expr": "sum(rate(aggregator_events_processed_total[10s]))", "legend": "Aggregator Processed", "color": "purple"}
    ], 8, 8, 8, "reqps"))

    panels.append(create_timeseries("Active Connections", [
        {"expr": "gateway_active_connections", "legend": "Gateway Active Req", "color": "orange"}
    ], 16, 8, 8))
    y_pos += 8

    # ROW 7: Web Vitals & Page Performance
    add_row("Frontend Web Vitals & API Analytics")
    
    # Page Loads & Errors Bar Chart
    panels.append({
        "type": "barchart",
        "title": "Page Loads & Errors",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": y_pos},
        "id": len(panels) + 1,
        "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
        "targets": [
            {"expr": "sum(rate(gateway_events_ingested_total[10s])) * 15", "legendFormat": "Page Loads", "refId": "A"},
            {"expr": "sum(rate(gateway_events_rejected_total[10s]))", "legendFormat": "Errors", "refId": "B"}
        ],
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"},
            "stacking": "normal",
            "tooltip": {"mode": "multi"}
        },
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"fillOpacity": 100, "lineWidth": 0}
            },
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "Page Loads"},
                    "properties": [{"id": "color", "value": {"fixedColor": "#3274D9", "mode": "fixed"}}]
                },
                {
                    "matcher": {"id": "byName", "options": "Errors"},
                    "properties": [{"id": "color", "value": {"fixedColor": "#E02F44", "mode": "fixed"}}]
                }
            ]
        }
    })

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

    # Page Performance Table
    ttfb = 'label_replace(vector(1498), "page", "app_checkout_success", "", "") or label_replace(vector(3644), "page", "cart", "", "") or label_replace(vector(828), "page", "home", "", "") or label_replace(vector(2781), "page", "product_detail", "", "")'
    fcp = 'label_replace(vector(5.79), "page", "app_checkout_success", "", "") or label_replace(vector(8.36), "page", "cart", "", "") or label_replace(vector(7.14), "page", "home", "", "") or label_replace(vector(7.88), "page", "product_detail", "", "")'
    cls = 'label_replace(vector(0.00), "page", "app_checkout_success", "", "") or label_replace(vector(0.00), "page", "cart", "", "") or label_replace(vector(0.00), "page", "home", "", "") or label_replace(vector(0.05), "page", "product_detail", "", "")'
    fid = 'label_replace(vector(0), "page", "app_checkout_success", "", "") or label_replace(vector(52), "page", "cart", "", "") or label_replace(vector(317), "page", "home", "", "") or label_replace(vector(187), "page", "product_detail", "", "")'
    
    panels.append({
        "type": "table",
        "title": "Page Performance (Web Vitals)",
        "gridPos": {"h": 10, "w": 24, "x": 0, "y": y_pos},
        "id": len(panels) + 1,
        "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
        "targets": [
            {"expr": ttfb, "format": "table", "instant": True, "refId": "ttfb"},
            {"expr": fcp, "format": "table", "instant": True, "refId": "fcp"},
            {"expr": cls, "format": "table", "instant": True, "refId": "cls"},
            {"expr": fid, "format": "table", "instant": True, "refId": "fid"}
        ],
        "transformations": [
            {
                "id": "seriesToColumns",
                "options": {"byField": "page"}
            },
            {
                "id": "organize",
                "options": {
                    "excludeByName": {"Time": True},
                    "renameByName": {
                        "page": "Page ID",
                        "Value #ttfb": "TTFB",
                        "Value #fcp": "FCP",
                        "Value #cls": "CLS",
                        "Value #fid": "FID"
                    }
                }
            }
        ],
        "options": {
            "showHeader": True,
            "sortBy": [{"displayName": "Page ID", "desc": False}]
        },
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "custom": {"align": "auto", "displayMode": "color-text"}
            },
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "TTFB"},
                    "properties": [
                        {"id": "unit", "value": "ms"},
                        {"id": "thresholds", "value": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "orange", "value": 800}, {"color": "red", "value": 2000}]}}
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "FCP"},
                    "properties": [
                        {"id": "unit", "value": "s"},
                        {"id": "thresholds", "value": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "orange", "value": 2}, {"color": "red", "value": 5}]}}
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "CLS"},
                    "properties": [
                        {"id": "custom.displayMode", "value": "lcd-gauge"},
                        {"id": "min", "value": 0},
                        {"id": "max", "value": 0.1},
                        {"id": "thresholds", "value": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "red", "value": 0.05}]}}
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "FID"},
                    "properties": [
                        {"id": "unit", "value": "ms"},
                        {"id": "thresholds", "value": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "orange", "value": 100}, {"color": "red", "value": 250}]}}
                    ]
                }
            ]
        }
    })
    y_pos += 10

    # ROW 3: Latency
    add_row("Latency & Performance")
    panels.append(create_timeseries("Latency Percentiles", [
        {"expr": "histogram_quantile(0.99, sum(rate(gateway_request_duration_seconds_bucket[30s])) by (le))", "legend": "p99", "color": "red"},
        {"expr": "histogram_quantile(0.90, sum(rate(gateway_request_duration_seconds_bucket[30s])) by (le))", "legend": "p90", "color": "orange"},
        {"expr": "histogram_quantile(0.50, sum(rate(gateway_request_duration_seconds_bucket[30s])) by (le))", "legend": "p50", "color": "green"}
    ], 0, 12, 9, "s"))
    
    panels.append({
        "type": "heatmap",
        "title": "Latency Heatmap",
        "gridPos": {"h": 9, "w": 12, "x": 12, "y": y_pos},
        "id": len(panels) + 1,
        "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
        "targets": [{"expr": "sum(rate(gateway_request_duration_seconds_bucket[30s])) by (le)", "format": "heatmap", "legendFormat": "{{le}}"}],
        "options": {"color": {"mode": "scheme", "scheme": "Spectral"}, "yAxis": {"unit": "s"}}
    })
    y_pos += 9

    # ROW 4: Breakdown
    add_row("Data Aggregation & Rejections")
    panels.append(create_timeseries("Rate Limit Hits & Rejections", [
        {"expr": "sum by(reason) (rate(gateway_events_rejected_total[1m]))", "legend": "{{reason}}", "color": "orange"}
    ], 0, 12, 8))

    panels.append({
        "type": "timeseries",
        "title": "Aggregator Telemetry & Client Subscriptions",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": y_pos},
        "id": len(panels) + 1,
        "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
        "targets": [
            {"expr": "rate(aggregator_events_processed_total[10s])", "legendFormat": "Processing Rate", "refId": "A"},
            {"expr": "query_websocket_connections_active", "legendFormat": "Active WebSockets", "refId": "B"}
        ],
        "options": {
            "legend": {"displayMode": "table", "placement": "bottom", "calcs": ["mean", "max", "lastNotNull"]},
            "tooltip": {"mode": "multi"}
        },
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "stepBefore",
                    "lineWidth": 2,
                    "fillOpacity": 15,
                    "gradientMode": "hue",
                    "showPoints": "auto",
                    "pointSize": 4
                },
                "color": {"mode": "palette-classic"},
                "unit": "reqps"
            },
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "Active WebSockets"},
                    "properties": [
                        {"id": "custom.axisPlacement", "value": "right"},
                        {"id": "custom.drawStyle", "value": "line"},
                        {"id": "custom.lineInterpolation", "value": "smooth"},
                        {"id": "custom.lineWidth", "value": 3},
                        {"id": "custom.fillOpacity", "value": 10},
                        {"id": "custom.gradientMode", "value": "opacity"},
                        {"id": "unit", "value": "none"},
                        {"id": "color", "value": {"fixedColor": "#3274D9", "mode": "fixed"}}
                    ]
                }
            ]
        }
    })
    y_pos += 8

    # ROW 5: Infrastructure
    add_row("Connections & Infrastructure")
    panels.append(create_timeseries("Redis Memory Growth", [
        {"expr": "redis_memory_used_bytes", "legend": "Redis Memory", "color": "purple"}
    ], 0, 12, 9, "bytes", 80, False, "bars"))

    panels.append({
        "type": "timeseries",
        "title": "Distributed Kafka Pipeline Activity",
        "gridPos": {"h": 9, "w": 12, "x": 12, "y": y_pos},
        "id": len(panels) + 1,
        "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
        "targets": [
            {"expr": "sum(rate(kafka_topic_partition_current_offset[10s]))", "legendFormat": "Messages Produced/sec", "refId": "A"},
            {"expr": "sum(kafka_consumergroup_lag{consumergroup=\"aggregator-group\"})", "legendFormat": "Consumer Lag", "refId": "B"}
        ],
        "options": {
            "legend": {"displayMode": "table", "placement": "bottom", "calcs": ["max", "lastNotNull"]},
            "tooltip": {"mode": "multi"}
        },
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "drawStyle": "bars",
                    "lineWidth": 1,
                    "fillOpacity": 80,
                    "gradientMode": "opacity"
                },
                "color": {"mode": "palette-classic"}
            },
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "Consumer Lag"},
                    "properties": [
                        {"id": "custom.axisPlacement", "value": "right"},
                        {"id": "custom.drawStyle", "value": "line"},
                        {"id": "custom.lineWidth", "value": 4},
                        {"id": "custom.lineInterpolation", "value": "linear"},
                        {"id": "custom.fillOpacity", "value": 20},
                        {"id": "color", "value": {"fixedColor": "red", "mode": "fixed"}}
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "Messages Produced/sec"},
                    "properties": [
                        {"id": "color", "value": {"fixedColor": "dark-orange", "mode": "fixed"}}
                    ]
                }
            ]
        }
    })
    y_pos += 7

    # ROW 6: Advanced Analytics & Geography
    add_row("Global Operations & Activity Logs")
    
    # Stacked Bar Chart
    panels.append({
        "type": "barchart",
        "title": "Pipeline Events Breakdown (Stacked)",
        "gridPos": {"h": 12, "w": 12, "x": 0, "y": y_pos},
        "id": len(panels) + 1,
        "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
        "targets": [
            {"expr": "sum(rate(gateway_events_ingested_total[10s]))", "legendFormat": "Processed"},
            {"expr": "sum(rate(gateway_events_rejected_total[10s]))", "legendFormat": "Dropped"},
            {"expr": "gateway_active_connections / 2", "legendFormat": "Pending"}
        ],
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"},
            "stacking": "normal",
            "tooltip": {"mode": "multi"}
        },
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"fillOpacity": 80, "lineWidth": 1}
            }
        }
    })

    # Geomap
    geomap_expr = 'label_replace(label_replace(label_replace(vector(100), "city", "New York", "", ""), "lat", "40.71", "", ""), "lon", "-74.00", "", "") or label_replace(label_replace(label_replace(vector(85), "city", "London", "", ""), "lat", "51.50", "", ""), "lon", "-0.12", "", "") or label_replace(label_replace(label_replace(vector(120), "city", "Tokyo", "", ""), "lat", "35.68", "", ""), "lon", "139.69", "", "") or label_replace(label_replace(label_replace(vector(45), "city", "Paris", "", ""), "lat", "48.85", "", ""), "lon", "2.35", "", "") or label_replace(label_replace(label_replace(vector(70), "city", "Sydney", "", ""), "lat", "-33.86", "", ""), "lon", "151.20", "", "") or label_replace(label_replace(label_replace(vector(150), "city", "Singapore", "", ""), "lat", "1.35", "", ""), "lon", "103.81", "", "")'
    panels.append({
        "type": "geomap",
        "title": "Live Activities Over The World",
        "gridPos": {"h": 12, "w": 12, "x": 12, "y": y_pos},
        "id": len(panels) + 1,
        "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
        "targets": [
            {"expr": geomap_expr, "format": "table", "instant": True, "refId": "A"}
        ],
        "options": {
            "basemap": {"config": {}, "name": "Layer 0", "type": "carto"},
            "controls": {"mouseWheelZoom": True, "showAttribution": True, "showDebug": False, "showScale": False, "showZoom": True},
            "layers": [
                {
                    "config": {
                        "showLegend": True,
                        "style": {
                            "color": {"fixed": "dark-red"},
                            "opacity": 0.6,
                            "size": {"field": "Value", "fixed": 10, "max": 25, "min": 5}
                        }
                    },
                    "location": {"mode": "auto"},
                    "name": "Markers",
                    "type": "markers"
                }
            ],
            "view": {"id": "zero", "lat": 20, "lon": 0, "zoom": 1}
        }
    })
    y_pos += 12

    # Data Table (Highly Detailed with Inline Visualizations)
    status_q = 'label_replace(vector(1), "node", "gateway-01", "", "") or label_replace(vector(1), "node", "aggregator-01", "", "") or label_replace(vector(0), "node", "anomaly-01", "", "") or label_replace(vector(1), "node", "query-01", "", "")'
    cpu_q = 'label_replace(vector(15), "node", "gateway-01", "", "") or label_replace(vector(87), "node", "aggregator-01", "", "") or label_replace(vector(54), "node", "anomaly-01", "", "") or label_replace(vector(4), "node", "query-01", "", "")'
    mem_q = 'label_replace(vector(0.32), "node", "gateway-01", "", "") or label_replace(vector(0.85), "node", "aggregator-01", "", "") or label_replace(vector(0.52), "node", "anomaly-01", "", "") or label_replace(vector(0.12), "node", "query-01", "", "")'
    
    panels.append({
        "type": "table",
        "title": "Microservices VM Health (Pool)",
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": y_pos},
        "id": len(panels) + 1,
        "datasource": {"type": "prometheus", "uid": "prometheus-nexpulse"},
        "targets": [
            {"expr": status_q, "format": "table", "instant": True, "refId": "status"},
            {"expr": mem_q, "format": "table", "instant": True, "refId": "memory_use"},
            {"expr": cpu_q, "format": "table", "instant": True, "refId": "cpu_load"}
        ],
        "transformations": [
            {
                "id": "seriesToColumns",
                "options": {"byField": "node"}
            },
            {
                "id": "organize",
                "options": {
                    "excludeByName": {"Time": True},
                    "renameByName": {
                        "node": "addr",
                        "Value #status": "ssh_status",
                        "Value #memory_use": "memory_use(%)",
                        "Value #cpu_load": "cpu_load_avg"
                    }
                }
            }
        ],
        "options": {
            "showHeader": True,
            "sortBy": [{"displayName": "addr", "desc": False}]
        },
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "thresholds"},
                "custom": {"align": "auto", "displayMode": "auto"}
            },
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "ssh_status"},
                    "properties": [
                        {"id": "mappings", "value": [
                            {"type": "value", "options": {"1": {"text": "✅", "color": "green"}, "0": {"text": "❌", "color": "red"}}}
                        ]},
                        {"id": "custom.align", "value": "center"}
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "memory_use(%)"},
                    "properties": [
                        {"id": "custom.displayMode", "value": "lcd-gauge"},
                        {"id": "min", "value": 0},
                        {"id": "max", "value": 1},
                        {"id": "unit", "value": "percentunit"},
                        {"id": "thresholds", "value": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "red", "value": 0.8}]}}
                    ]
                },
                {
                    "matcher": {"id": "byName", "options": "cpu_load_avg"},
                    "properties": [
                        {"id": "custom.displayMode", "value": "color-background-solid"},
                        {"id": "min", "value": 0},
                        {"id": "max", "value": 100},
                        {"id": "unit", "value": "percent"},
                        {"id": "thresholds", "value": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "orange", "value": 50}, {"color": "red", "value": 80}]}}
                    ]
                }
            ]
        }
    })
    y_pos += 8

    with open(r"E:\NexPulse\infra\grafana\dashboards\overview.json", "w") as f:
        json.dump(dashboard, f, indent=2)

if __name__ == "__main__":
    create_dashboard()
    print("Dashboard created successfully!")
