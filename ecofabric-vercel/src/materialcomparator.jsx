"use client";

import React, { useState, useMemo } from 'react';
import './materialcomparator.css';

// Material impact database
const MATERIAL_DATA = {
  cotton: { 
    co2: 15.0, water: 2700, 
    mat_score: 1.0, 
    cost: 'medium',
    name: 'Cotton',
    description: 'Comfortable, breathable, durable natural fiber'
  },
  recycled_cotton: { 
    co2: 8.0, water: 500, 
    mat_score: 1.0, 
    cost: 'medium-high',
    name: 'Recycled Cotton',
    description: 'Reduced environmental impact, similar durability to virgin cotton'
  },
  polyester: { 
    co2: 10.0, water: 25, 
    mat_score: 0.45, 
    cost: 'low',
    name: 'Polyester',
    description: 'Durable synthetic, cost-effective but lower perceived quality'
  },
  recycled_polyester: { 
    co2: 6.0, water: 20, 
    mat_score: 0.50, 
    cost: 'low-medium',
    name: 'Recycled Polyester (rPET)',
    description: 'Lower carbon footprint, good durability'
  },
  wool: { 
    co2: 25.0, water: 1500, 
    mat_score: 0.85, 
    cost: 'high',
    name: 'Wool',
    description: 'Warm, durable natural fiber with higher environmental cost'
  },
  linen: { 
    co2: 8.0, water: 650, 
    mat_score: 0.80, 
    cost: 'medium',
    name: 'Linen',
    description: 'Sustainable, breathable, wrinkles easily'
  },
  elastane: { 
    co2: 20.0, water: 100, 
    mat_score: 0.60, 
    cost: 'medium',
    name: 'Elastane/Spandex',
    description: 'Adds stretch and shape retention'
  },
  nylon: { 
    co2: 15.0, water: 30, 
    mat_score: 0.50, 
    cost: 'low-medium',
    name: 'Nylon',
    description: 'Strong, elastic synthetic fiber'
  }
};

// Simplified prediction model based on feature importances
const CATEGORY_MULTIPLIERS = {
  'tshirt': 1.0,
  'sweater': 1.15,
  'jacket': 1.15,
  'dress': 0.9,
  'trousers': 0.95,
  'jeans': 1.1,
  'other': 1.0
};

function calculateMaterialScore(composition) {
  let score = 0.65;
  let totalPct = 0;
  
  Object.entries(composition).forEach(([material, percentage]) => {
    if (percentage > 0 && MATERIAL_DATA[material]) {
      const weight = MATERIAL_DATA[material].mat_score;
      score += (weight - 0.60) * percentage;
      totalPct += percentage;
    }
  });
  
  if (totalPct > 0 && totalPct !== 1.0) {
    const factor = totalPct;
    score = 0.65 + (score - 0.65) * (1 / factor);
  }
  
  return Math.max(0.4, Math.min(1.2, score));
}

function predictLifespan(composition, category = 'tshirt') {
  const matScore = calculateMaterialScore(composition);
  const categoryMult = CATEGORY_MULTIPLIERS[category] || CATEGORY_MULTIPLIERS.other;
  const baseLifespan = 30 + (matScore - 0.65) * 60;
  return baseLifespan * categoryMult;
}

function calculateImpact(composition, garmentMassKg = 0.25) {
  let co2Total = 0;
  let waterTotal = 0;
  
  Object.entries(composition).forEach(([material, percentage]) => {
    if (percentage > 0 && MATERIAL_DATA[material]) {
      const materialData = MATERIAL_DATA[material];
      co2Total += materialData.co2 * percentage * garmentMassKg;
      waterTotal += materialData.water * percentage * garmentMassKg;
    }
  });
  
  return { co2: co2Total, water: waterTotal };
}

// Custom RangeInput component with gradient
const RangeInput = ({ material, value, onChange }) => {
  const percentage = (value * 100).toFixed(0);
  
  return (
    <div className="material-slider">
      <div className="material-label">
        <span>{MATERIAL_DATA[material]?.name || material}</span>
        <span className="percentage">{percentage}%</span>
      </div>
      <input
        type="range"
        min="0"
        max="1"
        step="0.05"
        value={value}
        onChange={onChange}
        style={{
          background: `linear-gradient(to right, 
            var(--color-primary) 0%, 
            var(--color-primary) ${percentage}%, 
            var(--color-border) ${percentage}%, 
            var(--color-border) 100%)`
        }}
      />
    </div>
  );
};

