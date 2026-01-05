import axios from 'axios';

const RAPIDAPI_KEY = '636a52f114msh5e592d08d7fb6eep118b9fjsn4a25d3e20db6';
const RAPIDAPI_HOST = 'apidojo-hm-hennes-mauritz-v1.p.rapidapi.com';

console.log('🔑 API Key loaded:', RAPIDAPI_KEY ? 'YES ✓' : 'NO ✗');

export const searchProducts = async (query) => {
  console.log('🔍 Searching H&M for:', query);

  if (!RAPIDAPI_KEY || RAPIDAPI_KEY === 'your-fallback-key-here') {
    throw new Error('API key not configured. Please add REACT_APP_RAPIDAPI_KEY to .env file');
  }

  try {
    const response = await axios({
      method: 'GET',
      url: 'https://apidojo-hm-hennes-mauritz-v1.p.rapidapi.com/products/list',
      params: {
        country: 'us',
        lang: 'en',
        currentpage: '0',
        pagesize: '30',
        query: query
      },
      headers: {
        'X-RapidAPI-Key': RAPIDAPI_KEY,
        'X-RapidAPI-Host': RAPIDAPI_HOST
      }
    });

    console.log('✅ Raw API Response:', response);
    console.log('✅ Response Data:', response.data);

    // Handle different response structures
    let productsArray = [];

    // Try different possible data structures
    if (response.data && response.data.results) {
      productsArray = response.data.results;
      console.log('📦 Found results array with', productsArray.length, 'items');
    } else if (response.data && response.data.products) {
      productsArray = response.data.products;
      console.log('📦 Found products array with', productsArray.length, 'items');
    } else if (Array.isArray(response.data)) {
      productsArray = response.data;
      console.log('📦 Response is array with', productsArray.length, 'items');
    } else {
      console.error('❌ Unexpected response structure:', response.data);
      throw new Error('Unexpected API response structure');
    }

    if (!productsArray || productsArray.length === 0) {
      console.warn('⚠️ No products found for:', query);
      throw new Error('No products found');
    }

    // Transform products
    const transformedProducts = productsArray
      .filter(item => item && (item.name || item.title)) // Filter out invalid items
      .map((item, index) => {
        console.log(`📦 Processing item ${index}:`, item);

        return {
          id: getProductId(item, index),
          title: getProductTitle(item),
          price: getProductPrice(item),
          image: getProductImage(item),
          link: getProductLink(item),
          composition: getProductComposition(item),
          category: getProductCategory(item)
        };
      });

    console.log('✅ Successfully transformed', transformedProducts.length, 'products');
    console.log('✅ Sample product:', transformedProducts[0]);

    return transformedProducts;

  } catch (error) {
    console.error('❌ H&M API Error:');
    console.error('  Message:', error.message);
    console.error('  Status:', error.response?.status);
    console.error('  Status Text:', error.response?.statusText);
    console.error('  Response Data:', error.response?.data);
    console.error('  Full Error:', error);

    // Provide helpful error messages
    if (error.response?.status === 403) {
      throw new Error('Not subscribed to H&M API. Please subscribe on RapidAPI.');
    } else if (error.response?.status === 401) {
      throw new Error('Invalid API key. Please check your REACT_APP_RAPIDAPI_KEY in .env file.');
    } else if (error.response?.status === 429) {
      throw new Error('API rate limit exceeded. Please wait or upgrade your plan.');
    }

    throw error;
  }
};

// Helper Functions

function getProductId(item, index) {
  return item.articleCode || 
         item.code || 
         item.id || 
         item.defaultArticle?.code ||
         `product-${index}`;
}

function getProductTitle(item) {
  return item.name || 
         item.title || 
         item.defaultArticle?.name ||
         'Untitled Product';
}

function getProductPrice(item) {
  // Try multiple price fields
  if (item.price?.value) {
    return `$${parseFloat(item.price.value).toFixed(2)}`;
  }
  if (item.price?.formattedValue) {
    return item.price.formattedValue;
  }
  if (item.whitePrice?.value) {
    return `$${parseFloat(item.whitePrice.value).toFixed(2)}`;
  }
  if (item.defaultArticle?.whitePrice?.value) {
    return `$${parseFloat(item.defaultArticle.whitePrice.value).toFixed(2)}`;
  }
  if (typeof item.price === 'string') {
    return item.price;
  }
  if (typeof item.price === 'number') {
    return `$${item.price.toFixed(2)}`;
  }
  return '$0.00';
}

function getProductImage(item) {
  // Try multiple image fields
  const imageUrl = 
    item.images?.[0]?.url ||
    item.images?.[0]?.baseUrl ||
    item.image?.url ||
    item.defaultArticle?.images?.[0]?.url ||
    item.defaultArticle?.images?.[0]?.baseUrl ||
    item.galleryImages?.[0]?.url ||
    item.galleryImages?.[0]?.baseUrl ||
    null;

  if (!imageUrl) {
    return 'https://via.placeholder.com/400?text=No+Image+Available';
  }

  // H&M images might need full URL
  if (imageUrl.startsWith('http')) {
    return imageUrl;
  } else if (imageUrl.startsWith('//')) {
    return 'https:' + imageUrl;
  } else {
    return imageUrl;
  }
}

function getProductLink(item) {
  const articleCode = item.articleCode || item.code || item.defaultArticle?.code;
  if (articleCode) {
    return `https://www2.hm.com/en_us/productpage.${articleCode}.html`;
  }
  return 'https://www2.hm.com';
}

