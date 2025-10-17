from pathlib import Path
import json
from pathlib import Path
from typing import Dict, Any, List
import requests
from ..base.loader import BaseLoader
import polars as pl


class FacebookLoader(BaseLoader):
    BASE_URL = "https://graph.facebook.com/v22.0"
    DEFAULT_METRICS = [
        "page_views_total",
        "page_daily_follows",
        "page_follows",
        "page_post_engagements",
        "page_impressions_unique",
    ]

    def __init__(self, duckdb_path: Path, page_id: str, access_token: str):
        super().__init__(duckdb_path)
        self.page_id = page_id
        self.access_token = access_token

    def extract_page_insights(
        self,
        date_preset: str = "maximum",
        period: str = "day",
        metrics: List[str] = DEFAULT_METRICS,
        # timestamp_window: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Fetch page insights data from Facebook Graph API.

        Args:
            metrics: List of metrics to fetch. Defaults to DEFAULT_METRICS.
            date_preset: Date preset for the data range (e.g., 'maximum', 'last_30d')
            period: Time period for aggregation ('day', 'week', 'days_28')

        Returns:
            Dict containing the API response with insights data

        Raises:
            requests.HTTPError: If the API request fails
        """

        # Build the fields parameter
        metrics_str = ",".join(metrics)
        fields = f"insights.date_preset({date_preset}).period({period}).metric({metrics_str})"

        # Build the request URL
        url = f"{self.BASE_URL}/{self.page_id}"
        params = {"fields": fields, "access_token": self.access_token}

        # Make the API request
        response = requests.get(url, params=params)
        response_json = response.json()
        result_dict = {}
        for item in response_json["insights"]["data"]:
            table = item["name"]
            df = pl.DataFrame(item["values"])
            df.write_csv(f"{table}.csv")
            result_dict[table] = df
        return result_dict

    def load_page_insights(self, schema: str):
        result_dict = self.extract_page_insights()
        for table, df in result_dict.items():
            self.load_dataframe(df, schema, table)
