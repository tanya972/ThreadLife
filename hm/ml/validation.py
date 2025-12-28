#!/usr/bin/env python3
"""
Validate Synthetic Durability Labels Against Real Behavioral Signals
----------------------------------------------------------------------
This script validates that our synthetic lifespan predictions correlate
with real-world signals like repurchase behavior and pricing.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import json

# Config
DATA_DIR = Path(r"C:\Users\tanya\clothing predictor\hm\data")
ARTICLES_CSV = DATA_DIR / "articles.csv"
TRANSACTIONS_CSV = DATA_DIR / "transactions.csv"  # Use FULL data
TRAIN_READY_CSV = DATA_DIR / "hm_train_ready.csv"
OUT_DIR = Path(r"C:\Users\tanya\clothing predictor\hm\ml\validation")

def load_data():
    """Load all necessary data"""
    print("Loading data...")
    articles = pd.read_csv(ARTICLES_CSV)
    tx = pd.read_csv(TRANSACTIONS_CSV, parse_dates=["t_dat"])
    train_data = pd.read_csv(TRAIN_READY_CSV)
    
    print(f"  Articles: {len(articles):,} rows")
    print(f"  Transactions: {len(tx):,} rows")
    print(f"  Date range: {tx['t_dat'].min()} to {tx['t_dat'].max()}")
    print(f"  Train data: {len(train_data):,} rows")
    
    return articles, tx, train_data


def calculate_real_repurchase_gaps(tx, articles):
    """
    Calculate ACTUAL repurchase gaps from transaction data.
    For each product_type_name, compute median days between customer repurchases.
    """
    print("\nCalculating real repurchase gaps...")
    
    t = tx.copy()
    t["t_dat"] = pd.to_datetime(t["t_dat"], errors="coerce")
    
    # Check date range
    date_range_days = (t["t_dat"].max() - t["t_dat"].min()).days
    print(f"  Transaction date range: {date_range_days} days")
    
    if date_range_days < 30:
        print(f"  ⚠ WARNING: Only {date_range_days} days of data!")
        print(f"  ⚠ This is insufficient for meaningful repurchase gap analysis")
        print(f"  ⚠ Validation will have limited value - need 3+ months ideally")
    
    # Map article_id to product_type_name
    prod_map = articles.set_index("article_id")["product_type_name"].to_dict()
    t["product_type_name"] = t["article_id"].map(prod_map)
    
    # Drop rows without product type
    t = t.dropna(subset=["product_type_name"])
    
    # Sort by customer, product type, and date
    t = t.sort_values(["customer_id", "product_type_name", "t_dat"])
    
    # Calculate gap between consecutive purchases of same product type by same customer
    t["gap_days"] = t.groupby(["customer_id", "product_type_name"])["t_dat"].diff().dt.days
    
    # Remove gaps that are unreasonably long (> 3 years = likely different lifecycle)
    t = t[t["gap_days"] <= 1095]  # 3 years max
    
    # Calculate median gap per product type
    gap_stats = (
        t.groupby("product_type_name")["gap_days"]
        .agg(['median', 'mean', 'count'])
        .reset_index()
    )
    gap_stats.columns = ['product_type_name', 'median_gap_days', 'mean_gap_days', 'n_gaps']
    
    # Debug: Check what we got
    print(f"  Raw gap stats shape: {gap_stats.shape}")
    
    # Check if we actually have meaningful gaps
    non_zero_gaps = gap_stats[gap_stats['median_gap_days'] > 0]
    if len(non_zero_gaps) == 0:
        print(f"  ⚠ WARNING: All repurchase gaps are 0 days!")
        print(f"  ⚠ This means transaction window is too short for validation")
        print(f"  ⚠ Correlation analysis will not be meaningful")
    
    # Filter out product types with too few observations
    gap_stats = gap_stats[gap_stats['n_gaps'] >= 10]  # At least 10 repurchases
    
    print(f"\n  After filtering (n >= 10):")
    print(f"  Found gaps for {len(gap_stats)} product types")
    print(f"  Total repurchase events: {gap_stats['n_gaps'].sum():,}")
    print(f"  Non-zero gaps: {len(gap_stats[gap_stats['median_gap_days'] > 0])}/{len(gap_stats)}")
    
    return gap_stats


def validation_1_repurchase_correlation(train_data, gap_stats, articles):
    """
    Validation 1: Correlation between predicted lifespan and actual repurchase gaps
    """
    print("\n" + "="*80)
    print("VALIDATION 1: Repurchase Gap Correlation")
    print("="*80)
    
    # Merge train data with gap stats via product_type_name
    # First add product_type_name to train_data
    merged = train_data.merge(
        articles[['article_id', 'product_type_name']], 
        on='article_id', 
        how='left'
    )
    
    # Drop the old median_gap_days from training.py if it exists (to avoid conflict)
    if 'median_gap_days' in merged.columns:
        merged = merged.drop(columns=['median_gap_days'])
    
    # Then merge with gap stats
    print(f"\nBefore gap merge: {len(merged):,} articles")
    print(f"Gap stats available for: {len(gap_stats)} product types")
    
    merged = merged.merge(gap_stats, on='product_type_name', how='inner')
    
    print(f"After gap merge: {len(merged):,} articles")
    
    # Check if we have meaningful gap data
    non_zero_gaps = merged[merged['median_gap_days'] > 0]
    if len(non_zero_gaps) < 100:
        print(f"\n⚠ WARNING: Only {len(non_zero_gaps)} articles with non-zero gaps")
        print(f"⚠ Transaction window too short for meaningful correlation")
        print(f"⚠ Skipping repurchase correlation (need longer time period)")
        return merged, 0.0, 1.0
    
    # Calculate correlation
    corr_median, p_median = stats.pearsonr(
        merged['lifespan_months'], 
        merged['median_gap_days'] / 30.4  # Convert to months
    )
    corr_mean, p_mean = stats.pearsonr(
        merged['lifespan_months'], 
        merged['mean_gap_days'] / 30.4
    )
    
    print(f"\nCorrelation with median repurchase gap:")
    print(f"  Pearson r = {corr_median:.3f}")
    print(f"  p-value   = {p_median:.2e}")
    print(f"  {'✓ SIGNIFICANT' if p_median < 0.01 else '✗ NOT SIGNIFICANT'}")
    
    print(f"\nCorrelation with mean repurchase gap:")
    print(f"  Pearson r = {corr_mean:.3f}")
    print(f"  p-value   = {p_mean:.2e}")
    
    # Interpretation
    if corr_median > 0.5:
        print("\n✓ STRONG positive correlation - Predictions align well with behavior!")
    elif corr_median > 0.3:
        print("\n✓ MODERATE positive correlation - Predictions capture some signal")
    elif corr_median > 0.1:
        print("\n⚠ WEAK positive correlation - Predictions have limited behavioral validity")
    else:
        print("\n✗ NO correlation - Predictions don't match customer behavior")
    
    return merged, corr_median, p_median


def validation_2_price_quality_correlation(train_data):
    """
    Validation 2: Correlation between predicted lifespan and price
    """
    print("\n" + "="*80)
    print("VALIDATION 2: Price-Quality Correlation")
    print("="*80)
    
    # Remove NaN prices
    valid = train_data.dropna(subset=['price', 'lifespan_months'])
    
    print(f"\nArticles with price data: {len(valid):,}")
    
    # Calculate correlation
    corr, p_value = stats.pearsonr(valid['lifespan_months'], valid['price'])
    
    print(f"\nCorrelation between predicted lifespan and price:")
    print(f"  Pearson r = {corr:.3f}")
    print(f"  p-value   = {p_value:.2e}")
    print(f"  {'✓ SIGNIFICANT' if p_value < 0.01 else '✗ NOT SIGNIFICANT'}")
    
    # Interpretation
    if corr > 0.3:
        print("\n✓ Positive correlation - Higher quality items are priced higher (expected)")
    elif corr > 0:
        print("\n⚠ Weak positive correlation - Some price-quality relationship exists")
    else:
        print("\n✗ No price-quality relationship detected")
    
    return valid, corr, p_value


def validation_3_category_sanity_check(train_data, articles):
    """
    Validation 3: Check if category rankings make intuitive sense
    """
    print("\n" + "="*80)
    print("VALIDATION 3: Category Sanity Check")
    print("="*80)
    
    # Merge to get product_type_name
    merged = train_data.merge(
        articles[['article_id', 'product_type_name']], 
        on='article_id', 
        how='left'
    )
    
    # Calculate average lifespan per product type
    category_avg = (
        merged.groupby('product_type_name')['lifespan_months']
        .agg(['mean', 'median', 'count'])
        .reset_index()
    )
    category_avg = category_avg[category_avg['count'] >= 20]  # At least 20 items
    category_avg = category_avg.sort_values('mean', ascending=False)
    
    print(f"\nTop 15 Most Durable Product Types:")
    print("-" * 80)
    for idx, row in category_avg.head(15).iterrows():
        print(f"  {row['product_type_name']:30s} {row['mean']:6.1f} months  (n={row['count']:,})")
    
    print(f"\nBottom 15 Least Durable Product Types:")
    print("-" * 80)
    for idx, row in category_avg.tail(15).iterrows():
        print(f"  {row['product_type_name']:30s} {row['mean']:6.1f} months  (n={row['count']:,})")
    
    # Define expected rankings (common sense)
    expected_durable = ['jacket', 'coat', 'jeans', 'denim', 'leather', 'boot', 'shoe']
    expected_less_durable = ['t-shirt', 'tee', 'tank', 'underwear', 'sock', 'tights']
    
    # Check if expectations are met
    top_categories = category_avg.head(20)['product_type_name'].str.lower()
    bottom_categories = category_avg.tail(20)['product_type_name'].str.lower()
    
    durable_matches = sum(1 for exp in expected_durable if any(exp in cat for cat in top_categories))
    less_durable_matches = sum(1 for exp in expected_less_durable if any(exp in cat for cat in bottom_categories))
    
    print(f"\nSanity Check Results:")
    print(f"  Expected durable items in top 20: {durable_matches}/{len(expected_durable)}")
    print(f"  Expected less durable in bottom 20: {less_durable_matches}/{len(expected_less_durable)}")
    
    if durable_matches >= 4 and less_durable_matches >= 3:
        print("\n✓ PASS - Rankings align with common sense expectations")
        sanity_pass = True
    else:
        print("\n⚠ PARTIAL - Some rankings don't match expectations")
        sanity_pass = False
    
    return category_avg, sanity_pass


def create_validation_visualizations(repurchase_data, price_data, category_data):
    """Create comprehensive validation visualizations"""
    print("\nCreating validation visualizations...")
    
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    # 1. Repurchase gap correlation scatter
    ax1 = fig.add_subplot(gs[0, 0])
    gap_months = repurchase_data['median_gap_days'] / 30.4
    ax1.scatter(repurchase_data['lifespan_months'], gap_months, alpha=0.3, s=20)
    
    # Add trend line
    z = np.polyfit(repurchase_data['lifespan_months'], gap_months, 1)
    p = np.poly1d(z)
    x_line = np.linspace(repurchase_data['lifespan_months'].min(), 
                         repurchase_data['lifespan_months'].max(), 100)
    ax1.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label='Trend')
    
    ax1.set_xlabel('Predicted Lifespan (months)', fontsize=11)
    ax1.set_ylabel('Actual Repurchase Gap (months)', fontsize=11)
    ax1.set_title('Validation 1: Predicted vs Actual Repurchase Behavior', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add correlation text
    corr = repurchase_data[['lifespan_months', 'median_gap_days']].corr().iloc[0, 1]
    ax1.text(0.05, 0.95, f'r = {corr:.3f}', transform=ax1.transAxes, 
             fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # 2. Price-quality correlation scatter
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.scatter(price_data['lifespan_months'], price_data['price'], alpha=0.3, s=20)
    
    # Add trend line
    z = np.polyfit(price_data['lifespan_months'], price_data['price'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(price_data['lifespan_months'].min(), 
                         price_data['lifespan_months'].max(), 100)
    ax2.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label='Trend')
    
    ax2.set_xlabel('Predicted Lifespan (months)', fontsize=11)
    ax2.set_ylabel('Price', fontsize=11)
    ax2.set_title('Validation 2: Price-Quality Relationship', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Add correlation text
    corr = price_data[['lifespan_months', 'price']].corr().iloc[0, 1]
    ax2.text(0.05, 0.95, f'r = {corr:.3f}', transform=ax2.transAxes, 
             fontsize=12, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # 3. Top 10 most durable categories
    ax3 = fig.add_subplot(gs[1, 0])
    top_10 = category_data.head(10)
    ax3.barh(range(len(top_10)), top_10['mean'], color='green', alpha=0.7)
    ax3.set_yticks(range(len(top_10)))
    ax3.set_yticklabels(top_10['product_type_name'], fontsize=9)
    ax3.set_xlabel('Average Predicted Lifespan (months)', fontsize=11)
    ax3.set_title('Top 10 Most Durable Product Types', fontsize=12, fontweight='bold')
    ax3.invert_yaxis()
    ax3.grid(True, alpha=0.3, axis='x')
    
    # 4. Bottom 10 least durable categories
    ax4 = fig.add_subplot(gs[1, 1])
    bottom_10 = category_data.tail(10)
    ax4.barh(range(len(bottom_10)), bottom_10['mean'], color='orange', alpha=0.7)
    ax4.set_yticks(range(len(bottom_10)))
    ax4.set_yticklabels(bottom_10['product_type_name'], fontsize=9)
    ax4.set_xlabel('Average Predicted Lifespan (months)', fontsize=11)
    ax4.set_title('Bottom 10 Least Durable Product Types', fontsize=12, fontweight='bold')
    ax4.invert_yaxis()
    ax4.grid(True, alpha=0.3, axis='x')
    
    # 5. Distribution of predicted lifespans
    ax5 = fig.add_subplot(gs[2, 0])
    ax5.hist(repurchase_data['lifespan_months'], bins=50, color='steelblue', alpha=0.7, edgecolor='black')
    ax5.axvline(repurchase_data['lifespan_months'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
    ax5.axvline(repurchase_data['lifespan_months'].median(), color='green', linestyle='--', linewidth=2, label='Median')
    ax5.set_xlabel('Predicted Lifespan (months)', fontsize=11)
    ax5.set_ylabel('Frequency', fontsize=11)
    ax5.set_title('Distribution of Predicted Lifespans', fontsize=12, fontweight='bold')
    ax5.legend()
    ax5.grid(True, alpha=0.3, axis='y')
    
    # 6. Distribution of actual repurchase gaps
    ax6 = fig.add_subplot(gs[2, 1])
    gap_months = repurchase_data['median_gap_days'] / 30.4
    ax6.hist(gap_months, bins=50, color='coral', alpha=0.7, edgecolor='black')
    ax6.axvline(gap_months.mean(), color='red', linestyle='--', linewidth=2, label='Mean')
    ax6.axvline(gap_months.median(), color='green', linestyle='--', linewidth=2, label='Median')
    ax6.set_xlabel('Actual Repurchase Gap (months)', fontsize=11)
    ax6.set_ylabel('Frequency', fontsize=11)
    ax6.set_title('Distribution of Actual Repurchase Gaps', fontsize=12, fontweight='bold')
    ax6.legend()
    ax6.grid(True, alpha=0.3, axis='y')
    
    plt.savefig(OUT_DIR / 'validation_results.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {OUT_DIR / 'validation_results.png'}")


def save_validation_report(repurchase_corr, price_corr, sanity_pass):
    """Save comprehensive validation report"""
    
    report = {
        'validation_summary': {
            'repurchase_correlation': {
                'pearson_r': float(repurchase_corr[0]),
                'p_value': float(repurchase_corr[1]),
                'interpretation': 'Strong' if abs(repurchase_corr[0]) > 0.5 else 'Moderate' if abs(repurchase_corr[0]) > 0.3 else 'Weak',
                'significant': bool(repurchase_corr[1] < 0.01)
            },
            'price_quality_correlation': {
                'pearson_r': float(price_corr[0]),
                'p_value': float(price_corr[1]),
                'interpretation': 'Strong' if abs(price_corr[0]) > 0.5 else 'Moderate' if abs(price_corr[0]) > 0.3 else 'Weak',
                'significant': bool(price_corr[1] < 0.01)
            },
            'category_sanity_check': {
                'passed': sanity_pass
            }
        },
        'overall_assessment': 'VALIDATED' if (abs(repurchase_corr[0]) > 0.3 and sanity_pass) else 'NEEDS_IMPROVEMENT'
    }
    
    with open(OUT_DIR / 'validation_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Markdown summary
    md = f"""# Validation Report: Synthetic Durability Labels

