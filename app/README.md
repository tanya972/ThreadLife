# Material Impact Calculator

A web application that demonstrates how changing material compositions in clothing can affect both garment lifespan and environmental impact.

## Features

- **Interactive Material Slider**: Adjust material percentages to see real-time impact calculations
- **Lifespan Prediction**: Predict garment lifespan based on material composition using a simplified ML model
- **Environmental Impact**: Calculate CO₂ footprint and water usage for different material combinations
- **Improvement Suggestions**: Get AI-powered recommendations for more sustainable material swaps
- **Material Reference**: Browse an extensive database of materials with their environmental data

## How It Works

The app uses a simplified prediction model based on material scoring:
- **Material Score**: Each material has a durability score (0.4-1.2) that affects predicted lifespan
- **Category Multipliers**: Different clothing categories have varying baseline lifespans
- **Weighted Composition**: Material scores are weighted by their percentage in the garment

## Getting Started

### Install Dependencies
```bash
npm install
```

### Run Development Server
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production
```bash
npm run build
```

## Material Database

The app includes data on:
- Cotton & Recycled Cotton
- Polyester & Recycled Polyester (rPET)
- Wool
- Linen
- Elastane/Spandex
- Nylon

Each material includes:
- CO₂ emissions (kg per kg of material)
- Water usage (liters per kg)
- Durability score
- Cost category
- Description

## Technical Stack

- **React 19** - UI framework
- **Vite** - Build tool and dev server
- **Custom CSS** - Styled components without external dependencies

## Model Details

The prediction model is based on feature importances from a RandomForest regressor trained on 105,542 H&M products:
- Material score is the dominant factor (77% importance)
- Category effects account for additional variance
- Base lifespan calculation: `30 + (mat_score - 0.65) * 60` months
- Category multipliers adjust final predictions

## License

MIT License - feel free to use this for educational and commercial purposes.

## Contributing

Contributions welcome! Areas for improvement:
- Additional material types
- More sophisticated prediction models
- Batch comparison features
- Export/sharing functionality
- Cost analysis
