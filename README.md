# 🌿 Sustainable Fashion Tracker

A web application that helps conscious consumers make informed clothing purchase decisions by analyzing fabric composition and providing sustainability recommendations.

## 🎯 Overview

The Sustainable Fashion Tracker empowers users to make environmentally conscious clothing choices by:
- Searching H&M's product catalog
- Analyzing fabric composition
- Providing sustainability ratings based on material impact
- Offering eco-friendly recommendations

**Why This Matters:** The fashion industry accounts for ~10% of global carbon emissions. By helping consumers choose sustainable materials, we can collectively reduce our environmental impact.

## ✨ Features

### Core Functionality
- 🔍 **Product Search** - Browse H&M products by category (dresses, tops, jeans, etc.)
- 🧵 **Material Analysis** - View detailed fabric composition for each item
- 💡 **Smart Recommendations** - Receive suggestions for more sustainable alternatives
- 📊 **Visual Breakdown** - See material composition in an easy-to-read format

**Screenshots:**

| Home Page | Product Results | Material Analysis |
|-----------|----------------|-------------------|
| ![Home](screenshots/home.png) | ![Results](screenshots/search.png) | ![Analysis](screenshots/analysis.png) |

## 🛠️ Tech Stack

### Frontend
- **React** (v18+) - UI framework
- **Axios** - HTTP client for API requests
- **CSS3** - Styling

### APIs
- **H&M Hennes & Mauritz API** (via RapidAPI) - Product data and composition
  - `/products/v2/list` - Product catalog
  - `/products/detail` - Detailed product information

### Development Tools
- **Node.js** (v16+)
- **npm** - Package management
- **Git** - Version control

## 📦 Installation

### Prerequisites
- Node.js (v16 or higher)
- npm or yarn
- RapidAPI account with H&M API subscription

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/sustainable-fashion-tracker.git
   cd sustainable-fashion-tracker
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure API credentials**
   
   Create a `.env` file in the root directory:
   ```env
   REACT_APP_RAPIDAPI_KEY=your_rapidapi_key_here
   REACT_APP_RAPIDAPI_HOST=apidojo-hm-hennes-mauritz-v1.p.rapidapi.com
   ```

   **To get your API key:**
   - Sign up at [RapidAPI](https://rapidapi.com/)
   - Subscribe to [H&M Hennes & Mauritz API](https://rapidapi.com/apidojo/api/hm-hennes-mauritz)
   - Copy your API key from the dashboard

4. **Start the development server**
   ```bash
   npm start
   ```

5. **Open your browser**
   
   Navigate to `http://localhost:3000`

## 🎮 Usage

### Basic Workflow

1. **Search for Products**
   - Enter a search term (e.g., "dress", "jeans", "hoodie")
   - The app maps your search to H&M categories
   - Results display with images and prices

2. **View Material Composition**
   - Click on any product to see detailed fabric breakdown
   - Composition shows percentage of each material

3. **Check Sustainability Score**
   - Each material is rated on environmental impact
   - Overall product score calculated automatically
   - Color-coded ratings (green = good, red = poor)

4. **Get Recommendations**
   - Receive suggestions for more sustainable alternatives
   - Learn about eco-friendly materials

### Search Tips

| Search Term | Returns |
|-------------|---------|
| "dress" | Dresses from ladies_dresses category |
| "jeans" | Denim from ladies_jeans category |
| "hoodie" | Hoodies and sweatshirts |
| "jacket" | Jackets and coats |
| "" (empty) | All ladies items |

### Inspiration & Resources
- [Textile Exchange](https://textileexchange.org/) - Material sustainability data
- [Good On You](https://goodonyou.eco/) - Fashion sustainability ratings
- [Fashion Revolution](https://www.fashionrevolution.org/) - Sustainable fashion movement

### Materials Sustainability Research
- Organic cotton requires 91% less water than conventional cotton
- Recycled polyester reduces carbon emissions by 32% compared to virgin polyester
- Textile production accounts for ~20% of global clean water pollution

## 🔮 Future Enhancements

### Technical Improvements
- [ ] Implement Redis caching
- [ ] Add comprehensive testing (Jest, React Testing Library)
- [ ] Improve accessibility (WCAG 2.1 AA compliance)
- [ ] Add internationalization (i18n)
- [ ] Optimize bundle size
- [ ] Add service worker for offline functionality
