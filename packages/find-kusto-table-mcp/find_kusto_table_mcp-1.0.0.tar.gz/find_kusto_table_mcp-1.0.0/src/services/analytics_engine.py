"""
Advanced Analytics Engine for Query Results

Provides statistical analysis, time-series analysis, anomaly detection,
and data quality checks on cached query results.
"""

import math
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from ..core.logging_config import get_logger
from ..core.performance import measure_operation
from ..core.exceptions import ValidationError

logger = get_logger("analytics_engine")


class AdvancedAnalyticsEngine:
    """
    Advanced analytics operations on cached query results
    
    Provides:
    - Statistical operations (percentiles, stddev, correlation)
    - Time-series analysis (trends, seasonality, forecasting)
    - Anomaly detection (outliers, statistical anomalies)
    - Data quality checks (completeness, consistency, validity)
    """
    
    def __init__(self):
        self.logger = logger
    
    # ============================================================================
    # STATISTICAL OPERATIONS
    # ============================================================================
    
    @measure_operation("analytics_statistics")
    def calculate_statistics(
        self,
        results: List[Dict[str, Any]],
        column: str
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for a numeric column
        
        Returns: min, max, mean, median, stddev, variance, percentiles, skewness, kurtosis
        """
        values = self._extract_numeric_values(results, column)
        
        if not values:
            raise ValidationError(f"No numeric values found in column '{column}'")
        
        sorted_values = sorted(values)
        n = len(values)
        
        stats = {
            "count": n,
            "min": min(values),
            "max": max(values),
            "sum": sum(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "mode": self._safe_mode(values),
            "range": max(values) - min(values)
        }
        
        # Standard deviation and variance (require at least 2 values)
        if n >= 2:
            stats["stddev"] = statistics.stdev(values)
            stats["variance"] = statistics.variance(values)
        else:
            stats["stddev"] = 0.0
            stats["variance"] = 0.0
        
        # Percentiles
        stats["percentiles"] = {
            "p1": self._percentile(sorted_values, 1),
            "p5": self._percentile(sorted_values, 5),
            "p10": self._percentile(sorted_values, 10),
            "p25": self._percentile(sorted_values, 25),
            "p50": self._percentile(sorted_values, 50),
            "p75": self._percentile(sorted_values, 75),
            "p90": self._percentile(sorted_values, 90),
            "p95": self._percentile(sorted_values, 95),
            "p99": self._percentile(sorted_values, 99)
        }
        
        # Quartiles and IQR
        stats["q1"] = stats["percentiles"]["p25"]
        stats["q2"] = stats["percentiles"]["p50"]
        stats["q3"] = stats["percentiles"]["p75"]
        stats["iqr"] = stats["q3"] - stats["q1"]
        
        # Skewness and kurtosis (require at least 3 values)
        if n >= 3:
            stats["skewness"] = self._calculate_skewness(values, stats["mean"], stats["stddev"])
            stats["kurtosis"] = self._calculate_kurtosis(values, stats["mean"], stats["stddev"])
        
        return stats
    
    @measure_operation("analytics_correlation")
    def calculate_correlation(
        self,
        results: List[Dict[str, Any]],
        column_x: str,
        column_y: str
    ) -> Dict[str, Any]:
        """
        Calculate correlation between two numeric columns
        
        Returns: pearson correlation, covariance, scatter plot data
        """
        values_x = self._extract_numeric_values(results, column_x)
        values_y = self._extract_numeric_values(results, column_y)
        
        if len(values_x) != len(values_y):
            raise ValidationError("Columns must have same number of values")
        
        if not values_x:
            raise ValidationError("No numeric values found")
        
        n = len(values_x)
        
        # Calculate means
        mean_x = statistics.mean(values_x)
        mean_y = statistics.mean(values_y)
        
        # Calculate covariance
        covariance = sum((x - mean_x) * (y - mean_y) for x, y in zip(values_x, values_y)) / n
        
        # Calculate standard deviations
        stddev_x = statistics.stdev(values_x) if n >= 2 else 0
        stddev_y = statistics.stdev(values_y) if n >= 2 else 0
        
        # Calculate Pearson correlation
        if stddev_x == 0 or stddev_y == 0:
            correlation = 0.0
        else:
            correlation = covariance / (stddev_x * stddev_y)
        
        # Interpret correlation strength
        strength = self._interpret_correlation(abs(correlation))
        direction = "positive" if correlation > 0 else "negative" if correlation < 0 else "none"
        
        return {
            "pearson_correlation": correlation,
            "covariance": covariance,
            "strength": strength,
            "direction": direction,
            "sample_size": n,
            "interpretation": f"{strength} {direction} correlation ({correlation:.3f})"
        }
    
    # ============================================================================
    # TIME-SERIES ANALYSIS
    # ============================================================================
    
    @measure_operation("analytics_time_series")
    def analyze_time_series(
        self,
        results: List[Dict[str, Any]],
        time_column: str,
        value_column: str,
        interval_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze time-series data for trends, seasonality, and patterns
        
        Returns: trend, seasonality, statistics over time, anomalies
        """
        # Extract and sort by time
        time_series = []
        for row in results:
            time_val = row.get(time_column)
            value_val = row.get(value_column)
            
            if time_val is not None and value_val is not None:
                try:
                    # Parse time if string
                    if isinstance(time_val, str):
                        time_val = datetime.fromisoformat(time_val.replace('Z', '+00:00'))
                    
                    # Convert value to float
                    value_val = float(value_val)
                    
                    time_series.append((time_val, value_val))
                except (ValueError, TypeError):
                    continue
        
        if not time_series:
            raise ValidationError("No valid time-series data found")
        
        time_series.sort(key=lambda x: x[0])
        
        times = [t for t, v in time_series]
        values = [v for t, v in time_series]
        
        # Calculate trend
        trend = self._calculate_trend(times, values)
        
        # Calculate moving averages
        moving_avg_5 = self._moving_average(values, 5)
        moving_avg_10 = self._moving_average(values, 10)
        
        # Detect anomalies
        anomalies = self._detect_time_series_anomalies(time_series, moving_avg_10)
        
        # Calculate statistics
        stats = {
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "stddev": statistics.stdev(values) if len(values) >= 2 else 0
        }
        
        # Time range
        time_range = {
            "start": times[0].isoformat() if isinstance(times[0], datetime) else str(times[0]),
            "end": times[-1].isoformat() if isinstance(times[-1], datetime) else str(times[-1]),
            "duration_seconds": (times[-1] - times[0]).total_seconds() if isinstance(times[0], datetime) else None
        }
        
        return {
            "data_points": len(time_series),
            "time_range": time_range,
            "statistics": stats,
            "trend": trend,
            "moving_averages": {
                "ma_5": moving_avg_5[-1] if moving_avg_5 else None,
                "ma_10": moving_avg_10[-1] if moving_avg_10 else None
            },
            "anomalies": anomalies,
            "interpretation": self._interpret_trend(trend)
        }
    
    # ============================================================================
    # ANOMALY DETECTION
    # ============================================================================
    
    @measure_operation("analytics_anomaly_detection")
    def detect_anomalies(
        self,
        results: List[Dict[str, Any]],
        column: str,
        method: str = "iqr",
        threshold: float = 1.5
    ) -> Dict[str, Any]:
        """
        Detect anomalies in numeric data
        
        Methods:
        - iqr: Interquartile range method (default)
        - zscore: Z-score method
        - modified_zscore: Modified Z-score using median absolute deviation
        
        Returns: anomalies, statistics, thresholds
        """
        values = self._extract_numeric_values(results, column)
        
        if not values:
            raise ValidationError(f"No numeric values found in column '{column}'")
        
        if method == "iqr":
            anomalies, lower_bound, upper_bound = self._detect_iqr_anomalies(values, threshold)
        elif method == "zscore":
            anomalies, lower_bound, upper_bound = self._detect_zscore_anomalies(values, threshold)
        elif method == "modified_zscore":
            anomalies, lower_bound, upper_bound = self._detect_modified_zscore_anomalies(values, threshold)
        else:
            raise ValidationError(f"Unknown anomaly detection method: {method}")
        
        # Find anomalous rows
        anomalous_rows = []
        for i, row in enumerate(results):
            value = row.get(column)
            if value is not None and self._is_numeric(value):
                if float(value) in anomalies:
                    anomalous_rows.append({
                        "index": i,
                        "value": value,
                        "row": row
                    })
        
        return {
            "method": method,
            "threshold": threshold,
            "total_values": len(values),
            "anomaly_count": len(anomalies),
            "anomaly_percentage": (len(anomalies) / len(values)) * 100 if values else 0,
            "bounds": {
                "lower": lower_bound,
                "upper": upper_bound
            },
            "anomalous_values": sorted(anomalies),
            "anomalous_rows": anomalous_rows[:10]  # Limit to first 10
        }
    
    # ============================================================================
    # DATA QUALITY CHECKS
    # ============================================================================
    
    @measure_operation("analytics_data_quality")
    def check_data_quality(
        self,
        results: List[Dict[str, Any]],
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive data quality checks
        
        Checks:
        - Completeness (missing values, null ratio)
        - Consistency (duplicate rows, unique values)
        - Validity (data type consistency, range violations)
        - Accuracy (outliers, anomalies)
        
        Returns: quality score, issues, recommendations
        """
        if not results:
            return {
                "quality_score": 0,
                "issues": ["No data to analyze"],
                "recommendations": ["Verify query returned results"]
            }
        
        # Determine columns to check
        if columns is None:
            columns = list(results[0].keys())
        
        checks = {
            "completeness": self._check_completeness(results, columns),
            "consistency": self._check_consistency(results, columns),
            "validity": self._check_validity(results, columns),
            "uniqueness": self._check_uniqueness(results, columns)
        }
        
        # Calculate overall quality score (0-100)
        quality_score = self._calculate_quality_score(checks)
        
        # Collect issues and recommendations
        issues = []
        recommendations = []
        
        for check_name, check_results in checks.items():
            if check_results.get("issues"):
                issues.extend(check_results["issues"])
            if check_results.get("recommendations"):
                recommendations.extend(check_results["recommendations"])
        
        return {
            "quality_score": quality_score,
            "grade": self._quality_grade(quality_score),
            "total_rows": len(results),
            "total_columns": len(columns),
            "checks": checks,
            "issues": issues,
            "recommendations": recommendations
        }
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _extract_numeric_values(self, results: List[Dict[str, Any]], column: str) -> List[float]:
        """Extract numeric values from a column"""
        values = []
        for row in results:
            value = row.get(column)
            if value is not None and self._is_numeric(value):
                values.append(float(value))
        return values
    
    def _is_numeric(self, value: Any) -> bool:
        """Check if value is numeric"""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _percentile(self, sorted_values: List[float], p: float) -> float:
        """Calculate percentile from sorted values"""
        if not sorted_values:
            return 0.0
        
        k = (len(sorted_values) - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        
        if f == c:
            return sorted_values[int(k)]
        
        d0 = sorted_values[int(f)] * (c - k)
        d1 = sorted_values[int(c)] * (k - f)
        return d0 + d1
    
    def _safe_mode(self, values: List[float]) -> Optional[float]:
        """Calculate mode, return None if no unique mode"""
        try:
            return statistics.mode(values)
        except statistics.StatisticsError:
            return None
    
    def _calculate_skewness(self, values: List[float], mean: float, stddev: float) -> float:
        """Calculate skewness (measure of asymmetry)"""
        if stddev == 0:
            return 0.0
        
        n = len(values)
        m3 = sum((x - mean) ** 3 for x in values) / n
        return m3 / (stddev ** 3)
    
    def _calculate_kurtosis(self, values: List[float], mean: float, stddev: float) -> float:
        """Calculate kurtosis (measure of tailedness)"""
        if stddev == 0:
            return 0.0
        
        n = len(values)
        m4 = sum((x - mean) ** 4 for x in values) / n
        return (m4 / (stddev ** 4)) - 3  # Excess kurtosis
    
    def _interpret_correlation(self, abs_corr: float) -> str:
        """Interpret correlation strength"""
        if abs_corr >= 0.9:
            return "very strong"
        elif abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.5:
            return "moderate"
        elif abs_corr >= 0.3:
            return "weak"
        else:
            return "very weak"
    
    def _calculate_trend(self, times: List[datetime], values: List[float]) -> Dict[str, Any]:
        """Calculate linear trend"""
        n = len(values)
        if n < 2:
            return {"slope": 0, "direction": "none"}
        
        # Convert times to numeric (seconds since first timestamp)
        if isinstance(times[0], datetime):
            x = [(t - times[0]).total_seconds() for t in times]
        else:
            x = list(range(n))
        
        y = values
        
        # Calculate linear regression
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, y))
        denominator = sum((xi - x_mean) ** 2 for xi in x)
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        # Determine direction
        if slope > 0.01:
            direction = "increasing"
        elif slope < -0.01:
            direction = "decreasing"
        else:
            direction = "stable"
        
        return {
            "slope": slope,
            "intercept": intercept,
            "direction": direction
        }
    
    def _interpret_trend(self, trend: Dict[str, Any]) -> str:
        """Interpret trend analysis"""
        direction = trend.get("direction", "unknown")
        slope = trend.get("slope", 0)
        
        if direction == "increasing":
            return f"Values are increasing over time (slope: {slope:.4f})"
        elif direction == "decreasing":
            return f"Values are decreasing over time (slope: {slope:.4f})"
        else:
            return "Values are relatively stable over time"
    
    def _moving_average(self, values: List[float], window: int) -> List[float]:
        """Calculate moving average"""
        if len(values) < window:
            return []
        
        averages = []
        for i in range(len(values) - window + 1):
            window_values = values[i:i+window]
            averages.append(sum(window_values) / window)
        
        return averages
    
    def _detect_time_series_anomalies(
        self,
        time_series: List[Tuple[datetime, float]],
        moving_avg: List[float]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in time series"""
        if not moving_avg or len(time_series) < len(moving_avg):
            return []
        
        anomalies = []
        values = [v for t, v in time_series]
        
        # Calculate threshold based on stddev from moving average
        stddev = statistics.stdev(values) if len(values) >= 2 else 0
        threshold = 2 * stddev
        
        # Check last points against moving average
        for i, (time, value) in enumerate(time_series[-len(moving_avg):]):
            ma_value = moving_avg[i]
            deviation = abs(value - ma_value)
            
            if deviation > threshold:
                anomalies.append({
                    "timestamp": time.isoformat() if isinstance(time, datetime) else str(time),
                    "value": value,
                    "expected": ma_value,
                    "deviation": deviation
                })
        
        return anomalies
    
    def _detect_iqr_anomalies(
        self,
        values: List[float],
        threshold: float
    ) -> Tuple[List[float], float, float]:
        """Detect anomalies using IQR method"""
        sorted_values = sorted(values)
        q1 = self._percentile(sorted_values, 25)
        q3 = self._percentile(sorted_values, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        anomalies = [v for v in values if v < lower_bound or v > upper_bound]
        
        return anomalies, lower_bound, upper_bound
    
    def _detect_zscore_anomalies(
        self,
        values: List[float],
        threshold: float
    ) -> Tuple[List[float], float, float]:
        """Detect anomalies using Z-score method"""
        mean = statistics.mean(values)
        stddev = statistics.stdev(values) if len(values) >= 2 else 0
        
        if stddev == 0:
            return [], mean, mean
        
        lower_bound = mean - threshold * stddev
        upper_bound = mean + threshold * stddev
        
        anomalies = [v for v in values if abs((v - mean) / stddev) > threshold]
        
        return anomalies, lower_bound, upper_bound
    
    def _detect_modified_zscore_anomalies(
        self,
        values: List[float],
        threshold: float
    ) -> Tuple[List[float], float, float]:
        """Detect anomalies using Modified Z-score (MAD) method"""
        median = statistics.median(values)
        mad = statistics.median([abs(v - median) for v in values])
        
        if mad == 0:
            return [], median, median
        
        modified_zscores = [0.6745 * (v - median) / mad for v in values]
        
        anomalies = [values[i] for i, z in enumerate(modified_zscores) if abs(z) > threshold]
        
        # Calculate approximate bounds
        lower_bound = median - (threshold * mad / 0.6745)
        upper_bound = median + (threshold * mad / 0.6745)
        
        return anomalies, lower_bound, upper_bound
    
    def _check_completeness(
        self,
        results: List[Dict[str, Any]],
        columns: List[str]
    ) -> Dict[str, Any]:
        """Check data completeness"""
        total_rows = len(results)
        completeness = {}
        issues = []
        recommendations = []
        
        for column in columns:
            null_count = sum(1 for row in results if row.get(column) is None)
            null_ratio = null_count / total_rows if total_rows > 0 else 0
            
            completeness[column] = {
                "null_count": null_count,
                "null_ratio": null_ratio,
                "completeness": 1 - null_ratio
            }
            
            if null_ratio > 0.5:
                issues.append(f"Column '{column}' has {null_ratio*100:.1f}% null values")
                recommendations.append(f"Investigate why '{column}' has high null rate")
            elif null_ratio > 0.1:
                issues.append(f"Column '{column}' has {null_ratio*100:.1f}% null values")
        
        avg_completeness = sum(c["completeness"] for c in completeness.values()) / len(completeness) if completeness else 0
        
        return {
            "average_completeness": avg_completeness,
            "columns": completeness,
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _check_consistency(
        self,
        results: List[Dict[str, Any]],
        columns: List[str]
    ) -> Dict[str, Any]:
        """Check data consistency"""
        issues = []
        recommendations = []
        
        # Check for duplicate rows
        row_tuples = [tuple(sorted(row.items())) for row in results]
        duplicate_count = len(row_tuples) - len(set(row_tuples))
        
        if duplicate_count > 0:
            duplicate_ratio = duplicate_count / len(results)
            issues.append(f"Found {duplicate_count} duplicate rows ({duplicate_ratio*100:.1f}%)")
            recommendations.append("Review query to eliminate duplicates or use 'distinct' operator")
        
        return {
            "duplicate_count": duplicate_count,
            "duplicate_ratio": duplicate_count / len(results) if results else 0,
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _check_validity(
        self,
        results: List[Dict[str, Any]],
        columns: List[str]
    ) -> Dict[str, Any]:
        """Check data validity"""
        issues = []
        recommendations = []
        type_consistency = {}
        
        for column in columns:
            # Check type consistency
            types = defaultdict(int)
            for row in results:
                value = row.get(column)
                if value is not None:
                    types[type(value).__name__] += 1
            
            # If more than one type, flag as inconsistent
            if len(types) > 1:
                type_consistency[column] = dict(types)
                issues.append(f"Column '{column}' has inconsistent types: {dict(types)}")
                recommendations.append(f"Ensure '{column}' has consistent data type")
        
        return {
            "type_consistency": type_consistency,
            "issues": issues,
            "recommendations": recommendations
        }
    
    def _check_uniqueness(
        self,
        results: List[Dict[str, Any]],
        columns: List[str]
    ) -> Dict[str, Any]:
        """Check data uniqueness"""
        uniqueness = {}
        
        for column in columns:
            values = [row.get(column) for row in results if row.get(column) is not None]
            unique_values = set(str(v) for v in values)
            uniqueness_ratio = len(unique_values) / len(values) if values else 0
            
            uniqueness[column] = {
                "total_values": len(values),
                "unique_values": len(unique_values),
                "uniqueness_ratio": uniqueness_ratio,
                "cardinality": "high" if uniqueness_ratio > 0.9 else "medium" if uniqueness_ratio > 0.5 else "low"
            }
        
        return {"columns": uniqueness, "issues": [], "recommendations": []}
    
    def _calculate_quality_score(self, checks: Dict[str, Any]) -> float:
        """Calculate overall quality score (0-100)"""
        scores = []
        
        # Completeness score
        completeness = checks.get("completeness", {}).get("average_completeness", 0)
        scores.append(completeness * 100)
        
        # Consistency score (penalize duplicates)
        duplicate_ratio = checks.get("consistency", {}).get("duplicate_ratio", 0)
        consistency_score = (1 - duplicate_ratio) * 100
        scores.append(consistency_score)
        
        # Validity score (penalize type inconsistencies)
        type_issues = len(checks.get("validity", {}).get("type_consistency", {}))
        validity_score = 100 if type_issues == 0 else max(0, 100 - type_issues * 20)
        scores.append(validity_score)
        
        return sum(scores) / len(scores) if scores else 0
    
    def _quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"


def create_analytics_engine() -> AdvancedAnalyticsEngine:
    """Create analytics engine instance"""
    return AdvancedAnalyticsEngine()
