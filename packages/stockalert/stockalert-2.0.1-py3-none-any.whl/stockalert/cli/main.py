"""StockAlert CLI - Command line interface for StockAlert.pro."""
import argparse
import json
import os
import sys
from typing import Any

from stockalert import StockAlert, __version__
from stockalert.exceptions import StockAlertError


def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, default=str))


def get_client() -> StockAlert:
    """Get StockAlert client from environment or prompt."""
    api_key = os.environ.get("STOCKALERT_API_KEY")
    if not api_key:
        print("Error: STOCKALERT_API_KEY environment variable not set", file=sys.stderr)
        print("Set it with: export STOCKALERT_API_KEY=sk_your_api_key", file=sys.stderr)
        sys.exit(1)
    return StockAlert(api_key=api_key)


def cmd_list(args: argparse.Namespace) -> None:
    """List alerts command."""
    client = get_client()

    params = {}
    if args.symbol:
        params["symbol"] = args.symbol
    if args.status:
        params["status"] = args.status
    if args.limit:
        params["limit"] = args.limit

    try:
        response = client.alerts.list(**params)

        if args.json:
            print_json(response)
        else:
            # Check if response is a dict with data key or direct list
            if isinstance(response, dict) and "data" in response:
                alerts = response["data"]
            elif isinstance(response, list):
                alerts = response
            else:
                alerts = []

            if not alerts:
                print("No alerts found")
                return

            print(f"Found {len(alerts)} alerts:")
            for alert in alerts:
                threshold = alert.get('threshold', 'N/A')
                if threshold != 'N/A' and isinstance(threshold, (int, float)):
                    threshold = f"${threshold}"
                print(f"- {alert['id']}: {alert['symbol']} {alert['condition']} "
                      f"@ {threshold} [{alert['status']}]")
    except StockAlertError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_create(args: argparse.Namespace) -> None:
    """Create alert command."""
    client = get_client()

    data = {
        "symbol": args.symbol,
        "condition": args.condition,
        "notification": args.notification or "email"
    }

    if args.threshold:
        data["threshold"] = args.threshold

    if args.parameters:
        data["parameters"] = json.loads(args.parameters)

    try:
        alert = client.alerts.create(**data)

        if args.json:
            print_json(alert.to_dict())
        else:
            print(f"✅ Alert created: {alert.id}")
            print(f"   Symbol: {alert.symbol}")
            print(f"   Condition: {alert.condition}")
            if hasattr(alert, "threshold"):
                print(f"   Threshold: ${alert.threshold}")
    except StockAlertError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_get(args: argparse.Namespace) -> None:
    """Get alert command."""
    client = get_client()

    try:
        alert = client.alerts.get(args.alert_id)

        if args.json:
            print_json(alert.to_dict())
        else:
            print(f"Alert: {alert.id}")
            print(f"Symbol: {alert.symbol}")
            print(f"Condition: {alert.condition}")
            print(f"Status: {alert.status}")
            if hasattr(alert, "threshold"):
                print(f"Threshold: ${alert.threshold}")
            print(f"Created: {alert.created_at}")
            print(f"Updated: {alert.updated_at}")
    except StockAlertError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args: argparse.Namespace) -> None:
    """Delete alert command."""
    client = get_client()

    try:
        if not args.force:
            response = input(f"Delete alert {args.alert_id}? [y/N] ")
            if response.lower() != "y":
                print("Cancelled")
                return

        client.alerts.delete(args.alert_id)
        print(f"✅ Alert {args.alert_id} deleted")
    except StockAlertError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_pause(args: argparse.Namespace) -> None:
    """Pause alert command."""
    client = get_client()

    try:
        result = client.alerts.pause(args.alert_id)
        alert_id = result.get("alertId", args.alert_id)
        print(f"✅ Alert {alert_id} paused")
    except StockAlertError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_activate(args: argparse.Namespace) -> None:
    """Activate alert command."""
    client = get_client()

    try:
        result = client.alerts.activate(args.alert_id)
        alert_id = result.get("alertId", args.alert_id)
        print(f"✅ Alert {alert_id} activated")
    except StockAlertError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="StockAlert CLI - Manage stock alerts from the command line"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List alerts")
    list_parser.add_argument("-s", "--symbol", help="Filter by symbol")
    list_parser.add_argument("--status", choices=["active", "paused", "triggered"])
    list_parser.add_argument("-l", "--limit", type=int, help="Limit results")
    list_parser.add_argument("-j", "--json", action="store_true", help="Output as JSON")
    list_parser.set_defaults(func=cmd_list)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create an alert")
    create_parser.add_argument("symbol", help="Stock symbol")
    create_parser.add_argument("condition", help="Alert condition")
    create_parser.add_argument("-t", "--threshold", type=float, help="Threshold value")
    create_parser.add_argument("-n", "--notification", choices=["email", "sms"])
    create_parser.add_argument("-p", "--parameters", help="Additional parameters as JSON")
    create_parser.add_argument("-j", "--json", action="store_true", help="Output as JSON")
    create_parser.set_defaults(func=cmd_create)

    # Get command
    get_parser = subparsers.add_parser("get", help="Get alert details")
    get_parser.add_argument("alert_id", help="Alert ID")
    get_parser.add_argument("-j", "--json", action="store_true", help="Output as JSON")
    get_parser.set_defaults(func=cmd_get)

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete an alert")
    delete_parser.add_argument("alert_id", help="Alert ID")
    delete_parser.add_argument("-f", "--force", action="store_true", help="Skip confirmation")
    delete_parser.set_defaults(func=cmd_delete)

    # Pause command
    pause_parser = subparsers.add_parser("pause", help="Pause an alert")
    pause_parser.add_argument("alert_id", help="Alert ID")
    pause_parser.set_defaults(func=cmd_pause)

    # Activate command
    activate_parser = subparsers.add_parser("activate", help="Activate an alert")
    activate_parser.add_argument("alert_id", help="Alert ID")
    activate_parser.set_defaults(func=cmd_activate)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
