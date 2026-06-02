import random

cities = [
    # North America
    ("New York", 40.71, -74.00, 150),
    ("Los Angeles", 34.05, -118.24, 120),
    ("San Francisco", 37.77, -122.41, 140),
    ("Chicago", 41.87, -87.62, 90),
    ("Toronto", 43.65, -79.38, 85),
    ("Vancouver", 49.28, -123.12, 60),
    ("Mexico City", 19.43, -99.13, 110),
    ("Miami", 25.76, -80.19, 75),
    ("Dallas", 32.77, -96.79, 80),
    ("Seattle", 47.60, -122.33, 95),
    
    # Europe
    ("London", 51.50, -0.12, 160),
    ("Paris", 48.85, 2.35, 130),
    ("Berlin", 52.52, 13.40, 110),
    ("Madrid", 40.41, -3.70, 90),
    ("Rome", 41.90, 12.49, 80),
    ("Amsterdam", 52.36, 4.90, 140),
    ("Frankfurt", 50.11, 8.68, 180), # major hub
    ("Stockholm", 59.32, 18.06, 60),
    ("Moscow", 55.75, 37.61, 70),
    ("Dublin", 53.34, -6.26, 85),
    
    # Asia
    ("Tokyo", 35.68, 139.69, 170),
    ("Seoul", 37.56, 126.97, 130),
    ("Beijing", 39.90, 116.40, 150),
    ("Shanghai", 31.23, 121.47, 160),
    ("Hong Kong", 22.31, 114.16, 140),
    ("Mumbai", 19.07, 72.87, 120),
    ("Delhi", 28.70, 77.10, 110),
    ("Bangalore", 12.97, 77.59, 135),
    ("Singapore", 1.35, 103.81, 190),
    ("Bangkok", 13.75, 100.50, 90),
    ("Jakarta", -6.20, 106.81, 100),
    ("Dubai", 25.20, 55.27, 115),
    
    # South America
    ("Sao Paulo", -23.55, -46.63, 130),
    ("Buenos Aires", -34.60, -58.38, 80),
    ("Bogota", 4.71, -74.07, 70),
    ("Lima", -12.04, -77.02, 65),
    ("Santiago", -33.44, -70.66, 75),
    
    # Africa
    ("Lagos", 6.52, 3.37, 95),
    ("Cairo", 30.04, 31.23, 85),
    ("Johannesburg", -26.20, 28.04, 90),
    ("Nairobi", -1.29, 36.82, 60),
    ("Cape Town", -33.92, 18.42, 75),
    
    # Oceania
    ("Sydney", -33.86, 151.20, 110),
    ("Melbourne", -37.81, 144.96, 95),
    ("Auckland", -36.84, 174.76, 60),
    ("Brisbane", -27.46, 153.02, 50)
]

queries = []
for city, lat, lon, val in cities:
    # Add some randomness to value
    # We use vector({val})
    q = f'label_replace(label_replace(label_replace(vector({val}), "city", "{city}", "", ""), "lat", "{lat}", "", ""), "lon", "{lon}", "", "")'
    queries.append(q)

final_expr = " or ".join(queries)

# Now read generate_dashboard.py and replace the geomap_expr line
file_path = r"E:\NexPulse\infra\grafana\dashboards\generate_dashboard.py"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.strip().startswith("geomap_expr = "):
        # Keep indentation
        indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(f"{indent}geomap_expr = '{final_expr}'\n")
    else:
        new_lines.append(line)

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Injected fully populated map data!")
