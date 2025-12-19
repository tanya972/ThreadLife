# Material Recommendation System - Data Requirements

## Overview
To build a system that recommends the most suitable material changes for a specific item from a specific brand, you'll need the following data and functionality.

## Current Model Capabilities

### What the Model Already Uses
Based on `training_report.json` and `feature_importances.csv`:

**Most Important Features (77% importance):**
- `mat_score` - Material quality/durability score (0.4-1.2)

**Secondary Features (15% importance):**
- `category` - Product type (tshirt, sweater, jacket, dress, trousers, etc.)

**Other Features (8% importance):**
- `product_group_name` - Product group (Garments, Accessories, etc.)
- `graphical_appearance_name` - Design pattern (Solid, Stripe, All over pattern, etc.)
- `colour_group_name` - Color (White, Black, Blue, etc.)
- `perceived_colour_value_name` - Color tone (Light, Dark, Medium, etc.)
- `index_group_name` - Target market (Ladieswear, Menswear, Divided, etc.)
- `gap_months` - Purchase gap proxy
- `median_gap_days` - Transaction timing data

## Required Data for Brand-Specific Recommendations

### 1. **Current Product Information** (Minimum Required)

For each item you want to recommend improvements for:

```python
{
    # Required
    "category": "tshirt",  # or "sweater", "jacket", "dress", "trousers"
    "current_materials": {
        "cotton": 0.5,      # 0.0 to 1.0
        "polyester": 0.5,
        "wool": 0.0,
        "elastane": 0.0,
        # ... other materials
    },
    
    # Highly Recommended
    "product_group_name": "Garments",
    "graphical_appearance_name": "Solid",
    "colour_group_name": "White",
    "perceived_colour_value_name": "Light",
    "index_group_name": "Ladieswear",
    
    # Optional but helpful
    "price": 24.99,  # USD or EUR
    "brand": "H&M",  # Brand name (for tracking, not used in model)
    "product_id": "12345",  # Unique identifier
    "product_name": "Basic T-Shirt",  # Human-readable name
}
```

### 2. **Material Alternatives Database**

You already have this in `impacts.py`, but you may want to expand it:

```python
MATERIAL_ALTERNATIVES = {
    "cotton": {
        "better_options": ["recycled_cotton"],  # Lower environmental impact
        "similar_options": ["linen", "hemp"],   # Similar feel/durability
        "upgrade_options": ["organic_cotton"],  # Premium version
    },
    "polyester": {
        "better_options": ["recycled_polyester"],  # Lower CO2
        "natural_alternatives": ["cotton", "linen"],
    },
    # ... etc
}
```

### 3. **Brand/Product Constraints** (Optional but Recommended)

To make recommendations more realistic:

```python
{
    "brand_constraints": {
        "price_range": (10.0, 50.0),  # Brand's typical price range
        "preferred_materials": ["cotton", "polyester"],  # What brand typically uses
        "avoid_materials": ["wool"],  # Materials brand avoids
        "sustainability_goals": "reduce_co2",  # "reduce_co2", "reduce_water", "increase_lifespan"
    },
    "product_constraints": {
        "must_maintain": ["stretch"],  # Features that must be preserved
        "category_requirements": {
            "tshirt": {"max_weight": 0.2},  # kg - for material weight limits
        }
    }
}
```

### 4. **Target Metrics** (What to Optimize For)

```python
OPTIMIZATION_GOALS = {
    "lifespan_only": {
        "weight_lifespan": 1.0,
        "weight_co2": 0.0,
        "weight_water": 0.0,
        "weight_cost": 0.0,
    },
    "sustainability": {
        "weight_lifespan": 0.3,
        "weight_co2": 0.4,
        "weight_water": 0.3,
        "weight_cost": 0.0,
    },
    "balanced": {
        "weight_lifespan": 0.4,
        "weight_co2": 0.2,
        "weight_water": 0.2,
        "weight_cost": 0.2,
    }
}
```

## Implementation Approach

### Step 1: Create Recommendation Function

```python
def recommend_material_changes(
    current_item: dict,
    optimization_goal: str = "balanced",
    max_recommendations: int = 5,
    constraints: dict = None
) -> list:
    """
    Returns ranked list of material change recommendations.
    
    Returns:
        [
            {
                "recommendation_id": 1,
                "new_composition": {"cotton": 0.8, "recycled_cotton": 0.2, ...},
                "predicted_lifespan_months": 48.5,
                "lifespan_improvement": +3.2,  # months
                "co2_impact_kg": 2.1,
                "co2_reduction": -0.4,  # kg
                "water_impact_l": 600,
                "water_reduction": -200,  # liters
                "cost_change": +2.50,  # USD (if material costs available)
                "overall_score": 8.5,  # weighted score
                "change_description": "Replace 20% cotton with recycled cotton",
                "feasibility": "high",  # high, medium, low
            },
            ...
        ]
    """
    pass
```

