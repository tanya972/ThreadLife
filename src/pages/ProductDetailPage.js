import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Leaf, ExternalLink } from 'lucide-react';

function ProductDetailPage() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    // Get product from sessionStorage
    const storedProduct = sessionStorage.getItem('currentProduct');
    if (storedProduct) {
      const productData = JSON.parse(storedProduct);
      setProduct(productData);
      
      // Generate recommendations
      const recs = generateImprovedCompositions(productData.composition, productData.category);
      setRecommendations(recs);
    }
  }, [productId]);

  const generateImprovedCompositions = (currentComp, category) => {
    const alternatives = {
      'Cotton': ['Organic Cotton', 'Hemp', 'Linen'],
      'Polyester': ['Recycled Polyester', 'Tencel', 'Hemp'],
      'Viscose': ['Tencel', 'Modal', 'Organic Cotton'],
      'Acrylic': ['Organic Cotton', 'Wool', 'Tencel'],
      'Nylon': ['Recycled Nylon', 'Tencel'],
      'Polyamide': ['Recycled Nylon', 'Tencel'],
      'Elastane': ['Elastane'],
      'Wool': ['Organic Wool', 'Alpaca'],
      'Linen': ['Organic Linen', 'Hemp']
    };

    const recommendations = [];

    // Recommendation 1: Replace synthetics
    const rec1 = { ...currentComp };
    Object.keys(rec1).forEach(material => {
      if (['Polyester', 'Viscose', 'Acrylic', 'Nylon', 'Polyamide'].includes(material)) {
        const replacement = alternatives[material][0];
        rec1[replacement] = rec1[material];
        delete rec1[material];
      } else if (material === 'Cotton' && rec1[material] > 50) {
        rec1['Organic Cotton'] = rec1[material];
        delete rec1[material];
      }
    });
    recommendations.push({
      name: 'Sustainable Blend',
      composition: rec1,
      description: 'Replace synthetics with eco-friendly alternatives',
      carbonSaving: 45,
      waterSaving: 38
    });

    // Recommendation 2: Maximum natural
    const rec2 = {};
    const mainFiber = Object.keys(currentComp)[0];
    const sustainableVersion = alternatives[mainFiber]?.[0] || 'Organic Cotton';
    
    rec2[sustainableVersion] = 95;
    if (currentComp['Elastane']) {
      rec2['Elastane'] = 5;
    } else {
      rec2[sustainableVersion] = 100;
    }
    
    recommendations.push({
      name: 'Maximum Natural',
      composition: rec2,
      description: 'Maximize natural, biodegradable fibers',
      carbonSaving: 52,
      waterSaving: 41
    });

    // Recommendation 3: Hemp blend
    const rec3 = {};
    const totalSynthetic = Object.keys(currentComp)
      .filter(m => ['Polyester', 'Nylon', 'Acrylic', 'Polyamide'].includes(m))
      .reduce((sum, m) => sum + currentComp[m], 0);
    
    if (totalSynthetic > 0) {
      rec3['Hemp'] = 70;
      rec3['Organic Cotton'] = 25;
      if (currentComp['Elastane']) {
        rec3['Elastane'] = 5;
      } else {
        rec3['Organic Cotton'] = 30;
      }
    } else {
      rec3['Hemp'] = 60;
      rec3['Linen'] = 40;
    }

    recommendations.push({
      name: 'Hemp Blend',
      composition: rec3,
      description: 'Durable hemp-based composition',
      carbonSaving: 67,
      waterSaving: 72
    });

    return recommendations;
  };

  if (!product) {
    return (
      <div className="app">
        <div className="container" style={{padding: '48px 16px', textAlign: 'center'}}>
          <p>Loading product...</p>
          <button 
            onClick={() => navigate('/')}
            style={{
              marginTop: '16px',
              padding: '12px 24px',
              backgroundColor: '#059669',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            Go Back Home
          </button>
        </div>
      </div>
    );
  }

  const currentSynthetic = Object.keys(product.composition)
    .filter(m => ['Polyester', 'Acrylic', 'Nylon', 'Polyamide', 'Viscose'].includes(m))
    .reduce((sum, m) => sum + product.composition[m], 0);

  return (
    <div className="app">
      {/* Header */}
      <header>
        <div className="header-content">
          <div className="logo">
            <Leaf />
            <h1>EcoFabric Advisor</h1>
          </div>
        </div>
      </header>

      <div className="container" style={{padding: '32px 16px'}}>
        {/* Back Button */}
        <button 
          onClick={() => navigate('/')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'none',
            border: 'none',
            color: '#059669',
            fontSize: '16px',
            cursor: 'pointer',
            marginBottom: '24px',
            fontWeight: '500'
          }}
        >
          <ArrowLeft size={20} />
          Back to Search
        </button>

        {/* Product Detail */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: window.innerWidth > 768 ? '1fr 2fr' : '1fr',
          gap: '48px',
          marginBottom: '48px'
        }}>
          {/* Product Image */}
          <div>
            <img 
              src={product.image} 
              alt={product.title}
              style={{
                width: '100%',
                borderRadius: '12px',
                boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
              }}
            />
            <a 
              href={product.link}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
                marginTop: '16px',
                padding: '12px',
                backgroundColor: '#f3f4f6',
                borderRadius: '8px',
                textDecoration: 'none',
                color: '#374151',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              View on H&M <ExternalLink size={16} />
            </a>
          </div>

          {/* Product Info */}
          <div>
            <h1 style={{fontSize: '32px', fontWeight: 'bold', marginBottom: '8px'}}>
              {product.title}
            </h1>
            <p style={{fontSize: '24px', fontWeight: 'bold', color: '#059669', marginBottom: '24px'}}>
              {product.price}
            </p>

            {/* Current Composition */}
            <div style={{
              backgroundColor: '#fef2f2',
              padding: '24px',
              borderRadius: '12px',
              marginBottom: '24px'
            }}>
              <h3 style={{fontSize: '18px', fontWeight: '600', marginBottom: '16px'}}>
                Current Material Composition
              </h3>
              
              <StackedBar composition={product.composition} height={40} />
              
              <div style={{
                marginTop: '16px',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: '12px'
              }}>
                {Object.entries(product.composition).map(([material, percentage]) => (
                  <div key={material} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '14px'
                  }}>
                    <span style={{color: '#6b7280'}}>{material}</span>
                    <span style={{fontWeight: '600'}}>{percentage}%</span>
                  </div>
                ))}
              </div>

              {currentSynthetic > 0 && (
                <div style={{
                  marginTop: '16px',
                  padding: '12px',
                  backgroundColor: '#fee2e2',
                  borderRadius: '6px',
                  fontSize: '14px',
                  color: '#991b1b'
                }}>
                  ⚠️ Contains {currentSynthetic}% synthetic materials
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Recommendations */}
        <div>
          <h2 style={{fontSize: '28px', fontWeight: 'bold', marginBottom: '24px'}}>
            Recommended Sustainable Alternatives
          </h2>

          <div style={{display: 'grid', gap: '24px'}}>
            {recommendations.map((rec, idx) => (
              <RecommendationCard key={idx} recommendation={rec} rank={idx + 1} />
            ))}
          </div>
        </div>

        {/* Footer Info */}
        <div style={{
          marginTop: '48px',
          padding: '24px',
          backgroundColor: '#f0fdf4',
          borderRadius: '12px'
        }}>
          <h3 style={{fontSize: '18px', fontWeight: '600', marginBottom: '12px'}}>
            💡 Why These Recommendations?
          </h3>
          <p style={{fontSize: '14px', color: '#374151', lineHeight: '1.6'}}>
            We prioritize natural, biodegradable fibers like organic cotton, hemp, and linen over synthetic materials. 
            These alternatives have lower environmental impact (reduced carbon emissions and water usage) while 
            maintaining or improving durability. Hemp, for example, uses 75% less water than conventional cotton 
            and produces 69% less carbon emissions.
          </p>
        </div>
      </div>
    </div>
  );
}

