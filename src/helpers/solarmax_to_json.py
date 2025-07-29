import csv
import json

# File paths
csv_file = r'C:\Users\JNewton\Documents\GitHub\portfolio-sensitivity-prototype\designs\01jp2dyccrpvxb8fypqbdpphnr.csv'
json_file = r'C:\Users\JNewton\Documents\GitHub\portfolio-sensitivity-prototype\designs\design_options_wolf_tail.json'

# Initialize the JSON structure
design_output = {
    "project_assessments": [
        {
            "project_id": 22684,
            "assessment_id": "01jp2dyccrpvxb8fypqbdpphnr"
        }
    ],
    "designs": {
        "22684": []
    }
}

# Read the CSV file and populate the designs
with open(csv_file, 'r') as f:
    reader = csv.reader(f)
    for i, row in enumerate(reader, start=1):
        if i == 1:  # Skip the header row
            continue
        design = {
            "name": str(i),
            "installed_capacity_dc": float(row[4]),
            "land_area": float(row[12]) * 0.404686,
            "energy_yield": float(row[18])/1000
        }
        design_output["designs"]["22684"].append(design)

# Write the JSON file
with open(json_file, 'w') as f:
    json.dump(design_output, f, indent=4)

print(f"Design JSON file created at {json_file}.")