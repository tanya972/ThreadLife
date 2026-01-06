import axios from 'axios';

const RAPIDAPI_KEY = '636a52f114msh5e592d08d7fb6eep118b9fjsn4a25d3e20db6';
const RAPIDAPI_HOST = 'apidojo-hm-hennes-mauritz-v1.p.rapidapi.com';

console.log('🔑 Using H&M API with Category Mapping - IMAGE FIX');

const CATEGORY_MAP = {
  'dress': 'ladies_dresses',
  'dresses': 'ladies_dresses',
  'top': 'ladies_tops',
  'tops': 'ladies_tops',
  'shirt': 'ladies_shirts_blouses',
  'blouse': 'ladies_shirts_blouses',
  'jeans': 'ladies_jeans',
  'denim': 'ladies_jeans',
  'pants': 'ladies_trousers',
  'trousers': 'ladies_trousers',
  'skirt': 'ladies_skirts',
  'jacket': 'ladies_jacketscoats',
  'coat': 'ladies_jacketscoats',
  'sweater': 'ladies_cardigansjumpers',
  'cardigan': 'ladies_cardigansjumpers',
  'hoodie': 'ladies_hoodiesswetshirts',
  'sweatshirt': 'ladies_hoodiesswetshirts'
};

export const searchProducts = async (query = '', maxProducts = 5) => {
  console.log(`🔍 Searching H&M for: "${query}" (max ${maxProducts} products)`);

  try {
    const categoryId = getCategoryFromQuery(query);
    console.log(`📂 Using category: ${categoryId}`);

    // STEP 1: Get product list
    const listResponse = await axios({
      method: 'GET',
      url: `https://${RAPIDAPI_HOST}/products/v2/list`,
      params: {
        country: 'us',
        lang: 'en',
        page: 1,
        pageSize: maxProducts,
        categoryId: categoryId,
        sort: 'RELEVANCE'
      },
      headers: {
        'x-rapidapi-host': RAPIDAPI_HOST,
        'x-rapidapi-key': RAPIDAPI_KEY
      },
      timeout: 10000
    });

    const productList = listResponse.data?.plpList?.productList || [];
    console.log(`📦 Found ${productList.length} products in category`);

    if (productList.length === 0) {
      throw new Error('No products found in category');
    }

    // Create a map of article IDs to list data (for images)
    const listDataMap = {};
    productList.forEach(p => {
      const articleId = p.swatches?.[0]?.articleId || p.id;
      if (articleId) {
        listDataMap[articleId] = p;
      }
    });

    const productCodes = Object.keys(listDataMap).slice(0, maxProducts);
    console.log(`📦 Got ${productCodes.length} product codes`);

    // STEP 2: Get details for composition
    const detailPromises = productCodes.map(code => 
      fetchProductDetail(code, listDataMap[code])
    );
    const products = await Promise.all(detailPromises);
    
    const validProducts = products.filter(Boolean);
    console.log(`✅ Got complete details for ${validProducts.length} products`);

    return validProducts;

  } catch (error) {
    console.error('❌ H&M API Error:', error.message);
    throw error;
  }
};

function getCategoryFromQuery(query) {
  if (!query) return 'ladies_all';
  
  const queryLower = query.toLowerCase().trim();
  
  if (CATEGORY_MAP[queryLower]) {
    return CATEGORY_MAP[queryLower];
  }
  
  for (const [term, category] of Object.entries(CATEGORY_MAP)) {
    if (queryLower.includes(term)) {
      return category;
    }
  }
  
  return 'ladies_all';
}

async function fetchProductDetail(productCode, listData) {
  try {
    const response = await axios({
      method: 'GET',
      url: `https://${RAPIDAPI_HOST}/products/detail`,
      params: {
        productcode: productCode,
        country: 'us',
        lang: 'en'
      },
      headers: {
        'x-rapidapi-host': RAPIDAPI_HOST,
        'x-rapidapi-key': RAPIDAPI_KEY
      },
      timeout: 10000
    });

    const data = response.data.product || response.data;

    return {
      id: data.code,
      title: data.name || 'Untitled Product',
      price: formatPrice(data, listData),
      image: getProductImage(listData, data), // Use listData FIRST
      link: data.productUrl || `https://www2.hm.com/en_us/productpage.${data.code}.html`,
      composition: extractComposition(data),
      description: data.description || '',
      category: getCategoryFromData(data)
    };

  } catch (error) {
    console.error(`  ❌ Failed to get details for ${productCode}:`, error.message);
    return null;
  }
}

/**
 * Get product image - prioritize list response data
 */
