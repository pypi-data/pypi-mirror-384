#!/usr/bin/env python3
"""
Comprehensive live test for StockAlert.pro Python SDK
Tests all major functionality with the provided API key
"""

import sys
import time
from datetime import datetime

from stockalert import StockAlert
from stockalert.exceptions import (
    APIError,
    AuthenticationError,
    ValidationError,
)


class TestRunner:
    """Test runner for SDK live testing"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = StockAlert(api_key=api_key, debug=True)
        self.created_alert_ids = []
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

    def log(self, message: str, level: str = "INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "SKIP": "⏭️ ",
            "TEST": "🧪",
        }.get(level, "  ")
        print(f"[{timestamp}] {prefix} {message}")

    def test_passed(self, test_name: str):
        """Mark test as passed"""
        self.test_results["passed"] += 1
        self.log(f"PASSED: {test_name}", "SUCCESS")

    def test_failed(self, test_name: str, error: str):
        """Mark test as failed"""
        self.test_results["failed"] += 1
        self.test_results["errors"].append(f"{test_name}: {error}")
        self.log(f"FAILED: {test_name} - {error}", "ERROR")

    def test_skipped(self, test_name: str, reason: str):
        """Mark test as skipped"""
        self.test_results["skipped"] += 1
        self.log(f"SKIPPED: {test_name} - {reason}", "SKIP")

    def cleanup(self):
        """Clean up created alerts"""
        self.log("\n🧹 Cleaning up created alerts...", "INFO")
        for alert_id in self.created_alert_ids:
            try:
                self.client.alerts.delete(alert_id)
                self.log(f"Deleted alert {alert_id}", "INFO")
            except Exception as e:
                self.log(f"Failed to delete alert {alert_id}: {e}", "ERROR")

    # ===== Authentication Tests =====

    def test_authentication(self):
        """Test API authentication"""
        self.log("\n=== Testing Authentication ===", "TEST")

        try:
            # Test valid API key
            response = self.client.alerts.list(limit=1)
            if response and "data" in response:
                self.test_passed("Valid API key authentication")
            else:
                self.test_failed("Valid API key authentication", "Unexpected response format")
        except Exception as e:
            self.test_failed("Valid API key authentication", str(e))

        # Test invalid API key
        try:
            invalid_client = StockAlert(api_key="sk_invalid_key_12345")
            invalid_client.alerts.list()
            self.test_failed("Invalid API key rejection", "Should have raised AuthenticationError")
        except AuthenticationError:
            self.test_passed("Invalid API key rejection")
        except Exception as e:
            self.test_failed("Invalid API key rejection", f"Wrong exception: {e}")

    # ===== Alert Creation Tests =====

    def test_alert_creation(self):
        """Test creating various types of alerts"""
        self.log("\n=== Testing Alert Creation ===", "TEST")

        # Test 1: Price above alert
        try:
            alert = self.client.alerts.create(
                symbol="AAPL",
                condition="price_above",
                threshold=200.0,
                notification="email",
            )
            if alert and hasattr(alert, 'id'):
                alert_id = alert.id
                self.created_alert_ids.append(alert_id)
                self.test_passed("Create price_above alert")
            else:
                self.test_failed("Create price_above alert", "Invalid response format")
        except Exception as e:
            self.test_failed("Create price_above alert", str(e))

        time.sleep(0.5)

        # Test 2: Price below alert
        try:
            alert = self.client.alerts.create(
                symbol="TSLA",
                condition="price_below",
                threshold=100.0,
                notification="email",
            )
            if alert and hasattr(alert, 'id'):
                alert_id = alert.id
                self.created_alert_ids.append(alert_id)
                self.test_passed("Create price_below alert")
            else:
                self.test_failed("Create price_below alert", "Invalid response format")
        except Exception as e:
            self.test_failed("Create price_below alert", str(e))

        time.sleep(0.5)

        # Test 3: Price change alert with parameters
        try:
            alert = self.client.alerts.create(
                symbol="MSFT",
                condition="price_change_up",
                threshold=5.0,
                notification="email",
                parameters={"period": "1d"},
            )
            if alert and hasattr(alert, 'id'):
                alert_id = alert.id
                self.created_alert_ids.append(alert_id)
                self.test_passed("Create price_change_up alert with parameters")
            else:
                self.test_failed("Create price_change_up alert", "Invalid response format")
        except Exception as e:
            self.test_failed("Create price_change_up alert with parameters", str(e))

        time.sleep(0.5)

        # Test 4: MA crossover alert
        try:
            alert = self.client.alerts.create(
                symbol="NVDA",
                condition="ma_crossover_golden",
                notification="email",
                parameters={"fast_period": 50, "slow_period": 200},
            )
            if alert and hasattr(alert, 'id'):
                alert_id = alert.id
                self.created_alert_ids.append(alert_id)
                self.test_passed("Create MA crossover alert")
            else:
                self.test_failed("Create MA crossover alert", "Invalid response format")
        except Exception as e:
            self.test_failed("Create MA crossover alert", str(e))

        time.sleep(0.5)

        # Test 5: Earnings announcement alert (requires threshold for days before)
        try:
            alert = self.client.alerts.create(
                symbol="META",
                condition="earnings_announcement",
                threshold=7,  # 7 days before earnings
                notification="email",
            )
            if alert and hasattr(alert, 'id'):
                alert_id = alert.id
                self.created_alert_ids.append(alert_id)
                self.test_passed("Create earnings announcement alert")
            else:
                self.test_failed("Create earnings announcement alert", "Invalid response format")
        except Exception as e:
            self.test_failed("Create earnings announcement alert", str(e))

    # ===== Alert Retrieval Tests =====

    def test_alert_retrieval(self):
        """Test retrieving alerts"""
        self.log("\n=== Testing Alert Retrieval ===", "TEST")

        # Test 1: List all alerts
        try:
            response = self.client.alerts.list()
            if response and "data" in response:
                alerts = response["data"]
                self.log(f"Retrieved {len(alerts)} alerts", "INFO")
                self.test_passed("List all alerts")
            else:
                self.test_failed("List all alerts", "Invalid response format")
        except Exception as e:
            self.test_failed("List all alerts", str(e))

        # Test 2: List with limit
        try:
            response = self.client.alerts.list(limit=2)
            if response and "data" in response:
                alerts = response["data"]
                if len(alerts) <= 2:
                    self.test_passed("List alerts with limit")
                else:
                    self.test_failed("List alerts with limit", f"Expected ≤2, got {len(alerts)}")
            else:
                self.test_failed("List alerts with limit", "Invalid response format")
        except Exception as e:
            self.test_failed("List alerts with limit", str(e))

        # Test 3: Filter by status
        try:
            response = self.client.alerts.list(status="active")
            if response and "data" in response:
                alerts = response["data"]
                all_active = all(a.get("status") == "active" for a in alerts)
                if all_active:
                    self.test_passed("Filter alerts by status")
                else:
                    self.test_failed("Filter alerts by status", "Found non-active alerts")
            else:
                self.test_failed("Filter alerts by status", "Invalid response format")
        except Exception as e:
            self.test_failed("Filter alerts by status", str(e))

        # Test 4: Get specific alert
        if self.created_alert_ids:
            try:
                alert_id = self.created_alert_ids[0]
                alert = self.client.alerts.get(alert_id)
                if alert and hasattr(alert, 'id'):
                    if alert.id == alert_id:
                        self.test_passed("Get specific alert")
                    else:
                        self.test_failed("Get specific alert", "ID mismatch")
                else:
                    self.test_failed("Get specific alert", "Invalid response format")
            except Exception as e:
                self.test_failed("Get specific alert", str(e))
        else:
            self.test_skipped("Get specific alert", "No alerts created")

    # ===== Alert Update Tests =====

    def test_alert_updates(self):
        """Test updating alerts"""
        self.log("\n=== Testing Alert Updates ===", "TEST")

        if not self.created_alert_ids:
            self.test_skipped("All update tests", "No alerts created")
            return

        alert_id = self.created_alert_ids[0]

        # Test 1: Pause alert
        try:
            result = self.client.alerts.pause(alert_id)
            if result and result.get("status") == "paused":
                # Verify via get
                check = self.client.alerts.get(alert_id)
                if check.status == "paused":
                    self.test_passed("Pause alert")
                else:
                    self.test_failed("Pause alert", "Status not updated in get()")
            else:
                self.test_failed("Pause alert", f"Unexpected response: {result}")
        except Exception as e:
            self.test_failed("Pause alert", str(e))

        time.sleep(0.5)

        # Test 2: Activate alert
        try:
            result = self.client.alerts.activate(alert_id)
            if result and result.get("status") == "active":
                # Verify via get
                check = self.client.alerts.get(alert_id)
                if check.status == "active":
                    self.test_passed("Activate alert")
                else:
                    self.test_failed("Activate alert", "Status not updated in get()")
            else:
                self.test_failed("Activate alert", f"Unexpected response: {result}")
        except Exception as e:
            self.test_failed("Activate alert", str(e))

        time.sleep(0.5)

        # Test 3: Update alert threshold
        try:
            alert = self.client.alerts.update(alert_id, threshold=250.0)
            if alert:
                # Verify threshold
                check = self.client.alerts.get(alert_id)
                if check.threshold == 250.0:
                    self.test_passed("Update alert threshold")
                else:
                    self.test_failed("Update alert threshold", "Threshold not updated")
            else:
                self.test_failed("Update alert threshold", "No response")
        except Exception as e:
            self.test_failed("Update alert threshold", str(e))

    # ===== Alert History Tests =====

    def test_alert_history(self):
        """Test alert history retrieval"""
        self.log("\n=== Testing Alert History ===", "TEST")

        if not self.created_alert_ids:
            self.test_skipped("Alert history tests", "No alerts created")
            return

        alert_id = self.created_alert_ids[0]

        try:
            response = self.client.alerts.history(alert_id)
            if response:
                if "data" in response:
                    history = response["data"]
                    self.log(f"Retrieved {len(history)} history entries", "INFO")
                    self.test_passed("Get alert history")
                else:
                    self.test_passed("Get alert history (empty)")
            else:
                self.test_failed("Get alert history", "No response")
        except Exception as e:
            # History might not be available for new alerts
            if "404" in str(e) or "not found" in str(e).lower():
                self.test_passed("Get alert history (no history yet)")
            else:
                self.test_failed("Get alert history", str(e))

    # ===== Alert Statistics Tests =====

    def test_alert_statistics(self):
        """Test alert statistics"""
        self.log("\n=== Testing Alert Statistics ===", "TEST")

        try:
            response = self.client.alerts.stats()
            if response and "data" in response:
                stats = response["data"]
                self.log(f"Stats: {stats}", "INFO")
                self.test_passed("Get alert statistics")
            else:
                self.test_failed("Get alert statistics", "Invalid response format")
        except Exception as e:
            self.test_failed("Get alert statistics", str(e))

    # ===== Pagination Tests =====

    def test_pagination(self):
        """Test pagination functionality"""
        self.log("\n=== Testing Pagination ===", "TEST")

        try:
            # Test with small page size
            response = self.client.alerts.list(limit=2)
            if response and "meta" in response:
                meta = response["meta"]
                pagination = meta.get("pagination", {})
                self.log(f"Pagination: {pagination}", "INFO")
                self.test_passed("Pagination metadata")
            else:
                self.test_failed("Pagination metadata", "No meta in response")
        except Exception as e:
            self.test_failed("Pagination metadata", str(e))

        # Test iterate method
        try:
            count = 0
            for _alert in self.client.alerts.iterate(limit=2):
                count += 1
                if count >= 5:  # Limit iterations
                    break
            self.test_passed("Alert iteration")
        except Exception as e:
            self.test_failed("Alert iteration", str(e))

    # ===== Error Handling Tests =====

    def test_error_handling(self):
        """Test error handling"""
        self.log("\n=== Testing Error Handling ===", "TEST")

        # Test 1: Invalid symbol
        try:
            self.client.alerts.create(
                symbol="INVALID_SYMBOL_12345",
                condition="price_above",
                threshold=100.0,
                notification="email",
            )
            self.test_failed("Invalid symbol handling", "Should have raised error")
        except (APIError, ValidationError):
            self.test_passed("Invalid symbol handling")
        except Exception as e:
            self.test_failed("Invalid symbol handling", f"Unexpected error: {e}")

        # Test 2: Missing required field
        try:
            self.client.alerts.create(
                symbol="AAPL",
                condition="price_above",
                # Missing threshold
                notification="email",
            )
            self.test_failed("Missing field validation", "Should have raised error")
        except (APIError, ValidationError, TypeError):
            self.test_passed("Missing field validation")
        except Exception as e:
            self.test_failed("Missing field validation", f"Unexpected error: {e}")

        # Test 3: Invalid alert ID
        try:
            self.client.alerts.get("invalid_alert_id_12345")
            self.test_failed("Invalid alert ID handling", "Should have raised error")
        except APIError:
            self.test_passed("Invalid alert ID handling")
        except Exception as e:
            self.test_failed("Invalid alert ID handling", f"Unexpected error: {e}")

    # ===== Alert Deletion Tests =====

    def test_alert_deletion(self):
        """Test deleting alerts"""
        self.log("\n=== Testing Alert Deletion ===", "TEST")

        if not self.created_alert_ids:
            self.test_skipped("Alert deletion", "No alerts created")
            return

        # Delete one alert and verify
        alert_id = self.created_alert_ids[0]

        try:
            response = self.client.alerts.delete(alert_id)
            if response:
                # Verify deletion
                try:
                    self.client.alerts.get(alert_id)
                    self.test_failed("Delete alert", "Alert still exists")
                except APIError as e:
                    if "404" in str(e) or "not found" in str(e).lower():
                        self.test_passed("Delete alert")
                        self.created_alert_ids.remove(alert_id)
                    else:
                        self.test_failed("Delete alert", f"Unexpected error: {e}")
            else:
                self.test_failed("Delete alert", "No response")
        except Exception as e:
            self.test_failed("Delete alert", str(e))

    # ===== Run All Tests =====

    def run_all_tests(self):
        """Run all tests"""
        self.log("\n" + "=" * 60, "INFO")
        self.log("StockAlert.pro Python SDK - Live Test Suite", "INFO")
        self.log("=" * 60 + "\n", "INFO")

        start_time = time.time()

        try:
            self.test_authentication()
            self.test_alert_creation()
            self.test_alert_retrieval()
            self.test_alert_updates()
            self.test_alert_history()
            self.test_alert_statistics()
            self.test_pagination()
            self.test_error_handling()
            self.test_alert_deletion()
        finally:
            self.cleanup()

        elapsed_time = time.time() - start_time

        # Print summary
        self.log("\n" + "=" * 60, "INFO")
        self.log("Test Summary", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Total Tests: {self.test_results['passed'] + self.test_results['failed']}", "INFO")
        self.log(f"Passed: {self.test_results['passed']}", "SUCCESS")
        self.log(f"Failed: {self.test_results['failed']}", "ERROR" if self.test_results["failed"] > 0 else "INFO")
        self.log(f"Skipped: {self.test_results['skipped']}", "INFO")
        self.log(f"Time: {elapsed_time:.2f}s", "INFO")

        if self.test_results["errors"]:
            self.log("\nFailed Tests:", "ERROR")
            for error in self.test_results["errors"]:
                self.log(f"  - {error}", "ERROR")

        self.log("=" * 60 + "\n", "INFO")

        return self.test_results["failed"] == 0


def main():
    """Main test function"""
    API_KEY = "sk_d4a622c84ff73395e4f828b2c7a2f4dec35c0cfcc599e369a20f608dcff1f614"

    try:
        runner = TestRunner(API_KEY)
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