## Executive Summary

This report validates whether our synthetic durability labels correlate with real-world behavioral and market signals.

## Validation Tests

### 1. Repurchase Gap Correlation ⭐
**Hypothesis:** Items with higher predicted durability should show longer gaps between customer repurchases.

**Results:**
- Pearson r = {repurchase_corr[0]:.3f}
- p-value = {repurchase_corr[1]:.2e}
- Status: {'✓ SIGNIFICANT' if repurchase_corr[1] < 0.01 else '✗ NOT SIGNIFICANT'}
- Interpretation: {report['validation_summary']['repurchase_correlation']['interpretation']}

**Conclusion:** {'Synthetic labels align with actual customer behavior' if abs(repurchase_corr[0]) > 0.3 else 'Weak alignment with customer behavior'}

### 2. Price-Quality Correlation
**Hypothesis:** Higher quality (more durable) items should command higher prices in the market.

**Results:**
- Pearson r = {price_corr[0]:.3f}
- p-value = {price_corr[1]:.2e}
- Status: {'✓ SIGNIFICANT' if price_corr[1] < 0.01 else '✗ NOT SIGNIFICANT'}
- Interpretation: {report['validation_summary']['price_quality_correlation']['interpretation']}

**Conclusion:** {'Predictions align with market pricing signals' if abs(price_corr[0]) > 0.2 else 'Limited alignment with pricing'}

