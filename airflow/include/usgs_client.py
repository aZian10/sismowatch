"""
USGS Earthquake Catalog API Client.
Provides resilient methods to query the real-time GeoJSON feed and historical query API.
"""
import logging
import time
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from include.config import (
        USGS_REALTIME_URL,
        USGS_QUERY_URL,
        REQUEST_TIMEOUT_SECONDS,
        MAX_RETRIES,
    )
except ImportError:
    from airflow.include.config import (
        USGS_REALTIME_URL,
        USGS_QUERY_URL,
        REQUEST_TIMEOUT_SECONDS,
        MAX_RETRIES,
    )

logger = logging.getLogger("sismowatch.usgs_client")

class USGSClient:
    """Robust client for fetching USGS earthquake GeoJSON feeds."""

    def __init__(self, timeout: int = REQUEST_TIMEOUT_SECONDS, max_retries: int = MAX_RETRIES):
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configure automatic retries for transient HTTP errors (500, 502, 503, 504)
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update({
            "User-Agent": "SismoWatch-DataPlatform/1.0 (Airflow Data Pipeline)",
            "Accept": "application/json"
        })

    def fetch_realtime_hour_feed(self) -> Dict[str, Any]:
        """
        Fetches the last hour earthquake GeoJSON feed.
        Endpoint: https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson
        """
        logger.info(f"Requesting USGS real-time feed from: {USGS_REALTIME_URL}")
        try:
            response = self.session.get(USGS_REALTIME_URL, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched USGS feed: {len(data.get('features', []))} features found.")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch USGS real-time feed: {e}")
            raise

    def fetch_historical_events(
        self,
        starttime: str,
        endtime: str,
        minmagnitude: float = 2.5,
        limit: int = 20000
    ) -> Dict[str, Any]:
        """
        Queries the USGS event catalog for a historical time range.
        Format: YYYY-MM-DD
        """
        params = {
            "format": "geojson",
            "starttime": starttime,
            "endtime": endtime,
            "minmagnitude": minmagnitude,
            "limit": limit
        }
        logger.info(f"Querying USGS historical API: {USGS_QUERY_URL} with params: {params}")
        try:
            response = self.session.get(USGS_QUERY_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Historical query succeeded: {len(data.get('features', []))} events retrieved.")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"USGS historical query failed: {e}")
            raise