### Step 2: Material Change Generation

Generate candidate material compositions:

1. **Incremental Changes** (conservative)
   - Swap 10-30% of one material for a better alternative
   - Example: 50% cotton → 70% cotton (add 20% recycled cotton)

2. **Blend Improvements** (moderate)
   - Add small amounts of durability materials
   - Example: Add 5-10% wool to polyester blend

3. **Major Swaps** (aggressive)
   - Replace entire material categories
   - Example: 100% polyester → 100% cotton

4. **Category-Specific Rules**
   - Sweaters: wool blends increase lifespan significantly
   - T-shirts: recycled cotton reduces impact without losing durability
   - Activewear: need elastane, but can use recycled polyester

### Step 3: Scoring & Ranking

For each candidate composition:

1. **Predict lifespan** using the trained model
2. **Calculate environmental impact** (CO2, water) using `impacts.py`
3. **Calculate cost change** (if material cost data available)
4. **Apply constraints** (brand preferences, product requirements)
5. **Score** using weighted optimization goal
6. **Rank** by overall score

### Step 4: Feasibility Check

Filter/rank by:
- **Technical feasibility**: Can the materials be blended this way?
- **Brand alignment**: Does it fit brand's style/market?
- **Cost constraints**: Within price range?
- **Supply chain**: Are materials available?

## Data You'll Need to Collect

### If Building from Scratch:

1. **Product Catalog** (CSV/JSON/Database)
   ```
   product_id, brand, category, current_materials_json, price, ...
   ```

2. **Material Database** (extend `impacts.py`)
   - Material properties (durability, cost, availability)
   - Compatibility matrix (which materials work well together)
   - Environmental impact data (CO2, water, waste)

3. **Brand Preferences** (CSV/JSON)
   ```
   brand, preferred_materials, price_range_min, price_range_max, sustainability_focus, ...
   ```

4. **Material Costs** (Optional but Recommended)
   ```
   material, cost_per_kg_usd, availability, region, ...
   ```

### If Using Existing H&M Data:

You can extract from your current datasets:

```python
# From articles.csv - if it has brand/product info
# From hm_train_ready.csv - product attributes
# From transactions_train.csv - sales patterns (for demand forecasting)
```

## Example Workflow

```python
# 1. Load current item data
item = {
    "brand": "H&M",
    "product_id": "12345",
    "category": "tshirt",
    "current_materials": {"cotton": 0.5, "polyester": 0.5},
    "price": 24.99,
    "product_group_name": "Garments",
    "graphical_appearance_name": "Solid",
    "colour_group_name": "White",
}

# 2. Get recommendations
recommendations = recommend_material_changes(
    current_item=item,
    optimization_goal="sustainability",
    max_recommendations=5,
    constraints={
        "max_price_increase": 5.00,  # Don't increase cost by more than $5
        "min_lifespan_improvement": 2.0,  # At least 2 months improvement
    }
)

# 3. Display top recommendation
top_rec = recommendations[0]
print(f"Best change: {top_rec['change_description']}")
print(f"Lifespan: {top_rec['predicted_lifespan_months']:.1f} months (+{top_rec['lifespan_improvement']:.1f})")
print(f"CO2 reduction: {top_rec['co2_reduction']:.2f} kg")
```

## Next Steps

1. **Decide on data source**:
   - Do you have a product catalog with current materials?
   - Do you need to extract from existing H&M data?
   - Do you need to manually input item data?

2. **Define optimization priorities**:
   - What's most important: lifespan, sustainability, cost, or balanced?

3. **Set up recommendation engine**:
   - Create the Python function to generate and score material alternatives
   - Integrate with your existing model (`predict_safe.py`)

4. **Build UI integration**:
   - Add to React app: input form for item details
   - Display ranked recommendations
   - Show comparison charts (current vs. recommended)

5. **Add constraints** (optional):
   - Brand-specific rules
   - Material compatibility matrix
   - Cost constraints

Would you like me to:
- Create the recommendation function code?
- Build a data collection form/script?
- Integrate this into the React app?
- Set up a brand/product database structure?





