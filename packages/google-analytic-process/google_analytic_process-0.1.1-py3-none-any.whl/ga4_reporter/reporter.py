"""
Google Analytics 4 Reporter Module

This module provides functionality to run Google Analytics 4 reports
and return the results as pandas DataFrames.
"""

from datetime import datetime, date
from typing import List, Union, Optional
import pandas as pd
import warnings

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)

warnings.filterwarnings("ignore")


class GA4Reporter:
    """
    A class to handle Google Analytics 4 report generation.

    Attributes:
        property_id (str): The GA4 property ID
        credentials_path (str): Path to the service account JSON file
        client (BetaAnalyticsDataClient): The GA4 client instance
    """

    def __init__(self, property_id: str, credentials_path: str):
        """
        Initialize the GA4Reporter.

        Args:
            property_id (str): The GA4 property ID (e.g., "276493948")
            credentials_path (str): Path to the service account credentials JSON file
        """
        self.property_id = property_id
        self.credentials_path = credentials_path
        self.client = BetaAnalyticsDataClient.from_service_account_json(credentials_path)

    def run_report(
        self,
        dimensions: List[str],
        metrics: List[str],
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        limit: int = 1000000,
        offset: int = 0
    ) -> pd.DataFrame:
        """
        Run a Google Analytics 4 report with specified dimensions and metrics.

        Args:
            dimensions (List[str]): List of dimension names (e.g., ["date", "sessionDefaultChannelGroup"])
            metrics (List[str]): List of metric names (e.g., ["sessions", "totalRevenue"])
            start_date: Start date for the report (str in 'YYYY-MM-DD' format, date, or datetime)
            end_date: End date for the report (str in 'YYYY-MM-DD' format, date, or datetime)
            limit (int, optional): Maximum number of rows to return. Defaults to 1000000.
            offset (int, optional): Number of rows to skip. Defaults to 0.

        Returns:
            pd.DataFrame: DataFrame containing the report data with dimensions and metrics as columns

        Example:
            >>> reporter = GA4Reporter("276493948", "/path/to/credentials.json")
            >>> dimensions = ["date", "sessionDefaultChannelGroup"]
            >>> metrics = ["sessions", "totalRevenue"]
            >>> df = reporter.run_report(dimensions, metrics, "2024-01-01", "2024-01-31")
        """
        # Convert dates to string format
        if isinstance(start_date, (date, datetime)):
            start_date_str = start_date.strftime('%Y-%m-%d')
        else:
            start_date_str = start_date

        if isinstance(end_date, (date, datetime)):
            end_date_str = end_date.strftime('%Y-%m-%d')
        else:
            end_date_str = end_date

        # Create dimension and metric objects
        dimension_objects = [Dimension(name=dim) for dim in dimensions]
        metric_objects = [Metric(name=metric) for metric in metrics]

        # Create the request
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            dimensions=dimension_objects,
            metrics=metric_objects,
            date_ranges=[DateRange(start_date=start_date_str, end_date=end_date_str)],
            limit=limit,
            offset=offset
        )

        # Execute the request
        response = self.client.run_report(request)

        # Parse the response into a list of rows
        data = []
        for row in response.rows:
            dimension_values = [dim.value for dim in row.dimension_values]
            metric_values = [float(metric.value) for metric in row.metric_values]
            data.append(dimension_values + metric_values)

        # Create DataFrame with appropriate column names
        columns = dimensions + metrics
        df = pd.DataFrame(data, columns=columns)

        return df


def run_report(
    dimensions: List[str],
    metrics: List[str],
    start_date: Union[str, date, datetime],
    end_date: Union[str, date, datetime],
    credentials_path: str,
    property_id: str = "276493948",
    limit: int = 1000000,
    offset: int = 0
) -> pd.DataFrame:
    """
    Convenience function to run a GA4 report without instantiating the class.

    Args:
        dimensions (List[str]): List of dimension names (e.g., ["date", "sessionDefaultChannelGroup"])
        metrics (List[str]): List of metric names (e.g., ["sessions", "totalRevenue"])
        start_date: Start date for the report (str in 'YYYY-MM-DD' format, date, or datetime)
        end_date: End date for the report (str in 'YYYY-MM-DD' format, date, or datetime)
        credentials_path (str): Path to the service account credentials JSON file
        property_id (str, optional): The GA4 property ID. Defaults to "276493948".
        limit (int, optional): Maximum number of rows to return. Defaults to 1000000.
        offset (int, optional): Number of rows to skip. Defaults to 0.

    Returns:
        pd.DataFrame: DataFrame containing the report data with dimensions and metrics as columns

    Example:
        >>> from ga4_reporter import run_report
        >>> from datetime import datetime, timedelta
        >>>
        >>> end_date = datetime.now().date()
        >>> start_date = end_date - timedelta(days=7)
        >>>
        >>> dimensions = ["date", "sessionDefaultChannelGroup", "sessionCampaignName"]
        >>> metrics = ["sessions", "transactions", "totalRevenue"]
        >>>
        >>> df = run_report(
        ...     dimensions=dimensions,
        ...     metrics=metrics,
        ...     start_date=start_date,
        ...     end_date=end_date,
        ...     credentials_path="/path/to/credentials.json",
        ...     property_id="276493948"
        ... )
    """
    reporter = GA4Reporter(property_id, credentials_path)
    return reporter.run_report(dimensions, metrics, start_date, end_date, limit, offset)
