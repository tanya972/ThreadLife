import React, { useState } from 'react';
import { searchProducts } from '../services/hmApi';

function HomePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [allProducts, setAllProducts] = useState([]); // Store all fetched products
  const [displayedProducts, setDisplayedProducts] = useState([]); // Products currently shown
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [itemsPerPage, setItemsPerPage] = useState(5); // Items shown per page
  const [currentPage, setCurrentPage] = useState(1);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    setLoading(true);
    setError(null);
    setCurrentPage(1); // Reset to page 1 on new search

    try {
      console.log(`Searching for "${searchQuery}"`);
      // Fetch more products than we'll show (e.g., fetch 50, show 5 at a time)
      const results = await searchProducts(searchQuery, 50);
      setAllProducts(results);
      
      // Show first page
      const firstPageItems = results.slice(0, itemsPerPage);
      setDisplayedProducts(firstPageItems);
      
      console.log(`Fetched ${results.length} products, showing first ${firstPageItems.length}`);
    } catch (err) {
      console.error('API Error:', err);
      setError('Failed to fetch products. Please try again.');
      setAllProducts([]);
      setDisplayedProducts([]);
    } finally {
      setLoading(false);
    }
  };

  // Handle items per page change
  const handleItemsPerPageChange = (newItemsPerPage) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1); // Reset to page 1
    
    // Update displayed products
    const startIndex = 0;
    const endIndex = newItemsPerPage;
    setDisplayedProducts(allProducts.slice(startIndex, endIndex));
  };

  // Handle page change
  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    
    // Calculate which products to show
    const startIndex = (newPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    setDisplayedProducts(allProducts.slice(startIndex, endIndex));
    
    // Scroll to top of results
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Calculate pagination info
  const totalPages = Math.ceil(allProducts.length / itemsPerPage);
  const startItem = allProducts.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
  const endItem = Math.min(currentPage * itemsPerPage, allProducts.length);

  // Generate page numbers to show
  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 5;
    
    if (totalPages <= maxPagesToShow) {
      // Show all pages if total is small
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Show first page, last page, and pages around current
      if (currentPage <= 3) {
        pages.push(1, 2, 3, 4, '...', totalPages);
      } else if (currentPage >= totalPages - 2) {
        pages.push(1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
      } else {
        pages.push(1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages);
      }
    }
    
    return pages;
  };

  // Inline Styles
  const styles = {
    container: {
      maxWidth: '1400px',
      margin: '0 auto',
      padding: '20px',
      fontFamily: 'Arial, sans-serif'
    },
    header: {
      textAlign: 'center',
      marginBottom: '40px',
      padding: '40px 20px',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      borderRadius: '12px',
      color: 'white'
    },
    searchForm: {
      maxWidth: '800px',
      margin: '0 auto 40px',
      background: 'white',
      padding: '30px',
      borderRadius: '12px',
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
    },
    searchRow: {
      display: 'flex',
      gap: '12px',
      marginBottom: '12px',
      flexWrap: 'wrap'
    },
    searchInput: {
      flex: '1',
      minWidth: '250px',
      padding: '14px 20px',
      fontSize: '1rem',
      border: '2px solid #e0e0e0',
      borderRadius: '8px',
      outline: 'none'
    },
    searchButton: {
      padding: '14px 32px',
      fontSize: '1rem',
      fontWeight: '600',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      whiteSpace: 'nowrap'
    },
    hint: {
      margin: '0',
      fontSize: '0.9rem',
      color: '#666',
      textAlign: 'center'
    },
    error: {
      marginTop: '20px',
      padding: '16px',
      background: '#fee',
      color: '#c33',
      borderRadius: '8px',
      borderLeft: '4px solid #c33'
    },
    loading: {
      textAlign: 'center',
      padding: '60px 20px'
    },
    resultsHeader: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '20px',
      padding: '20px',
      background: 'white',
      borderRadius: '8px',
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.05)',
      flexWrap: 'wrap',
      gap: '12px'
    },
    resultsInfo: {
      fontSize: '1rem',
      color: '#333'
    },
    paginationControls: {
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      flexWrap: 'wrap'
    },
    itemsPerPageLabel: {
      fontSize: '0.9rem',
      color: '#666'
    },
    dropdown: {
      padding: '8px 12px',
      fontSize: '0.9rem',
      border: '2px solid #e0e0e0',
      borderRadius: '6px',
      background: 'white',
      cursor: 'pointer',
      fontWeight: '500'
    },
    productsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
      gap: '24px',
      marginTop: '20px'
    },
    productCard: {
      background: 'white',
      borderRadius: '12px',
      overflow: 'hidden',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
      transition: 'transform 0.3s, box-shadow 0.3s'
    },
    productImage: {
      width: '100%',
      height: '400px',
      objectFit: 'cover'
    },
    productInfo: {
      padding: '20px'
    },
    productTitle: {
      margin: '0 0 8px 0',
      fontSize: '1.2rem',
      fontWeight: '600',
      color: '#333'
    },
    productPrice: {
      margin: '0 0 16px 0',
      fontSize: '1.3rem',
      fontWeight: '700',
      color: '#667eea'
    },
    compositionSection: {
      margin: '16px 0',
      padding: '16px',
      background: '#f8f9ff',
      borderRadius: '8px'
    },
    compositionItem: {
      display: 'flex',
      justifyContent: 'space-between',
      padding: '8px 12px',
      marginBottom: '8px',
      background: 'white',
      borderRadius: '6px',
      borderLeft: '3px solid #667eea'
    },
    viewLink: {
      display: 'inline-block',
      marginTop: '12px',
      padding: '10px 20px',
      background: '#667eea',
      color: 'white',
      textDecoration: 'none',
      borderRadius: '6px',
      fontWeight: '500'
    },
    pagination: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      gap: '8px',
      marginTop: '40px',
      padding: '20px',
      background: 'white',
      borderRadius: '8px',
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.05)',
      flexWrap: 'wrap'
    },
    pageButton: {
      padding: '10px 16px',
      fontSize: '0.95rem',
      border: '2px solid #e0e0e0',
      background: 'white',
      color: '#333',
      borderRadius: '6px',
      cursor: 'pointer',
      fontWeight: '500',
      transition: 'all 0.2s'
    },
    pageButtonActive: {
      padding: '10px 16px',
      fontSize: '0.95rem',
      border: '2px solid #667eea',
      background: '#667eea',
      color: 'white',
      borderRadius: '6px',
      cursor: 'pointer',
      fontWeight: '600'
    },
    pageButtonDisabled: {
      padding: '10px 16px',
      fontSize: '0.95rem',
      border: '2px solid #e0e0e0',
      background: '#f5f5f5',
      color: '#999',
      borderRadius: '6px',
      cursor: 'not-allowed',
      fontWeight: '500'
    },
    ellipsis: {
      padding: '10px 8px',
      color: '#999'
    }
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1>🌿 Sustainable Fashion Tracker</h1>
        <p>Make informed, eco-friendly clothing choices</p>
      </header>

      <div style={styles.searchForm}>
        <form onSubmit={handleSearch}>
          <div style={styles.searchRow}>
            <input
              type="text"
              style={styles.searchInput}
              placeholder="Search for products (e.g., dress, jeans, hoodie)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />

            <button 
              type="submit" 
              style={styles.searchButton}
              disabled={loading}
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
          
          <p style={styles.hint}>
            Try: "dress", "jeans", "hoodie", "jacket" or leave empty for all items
          </p>
        </form>

        {error && <div style={styles.error}>⚠️ {error}</div>}
      </div>

      {loading && (
        <div style={styles.loading}>
          <p>Searching H&M products...</p>
        </div>
      )}

      {!loading && allProducts.length > 0 && (
        <>
          <div style={styles.resultsHeader}>
            <div style={styles.resultsInfo}>
              <strong>Showing {startItem}-{endItem} of {allProducts.length} products</strong>
            </div>
            
            <div style={styles.paginationControls}>
              <label style={styles.itemsPerPageLabel}>Show:</label>
              <select 
                style={styles.dropdown}
                value={itemsPerPage}
                onChange={(e) => handleItemsPerPageChange(Number(e.target.value))}
              >
                <option value="5">5 per page</option>
                <option value="10">10 per page</option>
                <option value="15">15 per page</option>
                <option value="20">20 per page</option>
                <option value="50">50 per page</option>
              </select>
            </div>
          </div>

          <div style={styles.productsGrid}>
            {displayedProducts.map((product) => (
              <div key={product.id} style={styles.productCard}>
                <img 
                  src={product.image} 
                  alt={product.title}
                  style={styles.productImage}
                  onError={(e) => {
                    e.target.src = 'https://via.placeholder.com/400?text=No+Image';
                  }}
                />

                <div style={styles.productInfo}>
                  <h3 style={styles.productTitle}>{product.title}</h3>
                  <p style={styles.productPrice}>{product.price}</p>

                  {product.composition && Object.keys(product.composition).length > 0 && (
                    <div style={styles.compositionSection}>
                      <h4 style={{ margin: '0 0 12px 0', fontSize: '0.95rem' }}>
                        🧵 Material Composition
                      </h4>
                      {Object.entries(product.composition).map(([material, percentage]) => (
                        <div key={material} style={styles.compositionItem}>
                          <span>{material}</span>
                          <strong style={{ color: '#667eea' }}>{percentage}%</strong>
                        </div>
                      ))}
                    </div>
                  )}

                  <a 
                    href={product.link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    style={styles.viewLink}
                  >
                    View on H&M →
                  </a>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={styles.pagination}>
              <button
                style={currentPage === 1 ? styles.pageButtonDisabled : styles.pageButton}
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
              >
                ← Previous
              </button>

              {getPageNumbers().map((page, index) => (
                page === '...' ? (
                  <span key={`ellipsis-${index}`} style={styles.ellipsis}>...</span>
                ) : (
                  <button
                    key={page}
                    style={currentPage === page ? styles.pageButtonActive : styles.pageButton}
                    onClick={() => handlePageChange(page)}
                  >
                    {page}
                  </button>
                )
              ))}

              <button
                style={currentPage === totalPages ? styles.pageButtonDisabled : styles.pageButton}
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default HomePage;
