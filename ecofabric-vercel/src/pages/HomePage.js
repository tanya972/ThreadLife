import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Leaf } from 'lucide-react';
import { searchProducts as fetchHMProducts } from '../services/hmApi'; // Rename import

function HomePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSearch = async () => {  // Renamed from searchProducts
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Try real H&M API first
      const results = await fetchHMProducts(searchQuery);
      setProducts(results);
    } catch (error) {
      console.error('API Error:', error);
      setError('Failed to fetch products from H&M. Showing sample products.');
      
      // Fallback to mock data
      const mockProducts = getMockProducts(searchQuery);
      setProducts(mockProducts);
    }
    
    setLoading(false);
  };

  const getMockProducts = (query) => {
    const mockProducts = [
      {
        id: '0970819001',
        title: 'Relaxed Fit T-shirt',
        price: '$9.99',
        image: 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400',
        link: 'https://www2.hm.com',
        composition: { 'Cotton': 100 },
        category: 't-shirt'
      },
      {
        id: '1074406003',
        title: 'Slim Fit Cotton Shirt',
        price: '$17.99',
        image: 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400',
        link: 'https://www2.hm.com',
        composition: { 'Cotton': 97, 'Elastane': 3 },
        category: 'shirt'
      },
      {
        id: '0608945065',
        title: 'Printed Dress',
        price: '$24.99',
        image: 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400',
        link: 'https://www2.hm.com',
        composition: { 'Viscose': 95, 'Elastane': 5 },
        category: 'dress'
      },
      {
        id: '1005941013',
        title: 'Skinny Jeans',
        price: '$29.99',
        image: 'https://images.unsplash.com/photo-1542272454315-7f6fabf90b1f?w=400',
        link: 'https://www2.hm.com',
        composition: { 'Cotton': 79, 'Polyester': 20, 'Elastane': 1 },
        category: 'jeans'
      },
      {
        id: '0685816050',
        title: 'Fine-knit Sweater',
        price: '$19.99',
        image: 'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400',
        link: 'https://www2.hm.com',
        composition: { 'Viscose': 80, 'Polyester': 20 },
        category: 'sweater'
      },
      {
        id: '0714032044',
        title: 'Sports Leggings',
        price: '$14.99',
        image: 'https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=400',
        link: 'https://www2.hm.com',
        composition: { 'Polyester': 73, 'Polyamide': 20, 'Elastane': 7 },
        category: 'activewear'
      },
      {
        id: '0979945001',
        title: 'Linen-blend Shirt',
        price: '$24.99',
        image: 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400',
        link: 'https://www2.hm.com',
        composition: { 'Linen': 55, 'Cotton': 45 },
        category: 'shirt'
      },
      {
        id: '1032572001',
        title: 'Hooded Jacket',
        price: '$39.99',
        image: 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400',
        link: 'https://www2.hm.com',
        composition: { 'Polyester': 100 },
        category: 'jacket'
      }
    ];

    const queryLower = query.toLowerCase();
    return mockProducts.filter(p => 
      p.title.toLowerCase().includes(queryLower) ||
      p.category.toLowerCase().includes(queryLower)
    );
  };

  const handleProductClick = (product) => {
    sessionStorage.setItem('currentProduct', JSON.stringify(product));
    navigate(`/product/${product.id}`);
  };

  return (
    <div className="app">
      {/* Header */}
      <header>
        <div className="header-content">
          <div className="logo">
            <Leaf />
            <h1>EcoFabric Advisor</h1>
          </div>
          <p className="tagline">
            Find sustainable material alternatives for H&M products
          </p>
        </div>
      </header>

      {/* Search Section */}
      <div className="search-section">
        <div className="search-box">
          <h2>Search H&M Products</h2>
          <p style={{textAlign: 'center', color: '#6b7280', fontSize: '14px', marginBottom: '16px'}}>
            Try: "dress", "jeans", "sweater", "cotton shirt"
          </p>
          <div className="search-form">
            <input
              type="text"
              placeholder="Search real H&M products..."
              className="search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="search-button"
            >
              <Search size={20} />
              <span>{loading ? 'Searching...' : 'Search'}</span>
            </button>
          </div>
          {error && (
            <p style={{color: '#ef4444', fontSize: '14px', marginTop: '12px', textAlign: 'center'}}>
              {error}
            </p>
          )}
        </div>
      </div>

      {/* Products Grid */}
      {products.length > 0 && (
        <div className="container">
          <div className="products-section">
            <h3>Search Results ({products.length} items)</h3>
            <div className="products-grid">
              {products.map((product) => (
                <div 
                  key={product.id} 
                  className="product-card"
                  onClick={() => handleProductClick(product)}
                  style={{cursor: 'pointer'}}
                >
                  <img
                    src={product.image}
                    alt={product.title}
                    className="product-image"
                  />
                  <div className="product-content">
                    <h4 className="product-title">{product.title}</h4>
                    <p className="product-price">{product.price}</p>
                    
                    {/* Single Stacked Bar */}
                    <div style={{marginTop: '12px'}}>
                      <div style={{fontSize: '12px', color: '#6b7280', marginBottom: '6px'}}>
                        Material Composition:
                      </div>
                      <StackedBar composition={product.composition} height={20} />
                      
                      {/* Legend */}
                      <div style={{marginTop: '8px', fontSize: '11px', color: '#374151'}}>
                        {Object.entries(product.composition).map(([material, percentage]) => (
                          <div key={material} style={{display: 'flex', justifyContent: 'space-between'}}>
                            <span>{material}</span>
                            <span style={{fontWeight: '600'}}>{percentage}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Stacked Bar Component
function StackedBar({ composition, height = 20 }) {
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
    'Silk': '#ec4899'
  };

  return (
    <div style={{
      width: '100%',
      height: `${height}px`,
      display: 'flex',
      borderRadius: '4px',
      overflow: 'hidden',
      border: '1px solid #e5e7eb'
    }}>
      {Object.entries(composition).map(([material, percentage]) => (
        <div
          key={material}
          style={{
            width: `${percentage}%`,
            backgroundColor: COLORS[material] || '#9ca3af',
            position: 'relative',
            transition: 'all 0.3s'
          }}
          title={`${material}: ${percentage}%`}
        />
      ))}
    </div>
  );
}

export default HomePage;
