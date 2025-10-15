# LTVToolkit

Customer Lifetime Value modeling with cohort curves, RFMT, and gradient boosting.

## Installation

```bash
pip install ltvtoolkit
```

For full functionality (XGBoost, LightGBM, Lifetimes):
```bash
pip install ltvtoolkit[full]
```

## Quick Start

```python
import pandas as pd
import asyncio
from ltvtoolkit import run_ltv_model

# Load your transaction data
transactions = pd.read_csv('transactions.csv')

# Required columns: customer_id, order_date, value
# Optional: acquisition_date, acquisition_channel

# Convert to bytes
data_bytes = transactions.to_csv(index=False).encode()

# Run LTV model
async def analyze():
    results = await run_ltv_model(data_bytes)
    return results

results = asyncio.run(analyze())

# Access predictions
customer_predictions = results['individual_files']['ltv_projection_by_customer']
print(customer_predictions)
```

## Features

- **Multi-model ensemble**: Combines cohort curves, gradient boosted trees, and RFMT/BG-NBD models
- **Flexible data formats**: Supports various transaction schemas
- **36-month projections**: Customer and cohort-level LTV forecasts
- **Production-ready**: Comprehensive validation and error handling

## Data Requirements

Your CSV/DataFrame must have:
- `customer_id`: Unique customer identifier
- `order_date`: Transaction date
- `value`: Transaction amount

Optional columns:
- `acquisition_date`: Customer acquisition date
- `acquisition_channel`: Marketing channel

## Output

The model returns a dictionary with:
- `individual_files`: Dict of output datasets
  - `ltv_projection_by_customer`: Customer-level predictions
  - `ltv_projection_by_cohort`: Cohort curves (M0-M36)
  - `ltv_model_performance_metrics`: Performance metrics
  - `ltv_feature_importance`: Feature importance scores
  - And more...
- `summary_file`: Combined summary report

## Use Cases

- Marketing ROI analysis
- Customer segmentation  
- Revenue forecasting
- Channel optimization
- CAC payback analysis

## License

MIT License - see LICENSE file for details.

## Links

- **GitHub**: https://github.com/yourusername/ltvtoolkit
- **PyPI**: https://pypi.org/project/ltvtoolkit/
- **Issues**: https://github.com/yourusername/ltvtoolkit/issues

## Version History

### 0.1.0 (2025-01-XX)
- Initial release
- Cohort revenue curve model
- Gradient boosted trees model
- RFMT/BG-NBD model
- Ensemble prediction strategy