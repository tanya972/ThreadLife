#!/usr/bin/env python3
"""
Compare Multiple ML Models for Lifespan Prediction
Shows you understand model selection and evaluation
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import json

# Setup
DATA_PATH = Path(r"C:\Users\tanya\clothing predictor\hm\data\hm_train_ready.csv")
OUT_DIR = Path(r"C:\Users\tanya\clothing predictor\hm\ml\model_comparison")

def prepare_data():
    """Load and prepare data"""
    df = pd.read_csv(DATA_PATH)
    
    # Target
    y = df['lifespan_months']
    
    # Select ONLY features with actual data (not NaN columns)
    feature_cols = [
        'category',
        'product_group_name', 
        'graphical_appearance_name',
        'colour_group_name',
        'perceived_colour_value_name',
        'index_group_name',
        'price',
        'mat_score',
        'price_decay'
    ]
    
    # Only include columns that exist in the dataframe
    feature_cols = [col for col in feature_cols if col in df.columns]
    
    X = df[feature_cols]
    
    # Remove rows where target is NaN
    valid_idx = ~y.isna()
    X = X[valid_idx]
    y = y[valid_idx]
    
    # Identify feature types
    num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = X.select_dtypes(include=['object', 'string']).columns.tolist()
    
    print(f"\nFeatures being used:")
    print(f"  Numeric: {num_cols}")
    print(f"  Categorical: {cat_cols}")
    
    return X, y, num_cols, cat_cols

def create_preprocessor(num_cols, cat_cols):
    """Create preprocessing pipeline"""
    numeric_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer([
        ('num', numeric_transformer, num_cols),
        ('cat', categorical_transformer, cat_cols)
    ])
    
    return preprocessor

def train_and_evaluate_models(X, y, num_cols, cat_cols):
    """Train multiple models and compare performance"""
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Preprocessing
    preprocessor = create_preprocessor(num_cols, cat_cols)
    
    # Define models to compare
    models = {
        'Random Forest': RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1
        ),
        'Gradient Boosting': GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        ),
        'Ridge Regression': Ridge(alpha=1.0),
        'Neural Network': MLPRegressor(
            hidden_layer_sizes=(100, 50),
            max_iter=500,
            random_state=42,
            early_stopping=True
        )
    }
    
    results = {}
    trained_models = {}
    
    print("\nTraining and evaluating models...\n")
    print("=" * 70)
    
    for name, model in models.items():
        print(f"\n{name}:")
        print("-" * 70)
        
        # Create pipeline
        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('model', model)
        ])
        
        # Train
        pipeline.fit(X_train, y_train)
        
        # Predict
        y_pred_train = pipeline.predict(X_train)
        y_pred_test = pipeline.predict(X_test)
        
        # Metrics
        train_mae = mean_absolute_error(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        
        # Cross-validation (on training set)
        cv_scores = cross_val_score(
            pipeline, X_train, y_train, 
            cv=3, scoring='neg_mean_absolute_error', n_jobs=-1
        )
        cv_mae = -cv_scores.mean()
        
        results[name] = {
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'cv_mae': cv_mae,
            'predictions': y_pred_test
        }
        
        trained_models[name] = pipeline
        
        print(f"  Train MAE: {train_mae:.2f} months")
        print(f"  Test MAE:  {test_mae:.2f} months")
        print(f"  CV MAE:    {cv_mae:.2f} months")
        print(f"  Train R²:  {train_r2:.3f}")
        print(f"  Test R²:   {test_r2:.3f}")
        print(f"  Test RMSE: {test_rmse:.2f} months")
    
    return results, trained_models, y_test

def plot_results(results, y_test):
    """Create visualization comparing models"""
    
    # 1. Performance comparison bar chart
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Test MAE
    models = list(results.keys())
    test_mae = [results[m]['test_mae'] for m in models]
    
    axes[0, 0].barh(models, test_mae, color='steelblue')
    axes[0, 0].set_xlabel('Mean Absolute Error (months)')
    axes[0, 0].set_title('Test Set MAE (Lower is Better)')
    axes[0, 0].invert_yaxis()
    
    # Test R²
    test_r2 = [results[m]['test_r2'] for m in models]
    axes[0, 1].barh(models, test_r2, color='coral')
    axes[0, 1].set_xlabel('R² Score')
    axes[0, 1].set_title('Test Set R² (Higher is Better)')
    axes[0, 1].invert_yaxis()
    axes[0, 1].set_xlim([0, 1])
    
    # Overfitting check (Train vs Test MAE)
    train_mae = [results[m]['train_mae'] for m in models]
    x = np.arange(len(models))
    width = 0.35
    
    axes[1, 0].bar(x - width/2, train_mae, width, label='Train', color='lightblue')
    axes[1, 0].bar(x + width/2, test_mae, width, label='Test', color='darkblue')
    axes[1, 0].set_ylabel('MAE (months)')
    axes[1, 0].set_title('Train vs Test MAE (Gap shows overfitting)')
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(models, rotation=45, ha='right')
    axes[1, 0].legend()
    
    # Prediction scatter (best model)
    best_model = min(results.keys(), key=lambda m: results[m]['test_mae'])
    y_pred_best = results[best_model]['predictions']
    
    axes[1, 1].scatter(y_test, y_pred_best, alpha=0.5, s=20)
    axes[1, 1].plot([y_test.min(), y_test.max()], 
                     [y_test.min(), y_test.max()], 
                     'r--', lw=2, label='Perfect prediction')
    axes[1, 1].set_xlabel('Actual Lifespan (months)')
    axes[1, 1].set_ylabel('Predicted Lifespan (months)')
    axes[1, 1].set_title(f'Best Model: {best_model}')
    axes[1, 1].legend()
    
    plt.tight_layout()
    plt.savefig(OUT_DIR / 'model_comparison.png', dpi=300, bbox_inches='tight')
    print(f"\n✓ Saved visualization: {OUT_DIR / 'model_comparison.png'}")
    
    return best_model

def create_ensemble(trained_models, X, y):
    """Create simple ensemble by averaging top models"""
    
    # Split for testing
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Get predictions from all models
    predictions = {}
    for name, model in trained_models.items():
        pred = model.predict(X_test)
        predictions[name] = pred
    
    # Simple average ensemble
    ensemble_pred = np.mean(list(predictions.values()), axis=0)
    
    # Weighted ensemble (weight by inverse test error)
    # Best models get more weight
    errors = {name: mean_absolute_error(y_test, pred) 
              for name, pred in predictions.items()}
    weights = {name: 1.0 / error for name, error in errors.items()}
    weight_sum = sum(weights.values())
    weights = {name: w / weight_sum for name, w in weights.items()}
    
    weighted_pred = sum(weights[name] * predictions[name] 
                       for name in predictions.keys())
    
    # Compare
    ensemble_mae = mean_absolute_error(y_test, ensemble_pred)
    weighted_mae = mean_absolute_error(y_test, weighted_pred)
    ensemble_r2 = r2_score(y_test, ensemble_pred)
    weighted_r2 = r2_score(y_test, weighted_pred)
    
    print("\n" + "=" * 70)
    print("ENSEMBLE RESULTS:")
    print("-" * 70)
    print(f"Simple Average Ensemble MAE:  {ensemble_mae:.2f} months")
    print(f"Simple Average Ensemble R²:   {ensemble_r2:.3f}")
    print(f"\nWeighted Ensemble MAE:        {weighted_mae:.2f} months")
    print(f"Weighted Ensemble R²:         {weighted_r2:.3f}")
    print(f"\nModel Weights:")
    for name, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        print(f"  {name:20s}: {weight:.3f}")
    
    return {
        'simple_mae': ensemble_mae,
        'simple_r2': ensemble_r2,
        'weighted_mae': weighted_mae,
        'weighted_r2': weighted_r2,
        'weights': weights
    }

def save_report(results, best_model, ensemble_results):
    """Save comprehensive report"""
    
    report = {
        'model_comparison': {
            name: {
                'test_mae': float(res['test_mae']),
                'test_r2': float(res['test_r2']),
                'cv_mae': float(res['cv_mae']),
                'test_rmse': float(res['test_rmse'])
            }
            for name, res in results.items()
        },
        'best_model': best_model,
        'best_model_mae': float(results[best_model]['test_mae']),
        'best_model_r2': float(results[best_model]['test_r2']),
        'ensemble': ensemble_results
    }
    
    report_path = OUT_DIR / 'model_comparison_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, indent=2, fp=f)
    
    print(f"✓ Saved report: {report_path}")
    
    # Create markdown summary
    md = f"""# Model Comparison Report

