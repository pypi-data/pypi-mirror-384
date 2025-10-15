"""
LTVToolkit - Customer Lifetime Value Modeling
Simple wrapper around the core LTV analyzer
"""

from ._version import __version__
from .core import AdvancedLTVAnalyzer, run_ltv_model, run_ltv_model_with_saving, run_ltv_forecast

class LTVModel:
    """
    Simple wrapper for LTV analysis.
    
    Example:
        >>> import pandas as pd
        >>> from ltvtoolkit import LTVModel
        >>> 
        >>> transactions = pd.read_csv('transactions.csv')
        >>> model = LTVModel()
        >>> results = model.fit(transactions)
        >>> predictions = results['individual_files']['ltv_projection_by_customer']
    """
    
    def __init__(self):
        self.analyzer = AdvancedLTVAnalyzer()
        self._fitted = False
    
    async def fit(self, transactions_bytes):
        """Fit the model on transaction data (bytes or DataFrame)"""
        if hasattr(transactions_bytes, 'to_csv'):
            # If DataFrame, convert to bytes
            transactions_bytes = transactions_bytes.to_csv(index=False).encode()
        
        results = await run_ltv_model(transactions_bytes)
        self._fitted = True
        return results
    
    async def fit_and_save(self, transactions_bytes):
        """Fit the model and return saveable format"""
        if hasattr(transactions_bytes, 'to_csv'):
            transactions_bytes = transactions_bytes.to_csv(index=False).encode()
        
        results, model_data = await run_ltv_model_with_saving(transactions_bytes, save_model=True)
        self._fitted = True
        return results, model_data

# Also expose core functions directly
__all__ = [
    '__version__',
    'LTVModel',
    'AdvancedLTVAnalyzer',
    'run_ltv_model',
    'run_ltv_model_with_saving', 
    'run_ltv_forecast'
]