#!/usr/bin/env python3
"""
Sustainable Material Recommendation System
-------------------------------------------
Suggests alternative materials that improve both durability and environmental impact.
Only run this AFTER validation confirms synthetic labels are meaningful.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import re
import joblib
import json

# Config
DATA_DIR = Path(r"C:\Users\tanya\clothing predictor\hm\data")
TRAIN_READY_CSV = DATA_DIR / "hm_train_ready.csv"
MODEL_PATH = Path(r"C:\Users\tanya\clothing predictor\hm\ml\model_comparison\best_model.joblib")
OUT_DIR = Path(r"C:\Users\tanya\clothing predictor\hm\ml\recommendations")

# Environmental Impact Database (kg CO2, liters water, recyclability 0-1)
MATERIAL_ENVIRONMENTAL_IMPACT = {
    'cotton': {
        'carbon_kg_co2': 5.9,
        'water_liters': 10000,
        'recyclability': 0.8,
        'biodegradable': True,
        'microplastic_shedding': False,
        'durability_base': 0.70
    },
    'organic_cotton': {
        'carbon_kg_co2': 3.5,
        'water_liters': 7000,
        'recyclability': 0.9,
        'biodegradable': True,
        'microplastic_shedding': False,
        'durability_base': 0.75
    },
    'polyester': {
        'carbon_kg_co2': 7.1,
        'water_liters': 2000,
        'recyclability': 0.3,
        'biodegradable': False,
        'microplastic_shedding': True,
        'durability_base': 0.50
    },
    'recycled_polyester': {
        'carbon_kg_co2': 3.2,
        'water_liters': 500,
        'recyclability': 0.6,
        'biodegradable': False,
        'microplastic_shedding': True,
        'durability_base': 0.55
    },
    'wool': {
        'carbon_kg_co2': 6.0,
        'water_liters': 8000,
        'recyclability': 0.7,
        'biodegradable': True,
        'microplastic_shedding': False,
        'durability_base': 0.85
    },
    'linen': {
        'carbon_kg_co2': 2.0,
        'water_liters': 3000,
        'recyclability': 0.9,
        'biodegradable': True,
        'microplastic_shedding': False,
        'durability_base': 0.80
    },
    'hemp': {
        'carbon_kg_co2': 1.8,
        'water_liters': 2500,
        'recyclability': 0.9,
        'biodegradable': True,
        'microplastic_shedding': False,
        'durability_base': 0.80
    },
    'viscose': {
        'carbon_kg_co2': 4.5,
        'water_liters': 6000,
        'recyclability': 0.4,
        'biodegradable': True,
        'microplastic_shedding': False,
        'durability_base': 0.55
    },
    'tencel': {  # Lyocell - sustainable viscose alternative
        'carbon_kg_co2': 3.0,
        'water_liters': 1500,
        'recyclability': 0.8,
        'biodegradable': True,
        'microplastic_shedding': False,
        'durability_base': 0.65
    },
    'nylon': {
        'carbon_kg_co2': 7.6,
        'water_liters': 2500,
        'recyclability': 0.3,
        'biodegradable': False,
        'microplastic_shedding': True,
        'durability_base': 0.60
    },
    'elastane': {
        'carbon_kg_co2': 8.0,
        'water_liters': 3000,
        'recyclability': 0.1,
        'biodegradable': False,
        'microplastic_shedding': True,
        'durability_base': 0.60
    },
    'silk': {
        'carbon_kg_co2': 5.5,
        'water_liters': 7000,
        'recyclability': 0.7,
        'biodegradable': True,
        'microplastic_shedding': False,
        'durability_base': 0.75
    },
    'leather': {
        'carbon_kg_co2': 17.0,
        'water_liters': 15000,
        'recyclability': 0.5,
        'biodegradable': True,
        'microplastic_shedding': False,
        'durability_base': 0.90
    }
}

# Material substitution rules (what can replace what, by category)
MATERIAL_SUBSTITUTIONS = {
    'polyester': {
        'activewear': ['recycled_polyester', 'tencel', 'hemp'],
        'dress': ['tencel', 'viscose', 'organic_cotton'],
        'jacket': ['recycled_polyester', 'wool'],
        'blouse': ['tencel', 'organic_cotton', 'silk'],
        't shirt': ['organic_cotton', 'hemp', 'tencel'],
        'default': ['recycled_polyester', 'tencel', 'organic_cotton']
    },
    'cotton': {
        't shirt': ['organic_cotton', 'hemp', 'tencel'],
        'jeans': ['organic_cotton', 'hemp'],
        'dress': ['linen', 'tencel', 'organic_cotton'],
        'blouse': ['organic_cotton', 'linen', 'tencel'],
        'sweater': ['organic_cotton', 'wool'],
        'default': ['organic_cotton', 'linen', 'hemp']
    },
    'viscose': {
        'dress': ['tencel', 'linen', 'organic_cotton'],
        'blouse': ['tencel', 'organic_cotton', 'silk'],
        'skirt': ['tencel', 'linen'],
        'default': ['tencel', 'organic_cotton']
    },
    'nylon': {
        'activewear': ['recycled_polyester', 'tencel'],
        'underwear': ['organic_cotton', 'tencel'],
        'tights': ['recycled_polyester'],
        'jacket': ['recycled_polyester', 'wool'],
        'default': ['recycled_polyester', 'tencel']
    }
}


def extract_primary_material(detail_desc):
    """Extract the primary material from product description"""
    if not isinstance(detail_desc, str):
        return 'cotton'  # Default
    
    desc = detail_desc.lower()
    
    # Check in order of specificity
    materials = [
        'organic_cotton', 'recycled_polyester', 'tencel', 
        'cotton', 'polyester', 'wool', 'linen', 'hemp', 
        'viscose', 'nylon', 'elastane', 'silk', 'leather'
    ]
    
    for mat in materials:
        mat_pattern = mat.replace('_', ' ')
        if mat_pattern in desc or mat in desc:
            return mat
    
    return 'cotton'  # Default fallback


def get_alternative_materials(current_material, category):
    """Get viable material alternatives based on category"""
    current_material = current_material.lower()
    category = category.lower() if isinstance(category, str) else ''
    
    if current_material not in MATERIAL_SUBSTITUTIONS:
        # If no specific substitutions, suggest generally sustainable materials
        return ['organic_cotton', 'tencel', 'hemp', 'linen']
    
    # Try category-specific first
    for cat_key, alternatives in MATERIAL_SUBSTITUTIONS[current_material].items():
        if cat_key in category:
            return alternatives
    
    # Fall back to default
    return MATERIAL_SUBSTITUTIONS[current_material].get('default', ['organic_cotton', 'tencel'])


def calculate_environmental_score(material):
    """Calculate composite environmental impact score (0-100, higher = better)"""
    if material not in MATERIAL_ENVIRONMENTAL_IMPACT:
        material = 'cotton'
    
    impact = MATERIAL_ENVIRONMENTAL_IMPACT[material]
    
    # Normalize scores (lower carbon/water = better)
    # Using rough max values for normalization
    carbon_score = max(0, (20 - impact['carbon_kg_co2']) / 20) * 100
    water_score = max(0, (20000 - impact['water_liters']) / 20000) * 100
    recyclability_score = impact['recyclability'] * 100
    biodegradable_score = 100 if impact['biodegradable'] else 0
    microplastic_score = 100 if not impact['microplastic_shedding'] else 0
    
    # Weighted composite
    composite = (
        0.30 * carbon_score +
        0.25 * water_score +
        0.20 * recyclability_score +
        0.15 * biodegradable_score +
        0.10 * microplastic_score
    )
    
    return {
        'composite': composite,
        'carbon': impact['carbon_kg_co2'],
        'water': impact['water_liters'],
        'recyclability': impact['recyclability'],
        'biodegradable': impact['biodegradable'],
        'microplastic_free': not impact['microplastic_shedding']
    }


def predict_with_new_material(article_row, new_material, model):
    """Predict lifespan if article was made with different material"""
    # Create copy of article with new material
    modified_row = article_row.copy()
    
    # Update material score based on new material
    if new_material in MATERIAL_ENVIRONMENTAL_IMPACT:
        modified_row['mat_score'] = MATERIAL_ENVIRONMENTAL_IMPACT[new_material]['durability_base']
    
    # Prepare features for prediction
    feature_cols = ['category', 'product_group_name', 'graphical_appearance_name',
                   'colour_group_name', 'perceived_colour_value_name', 'index_group_name',
                   'price', 'mat_score', 'price_decay']
    
    # Ensure all features exist
    features = {}
    for col in feature_cols:
        if col in modified_row:
            features[col] = modified_row[col]
        else:
            features[col] = np.nan
    
    # Convert to DataFrame for prediction
    X = pd.DataFrame([features])
    
    # Predict
    try:
        prediction = model.predict(X)[0]
    except:
        # If prediction fails, use simple adjustment
        prediction = article_row.get('lifespan_months', 50) * (modified_row['mat_score'] / article_row.get('mat_score', 0.65))
    
    return prediction


def recommend_sustainable_alternatives(article_row, model, top_n=3):
    """
    Recommend material alternatives that improve durability and sustainability
    """
    # Get current state
    current_material = extract_primary_material(article_row['detail_desc'])
    current_lifespan = article_row['lifespan_months']
    current_env = calculate_environmental_score(current_material)
    
    # Get viable alternatives
    alternatives = get_alternative_materials(current_material, article_row.get('category', ''))
    
    # Remove current material from alternatives
    alternatives = [alt for alt in alternatives if alt != current_material]
    
    recommendations = []
    
    for alt_material in alternatives:
        # Predict new lifespan
        new_lifespan = predict_with_new_material(article_row, alt_material, model)
        
        # Calculate environmental impact
        new_env = calculate_environmental_score(alt_material)
        
        # Calculate improvements
        lifespan_gain = new_lifespan - current_lifespan
        lifespan_gain_pct = (lifespan_gain / current_lifespan) * 100
        
        carbon_reduction = current_env['carbon'] - new_env['carbon']
        carbon_reduction_pct = (carbon_reduction / current_env['carbon']) * 100
        
        water_reduction = current_env['water'] - new_env['water']
        water_reduction_pct = (water_reduction / current_env['water']) * 100
        
        env_score_gain = new_env['composite'] - current_env['composite']
        
        # Combined score (weighted: 40% durability, 60% environment)
        combined_score = (
            0.40 * lifespan_gain_pct +
            0.60 * env_score_gain
        )
        
        recommendations.append({
            'material': alt_material,
            'current_lifespan': current_lifespan,
            'predicted_lifespan': new_lifespan,
            'lifespan_gain_months': lifespan_gain,
            'lifespan_gain_pct': lifespan_gain_pct,
            'current_carbon': current_env['carbon'],
            'new_carbon': new_env['carbon'],
            'carbon_reduction': carbon_reduction,
            'carbon_reduction_pct': carbon_reduction_pct,
            'current_water': current_env['water'],
            'new_water': new_env['water'],
            'water_reduction': water_reduction,
            'water_reduction_pct': water_reduction_pct,
            'current_env_score': current_env['composite'],
            'new_env_score': new_env['composite'],
            'combined_score': combined_score,
            'biodegradable': new_env['biodegradable'],
            'microplastic_free': new_env['microplastic_free'],
            'recyclability': new_env['recyclability']
        })
    
    # Sort by combined score
    recommendations.sort(key=lambda x: x['combined_score'], reverse=True)
    
    return recommendations[:top_n], current_material


def display_recommendations(article_id, recommendations, current_material):
    """Pretty print recommendations"""
    print("\n" + "="*80)
    print(f"SUSTAINABLE MATERIAL RECOMMENDATIONS")
    print(f"Article: {article_id} | Current Material: {current_material.upper().replace('_', ' ')}")
    print("="*80)
    
    if not recommendations:
        print("\n⚠ No alternative materials available for this product category")
        return
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{'🥇' if i == 1 else '🥈' if i == 2 else '🥉'} OPTION {i}: {rec['material'].upper().replace('_', ' ')}")
        print("-" * 80)
        
        print(f"  ✨ Durability Impact:")
        print(f"     Current lifespan:  {rec['current_lifespan']:.1f} months")
        print(f"     New lifespan:      {rec['predicted_lifespan']:.1f} months")
        if rec['lifespan_gain_months'] >= 0:
            print(f"     Improvement:       +{rec['lifespan_gain_months']:.1f} months ({rec['lifespan_gain_pct']:+.1f}%) ✓")
        else:
            print(f"     Change:            {rec['lifespan_gain_months']:.1f} months ({rec['lifespan_gain_pct']:+.1f}%)")
        
        print(f"\n  🌍 Environmental Impact:")
        print(f"     Carbon:            {rec['new_carbon']:.1f} kg CO2 ({rec['carbon_reduction_pct']:+.1f}%)")
        print(f"     Water:             {rec['new_water']:,.0f} liters ({rec['water_reduction_pct']:+.1f}%)")
        print(f"     Recyclability:     {rec['recyclability']*100:.0f}%")
        print(f"     Biodegradable:     {'✓ Yes' if rec['biodegradable'] else '✗ No'}")
        print(f"     Microplastic-free: {'✓ Yes' if rec['microplastic_free'] else '✗ No'}")
        
        print(f"\n  📊 Overall Score:     {rec['combined_score']:.2f}")
    
    print("\n" + "="*80)


def create_recommendation_visualization(article_id, recommendations, current_material, current_stats):
    """Create visual comparison of material alternatives"""
    if not recommendations:
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    materials = ['Current\n' + current_material.replace('_', ' ').title()] + \
                [rec['material'].replace('_', ' ').title() for rec in recommendations]
    
    # 1. Lifespan comparison
    lifespans = [current_stats['lifespan']] + [rec['predicted_lifespan'] for rec in recommendations]
    colors = ['red'] + ['green' if rec['lifespan_gain_months'] > 0 else 'orange' for rec in recommendations]
    
    axes[0, 0].barh(materials, lifespans, color=colors, alpha=0.7)
    axes[0, 0].set_xlabel('Predicted Lifespan (months)', fontsize=11)
    axes[0, 0].set_title('Durability Comparison', fontsize=12, fontweight='bold')
    axes[0, 0].invert_yaxis()
    axes[0, 0].grid(True, alpha=0.3, axis='x')
    
    # 2. Carbon footprint
    carbon = [current_stats['carbon']] + [rec['new_carbon'] for rec in recommendations]
    colors = ['red'] + ['green' if rec['carbon_reduction'] > 0 else 'orange' for rec in recommendations]
    
    axes[0, 1].barh(materials, carbon, color=colors, alpha=0.7)
    axes[0, 1].set_xlabel('Carbon Footprint (kg CO2/kg)', fontsize=11)
    axes[0, 1].set_title('Carbon Emissions (Lower is Better)', fontsize=12, fontweight='bold')
    axes[0, 1].invert_yaxis()
    axes[0, 1].grid(True, alpha=0.3, axis='x')
    
    # 3. Water usage
    water = [current_stats['water']] + [rec['new_water'] for rec in recommendations]
    colors = ['red'] + ['green' if rec['water_reduction'] > 0 else 'orange' for rec in recommendations]
    
    axes[1, 0].barh(materials, water, color=colors, alpha=0.7)
    axes[1, 0].set_xlabel('Water Usage (liters/kg)', fontsize=11)
    axes[1, 0].set_title('Water Consumption (Lower is Better)', fontsize=12, fontweight='bold')
    axes[1, 0].invert_yaxis()
    axes[1, 0].grid(True, alpha=0.3, axis='x')
    
    # 4. Scatter: Lifespan vs Environmental Score
    env_scores = [current_stats['env_score']] + [rec['new_env_score'] for rec in recommendations]
    
    axes[1, 1].scatter(lifespans[1:], env_scores[1:], s=200, alpha=0.6, c=range(len(recommendations)), cmap='viridis')
    axes[1, 1].scatter([lifespans[0]], [env_scores[0]], color='red', s=300, marker='*', label='Current', zorder=10)
    
    # Annotate points
    for i, mat in enumerate(materials[1:], 1):
        axes[1, 1].annotate(mat, (lifespans[i], env_scores[i]), fontsize=8, ha='right')
    
    axes[1, 1].set_xlabel('Predicted Lifespan (months)', fontsize=11)
    axes[1, 1].set_ylabel('Environmental Score (0-100)', fontsize=11)
    axes[1, 1].set_title('Durability vs Sustainability', fontsize=12, fontweight='bold')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    filename = OUT_DIR / f'recommendations_{article_id}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✓ Saved visualization: {filename}")
    plt.close()


def batch_analyze_dataset(df, model, sample_size=100):
    """Run recommendations on sample of dataset and summarize findings"""
    print(f"\nAnalyzing {sample_size} random articles...")
    
    sample = df.sample(min(sample_size, len(df)), random_state=42)
    
    all_recommendations = []
    material_counts = {}
    
    for idx, row in sample.iterrows():
        recs, current_mat = recommend_sustainable_alternatives(row, model, top_n=3)
        
        if recs:
            best_rec = recs[0]
            all_recommendations.append({
                'article_id': row['article_id'],
                'category': row.get('category', 'unknown'),
                'current_material': current_mat,
                'recommended_material': best_rec['material'],
                'lifespan_gain': best_rec['lifespan_gain_months'],
                'carbon_reduction_pct': best_rec['carbon_reduction_pct'],
                'water_reduction_pct': best_rec['water_reduction_pct'],
                'combined_score': best_rec['combined_score']
            })
            
            # Count recommendations
            rec_mat = best_rec['material']
            material_counts[rec_mat] = material_counts.get(rec_mat, 0) + 1
    
    # Summary statistics
    recs_df = pd.DataFrame(all_recommendations)
    
    print("\n" + "="*80)
    print("BATCH ANALYSIS SUMMARY")
    print("="*80)
    print(f"\nArticles analyzed: {len(all_recommendations)}")
    print(f"\nAverage potential improvements:")
    print(f"  Lifespan:        +{recs_df['lifespan_gain'].mean():.1f} months")
    print(f"  Carbon:          {recs_df['carbon_reduction_pct'].mean():.1f}%")
    print(f"  Water:           {recs_df['water_reduction_pct'].mean():.1f}%")
    
    print(f"\nMost recommended materials:")
    for mat, count in sorted(material_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {mat.replace('_', ' ').title():20s} {count:3d} times ({count/len(all_recommendations)*100:.1f}%)")
    
    return recs_df


def main():
    # Create output directory
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("SUSTAINABLE MATERIAL RECOMMENDATION SYSTEM")
    print("="*80)
    
    # Load data and model
    print("\nLoading data and model...")
    df = pd.read_csv(TRAIN_READY_CSV)
    model = joblib.load(MODEL_PATH)
    print(f"✓ Loaded {len(df):,} articles")
    print(f"✓ Loaded model from {MODEL_PATH}")
    
    # Example 1: Single article recommendation
    print("\n" + "="*80)
    print("EXAMPLE: Single Article Recommendation")
    print("="*80)
    
    sample_article = df.iloc[100]  # Pick an example
    recommendations, current_mat = recommend_sustainable_alternatives(sample_article, model)
    
    current_env = calculate_environmental_score(current_mat)
    current_stats = {
        'lifespan': sample_article['lifespan_months'],
        'carbon': current_env['carbon'],
        'water': current_env['water'],
        'env_score': current_env['composite']
    }
    
    display_recommendations(sample_article['article_id'], recommendations, current_mat)
    create_recommendation_visualization(
        sample_article['article_id'], 
        recommendations, 
        current_mat,
        current_stats
    )
    
    # Example 2: Batch analysis
    print("\n" + "="*80)
    print("BATCH ANALYSIS")
    print("="*80)
    
    batch_results = batch_analyze_dataset(df, model, sample_size=500)
    batch_results.to_csv(OUT_DIR / 'batch_recommendations.csv', index=False)
    print(f"\n✓ Saved batch results to: {OUT_DIR / 'batch_recommendations.csv'}")
    
    print("\n" + "="*80)
    print("DONE! Check the 'ml/recommendations' folder for results.")
    print("="*80)


if __name__ == "__main__":
    main()