// Stacked Bar Component
function StackedBar({ composition, height = 40 }) {
  const COLORS = {
    'Cotton': '#10b981',
    'Organic Cotton': '#059669',
    'Polyester': '#ef4444',
    'Recycled Polyester': '#f97316',
    'Viscose': '#ec4899',
    'Tencel': '#06b6d4',
    'Hemp': '#84cc16',
    'Linen': '#a3e635',
    'Elastane': '#6366f1',
    'Wool': '#8b5cf6',
    'Organic Wool': '#7c3aed',
    'Acrylic': '#f43f5e',
    'Nylon': '#dc2626',
    'Polyamide': '#dc2626',
    'Recycled Nylon': '#fb923c',
    'Modal': '#14b8a6',
    'Alpaca': '#a855f7',
    'Organic Linen': '#bef264'
  };

  return (
    <div style={{
      width: '100%',
      height: `${height}px`,
      display: 'flex',
      borderRadius: '8px',
      overflow: 'hidden',
      border: '2px solid #e5e7eb',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      {Object.entries(composition).map(([material, percentage]) => (
        <div
          key={material}
          style={{
            width: `${percentage}%`,
            backgroundColor: COLORS[material] || '#9ca3af',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: percentage > 15 ? '12px' : '0',
            fontWeight: '600',
            textShadow: '0 1px 2px rgba(0,0,0,0.3)'
          }}
          title={`${material}: ${percentage}%`}
        >
          {percentage > 15 && `${percentage}%`}
        </div>
      ))}
    </div>
  );
}

// Recommendation Card
function RecommendationCard({ recommendation, rank }) {
  const medals = ['🥇', '🥈', '🥉'];

  return (
    <div style={{
      border: '2px solid #e5e7eb',
      borderRadius: '12px',
      padding: '24px',
      backgroundColor: 'white',
      boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
      transition: 'box-shadow 0.3s'
    }}
    onMouseEnter={(e) => e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.1)'}
    onMouseLeave={(e) => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)'}
    >
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '16px', flexWrap: 'wrap', gap: '16px'}}>
        <div>
          <h4 style={{fontSize: '20px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px'}}>
            <span>{medals[rank - 1]}</span>
            <span>{recommendation.name}</span>
          </h4>
          <p style={{fontSize: '14px', color: '#6b7280'}}>{recommendation.description}</p>
        </div>
        <div style={{textAlign: 'right'}}>
          <div style={{display: 'flex', gap: '12px'}}>
            <div>
              <p style={{fontSize: '20px', fontWeight: 'bold', color: '#059669'}}>
                -{recommendation.carbonSaving}%
              </p>
              <p style={{fontSize: '12px', color: '#6b7280'}}>Carbon</p>
            </div>
            <div>
              <p style={{fontSize: '20px', fontWeight: 'bold', color: '#0891b2'}}>
                -{recommendation.waterSaving}%
              </p>
              <p style={{fontSize: '12px', color: '#6b7280'}}>Water</p>
            </div>
          </div>
        </div>
      </div>

      <div style={{
        backgroundColor: '#f0fdf4',
        padding: '16px',
        borderRadius: '8px'
      }}>
        <StackedBar composition={recommendation.composition} height={40} />
        
        <div style={{
          marginTop: '16px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
          gap: '8px'
        }}>
          {Object.entries(recommendation.composition).map(([material, percentage]) => (
            <div key={material} style={{
              padding: '8px',
              backgroundColor: 'white',
              borderRadius: '6px',
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '12px'
            }}>
              <span style={{fontWeight: '500', color: '#374151'}}>{material}:</span>
              <span style={{color: '#059669', fontWeight: '600'}}>{percentage}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default ProductDetailPage;
    
