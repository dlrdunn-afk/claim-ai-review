import csv
import os

input_csv = "out/estimate_xact_final.csv"
output_html = "out/estimate_preview.html"

def mm_to_ft_in(mm_str):
    try:
        mm = float(mm_str)
        inches_total = mm / 25.4
        feet = int(inches_total // 12)
        inches = round(inches_total % 12)
        return f"{feet}′ {inches}″"
    except:
        return mm_str  # Return original if conversion fails

# Read the CSV
with open(input_csv, newline='') as f:
    reader = csv.reader(f)
    rows = list(reader)

headers = rows[0]
data = rows[1:]

# Identify the index of "Ceiling Height (mm)"
ceiling_index = None
for i, h in enumerate(headers):
    if "Ceiling Height" in h:
        ceiling_index = i
        headers[i] = "Ceiling Height (ft/in)"  # Update column title
        break

# Convert values
for row in data:
    if ceiling_index is not None and len(row) > ceiling_index:
        row[ceiling_index] = mm_to_ft_in(row[ceiling_index])

# Create HTML
html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Estimate Preview</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ text-align: center; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 30px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
    </style>
</head>
<body>
    <h1>Insurance Estimate Preview</h1>
    <table>
        <tr>
            {''.join(f'<th>{col}</th>' for col in headers)}
        </tr>
        {''.join(f"<tr>{''.join(f'<td>{cell}</td>' for cell in row)}</tr>" for row in data)}
    </table>
</body>
</html>
"""

# Write the HTML
os.makedirs("out", exist_ok=True)
with open(output_html, "w") as f:
    f.write(html)

print(f"✅ Estimate preview saved to: {output_html}")
