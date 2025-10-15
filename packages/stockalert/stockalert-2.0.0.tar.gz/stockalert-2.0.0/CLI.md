# StockAlert CLI

The StockAlert Python SDK includes a command-line interface for managing alerts.

## Installation

```bash
pip install stockalert
```

## Configuration

Set your API key as an environment variable:

```bash
export STOCKALERT_API_KEY=sk_your_api_key
```

## Usage

### List alerts

```bash
# List all alerts
stockalert list

# Filter by symbol
stockalert list --symbol AAPL

# Filter by status
stockalert list --status active

# Output as JSON
stockalert list --json
```

### Create an alert

```bash
# Basic price alert
stockalert create AAPL price_above --threshold 200

# With SMS notification
stockalert create AAPL price_below --threshold 150 --notification sms

# Technical indicator alert
stockalert create TSLA ma_touch_above --parameters '{"ma_period": 50}'
```

### Get alert details

```bash
stockalert get <alert-id>

# As JSON
stockalert get <alert-id> --json
```

### Update alert status

```bash
# Pause an alert
stockalert pause <alert-id>

# Activate an alert
stockalert activate <alert-id>
```

### Delete an alert

```bash
# With confirmation
stockalert delete <alert-id>

# Skip confirmation
stockalert delete <alert-id> --force
```

## Examples

```bash
# Create a price alert for Apple
stockalert create AAPL price_above -t 200

# List all active alerts
stockalert list --status active

# Get details in JSON format
stockalert get abc123 --json

# Pause an alert
stockalert pause abc123
```

## Help

```bash
# General help
stockalert --help

# Command-specific help
stockalert create --help
```
