# impacts.py
# Units:
# - co2_kg_per_kg: kg CO2e per kg of material
# - water_l_per_kg: liters per kg (optional; you can include more dimensions)

MATERIAL_IMPACT = {
    "cotton":              {"co2_kg_per_kg": 15.0, "water_l_per_kg": 2700},
    "recycled_cotton":     {"co2_kg_per_kg": 8.0,  "water_l_per_kg": 500},
    "polyester":           {"co2_kg_per_kg": 10.0, "water_l_per_kg": 25},
    "recycled_polyester":  {"co2_kg_per_kg": 6.0,  "water_l_per_kg": 20},
    "wool":                {"co2_kg_per_kg": 25.0, "water_l_per_kg": 1500},
    "elastane":            {"co2_kg_per_kg": 20.0, "water_l_per_kg": 100},
    "nylon":               {"co2_kg_per_kg": 15.0, "water_l_per_kg": 30},
    "linen":               {"co2_kg_per_kg": 8.0,  "water_l_per_kg": 650},
    # add more as needed
}
