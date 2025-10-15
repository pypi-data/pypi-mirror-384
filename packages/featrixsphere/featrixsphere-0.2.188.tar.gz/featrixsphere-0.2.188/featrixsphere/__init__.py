"""
Featrix Sphere API Client

Transform any CSV into a production-ready ML model in minutes, not months.

The Featrix Sphere API automatically builds neural embedding spaces from your data 
and trains high-accuracy predictors without requiring any ML expertise. 
Just upload your data, specify what you want to predict, and get a production API endpoint.

🆕 NEW: Beautiful training visualization with matplotlib plotting!

Example:
    >>> from featrixsphere import FeatrixSphereClient
    >>> import pandas as pd
    >>> 
    >>> client = FeatrixSphereClient("http://your-server.com")
    >>> 
    >>> # Upload DataFrame directly
    >>> df = pd.read_csv("data.csv")
    >>> session = client.upload_df_and_create_session(df=df)
    >>> 
    >>> # Or upload CSV file directly (with automatic gzip compression)
    >>> session = client.upload_df_and_create_session(file_path="data.csv")
    >>> 
    >>> # Train a predictor
    >>> client.train_single_predictor(session.session_id, "target_column", "set")
    >>> 
    >>> # Make predictions
    >>> result = client.predict(session.session_id, {"feature": "value"})
    >>> print(result['prediction'])
    >>> 
    >>> # 🎨 NEW: Visualize training progress with beautiful plots!
    >>> fig = client.plot_training_loss(session.session_id, style='notebook')
    >>> # Returns matplotlib Figure - perfect for Jupyter notebooks!
    >>> 
    >>> # Compare multiple training runs
    >>> client.plot_training_comparison(['session1', 'session2'], 
    ...                                labels=['Experiment A', 'Experiment B'])
"""

__version__ = "0.2.188"
__author__ = "Featrix"
__email__ = "support@featrix.com"
__license__ = "MIT"

from .client import FeatrixSphereClient, SessionInfo, PredictionBatch, PredictionGrid

__all__ = [
    "FeatrixSphereClient",
    "SessionInfo", 
    "PredictionBatch",
    "PredictionGrid",
    "__version__",
] 