function getProductImage(listData, detailData) {
  // PRIORITY 1: List response has the best images
  if (listData) {
    if (listData.productImage) {
      console.log('  🖼️ Using productImage from list');
      return listData.productImage;
    }
    if (listData.modelImage) {
      console.log('  🖼️ Using modelImage from list');
      return listData.modelImage;
    }
    if (listData.images?.[0]?.url) {
      console.log('  🖼️ Using images[0] from list');
      return listData.images[0].url;
    }
  }

  // PRIORITY 2: Detail response galleryDetails
  if (detailData?.galleryDetails && detailData.galleryDetails.length > 0) {
    const mainImage = detailData.galleryDetails.find(img => 
      img.assetType === 'DESCRIPTIVESTILLLIFE'
    ) || detailData.galleryDetails[0];
    
    if (mainImage?.baseUrl) {
      console.log('  🖼️ Using galleryDetails from detail');
      return mainImage.baseUrl;
    }
  }

  // PRIORITY 3: Detail response images array
  if (detailData?.images && detailData.images.length > 0) {
    const imageUrl = detailData.images[0].baseUrl || detailData.images[0].url;
    if (imageUrl) {
      console.log('  🖼️ Using images array from detail');
      return imageUrl.startsWith('http') ? imageUrl : `https:${imageUrl}`;
    }
  }

  console.log('  ❌ No image found!');
  return 'https://via.placeholder.com/400?text=No+Image';
}

function formatPrice(detailData, listData) {
  // Try detail response first
  let price = detailData?.whitePrice?.price || 
              detailData?.price?.value || 
              detailData?.redPrice?.value;
  
  // Fallback to list response
  if (!price && listData?.prices?.[0]?.price) {
    price = listData.prices[0].price;
  }
  
  if (price) {
    return `$${parseFloat(price).toFixed(2)}`;
  }
  return '$0.00';
}

function extractComposition(data) {
  const composition = {};

  if (data.compositions && Array.isArray(data.compositions)) {
    const mainComposition = data.compositions.find(c => 
      c.compositionType === 'Shell' || !c.compositionType
    ) || data.compositions[0];

    if (mainComposition && mainComposition.materials) {
      mainComposition.materials.forEach(material => {
        const name = normalizeMaterialName(material.name);
        const percentage = parseFloat(material.percentage);
        
        if (name && !isNaN(percentage) && percentage > 0) {
          composition[name] = Math.round(percentage);
        }
      });
    }
  }

  if (Object.keys(composition).length === 0) {
    return guessComposition(data.name, data.description);
  }

  return composition;
}

function normalizeMaterialName(material) {
  if (!material) return '';
  
  const materialMap = {
    'cotton': 'Cotton',
    'organic cotton': 'Organic Cotton',
    'polyester': 'Polyester',
    'recycled polyester': 'Recycled Polyester',
    'elastane': 'Elastane',
    'spandex': 'Elastane',
    'viscose': 'Viscose',
    'rayon': 'Viscose',
    'nylon': 'Nylon',
    'polyamide': 'Nylon',
    'wool': 'Wool',
    'linen': 'Linen',
    'acrylic': 'Acrylic',
    'modal': 'Modal',
    'tencel': 'Tencel',
    'lyocell': 'Tencel',
    'silk': 'Silk'
  };

  const normalized = material.toLowerCase().trim();
  return materialMap[normalized] || 
         material.charAt(0).toUpperCase() + material.slice(1).toLowerCase();
}

function getCategoryFromData(data) {
  const name = (data.name || '').toLowerCase();
  const desc = (data.description || '').toLowerCase();
  const text = name + ' ' + desc;
  
  if (text.includes('dress')) return 'dress';
  if (text.includes('hoodie') || text.includes('sweatshirt')) return 'hoodie';
  if (text.includes('sweater') || text.includes('cardigan')) return 'sweater';
  if (text.includes('shirt') || text.includes('blouse')) return 'shirt';
  if (text.includes('t-shirt') || text.includes('tee')) return 't-shirt';
  if (text.includes('jean') || text.includes('denim')) return 'jeans';
  if (text.includes('jacket') || text.includes('coat')) return 'jacket';
  
  return 'top';
}

function guessComposition(name, description) {
  const text = ((name || '') + ' ' + (description || '')).toLowerCase();
  
  if (text.includes('cotton') && text.includes('poly')) {
    return { 'Cotton': 60, 'Polyester': 40 };
  }
  if (text.includes('organic cotton')) {
    return { 'Organic Cotton': 100 };
  }
  if (text.includes('cotton')) {
    return { 'Cotton': 100 };
  }
  if (text.includes('denim') || text.includes('jean')) {
    return { 'Cotton': 98, 'Elastane': 2 };
  }
  if (text.includes('linen')) {
    return { 'Linen': 100 };
  }
  if (text.includes('wool')) {
    return { 'Wool': 100 };
  }
  
  return { 'Cotton': 60, 'Polyester': 40 };
}

export default { searchProducts };
