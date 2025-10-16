"""
TradeXil Python SDK
===================

Official Python library for accessing TradeXil Real-Time API.

Installation:
    pip install requests pandas pyarrow

Usage:
    from tradexil import TradeXilAPI
    
    # Initialize
    api = TradeXilAPI(api_key="your-key-here")
    
    # Get latest candle (JSON)
    candle = api.get_latest_candle("1h", format="json")
    print(f"Close: {candle['close']}, RSI: {candle['RSI_14']}")
    
    # Get latest candle (Parquet - faster)
    df = api.get_latest_candle("5m", format="parquet")
    print(df[['timestamp', 'close', 'volume', 'RSI_14']])
    
    # Get status
    status = api.get_status()
    print(f"Available: {status['available_timeframes']}")

Author: TradeXil
License: MIT
"""

import requests
import pandas as pd
import io
from typing import Union, Dict, List, Optional
import time
from datetime import datetime


class TradeXilAPIError(Exception):
    """Base exception for TradeXil API errors."""
    pass


class TradeXilAuthError(TradeXilAPIError):
    """Authentication/authorization error."""
    pass


class TradeXilDataError(TradeXilAPIError):
    """Data not available error."""
    pass


class TradeXilAPI:
    """
    Official Python client for TradeXil Real-Time API.
    
    Provides easy access to real-time BTCUSDT candle data with 197 calculated
    technical indicators across 6 timeframes.
    
    Args:
        api_key: Your TradeXil API key (20-character string)
        base_url: API base URL (default: https://tradexil.com)
        timeout: Request timeout in seconds (default: 10)
    
    Example:
        >>> api = TradeXilAPI(api_key="YOUR_KEY_HERE")
        >>> candle = api.get_latest_candle("1h")
        >>> print(f"Close: {candle['close']}")
    """
    
    VALID_TIMEFRAMES = ['5m', '15m', '30m', '1h', '4h', '1d']
    VALID_FORMATS = ['json', 'parquet']
    
    def __init__(self, 
                 api_key: str,
                 base_url: str = "https://tradexil.com",
                 timeout: int = 10):
        """
        Initialize TradeXil API client.
        
        Args:
            api_key: Your 20-character API key
            base_url: API endpoint URL
            timeout: Request timeout in seconds
        """
        if not api_key:
            raise TradeXilAuthError("API key is required")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Set up headers
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'TradeXil-Python-SDK/1.0'
        }
    
    def _make_request(self, endpoint: str, method: str = 'GET') -> requests.Response:
        """
        Make HTTP request to API.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            
        Returns:
            Response object
            
        Raises:
            TradeXilAuthError: If authentication fails
            TradeXilAPIError: For other API errors
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                timeout=self.timeout
            )
            
            # Handle authentication errors
            if response.status_code == 401:
                error_data = response.json()
                raise TradeXilAuthError(f"{error_data.get('error', 'Unauthorized')}: {error_data.get('message', 'Invalid or expired API key')}")
            
            # Handle data not available
            if response.status_code == 503:
                error_data = response.json()
                raise TradeXilDataError(error_data.get('message', 'Data not available yet'))
            
            # Handle other errors
            if not response.ok:
                try:
                    error_data = response.json()
                    raise TradeXilAPIError(f"{error_data.get('error', 'API Error')}: {error_data.get('message', 'Unknown error')}")
                except ValueError:
                    response.raise_for_status()
            
            return response
            
        except requests.exceptions.Timeout:
            raise TradeXilAPIError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise TradeXilAPIError(f"Failed to connect to {self.base_url}")
        except requests.exceptions.RequestException as e:
            raise TradeXilAPIError(f"Request failed: {str(e)}")
    
    def get_status(self) -> Dict:
        """
        Get API status and available timeframes.
        
        Returns:
            Dictionary with status information
            
        Example:
            >>> status = api.get_status()
            >>> print(status['available_timeframes'])
            ['5m', '15m', '30m', '1h', '4h', '1d']
        """
        response = self._make_request('/api/v1/status')
        return response.json()
    
    def get_latest_candle(self, 
                         timeframe: str,
                         format: str = 'json') -> Union[Dict, pd.DataFrame]:
        """
        Get the latest candle for a specific timeframe.
        
        Args:
            timeframe: One of: 5m, 15m, 30m, 1h, 4h, 1d
            format: 'json' or 'parquet' (default: json)
            
        Returns:
            Dictionary (if format='json') or DataFrame (if format='parquet')
            
        Raises:
            ValueError: If timeframe or format is invalid
            TradeXilAuthError: If API key is invalid
            TradeXilDataError: If data not available yet
            
        Example (JSON):
            >>> candle = api.get_latest_candle('1h', format='json')
            >>> print(f"Close: {candle['close']}, RSI: {candle['RSI_14']}")
            
        Example (Parquet):
            >>> df = api.get_latest_candle('5m', format='parquet')
            >>> print(df[['timestamp', 'close', 'RSI_14']])
        """
        # Validate timeframe
        if timeframe not in self.VALID_TIMEFRAMES:
            raise ValueError(f"Invalid timeframe '{timeframe}'. Must be one of: {', '.join(self.VALID_TIMEFRAMES)}")
        
        # Validate format
        format = format.lower()
        if format not in self.VALID_FORMATS:
            raise ValueError(f"Invalid format '{format}'. Must be one of: {', '.join(self.VALID_FORMATS)}")
        
        if format == 'json':
            # JSON format
            response = self._make_request(f'/api/v1/latest-candle/{timeframe}/json')
            data = response.json()
            return data['data']  # Return just the candle data
        
        else:
            # Parquet format
            response = self._make_request(f'/api/v1/latest-candle/{timeframe}')
            buffer = io.BytesIO(response.content)
            df = pd.read_parquet(buffer)
            return df
    
    def get_all_timeframes(self, format: str = 'json') -> Dict[str, Union[Dict, pd.DataFrame]]:
        """
        Get latest candles for all available timeframes.
        
        Args:
            format: 'json' or 'parquet' (default: json)
            
        Returns:
            Dictionary with timeframe as key and candle data as value
            
        Example:
            >>> candles = api.get_all_timeframes()
            >>> for tf, candle in candles.items():
            >>>     print(f"{tf}: Close = {candle['close']}")
        """
        status = self.get_status()
        available = status.get('available_timeframes', self.VALID_TIMEFRAMES)
        
        results = {}
        for timeframe in available:
            try:
                results[timeframe] = self.get_latest_candle(timeframe, format=format)
            except TradeXilDataError:
                # Skip timeframes where data isn't available yet
                continue
        
        return results
    
    def stream_candles(self, 
                      timeframe: str,
                      format: str = 'json',
                      interval: int = 60,
                      callback=None):
        """
        Stream candles by polling at regular intervals.
        
        Args:
            timeframe: Timeframe to monitor
            format: 'json' or 'parquet'
            interval: Polling interval in seconds (default: 60)
            callback: Optional callback function(candle_data)
            
        Yields:
            Candle data (dict or DataFrame)
            
        Example:
            >>> for candle in api.stream_candles('5m', interval=60):
            >>>     print(f"New candle: {candle['close']}")
            
        Example with callback:
            >>> def on_candle(candle):
            >>>     print(f"Close: {candle['close']}")
            >>> api.stream_candles('1h', callback=on_candle)
        """
        print(f"📡 Streaming {timeframe} candles (polling every {interval}s)...")
        print("Press Ctrl+C to stop\n")
        
        last_timestamp = None
        
        try:
            while True:
                try:
                    candle = self.get_latest_candle(timeframe, format=format)
                    
                    # Get timestamp (works for both dict and DataFrame)
                    if isinstance(candle, pd.DataFrame):
                        timestamp = candle['timestamp'].iloc[0]
                    else:
                        timestamp = candle['timestamp']
                    
                    # Only yield if it's a new candle
                    if timestamp != last_timestamp:
                        last_timestamp = timestamp
                        
                        if callback:
                            callback(candle)
                        else:
                            yield candle
                
                except TradeXilDataError:
                    print("⏳ Data not available yet, waiting...")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stream stopped by user")


# Convenience function for quick usage
def get_latest_candle(timeframe: str, 
                     api_key: str,
                     format: str = 'json',
                     base_url: str = "https://tradexil.com") -> Union[Dict, pd.DataFrame]:
    """
    Quick function to get latest candle without initializing client.
    
    Args:
        timeframe: One of: 5m, 15m, 30m, 1h, 4h, 1d
        api_key: Your TradeXil API key
        format: 'json' or 'parquet'
        base_url: API URL
        
    Returns:
        Candle data (dict or DataFrame)
        
    Example:
        >>> from tradexil import get_latest_candle
        >>> candle = get_latest_candle('1h', api_key='YOUR_KEY')
        >>> print(candle['close'])
    """
    client = TradeXilAPI(api_key=api_key, base_url=base_url)
    return client.get_latest_candle(timeframe, format=format)


# Example usage
if __name__ == "__main__":
    import sys
    
    # Example usage
    print("TradeXil Python SDK - Example Usage\n")
    
    # Get API key from command line or use default
    api_key = sys.argv[1] if len(sys.argv) > 1 else "devkey123"
    
    try:
        # Initialize client
        print("1. Initializing client...")
        api = TradeXilAPI(api_key=api_key)
        
        # Get status
        print("\n2. Getting API status...")
        status = api.get_status()
        print(f"   Status: {status['status']}")
        print(f"   Available timeframes: {', '.join(status['available_timeframes'])}")
        print(f"   Total columns: {status['total_columns']}")
        
        # Get latest candle (JSON)
        print("\n3. Getting latest 1h candle (JSON)...")
        candle = api.get_latest_candle('1h', format='json')
        print(f"   Timestamp: {candle['timestamp']}")
        print(f"   Close: {candle['close']}")
        print(f"   RSI(14): {candle['RSI_14']}")
        print(f"   MACD: {candle['MACD_12_26_9_line']}")
        
        # Get latest candle (Parquet)
        print("\n4. Getting latest 5m candle (Parquet)...")
        df = api.get_latest_candle('5m', format='parquet')
        print(f"   Shape: {df.shape}")
        print(f"   Columns: {len(df.columns)}")
        print("\n   OHLCV + Indicators:")
        print(df[['timestamp', 'close', 'volume', 'RSI_14', 'MACD_12_26_9_line']].to_string())
        
        print("\n✅ All tests passed!")
        
    except TradeXilAuthError as e:
        print(f"\n❌ Authentication Error: {e}")
        print("   Please check your API key")
    except TradeXilDataError as e:
        print(f"\n⏳ Data Not Available: {e}")
        print("   Wait a few seconds and try again")
    except TradeXilAPIError as e:
        print(f"\n❌ API Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