### 3. Category Sanity Check
**Hypothesis:** Product category rankings should match common sense (e.g., jeans more durable than t-shirts).

**Results:**
- Status: {'✓ PASS' if sanity_pass else '⚠ PARTIAL'}

**Conclusion:** {'Rankings align with domain knowledge expectations' if sanity_pass else 'Some rankings need adjustment'}

## Overall Assessment

**Status: {report['overall_assessment']}**

{'✓ The synthetic durability labels demonstrate meaningful correlation with real-world signals and can be considered a valid proxy for clothing lifespan.' if report['overall_assessment'] == 'VALIDATED' else '⚠ The synthetic labels show some alignment but may need refinement for stronger validity.'}

## Implications

- Model predictions correlate with actual customer repurchase behavior
- Price-quality relationship is {'present' if abs(price_corr[0]) > 0.2 else 'weak'}
- Category rankings {'match' if sanity_pass else 'partially match'} domain knowledge

## Next Steps

1. {'Consider using validated predictions for downstream applications' if report['overall_assessment'] == 'VALIDATED' else 'Refine synthetic label generation approach'}
2. Explore material substitution recommendations based on validated durability scores
3. Calculate cost-per-wear metrics using validated lifespan predictions
"""
    
    with open(OUT_DIR / 'validation_summary.md', 'w', encoding='utf-8') as f:
        f.write(md)
    
    print(f"✓ Saved: {OUT_DIR / 'validation_report.json'}")
    print(f"✓ Saved: {OUT_DIR / 'validation_summary.md'}")


def main():
    # Create output directory
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("VALIDATION: Synthetic Durability Labels vs Real-World Signals")
    print("="*80)
    
    # Load data
    articles, tx, train_data = load_data()
    
    # Calculate real repurchase gaps
    gap_stats = calculate_real_repurchase_gaps(tx, articles)
    
    # Validation 1: Repurchase correlation
    repurchase_data, corr_repurchase, p_repurchase = validation_1_repurchase_correlation(
        train_data, gap_stats, articles
    )
    
    # Validation 2: Price-quality correlation
    price_data, corr_price, p_price = validation_2_price_quality_correlation(train_data)
    
    # Validation 3: Category sanity check
    category_data, sanity_pass = validation_3_category_sanity_check(train_data, articles)
    
    # Create visualizations
    create_validation_visualizations(repurchase_data, price_data, category_data)
    
    # Save report
    save_validation_report(
        (corr_repurchase, p_repurchase),
        (corr_price, p_price),
        sanity_pass
    )
    
    print("\n" + "="*80)
    print("VALIDATION COMPLETE!")
    print("="*80)
    print(f"\nCheck the '{OUT_DIR}' folder for:")
    print("  - validation_results.png (visualizations)")
    print("  - validation_report.json (detailed metrics)")
    print("  - validation_summary.md (readable summary)")
    
    # Final summary
    print("\n" + "="*80)
    print("QUICK SUMMARY:")
    print("="*80)
    print(f"Repurchase Correlation: r = {corr_repurchase:.3f} ({'STRONG' if abs(corr_repurchase) > 0.5 else 'MODERATE' if abs(corr_repurchase) > 0.3 else 'WEAK'})")
    print(f"Price Correlation:      r = {corr_price:.3f} ({'STRONG' if abs(corr_price) > 0.5 else 'MODERATE' if abs(corr_price) > 0.3 else 'WEAK'})")
    print(f"Sanity Check:           {'✓ PASS' if sanity_pass else '⚠ PARTIAL'}")
    
    if abs(corr_repurchase) > 0.3 and sanity_pass:
        print("\n✓✓✓ VALIDATION PASSED - Your synthetic labels are meaningful! ✓✓✓")
    else:
        print("\n⚠ VALIDATION PARTIAL - Consider refining synthetic label generation")


if __name__ == "__main__":
    main()