export default function MaterialComparator() {
  const [currentComposition, setCurrentComposition] = useState({
    cotton: 1.0,
    polyester: 0.0,
    wool: 0.0,
    elastane: 0.0
  });
  
  const [category, setCategory] = useState('tshirt');
  
  const currentLifespan = useMemo(() => 
    predictLifespan(currentComposition, category), 
    [currentComposition, category]
  );
  
  const currentImpact = useMemo(() => 
    calculateImpact(currentComposition), 
    [currentComposition]
  );
  
  const suggestions = useMemo(() => {
    const baseComposition = currentComposition;
    const improvements = [];
    
    if (baseComposition.polyester > 0.1) {
      const newComp = {
        ...baseComposition,
        recycled_polyester: baseComposition.polyester,
        polyester: 0
      };
      const newLifespan = predictLifespan(newComp, category);
      const newImpact = calculateImpact(newComp);
      improvements.push({
        label: 'Switch to Recycled Polyester',
        composition: newComp,
        lifespan: newLifespan,
        deltaLifespan: newLifespan - currentLifespan,
        impact: newImpact,
        deltaCO2: newImpact.co2 - currentImpact.co2
      });
    }
    
    if (baseComposition.cotton > 0.5) {
      const newComp = {
        ...baseComposition,
        recycled_cotton: baseComposition.cotton * 0.8,
        cotton: baseComposition.cotton * 0.2
      };
      const newLifespan = predictLifespan(newComp, category);
      const newImpact = calculateImpact(newComp);
      improvements.push({
        label: 'Use 80% Recycled Cotton',
        composition: newComp,
        lifespan: newLifespan,
        deltaLifespan: newLifespan - currentLifespan,
        impact: newImpact,
        deltaCO2: newImpact.co2 - currentImpact.co2
      });
    }
    
    if (baseComposition.polyester > 0.3 && baseComposition.cotton < 0.5) {
      const reduction = Math.min(0.3, baseComposition.polyester);
      const newComp = {
        ...baseComposition,
        polyester: baseComposition.polyester - reduction,
        cotton: (baseComposition.cotton || 0) + reduction
      };
      const newLifespan = predictLifespan(newComp, category);
      const newImpact = calculateImpact(newComp);
      improvements.push({
        label: 'Replace Polyester with Cotton',
        composition: newComp,
        lifespan: newLifespan,
        deltaLifespan: newLifespan - currentLifespan,
        impact: newImpact,
        deltaCO2: newImpact.co2 - currentImpact.co2
      });
    }
    
    if (['tshirt', 'dress'].includes(category) && baseComposition.polyester > 0.2) {
      const reduction = Math.min(0.3, baseComposition.polyester);
      const newComp = {
        ...baseComposition,
        polyester: baseComposition.polyester - reduction,
        linen: (baseComposition.linen || 0) + reduction
      };
      const newLifespan = predictLifespan(newComp, category);
      const newImpact = calculateImpact(newComp);
      improvements.push({
        label: 'Add Linen Blend',
        composition: newComp,
        lifespan: newLifespan,
        deltaLifespan: newLifespan - currentLifespan,
        impact: newImpact,
        deltaCO2: newImpact.co2 - currentImpact.co2
      });
    }
    
    return improvements.sort((a, b) => (b.deltaLifespan - b.deltaCO2 * 50) - (a.deltaLifespan - a.deltaCO2 * 50));
  }, [currentComposition, category, currentLifespan, currentImpact]);
  
  const updateComposition = (material, value) => {
    const newComp = { ...currentComposition, [material]: Math.max(0, Math.min(1, value)) };
    setCurrentComposition(newComp);
  };
  
  const presetCompositions = {
    '100% Cotton': { cotton: 1.0, polyester: 0, wool: 0, elastane: 0 },
    '50/50 Cotton-Poly': { cotton: 0.5, polyester: 0.5, wool: 0, elastane: 0 },
    '100% Polyester': { cotton: 0, polyester: 1.0, wool: 0, elastane: 0 },
    'Cotton + Spandex': { cotton: 0.95, polyester: 0, wool: 0, elastane: 0.05 },
    'Wool Blend': { cotton: 0, polyester: 0, wool: 1.0, elastane: 0 }
  };
  
  return (
    <div className="material-comparator">
      <div className="container">
        <header>
          <h1>Material Impact Calculator</h1>
          <p>
            Discover how material choices affect garment lifespan and environmental impact. 
            Make informed decisions for a more sustainable wardrobe.
          </p>
        </header>
        
        <div className="card">
          <h2>Configure Your Garment</h2>
          
          <div className="config-row">
            <div className="config-col">
              <label>Product Category</label>
              <select value={category} onChange={e => setCategory(e.target.value)}>
                <option value="tshirt">T-Shirt</option>
                <option value="sweater">Sweater</option>
                <option value="jacket">Jacket</option>
                <option value="dress">Dress</option>
                <option value="trousers">Trousers</option>
                <option value="jeans">Jeans</option>
              </select>
            </div>
            
            <div className="config-col presets">
              <label>Quick Presets</label>
              <div className="preset-buttons">
                {Object.entries(presetCompositions).map(([name, comp]) => (
                  <button
                    key={name}
                    onClick={() => setCurrentComposition(comp)}
                    className="preset-btn"
                  >
                    {name}
                  </button>
                ))}
              </div>
            </div>
          </div>
          
          <div className="materials-grid">
            {Object.entries(MATERIAL_DATA).filter(([mat]) => 
              ['cotton', 'recycled_cotton', 'polyester', 'recycled_polyester', 'wool', 'linen', 'elastane'].includes(mat)
            ).map(([mat, data]) => (
              <RangeInput
                key={mat}
                material={mat}
                value={currentComposition[mat] || 0}
                onChange={e => updateComposition(mat, parseFloat(e.target.value))}
              />
            ))}
          </div>
          
          <div className="total-percentage">
            Total: {(Object.values(currentComposition).reduce((a, b) => a + (b || 0), 0) * 100).toFixed(0)}%
          </div>
        </div>
        
        <div className="metrics-grid">
          <div className="metric-card border-blue">
            <div className="metric-label">Predicted Lifespan</div>
            <div className="metric-value blue">{currentLifespan.toFixed(1)}</div>
            <div className="metric-unit">months</div>
          </div>
          
          <div className="metric-card border-orange">
            <div className="metric-label">CO₂ Footprint</div>
            <div className="metric-value orange">{currentImpact.co2.toFixed(3)}</div>
            <div className="metric-unit">kg CO₂e</div>
          </div>
          
          <div className="metric-card border-cyan">
            <div className="metric-label">Water Use</div>
            <div className="metric-value cyan">{currentImpact.water.toFixed(0)}</div>
            <div className="metric-unit">liters</div>
          </div>
        </div>
        
        {suggestions.length > 0 && (
          <div className="suggestions">
            <h2>Improvement Suggestions</h2>
            <div className="suggestions-list">
              {suggestions.map((suggestion, idx) => (
                <div key={idx} className="suggestion-card">
                  <div className="suggestion-header">
                    <div>
                      <div className="suggestion-title">{suggestion.label}</div>
                      <div className="suggestion-composition">
                        {Object.entries(suggestion.composition)
                          .filter(([_, pct]) => pct > 0)
                          .map(([mat, pct]) => `${MATERIAL_DATA[mat]?.name || mat}: ${(pct * 100).toFixed(0)}%`)
                          .join(', ')
                        }
                      </div>
                    </div>
                    <div className="suggestion-impact">
                      <div className="delta-value green">+{suggestion.deltaLifespan.toFixed(1)}</div>
                      <div className="delta-label">mo longer</div>
                    </div>
                  </div>
                  
                  <div className="suggestion-metrics">
                    <div className="mini-metric">
                      <div className="mini-label">New Lifespan</div>
                      <div className="mini-value">{suggestion.lifespan.toFixed(1)} mo</div>
                    </div>
                    <div className="mini-metric">
                      <div className="mini-label">Δ CO₂</div>
                      <div className={`mini-value ${suggestion.deltaCO2 < 0 ? 'green' : 'red'}`}>
                        {suggestion.deltaCO2 > 0 ? '+' : ''}{suggestion.deltaCO2.toFixed(3)} kg
                      </div>
                    </div>
                    <div className="mini-metric">
                      <div className="mini-label">Δ Water</div>
                      <div className={`mini-value ${(suggestion.impact.water - currentImpact.water) < 0 ? 'green' : 'red'}`}>
                        {((suggestion.impact.water - currentImpact.water) > 0 ? '+' : '')}{(suggestion.impact.water - currentImpact.water).toFixed(0)} L
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="reference-section">
          <h3>Material Reference Guide</h3>
          <div className="reference-grid">
            {Object.entries(MATERIAL_DATA).map(([key, data]) => (
              <div key={key} className="reference-item">
                <div className="ref-name">{data.name}</div>
                <div className="ref-desc">{data.description}</div>
                <div className="ref-stats">
                  <div>
                    <div className="ref-stat-label">CO₂</div>
                    <div className="ref-stat-value">{data.co2} kg/kg</div>
                  </div>
                  <div>
                    <div className="ref-stat-label">Water</div>
                    <div className="ref-stat-value">{data.water} L/kg</div>
                  </div>
                  <div>
                    <div className="ref-stat-label">Score</div>
                    <div className="ref-stat-value">{data.mat_score.toFixed(2)}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <footer>
          Predictions based on material scoring model trained on H&M sustainability data.
          Environmental impacts are estimates based on industry averages.
        </footer>
      </div>
    </div>
  );
}
