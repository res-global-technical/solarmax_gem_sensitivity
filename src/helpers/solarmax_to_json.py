import csv
import json
import os

cwd = os.getcwd()
wd = os.path.abspath(os.path.join(cwd, os.pardir))
new_cwd = os.path.abspath(os.path.join(wd, os.pardir))

os.chdir(new_cwd)

print(f"Current working directory: {os.getcwd()}")
# File paths

projects = [5342, 5031, 30655, 5416]
solarmax_runs = ['01jp2b3a4ww1fhvpm8eavx87hv', '01jp2c4jj3a16e2yav00ctxwqk', '01jp28vg7a4xktdqm8w7x32m0t', '01jp2g3y946329wvjgk5p8pzm7']
gem_runs = ['01jp88a66vye03najah01qqp4z', '01jp88bsdg4kysnpczetdskvbb', '01jns7fm1cvrwp4zsy4bxxh6qe', '01jk8crcgzcsgk2kqs7p1acvgg']

csv_path = r'designs'
json_file = r'designs\design_options.json'



# Initialize the JSON structure
design_output = {"project_assessments": [{}],
                 "designs": {str(project_id): [] for project_id in projects}}

for project_id, solarmax_run, gem_run in zip(projects, solarmax_runs, gem_runs):
    design_output["project_assessments"].append({
        "project_id": project_id,
        "assessment_id": gem_run
    })

    csv_file = f"{csv_path}\\{solarmax_run}.csv"
# Read the CSV file and populate the designs
    try:
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
                design_output["designs"][str(project_id)].append(design)
    except:
        print(f"Error reading file: {csv_file}. Please ensure the file exists and is formatted correctly.")
        continue

# Write the JSON file
with open(json_file, 'w') as f:
    json.dump(design_output, f, indent=4)

print(f"Design JSON file created at {json_file}.")