## Best Model: {best_model}
- Test MAE: {results[best_model]['test_mae']:.2f} months
- Test R²: {results[best_model]['test_r2']:.3f}
- CV MAE: {results[best_model]['cv_mae']:.2f} months

## All Models Performance

| Model | Test MAE | Test R² | CV MAE | Test RMSE |
|-------|----------|---------|--------|-----------|
"""
    
    for name, res in sorted(results.items(), key=lambda x: x[1]['test_mae']):
        md += f"| {name} | {res['test_mae']:.2f} | {res['test_r2']:.3f} | {res['cv_mae']:.2f} | {res['test_rmse']:.2f} |\n"
    
    md += f"""
## Ensemble Results
- Simple Average MAE: {ensemble_results['simple_mae']:.2f} months
- Weighted Ensemble MAE: {ensemble_results['weighted_mae']:.2f} months

**Improvement over best single model:** {results[best_model]['test_mae'] - ensemble_results['weighted_mae']:.2f} months
"""
    
    md_path = OUT_DIR / 'model_comparison_summary.md'
    md_path.write_text(md)
    print(f"✓ Saved summary: {md_path}")

def main():
    # Create output directory
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("MODEL COMPARISON FOR LIFESPAN PREDICTION")
    print("=" * 70)
    
    # Prepare data
    X, y, num_cols, cat_cols = prepare_data()
    print(f"\nDataset: {len(X)} samples, {len(X.columns)} features")
    print(f"Numeric features: {len(num_cols)}")
    print(f"Categorical features: {len(cat_cols)}")
    
    # Train and evaluate
    results, trained_models, y_test = train_and_evaluate_models(X, y, num_cols, cat_cols)
    
    # Visualize
    best_model = plot_results(results, y_test)
    
    # Ensemble
    ensemble_results = create_ensemble(trained_models, X, y)
    
    # Save report
    save_report(results, best_model, ensemble_results)
    
    # Save best model
    best_pipeline = trained_models[best_model]
    joblib.dump(best_pipeline, OUT_DIR / 'best_model.joblib')
    print(f"✓ Saved best model: {OUT_DIR / 'best_model.joblib'}")
    
    print("\n" + "=" * 70)
    print("DONE! Check the 'ml/model_comparison' folder for results.")
    print("=" * 70)

if __name__ == "__main__":
    main()
