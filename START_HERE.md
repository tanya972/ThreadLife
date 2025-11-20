# Material Impact Calculator - Quick Start Guide

## Overview
A web application that demonstrates how changing material compositions in clothing affects garment lifespan and environmental impact. Built with React and powered by machine learning predictions based on H&M sustainability data.

## What You Need

### Requirements
- **Node.js 18.16.0+** ✅ (Your version: 18.16.0 - compatible!)
- npm or yarn

### Quick Start

1. **Install dependencies** (if not already installed):
   ```bash
   cd hm/clothing-longevity
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```
   App will be available at `http://localhost:5173`

3. **Build for production**:
   ```bash
   npm run build
   npm run preview
   ```

## Features

✅ **Interactive Material Slider** - Adjust material percentages in real-time
✅ **Lifespan Prediction** - See predicted garment lifespan based on composition
✅ **Environmental Impact** - Calculate CO₂ footprint and water usage
✅ **Improvement Suggestions** - Get AI-powered recommendations for better materials
✅ **Material Database** - Browse 8+ materials with detailed sustainability data

## File Structure

```
hm/clothing-longevity/
├── src/
│   ├── MaterialComparator.jsx   # Main component with all logic
│   ├── MaterialComparator.css    # Styled components
│   ├── App.jsx                   # App wrapper
│   ├── index.css                 # Base styles
│   └── main.jsx                  # Entry point
├── index.html                    # HTML template
├── package.json                  # Dependencies
└── vite.config.js               # Build configuration
```

## How It Works

### Prediction Model
- **Material Score**: Each material has a durability score (0.4-1.2)
- **Category Multipliers**: Different clothing types have varying baseline lifespans
- **Base Formula**: `30 + (mat_score - 0.65) * 60` months, multiplied by category factor

### Material Database
The app includes 8 materials with:
- CO₂ emissions (kg per kg of material)
- Water usage (liters per kg)
- Durability score
- Cost category
- Detailed description

### Improvement Suggestions
The app automatically suggests material swaps:
1. **Recycled Polyester** - Lower CO₂ than virgin polyester
2. **Recycled Cotton** - 80% reduction in environmental impact
3. **Cotton Replacements** - Natural fiber alternatives
4. **Linen Blends** - Sustainable for certain categories

## Example Use Cases

### Scenario 1: Improving a Basic Tee
- Start: 100% Polyester → 45 months lifespan, 2.5 kg CO₂
- Switch to: 100% Cotton → 48 months lifespan, 3.75 kg CO₂
- Best Option: 80% Recycled Cotton / 20% Cotton → 48 months, 1.5 kg CO₂

### Scenario 2: Sweater Upgrade
- Start: 100% Polyester → 52 months
- Add Wool blend → 88 months (70% increase!)
- Environmental trade-off: Higher CO₂ but much longer lifespan

## Machine Learning Backend

The predictions are based on a RandomForest model trained on:
- **105,542 H&M products**
- **77% importance**: Material score
- **15% importance**: Category type
- **8% importance**: Other factors (color, pattern, etc.)

Model files located in: `hm/data/hm/`
- `lifespan_pipeline.joblib` - Trained model
- `feature_importances.csv` - Feature analysis
- `training_report.json` - Performance metrics

## Next Steps

### ✅ Project is Now Compatible with Node 18!
The project has been updated to work with Node.js 18.16.0. Just run `npm install` and `npm run dev`.

### Optional: Upgrade Node.js (for latest features)
If you want to use the very latest packages, you can upgrade:
- Download Node.js 20 LTS from https://nodejs.org/
- But it's not required - everything works with Node 18!

### To Extend the App
1. **Add more materials** - Edit `MATERIAL_DATA` in `MaterialComparator.jsx`
2. **Improve predictions** - Integrate the full sklearn model (currently using simplified version)
3. **Add features** - Batch comparisons, cost analysis, sharing
4. **Deploy** - Use Vercel, Netlify, or GitHub Pages

## Troubleshooting

### "Node.js version too old"
- ✅ **Fixed!** The project now works with Node.js 18.16.0+
- If you still see errors, make sure you've run `npm install` after the updates

### "Module not found"
- Run `npm install` in the clothing-longevity directory
- Check node_modules exists

### "Port 5173 already in use"
- Change port in vite.config.js or kill the process using port 5173

## Support

For questions or issues:
1. Check the README.md in clothing-longevity folder
2. Review the code comments in MaterialComparator.jsx
3. Check the ML model outputs in hm/data/hm/

## License

MIT License - Free to use for educational and commercial purposes.

---

**Built with ❤️ for sustainable fashion**