function getProductComposition(item) {
  // Try to extract composition from various fields
  const compositionSources = [
    item.fabricComposition,
    item.composition,
    item.materialComposition,
    item.defaultArticle?.fabricComposition,
    item.articlesList?.[0]?.fabricComposition,
    item.description
  ];

  for (const source of compositionSources) {
    if (source && typeof source === 'string') {
      const parsed = parseCompositionText(source);
      if (Object.keys(parsed).length > 0) {
        console.log('🧵 Found composition:', parsed, 'from:', source);
        return parsed;
      }
    }
  }

  // Fallback: guess from product name
  const productName = item.name || item.title || '';
  console.log('🧵 Guessing composition from name:', productName);
  return guessCompositionFromName(productName);
}

function parseCompositionText(text) {
  const composition = {};
  
  // Remove HTML tags if any
  text = text.replace(/<[^>]*>/g, '');
  
  // Multiple regex patterns to match different formats
  const patterns = [
    /(\d+)%\s*([A-Za-z\s]+?)(?=\s*\d+%|$|,|\.|;)/gi,  // "60% Cotton"
    /([A-Za-z\s]+?)\s*:?\s*(\d+)%/gi,                  // "Cotton: 60%" or "Cotton 60%"
    /([A-Za-z\s]+?)\s+(\d+)\s*%/gi                     // "Cotton 60 %"
  ];

  for (const pattern of patterns) {
    const matches = [...text.matchAll(pattern)];
    
    for (const match of matches) {
      let material, percentage;
      
      // Determine which group is the number
      if (!isNaN(match[1])) {
        percentage = parseInt(match[1]);
        material = match[2];
      } else {
        material = match[1];
        percentage = parseInt(match[2]);
      }

      // Clean and normalize material name
      material = material.trim();
      material = normalizeMaterialName(material);
      
      // Only add valid percentages
      if (percentage > 0 && percentage <= 100 && material) {
        composition[material] = percentage;
      }
    }
    
    // If we found valid composition, stop trying other patterns
    if (Object.keys(composition).length > 0) {
      break;
    }
  }

  // Normalize percentages to sum to 100
  const total = Object.values(composition).reduce((sum, val) => sum + val, 0);
  if (total > 0 && total !== 100) {
    Object.keys(composition).forEach(key => {
      composition[key] = Math.round((composition[key] / total) * 100);
    });
  }

  return composition;
}

function normalizeMaterialName(material) {
  // Remove extra spaces and convert to title case
  material = material.trim().replace(/\s+/g, ' ');
  
  const materialMap = {
    'cotton': 'Cotton',
    'organic cotton': 'Organic Cotton',
    'polyester': 'Polyester',
    'recycled polyester': 'Recycled Polyester',
    'viscose': 'Viscose',
    'rayon': 'Viscose',
    'elastane': 'Elastane',
    'spandex': 'Elastane',
    'lycra': 'Elastane',
    'nylon': 'Nylon',
    'polyamide': 'Polyamide',
    'wool': 'Wool',
    'merino': 'Wool',
    'linen': 'Linen',
    'acrylic': 'Acrylic',
    'modal': 'Modal',
    'tencel': 'Tencel',
    'lyocell': 'Tencel',
    'silk': 'Silk'
  };

  const normalized = material.toLowerCase();
  return materialMap[normalized] || material.charAt(0).toUpperCase() + material.slice(1).toLowerCase();
}

function guessCompositionFromName(name) {
  const nameLower = name.toLowerCase();
  
  // Look for material keywords in product name
  if (nameLower.includes('cotton') && nameLower.includes('poly')) {
    return { 'Cotton': 65, 'Polyester': 35 };
  }
  if (nameLower.includes('organic cotton')) {
    return { 'Organic Cotton': 100 };
  }
  if (nameLower.includes('cotton')) {
    return { 'Cotton': 100 };
  }
  if (nameLower.includes('denim') || nameLower.includes('jean')) {
    return { 'Cotton': 98, 'Elastane': 2 };
  }
  if (nameLower.includes('linen')) {
    return { 'Linen': 100 };
  }
  if (nameLower.includes('wool')) {
    return { 'Wool': 100 };
  }
  if (nameLower.includes('silk')) {
    return { 'Silk': 100 };
  }
  if (nameLower.includes('polyester')) {
    return { 'Polyester': 100 };
  }
  if (nameLower.includes('viscose')) {
    return { 'Viscose': 100 };
  }
  if (nameLower.includes('knit') || nameLower.includes('sweater')) {
    return { 'Acrylic': 50, 'Polyester': 30, 'Wool': 20 };
  }
  
  // Default blend
  return { 'Cotton': 60, 'Polyester': 40 };
}

function getProductCategory(item) {
  const sources = [
    item.categoryName,
    item.category,
    item.name,
    item.title,
    item.defaultArticle?.categoryName
  ].filter(Boolean);

  for (const source of sources) {
    const nameLower = source.toLowerCase();
    
    if (nameLower.includes('dress')) return 'dress';
    if (nameLower.includes('sweater') || nameLower.includes('cardigan') || nameLower.includes('knit') || nameLower.includes('jumper')) return 'sweater';
    if (nameLower.includes('shirt') || nameLower.includes('blouse')) return 'shirt';
    if (nameLower.includes('t-shirt') || nameLower.includes('tee') || nameLower.includes('tank')) return 't-shirt';
    if (nameLower.includes('jean') || nameLower.includes('denim')) return 'jeans';
    if (nameLower.includes('jacket') || nameLower.includes('coat') || nameLower.includes('blazer')) return 'jacket';
    if (nameLower.includes('trouser') || nameLower.includes('pant') || nameLower.includes('chino')) return 'pants';
    if (nameLower.includes('skirt')) return 'skirt';
    if (nameLower.includes('short')) return 'shorts';
    if (nameLower.includes('legging')) return 'activewear';
  }
  
  return 'top';
}

export default { searchProducts };
