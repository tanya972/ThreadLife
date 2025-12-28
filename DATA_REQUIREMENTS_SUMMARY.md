# Quick Reference: Data Needed for Material Recommendations

## What You Need (Minimum)

For each product you want to get recommendations for, provide:

### ✅ Required Fields
1. **Category**: `"tshirt"`, `"sweater"`, `"jacket"`, `"dress"`, `"trousers"`, etc.
2. **Current Material Composition** (percentages that add up to 100%):
   - `cotton`: 0.0 to 1.0
   - `polyester`: 0.0 to 1.0  
   - `wool`: 0.0 to 1.0
   - `elastane`: 0.0 to 1.0
   - (and any other materials)

### ✅ Recommended Fields (for better accuracy)
3. **Product Attributes**:
   - `product_group_name`: e.g., "Garments"
   - `graphical_appearance_name`: e.g., "Solid", "Stripe"
   - `colour_group_name`: e.g., "White", "Black"
   - `index_group_name`: e.g., "Ladieswear", "Menswear"

### ✅ Optional Fields (for brand-specific recommendations)
4. **Brand Information**:
   - `brand`: Brand name (e.g., "H&M", "Zara")
   - `product_id`: Unique product identifier
   - `price`: Current price in USD/EUR
   - `brand_constraints`: Price limits, preferred materials, etc.

## Example Input

```json
{
  "brand": "H&M",
  "product_id": "BASIC_TSHIRT_001",
  "category": "tshirt",
  "current_materials": {
    "cotton": 0.5,
    "polyester": 0.5,
    "wool": 0.0,
    "elastane": 0.0
  },
  "product_group_name": "Garments",
  "graphical_appearance_name": "Solid",
  "colour_group_name": "White",
  "index_group_name": "Ladieswear",
  "price": 24.99
}
```

## What You'll Get Back

```json
{
  "recommendations": [
    {
      "rank": 1,
      "new_materials": {
        "cotton": 0.3,
        "recycled_cotton": 0.7,
        "polyester": 0.0
      },
      "predicted_lifespan_months": 48.5,
      "lifespan_improvement": "+3.2 months",
      "co2_reduction": "-0.4 kg",
      "water_reduction": "-200 liters",
      "reason": "Replacing cotton with recycled cotton reduces environmental impact by 80% while maintaining durability"
    },
    {
      "rank": 2,
      "new_materials": {
        "cotton": 0.8,
        "polyester": 0.2
      },
      "predicted_lifespan_months": 46.0,
      "lifespan_improvement": "+1.5 months",
      "co2_reduction": "+0.5 kg",
      "reason": "Higher cotton content improves durability and perceived quality"
    }
  ]
}
```

## Where to Get This Data

### Option 1: From Your Existing H&M Data
If you have product catalogs, extract:
- Material composition from product descriptions
- Category from product type
- Attributes from existing data files

### Option 2: Manual Input
Create a form where users can input:
- Product category (dropdown)
- Material percentages (sliders)
- Product attributes (dropdowns)

### Option 3: API/Product Database
If you have access to brand product databases, query:
- Product ID → Get all attributes
- Material composition → Parse from product specs

## Next Steps

1. **Do you have product data already?**
   - ✅ Yes → I'll help you create a script to extract and format it
   - ❌ No → I'll help you build an input form

2. **What's your optimization goal?**
   - Maximize lifespan?
   - Reduce environmental impact (CO2/water)?
   - Balance both?
   - Minimize cost?

3. **Do you want brand-specific constraints?**
   - Price limits?
   - Material preferences?
   - Supply chain considerations?

Let me know and I'll help you implement the recommendation system!





