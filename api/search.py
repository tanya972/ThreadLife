from http.server import BaseHTTPRequestHandler
import json
import urllib.parse

def get_mock_products(query=''):
    """Mock H&M products"""
    products = [
        {
            'id': 1,
            'title': 'Cotton Jersey T-shirt',
            'price': '$9.99',
            'image': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400',
            'link': 'https://www2.hm.com',
            'material': 'cotton',
            'category': 't-shirt'
        },
        {
            'id': 2,
            'title': 'Organic Cotton Dress',
            'price': '$29.99',
            'image': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400',
            'link': 'https://www2.hm.com',
            'material': 'organic cotton',
            'category': 'dress'
        },
        {
            'id': 3,
            'title': 'Linen Shirt',
            'price': '$24.99',
            'image': 'https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400',
            'link': 'https://www2.hm.com',
            'material': 'linen',
            'category': 'top'
        },
        {
            'id': 4,
            'title': 'Polyester Jacket',
            'price': '$49.99',
            'image': 'https://images.unsplash.com/photo-1551028719-00167b16eac5?w=400',
            'link': 'https://www2.hm.com',
            'material': 'polyester',
            'category': 'jacket'
        },
        {
            'id': 5,
            'title': 'Cotton Jeans',
            'price': '$39.99',
            'image': 'https://images.unsplash.com/photo-1542272454315-7f6fabf90b1f?w=400',
            'link': 'https://www2.hm.com',
            'material': 'cotton',
            'category': 'jeans'
        },
        {
            'id': 6,
            'title': 'Wool Sweater',
            'price': '$34.99',
            'image': 'https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=400',
            'link': 'https://www2.hm.com',
            'material': 'wool',
            'category': 'sweater'
        }
    ]
    
    if query:
        products = [p for p in products if query.lower() in p['title'].lower() or query.lower() in p['material'].lower()]
    
    return products

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query_components = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(query_components.query)
        search_query = params.get('q', [''])[0]
        
        products = get_mock_products(search_query)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        self.wfile.write(json.dumps(products).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
