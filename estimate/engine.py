import csv

# === Dummy Room Data (stand-in for iGUIDE parsing) ===
rooms = [
    {
        "name": "Kitchen",
        "area_sf": 180,
        "perimeter_lf": 82,
        "height_ft": 9,
        "openings_sf": 26,
        "door_widths_lf": 9,
    },
    {
        "name": "Living Room",
        "area_sf": 370,
        "perimeter_lf": 100,
        "height_ft": 9,
        "openings_sf": 30,
        "door_widths_lf": 12,
    },
]


# === Quantity Calculation Functions ===
def paint_walls_sf(perimeter_lf, height_ft, openings_sf):
    return max((perimeter_lf * height_ft) - openings_sf, 0.0)


def baseboard_lf(perimeter_lf, door_widths_lf):
    return max(perimeter_lf - door_widths_lf, 0.0)


# === Build Estimate Rows ===
rows = []

# Paint walls in every room
for r in rooms:
    sf = round(paint_walls_sf(r["perimeter_lf"], r["height_ft"], r["openings_sf"]), 1)
    rows.append(
        {
            "Group": r["name"],
            "Item Code": "PAINT-WALLS",
            "Qty": sf,
            "Unit": "sf",
            "Notes": "Walls paint per room",
        }
    )

# Baseboard damage in Living Room only
lr = rooms[1]  # index 1 = Living Room
lf = round(baseboard_lf(lr["perimeter_lf"], lr["door_widths_lf"]), 1)
rows.append(
    {
        "Group": "Living Room",
        "Item Code": "BASEBOARD-RR",
        "Qty": lf,
        "Unit": "lf",
        "Notes": "Detected baseboard damage",
    }
)

# Ceiling water stain in Kitchen (no AI mask yet, just use fallback minimum)
rows.append(
    {
        "Group": "Kitchen",
        "Item Code": "DW-PATCH",
        "Qty": 4,
        "Unit": "sf",
        "Notes": "Ceiling water stain – estimated minimum",
    }
)
rows.append(
    {
        "Group": "Kitchen",
        "Item Code": "PRIME-PAINT",
        "Qty": 4,
        "Unit": "sf",
        "Notes": "Prime and paint patched area",
    }
)

# === Write CSV Output ===
with open("out/estimate_xact.csv", "w", newline="") as f:
    writer = csv.DictWriter(
        f, fieldnames=["Group", "Item Code", "Qty", "Unit", "Notes"]
    )
    writer.writeheader()
    writer.writerows(rows)

print("✅ Estimate created: out/estimate_xact.csv")
