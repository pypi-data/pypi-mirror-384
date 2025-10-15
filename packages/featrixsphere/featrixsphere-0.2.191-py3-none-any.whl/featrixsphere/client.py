#!/usr/bin/env python3
"""
Featrix Sphere API Client

A simple Python client for testing the Featrix Sphere API endpoints,
with a focus on the new single predictor functionality.
"""

import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
import gzip
import os
import random
import ssl
from urllib3.exceptions import SSLError as Urllib3SSLError
import base64
import hashlib
import numpy as np
from datetime import datetime

# Optional imports for plotting functionality
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    mdates = None

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    from IPython.display import HTML, display
    from ipywidgets import interact, widgets, Layout
    HAS_IPYWIDGETS = True
except ImportError:
    HAS_IPYWIDGETS = False

import warnings


@dataclass
class SessionInfo:
    """Container for session information."""
    session_id: str
    session_type: str
    status: str
    jobs: Dict[str, Any]
    job_queue_positions: Dict[str, Any]


class PredictionBatch:
    """
    Cached prediction batch that allows instant lookups after initial batch processing.
    
    Usage:
        # First run - populate cache
        batch = client.predict_batch(session_id, records)
        
        # Second run - instant cache lookups
        for i in values1:
            for j in values2:
                record = {"param1": i, "param2": j}
                result = batch.predict(record)  # Instant!
    """
    
    def __init__(self, session_id: str, client: 'FeatrixSphereClient', target_column: str = None):
        self.session_id = session_id
        self.client = client
        self.target_column = target_column
        self._cache = {}  # record_hash -> prediction_result
        self._stats = {'hits': 0, 'misses': 0, 'populated': 0}
        
    def _hash_record(self, record: Dict[str, Any]) -> str:
        """Create a stable hash for a record to use as cache key."""
        # Sort keys for consistent hashing
        sorted_items = sorted(record.items())
        record_str = json.dumps(sorted_items, sort_keys=True)
        return hashlib.md5(record_str.encode()).hexdigest()
    
    def predict(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get prediction for a record from cache, or return cache miss info.
        
        Args:
            record: Record dictionary to predict
            
        Returns:
            Prediction result if cached, or cache miss information
        """
        record_hash = self._hash_record(record)
        
        if record_hash in self._cache:
            self._stats['hits'] += 1
            return self._cache[record_hash]
        else:
            self._stats['misses'] += 1
            return {
                'cache_miss': True,
                'record': record,
                'suggestion': 'Record not found in batch cache. Add to records list and recreate batch.'
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'populated_records': self._stats['populated'],
            'cache_hits': self._stats['hits'],
            'cache_misses': self._stats['misses'],
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }
    
    def _populate_cache(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Populate the cache with batch predictions."""
        if not records:
            return {'summary': {'total_records': 0, 'successful': 0, 'failed': 0}}
        
        print(f"🚀 Creating prediction batch for {len(records)} records...")
        
        # Use existing batch prediction system
        batch_results = self.client.predict_records(
            session_id=self.session_id,
            records=records,
            target_column=self.target_column,
            show_progress_bar=True
        )
        
        # Populate cache with results
        predictions = batch_results.get('predictions', [])
        successful = 0
        failed = 0
        
        for prediction in predictions:
            row_index = prediction.get('row_index', 0)
            if row_index < len(records):
                record = records[row_index]
                record_hash = self._hash_record(record)
                self._cache[record_hash] = prediction
                
                if prediction.get('prediction') is not None:
                    successful += 1
                else:
                    failed += 1
        
        self._stats['populated'] = len(self._cache)
        
        print(f"✅ Batch cache populated: {successful} successful, {failed} failed")
        print(f"💾 Cache ready for instant lookups with batch.predict(record)")
        
        return batch_results


class FeatrixSphereClient:
    """Client for interacting with the Featrix Sphere API."""
    
    def __init__(self, base_url: str = "https://sphere-api.featrix.com", 
                 default_max_retries: int = 5, 
                 default_timeout: int = 30,
                 retry_base_delay: float = 2.0,
                 retry_max_delay: float = 60.0,
                 compute_cluster: str = None):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API server
            default_max_retries: Default number of retries for failed requests
            default_timeout: Default timeout for requests in seconds
            retry_base_delay: Base delay for exponential backoff in seconds
            retry_max_delay: Maximum delay for exponential backoff in seconds
            compute_cluster: Compute cluster port (e.g., "8001") for X-Sphere-Compute header
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        # Set a reasonable timeout
        self.session.timeout = default_timeout
        
        # Retry configuration
        self.default_max_retries = default_max_retries
        self.retry_base_delay = retry_base_delay
        self.retry_max_delay = retry_max_delay
        
        # Compute cluster configuration
        self.compute_cluster = compute_cluster
        if compute_cluster:
            self.session.headers.update({'X-Sphere-Compute': compute_cluster})
        
        # Prediction queue and rate tracking
        self._prediction_queues = {}  # session_id -> list of queued records
        self._prediction_call_times = {}  # session_id -> list of recent call timestamps
        self._last_warning_time = {}  # session_id -> last warning timestamp
        self._rate_warning_threshold = 3  # calls per second
        self._warning_cooldown = 300  # 5 minutes in seconds
        
        # Prediction cache for predict_from_cache() functionality
        self._prediction_cache = {}  # session_id -> {record_hash: prediction_result}
        self._cache_mode = {}  # session_id -> 'populate' or 'fetch'
        self._cache_stats = {}  # session_id -> {hits: int, misses: int, populated: int}
    
    def set_compute_cluster(self, cluster: str) -> None:
        """
        Set the compute cluster for all subsequent API requests.
        
        Args:
            cluster: Compute cluster port (e.g., "8001") or None to use default cluster
            
        Examples:
            client.set_compute_cluster("8001")  # Use cluster on port 8001
            client.set_compute_cluster("8002")  # Switch to cluster on port 8002
            client.set_compute_cluster(None)    # Use default cluster
        """
        self.compute_cluster = cluster
        if cluster:
            self.session.headers.update({'X-Sphere-Compute': cluster})
        else:
            # Remove the header if cluster is None
            self.session.headers.pop('X-Sphere-Compute', None)
    
    def _make_request(self, method: str, endpoint: str, max_retries: int = None, **kwargs) -> requests.Response:
        """
        Make an HTTP request with comprehensive error handling and retry logic.
        
        Retries on:
        - 500 Internal Server Error with connection patterns (server restarting)
        - 503 Service Unavailable
        - SSL/TLS errors  
        - Connection errors
        - Timeout errors
        - Other transient network errors
        """
        if max_retries is None:
            max_retries = self.default_max_retries
            
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(max_retries + 1):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response
                
            except requests.exceptions.HTTPError as e:
                if e.response is not None:
                    status_code = e.response.status_code
                    response_text = e.response.text
                    
                    # Check for server restart patterns in 500 errors
                    is_server_restarting = False
                    if status_code == 500:
                        restart_patterns = [
                            'connection refused',
                            'failed to establish a new connection',
                            'httpconnectionpool',
                            'max retries exceeded',
                            'newconnectionerror',
                            'connection aborted',
                            'bad gateway',
                            'gateway timeout'
                        ]
                        response_lower = response_text.lower()
                        is_server_restarting = any(pattern in response_lower for pattern in restart_patterns)
                    
                    # Retry on 503 Service Unavailable or 500 with server restart patterns
                    if (status_code == 503 or (status_code == 500 and is_server_restarting)) and attempt < max_retries:
                        wait_time = self._calculate_backoff(attempt)
                        if status_code == 503:
                            print(f"503 Service Unavailable, retrying in {wait_time:.1f}s... (attempt {attempt + 1}/{max_retries + 1})")
                        else:
                            print(f"🔄 Server restarting (500 error), retrying in {wait_time:.1f}s... (attempt {attempt + 1}/{max_retries + 1})")
                        time.sleep(wait_time)
                        continue
                
                # Re-raise for other status codes or final attempt
                print(f"API request failed: {method} {url}")
                print(f"HTTP Error: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response status: {e.response.status_code}")
                    print(f"Response body: {e.response.text[:500]}")
                raise
                    
            except (requests.exceptions.SSLError, ssl.SSLError, Urllib3SSLError) as e:
                # Retry on SSL/TLS errors (often transient)
                if attempt < max_retries:
                    wait_time = self._calculate_backoff(attempt)
                    print(f"SSL/TLS error, retrying in {wait_time:.1f}s... (attempt {attempt + 1}/{max_retries + 1})")
                    print(f"SSL Error details: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"API request failed after {max_retries + 1} attempts: {method} {url}")
                    print(f"SSL Error: {e}")
                    raise
                    
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                # Retry on connection errors and timeouts
                if attempt < max_retries:
                    wait_time = self._calculate_backoff(attempt)
                    error_type = "Connection" if isinstance(e, requests.exceptions.ConnectionError) else "Timeout"
                    print(f"{error_type} error, retrying in {wait_time:.1f}s... (attempt {attempt + 1}/{max_retries + 1})")
                    print(f"Error details: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"API request failed after {max_retries + 1} attempts: {method} {url}")
                    print(f"Connection/Timeout Error: {e}")
                    raise
                    
            except requests.exceptions.RequestException as e:
                # For other request exceptions, retry if they might be transient
                error_msg = str(e).lower()
                is_transient = any(keyword in error_msg for keyword in [
                    'temporary failure', 'name resolution', 'network', 'reset', 
                    'broken pipe', 'connection aborted', 'bad gateway', 'gateway timeout'
                ])
                
                if is_transient and attempt < max_retries:
                    wait_time = self._calculate_backoff(attempt)
                    print(f"Transient network error, retrying in {wait_time:.1f}s... (attempt {attempt + 1}/{max_retries + 1})")
                    print(f"Error details: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"API request failed: {method} {url}")
                    print(f"Request Error: {e}")
                    raise
    
    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff with jitter.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay time in seconds with jitter applied
        """
        # Exponential backoff: base_delay * (2 ^ attempt)
        delay = self.retry_base_delay * (2 ** attempt)
        
        # Cap at max_delay
        delay = min(delay, self.retry_max_delay)
        
        # Add jitter (±25% randomization)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        
        return max(0.1, delay + jitter)  # Ensure minimum 0.1s delay
    
    def _track_prediction_call(self, session_id: str) -> bool:
        """
        Track prediction call rate and return True if warning should be shown.
        
        Args:
            session_id: Session ID to track
            
        Returns:
            True if rate warning should be displayed
        """
        current_time = time.time()
        
        # Initialize tracking for this session if needed
        if session_id not in self._prediction_call_times:
            self._prediction_call_times[session_id] = []
        
        # Add current call time
        self._prediction_call_times[session_id].append(current_time)
        
        # Keep only calls from the last second
        cutoff_time = current_time - 1.0
        self._prediction_call_times[session_id] = [
            t for t in self._prediction_call_times[session_id] if t > cutoff_time
        ]
        
        # Check if we're over the rate threshold
        call_count = len(self._prediction_call_times[session_id])
        if call_count > self._rate_warning_threshold:
            # Check if we should show warning (cooldown period)
            last_warning = self._last_warning_time.get(session_id, 0)
            if current_time - last_warning > self._warning_cooldown:
                self._last_warning_time[session_id] = current_time
                return True
        
        return False
    
    def _show_batching_warning(self, session_id: str, call_rate: float):
        """Show warning about using queue_batches for high-frequency predict() calls."""
        print("⚠️  " + "="*70)
        print("⚠️  HIGH-FREQUENCY PREDICTION DETECTED")
        print("⚠️  " + "="*70)
        print(f"📊 Current rate: {call_rate:.1f} predict() calls/second")
        print("🚀 For better performance, consider using queue_batches=True:")
        print()
        print("   # Instead of:")
        print("   for record in records:")
        print("       result = client.predict(session_id, record)")
        print()
        print("   # Use queued batching:")
        print("   for record in records:")
        print("       client.predict(session_id, record, queue_batches=True)")
        print("   results = client.flush_predict_queues(session_id)")
        print()
        print("💡 Benefits:")
        print("   • 5-20x faster for multiple predictions")
        print("   • Automatic batching with optimal chunk sizes")
        print("   • Maintains clean loop structure in your code")
        print("   • Reduces API overhead and server load")
        print()
        print("📚 See client documentation for more details.")
        print("⚠️  " + "="*70)
    
    def _add_to_prediction_queue(self, session_id: str, record: Dict[str, Any], 
                                target_column: str = None, predictor_id: str = None) -> str:
        """
        Add a record to the prediction queue.
        
        Args:
            session_id: Session ID
            record: Record to queue for prediction
            target_column: Target column for prediction
            
        Returns:
            Queue ID for this record
        """
        if session_id not in self._prediction_queues:
            self._prediction_queues[session_id] = []
        
        # Generate unique queue ID for this record
        queue_id = f"queue_{len(self._prediction_queues[session_id])}_{int(time.time()*1000)}"
        
        queued_record = {
            'queue_id': queue_id,
            'record': record,
            'target_column': target_column,
            'predictor_id': predictor_id,
            'timestamp': time.time()
        }
        
        self._prediction_queues[session_id].append(queued_record)
        return queue_id
    
    def _get_json(self, endpoint: str, max_retries: int = None, **kwargs) -> Dict[str, Any]:
        """Make a GET request and return JSON response."""
        response = self._make_request("GET", endpoint, max_retries=max_retries, **kwargs)
        return response.json()
    
    def _post_json(self, endpoint: str, data: Dict[str, Any] = None, max_retries: int = None, **kwargs) -> Dict[str, Any]:
        """Make a POST request with JSON data and return JSON response."""
        if data is not None:
            kwargs['json'] = data
        response = self._make_request("POST", endpoint, max_retries=max_retries, **kwargs)
        return response.json()
    
    def _delete_json(self, endpoint: str, max_retries: int = None, **kwargs) -> Dict[str, Any]:
        """Make a DELETE request and return JSON response."""
        response = self._make_request("DELETE", endpoint, max_retries=max_retries, **kwargs)
        return response.json()

    # =========================================================================
    # Session Management
    # =========================================================================
    
    def create_session(self, session_type: str = "sphere", metadata: Dict[str, Any] = None) -> SessionInfo:
        """
        Create a new session.
        
        Args:
            session_type: Type of session to create ('sphere', 'predictor', etc.)
            metadata: Optional metadata to store with the session (e.g., future target columns)
            
        Returns:
            SessionInfo object with session details
        """
        print(f"Creating {session_type} session...")
        
        # Prepare request data
        request_data = {}
        if metadata:
            request_data['metadata'] = metadata
            print(f"Session metadata: {metadata}")
        
        # Send request with optional metadata
        response_data = self._post_json("/session", request_data)
        
        session_id = response_data.get('session_id')
        print(f"Created session: {session_id}")
        
        return SessionInfo(
            session_id=session_id,
            session_type=response_data.get('session_type', 'sphere'),
            status=response_data.get('status', 'unknown'),
            jobs={},
            job_queue_positions={}
        )
    
    def get_session_status(self, session_id: str, max_retries: int = None) -> SessionInfo:
        """
        Get detailed session status.
        
        Args:
            session_id: ID of the session
            max_retries: Override default retry count (useful during server restarts)
            
        Returns:
            SessionInfo object with current session details
        """
        # Use higher retry count for session endpoints during server restarts
        if max_retries is None:
            max_retries = max(8, self.default_max_retries)
            
        response_data = self._get_json(f"/session/{session_id}", max_retries=max_retries)
        
        session = response_data.get('session', {})
        jobs = response_data.get('jobs', {})
        positions = response_data.get('job_queue_positions', {})
        
        return SessionInfo(
            session_id=session.get('session_id', session_id),
            session_type=session.get('session_type', 'unknown'),
            status=session.get('status', 'unknown'),
            jobs=jobs,
            job_queue_positions=positions
        )
    
    def get_session_models(self, session_id: str, max_retries: int = None) -> Dict[str, Any]:
        """
        Get available models and embedding spaces for a session.
        
        Args:
            session_id: ID of the session
            max_retries: Override default retry count (useful during server restarts)
            
        Returns:
            Dictionary containing available models, their metadata, and summary information
        """
        print(f"Getting available models for session {session_id}")
        
        # Use higher retry count for session endpoints during server restarts
        if max_retries is None:
            max_retries = max(8, self.default_max_retries)
            
        response_data = self._get_json(f"/session/{session_id}/models", max_retries=max_retries)
        
        models = response_data.get('models', {})
        summary = response_data.get('summary', {})
        
        print(f"Available models: {summary.get('available_model_types', [])}")
        print(f"Training complete: {'✅' if summary.get('training_complete') else '❌'}")
        print(f"Prediction ready: {'✅' if summary.get('prediction_ready') else '❌'}")
        print(f"Similarity search ready: {'✅' if summary.get('similarity_search_ready') else '❌'}")
        print(f"Visualization ready: {'✅' if summary.get('visualization_ready') else '❌'}")
        
        return response_data
    
    def wait_for_session_completion(self, session_id: str, max_wait_time: int = 3600, 
                                   check_interval: int = 10, show_live_training_movie: bool = None,
                                   training_interval_movie: int = 3) -> SessionInfo:
        """
        Wait for a session to complete, with smart progress display.
        
        Args:
            session_id: ID of the session to monitor
            max_wait_time: Maximum time to wait in seconds
            check_interval: How often to check status in seconds
            show_live_training_movie: If True, show live training visualization as epochs progress.
                                    If None, auto-enable in notebook environments (default: None)
            training_interval_movie: Show training movie updates every N epochs (default: 3)
            
        Returns:
            Final SessionInfo when session completes or times out
        """
        # Auto-enable live training movie in notebooks if not explicitly set
        if show_live_training_movie is None:
            show_live_training_movie = self._is_notebook()
            
        return self._wait_with_smart_display(session_id, max_wait_time, check_interval, 
                                           show_live_training_movie, training_interval_movie)
    
    def wait_for_training(self, session_id: str, max_wait_time: int = 3600, 
                         check_interval: int = 10, show_live_training_movie: bool = None,
                         training_interval_movie: int = 3) -> SessionInfo:
        """
        Alias for wait_for_session_completion with live training movie support.
        
        Args:
            session_id: ID of the session to monitor
            max_wait_time: Maximum time to wait in seconds
            check_interval: How often to check status in seconds
            show_live_training_movie: If True, show live training visualization as epochs progress.
                                    If None, auto-enable in notebook environments (default: None)
            training_interval_movie: Show training movie updates every N epochs (default: 3)
            
        Returns:
            Final SessionInfo when session completes or times out
        """
        return self.wait_for_session_completion(session_id, max_wait_time, check_interval, 
                                              show_live_training_movie, training_interval_movie)
    
    def _is_notebook(self) -> bool:
        """Detect if running in a Jupyter notebook."""
        try:
            from IPython import get_ipython
            ipython = get_ipython()
            return ipython is not None and hasattr(ipython, 'kernel')
        except ImportError:
            return False
    
    def _has_rich(self) -> bool:
        """Check if rich library is available."""
        try:
            import rich
            return True
        except ImportError:
            return False
    
    def _wait_with_smart_display(self, session_id: str, max_wait_time: int, check_interval: int, show_live_training_movie: bool = False, training_interval_movie: int = 3) -> SessionInfo:
        """Smart progress display that adapts to environment."""
        
        if self._is_notebook():
            return self._wait_with_notebook_display(session_id, max_wait_time, check_interval, show_live_training_movie, training_interval_movie)
        elif self._has_rich():
            return self._wait_with_rich_display(session_id, max_wait_time, check_interval, training_interval_movie)
        else:
            return self._wait_with_simple_display(session_id, max_wait_time, check_interval)
    
    def _wait_with_notebook_display(self, session_id: str, max_wait_time: int, check_interval: int, show_live_training_movie: bool = False, training_interval_movie: int = 3) -> SessionInfo:
        """Notebook-optimized display with clean updates and optional live training visualization."""
        try:
            from IPython.display import clear_output, display, HTML
            import time
            
            print(f"🚀 Monitoring session {session_id}")
            if show_live_training_movie:
                print("🎬 Live training visualization enabled - will show embedding space evolution as epochs progress")
            
            start_time = time.time()
            
            # Live training movie state
            live_viz_state = {
                'last_es_epoch_count': 0,
                'last_sp_epoch_count': 0,
                'training_metrics': None,
                'epoch_projections': {},
                'plot_initialized': False
            } if show_live_training_movie else None
            
            while time.time() - start_time < max_wait_time:
                session_info = self.get_session_status(session_id)
                
                # Clear previous output and show updated status
                clear_output(wait=True)
                
                elapsed = int(time.time() - start_time)
                mins, secs = divmod(elapsed, 60)
                
                html_content = f"""
                <h3>🚀 Session {session_id}</h3>
                <p><strong>Status:</strong> {session_info.status} | <strong>Elapsed:</strong> {mins:02d}:{secs:02d}</p>
                """
                
                if session_info.jobs:
                    html_content += "<h4>Jobs:</h4><ul>"
                    for job_id, job in session_info.jobs.items():
                        job_status = job.get('status', 'unknown')
                        progress = job.get('progress')
                        job_type = job.get('type', job_id.split('_')[0])
                        
                        if progress is not None:
                            progress_pct = progress * 100
                            progress_bar = "▓" * int(progress_pct / 5) + "░" * (20 - int(progress_pct / 5))
                            html_content += f"<li><strong>{job_type}:</strong> {job_status} [{progress_bar}] {progress_pct:.1f}%</li>"
                        else:
                            status_emoji = "✅" if job_status == "done" else "🔄" if job_status == "running" else "❌"
                            html_content += f"<li>{status_emoji} <strong>{job_type}:</strong> {job_status}</li>"
                    html_content += "</ul>"
                
                display(HTML(html_content))
                
                # Live training movie update
                if show_live_training_movie and live_viz_state:
                    try:
                        # Check if we have ES training or single predictor training running
                        has_es_training = any('train_es' in job_id and job.get('status') == 'running' 
                                            for job_id, job in session_info.jobs.items())
                        has_sp_training = any('train_single_predictor' in job_id and job.get('status') == 'running' 
                                            for job_id, job in session_info.jobs.items())
                        
                        if has_es_training or has_sp_training:
                            self._update_live_training_movie(session_id, live_viz_state, training_interval_movie)
                    except Exception as e:
                        print(f"⚠️ Live visualization error: {e}")
                
                # Check completion
                if session_info.status in ['done', 'failed', 'cancelled']:
                    if show_live_training_movie and live_viz_state and live_viz_state['plot_initialized']:
                        print("🎬 Training completed - final visualization available via plot_training_movie()")
                    print(f"✅ Session completed with status: {session_info.status}")
                    return session_info
                
                if session_info.jobs:
                    terminal_states = {'done', 'failed', 'cancelled'}
                    all_jobs_terminal = all(job.get('status') in terminal_states for job in session_info.jobs.values())
                    if all_jobs_terminal:
                        if show_live_training_movie and live_viz_state and live_viz_state['plot_initialized']:
                            print("🎬 Training completed - final visualization available via plot_training_movie()")
                        job_summary = self._analyze_job_completion(session_info.jobs)
                        print(f"✅ All jobs completed. {job_summary}")
                        return session_info
                
                time.sleep(check_interval)
            
            print(f"⏰ Timeout after {max_wait_time} seconds")
            return self.get_session_status(session_id)
            
        except ImportError:
            # Fallback if IPython not available
            return self._wait_with_simple_display(session_id, max_wait_time, check_interval)
    
    def _wait_with_rich_display(self, session_id: str, max_wait_time: int, check_interval: int, training_interval_movie: int) -> SessionInfo:
        """Rich progress bars for beautiful terminal display."""
        try:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
            from rich.live import Live
            from rich.table import Table
            from rich.panel import Panel
            from rich.text import Text
            import time
            
            start_time = time.time()
            job_tasks = {}  # Track progress tasks for each job
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                expand=True
            ) as progress:
                
                # Main session task
                session_task = progress.add_task(f"[bold green]Session {session_id}", total=100)
                
                while time.time() - start_time < max_wait_time:
                    session_info = self.get_session_status(session_id)
                    
                    # Update session progress
                    elapsed = time.time() - start_time
                    session_progress = min(elapsed / max_wait_time * 100, 99)
                    progress.update(session_task, completed=session_progress, 
                                  description=f"[bold green]Session {session_id} ({session_info.status})")
                    
                    # Update job progress
                    current_jobs = set(session_info.jobs.keys())
                    
                    # Add new jobs
                    for job_id, job in session_info.jobs.items():
                        if job_id not in job_tasks:
                            job_type = job.get('type', job_id.split('_')[0])
                            job_tasks[job_id] = progress.add_task(f"[cyan]{job_type}", total=100)
                        
                        # Update job progress
                        job_status = job.get('status', 'unknown')
                        raw_progress = job.get('progress', 0)
                        job_progress = 100 if job_status == 'done' else (raw_progress * 100 if raw_progress else 0)
                        
                        progress.update(job_tasks[job_id], completed=job_progress,
                                      description=f"[cyan]{job.get('type', job_id.split('_')[0])} ({job_status})")
                    
                    # Check completion
                    if session_info.status in ['done', 'failed', 'cancelled']:
                        progress.update(session_task, completed=100, 
                                      description=f"[bold green]Session {session_id} ✅ {session_info.status}")
                        break
                    
                    if session_info.jobs:
                        terminal_states = {'done', 'failed', 'cancelled'}
                        all_jobs_terminal = all(job.get('status') in terminal_states for job in session_info.jobs.values())
                        if all_jobs_terminal:
                            progress.update(session_task, completed=100,
                                          description=f"[bold green]Session {session_id} ✅ completed")
                            break
                    
                    time.sleep(check_interval)
                
                # Final summary
                session_info = self.get_session_status(session_id)
                if session_info.jobs:
                    job_summary = self._analyze_job_completion(session_info.jobs)
                    progress.console.print(f"\n[bold green]✅ {job_summary}")
                
                return session_info
                
        except ImportError:
            # Fallback if rich not available
            return self._wait_with_simple_display(session_id, max_wait_time, check_interval)
    
    def _wait_with_simple_display(self, session_id: str, max_wait_time: int, check_interval: int) -> SessionInfo:
        """Simple display with line overwriting for basic terminals."""
        import sys
        import time
        
        print(f"🚀 Waiting for session {session_id} to complete...")
        start_time = time.time()
        last_num_lines = 0
        
        while time.time() - start_time < max_wait_time:
            session_info = self.get_session_status(session_id)
            
            # Clear previous lines if terminal supports it
            if sys.stdout.isatty() and last_num_lines > 0:
                for _ in range(last_num_lines):
                    sys.stdout.write('\033[F')  # Move cursor up
                    sys.stdout.write('\033[2K')  # Clear line
            
            # Build status display
            elapsed = int(time.time() - start_time)
            mins, secs = divmod(elapsed, 60)
            
            lines = []
            lines.append(f"📊 Session {session_id} | Status: {session_info.status} | Elapsed: {mins:02d}:{secs:02d}")
            
            if session_info.jobs:
                for job_id, job in session_info.jobs.items():
                    job_status = job.get('status', 'unknown')
                    progress = job.get('progress')
                    job_type = job.get('type', job_id.split('_')[0])
                    
                    if progress is not None:
                        # Fix percentage issue: show 100% when job is done
                        progress_pct = 100.0 if job_status == 'done' else (progress * 100)
                        progress_bar = "█" * int(progress_pct / 5) + "░" * (20 - int(progress_pct / 5))
                        lines.append(f"  {job_type}: {job_status} [{progress_bar}] {progress_pct:.1f}%")
                    else:
                        status_emoji = "✅" if job_status == "done" else "🔄" if job_status == "running" else "❌"
                        lines.append(f"  {status_emoji} {job_type}: {job_status}")
            
            # Print all lines
            for line in lines:
                print(line)
            
            last_num_lines = len(lines)
            
            # Check completion
            if session_info.status in ['done', 'failed', 'cancelled']:
                print(f"\n✅ Session completed with status: {session_info.status}")
                return session_info
            
            if session_info.jobs:
                terminal_states = {'done', 'failed', 'cancelled'}
                all_jobs_terminal = all(job.get('status') in terminal_states for job in session_info.jobs.values())
                if all_jobs_terminal:
                    job_summary = self._analyze_job_completion(session_info.jobs)
                    print(f"\n✅ All jobs completed. {job_summary}")
                    return session_info
            
            time.sleep(check_interval)
        
        print(f"\n⏰ Timeout waiting for session completion after {max_wait_time} seconds")
        return self.get_session_status(session_id)

    def _analyze_job_completion(self, jobs: Dict[str, Any]) -> str:
        """
        Analyze job completion status and provide detailed summary.
        
        Args:
            jobs: Dictionary of job information
            
        Returns:
            Formatted string describing job completion status
        """
        done_jobs = []
        failed_jobs = []
        cancelled_jobs = []
        
        for job_id, job in jobs.items():
            status = job.get('status', 'unknown')
            job_type = job.get('type', 'unknown')
            
            if status == 'done':
                done_jobs.append(f"{job_type} ({job_id})")
            elif status == 'failed':
                error_info = ""
                # Look for error information in various possible fields
                if 'error' in job:
                    error_info = f" - Error: {job['error']}"
                elif 'message' in job:
                    error_info = f" - Message: {job['message']}"
                failed_jobs.append(f"{job_type} ({job_id}){error_info}")
            elif status == 'cancelled':
                cancelled_jobs.append(f"{job_type} ({job_id})")
        
        # Build summary message
        summary_parts = []
        if done_jobs:
            summary_parts.append(f"✅ {len(done_jobs)} succeeded: {', '.join(done_jobs)}")
        if failed_jobs:
            summary_parts.append(f"❌ {len(failed_jobs)} failed: {', '.join(failed_jobs)}")
        if cancelled_jobs:
            summary_parts.append(f"🚫 {len(cancelled_jobs)} cancelled: {', '.join(cancelled_jobs)}")
        
        return " | ".join(summary_parts) if summary_parts else "No jobs found"

    def _update_live_training_movie(self, session_id: str, live_viz_state: Dict[str, Any], training_interval_movie: int = 3):
        """Update live training movie visualization as new epochs become available."""
        try:
            # Get current epoch projections (for ES training) - now with better error handling
            epoch_projections = self._get_epoch_projections(session_id)
            es_epoch_count = len(epoch_projections)
            
            # Debug logging
            print(f"🎬 Live movie update: ES epochs={es_epoch_count}, last_es={live_viz_state.get('last_es_epoch_count', 0)}")
            
            # Get training metrics (for both ES and single predictor) - now with better error handling
            try:
                metrics_data = self.get_training_metrics(session_id)
                training_metrics = metrics_data.get('training_metrics', {})
                live_viz_state['training_metrics'] = training_metrics
                print(f"✅ Training metrics retrieved successfully")
            except Exception as e:
                # Training metrics might not be available yet - use cached or empty
                print(f"⚠️ Training metrics not available: {e}")
                training_metrics = live_viz_state.get('training_metrics', {})
            
            # Check single predictor training progress
            training_info = training_metrics.get('training_info', [])
            sp_epoch_count = len(training_info)
            
            # Check if we have new data to display (either ES or SP)
            last_es_count = live_viz_state.get('last_es_epoch_count', 0)
            last_sp_count = live_viz_state.get('last_sp_epoch_count', 0)
            
            has_new_data = (es_epoch_count > last_es_count) or (sp_epoch_count > last_sp_count)
            
            if has_new_data:
                live_viz_state['epoch_projections'] = epoch_projections
                live_viz_state['last_es_epoch_count'] = es_epoch_count
                live_viz_state['last_sp_epoch_count'] = sp_epoch_count
                
                # Check if we should display based on epoch modulus (only show every N epochs)
                should_display = False
                
                # Check ES training epochs
                if es_epoch_count > 0:
                    latest_es_epoch = self._get_latest_es_epoch(epoch_projections)
                    if latest_es_epoch % training_interval_movie == 0 or latest_es_epoch == 1:
                        should_display = True
                
                # Check single predictor training epochs
                if sp_epoch_count > 0:
                    if sp_epoch_count % training_interval_movie == 0 or sp_epoch_count == 1:
                        should_display = True
                
                # Always show the first epoch or if we haven't initialized yet
                if not live_viz_state.get('plot_initialized', False):
                    should_display = True
                
                if should_display and (es_epoch_count > 0 or sp_epoch_count > 0):
                    # Display live training update
                    self._display_live_training_frame(session_id, live_viz_state, es_epoch_count, sp_epoch_count)
                    live_viz_state['plot_initialized'] = True
                    
        except Exception as e:
            # Don't let live visualization errors break the main monitoring, but show what went wrong
            print(f"⚠️ Live training movie error: {e}")
            print(f"   🐛 This is likely a visualization issue, not a training problem")
            import traceback
            print(f"   📋 Details: {traceback.format_exc()[:500]}...")  # Show first 500 chars of traceback

    def _display_live_training_frame(self, session_id: str, live_viz_state: Dict[str, Any], es_epoch_count: int, sp_epoch_count: int):
        """Display the current frame of the live training movie."""
        try:
            import matplotlib.pyplot as plt
            from IPython.display import display
            
            epoch_projections = live_viz_state.get('epoch_projections', {})
            training_metrics = live_viz_state.get('training_metrics', {})
            
            # Determine what we have available to display
            has_es_data = es_epoch_count > 0 and epoch_projections
            has_sp_data = sp_epoch_count > 0 and training_metrics.get('training_info')
            
            if not has_es_data and not has_sp_data:
                return
            
            # Determine layout based on available data
            if has_es_data and has_sp_data:
                # Show both ES embedding evolution and loss curves
                fig, axes = plt.subplots(1, 3, figsize=(20, 6))
                ax_loss, ax_sp_loss, ax_embedding = axes
            elif has_es_data:
                # Show ES loss curves and embedding evolution
                fig, axes = plt.subplots(1, 2, figsize=(15, 6))
                ax_loss, ax_embedding = axes
                ax_sp_loss = None
            else:
                # Show only single predictor training
                fig, ax_sp_loss = plt.subplots(1, 1, figsize=(10, 6))
                ax_loss = None
                ax_embedding = None
            
            # Plot ES loss curves if available
            if has_es_data and ax_loss is not None:
                latest_es_epoch = self._get_latest_es_epoch(epoch_projections)
                self._plot_live_loss_evolution(ax_loss, training_metrics, latest_es_epoch)
                ax_loss.set_title('🧠 Embedding Space Training', fontweight='bold')
            
            # Plot single predictor loss curves if available
            if has_sp_data and ax_sp_loss is not None:
                latest_sp_epoch = sp_epoch_count
                self._plot_live_sp_loss_evolution(ax_sp_loss, training_metrics, latest_sp_epoch)
                ax_sp_loss.set_title('🎯 Single Predictor Training', fontweight='bold')
            
            # Plot current embedding space if available
            if has_es_data and ax_embedding is not None:
                latest_es_epoch = self._get_latest_es_epoch(epoch_projections)
                latest_projection = self._get_latest_projection(epoch_projections)
                if latest_projection:
                    self._plot_live_embedding_frame(ax_embedding, latest_projection, latest_es_epoch)
                    ax_embedding.set_title('🌌 Embedding Space Evolution', fontweight='bold')
            
            # Create title based on what's training
            title_parts = []
            if has_es_data:
                latest_es_epoch = self._get_latest_es_epoch(epoch_projections)
                title_parts.append(f"ES Epoch {latest_es_epoch}")
            if has_sp_data:
                title_parts.append(f"SP Epoch {sp_epoch_count}")
            
            title = f"🎬 Live Training - Session {session_id[:12]}... - {' | '.join(title_parts)}"
            plt.suptitle(title, fontsize=14, fontweight='bold')
            plt.tight_layout()
            display(fig)
            plt.close(fig)  # Prevent memory leaks
            
        except Exception as e:
            print(f"⚠️ Error displaying training frame: {e}")
            print(f"   🔍 Debug info: ES epochs={es_epoch_count}, SP epochs={sp_epoch_count}")
            print(f"   📊 Available data: projections={len(live_viz_state.get('epoch_projections', {}))}, metrics={bool(live_viz_state.get('training_metrics'))}")
            import traceback
            print(f"   📋 Traceback: {traceback.format_exc()[:400]}...")  # Show first 400 chars
    
    def _get_latest_es_epoch(self, epoch_projections: Dict[str, Any]) -> int:
        """Get the latest epoch from ES projections."""
        latest_epoch = 0
        for proj_data in epoch_projections.values():
            epoch = proj_data.get('epoch', 0)
            if epoch > latest_epoch:
                latest_epoch = epoch
        return latest_epoch
    
    def _get_latest_projection(self, epoch_projections: Dict[str, Any]) -> Dict[str, Any]:
        """Get the latest projection data from ES projections."""
        latest_epoch = 0
        latest_projection = None
        for proj_data in epoch_projections.values():
            epoch = proj_data.get('epoch', 0)
            if epoch > latest_epoch:
                latest_epoch = epoch
                latest_projection = proj_data
        return latest_projection

    def _plot_live_sp_loss_evolution(self, ax, training_metrics: Dict[str, Any], current_epoch: int):
        """Plot single predictor training and validation loss up to the current epoch for live visualization."""
        try:
            training_info = training_metrics.get('training_info', [])
            
            if not training_info:
                ax.text(0.5, 0.5, 'Single predictor training data not available yet', 
                       transform=ax.transAxes, ha='center', va='center')
                ax.set_title('Single Predictor Training (Live)', fontweight='bold')
                return
            
            # Filter data up to current epoch and extract loss data
            epochs = []
            train_losses = []
            val_losses = []
            
            for entry in training_info:
                epoch = entry.get('epoch_idx', 0) + 1  # Convert 0-based to 1-based
                if epoch <= current_epoch:
                    epochs.append(epoch)
                    train_losses.append(entry.get('loss', 0))
                    val_losses.append(entry.get('validation_loss', 0))
            
            if epochs:
                ax.plot(epochs, train_losses, 'g-', label='Training Loss', linewidth=2, marker='o', markersize=3)
                if val_losses and any(v > 0 for v in val_losses):
                    ax.plot(epochs, val_losses, 'r--', label='Validation Loss', linewidth=2, marker='s', markersize=3)
                
                ax.set_xlabel('Epoch', fontweight='bold')
                ax.set_ylabel('Loss', fontweight='bold')
                ax.set_title('Single Predictor Training (Live)', fontweight='bold')
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                # Highlight current epoch
                if epochs:
                    current_train_loss = train_losses[-1] if train_losses else 0
                    ax.axvline(x=current_epoch, color='orange', linestyle=':', alpha=0.7, linewidth=2)
                    ax.plot(current_epoch, current_train_loss, 'ro', markersize=8, label=f'Current (Epoch {current_epoch})')
                    ax.legend()
            else:
                ax.text(0.5, 0.5, f'Waiting for epoch {current_epoch} data...', 
                       transform=ax.transAxes, ha='center', va='center')
                
        except Exception as e:
            ax.text(0.5, 0.5, f'Error plotting SP loss: {e}', 
                   transform=ax.transAxes, ha='center', va='center')

    def _plot_live_loss_evolution(self, ax, training_metrics: Dict[str, Any], current_epoch: int):
        """Plot loss curves up to the current epoch for live visualization."""
        try:
            progress_info = training_metrics.get('progress_info', {})
            loss_history = progress_info.get('loss_history', [])
            
            if not loss_history:
                ax.text(0.5, 0.5, 'Training loss data not available yet', 
                       transform=ax.transAxes, ha='center', va='center')
                ax.set_title('Training Loss (Live)', fontweight='bold')
                return
            
            # Filter data up to current epoch
            epochs = [e.get('epoch', 0) for e in loss_history if e.get('epoch', 0) <= current_epoch]
            losses = [e.get('loss', 0) for e in loss_history if e.get('epoch', 0) <= current_epoch]
            val_losses = [e.get('validation_loss', 0) for e in loss_history if e.get('epoch', 0) <= current_epoch]
            
            if epochs:
                ax.plot(epochs, losses, 'b-', label='Training Loss', linewidth=2, marker='o', markersize=3)
                if val_losses and any(v > 0 for v in val_losses):
                    ax.plot(epochs, val_losses, 'r--', label='Validation Loss', linewidth=2, marker='s', markersize=3)
                
                ax.set_xlabel('Epoch', fontweight='bold')
                ax.set_ylabel('Loss', fontweight='bold')
                ax.set_title('Training Loss (Live)', fontweight='bold')
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                # Highlight current epoch
                if epochs:
                    current_loss = losses[-1] if losses else 0
                    ax.axvline(x=current_epoch, color='green', linestyle=':', alpha=0.7, linewidth=2)
                    ax.plot(current_epoch, current_loss, 'go', markersize=8, label=f'Current (Epoch {current_epoch})')
                    ax.legend()
            else:
                ax.text(0.5, 0.5, f'Waiting for epoch {current_epoch} data...', 
                       transform=ax.transAxes, ha='center', va='center')
                
        except Exception as e:
            ax.text(0.5, 0.5, f'Error plotting loss: {e}', 
                   transform=ax.transAxes, ha='center', va='center')

    def _plot_live_embedding_frame(self, ax, projection_data: Dict[str, Any], current_epoch: int):
        """Plot current embedding space frame for live visualization."""
        try:
            coords = projection_data.get('coords', [])
            
            if not coords:
                ax.text(0.5, 0.5, f'Waiting for epoch {current_epoch} projections...', 
                       transform=ax.transAxes, ha='center', va='center')
                ax.set_title(f'Embedding Space - Epoch {current_epoch} (Live)', fontweight='bold')
                return
            
            import pandas as pd
            df = pd.DataFrame(coords)
            
            # Sample for performance if too many points
            if len(df) > 2000:
                df = df.sample(2000, random_state=42)
            
            if 'x' in df.columns and 'y' in df.columns:
                # 2D projection
                scatter = ax.scatter(df['x'], df['y'], alpha=0.6, s=20, c='blue')
                ax.set_xlabel('Dimension 1', fontweight='bold')
                ax.set_ylabel('Dimension 2', fontweight='bold')
            elif all(col in df.columns for col in ['x', 'y', 'z']):
                # 3D projection - show as 2D with color representing z
                scatter = ax.scatter(df['x'], df['y'], alpha=0.6, s=20, c=df['z'], cmap='viridis')
                ax.set_xlabel('Dimension 1', fontweight='bold')
                ax.set_ylabel('Dimension 2', fontweight='bold')
                plt.colorbar(scatter, ax=ax, label='Dimension 3')
            else:
                ax.text(0.5, 0.5, 'Unsupported projection format', 
                       transform=ax.transAxes, ha='center', va='center')
            
            ax.set_title(f'Embedding Space - Epoch {current_epoch} (Live)', fontweight='bold')
            ax.grid(True, alpha=0.3)
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error plotting embedding: {e}', 
                   transform=ax.transAxes, ha='center', va='center')

    def create_embedding_space(self, name: str, s3_training_dataset: str, s3_validation_dataset: str) -> SessionInfo:
        """
        Create a new embedding space from S3 training and validation datasets.
        
        Args:
            name: Name for the embedding space
            s3_training_dataset: S3 URL for training dataset (must start with 's3://')
            s3_validation_dataset: S3 URL for validation dataset (must start with 's3://')
            
        Returns:
            SessionInfo for the newly created embedding space session
            
        Raises:
            ValueError: If S3 URLs are invalid
        """
        # Validate S3 URLs
        if not s3_training_dataset.startswith('s3://'):
            raise ValueError("s3_training_dataset must be a valid S3 URL (s3://...)")
        if not s3_validation_dataset.startswith('s3://'):
            raise ValueError("s3_validation_dataset must be a valid S3 URL (s3://...)")
        
        print(f"Creating embedding space '{name}' from S3 datasets...")
        print(f"  Training: {s3_training_dataset}")
        print(f"  Validation: {s3_validation_dataset}")
        
        data = {
            "name": name,
            "s3_file_data_set_training": s3_training_dataset,
            "s3_file_data_set_validation": s3_validation_dataset
        }
        
        response_data = self._post_json("/compute/create-embedding-space", data)
        
        session_id = response_data.get('session_id')
        print(f"Embedding space session created: {session_id}")
        
        return SessionInfo(
            session_id=session_id,
            session_type=response_data.get('session_type', 'embedding_space'),
            status=response_data.get('status', 'ready'),
            jobs={},
            job_queue_positions={}
        )

    # =========================================================================
    # File Upload
    # =========================================================================
    
    def upload_file_and_create_session(self, file_path: Path) -> SessionInfo:
        """
        Upload a CSV file and create a new session.
        
        Args:
            file_path: Path to the CSV file to upload
            
        Returns:
            SessionInfo for the newly created session
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        print(f"Uploading file: {file_path}")
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'text/csv')}
            response = self._make_request("POST", "/compute/upload_with_new_session/", files=files)
        
        response_data = response.json()
        session_id = response_data.get('session_id')
        
        print(f"File uploaded, session created: {session_id}")
        
        # Check for and display warnings
        warnings = response_data.get('warnings', [])
        if warnings:
            print("\n" + "="*60)
            print("⚠️  UPLOAD WARNINGS")
            print("="*60)
            for warning in warnings:
                print(warning)
            print("="*60 + "\n")
        
        return SessionInfo(
            session_id=session_id,
            session_type=response_data.get('session_type', 'sphere'),
            status=response_data.get('status', 'ready'),
            jobs={},
            job_queue_positions={}
        )

    def upload_df_and_create_session(self, df=None, filename: str = "data.csv", file_path: str = None, 
                                    column_overrides: Dict[str, str] = None, string_list_delimiter: str = "|",
                                    metadata: Dict[str, Any] = None) -> SessionInfo:
        """
        Upload a pandas DataFrame or CSV file and create a new session.
        
        Args:
            df: pandas DataFrame to upload (optional if file_path is provided)
            filename: Name to give the uploaded file (default: "data.csv")
            file_path: Path to CSV file to upload (optional if df is provided)
            column_overrides: Dict mapping column names to types ("scalar", "set", "free_string", "free_string_list")
            string_list_delimiter: Delimiter for free_string_list columns (default: "|")
            metadata: Optional metadata to store with the session (e.g., future target columns)
            
        Returns:
            SessionInfo for the newly created session
        """
        import pandas as pd
        import io
        import gzip
        import os
        
        # Validate inputs
        if df is None and file_path is None:
            raise ValueError("Either df or file_path must be provided")
        if df is not None and file_path is not None:
            raise ValueError("Provide either df or file_path, not both")
        
        # Handle file path input
        if file_path:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check if it's a CSV file
            if not file_path.lower().endswith(('.csv', '.csv.gz')):
                raise ValueError("File must be a CSV file (with .csv or .csv.gz extension)")
            
            print(f"Uploading file: {file_path}")
            
            # Read the file content
            if file_path.endswith('.gz'):
                # Already gzipped
                with gzip.open(file_path, 'rb') as f:
                    file_content = f.read()
                upload_filename = os.path.basename(file_path)
                content_type = 'application/gzip'
            else:
                # Read CSV and compress it
                with open(file_path, 'rb') as f:
                    csv_content = f.read()
                
                # Compress the content
                print("Compressing CSV file...")
                compressed_buffer = io.BytesIO()
                with gzip.GzipFile(fileobj=compressed_buffer, mode='wb') as gz:
                    gz.write(csv_content)
                file_content = compressed_buffer.getvalue()
                upload_filename = os.path.basename(file_path) + '.gz'
                content_type = 'application/gzip'
                
                original_size = len(csv_content)
                compressed_size = len(file_content)
                compression_ratio = (1 - compressed_size / original_size) * 100
                print(f"Compressed from {original_size:,} to {compressed_size:,} bytes ({compression_ratio:.1f}% reduction)")
        
        # Handle DataFrame input
        else:
            if not isinstance(df, pd.DataFrame):
                raise TypeError("df must be a pandas DataFrame")
            
            print(f"Uploading DataFrame ({len(df)} rows, {len(df.columns)} columns)")
            
            # Clean NaN values in DataFrame before CSV conversion
            # This prevents JSON encoding issues when the server processes the data
            # Use pandas.notna() with where() for compatibility with all pandas versions
            cleaned_df = df.where(pd.notna(df), None)  # Replace NaN with None for JSON compatibility
            
            # Convert DataFrame to CSV and compress
            csv_buffer = io.StringIO()
            cleaned_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue().encode('utf-8')
            
            # Compress the CSV data
            print("Compressing DataFrame...")
            compressed_buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=compressed_buffer, mode='wb') as gz:
                gz.write(csv_data)
            file_content = compressed_buffer.getvalue()
            upload_filename = filename if filename.endswith('.gz') else filename + '.gz'
            content_type = 'application/gzip'
            
            original_size = len(csv_data)
            compressed_size = len(file_content)
            compression_ratio = (1 - compressed_size / original_size) * 100
            print(f"Compressed from {original_size:,} to {compressed_size:,} bytes ({compression_ratio:.1f}% reduction)")
        
        # Upload the compressed file with optional column overrides
        files = {'file': (upload_filename, file_content, content_type)}
        
        # Add column overrides, string_list_delimiter, and metadata as form data if provided
        data = {}
        if column_overrides:
            import json
            data['column_overrides'] = json.dumps(column_overrides)
            print(f"Column overrides: {column_overrides}")
        if string_list_delimiter != "|":  # Only send if non-default
            data['string_list_delimiter'] = string_list_delimiter
            print(f"String list delimiter: '{string_list_delimiter}'")
        if metadata:
            import json
            data['metadata'] = json.dumps(metadata)
            print(f"Session metadata: {metadata}")
            
        response = self._make_request("POST", "/compute/upload_with_new_session/", files=files, data=data)
        
        response_data = response.json()
        session_id = response_data.get('session_id')
        
        print(f"Upload complete, session created: {session_id}")
        
        # Check for and display warnings
        warnings = response_data.get('warnings', [])
        if warnings:
            print("\n" + "="*60)
            print("⚠️  UPLOAD WARNINGS")
            print("="*60)
            for warning in warnings:
                print(warning)
            print("="*60 + "\n")
        
        return SessionInfo(
            session_id=session_id,
            session_type=response_data.get('session_type', 'sphere'),
            status=response_data.get('status', 'ready'),
            jobs={},
            job_queue_positions={}
        )
        

    def create_session_with_future_targets(self, future_target_columns: List[str], 
                                         session_type: str = "sphere", 
                                         additional_metadata: Dict[str, Any] = None) -> SessionInfo:
        """
        Create a new session with future target columns specified for optimization.
        
        This is a convenience method that creates a session with metadata indicating
        which columns will be used as targets in the future. This can help optimize
        data processing and reduce dataset sizing.
        
        Args:
            future_target_columns: List of column names that will be used as targets
            session_type: Type of session to create ('sphere', 'predictor', etc.)
            additional_metadata: Additional metadata to store with the session
            
        Returns:
            SessionInfo object with session details
            
        Example:
            # Create session optimized for future predictions on specific columns
            session = client.create_session_with_future_targets(
                future_target_columns=['fuel_card_network', 'customer_segment', 'spend_category'],
                additional_metadata={'project': 'fuel_card_analysis', 'priority': 'high'}
            )
        """
        metadata = {
            'future_target_columns': future_target_columns,
            'optimization_hint': 'target_columns_known'
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
            
        print(f"Creating {session_type} session optimized for future targets: {future_target_columns}")
        
        return self.create_session(session_type=session_type, metadata=metadata)

    def upload_df_and_create_session_with_future_targets(self, df=None, filename: str = "data.csv", 
                                                        file_path: str = None,
                                                        future_target_columns: List[str] = None,
                                                        column_overrides: Dict[str, str] = None, 
                                                        string_list_delimiter: str = "|",
                                                        additional_metadata: Dict[str, Any] = None) -> SessionInfo:
        """
        Upload a pandas DataFrame or CSV file and create a new session optimized for future targets.
        
        This is a convenience method that uploads data and creates a session with metadata
        indicating which columns will be used as targets in the future. This can help optimize
        data processing and reduce dataset sizing.
        
        Args:
            df: pandas DataFrame to upload (optional if file_path is provided)
            filename: Name to give the uploaded file (default: "data.csv")
            file_path: Path to CSV file to upload (optional if df is provided)
            future_target_columns: List of column names that will be used as targets
            column_overrides: Dict mapping column names to types ("scalar", "set", "free_string", "free_string_list")
            string_list_delimiter: Delimiter for free_string_list columns (default: "|")
            additional_metadata: Additional metadata to store with the session
            
        Returns:
            SessionInfo for the newly created session
            
        Example:
            # Upload data and create session optimized for specific future targets
            session = client.upload_df_and_create_session_with_future_targets(
                df=my_dataframe,
                future_target_columns=['fuel_card_network', 'customer_segment'],
                additional_metadata={'project': 'fuel_analysis', 'version': '1.0'}
            )
        """
        metadata = {
            'future_target_columns': future_target_columns or [],
            'optimization_hint': 'target_columns_known'
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
            
        print(f"Uploading data and creating session optimized for future targets: {future_target_columns}")
        
        return self.upload_df_and_create_session(
            df=df,
            filename=filename,
            file_path=file_path,
            column_overrides=column_overrides,
            string_list_delimiter=string_list_delimiter,
            metadata=metadata
        )


    # =========================================================================
    # Single Predictor Functionality
    # =========================================================================
    
    def predict(self, session_id: str, record: Dict[str, Any], target_column: str = None, 
               predictor_id: str = None, max_retries: int = None, queue_batches: bool = False) -> Dict[str, Any]:
        """
        Make a single prediction for a record.
        
        Args:
            session_id: ID of session with trained predictor
            record: Record dictionary (without target column)
            target_column: Specific target column predictor to use (required if multiple predictors exist and predictor_id not specified)
            predictor_id: Specific predictor ID to use (recommended - more precise than target_column)
            max_retries: Number of retries for errors (default: uses client default)
            queue_batches: If True, queue this prediction for batch processing instead of immediate API call
            
        Returns:
            Prediction result dictionary if queue_batches=False, or queue ID if queue_batches=True
            
        Note:
            predictor_id is recommended over target_column for precision. If both are provided, predictor_id takes precedence.
            Use client.list_predictors(session_id) to see available predictor IDs.
        """
        # Track prediction call rate and show warning if needed
        if not queue_batches:
            should_warn = self._track_prediction_call(session_id)
            if should_warn:
                call_count = len(self._prediction_call_times.get(session_id, []))
                self._show_batching_warning(session_id, call_count)
        
        # If queueing is enabled, add to queue and return queue ID
        if queue_batches:
            queue_id = self._add_to_prediction_queue(session_id, record, target_column, predictor_id)
            return {"queued": True, "queue_id": queue_id}
        
        # Resolve predictor information (handles both predictor_id and target_column)
        predictor_info = self._resolve_predictor_id(session_id, predictor_id, target_column)
        validated_target_column = predictor_info['target_column']
        resolved_predictor_id = predictor_info['predictor_id']
        
        # Clean NaN/Inf values and remove target column
        cleaned_record = self._clean_numpy_values(record)
        # Additional NaN cleaning for JSON encoding
        cleaned_record = self.replace_nans_with_nulls(cleaned_record)
        cleaned_records = self._remove_target_columns(session_id, [cleaned_record], validated_target_column)
        final_record = cleaned_records[0] if cleaned_records else cleaned_record
        
        # Add predictor info to request so server knows exactly which predictor to use
        request_payload = {
            "query_record": final_record,
            "target_column": validated_target_column
        }
        
        # Include predictor_id if available for server-side routing
        if resolved_predictor_id:
            request_payload["predictor_id"] = resolved_predictor_id
        
        response_data = self._post_json(f"/session/{session_id}/predict", request_payload, max_retries=max_retries)
        return response_data
    
    def get_training_metrics(self, session_id: str, max_retries: int = None) -> Dict[str, Any]:
        """
        Get training metrics for a session's single predictor.
        
        Args:
            session_id: ID of session with trained single predictor
            max_retries: Override default retry count (useful during server restarts)
            
        Returns:
            Training metrics including loss history, validation metrics, etc.
        """
        # Use higher retry count for session endpoints during server restarts
        if max_retries is None:
            max_retries = max(8, self.default_max_retries)
        
        try:
            response_data = self._get_json(f"/session/{session_id}/training_metrics", max_retries=max_retries)
            return response_data
        except Exception as e:
            # Provide helpful messaging for early training scenarios
            error_str = str(e).lower()
            
            if "404" in error_str or "not found" in error_str:
                # Check if training is still in progress
                try:
                    session_status = self.get_session_status(session_id)
                    jobs = session_status.jobs
                    
                    # Look for any training jobs
                    running_training = []
                    completed_training = []
                    
                    for job_id, job_info in jobs.items():
                        job_type = job_info.get('type', '')
                        job_status = job_info.get('status', '')
                        
                        if 'train' in job_type:
                            if job_status == 'running':
                                running_training.append(job_type)
                            elif job_status == 'done':
                                completed_training.append(job_type)
                    
                    if running_training:
                        print(f"🔄 Training in progress ({', '.join(running_training)}) - metrics will be available as training progresses")
                        print(f"   💡 Training metrics become available once sufficient epochs have completed")
                        print(f"   ⏱️ Try again in a few minutes when training has advanced further")
                        return {}
                    elif completed_training:
                        print(f"⚠️ Training metrics not yet populated - completed training: {', '.join(completed_training)}")
                        print(f"   🔍 Metrics may still be processing - try again in a moment")
                        return {}
                    else:
                        print(f"💡 No training jobs found - start training to generate metrics")
                        print(f"   📖 Use client.train_single_predictor() to begin training")
                        return {}
                        
                except:
                    # Fallback message if session status check fails
                    print(f"⚠️ Training metrics not yet available - training may be in early stages")
                    print(f"   💡 Metrics will appear as training progresses")
                    return {}
            
            elif "500" in error_str or "internal server error" in error_str:
                print(f"🔄 Training metrics temporarily unavailable - server processing training data")
                print(f"   💡 Try again in a moment")
                return {}
            
            else:
                # Other errors - show generic message
                print(f"❌ Error retrieving training metrics: {e}")
                return {}

    # =========================================================================
    # Training Visualization & Plotting
    # =========================================================================
    
    def plot_training_loss(self, session_id: str, figsize: Tuple[int, int] = (12, 8), 
                          style: str = 'notebook', save_path: Optional[str] = None,
                          show_learning_rate: bool = True, smooth: bool = True,
                          title: Optional[str] = None) -> 'plt.Figure':
        """
        Plot comprehensive training loss curves for a session (both embedding space and single predictor).
        
        Args:
            session_id: Session ID to plot training for
            figsize: Figure size (width, height) in inches
            style: Plot style ('notebook', 'paper', 'presentation')
            save_path: Optional path to save the plot
            show_learning_rate: Whether to show learning rate on secondary y-axis
            smooth: Whether to apply smoothing to noisy curves
            title: Custom title (auto-generated if None)
            
        Returns:
            matplotlib Figure object for notebook display
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for plotting. Install with: pip install matplotlib")
        # Set up beautiful plotting style
        self._setup_plot_style(style)
        
        try:
            # Get training metrics
            metrics_data = self.get_training_metrics(session_id)
            training_metrics = metrics_data.get('training_metrics', {})
            
            # Create figure with subplots
            if show_learning_rate:
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)
                fig.subplots_adjust(hspace=0.3)
            else:
                fig, ax1 = plt.subplots(1, 1, figsize=figsize)
                ax2 = None
            
            # Plot embedding space training if available
            es_plotted = self._plot_embedding_space_data(ax1, training_metrics, smooth=smooth)
            
            # Plot single predictor training if available  
            sp_plotted = self._plot_single_predictor_data(ax1, training_metrics, smooth=smooth)
            
            if not es_plotted and not sp_plotted:
                ax1.text(0.5, 0.5, 'No training data available', 
                        transform=ax1.transAxes, ha='center', va='center',
                        fontsize=14, alpha=0.7)
                ax1.set_title('No Training Data Available')
            else:
                # Configure main plot
                ax1.set_ylabel('Loss', fontsize=12, fontweight='bold')
                ax1.grid(True, alpha=0.3)
                ax1.legend(frameon=True, fancybox=True, shadow=True, fontsize=10)
                
                # Set title
                if title is None:
                    title = f'Training Loss - Session {session_id[:12]}...'
                ax1.set_title(title, fontsize=14, fontweight='bold', pad=20)
                
                # Plot learning rate if requested and data available
                if show_learning_rate and ax2 is not None:
                    self._plot_learning_rate(ax2, training_metrics, smooth=smooth)
                    ax2.set_ylabel('Learning Rate', fontsize=12, fontweight='bold')
                    ax2.set_xlabel('Epoch', fontsize=12, fontweight='bold')
                    ax2.grid(True, alpha=0.3)
                    ax2.legend(frameon=True, fancybox=True, shadow=True, fontsize=10)
                else:
                    ax1.set_xlabel('Epoch', fontsize=12, fontweight='bold')
            
            # Final styling
            plt.tight_layout()
            
            # Save if requested
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
                print(f"📊 Plot saved to: {save_path}")
            
            return fig
            
        except Exception as e:
            print(f"❌ Error plotting training loss: {e}")
            # Return empty figure so notebooks don't crash
            fig, ax = plt.subplots(1, 1, figsize=figsize)
            ax.text(0.5, 0.5, f'Error loading data:\n{str(e)}', 
                   transform=ax.transAxes, ha='center', va='center',
                   fontsize=12, alpha=0.7)
            ax.set_title('Training Loss Plot - Error')
            return fig

    def plot_embedding_space_training(self, session_id: str, figsize: Tuple[int, int] = (10, 6),
                                     style: str = 'notebook', save_path: Optional[str] = None,
                                     show_mutual_info: bool = False) -> 'plt.Figure':
        """
        Plot detailed embedding space training metrics.
        
        Args:
            session_id: Session ID to plot
            figsize: Figure size (width, height) in inches 
            style: Plot style ('notebook', 'paper', 'presentation')
            save_path: Optional path to save the plot
            show_mutual_info: Whether to show mutual information curves
            
        Returns:
            matplotlib Figure object
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for plotting. Install with: pip install matplotlib")
        self._setup_plot_style(style)
        
        try:
            metrics_data = self.get_training_metrics(session_id)
            training_metrics = metrics_data.get('training_metrics', {})
            
            # Check for embedding space data
            progress_info = training_metrics.get('progress_info', {})
            loss_history = progress_info.get('loss_history', [])
            
            if not loss_history:
                fig, ax = plt.subplots(1, 1, figsize=figsize)
                ax.text(0.5, 0.5, 'No embedding space training data available', 
                       transform=ax.transAxes, ha='center', va='center')
                return fig
            
            # Create subplots
            if show_mutual_info:
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(figsize[0], figsize[1]*1.3))
                fig.subplots_adjust(hspace=0.4)
            else:
                fig, ax1 = plt.subplots(1, 1, figsize=figsize)
                ax2 = None
            
            # Extract data
            epochs = [entry.get('epoch', 0) for entry in loss_history]
            train_losses = [entry.get('loss', 0) for entry in loss_history]
            val_losses = [entry.get('validation_loss', 0) for entry in loss_history]
            
            # Plot loss curves
            ax1.plot(epochs, train_losses, 'o-', label='Training Loss', 
                    linewidth=2, markersize=4, alpha=0.8)
            ax1.plot(epochs, val_losses, 's-', label='Validation Loss', 
                    linewidth=2, markersize=4, alpha=0.8)
            
            ax1.set_xlabel('Epoch', fontweight='bold')
            ax1.set_ylabel('Loss', fontweight='bold')
            ax1.set_title('Embedding Space Training Progress', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # Plot mutual information if available and requested
            if show_mutual_info and ax2 is not None:
                self._plot_mutual_information(ax2, progress_info)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
                
            return fig
            
        except Exception as e:
            print(f"❌ Error plotting embedding space training: {e}")
            fig, ax = plt.subplots(1, 1, figsize=figsize)
            ax.text(0.5, 0.5, f'Error: {str(e)}', transform=ax.transAxes, ha='center', va='center')
            return fig

    def plot_single_predictor_training(self, session_id: str, figsize: Tuple[int, int] = (10, 6),
                                      style: str = 'notebook', save_path: Optional[str] = None,
                                      show_metrics: bool = True) -> 'plt.Figure':
        """
        Plot detailed single predictor training metrics.
        
        Args:
            session_id: Session ID to plot
            figsize: Figure size (width, height) in inches
            style: Plot style ('notebook', 'paper', 'presentation')
            save_path: Optional path to save the plot
            show_metrics: Whether to show accuracy/precision/recall metrics
            
        Returns:
            matplotlib Figure object
        """
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib is required for plotting. Install with: pip install matplotlib")
        self._setup_plot_style(style)
        
        try:
            metrics_data = self.get_training_metrics(session_id)
            training_metrics = metrics_data.get('training_metrics', {})
            
            # Check for single predictor data
            training_info = training_metrics.get('training_info', [])
            
            if not training_info:
                fig, ax = plt.subplots(1, 1, figsize=figsize)
                ax.text(0.5, 0.5, 'No single predictor training data available', 
                       transform=ax.transAxes, ha='center', va='center')
                return fig
            
            # Create subplots
            if show_metrics:
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(figsize[0], figsize[1]*1.3))
                fig.subplots_adjust(hspace=0.4)
            else:
                fig, ax1 = plt.subplots(1, 1, figsize=figsize)
                ax2 = None
            
            # Extract loss data
            epochs = [entry.get('epoch', 0) for entry in training_info]
            train_losses = [entry.get('loss', 0) for entry in training_info]
            val_losses = [entry.get('validation_loss', 0) for entry in training_info]
            
            # Plot loss curves
            ax1.plot(epochs, train_losses, 'o-', label='Training Loss', 
                    linewidth=2, markersize=4, alpha=0.8)
            ax1.plot(epochs, val_losses, 's-', label='Validation Loss', 
                    linewidth=2, markersize=4, alpha=0.8)
            
            target_col = training_metrics.get('target_column', 'Unknown')
            ax1.set_title(f'Single Predictor Training - {target_col}', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Epoch', fontweight='bold')
            ax1.set_ylabel('Loss', fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # Plot performance metrics if available and requested
            if show_metrics and ax2 is not None:
                self._plot_performance_metrics(ax2, training_info)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
                
            return fig
            
        except Exception as e:
            print(f"❌ Error plotting single predictor training: {e}")
            fig, ax = plt.subplots(1, 1, figsize=figsize)
            ax.text(0.5, 0.5, f'Error: {str(e)}', transform=ax.transAxes, ha='center', va='center')
            return fig

    def plot_training_comparison(self, session_ids: List[str], labels: Optional[List[str]] = None,
                               figsize: Tuple[int, int] = (12, 8), style: str = 'notebook',
                               save_path: Optional[str] = None) -> plt.Figure:
        """
        Compare training curves across multiple sessions.
        
        Args:
            session_ids: List of session IDs to compare
            labels: Optional custom labels for each session
            figsize: Figure size (width, height) in inches
            style: Plot style ('notebook', 'paper', 'presentation')
            save_path: Optional path to save the plot
            
        Returns:
            matplotlib Figure object
        """
        self._setup_plot_style(style)
        
        if labels is None:
            labels = [f"Session {sid[:8]}..." for sid in session_ids]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(session_ids)))
        
        for i, (session_id, label) in enumerate(zip(session_ids, labels)):
            try:
                metrics_data = self.get_training_metrics(session_id)
                training_metrics = metrics_data.get('training_metrics', {})
                
                # Plot embedding space if available
                progress_info = training_metrics.get('progress_info', {})
                loss_history = progress_info.get('loss_history', [])
                if loss_history:
                    epochs = [entry.get('epoch', 0) for entry in loss_history]
                    val_losses = [entry.get('validation_loss', 0) for entry in loss_history]
                    ax1.plot(epochs, val_losses, 'o-', label=f'{label} (ES)', 
                            color=colors[i], alpha=0.8)
                
                # Plot single predictor if available
                training_info = training_metrics.get('training_info', [])
                if training_info:
                    epochs = [entry.get('epoch', 0) for entry in training_info]
                    val_losses = [entry.get('validation_loss', 0) for entry in training_info]
                    ax2.plot(epochs, val_losses, 's-', label=f'{label} (SP)', 
                            color=colors[i], alpha=0.8, linestyle='--')
                    
            except Exception as e:
                print(f"⚠️ Could not load data for session {session_id}: {e}")
        
        # Configure plots
        ax1.set_title('Embedding Space Validation Loss', fontweight='bold')
        ax1.set_xlabel('Epoch', fontweight='bold')
        ax1.set_ylabel('Validation Loss', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        ax2.set_title('Single Predictor Validation Loss', fontweight='bold')
        ax2.set_xlabel('Epoch', fontweight='bold')
        ax2.set_ylabel('Validation Loss', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            
        return fig

    def _setup_plot_style(self, style: str = 'notebook'):
        """Configure matplotlib for beautiful plots."""
        if HAS_SEABORN:
            if style == 'notebook':
                sns.set_style("whitegrid")
                sns.set_context("notebook", font_scale=1.1)
                sns.set_palette("husl")
            elif style == 'paper':
                sns.set_style("white")
                sns.set_context("paper", font_scale=1.0)
                sns.set_palette("deep")
            elif style == 'presentation':
                sns.set_style("whitegrid")
                sns.set_context("talk", font_scale=1.2)
                sns.set_palette("bright")
        else:
            # Fallback without seaborn
            plt.style.use('default')
            plt.rcParams.update({
                'figure.facecolor': 'white',
                'axes.facecolor': 'white',
                'axes.grid': True,
                'grid.alpha': 0.3,
                'font.size': 11 if style == 'notebook' else (10 if style == 'paper' else 13),
                'axes.labelweight': 'bold',
                'axes.titleweight': 'bold'
            })

    def _plot_embedding_space_data(self, ax, training_metrics: Dict, smooth: bool = True) -> bool:
        """Plot embedding space training data on given axes. Returns True if data was plotted."""
        progress_info = training_metrics.get('progress_info', {})
        loss_history = progress_info.get('loss_history', [])
        
        if not loss_history:
            return False
        
        epochs = [entry.get('epoch', 0) for entry in loss_history]
        train_losses = [entry.get('loss', 0) for entry in loss_history]
        val_losses = [entry.get('validation_loss', 0) for entry in loss_history]
        
        if smooth and len(epochs) > 5:
            epochs_smooth, train_smooth = self._smooth_curve(epochs, train_losses)
            epochs_smooth, val_smooth = self._smooth_curve(epochs, val_losses)
            ax.plot(epochs_smooth, train_smooth, '-', label='ES Training Loss', 
                   linewidth=2.5, alpha=0.9)
            ax.plot(epochs_smooth, val_smooth, '-', label='ES Validation Loss', 
                   linewidth=2.5, alpha=0.9)
        else:
            ax.plot(epochs, train_losses, 'o-', label='ES Training Loss', 
                   linewidth=2, markersize=4, alpha=0.8)
            ax.plot(epochs, val_losses, 's-', label='ES Validation Loss', 
                   linewidth=2, markersize=4, alpha=0.8)
        
        return True

    def _plot_single_predictor_data(self, ax, training_metrics: Dict, smooth: bool = True) -> bool:
        """Plot single predictor training data on given axes. Returns True if data was plotted."""
        training_info = training_metrics.get('training_info', [])
        
        if not training_info:
            return False
        
        epochs = [entry.get('epoch', 0) for entry in training_info]
        train_losses = [entry.get('loss', 0) for entry in training_info]
        val_losses = [entry.get('validation_loss', 0) for entry in training_info]
        
        if smooth and len(epochs) > 5:
            epochs_smooth, train_smooth = self._smooth_curve(epochs, train_losses)
            epochs_smooth, val_smooth = self._smooth_curve(epochs, val_losses)
            ax.plot(epochs_smooth, train_smooth, '--', label='SP Training Loss', 
                   linewidth=2.5, alpha=0.9)
            ax.plot(epochs_smooth, val_smooth, '--', label='SP Validation Loss', 
                   linewidth=2.5, alpha=0.9)
        else:
            ax.plot(epochs, train_losses, '^-', label='SP Training Loss', 
                   linewidth=2, markersize=4, alpha=0.8, linestyle='--')
            ax.plot(epochs, val_losses, 'v-', label='SP Validation Loss', 
                   linewidth=2, markersize=4, alpha=0.8, linestyle='--')
        
        return True

    def _plot_learning_rate(self, ax, training_metrics: Dict, smooth: bool = True) -> bool:
        """Plot learning rate curves. Returns True if data was plotted."""
        # Try embedding space first
        progress_info = training_metrics.get('progress_info', {})
        loss_history = progress_info.get('loss_history', [])
        
        plotted = False
        
        if loss_history:
            epochs = [entry.get('epoch', 0) for entry in loss_history]
            lrs = [entry.get('current_learning_rate', 0) for entry in loss_history]
            
            if any(lr > 0 for lr in lrs):  # Only plot if we have valid LR data
                ax.plot(epochs, lrs, 'o-', label='ES Learning Rate', 
                       linewidth=2, markersize=3, alpha=0.8)
                plotted = True
        
        # Try single predictor
        training_info = training_metrics.get('training_info', [])
        if training_info:
            epochs = [entry.get('epoch', 0) for entry in training_info]
            lrs = [entry.get('lr', 0) for entry in training_info]
            
            if any(lr > 0 for lr in lrs):  # Only plot if we have valid LR data
                ax.plot(epochs, lrs, '^-', label='SP Learning Rate', 
                       linewidth=2, markersize=3, alpha=0.8, linestyle='--')
                plotted = True
        
        if plotted:
            ax.set_yscale('log')  # Learning rates are often better viewed on log scale
        
        return plotted

    def _plot_mutual_information(self, ax, progress_info: Dict):
        """Plot mutual information curves if available."""
        mi_history = progress_info.get('mutual_information', [])
        if not mi_history:
            ax.text(0.5, 0.5, 'No mutual information data', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        epochs = [entry.get('epoch', 0) for entry in mi_history]
        joint_mi = [entry.get('joint', 0) for entry in mi_history]
        
        ax.plot(epochs, joint_mi, 'o-', label='Joint MI', linewidth=2, markersize=4)
        ax.set_xlabel('Epoch', fontweight='bold')
        ax.set_ylabel('Mutual Information', fontweight='bold')
        ax.set_title('Mutual Information Progress', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()

    def _plot_performance_metrics(self, ax, training_info: List[Dict]):
        """Plot accuracy, precision, recall metrics if available."""
        epochs = []
        accuracies = []
        precisions = []
        recalls = []
        
        for entry in training_info:
            epoch = entry.get('epoch', 0)
            metrics = entry.get('metrics', {})
            
            if metrics:
                epochs.append(epoch)
                accuracies.append(metrics.get('accuracy', 0))
                precisions.append(metrics.get('precision', 0))
                recalls.append(metrics.get('recall', 0))
        
        if epochs:
            ax.plot(epochs, accuracies, 'o-', label='Accuracy', linewidth=2, markersize=4)
            ax.plot(epochs, precisions, 's-', label='Precision', linewidth=2, markersize=4)
            ax.plot(epochs, recalls, '^-', label='Recall', linewidth=2, markersize=4)
            
            ax.set_xlabel('Epoch', fontweight='bold')
            ax.set_ylabel('Score', fontweight='bold')
            ax.set_title('Performance Metrics', fontweight='bold')
            ax.set_ylim(0, 1.05)  # Performance metrics are typically 0-1
            ax.grid(True, alpha=0.3)
            ax.legend()
        else:
            ax.text(0.5, 0.5, 'No performance metrics available', 
                   transform=ax.transAxes, ha='center', va='center')

    def _smooth_curve(self, x: List[float], y: List[float], window: int = 5) -> Tuple[List[float], List[float]]:
        """Apply simple moving average smoothing to noisy curves."""
        if len(x) <= window:
            return x, y
        
        # Simple moving average
        y_smooth = []
        for i in range(len(y)):
            start_idx = max(0, i - window // 2)
            end_idx = min(len(y), i + window // 2 + 1)
            y_smooth.append(np.mean(y[start_idx:end_idx]))
        
        return x, y_smooth

    # =========================================================================
    # 3D Embedding Space Visualization 
    # =========================================================================
    
    def plot_embedding_space_3d(self, session_id: str, sample_size: int = 2000,
                                color_by: Optional[str] = None, size_by: Optional[str] = None,
                                interactive: bool = True, style: str = 'notebook',
                                title: Optional[str] = None, save_path: Optional[str] = None) -> Union[plt.Figure, 'go.Figure']:
        """
        Create interactive 3D visualization of the embedding space.
        
        Args:
            session_id: Session ID with trained embedding space
            sample_size: Maximum number of points to display (for performance)
            color_by: Column name to color points by (categorical data)
            size_by: Column name to size points by (numerical data)
            interactive: Use plotly for interactive plots (default) vs matplotlib
            style: Plot style ('notebook', 'paper', 'presentation')
            title: Custom plot title
            save_path: Path to save the plot (HTML for interactive, PNG for static)
            
        Returns:
            plotly Figure (interactive=True) or matplotlib Figure (interactive=False)
        """
        try:
            # Get projection data
            projections_data = self.get_projections(session_id)
            coords = projections_data.get('projections', {}).get('coords', [])
            
            if not coords:
                print("❌ No projection data available. Run embedding space training first.")
                return self._create_empty_3d_plot(interactive, "No projection data available")
            
            # Convert to DataFrame for easier manipulation
            import pandas as pd
            df = pd.DataFrame(coords)
            
            # Sample data if too large
            if len(df) > sample_size:
                df = df.sample(sample_size, random_state=42)
                print(f"📊 Sampled {sample_size} points from {len(coords)} total for performance")
            
            # Extract 3D coordinates
            if not all(col in df.columns for col in ['x', 'y', 'z']):
                print("❌ Missing 3D coordinates in projection data")
                return self._create_empty_3d_plot(interactive, "Invalid projection data format")
            
            x, y, z = df['x'].values, df['y'].values, df['z'].values
            
            if interactive and HAS_PLOTLY:
                return self._create_interactive_3d_plot(
                    df, x, y, z, color_by, size_by, title, save_path, session_id
                )
            else:
                return self._create_static_3d_plot(
                    df, x, y, z, color_by, size_by, title, save_path, style, session_id
                )
                
        except Exception as e:
            print(f"❌ Error creating 3D embedding plot: {e}")
            return self._create_empty_3d_plot(interactive, f"Error: {str(e)}")

    def plot_training_movie(self, session_id: str, figsize: Tuple[int, int] = (15, 10),
                           style: str = 'notebook', save_path: Optional[str] = None,
                           show_embedding_evolution: bool = True, 
                           show_loss_evolution: bool = True,
                           fps: int = 2, notebook_mode: bool = True) -> Union[plt.Figure, 'HTML']:
        """
        Create an animated training movie showing loss curves and embedding evolution.
        
        Args:
            session_id: Session ID with training data
            figsize: Figure size for animation frames
            style: Plot style ('notebook', 'paper', 'presentation') 
            save_path: Path to save animation (GIF or HTML)
            show_embedding_evolution: Include 3D embedding space evolution
            show_loss_evolution: Include loss curve progression
            fps: Frames per second for animation
            notebook_mode: Optimize for Jupyter notebook display
            
        Returns:
            Animated plot or HTML widget for notebook display
        """
        try:
            print("🎬 Creating training movie...")
            
            # Get training data
            metrics_data = self.get_training_metrics(session_id)
            training_metrics = metrics_data.get('training_metrics', {})
            
            # Check for epoch projections (for embedding evolution)
            epoch_projections = self._get_epoch_projections(session_id)
            
            if show_embedding_evolution and not epoch_projections:
                print("⚠️ No epoch projections found - embedding evolution disabled.")
                print("   💡 To enable embedding evolution, make sure epoch projections are generated during ES training.")
                show_embedding_evolution = False
            
            if notebook_mode and HAS_IPYWIDGETS:
                return self._create_interactive_training_movie(
                    training_metrics, epoch_projections, session_id,
                    show_embedding_evolution, show_loss_evolution
                )
            else:
                return self._create_static_training_movie(
                    training_metrics, epoch_projections, figsize, style,
                    save_path, show_embedding_evolution, show_loss_evolution, fps
                )
                
        except Exception as e:
            print(f"❌ Error creating training movie: {e}")
            if notebook_mode and HAS_IPYWIDGETS:
                return HTML(f"<div style='color: red;'>Error creating training movie: {e}</div>")
            else:
                fig, ax = plt.subplots(1, 1, figsize=figsize)
                ax.text(0.5, 0.5, f'Error: {str(e)}', transform=ax.transAxes, ha='center', va='center')
                return fig

    def plot_embedding_evolution(self, session_id: str, epoch_range: Optional[Tuple[int, int]] = None,
                                 interactive: bool = True, sample_size: int = 1000,
                                 color_by: Optional[str] = None) -> Union[plt.Figure, 'go.Figure']:
        """
        Show how embedding space evolves during training across epochs.
        
        Args:
            session_id: Session ID with epoch projection data
            epoch_range: Tuple of (start_epoch, end_epoch) to show, None for all
            interactive: Use plotly for interactive visualization
            sample_size: Maximum points per epoch to display
            color_by: Column to color points by
            
        Returns:
            Interactive plot showing embedding evolution over time
        """
        try:
            epoch_projections = self._get_epoch_projections(session_id)
            
            if not epoch_projections:
                print("❌ No epoch projection data found. Enable epoch projections during training.")
                return self._create_empty_3d_plot(interactive, "No epoch projection data")
            
            # Filter epoch range if specified
            if epoch_range:
                start_epoch, end_epoch = epoch_range
                epoch_projections = {
                    k: v for k, v in epoch_projections.items() 
                    if start_epoch <= v.get('epoch', 0) <= end_epoch
                }
            
            if interactive and HAS_PLOTLY:
                return self._create_interactive_evolution_plot(
                    epoch_projections, sample_size, color_by, session_id
                )
            else:
                return self._create_static_evolution_plot(
                    epoch_projections, sample_size, color_by, session_id
                )
                
        except Exception as e:
            print(f"❌ Error creating embedding evolution plot: {e}")
            return self._create_empty_3d_plot(interactive, f"Error: {str(e)}")

    # =========================================================================
    # Helper Methods for 3D Visualization and Training Movies
    # =========================================================================
    
    def _create_interactive_3d_plot(self, df, x, y, z, color_by, size_by, title, save_path, session_id):
        """Create interactive 3D plot using plotly."""
        if not HAS_PLOTLY:
            print("⚠️ Plotly not available - falling back to matplotlib")
            return self._create_static_3d_plot(df, x, y, z, color_by, size_by, title, save_path, 'notebook', session_id)
        
        # Prepare hover data
        hover_data = ['__featrix_row_id'] if '__featrix_row_id' in df.columns else []
        
        # Create color mapping
        color_data = None
        if color_by and color_by in df.columns:
            color_data = df[color_by]
            hover_data.append(color_by)
        
        # Create size mapping
        size_data = None
        if size_by and size_by in df.columns:
            size_data = df[size_by]
            hover_data.append(size_by)
            # Normalize sizes for better visualization
            size_data = (size_data - size_data.min()) / (size_data.max() - size_data.min()) * 20 + 5
        
        # Create 3D scatter plot
        fig = go.Figure(data=go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers',
            marker=dict(
                size=size_data if size_data is not None else 5,
                color=color_data if color_data is not None else 'blue',
                colorscale='viridis' if color_data is not None else None,
                colorbar=dict(title=color_by) if color_by else None,
                opacity=0.8,
                line=dict(width=0.5, color='white')
            ),
            text=[f"Row ID: {rid}" for rid in df.get('__featrix_row_id', range(len(df)))],
            hovertemplate="<b>Row ID:</b> %{text}<br>" +
                         "<b>X:</b> %{x:.3f}<br>" +
                         "<b>Y:</b> %{y:.3f}<br>" +
                         "<b>Z:</b> %{z:.3f}" +
                         ("<br><b>" + color_by + ":</b> %{marker.color}" if color_by else "") +
                         "<extra></extra>"
        ))
        
        # Update layout
        fig.update_layout(
            title=title or f'3D Embedding Space - Session {session_id[:12]}...',
            scene=dict(
                xaxis_title='Dimension 1',
                yaxis_title='Dimension 2', 
                zaxis_title='Dimension 3',
                bgcolor='white',
                xaxis=dict(gridcolor='lightgray'),
                yaxis=dict(gridcolor='lightgray'),
                zaxis=dict(gridcolor='lightgray')
            ),
            font=dict(size=12),
            width=800,
            height=600,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        if save_path:
            if save_path.endswith('.html'):
                fig.write_html(save_path)
                print(f"🎯 Interactive 3D plot saved to: {save_path}")
            else:
                fig.write_image(save_path, width=1200, height=800)
                print(f"🎯 3D plot image saved to: {save_path}")
        
        return fig

    def _create_static_3d_plot(self, df, x, y, z, color_by, size_by, title, save_path, style, session_id):
        """Create static 3D plot using matplotlib."""
        from mpl_toolkits.mplot3d import Axes3D
        
        self._setup_plot_style(style)
        
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d')
        
        # Prepare color and size data
        colors = 'blue'
        sizes = 50
        
        if color_by and color_by in df.columns:
            colors = df[color_by]
            if df[color_by].dtype == 'object':  # Categorical
                unique_vals = df[color_by].unique()
                color_map = plt.cm.Set3(np.linspace(0, 1, len(unique_vals)))
                colors = [color_map[list(unique_vals).index(val)] for val in df[color_by]]
        
        if size_by and size_by in df.columns:
            sizes = (df[size_by] - df[size_by].min()) / (df[size_by].max() - df[size_by].min()) * 100 + 20
        
        # Create scatter plot
        scatter = ax.scatter(x, y, z, c=colors, s=sizes, alpha=0.7, edgecolors='white', linewidth=0.5)
        
        # Add labels and title
        ax.set_xlabel('Dimension 1', fontweight='bold')
        ax.set_ylabel('Dimension 2', fontweight='bold')
        ax.set_zlabel('Dimension 3', fontweight='bold')
        ax.set_title(title or f'3D Embedding Space - Session {session_id[:12]}...', 
                    fontsize=14, fontweight='bold', pad=20)
        
        # Add colorbar if coloring by a column
        if color_by and color_by in df.columns and df[color_by].dtype != 'object':
            cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
            cbar.set_label(color_by, fontweight='bold')
        
        # Improve 3D visualization
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
            print(f"🎯 3D plot saved to: {save_path}")
        
        return fig

    def _create_empty_3d_plot(self, interactive, message):
        """Create an empty plot with error message."""
        if interactive and HAS_PLOTLY:
            fig = go.Figure()
            fig.add_annotation(
                text=message,
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="red")
            )
            fig.update_layout(
                title="3D Embedding Space - Error",
                scene=dict(
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    zaxis=dict(visible=False)
                )
            )
            return fig
        else:
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')
            ax.text(0.5, 0.5, 0.5, message, transform=ax.transAxes, 
                   ha='center', va='center', fontsize=14, color='red')
            ax.set_title('3D Embedding Space - Error')
            return fig

    def _get_epoch_projections(self, session_id: str) -> Dict[str, Any]:
        """Get epoch projection data for training movies."""
        try:
            # Get epoch projections from the API
            print(f"🔍 Requesting epoch projections for session {session_id[:12]}...")
            response_data = self._get_json(f"/session/{session_id}/epoch_projections")
            epoch_projections = response_data.get('epoch_projections', {})
            
            if epoch_projections:
                print(f"✅ Found {len(epoch_projections)} epoch projections for training movie")
            else:
                print(f"⚠️ No epoch projections found in response")
            
            return epoch_projections
        except Exception as e:
            # Provide helpful messaging based on error type
            error_str = str(e).lower()
            
            if "500" in error_str or "internal server error" in error_str:
                # Check if training is still in progress
                try:
                    session_status = self.get_session_status(session_id)
                    jobs = session_status.jobs
                    
                    # Look for ES training job
                    es_job = None
                    for job_id, job_info in jobs.items():
                        if job_info.get('type') == 'train_es':
                            es_job = job_info
                            break
                    
                    if es_job and es_job.get('status') == 'running':
                        print(f"🔄 ES training in progress - epoch projections will be available as training progresses")
                        print(f"   💡 Try again in a few minutes when training has advanced further")
                        return {}
                    elif es_job and es_job.get('status') == 'done':
                        print(f"⚠️ Epoch projections unavailable - may not have been enabled during training")
                        print(f"   💡 Future sessions will have epoch projections enabled by default")
                        return {}
                    else:
                        print(f"⚠️ No ES training found - epoch projections require embedding space training")
                        return {}
                except:
                    # Fallback to generic message if session status check fails
                    print(f"⚠️ Epoch projections not yet available - training may be in early stages")
                    return {}
            
            elif "404" in error_str or "not found" in error_str:
                print(f"💡 Epoch projections not available - this session may not have ES training")
                print(f"   ℹ️ Epoch projections are generated during embedding space training")
                return {}
            
            else:
                # Other errors - show generic message
                print(f"⚠️ Could not retrieve epoch projections: {e}")
                return {}

    def get_training_movie(self, session_id: str) -> Dict[str, Any]:
        """
        Get ES training movie JSON with complete trajectory data.
        
        Args:
            session_id: Session ID with trained embedding space
            
        Returns:
            Complete training movie data including trajectory, WeightWatcher metrics, etc.
        """
        try:
            response_data = self._get_json(f"/session/{session_id}/training_movie")
            training_movie = response_data.get('training_movie', {})
            
            if training_movie:
                trajectory_length = len(training_movie.get('training_trajectory', []))
                ww_length = len(training_movie.get('weightwatcher_metrics', []))
                print(f"🎬 Retrieved training movie with {trajectory_length} trajectory points and {ww_length} WeightWatcher entries")
            
            return training_movie
        except Exception as e:
            print(f"❌ Could not retrieve training movie: {e}")
            return {}
    
    def _extract_predictor_metadata(self, metrics_data: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
        """
        Extract metadata from training metrics including epochs, validation loss, and job status.
        
        Args:
            metrics_data: Training metrics data from API
            debug: Whether to print debug information
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            'epochs': None,
            'validation_loss': None,
            'training_loss': None,
            'job_status': 'unknown',
            'target_column_type': None,
            'final_metrics': None
        }
        
        try:
            training_metrics = metrics_data.get('training_metrics', {})
            
            # Extract basic info
            metadata['target_column_type'] = training_metrics.get('target_column_type')
            
            # Extract args (contains epochs and other training parameters)
            args = training_metrics.get('args', {})
            if args:
                metadata['epochs'] = args.get('n_epochs', args.get('epochs'))
                metadata['batch_size'] = args.get('batch_size')
                metadata['learning_rate'] = args.get('learning_rate')
            
            # Extract final metrics
            final_metrics = training_metrics.get('final_metrics', {})
            if final_metrics:
                metadata['final_metrics'] = final_metrics
                metadata['accuracy'] = final_metrics.get('accuracy')
                metadata['precision'] = final_metrics.get('precision')
                metadata['recall'] = final_metrics.get('recall')
                metadata['f1'] = final_metrics.get('f1')
                metadata['auc'] = final_metrics.get('auc')
            
            # Extract training info (per-epoch data)
            training_info = training_metrics.get('training_info', [])
            if training_info:
                # Get final epoch data
                last_epoch = training_info[-1] if training_info else {}
                metadata['training_loss'] = last_epoch.get('loss')
                metadata['validation_loss'] = last_epoch.get('validation_loss')
                metadata['actual_epochs'] = len(training_info)  # How many epochs actually completed
                
                # Check if training completed successfully
                if metadata['epochs'] and metadata['actual_epochs']:
                    if metadata['actual_epochs'] >= metadata['epochs']:
                        metadata['job_status'] = 'completed'
                    else:
                        metadata['job_status'] = 'incomplete'
                else:
                    metadata['job_status'] = 'completed'  # Assume completed if we have training data
            
            # Clean up None values for display
            metadata = {k: v for k, v in metadata.items() if v is not None}
            
            if debug:
                print(f"🔍 Extracted metadata: {metadata}")
                
        except Exception as e:
            if debug:
                print(f"⚠️ Error extracting metadata: {e}")
            # Return basic metadata even if extraction fails
            metadata = {'job_status': 'unknown'}
        
        return metadata
    
    def _generate_predictor_id(self, predictor_path: str, predictor_type: str) -> str:
        """
        Generate a unique predictor ID from the predictor path and type.
        
        Args:
            predictor_path: Full path to the predictor file
            predictor_type: Type/category of predictor for uniqueness
            
        Returns:
            Unique predictor ID string
        """
        import hashlib
        import os
        
        # Extract filename from path for readability
        filename = os.path.basename(predictor_path) if predictor_path else 'unknown'
        
        # Create a hash of the full path for uniqueness
        path_hash = hashlib.md5(predictor_path.encode('utf-8')).hexdigest()[:8]
        
        # Combine readable filename with unique hash
        predictor_id = f"{filename}_{path_hash}"
        
        return predictor_id
    
    def _resolve_predictor_id(self, session_id: str, predictor_id: str = None, target_column: str = None, debug: bool = False) -> Dict[str, Any]:
        """
        Resolve predictor_id or target_column to predictor information.
        
        Args:
            session_id: Session ID to check
            predictor_id: Specific predictor ID to resolve
            target_column: Target column name (fallback if predictor_id not provided)
            debug: Whether to print debug information
            
        Returns:
            Dictionary with predictor info including target_column, path, predictor_id
            
        Raises:
            ValueError: If predictor not found or ambiguous
        """
        available_predictors = self._get_available_predictors(session_id, debug=debug)
        
        if not available_predictors:
            raise ValueError(f"No trained predictors found for session {session_id}")
        
        # If predictor_id is provided, find it directly (since it's now the key)
        if predictor_id:
            if predictor_id in available_predictors:
                predictor_info = available_predictors[predictor_id]
                return {
                    'target_column': predictor_info.get('target_column'),
                    'predictor_id': predictor_id,
                    'path': predictor_info.get('path'),
                    'type': predictor_info.get('type')
                }
            
            # Predictor ID not found
            all_predictor_ids = list(available_predictors.keys())
            
            raise ValueError(
                f"Predictor ID '{predictor_id}' not found for session {session_id}. "
                f"Available predictor IDs: {all_predictor_ids}"
            )
        
        # Fallback to target_column validation (search through values)
        if target_column is None:
            # Auto-detect: only valid if there's exactly one predictor
            if len(available_predictors) == 1:
                predictor_id = list(available_predictors.keys())[0]
                predictor_info = available_predictors[predictor_id]
                return {
                    'target_column': predictor_info.get('target_column'),
                    'predictor_id': predictor_id,
                    'path': predictor_info.get('path'),
                    'type': predictor_info.get('type')
                }
            else:
                # Show unique target columns for clarity
                target_columns = list(set(pred.get('target_column') for pred in available_predictors.values()))
                raise ValueError(
                    f"Multiple predictors found for session {session_id} with target columns: {target_columns}. "
                    f"Please specify predictor_id parameter for precise selection."
                )
        else:
            # Find predictors by target column (there might be multiple)
            matching_predictors = {
                pred_id: pred_info for pred_id, pred_info in available_predictors.items()
                if pred_info.get('target_column') == target_column
            }
            
            if not matching_predictors:
                target_columns = list(set(pred.get('target_column') for pred in available_predictors.values()))
                raise ValueError(
                    f"No trained predictor found for target column '{target_column}' in session {session_id}. "
                    f"Available target columns: {target_columns}"
                )
            
            if len(matching_predictors) == 1:
                # Only one predictor for this target column
                predictor_id = list(matching_predictors.keys())[0]
                predictor_info = matching_predictors[predictor_id]
                return {
                    'target_column': target_column,
                    'predictor_id': predictor_id,
                    'path': predictor_info.get('path'),
                    'type': predictor_info.get('type')
                }
            else:
                # Multiple predictors for the same target column
                predictor_ids = list(matching_predictors.keys())
                raise ValueError(
                    f"Multiple predictors found for target column '{target_column}' in session {session_id}: {predictor_ids}. "
                    f"Please specify predictor_id parameter for precise selection."
                )
    
    def list_predictors(self, session_id: str, verbose: bool = True, debug: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        List all available predictors in a session and their target columns.
        
        Args:
            session_id: Session ID to check for predictors
            verbose: Whether to print a formatted summary (default: True)
            debug: Whether to print detailed debug information (default: False)
            
        Returns:
            Dictionary mapping predictor_id -> predictor_info
            
        Example:
            >>> predictors = client.list_predictors(session_id)
            📋 Available Predictors for Session 20250710-231855_c8db67:
            ✅ fuel_card (model.pth_abc12345)
               🆔 Predictor ID: model.pth_abc12345
               Target: fuel_card | Type: single_predictor
               
            >>> # Use programmatically  
            >>> predictors = client.list_predictors(session_id, verbose=False)
            >>> for pred_id, pred_info in predictors.items():
            >>>     print(f"Can use predictor {pred_id} for {pred_info['target_column']}")
            
            >>> # Debug mode for troubleshooting
            >>> predictors = client.list_predictors(session_id, debug=True)
        """
        predictors = self._get_available_predictors(session_id, debug=debug)
        
        if verbose:
            print(f"\n📋 Available Predictors for Session {session_id}:")
            if not predictors:
                print("❌ No trained predictors found")
                print("   💡 Train a single predictor first:")
                print("      client.train_single_predictor(session_id, 'target_column', 'target_type')")
                if debug:
                    print("   🔍 Enable debug mode to see detailed error information:")
                    print("      client.list_predictors(session_id, debug=True)")
            else:
                # Group by target column for cleaner display
                by_target = {}
                for predictor_id, predictor_info in predictors.items():
                    target_col = predictor_info.get('target_column', 'unknown')
                    if target_col not in by_target:
                        by_target[target_col] = []
                    by_target[target_col].append((predictor_id, predictor_info))
                
                for target_column, predictor_list in by_target.items():
                    print(f"🎯 Target Column: {target_column} ({len(predictor_list)} predictor{'s' if len(predictor_list) > 1 else ''})")
                    
                    for predictor_id, predictor_info in predictor_list:
                        print(f"   ✅ {predictor_id}")
                        print(f"      🆔 Predictor ID: {predictor_id}")
                        print(f"      📁 Type: {predictor_info.get('type', 'unknown')}")
                        
                        # Show training metadata
                        job_status = predictor_info.get('job_status', 'unknown')
                        epochs = predictor_info.get('epochs')
                        actual_epochs = predictor_info.get('actual_epochs')
                        validation_loss = predictor_info.get('validation_loss')
                        target_type = predictor_info.get('target_column_type')
                        
                        if job_status:
                            status_emoji = "✅" if job_status == "completed" else "⚠️" if job_status == "incomplete" else "❓"
                            print(f"      📊 Status: {status_emoji} {job_status}")
                        
                        if target_type:
                            print(f"      🎛️  Target Type: {target_type}")
                        
                        if epochs:
                            epoch_info = f"{epochs}"
                            if actual_epochs and actual_epochs != epochs:
                                epoch_info += f" (completed: {actual_epochs})"
                            print(f"      🔄 Epochs: {epoch_info}")
                        
                        if validation_loss is not None:
                            print(f"      📉 Validation Loss: {validation_loss:.4f}")
                        
                        # Show performance metrics if available
                        accuracy = predictor_info.get('accuracy')
                        f1 = predictor_info.get('f1')
                        if accuracy is not None:
                            print(f"      🎯 Accuracy: {accuracy:.3f}")
                        if f1 is not None:
                            print(f"      📈 F1 Score: {f1:.3f}")
                        
                        # Show path information in debug mode
                        if debug:
                            path = predictor_info.get('path', 'No path available')
                            print(f"      📂 Path: {path}")
                        
                        print()  # Add blank line between predictors
        
        return predictors
    
    def get_available_predictors(self, session_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Get available predictors for a session (alias for list_predictors with verbose=False).
        
        Args:
            session_id: Session ID to check for predictors
            
        Returns:
            Dictionary mapping predictor_id -> predictor_info
        """
        return self.list_predictors(session_id, verbose=False)

    def _create_interactive_training_movie(self, training_metrics, epoch_projections, session_id,
                                          show_embedding_evolution, show_loss_evolution):
        """Create interactive training movie widget for notebooks."""
        if not HAS_IPYWIDGETS:
            print("⚠️ ipywidgets not available - falling back to static movie")
            return self._create_static_training_movie(
                training_metrics, epoch_projections, (15, 10), 'notebook',
                None, show_embedding_evolution, show_loss_evolution, 2
            )
        
        # Extract training data
        progress_info = training_metrics.get('progress_info', {})
        loss_history = progress_info.get('loss_history', [])
        training_info = training_metrics.get('training_info', [])
        
        if not loss_history and not training_info:
            return HTML("<div style='color: red;'>No training data available for movie</div>")
        
        # Combine all epochs
        all_epochs = []
        if loss_history:
            all_epochs.extend([entry.get('epoch', 0) for entry in loss_history])
        if training_info:
            all_epochs.extend([entry.get('epoch', 0) for entry in training_info])
        
        if not all_epochs:
            return HTML("<div style='color: red;'>No epoch data found</div>")
        
        max_epoch = max(all_epochs)
        
        # Create interactive widget
        def update_movie(epoch=1):
            """Update movie display for given epoch."""
            try:
                # Create subplot layout
                if show_embedding_evolution and show_loss_evolution:
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
                elif show_loss_evolution:
                    fig, ax1 = plt.subplots(1, 1, figsize=(10, 6))
                    ax2 = None
                else:
                    fig, ax2 = plt.subplots(1, 1, figsize=(8, 6))
                    ax1 = None
                
                # Plot loss evolution up to current epoch
                if show_loss_evolution and ax1 is not None:
                    self._plot_loss_evolution_frame(ax1, loss_history, training_info, epoch)
                
                # Plot embedding evolution for current epoch
                if show_embedding_evolution and ax2 is not None:
                    self._plot_embedding_evolution_frame(ax2, epoch_projections, epoch)
                
                plt.tight_layout()
                plt.show()
                
            except Exception as e:
                print(f"Error in movie frame {epoch}: {e}")
        
        # Create slider widget
        epoch_slider = widgets.IntSlider(
            value=1,
            min=1,
            max=max_epoch,
            step=1,
            description='Epoch:',
            style={'description_width': '60px'},
            layout=Layout(width='500px')
        )
        
        # Add play button and speed control
        play_button = widgets.Play(
            value=1,
            min=1,
            max=max_epoch,
            step=1,
            description="Press play",
            disabled=False,
            interval=500  # milliseconds
        )
        
        speed_slider = widgets.IntSlider(
            value=500,
            min=100,
            max=2000,
            step=100,
            description='Speed (ms):',
            style={'description_width': '80px'},
            layout=Layout(width='300px')
        )
        
        # Link play button to epoch slider
        widgets.jslink((play_button, 'value'), (epoch_slider, 'value'))
        
        # Link speed to play button
        def update_speed(change):
            play_button.interval = change['new']
        speed_slider.observe(update_speed, names='value')
        
        # Create controls layout
        controls = widgets.HBox([
            widgets.VBox([play_button, speed_slider]),
            epoch_slider
        ])
        
        # Display controls and interactive output
        display(controls)
        interact(update_movie, epoch=epoch_slider)
        
        return HTML(f"""
        <div style='background: #f0f8ff; padding: 15px; border-radius: 10px; margin: 10px 0;'>
            <h3>🎬 Interactive Training Movie - Session {session_id[:12]}...</h3>
            <p><strong>Controls:</strong></p>
            <ul>
                <li>Use the <strong>Play button</strong> to automatically advance through epochs</li>
                <li>Adjust <strong>Speed</strong> to control playback rate</li>
                <li>Drag the <strong>Epoch slider</strong> to jump to specific epochs</li>
                <li>Watch how training progresses and embeddings evolve!</li>
            </ul>
        </div>
        """)

    def _create_static_training_movie(self, training_metrics, epoch_projections, figsize, style,
                                     save_path, show_embedding_evolution, show_loss_evolution, fps):
        """Create static training movie animation."""
        import matplotlib.animation as animation
        
        self._setup_plot_style(style)
        
        # Extract training data
        progress_info = training_metrics.get('progress_info', {})
        loss_history = progress_info.get('loss_history', [])
        training_info = training_metrics.get('training_info', [])
        
        # Determine epochs to animate
        all_epochs = set()
        if loss_history:
            all_epochs.update([entry.get('epoch', 0) for entry in loss_history])
        if training_info:
            all_epochs.update([entry.get('epoch', 0) for entry in training_info])
        
        epochs = sorted(list(all_epochs))
        if not epochs:
            fig, ax = plt.subplots(1, 1, figsize=figsize)
            ax.text(0.5, 0.5, 'No training data for animation', transform=ax.transAxes, ha='center', va='center')
            return fig
        
        # Create figure and axes
        if show_embedding_evolution and show_loss_evolution:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        elif show_loss_evolution:
            fig, ax1 = plt.subplots(1, 1, figsize=figsize)
            ax2 = None
        else:
            fig, ax2 = plt.subplots(1, 1, figsize=figsize)
            ax1 = None
        
        def animate(frame):
            """Animation function for each frame."""
            epoch = epochs[frame]
            
            if ax1 is not None:
                ax1.clear()
                self._plot_loss_evolution_frame(ax1, loss_history, training_info, epoch)
            
            if ax2 is not None:
                ax2.clear()
                self._plot_embedding_evolution_frame(ax2, epoch_projections, epoch)
            
            plt.tight_layout()
        
        # Create animation
        anim = animation.FuncAnimation(
            fig, animate, frames=len(epochs), 
            interval=1000//fps, blit=False, repeat=True
        )
        
        if save_path:
            if save_path.endswith('.gif'):
                anim.save(save_path, writer='pillow', fps=fps)
                print(f"🎬 Training movie saved as GIF: {save_path}")
            elif save_path.endswith('.mp4'):
                anim.save(save_path, writer='ffmpeg', fps=fps)
                print(f"🎬 Training movie saved as MP4: {save_path}")
        
        return fig

    def _plot_loss_evolution_frame(self, ax, loss_history, training_info, current_epoch):
        """Plot loss curves up to current epoch."""
        # Plot embedding space loss
        if loss_history:
            es_epochs = [e.get('epoch', 0) for e in loss_history if e.get('epoch', 0) <= current_epoch]
            es_losses = [e.get('loss', 0) for e in loss_history if e.get('epoch', 0) <= current_epoch]
            es_val_losses = [e.get('validation_loss', 0) for e in loss_history if e.get('epoch', 0) <= current_epoch]
            
            if es_epochs:
                ax.plot(es_epochs, es_losses, 'b-', label='ES Training Loss', linewidth=2)
                ax.plot(es_epochs, es_val_losses, 'b--', label='ES Validation Loss', linewidth=2)
        
        # Plot single predictor loss
        if training_info:
            sp_epochs = [e.get('epoch', 0) for e in training_info if e.get('epoch', 0) <= current_epoch]
            sp_losses = [e.get('loss', 0) for e in training_info if e.get('epoch', 0) <= current_epoch]
            sp_val_losses = [e.get('validation_loss', 0) for e in training_info if e.get('epoch', 0) <= current_epoch]
            
            if sp_epochs:
                ax.plot(sp_epochs, sp_losses, 'r-', label='SP Training Loss', linewidth=2)
                ax.plot(sp_epochs, sp_val_losses, 'r--', label='SP Validation Loss', linewidth=2)
        
        ax.set_xlabel('Epoch', fontweight='bold')
        ax.set_ylabel('Loss', fontweight='bold')
        ax.set_title(f'Training Progress - Epoch {current_epoch}', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()

    def _plot_embedding_evolution_frame(self, ax, epoch_projections, current_epoch):
        """Plot 3D embedding space for current epoch."""
        if not epoch_projections:
            ax.text(0.5, 0.5, 'No embedding evolution data', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        # Find projection data for current epoch
        current_projection = None
        for proj_data in epoch_projections.values():
            if proj_data.get('epoch', 0) == current_epoch:
                current_projection = proj_data
                break
        
        if not current_projection:
            ax.text(0.5, 0.5, f'No projection data for epoch {current_epoch}', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        # Extract coordinates
        coords = current_projection.get('coords', [])
        if not coords:
            ax.text(0.5, 0.5, 'No coordinate data', 
                   transform=ax.transAxes, ha='center', va='center')
            return
        
        import pandas as pd
        df = pd.DataFrame(coords)
        
        if 'x' in df.columns and 'y' in df.columns:
            # 2D projection
            ax.scatter(df['x'], df['y'], alpha=0.6, s=20)
            ax.set_xlabel('Dimension 1', fontweight='bold')
            ax.set_ylabel('Dimension 2', fontweight='bold')
        elif all(col in df.columns for col in ['x', 'y', 'z']):
            # 3D projection - project to 2D for display
            ax.scatter(df['x'], df['y'], alpha=0.6, s=20, c=df['z'], cmap='viridis')
            ax.set_xlabel('Dimension 1', fontweight='bold')
            ax.set_ylabel('Dimension 2', fontweight='bold')
        
        ax.set_title(f'Embedding Space - Epoch {current_epoch}', fontweight='bold')
        ax.grid(True, alpha=0.3)

    def _create_interactive_evolution_plot(self, epoch_projections, sample_size, color_by, session_id):
        """Create interactive evolution plot with plotly."""
        if not HAS_PLOTLY:
            return self._create_static_evolution_plot(epoch_projections, sample_size, color_by, session_id)
        
        # Prepare data for all epochs
        all_data = []
        epochs = sorted([v.get('epoch', 0) for v in epoch_projections.values()])
        
        for epoch in epochs:
            # Find data for this epoch
            epoch_data = None
            for proj_data in epoch_projections.values():
                if proj_data.get('epoch', 0) == epoch:
                    epoch_data = proj_data
                    break
            
            if not epoch_data:
                continue
            
            coords = epoch_data.get('coords', [])
            if not coords:
                continue
            
            import pandas as pd
            df = pd.DataFrame(coords)
            
            # Sample if needed
            if len(df) > sample_size:
                df = df.sample(sample_size, random_state=42)
            
            # Add epoch info
            df['epoch'] = epoch
            df['frame'] = epochs.index(epoch)
            
            all_data.append(df)
        
        if not all_data:
            return self._create_empty_3d_plot(True, "No epoch data available")
        
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Create animated 3D scatter plot
        fig = px.scatter_3d(
            combined_df, 
            x='x', y='y', z='z',
            animation_frame='frame',
            color=color_by if color_by and color_by in combined_df.columns else None,
            title=f'Embedding Space Evolution - Session {session_id[:12]}...',
            labels={'x': 'Dimension 1', 'y': 'Dimension 2', 'z': 'Dimension 3'}
        )
        
        # Update layout
        fig.update_layout(
            scene=dict(
                bgcolor='white',
                xaxis=dict(gridcolor='lightgray'),
                yaxis=dict(gridcolor='lightgray'),
                zaxis=dict(gridcolor='lightgray')
            ),
            font=dict(size=12),
            width=900,
            height=700
        )
        
        # Update animation settings
        fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 1000
        fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 500
        
        return fig

    def _create_static_evolution_plot(self, epoch_projections, sample_size, color_by, session_id):
        """Create static evolution plot with matplotlib."""
        epochs = sorted([v.get('epoch', 0) for v in epoch_projections.values()])
        
        if not epochs:
            fig, ax = plt.subplots(1, 1, figsize=(10, 8))
            ax.text(0.5, 0.5, 'No epoch projection data', transform=ax.transAxes, ha='center', va='center')
            return fig
        
        # Create subplot grid
        n_epochs = len(epochs)
        cols = min(4, n_epochs)
        rows = (n_epochs + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(4*cols, 4*rows))
        if rows == 1 and cols == 1:
            axes = [axes]
        elif rows == 1:
            axes = axes
        else:
            axes = axes.flatten()
        
        for i, epoch in enumerate(epochs):
            if i >= len(axes):
                break
                
            ax = axes[i]
            
            # Find data for this epoch
            epoch_data = None
            for proj_data in epoch_projections.values():
                if proj_data.get('epoch', 0) == epoch:
                    epoch_data = proj_data
                    break
            
            if epoch_data:
                coords = epoch_data.get('coords', [])
                if coords:
                    import pandas as pd
                    df = pd.DataFrame(coords)
                    
                    if len(df) > sample_size:
                        df = df.sample(sample_size, random_state=42)
                    
                    if 'x' in df.columns and 'y' in df.columns:
                        scatter = ax.scatter(df['x'], df['y'], alpha=0.6, s=20)
                        ax.set_xlabel('Dimension 1')
                        ax.set_ylabel('Dimension 2')
            
            ax.set_title(f'Epoch {epoch}', fontweight='bold')
            ax.grid(True, alpha=0.3)
        
        # Hide empty subplots
        for i in range(n_epochs, len(axes)):
            axes[i].set_visible(False)
        
        plt.suptitle(f'Embedding Evolution - Session {session_id[:12]}...', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        return fig

    def cancel_job(self, session_id: str, job_type: str) -> Dict[str, Any]:
        """
        Cancel specific job types for a session.
        
        Args:
            session_id: Session ID
            job_type: Type of jobs to cancel (e.g., 'train_single_predictor', 'train_es', 'create_structured_data')
            
        Returns:
            Response with cancellation details
        """
        response_data = self._delete_json(f"/compute/session/{session_id}/cancel_job?job_type={job_type}")
        return response_data

    def train_single_predictor(self, session_id: str, target_column: str, target_column_type: str, 
                              epochs: int = 50, batch_size: int = 256, learning_rate: float = 0.001,
                              validation_ignore_columns: List[str] = None, 
                              poll_interval: int = 30, max_poll_time: int = 3600,
                              verbose: bool = True) -> Dict[str, Any]:
        """
        Add single predictor training to an existing session that has a trained embedding space.
        If a job is already running, will poll for status until completion.
        
        Args:
            session_id: ID of session with trained embedding space
            target_column: Name of the target column to predict
            target_column_type: Type of target column ("set" or "scalar")
            epochs: Number of training epochs (default: 50)
            batch_size: Training batch size (default: 256)
            learning_rate: Learning rate for training (default: 0.001)
            validation_ignore_columns: List of column names to exclude from validation queries (default: None)
            poll_interval: Seconds between status checks when job is already running (default: 30)
            max_poll_time: Maximum time to poll in seconds (default: 3600 = 1 hour)
            verbose: Whether to print status updates during polling (default: True)
            
        Returns:
            Response with training start confirmation or completion status
        """
        import time
        
        data = {
            "target_column": target_column,
            "target_column_type": target_column_type,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "validation_ignore_columns": validation_ignore_columns or []
        }
        
        try:
            # Try to start training
            response_data = self._post_json(f"/compute/session/{session_id}/train_predictor", data)
            return response_data
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if this is a "job already running" error
            if "already running" in error_str or "job plan error" in error_str:
                if verbose:
                    print(f"🔄 Job already running for session {session_id}. Polling for completion...")
                
                # Poll for completion
                start_time = time.time()
                last_status = None
                
                while time.time() - start_time < max_poll_time:
                    try:
                        # Get session status
                        session_status = self.get_session_status(session_id)
                        jobs = session_status.jobs
                        
                        # Check for single predictor jobs
                        sp_jobs = {k: v for k, v in jobs.items() 
                                 if v.get('job_type') == 'train_single_predictor'}
                        
                        if not sp_jobs:
                            if verbose:
                                print("❌ No single predictor jobs found in session")
                            break
                        
                        # Check job statuses
                        running_jobs = []
                        completed_jobs = []
                        failed_jobs = []
                        
                        for job_id, job in sp_jobs.items():
                            status = job.get('status', 'unknown')
                            if status == 'running':
                                running_jobs.append(job_id)
                            elif status == 'done':
                                completed_jobs.append(job_id)
                            elif status == 'failed':
                                failed_jobs.append(job_id)
                        
                        # Update status message
                        current_status = f"Running: {len(running_jobs)}, Done: {len(completed_jobs)}, Failed: {len(failed_jobs)}"
                        if current_status != last_status and verbose:
                            print(f"📊 Status: {current_status}")
                            last_status = current_status
                        
                        # Check if training is complete
                        if not running_jobs and (completed_jobs or failed_jobs):
                            if completed_jobs:
                                if verbose:
                                    print(f"✅ Single predictor training completed successfully!")
                                
                                # Try to get training metrics
                                try:
                                    metrics = self.get_training_metrics(session_id)
                                    return {
                                        "message": "Single predictor training completed successfully",
                                        "session_id": session_id,
                                        "target_column": target_column,
                                        "target_column_type": target_column_type,
                                        "status": "completed",
                                        "training_metrics": metrics
                                    }
                                except Exception as metrics_error:
                                    if verbose:
                                        print(f"⚠️ Training completed but couldn't fetch metrics: {metrics_error}")
                                    return {
                                        "message": "Single predictor training completed successfully",
                                        "session_id": session_id,
                                        "target_column": target_column,
                                        "target_column_type": target_column_type,
                                        "status": "completed"
                                    }
                            else:
                                if verbose:
                                    print(f"❌ Single predictor training failed")
                                return {
                                    "message": "Single predictor training failed",
                                    "session_id": session_id,
                                    "target_column": target_column,
                                    "target_column_type": target_column_type,
                                    "status": "failed",
                                    "failed_jobs": failed_jobs
                                }
                        
                        # Wait before next poll
                        time.sleep(poll_interval)
                        
                    except Exception as poll_error:
                        if verbose:
                            print(f"⚠️ Error during polling: {poll_error}")
                        time.sleep(poll_interval)
                
                # Timeout reached
                if verbose:
                    print(f"⏰ Polling timeout reached ({max_poll_time}s). Training may still be in progress.")
                
                return {
                    "message": f"Polling timeout reached. Training may still be in progress.",
                    "session_id": session_id,
                    "target_column": target_column,
                    "target_column_type": target_column_type,
                    "status": "timeout",
                    "poll_time": max_poll_time
                }
            
            else:
                # Re-raise other errors
                raise e

    # =========================================================================
    # JSON Tables Batch Prediction
    # =========================================================================
    
    def predict_table(self, session_id: str, table_data: Dict[str, Any], max_retries: int = None) -> Dict[str, Any]:
        """
        Make batch predictions using JSON Tables format.
        
        Args:
            session_id: ID of session with trained predictor
            table_data: Data in JSON Tables format, or list of records, or dict with 'table'/'records'
            max_retries: Number of retries for errors (default: uses client default, recommend higher for batch)
            
        Returns:
            Batch prediction results in JSON Tables format
            
        Raises:
            PredictorNotFoundError: If no single predictor has been trained for this session
        """
        # Use higher default for batch operations if not specified
        if max_retries is None:
            max_retries = max(5, self.default_max_retries)
        
        try:
            response_data = self._post_json(f"/session/{session_id}/predict_table", table_data, max_retries=max_retries)
            return response_data
        except Exception as e:
            # Enhanced error handling for common prediction issues
            if "404" in str(e) and "Single predictor not found" in str(e):
                self._raise_predictor_not_found_error(session_id, "predict_table")
            else:
                raise
    
    def predict_records(self, session_id: str, records: List[Dict[str, Any]], 
                       target_column: str = None, predictor_id: str = None, batch_size: int = 2500, use_async: bool = False, 
                       show_progress_bar: bool = True, print_target_column_warning: bool = True) -> Dict[str, Any]:
        """
        Make batch predictions on a list of records with automatic client-side batching.
        
        Args:
            session_id: ID of session with trained predictor
            records: List of record dictionaries
            target_column: Specific target column predictor to use (required if multiple predictors exist and predictor_id not specified)
            predictor_id: Specific predictor ID to use (recommended - more precise than target_column)
            batch_size: Number of records to send per API call (default: 2500)
            use_async: Force async processing for large datasets (default: False - async disabled due to pickle issues)
            show_progress_bar: Whether to show progress bar for async jobs (default: True)
            print_target_column_warning: Whether to print warning when removing target column (default: True)
            
        Returns:
            Batch prediction results (may include job_id for async processing)
            
        Note:
            predictor_id is recommended over target_column for precision. If both are provided, predictor_id takes precedence.
            
        Raises:
            ValueError: If target_column is invalid or multiple predictors exist without specification
        """
        # Clean NaN/Inf values before sending
        cleaned_records = self._clean_numpy_values(records)
        # Additional NaN cleaning for JSON encoding
        cleaned_records = self.replace_nans_with_nulls(cleaned_records)
        
        # Remove target column that would interfere with prediction
        cleaned_records = self._remove_target_columns(session_id, cleaned_records, target_column, print_target_column_warning)
        
        # Determine if we should use async processing
        ASYNC_THRESHOLD = 1000
        total_records = len(cleaned_records)
        
        # DISABLED: Async processing disabled by default due to pickle loading issues
        # If dataset is large and use_async is explicitly True
        if use_async is True and total_records >= ASYNC_THRESHOLD:
            print(f"🚀 Large dataset detected ({total_records} records) - attempting async processing...")
            print("⚠️  WARNING: Async processing may hang due to known pickle issues. Use use_async=False for reliable processing.")
            
            # Try async processing first
            from jsontables import JSONTablesEncoder
            table_data = JSONTablesEncoder.from_records(cleaned_records)
            
            try:
                result = self.predict_table(session_id, table_data)
                
                # Check if server returned an async job
                if result.get('async') and result.get('job_id'):
                    print(f"✅ Async job submitted: {result['job_id']}")
                    print(f"📊 Polling URL: {result.get('polling_url', 'Not provided')}")
                    
                    # Show progress bar by default unless disabled
                    if show_progress_bar:
                        print("\n🚀 Starting job watcher...")
                        return self.watch_prediction_job(session_id, result['job_id'])
                    else:
                        print(f"\n📋 Job submitted. Use client.watch_prediction_job('{session_id}', '{result['job_id']}') to monitor progress.")
                        return result
                else:
                    # Server handled it synchronously, return results
                    return result
                    
            except Exception as e:
                if "404" in str(e) and "Single predictor not found" in str(e):
                    self._raise_predictor_not_found_error(session_id, "predict_records")
                else:
                    print(f"⚠️  Async processing failed, falling back to client-side batching: {e}")
                    # Fall through to client-side batching
        
        # Always use client-side batching for reliable processing
        if total_records >= ASYNC_THRESHOLD:
            print(f"📦 Large dataset detected ({total_records} records) - using reliable synchronous batching...")
            print(f"💡 Processing in chunks of {batch_size} for optimal performance and stability")
        
        # Client-side batching for small datasets or when async is disabled/fails
        if total_records <= batch_size:
            # Small dataset - send all at once
            from jsontables import JSONTablesEncoder
            table_data = JSONTablesEncoder.from_records(cleaned_records)
            
            try:
                return self.predict_table(session_id, table_data)
            except Exception as e:
                if "404" in str(e) and "Single predictor not found" in str(e):
                    self._raise_predictor_not_found_error(session_id, "predict_records")
                else:
                    raise
        
        # Large dataset - use client-side batching
        print(f"📦 Processing {total_records} records in batches of {batch_size}...")
        
        all_predictions = []
        successful_predictions = 0
        failed_predictions = 0
        errors = []
        
        from jsontables import JSONTablesEncoder
        
        # Process in chunks
        for i in range(0, total_records, batch_size):
            chunk_end = min(i + batch_size, total_records)
            chunk_records = cleaned_records[i:chunk_end]
            chunk_size = len(chunk_records)
            
            print(f"  Processing records {i+1}-{chunk_end} ({chunk_size} records)...")
            
            try:
                # Convert chunk to JSON Tables format
                table_data = JSONTablesEncoder.from_records(chunk_records)
                
                # Make prediction
                chunk_result = self.predict_table(session_id, table_data)
                chunk_predictions = chunk_result.get('predictions', [])
                
                # Adjust row indices to match original dataset
                for pred in chunk_predictions:
                    if 'row_index' in pred:
                        pred['row_index'] += i  # Offset by chunk start
                
                all_predictions.extend(chunk_predictions)
                successful_predictions += chunk_result.get('successful_predictions', 0)
                failed_predictions += chunk_result.get('failed_predictions', 0)
                
                if chunk_result.get('errors'):
                    errors.extend(chunk_result['errors'])
                
            except Exception as e:
                if "404" in str(e) and "Single predictor not found" in str(e):
                    self._raise_predictor_not_found_error(session_id, "predict_records")
                else:
                    print(f"    ❌ Chunk {i//batch_size + 1} failed: {e}")
                    
                    # Add failed predictions for this chunk
                    for j in range(chunk_size):
                        all_predictions.append({
                            "row_index": i + j,
                            "prediction_id": None,
                            "prediction": None,
                            "error": str(e)
                        })
                    failed_predictions += chunk_size
                    errors.append(f"Chunk {i//batch_size + 1} (records {i+1}-{chunk_end}): {str(e)}")
        
        print(f"✅ Completed: {successful_predictions} successful, {failed_predictions} failed")
        
        return {
            'predictions': all_predictions,
            'summary': {
                'total_records': total_records,
                'successful_predictions': successful_predictions,
                'failed_predictions': failed_predictions,
                'errors': errors,
                'batched': True,
                'batch_size': batch_size,
                'chunks_processed': (total_records + batch_size - 1) // batch_size
            }
        }
    
    def poll_prediction_job(self, session_id: str, job_id: str, max_wait_time: int = 3600, 
                           check_interval: int = 10) -> Dict[str, Any]:
        """
        Poll a Celery prediction job until completion.
        
        Args:
            session_id: Session ID
            job_id: Celery job ID from async prediction
            max_wait_time: Maximum time to wait in seconds (default: 1 hour)
            check_interval: How often to check status in seconds (default: 10s)
            
        Returns:
            Final job results or status information
        """
        import time
        
        print(f"🔄 Polling prediction job {job_id}...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = self._get_json(f"/session/{session_id}/prediction_job/{job_id}")
                
                status = response.get('status')
                print(f"📊 Status: {status}")
                
                if status == 'completed':
                    print("✅ Prediction job completed successfully!")
                    return response
                elif status == 'failed':
                    print("❌ Prediction job failed!")
                    return response
                elif status == 'running':
                    current = response.get('current', 0)
                    total = response.get('total', 0)
                    message = response.get('message', 'Processing...')
                    
                    if total > 0:
                        progress = response.get('progress_percent', 0)
                        print(f"  🚀 {message} ({current}/{total} - {progress}%)")
                    else:
                        print(f"  🚀 {message}")
                elif status == 'pending':
                    print("  ⏳ Job is waiting to be processed...")
                else:
                    print(f"  ❓ Unknown status: {status}")
                
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"❌ Error checking job status: {e}")
                return {'status': 'error', 'error': str(e)}
        
        print(f"⏰ Timeout after {max_wait_time} seconds")
        return {'status': 'timeout', 'message': f'Job did not complete within {max_wait_time} seconds'}
    
    def watch_prediction_job(self, session_id: str, job_id: str, max_wait_time: int = 3600, 
                            check_interval: int = 5) -> Dict[str, Any]:
        """
        Watch a prediction job with beautiful progress display (similar to training jobs).
        
        Args:
            session_id: Session ID
            job_id: Celery job ID from async prediction
            max_wait_time: Maximum time to wait in seconds (default: 1 hour)
            check_interval: How often to check status in seconds (default: 5s)
            
        Returns:
            Final job results with predictions
        """
        # Use the same smart display logic as training job watching
        if self._is_notebook():
            return self._watch_prediction_job_notebook(session_id, job_id, max_wait_time, check_interval)
        elif self._has_rich():
            return self._watch_prediction_job_rich(session_id, job_id, max_wait_time, check_interval)
        else:
            return self._watch_prediction_job_simple(session_id, job_id, max_wait_time, check_interval)
    
    def _watch_prediction_job_notebook(self, session_id: str, job_id: str, max_wait_time: int, check_interval: int) -> Dict[str, Any]:
        """Watch prediction job with Jupyter notebook display."""
        try:
            from IPython.display import clear_output, display, HTML
            import time
            
            print(f"🔄 Monitoring prediction job {job_id}")
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    response = self._get_json(f"/session/{session_id}/prediction_job/{job_id}")
                    
                    # Clear previous output and show updated status
                    clear_output(wait=True)
                    
                    elapsed = int(time.time() - start_time)
                    mins, secs = divmod(elapsed, 60)
                    
                    status = response.get('status')
                    
                    html_content = f"""
                    <h3>🔄 Prediction Job {job_id[:8]}...</h3>
                    <p><strong>Status:</strong> {status} | <strong>Elapsed:</strong> {mins:02d}:{secs:02d}</p>
                    """
                    
                    if status == 'running':
                        current = response.get('current', 0)
                        total = response.get('total', 0)
                        message = response.get('message', 'Processing...')
                        
                        if total > 0:
                            progress_pct = (current / total) * 100
                            progress_bar = "▓" * int(progress_pct / 5) + "░" * (20 - int(progress_pct / 5))
                            html_content += f"""
                            <p><strong>Progress:</strong> {current:,}/{total:,} records ({progress_pct:.1f}%)</p>
                            <p><code>[{progress_bar}]</code></p>
                            <p><em>{message}</em></p>
                            """
                        else:
                            html_content += f"<p><em>{message}</em></p>"
                    
                    display(HTML(html_content))
                    
                    # Check completion
                    if status == 'completed':
                        print(f"✅ Prediction job completed successfully!")
                        return response
                    elif status == 'failed':
                        print(f"❌ Prediction job failed!")
                        return response
                    
                    time.sleep(check_interval)
                    
                except Exception as e:
                    print(f"❌ Error checking job status: {e}")
                    return {'status': 'error', 'error': str(e)}
            
            print(f"⏰ Timeout after {max_wait_time} seconds")
            return {'status': 'timeout', 'message': f'Job did not complete within {max_wait_time} seconds'}
            
        except ImportError:
            # Fallback if IPython not available
            return self._watch_prediction_job_simple(session_id, job_id, max_wait_time, check_interval)
    
    def _watch_prediction_job_rich(self, session_id: str, job_id: str, max_wait_time: int, check_interval: int) -> Dict[str, Any]:
        """Watch prediction job with Rich progress bars."""
        try:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
            from rich.console import Console
            import time
            
            console = Console()
            start_time = time.time()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                expand=True
            ) as progress:
                
                # Main prediction task
                task = progress.add_task(f"[bold green]Prediction Job {job_id[:8]}...", total=100)
                
                while time.time() - start_time < max_wait_time:
                    try:
                        response = self._get_json(f"/session/{session_id}/prediction_job/{job_id}")
                        
                        status = response.get('status')
                        
                        if status == 'running':
                            current = response.get('current', 0)
                            total = response.get('total', 0)
                            message = response.get('message', 'Processing...')
                            
                            if total > 0:
                                progress_pct = (current / total) * 100
                                progress.update(task, completed=progress_pct,
                                              description=f"[bold green]Processing {current:,}/{total:,} records")
                            else:
                                progress.update(task, description=f"[bold green]{message}")
                        
                        elif status == 'pending':
                            progress.update(task, description="[bold yellow]Waiting to start...")
                        
                        elif status == 'completed':
                            progress.update(task, completed=100,
                                          description="[bold green]✅ Prediction job completed!")
                            console.print("🎉 [bold green]Success![/bold green] Predictions are ready.")
                            return response
                        
                        elif status == 'failed':
                            progress.update(task, description="[bold red]❌ Prediction job failed!")
                            console.print("💥 [bold red]Failed![/bold red] Check error details.")
                            return response
                        
                        time.sleep(check_interval)
                        
                    except Exception as e:
                        console.print(f"[bold red]❌ Error checking job status: {e}[/bold red]")
                        return {'status': 'error', 'error': str(e)}
                
                console.print(f"[bold yellow]⏰ Timeout after {max_wait_time} seconds[/bold yellow]")
                return {'status': 'timeout', 'message': f'Job did not complete within {max_wait_time} seconds'}
                
        except ImportError:
            # Fallback if rich not available
            return self._watch_prediction_job_simple(session_id, job_id, max_wait_time, check_interval)
    
    def _watch_prediction_job_simple(self, session_id: str, job_id: str, max_wait_time: int, check_interval: int) -> Dict[str, Any]:
        """Watch prediction job with simple terminal display."""
        import sys
        import time
        
        print(f"🔄 Watching prediction job {job_id}")
        start_time = time.time()
        last_num_lines = 0
        
        while time.time() - start_time < max_wait_time:
            try:
                response = self._get_json(f"/session/{session_id}/prediction_job/{job_id}")
                
                # Clear previous lines if terminal supports it
                if sys.stdout.isatty() and last_num_lines > 0:
                    for _ in range(last_num_lines):
                        sys.stdout.write('\033[F')  # Move cursor up
                        sys.stdout.write('\033[2K')  # Clear line
                
                # Build status display
                elapsed = int(time.time() - start_time)
                mins, secs = divmod(elapsed, 60)
                
                status = response.get('status')
                
                lines = []
                lines.append(f"🔄 Prediction Job {job_id[:8]}... | Status: {status} | Elapsed: {mins:02d}:{secs:02d}")
                
                if status == 'running':
                    current = response.get('current', 0)
                    total = response.get('total', 0)
                    message = response.get('message', 'Processing...')
                    
                    if total > 0:
                        progress_pct = (current / total) * 100
                        progress_bar = "█" * int(progress_pct / 5) + "░" * (20 - int(progress_pct / 5))
                        lines.append(f"  Progress: {current:,}/{total:,} records ({progress_pct:.1f}%)")
                        lines.append(f"  [{progress_bar}]")
                    
                    lines.append(f"  {message}")
                
                elif status == 'pending':
                    lines.append("  ⏳ Waiting for worker to start processing...")
                
                # Print all lines
                for line in lines:
                    print(line)
                
                last_num_lines = len(lines)
                
                # Check completion
                if status == 'completed':
                    print(f"\n✅ Prediction job completed successfully!")
                    return response
                elif status == 'failed':
                    print(f"\n❌ Prediction job failed!")
                    return response
                
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"\n❌ Error checking job status: {e}")
                return {'status': 'error', 'error': str(e)}
        
        print(f"\n⏰ Timeout after {max_wait_time} seconds")
        return {'status': 'timeout', 'message': f'Job did not complete within {max_wait_time} seconds'}
    
    def predict_df(self, session_id: str, df, target_column: str = None, predictor_id: str = None, show_progress_bar: bool = True, print_target_column_warning: bool = True) -> Dict[str, Any]:
        """
        Make batch predictions on a pandas DataFrame.
        
        Args:
            session_id: ID of session with trained predictor
            df: Pandas DataFrame
            target_column: Specific target column predictor to use (required if multiple predictors exist and predictor_id not specified)
            predictor_id: Specific predictor ID to use (recommended - more precise than target_column)
            show_progress_bar: Whether to show progress bar for async jobs (default: True)
            print_target_column_warning: Whether to print warning when removing target column (default: True)
            
        Returns:
            Batch prediction results
            
        Raises:
            ValueError: If target_column is invalid or multiple predictors exist without specification
            
        Note:
            predictor_id is recommended over target_column for precision. If both are provided, predictor_id takes precedence.
        """
        # Convert DataFrame to records and clean NaN/Inf values
        records = df.to_dict(orient='records')
        # Clean NaNs for JSON encoding
        cleaned_records = self.replace_nans_with_nulls(records)
        return self.predict_records(session_id, cleaned_records, target_column=target_column, predictor_id=predictor_id, show_progress_bar=show_progress_bar, print_target_column_warning=print_target_column_warning)
    
    def _raise_predictor_not_found_error(self, session_id: str, method_name: str):
        """
        Raise a helpful error message when a single predictor is not found.
        
        Args:
            session_id: ID of the session
            method_name: Name of the method that was called
        """
        # Try to get session status to provide better guidance
        try:
            status = self.get_session_status(session_id)
            has_embedding = any('train_es' in job_id or 'embedding' in job.get('type', '') 
                              for job_id, job in status.jobs.items())
            has_predictor = any('train_single_predictor' in job_id or 'single_predictor' in job.get('type', '') 
                               for job_id, job in status.jobs.items())
            
            if not has_embedding:
                error_msg = f"""
❌ No trained model found for session {session_id}

🔍 ISSUE: This session doesn't have a trained embedding space yet.

🛠️  SOLUTION: Wait for training to complete, or start training:
   1. Check session status: client.get_session_status('{session_id}')
   2. Wait for completion: client.wait_for_session_completion('{session_id}')

📊 Current session jobs: {len(status.jobs)} jobs, status: {status.status}
"""
            elif not has_predictor:
                error_msg = f"""
❌ No single predictor found for session {session_id}

🔍 ISSUE: This session has a trained embedding space but no single predictor.

🛠️  SOLUTION: Train a single predictor first:
   client.train_single_predictor('{session_id}', 'target_column_name', 'set')
   
   Replace 'target_column_name' with your actual target column.
   Use 'set' for classification or 'scalar' for regression.

📊 Session has embedding space but needs predictor training.
"""
            else:
                error_msg = f"""
❌ Single predictor not ready for session {session_id}

🔍 ISSUE: Predictor training may still be in progress or failed.

🛠️  SOLUTION: Check training status:
   1. Check status: client.get_session_status('{session_id}')
   2. Check training metrics: client.get_training_metrics('{session_id}')
   3. Wait for completion if still training

📊 Found predictor job but prediction failed - training may be incomplete.
"""
                
        except Exception:
            # Fallback error message if we can't get session info
            error_msg = f"""
❌ Single predictor not found for session {session_id}

🔍 ISSUE: No trained single predictor available for predictions.

🛠️  SOLUTIONS:
   1. Train a single predictor:
      client.train_single_predictor('{session_id}', 'target_column', 'set')
   
   2. Check if training is still in progress:
      client.get_session_status('{session_id}')
   
   3. Create a new session if this one is corrupted:
      session = client.upload_df_and_create_session(df=your_data)
      client.train_single_predictor(session.session_id, 'target_column', 'set')

💡 TIP: Use 'set' for classification, 'scalar' for regression.
"""
        
        # Create a custom exception class for better error handling
        class PredictorNotFoundError(Exception):
            def __init__(self, message):
                super().__init__(message)
                self.session_id = session_id
                self.method_name = method_name
        
        raise PredictorNotFoundError(error_msg.strip())
    
    def _get_available_predictors(self, session_id: str, debug: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Get all available predictors for a session from the server.
        
        Args:
            session_id: ID of the session
            debug: Whether to print detailed debug information
            
        Returns:
            Dictionary mapping predictor_id -> predictor_info
        """
        try:
            # First try to get predictor info from session models endpoint
            response_data = self._get_json(f"/session/{session_id}/models")
            models = response_data.get('models', {})
            
            predictors = {}
            
            if debug:
                # Debug: Print what we got from models endpoint
                print(f"🔍 Debug: Session models structure:")
                for key, value in models.items():
                    if isinstance(value, dict):
                        print(f"   {key}: {value.get('available', 'no available field')} - {value.get('path', 'no path')}")
                    else:
                        print(f"   {key}: {value}")
            
            # Check for single predictor (old format)
            single_predictor = models.get('single_predictor', {})
            if debug:
                print(f"🔍 Debug: single_predictor available = {single_predictor.get('available')}")
            if single_predictor.get('available'):
                # Need to load the actual predictor to get target column
                try:
                    session_data = self._get_json(f"/session/{session_id}", max_retries=8)
                    session = session_data.get('session', {})
                    
                    # Check if we have target column info in training metrics
                    training_metrics = models.get('training_metrics', {})
                    if debug:
                        print(f"🔍 Debug: training_metrics available = {training_metrics.get('available')}")
                    if training_metrics.get('available'):
                        metrics_data = self.get_training_metrics(session_id)
                        if debug:
                            print(f"🔍 Debug: metrics_data keys = {list(metrics_data.keys())}")
                        training_metrics_inner = metrics_data.get('training_metrics', {})
                        if debug:
                            print(f"🔍 Debug: training_metrics_inner keys = {list(training_metrics_inner.keys()) if training_metrics_inner else 'None'}")
                        target_column = training_metrics_inner.get('target_column')
                        if debug:
                            print(f"🔍 Debug: extracted target_column = {target_column}")
                        if target_column:
                            # Extract metadata from training metrics
                            metadata = self._extract_predictor_metadata(metrics_data, debug)
                            
                            # Generate unique predictor ID
                            predictor_path = single_predictor.get('path', '')
                            predictor_id = self._generate_predictor_id(predictor_path, 'single_predictor')
                            
                            predictors[predictor_id] = {
                                'predictor_id': predictor_id,
                                'path': predictor_path,
                                'target_column': target_column,
                                'available': True,
                                'type': 'single_predictor',
                                **metadata  # Include epochs, validation_loss, job_status, etc.
                            }
                            if debug:
                                print(f"✅ Added single predictor for target_column: {target_column}")
                                print(f"   Predictor ID: {predictor_id}")
                                print(f"   Metadata: {metadata}")
                except Exception as e:
                    print(f"Warning: Could not extract target column from single predictor: {e}")
            
            # Check for multiple predictors (new format)
            # Look at session info to get single_predictors array
            try:
                session_data = self._get_json(f"/session/{session_id}", max_retries=8)
                session = session_data.get('session', {})
                
                # New format: single_predictors array
                single_predictors_paths = session.get('single_predictors', [])
                if debug:
                    print(f"🔍 Debug: single_predictors array = {single_predictors_paths}")
                if single_predictors_paths:
                    # Try to get target column info from training metrics
                    training_metrics = models.get('training_metrics', {})
                    if training_metrics.get('available'):
                        try:
                            metrics_data = self.get_training_metrics(session_id)
                            target_column = metrics_data.get('training_metrics', {}).get('target_column')
                            if target_column:
                                # Extract metadata from training metrics
                                metadata = self._extract_predictor_metadata(metrics_data, debug)
                                
                                # Add each predictor individually with its own predictor_id key
                                for i, path in enumerate(single_predictors_paths):
                                    predictor_id = self._generate_predictor_id(path, f'multiple_predictor_{i}')
                                    
                                    predictors[predictor_id] = {
                                        'predictor_id': predictor_id,
                                        'path': path,
                                        'target_column': target_column,
                                        'available': True,
                                        'type': 'single_predictor',  # Each is treated as individual predictor
                                        'predictor_index': i,  # Track original index for compatibility
                                        **metadata  # Include epochs, validation_loss, job_status, etc.
                                    }
                                    if debug:
                                        print(f"✅ Added predictor {i} for target_column: {target_column}")
                                        print(f"   Predictor ID: {predictor_id}")
                                        print(f"   Path: {path}")
                                
                                if debug:
                                    print(f"   Total predictors added: {len(single_predictors_paths)}")
                                    print(f"   Shared metadata: {metadata}")
                        except Exception as e:
                            print(f"Warning: Could not extract target column from training metrics: {e}")
                
                # Fallback: check old format single_predictor field
                single_predictor_path = session.get('single_predictor')
                if debug:
                    print(f"🔍 Debug: legacy single_predictor path = {single_predictor_path}")
                if single_predictor_path and not predictors:
                    # Try to get target column from training metrics
                    try:
                        training_metrics = models.get('training_metrics', {})
                        if training_metrics.get('available'):
                            metrics_data = self.get_training_metrics(session_id)
                            target_column = metrics_data.get('training_metrics', {}).get('target_column')
                            if target_column:
                                # Extract metadata from training metrics
                                metadata = self._extract_predictor_metadata(metrics_data, debug)
                                
                                # Generate unique predictor ID
                                predictor_id = self._generate_predictor_id(single_predictor_path, 'single_predictor_legacy')
                                
                                predictors[predictor_id] = {
                                    'predictor_id': predictor_id,
                                    'path': single_predictor_path,
                                    'target_column': target_column,
                                    'available': True,
                                    'type': 'single_predictor_legacy',
                                    **metadata  # Include epochs, validation_loss, job_status, etc.
                                }
                                if debug:
                                    print(f"✅ Added legacy single predictor for target_column: {target_column}")
                                    print(f"   Predictor ID: {predictor_id}")
                                    print(f"   Metadata: {metadata}")
                    except Exception as e:
                        print(f"Warning: Could not extract target column from legacy predictor: {e}")
                        
            except Exception as e:
                print(f"Warning: Could not get session data: {e}")
            
            if debug:
                print(f"🔍 Debug: Final predictors = {predictors}")
            return predictors
            
        except Exception as e:
            print(f"Warning: Could not fetch predictors from server: {e}")
            return {}
    
    def _validate_and_get_target_column(self, session_id: str, target_column: str = None) -> str:
        """
        Validate that a predictor exists for the target column and return the column name.
        
        Args:
            session_id: ID of the session
            target_column: Specific target column to validate, or None for auto-detect
            
        Returns:
            Validated target column name
            
        Raises:
            ValueError: If target_column is invalid or multiple predictors exist without specification
        """
        available_predictors = self._get_available_predictors(session_id)
        
        if not available_predictors:
            raise ValueError(f"No trained predictors found for session {session_id}")
        
        if target_column is None:
            # Auto-detect: only valid if there's exactly one predictor
            if len(available_predictors) == 1:
                return list(available_predictors.keys())[0]
            else:
                available_columns = list(available_predictors.keys())
                raise ValueError(
                    f"Multiple predictors found for session {session_id}: {available_columns}. "
                    f"Please specify target_column parameter."
                )
        else:
            # Validate specified target column
            if target_column not in available_predictors:
                available_columns = list(available_predictors.keys())
                raise ValueError(
                    f"No trained predictor found for target column '{target_column}' in session {session_id}. "
                    f"Available predictors: {available_columns}"
                )
            return target_column
    
    def _remove_target_columns(self, session_id: str, records: List[Dict[str, Any]], target_column: str = None, print_warning: bool = True) -> List[Dict[str, Any]]:
        """
        Remove target column from prediction records to avoid model conflicts.
        Validates that the predictor exists and removes the appropriate target column.
        
        Args:
            session_id: ID of the session
            records: List of record dictionaries
            target_column: Specific target column to remove, or None for auto-detect
            print_warning: Whether to print warning when removing target column (default: True)
            
        Returns:
            Cleaned records with target column removed
        """
        if not records:
            return records
            
        # Validate and get the target column name
        try:
            validated_target_column = self._validate_and_get_target_column(session_id, target_column)
        except ValueError as e:
            # Re-raise validation errors
            raise e
        
        if validated_target_column in records[0]:
            if print_warning:
                print(f"⚠️  Warning: Removing target column '{validated_target_column}' from prediction data")
                print(f"   This column would interfere with model predictions.")
            
            # Remove target column from all records
            cleaned_records = []
            for record in records:
                cleaned_record = {k: v for k, v in record.items() if k != validated_target_column}
                cleaned_records.append(cleaned_record)
            return cleaned_records
        
        return records
    
    def _clean_numpy_values(self, data):
        """
        Recursively clean NaN, Inf, and other non-JSON-serializable values from data.
        Converts them to None which is JSON serializable.
        
        Args:
            data: Data structure to clean (dict, list, or primitive)
            
        Returns:
            Cleaned data structure
        """
        import math
        import numpy as np
        
        if isinstance(data, dict):
            return {k: self._clean_numpy_values(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_numpy_values(v) for v in data]
        elif isinstance(data, (float, np.floating)):
            if math.isnan(data) or math.isinf(data):
                return None
            return float(data)  # Convert numpy floats to Python floats
        elif isinstance(data, (int, np.integer)):
            return int(data)  # Convert numpy ints to Python ints
        elif isinstance(data, (bool, np.bool_)):
            return bool(data)  # Convert numpy bools to Python bools
        elif isinstance(data, np.ndarray):
            return self._clean_numpy_values(data.tolist())  # Convert arrays to lists
        elif data is None or isinstance(data, (str, bool)):
            return data
        else:
            # Handle other numpy types or unknown types
            try:
                # Try to convert to a basic Python type
                if hasattr(data, 'item'):  # numpy scalar
                    value = data.item()
                    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                        return None
                    return value
                else:
                    return data
            except:
                # If all else fails, convert to string
                return str(data)
    
    def replace_nans_with_nulls(self, data):
        """
        Recursively replace NaN values with None/null for JSON encoding.
        This prevents JSON encoding errors when DataFrames contain NaN values.
        
        Args:
            data: Data structure to clean (dict, list, or primitive)
            
        Returns:
            Cleaned data structure with NaNs replaced by None
        """
        import math
        
        if isinstance(data, dict):
            return {k: self.replace_nans_with_nulls(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.replace_nans_with_nulls(v) for v in data]
        elif isinstance(data, float) and math.isnan(data):
            return None
        else:
            return data
    
    def predict_csv_file(self, session_id: str, file_path: Path) -> Dict[str, Any]:
        """
        Make batch predictions on a CSV file.
        
        Args:
            session_id: ID of session with trained predictor
            file_path: Path to CSV file
            
        Returns:
            Batch prediction results
        """
        import pandas as pd
        from jsontables import JSONTablesEncoder
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        df = pd.read_csv(file_path)
        
        # Convert to JSON Tables format and clean NaNs
        table_data = JSONTablesEncoder.from_dataframe(df)
        cleaned_table_data = self.replace_nans_with_nulls(table_data)
        
        return self.predict_table(session_id, cleaned_table_data)

    def run_predictions(self, session_id: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run predictions on provided records. Clean and fast for production use.
        
        Args:
            session_id: ID of session with trained predictor
            records: List of record dictionaries
            
        Returns:
            Dictionary with prediction results
        """
        # Clean NaNs for JSON encoding
        cleaned_records = self.replace_nans_with_nulls(records)
        
        # Make batch predictions
        batch_results = self.predict_records(session_id, cleaned_records)
        predictions = batch_results['predictions']
        
        # Process predictions into clean format
        results = []
        for pred in predictions:
            if pred['prediction']:
                record_idx = pred['row_index']
                prediction = pred['prediction']
                predicted_class = max(prediction, key=prediction.get)
                confidence = prediction[predicted_class]
                
                results.append({
                    'record_index': record_idx,
                    'predicted_class': predicted_class,
                    'confidence': confidence,
                    'full_prediction': prediction,
                    'error': batch_results.get('error', None),
                    'full_prediction': pred
                })
        
        return {
            'predictions': results,
            'total_records': len(records),
            'successful_predictions': len(results),
            'failed_predictions': len(records) - len(results)
        }

    def update_prediction_label(self, prediction_id: str, user_label: str) -> Dict[str, Any]:
        """
        Update the label for a prediction to enable retraining.
        
        Args:
            prediction_id: UUID of the prediction to update
            user_label: Correct label provided by user
            
        Returns:
            Update confirmation with prediction details
        """
        data = {
            "prediction_id": prediction_id,
            "user_label": user_label
        }
        response_data = self._post_json(f"/compute/prediction/{prediction_id}/update_label", data)
        return response_data
    
    def get_session_predictions(self, session_id: str, corrected_only: bool = False, limit: int = 100) -> Dict[str, Any]:
        """
        Get predictions for a session, optionally filtered for corrected ones.
        
        Args:
            session_id: ID of session
            corrected_only: Only return predictions with user corrections
            limit: Maximum number of predictions to return
            
        Returns:
            List of predictions with metadata
        """
        params = {
            "corrected_only": corrected_only,
            "limit": limit
        }
        response_data = self._get_json(f"/session/{session_id}/predictions", params=params)
        return response_data
    
    def create_retraining_batch(self, session_id: str) -> Dict[str, Any]:
        """
        Create a retraining batch from corrected predictions.
        
        Args:
            session_id: ID of session with corrected predictions
            
        Returns:
            Retraining batch information
        """
        response_data = self._post_json(f"/session/{session_id}/create_retraining_batch", {})
        return response_data

    def evaluate_predictions(self, session_id: str, records: List[Dict[str, Any]], 
                           actual_values: List[str], target_column: str = None) -> Dict[str, Any]:
        """
        Evaluate predictions with accuracy calculation. Use this for testing/validation.
        
        Args:
            session_id: ID of session with trained predictor
            records: List of record dictionaries
            actual_values: List of actual target values for accuracy calculation
            target_column: Name of target column (for display purposes)
            
        Returns:
            Dictionary with prediction results and accuracy metrics
        """
        # Get predictions
        pred_results = self.run_predictions(session_id, records)
        
        # Calculate accuracy
        correct_predictions = 0
        total_predictions = 0
        confidence_scores = []
        
        for pred in pred_results['predictions']:
            record_idx = pred['record_index']
            if record_idx < len(actual_values):
                predicted_class = pred['predicted_class']
                actual = str(actual_values[record_idx])
                confidence = pred['confidence']
                
                confidence_scores.append(confidence)
                total_predictions += 1
                
                if predicted_class == actual:
                    correct_predictions += 1
        
        # Add accuracy metrics
        if total_predictions > 0:
            accuracy = correct_predictions / total_predictions
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            
            pred_results['accuracy_metrics'] = {
                'accuracy': accuracy,
                'correct_predictions': correct_predictions,
                'total_predictions': total_predictions,
                'average_confidence': avg_confidence,
                'target_column': target_column
            }
        
        return pred_results

    def run_csv_predictions(self, session_id: str, csv_file: str, target_column: str = None,
                           sample_size: int = None, remove_target: bool = True) -> Dict[str, Any]:
        """
        Run predictions on a CSV file with automatic accuracy calculation.
        
        Args:
            session_id: ID of session with trained predictor
            csv_file: Path to CSV file
            target_column: Name of target column (for accuracy calculation)
            sample_size: Number of records to test (None = all records)
            remove_target: Whether to remove target column from prediction input
            
        Returns:
            Dictionary with prediction results and accuracy metrics
        """
        import pandas as pd
        
        # Load CSV
        df = pd.read_csv(csv_file)
        
        # Handle target column
        actual_values = None
        if target_column and target_column in df.columns:
            actual_values = df[target_column].tolist()
            if remove_target:
                prediction_df = df.drop(target_column, axis=1)
            else:
                prediction_df = df
        else:
            prediction_df = df
        
        # Take sample ONLY if explicitly requested
        if sample_size and sample_size < len(prediction_df):
            sample_df = prediction_df.head(sample_size)
            if actual_values:
                actual_values = actual_values[:sample_size]
        else:
            sample_df = prediction_df
        
        # Convert to records
        records = sample_df.to_dict('records')
        
        # Run predictions with accuracy calculation
        return self.evaluate_predictions(
            session_id=session_id,
            records=records,
            actual_values=actual_values,
            target_column=target_column
        )

    def run_comprehensive_test(self, session_id: str, test_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run a comprehensive test of the single predictor including individual and batch predictions.
        
        Args:
            session_id: ID of session with trained predictor
            test_data: Optional dict with 'csv_file', 'target_column', 'sample_size', 'test_records'
            
        Returns:
            Comprehensive test results
        """
        print("🧪 " + "="*60)
        print("🧪 COMPREHENSIVE SINGLE PREDICTOR TEST")
        print("🧪 " + "="*60)
        
        results = {
            'session_id': session_id,
            'individual_tests': [],
            'batch_test': None,
            'training_metrics': None,
            'session_models': None
        }
        
        # 1. Check session models
        print("\n1. 📦 Checking available models...")
        try:
            models_info = self.get_session_models(session_id)
            results['session_models'] = models_info
        except Exception as e:
            print(f"Error checking models: {e}")
        
        # 2. Get training metrics
        print("\n2. 📊 Getting training metrics...")
        try:
            metrics = self.get_training_metrics(session_id)
            results['training_metrics'] = metrics
            
            training_metrics = metrics['training_metrics']
            print(f"Target column: {training_metrics.get('target_column')}")
            print(f"Target type: {training_metrics.get('target_column_type')}")
            print(f"Training epochs: {len(training_metrics.get('training_info', []))}")
        except Exception as e:
            print(f"Error getting training metrics: {e}")
        
        # 3. Individual prediction tests
        print("\n3. 🎯 Testing individual predictions...")
        
        # Default test records if none provided
        default_test_records = [
            {"domain": "shell.com", "snippet": "fuel card rewards program", "keyword": "fuel card"},
            {"domain": "exxon.com", "snippet": "gas station locator and fuel cards", "keyword": "gas station"},
            {"domain": "amazon.com", "snippet": "buy books online", "keyword": "books"},
            {"domain": "bp.com", "snippet": "fleet fuel cards for business", "keyword": "fleet cards"},
        ]
        
        test_records = test_data.get('test_records', default_test_records) if test_data else default_test_records
        
        for i, record in enumerate(test_records):
            try:
                result = self.predict(session_id, record)
                prediction = result['prediction']
                
                # Get predicted class and confidence
                predicted_class = max(prediction, key=prediction.get)
                confidence = prediction[predicted_class]
                
                test_result = {
                    'record': record,
                    'prediction': prediction,
                    'predicted_class': predicted_class,
                    'confidence': confidence,
                    'success': True
                }
                
                results['individual_tests'].append(test_result)
                print(f"✅ Record {i+1}: {predicted_class} ({confidence*100:.1f}%)")
                
            except Exception as e:
                test_result = {
                    'record': record,
                    'error': str(e),
                    'success': False
                }
                results['individual_tests'].append(test_result)
                print(f"❌ Record {i+1}: Error - {e}")
        
        # 4. Batch prediction test
        print("\n4. 📊 Testing batch predictions...")
        
        if test_data and test_data.get('csv_file'):
            try:
                batch_results = self.run_csv_predictions(
                    session_id=session_id,
                    csv_file=test_data['csv_file'],
                    target_column=test_data.get('target_column'),
                    sample_size=test_data.get('sample_size', 100)
                )
                results['batch_test'] = batch_results
                
                # Summary
                if batch_results.get('accuracy_metrics'):
                    acc = batch_results['accuracy_metrics']
                    print(f"✅ Batch test completed: {acc['accuracy']*100:.2f}% accuracy")
                else:
                    print(f"✅ Batch test completed: {batch_results['successful_predictions']} predictions")
                    
            except Exception as e:
                print(f"❌ Batch test failed: {e}")
                results['batch_test'] = {'error': str(e)}
        else:
            print("📝 No CSV file provided for batch testing")
        
        # 5. Summary
        print("\n" + "="*60)
        print("📋 TEST SUMMARY")
        print("="*60)
        
        individual_success = sum(1 for t in results['individual_tests'] if t['success'])
        print(f"Individual predictions: {individual_success}/{len(results['individual_tests'])} successful")
        
        if results['batch_test'] and 'accuracy_metrics' in results['batch_test']:
            acc = results['batch_test']['accuracy_metrics']
            print(f"Batch prediction accuracy: {acc['accuracy']*100:.2f}%")
            print(f"Average confidence: {acc['average_confidence']*100:.2f}%")
        
        if results['training_metrics']:
            tm = results['training_metrics']['training_metrics']
            print(f"Model trained on: {tm.get('target_column')} ({tm.get('target_column_type')})")
        
        print("\n🎉 Comprehensive test completed!")
        
        return results

    # =========================================================================
    # Other API Endpoints
    # =========================================================================
    
    def encode_records(self, session_id: str, query_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encode records using the embedding space.
        
        Args:
            session_id: ID of session with trained embedding space
            query_record: Record to encode
            
        Returns:
            Encoded vector representation
        """
        data = {"query_record": query_record}
        response_data = self._post_json(f"/session/{session_id}/encode_records", data)
        return response_data
    
    def similarity_search(self, session_id: str, query_record: Dict[str, Any], k: int = 5) -> Dict[str, Any]:
        """
        Find similar records using vector similarity search.
        
        Args:
            session_id: ID of session with trained embedding space and vector DB
            query_record: Record to find similarities for
            k: Number of similar records to return
            
        Returns:
            List of similar records with distances
        """
        data = {"query_record": query_record}
        response_data = self._post_json(f"/session/{session_id}/similarity_search", data)
        return response_data
    
    def get_projections(self, session_id: str) -> Dict[str, Any]:
        """
        Get 2D projections for visualization.
        
        Args:
            session_id: ID of session with generated projections
            
        Returns:
            Projection data for visualization
        """
        response_data = self._get_json(f"/session/{session_id}/projections")
        return response_data

    def flush_predict_queues(self, session_id: str, show_progress: bool = True) -> Dict[str, Any]:
        """
        Process all queued predictions for a session using efficient batching.
        
        Args:
            session_id: ID of session with queued predictions
            show_progress: Whether to show progress for batch processing
            
        Returns:
            Dictionary with prediction results mapped by queue_id
        """
        if session_id not in self._prediction_queues or not self._prediction_queues[session_id]:
            return {"results": {}, "summary": {"total_queued": 0, "successful": 0, "failed": 0}}
        
        queued_records = self._prediction_queues[session_id]
        total_queued = len(queued_records)
        
        if show_progress:
            print(f"🚀 Processing {total_queued} queued predictions for session {session_id}...")
        
        # Extract records and metadata
        records_to_predict = []
        queue_metadata = {}
        
        for queued_item in queued_records:
            queue_id = queued_item['queue_id']
            record = queued_item['record']
            target_column = queued_item['target_column']
            
            records_to_predict.append(record)
            queue_metadata[len(records_to_predict) - 1] = {
                'queue_id': queue_id,
                'target_column': target_column
            }
        
        # Use existing batch prediction system
        try:
            # Get the target column for batch processing (use first record's target column)
            batch_target_column = None
            if queue_metadata:
                batch_target_column = list(queue_metadata.values())[0]['target_column']
            
            # Process using existing batch system
            batch_results = self.predict_records(
                session_id=session_id,
                records=records_to_predict,
                target_column=batch_target_column,
                show_progress_bar=show_progress
            )
            
            # Map batch results back to queue IDs
            results = {}
            successful = 0
            failed = 0
            
            predictions = batch_results.get('predictions', [])
            for prediction in predictions:
                row_index = prediction.get('row_index', 0)
                if row_index in queue_metadata:
                    queue_id = queue_metadata[row_index]['queue_id']
                    results[queue_id] = prediction
                    
                    if prediction.get('prediction') is not None:
                        successful += 1
                    else:
                        failed += 1
            
            # Clear the queue for this session
            self._prediction_queues[session_id] = []
            
            if show_progress:
                print(f"✅ Queue processing complete: {successful} successful, {failed} failed")
            
            return {
                "results": results,
                "summary": {
                    "total_queued": total_queued,
                    "successful": successful,
                    "failed": failed,
                    "batch_summary": batch_results.get('summary', {})
                }
            }
            
        except Exception as e:
            # Clear queue even on error to prevent stuck state
            self._prediction_queues[session_id] = []
            raise Exception(f"Error processing prediction queue: {str(e)}")
    
    def get_queue_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get status of prediction queue for a session.
        
        Args:
            session_id: Session ID to check
            
        Returns:
            Dictionary with queue status information
        """
        queue = self._prediction_queues.get(session_id, [])
        if not queue:
            return {"queued_count": 0, "queue_empty": True}
        
        # Calculate queue statistics
        oldest_timestamp = min(item['timestamp'] for item in queue)
        newest_timestamp = max(item['timestamp'] for item in queue)
        queue_age = time.time() - oldest_timestamp
        
        return {
            "queued_count": len(queue),
            "queue_empty": False,
            "oldest_queued_age_seconds": queue_age,
            "queue_time_span_seconds": newest_timestamp - oldest_timestamp,
            "queue_ids": [item['queue_id'] for item in queue[:10]]  # First 10 IDs
        }
    
    def clear_predict_queues(self, session_id: str = None) -> Dict[str, int]:
        """
        Clear prediction queues without processing them.
        
        Args:
            session_id: Specific session to clear, or None to clear all
            
        Returns:
            Dictionary with count of cleared items per session
        """
        cleared_counts = {}
        
        if session_id:
            # Clear specific session
            count = len(self._prediction_queues.get(session_id, []))
            self._prediction_queues[session_id] = []
            cleared_counts[session_id] = count
        else:
            # Clear all sessions
            for sid, queue in self._prediction_queues.items():
                cleared_counts[sid] = len(queue)
            self._prediction_queues.clear()
        
        return cleared_counts

    def predict_batch(self, session_id: str, records: List[Dict[str, Any]], 
                     target_column: str = None) -> PredictionBatch:
        """
        Create a prediction batch for instant cached lookups.
        
        Perfect for parameter sweeps, grid searches, and exploring prediction surfaces.
        Run your loops twice with identical code - first populates cache, second gets instant results.
        
        Args:
            session_id: ID of session with trained predictor
            records: List of all records you'll want to predict on
            target_column: Specific target column predictor to use
            
        Returns:
            PredictionBatch object with instant predict() method
            
        Example:
            # Generate all combinations you'll need
            records = []
            for i in range(10):
                for j in range(10):
                    records.append({"param1": i, "param2": j})
            
            # First run - populate cache with batch processing
            batch = client.predict_batch(session_id, records)
            
            # Second run - same loops but instant cache lookups
            results = []
            for i in range(10):
                for j in range(10):
                    record = {"param1": i, "param2": j}
                    result = batch.predict(record)  # Instant!
                    results.append(result)
        """
        # Create batch object
        batch = PredictionBatch(session_id, self, target_column)
        
        # Populate cache with batch predictions
        batch._populate_cache(records)
        
        return batch

    def predict_grid(self, session_id: str, degrees_of_freedom: int, 
                    grid_shape: tuple = None, target_column: str = None) -> 'PredictionGrid':
        """
        Create a prediction grid for exploring parameter surfaces with automatic visualization.
        
        Perfect for 1D curves, 2D heatmaps, and 3D surfaces with built-in plotting functions.
        
        Args:
            session_id: ID of session with trained predictor
            degrees_of_freedom: Number of dimensions (1, 2, or 3)
            grid_shape: Custom grid shape tuple (default: auto-sized)
            target_column: Specific target column predictor to use
            
        Returns:
            PredictionGrid object with predict() and plotting methods
            
        Example:
            # 2D parameter sweep with automatic plotting
            grid = client.predict_grid(session_id, degrees_of_freedom=2)
            grid.set_axis_labels(["Spend", "Campaign Type"])
            grid.set_axis_values(0, [100, 250, 500])
            grid.set_axis_values(1, ["search", "display", "social"])
            
            for i, spend in enumerate([100, 250, 500]):
                for j, campaign in enumerate(["search", "display", "social"]):
                    record = {"spend": spend, "campaign_type": campaign}
                    grid.predict(record, grid_position=(i, j))
            
            # Automatic visualization
            grid.plot_heatmap()  # 2D heatmap
            grid.plot_3d()       # 3D surface
            
            # Find optimal parameters
            optimal_pos = grid.get_optimal_position()
            print(f"Optimal parameters at grid position: {optimal_pos}")
        """
        return PredictionGrid(session_id, self, degrees_of_freedom, grid_shape, target_column)


class PredictionGrid:
    """
    Grid-based prediction batch with automatic matrix building and visualization.
    
    Perfect for exploring prediction surfaces across 1-3 dimensions with automatic plotting.
    Collects all predictions and batches them for efficiency.
    
    Usage:
        # 2D parameter sweep with automatic plotting
        grid = client.predict_grid(session_id, degrees_of_freedom=2)
        
        # Fill grid (records are collected, not predicted yet)
        for i, spend in enumerate([100, 250, 500]):
            for j, campaign in enumerate(["search", "display"]):
                record = {"spend": spend, "campaign_type": campaign}
                grid.predict(record, grid_position=(i, j))
        
        # Process all predictions in one batch
        grid.process_batch()
        
        # Now plot results
        grid.plot_heatmap()  # Automatic heatmap
        grid.plot_3d()       # 3D surface plot
    """
    
    def __init__(self, session_id: str, client: 'FeatrixSphereClient', degrees_of_freedom: int, 
                 grid_shape: tuple = None, target_column: str = None):
        self.session_id = session_id
        self.client = client
        self.degrees_of_freedom = degrees_of_freedom
        self.target_column = target_column
        
        # Initialize grid matrix based on degrees of freedom
        if grid_shape:
            self.grid_shape = grid_shape
        else:
            # Default grid sizes
            default_sizes = {1: (20,), 2: (10, 10), 3: (8, 8, 8)}
            self.grid_shape = default_sizes.get(degrees_of_freedom, (10,) * degrees_of_freedom)
        
        # Initialize matrices for different data types
        self._prediction_matrix = {}  # class_name -> matrix
        self._confidence_matrix = None
        self._filled_positions = set()
        
        # Batch collection system
        self._pending_records = {}  # grid_position -> record
        self._position_to_index = {}  # grid_position -> batch_index
        self._batch_processed = False
        
        # Metadata for plotting
        self._axis_labels = [f"Param {i+1}" for i in range(degrees_of_freedom)]
        self._axis_values = [[] for _ in range(degrees_of_freedom)]
        self._colormap = 'viridis'
        
        # Statistics
        self._stats = {'predictions': 0, 'batched': 0, 'errors': 0}
        
    def predict(self, record: Dict[str, Any], grid_position: tuple) -> Dict[str, str]:
        """
        Add record to grid for batch processing.
        
        Args:
            record: Record to predict
            grid_position: Tuple of grid coordinates (i,) for 1D, (i,j) for 2D, (i,j,k) for 3D
            
        Returns:
            Status message about queuing for batch processing
        """
        if len(grid_position) != self.degrees_of_freedom:
            raise ValueError(f"Grid position must have {self.degrees_of_freedom} dimensions, got {len(grid_position)}")
        
        # Check bounds
        for i, pos in enumerate(grid_position):
            if pos >= self.grid_shape[i]:
                raise ValueError(f"Grid position {pos} exceeds dimension {i} size {self.grid_shape[i]}")
        
        # Store record for batch processing
        self._pending_records[grid_position] = record
        
        return {
            "status": "queued_for_batch",
            "grid_position": grid_position,
            "total_queued": len(self._pending_records),
            "message": f"Record queued at position {grid_position}. Call process_batch() to run predictions."
        }
    
    def process_batch(self, show_progress: bool = True) -> Dict[str, Any]:
        """
        Process all queued records in a single batch prediction.
        
        Args:
            show_progress: Whether to show progress during batch processing
            
        Returns:
            Batch processing results
        """
        if not self._pending_records:
            return {"message": "No records to process", "processed": 0}
        
        if self._batch_processed:
            return {"message": "Batch already processed", "processed": len(self._filled_positions)}
        
        # Convert grid records to list for batch processing
        records_list = []
        position_mapping = {}
        
        for grid_pos, record in self._pending_records.items():
            batch_index = len(records_list)
            records_list.append(record)
            position_mapping[batch_index] = grid_pos
            self._position_to_index[grid_pos] = batch_index
        
        if show_progress:
            print(f"🚀 Processing {len(records_list)} grid positions in batch...")
        
        # Use existing batch prediction system
        try:
            batch_results = self.client.predict_records(
                session_id=self.session_id,
                records=records_list,
                target_column=self.target_column,
                show_progress_bar=show_progress
            )
            
            # Process results and populate matrices
            predictions = batch_results.get('predictions', [])
            successful = 0
            failed = 0
            
            for prediction in predictions:
                row_index = prediction.get('row_index', 0)
                if row_index in position_mapping:
                    grid_pos = position_mapping[row_index]
                    
                    if 'prediction' in prediction and prediction['prediction']:
                        prediction_probs = prediction['prediction']
                        
                        # Initialize matrices if first successful prediction
                        if not self._prediction_matrix:
                            self._initialize_matrices(prediction_probs.keys())
                        
                        # Store prediction results in matrices
                        for class_name, probability in prediction_probs.items():
                            self._prediction_matrix[class_name][grid_pos] = probability
                        
                        # Store confidence (highest probability)
                        max_class = max(prediction_probs, key=prediction_probs.get)
                        confidence = prediction_probs[max_class]
                        self._confidence_matrix[grid_pos] = confidence
                        
                        # Mark position as filled
                        self._filled_positions.add(grid_pos)
                        successful += 1
                    else:
                        failed += 1
                        self._stats['errors'] += 1
            
            self._stats['predictions'] = successful
            self._stats['batched'] = len(records_list)
            self._batch_processed = True
            
            # Clear pending records
            self._pending_records.clear()
            
            if show_progress:
                print(f"✅ Batch processing complete: {successful} successful, {failed} failed")
                print(f"📊 Grid filled: {len(self._filled_positions)} positions")
            
            return {
                "processed": len(records_list),
                "successful": successful,
                "failed": failed,
                "batch_results": batch_results
            }
            
        except Exception as e:
            self._stats['errors'] += len(records_list)
            raise Exception(f"Error processing grid batch: {str(e)}")
    
    def _initialize_matrices(self, class_names: list):
        """Initialize prediction matrices for each class."""
        import numpy as np
        
        for class_name in class_names:
            self._prediction_matrix[class_name] = np.full(self.grid_shape, np.nan)
        
        self._confidence_matrix = np.full(self.grid_shape, np.nan)
    
    def set_axis_labels(self, labels: list):
        """Set custom labels for axes."""
        if len(labels) != self.degrees_of_freedom:
            raise ValueError(f"Must provide {self.degrees_of_freedom} labels")
        self._axis_labels = labels
    
    def set_axis_values(self, axis_index: int, values: list):
        """Set actual values for an axis (for proper tick labels)."""
        if axis_index >= self.degrees_of_freedom:
            raise ValueError(f"Axis index {axis_index} exceeds degrees of freedom {self.degrees_of_freedom}")
        self._axis_values[axis_index] = values
    
    def plot_heatmap(self, class_name: str = None, figsize: tuple = (10, 8), title: str = None):
        """
        Plot 2D heatmap of prediction probabilities.
        
        Args:
            class_name: Specific class to plot (default: highest probability class)
            figsize: Figure size
            title: Custom title
        """
        if self.degrees_of_freedom != 2:
            raise ValueError("Heatmap plotting only supports 2D grids")
        
        if not self._batch_processed:
            raise ValueError("Must call process_batch() first")
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            raise ImportError("matplotlib required for plotting. Install with: pip install matplotlib")
        
        if not self._prediction_matrix:
            raise ValueError("No predictions processed yet. Call process_batch() first.")
        
        # Choose class to plot
        if class_name is None:
            # Use the class with highest average probability
            avg_probs = {}
            for cls, matrix in self._prediction_matrix.items():
                avg_probs[cls] = np.nanmean(matrix)
            class_name = max(avg_probs, key=avg_probs.get)
        
        matrix = self._prediction_matrix[class_name]
        
        # Create plot
        fig, ax = plt.subplots(figsize=figsize)
        
        # Transpose matrix for correct matplotlib display orientation
        # matplotlib imshow: first dimension = Y-axis (vertical), second = X-axis (horizontal)
        # So we need to transpose to get axis 0 on X-axis and axis 1 on Y-axis
        display_matrix = matrix.T
        
        # Plot heatmap with transposed matrix
        im = ax.imshow(display_matrix, cmap=self._colormap, aspect='auto', origin='lower')
        
        # Set labels (axis 0 = X-axis, axis 1 = Y-axis after transpose)
        ax.set_xlabel(self._axis_labels[0])
        ax.set_ylabel(self._axis_labels[1])
        
        # Set tick labels if axis values provided (adjusted for transpose)
        if self._axis_values[0]:
            ax.set_xticks(range(len(self._axis_values[0])))
            ax.set_xticklabels(self._axis_values[0])
        if self._axis_values[1]:
            ax.set_yticks(range(len(self._axis_values[1])))
            ax.set_yticklabels(self._axis_values[1])
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(f'Probability of {class_name}')
        
        # Set title
        if title is None:
            title = f'Prediction Heatmap: {class_name}'
        ax.set_title(title)
        
        plt.tight_layout()
        return fig, ax
    
    def plot_3d(self, class_name: str = None, figsize: tuple = (12, 9), title: str = None,
                 value_filter: tuple = None, opacity: float = 0.8, show_wireframe: bool = False):
        """
        Plot 3D surface of prediction probabilities with filtering and opacity controls.
        
        Args:
            class_name: Specific class to plot (default: highest probability class)
            figsize: Figure size
            title: Custom title
            value_filter: Tuple (min_value, max_value) to filter displayed predictions
            opacity: Surface opacity (0.0 = transparent, 1.0 = opaque)
            show_wireframe: Whether to show wireframe overlay for better shape visibility
        """
        if self.degrees_of_freedom != 2:
            raise ValueError("3D surface plotting only supports 2D grids")
        
        if not self._batch_processed:
            raise ValueError("Must call process_batch() first")
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            from mpl_toolkits.mplot3d import Axes3D
        except ImportError:
            raise ImportError("matplotlib required for plotting. Install with: pip install matplotlib")
        
        if not self._prediction_matrix:
            raise ValueError("No predictions processed yet. Call process_batch() first.")
        
        # Choose class to plot
        if class_name is None:
            avg_probs = {}
            for cls, matrix in self._prediction_matrix.items():
                avg_probs[cls] = np.nanmean(matrix)
            class_name = max(avg_probs, key=avg_probs.get)
        
        matrix = self._prediction_matrix[class_name].copy()
        
        # Apply value filter if specified
        if value_filter is not None:
            min_val, max_val = value_filter
            # Mask values outside the filter range
            mask = (matrix < min_val) | (matrix > max_val)
            matrix[mask] = np.nan
        
        # Create meshgrid with proper axis orientation
        x = np.arange(matrix.shape[0])  # axis 0
        y = np.arange(matrix.shape[1])  # axis 1
        X, Y = np.meshgrid(x, y, indexing='ij')
        
        # Create 3D plot
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot surface with specified opacity
        surf = ax.plot_surface(X, Y, matrix, cmap=self._colormap, alpha=opacity)
        
        # Add wireframe if requested (helps see shape)
        if show_wireframe:
            ax.plot_wireframe(X, Y, matrix, alpha=0.3, color='black', linewidth=0.5)
        
        # Set labels (axis 0 = X-axis, axis 1 = Y-axis)
        ax.set_xlabel(self._axis_labels[0])
        ax.set_ylabel(self._axis_labels[1])
        ax.set_zlabel(f'Probability of {class_name}')
        
        # Set tick labels if axis values provided
        if self._axis_values[0]:
            ax.set_xticks(range(len(self._axis_values[0])))
            ax.set_xticklabels(self._axis_values[0])
        if self._axis_values[1]:
            ax.set_yticks(range(len(self._axis_values[1])))
            ax.set_yticklabels(self._axis_values[1])
        
        # Add colorbar
        cbar = fig.colorbar(surf, ax=ax, shrink=0.5)
        cbar.set_label(f'Probability of {class_name}')
        
        # Set title with filter info
        if title is None:
            title = f'3D Prediction Surface: {class_name}'
            if value_filter:
                title += f' (filtered: {value_filter[0]:.3f}-{value_filter[1]:.3f})'
        ax.set_title(title)
        
        return fig, ax
    
    def plot_3d_interactive(self, class_name: str = None, figsize: tuple = (12, 9)):
        """
        Create interactive 3D plot with sliders for filtering and opacity control.
        
        Perfect for Jupyter notebooks - provides sliders to explore the prediction surface.
        
        Args:
            class_name: Specific class to plot (default: highest probability class)
            figsize: Figure size
            
        Returns:
            Interactive widget (in Jupyter) or regular plot (elsewhere)
        """
        if self.degrees_of_freedom != 2:
            raise ValueError("Interactive 3D plotting only supports 2D grids")
        
        if not self._batch_processed:
            raise ValueError("Must call process_batch() first")
        
        # Check if we're in a Jupyter environment
        try:
            from IPython.display import display
            from ipywidgets import interact, FloatSlider, FloatRangeSlider, Checkbox
            import numpy as np
            jupyter_available = True
        except ImportError:
            print("⚠️ Interactive widgets require Jupyter and ipywidgets")
            print("   Install with: pip install ipywidgets")
            print("   Falling back to static 3D plot...")
            return self.plot_3d(class_name=class_name, figsize=figsize)
        
        if not self._prediction_matrix:
            raise ValueError("No predictions processed yet. Call process_batch() first.")
        
        # Choose class to plot
        if class_name is None:
            avg_probs = {}
            for cls, matrix in self._prediction_matrix.items():
                avg_probs[cls] = np.nanmean(matrix)
            class_name = max(avg_probs, key=avg_probs.get)
        
        matrix = self._prediction_matrix[class_name]
        
        # Get value range for sliders
        min_val = float(np.nanmin(matrix))
        max_val = float(np.nanmax(matrix))
        value_range = max_val - min_val
        
        print(f"🎛️ Interactive 3D Surface Explorer: {class_name}")
        print(f"   Value range: {min_val:.4f} to {max_val:.4f}")
        print("   Use sliders below to filter and adjust opacity")
        
        # Create interactive plot function
        def update_plot(value_range=(min_val, max_val), opacity=0.8, wireframe=False):
            """Update the 3D plot based on slider values."""
            import matplotlib.pyplot as plt
            plt.close('all')  # Close previous plots
            
            fig, ax = self.plot_3d(
                class_name=class_name,
                figsize=figsize,
                value_filter=value_range,
                opacity=opacity,
                show_wireframe=wireframe
            )
            
            # Show current filter stats
            filtered_matrix = matrix.copy()
            mask = (filtered_matrix < value_range[0]) | (filtered_matrix > value_range[1])
            filtered_matrix[mask] = np.nan
            
            visible_count = np.sum(~np.isnan(filtered_matrix))
            total_count = np.sum(~np.isnan(matrix))
            visible_percent = (visible_count / total_count) * 100 if total_count > 0 else 0
            
            print(f"📊 Showing {visible_count}/{total_count} points ({visible_percent:.1f}%)")
            plt.show()
        
        # Create interactive widgets
        value_slider = FloatRangeSlider(
            value=(min_val, max_val),
            min=min_val,
            max=max_val,
            step=value_range / 100,
            description='Value Filter:',
            continuous_update=False,
            style={'description_width': 'initial'}
        )
        
        opacity_slider = FloatSlider(
            value=0.8,
            min=0.1,
            max=1.0,
            step=0.1,
            description='Opacity:',
            continuous_update=False,
            style={'description_width': 'initial'}
        )
        
        wireframe_checkbox = Checkbox(
            value=False,
            description='Show Wireframe',
            style={'description_width': 'initial'}
        )
        
        # Create interactive widget
        return interact(
            update_plot,
            value_range=value_slider,
            opacity=opacity_slider,
            wireframe=wireframe_checkbox
        )
    
    def plot_1d(self, class_name: str = None, figsize: tuple = (10, 6), title: str = None):
        """
        Plot 1D line plot of prediction probabilities.
        
        Args:
            class_name: Specific class to plot (default: highest probability class)
            figsize: Figure size
            title: Custom title
        """
        if self.degrees_of_freedom != 1:
            raise ValueError("1D plotting only supports 1D grids")
        
        if not self._batch_processed:
            raise ValueError("Must call process_batch() first")
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            raise ImportError("matplotlib required for plotting. Install with: pip install matplotlib")
        
        if not self._prediction_matrix:
            raise ValueError("No predictions processed yet. Call process_batch() first.")
        
        # Choose class to plot
        if class_name is None:
            avg_probs = {}
            for cls, matrix in self._prediction_matrix.items():
                avg_probs[cls] = np.nanmean(matrix)
            class_name = max(avg_probs, key=avg_probs.get)
        
        matrix = self._prediction_matrix[class_name]
        
        # Create plot
        fig, ax = plt.subplots(figsize=figsize)
        
        # X values
        x = self._axis_values[0] if self._axis_values[0] else range(len(matrix))
        
        # Plot line
        ax.plot(x, matrix, marker='o', linewidth=2, markersize=6)
        
        # Set labels
        ax.set_xlabel(self._axis_labels[0])
        ax.set_ylabel(f'Probability of {class_name}')
        
        # Set title
        if title is None:
            title = f'Prediction Curve: {class_name}'
        ax.set_title(title)
        
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        return fig, ax
    
    def get_optimal_position(self, class_name: str = None) -> tuple:
        """
        Find grid position with highest probability for a class.
        
        Args:
            class_name: Class to optimize for (default: highest average probability)
            
        Returns:
            Grid position tuple with highest probability
        """
        import numpy as np
        
        if not self._batch_processed:
            raise ValueError("Must call process_batch() first")
        
        if not self._prediction_matrix:
            raise ValueError("No predictions processed yet. Call process_batch() first.")
        
        if class_name is None:
            avg_probs = {}
            for cls, matrix in self._prediction_matrix.items():
                avg_probs[cls] = np.nanmean(matrix)
            class_name = max(avg_probs, key=avg_probs.get)
        
        matrix = self._prediction_matrix[class_name]
        optimal_idx = np.unravel_index(np.nanargmax(matrix), matrix.shape)
        
        return optimal_idx
    
    def get_stats(self) -> Dict[str, Any]:
        """Get grid statistics."""
        import numpy as np
        
        total_positions = int(np.prod(self.grid_shape))
        filled_ratio = len(self._filled_positions) / total_positions if total_positions > 0 else 0
        
        return {
            'grid_shape': self.grid_shape,
            'degrees_of_freedom': self.degrees_of_freedom,
            'total_positions': total_positions,
            'filled_positions': len(self._filled_positions),
            'fill_ratio': filled_ratio,
            'pending_records': len(self._pending_records),
            'batch_processed': self._batch_processed,
            'predictions_made': self._stats['predictions'],
            'errors': self._stats['errors'],
            'available_classes': list(self._prediction_matrix.keys()) if self._prediction_matrix else []
        }
    
    def export_data(self) -> Dict[str, Any]:
        """Export grid data for external analysis."""
        import numpy as np
        
        if not self._batch_processed:
            raise ValueError("Must call process_batch() first")
        
        return {
            'prediction_matrices': {cls: matrix.tolist() for cls, matrix in self._prediction_matrix.items()},
            'confidence_matrix': self._confidence_matrix.tolist() if self._confidence_matrix is not None else None,
            'grid_shape': self.grid_shape,
            'axis_labels': self._axis_labels,
            'axis_values': self._axis_values,
            'filled_positions': list(self._filled_positions),
            'stats': self.get_stats()
        }
    
    def plot_3d_plotly(self, class_name: str = None, title: str = None,
                       value_filter: tuple = None, opacity: float = 0.8, 
                       show_wireframe: bool = False, auto_display: bool = True):
        """
        Create interactive 3D surface plot using Plotly for full interactivity.
        
        Perfect for Jupyter notebooks - you can rotate, zoom, pan, and hover!
        
        Args:
            class_name: Specific class to plot (default: highest probability class)
            title: Custom title
            value_filter: Tuple (min_value, max_value) to filter displayed predictions
            opacity: Surface opacity (0.0 = transparent, 1.0 = opaque)
            show_wireframe: Whether to show wireframe overlay
            auto_display: Whether to automatically display the plot (Jupyter) or return figure
            
        Returns:
            Plotly figure object (can be displayed with fig.show() or saved)
        """
        if self.degrees_of_freedom != 2:
            raise ValueError("3D surface plotting only supports 2D grids")
        
        if not self._batch_processed:
            raise ValueError("Must call process_batch() first")
        
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            import numpy as np
        except ImportError:
            print("❌ Plotly not installed! Install with: pip install plotly")
            print("🔄 Falling back to matplotlib static plot...")
            return self.plot_3d(class_name=class_name, title=title, 
                               value_filter=value_filter, opacity=opacity,
                               show_wireframe=show_wireframe)
        
        if not self._prediction_matrix:
            raise ValueError("No predictions processed yet. Call process_batch() first.")
        
        # Choose class to plot
        if class_name is None:
            avg_probs = {}
            for cls, matrix in self._prediction_matrix.items():
                avg_probs[cls] = np.nanmean(matrix)
            class_name = max(avg_probs, key=avg_probs.get)
        
        matrix = self._prediction_matrix[class_name].copy()
        
        # Apply value filter if specified
        if value_filter is not None:
            min_val, max_val = value_filter
            matrix[matrix < min_val] = np.nan
            matrix[matrix > max_val] = np.nan
        
        # Create meshgrid with proper axis orientation
        x_vals = self._axis_values[0] if self._axis_values[0] else list(range(matrix.shape[0]))
        y_vals = self._axis_values[1] if self._axis_values[1] else list(range(matrix.shape[1]))
        
        # For Plotly, we need to create the surface plot
        fig = go.Figure()
        
        # Add main surface
        surface = go.Surface(
            x=x_vals,
            y=y_vals, 
            z=matrix,
            colorscale=self._colormap,
            opacity=opacity,
            name=f'{class_name} Surface',
            hovertemplate=(
                f"<b>{self._axis_labels[0]}</b>: %{{x}}<br>" +
                f"<b>{self._axis_labels[1]}</b>: %{{y}}<br>" +
                f"<b>{class_name}</b>: %{{z:.4f}}<br>" +
                "<extra></extra>"
            )
        )
        fig.add_trace(surface)
        
        # Add wireframe if requested
        if show_wireframe:
            # Create wireframe using scatter3d lines
            x_grid, y_grid = np.meshgrid(range(len(x_vals)), range(len(y_vals)), indexing='ij')
            
            # Flatten for scatter plot
            x_flat = x_grid.flatten()
            y_flat = y_grid.flatten()
            z_flat = matrix.flatten()
            
            # Remove NaN points
            valid_mask = ~np.isnan(z_flat)
            x_valid = [x_vals[i] for i in x_flat[valid_mask]]
            y_valid = [y_vals[i] for i in y_flat[valid_mask]]
            z_valid = z_flat[valid_mask]
            
            wireframe = go.Scatter3d(
                x=x_valid,
                y=y_valid,
                z=z_valid,
                mode='markers',
                marker=dict(size=2, color='black', opacity=0.4),
                name='Wireframe Points',
                hoverinfo='skip'
            )
            fig.add_trace(wireframe)
        
        # Update layout for better appearance
        if title is None:
            title = f'Interactive 3D Prediction Surface: {class_name}'
            if value_filter:
                title += f' (filtered: {value_filter[0]:.3f}-{value_filter[1]:.3f})'
        
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                font=dict(size=16)
            ),
            scene=dict(
                xaxis_title=self._axis_labels[0],
                yaxis_title=self._axis_labels[1],
                zaxis_title=f'Probability of {class_name}',
                bgcolor='rgb(240, 240, 240)',
                camera=dict(
                    eye=dict(x=1.2, y=1.2, z=1.2)  # Nice initial viewing angle
                )
            ),
            width=800,
            height=600,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        # Auto-display in Jupyter or return figure
        if auto_display:
            try:
                # Check if we're in Jupyter
                from IPython.display import display, HTML
                print(f"🎯 Interactive 3D Plot: {class_name}")
                print("   🖱️  Click and drag to rotate")
                print("   🔍 Scroll to zoom in/out") 
                print("   📍 Hover for exact values")
                print("   💾 Click camera icon to save image")
                fig.show()
                return fig
            except ImportError:
                # Not in Jupyter, just return the figure
                print(f"📊 Created interactive 3D plot for {class_name}")
                print("   💡 Use fig.show() to display or fig.write_html('plot.html') to save")
                return fig
        else:
            return fig


def main():
    """Example usage of the API client."""
    
    # Initialize client
    client = FeatrixSphereClient("https://sphere-api.featrix.com")
    
    print("=== Featrix Sphere API Client Test ===\n")
    
    try:
        # Example 1: Create a session and check status
        print("1. Creating a new session...")
        session_info = client.create_session("sphere")
        print(f"Session created: {session_info.session_id}\n")
        
        # Example 2: Check session status
        print("2. Checking session status...")
        current_status = client.get_session_status(session_info.session_id)
        print(f"Current status: {current_status.status}\n")
        
        # Example 3: Upload a file (if test data exists)
        test_file = Path("featrix_data/test.csv")
        if test_file.exists():
            print("3. Uploading test file...")
            upload_session = client.upload_file_and_create_session(test_file)
            print(f"Upload session: {upload_session.session_id}\n")
        else:
            print("3. Skipping file upload (test.csv not found)\n")
        
        print("API client test completed successfully!")
        
    except Exception as e:
        print(f"Error during API client test: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 