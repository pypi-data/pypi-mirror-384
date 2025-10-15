# LLM Budget Management System

A comprehensive cost control and budget management system for LLM usage with real-time tracking, intelligent alerts, and optimization suggestions.

## Features

### 🎯 **Comprehensive Budget Control**
- **Flexible Budget Periods**: Hourly, daily, weekly, monthly, yearly, or total budgets
- **Hard & Soft Limits**: Enforce spending limits or just track usage
- **Intelligent Thresholds**: Configurable warning and critical alert levels
- **Auto-Suspension**: Automatically disable budgets when exceeded

### 📊 **Real-Time Usage Tracking**
- **Multi-Dimensional Tracking**: Cost, tokens, requests, latency, and success rates
- **Detailed Breakdowns**: Per-model, per-user, per-session cost analysis
- **Token Type Tracking**: Input, output, cache read/write token costs
- **Performance Metrics**: Efficiency scores and optimization insights

### ⚠️ **Intelligent Alerts & Monitoring**
- **Threshold-Based Alerts**: Warning, critical, and emergency notifications
- **Anomaly Detection**: Statistical analysis to detect unusual usage patterns
- **Rate Limiting**: Protect against runaway costs with usage rate controls
- **Trend Analysis**: Historical usage patterns and projections

### 🔧 **Advanced Cost Management**
- **Model-Specific Pricing**: Accurate cost calculation for different LLM models
- **Optimization Suggestions**: AI-powered recommendations to reduce costs
- **Usage Projections**: Predict end-of-period costs based on current trends
- **Efficiency Scoring**: Track cost-effectiveness of LLM usage

## Quick Start

### Basic Usage

```python
from aii.budget import BudgetManager, BudgetConfig, BudgetPeriod
from decimal import Decimal

# Initialize the budget manager
manager = BudgetManager()

# Create a monthly budget
budget = BudgetConfig(
    name="development",
    max_cost=Decimal("100.0"),
    period=BudgetPeriod.MONTHLY,
    warning_threshold=80.0,
    critical_threshold=90.0
)
manager.create_budget(budget)

# Track LLM usage
result = manager.track_usage(
    budget_name="development",
    cost=Decimal("2.50"),
    input_tokens=1000,
    output_tokens=500,
    model="gpt-4",
    user_id="user123"
)

print(f"Status: {result['status']}")
print(f"Usage: {result['cost_percentage']:.1f}%")
```

### Command Line Interface

The budget system integrates with the aii CLI:

```bash
# Create a new budget
aii budget create "development" max-cost 100.0 period monthly

# List all budgets
aii budget list

# Show detailed budget information
aii budget show "development"

# Track manual usage
aii budget track "development" cost 5.25 tokens 1500

# Generate usage reports
aii budget report
```

## Architecture

### Core Components

```
aii/budget/
├── __init__.py          # Package exports
├── models.py           # Pydantic data models
├── manager.py          # Main budget management logic
├── tracker.py          # Usage tracking and analysis
└── README.md           # This documentation
```

### Command Integration

```
aii/commands/
├── patterns/budget.yaml    # Command definitions
└── handlers/budget.py      # Command handlers
```

### Data Models

#### BudgetConfig
Central budget configuration with limits, thresholds, and policies.

```python
budget = BudgetConfig(
    name="production",
    max_cost=Decimal("500.0"),
    period=BudgetPeriod.MONTHLY,
    warning_threshold=75.0,
    critical_threshold=90.0,
    auto_suspend=True,
    hard_limit=True
)
```

#### UsageMetrics
Comprehensive usage tracking with performance analytics.

```python
metrics = UsageMetrics()
metrics.add_request(
    cost=Decimal("0.15"),
    input_tokens=800,
    output_tokens=400,
    latency=1.2,
    success=True,
    cached=False
)
```

#### CostBreakdown
Detailed cost analysis across multiple dimensions.

```python
breakdown = CostBreakdown()
breakdown.add_cost(
    total_cost=Decimal("0.15"),
    model="gpt-4",
    user_id="user123",
    input_token_cost=Decimal("0.10"),
    output_token_cost=Decimal("0.05")
)
```

## Command Reference

### Budget Creation

```bash
# Basic budget
aii budget create "project-name" max-cost 100.0

# Advanced budget with custom settings
aii budget create "production" max-cost 500.0 period monthly \
  --warning-threshold 75 --critical-threshold 90
```

### Budget Management

```bash
# List all budgets with status
aii budget list

# Show detailed budget information
aii budget show "project-name"

# Update budget limits
aii budget update "project-name" max-cost 150.0
aii budget update "project-name" warning 85

# Reset budget usage for current period
aii budget reset "project-name"

# Delete budget (requires confirmation)
aii budget delete "project-name"
```

### Usage Tracking

```bash
# Manual usage tracking
aii budget track "project-name" cost 2.50 tokens 1500 model gpt-4

# Generate reports
aii budget report                    # All budgets
aii budget report "project-name"     # Specific budget
aii budget report --format json     # JSON output
```

## Configuration Options

### Budget Periods

- **hourly**: Reset every hour
- **daily**: Reset every day at midnight
- **weekly**: Reset every Monday
- **monthly**: Reset on the 1st of each month
- **yearly**: Reset on January 1st
- **total**: Never reset (lifetime budget)

### Alert Thresholds

- **Warning Threshold**: 0-100% (default: 80%)
- **Critical Threshold**: 0-100% (default: 90%, must be > warning)

### Budget Policies

- **Auto Suspend**: Automatically disable budget when exceeded
- **Hard Limit**: Reject requests that would exceed budget
- **Soft Limit**: Allow requests but continue tracking

## Integration Examples

### Programmatic Usage

```python
from aii.budget import BudgetManager
from decimal import Decimal

# Initialize with custom database path
manager = BudgetManager(db_path="custom_budgets.db")

# Create budget with advanced settings
budget = BudgetConfig(
    name="ai-research",
    max_cost=Decimal("1000.0"),
    period=BudgetPeriod.MONTHLY,
    warning_threshold=70.0,
    critical_threshold=85.0,
    max_tokens=1000000,
    max_requests=10000,
    auto_suspend=False,
    hard_limit=True
)
manager.create_budget(budget)

# Set up alert callbacks
def budget_alert_handler(alert_data):
    print(f"🚨 Budget Alert: {alert_data['budget_name']}")
    print(f"Level: {alert_data['alert_level']}")
    print(f"Usage: {alert_data['cost_percentage']:.1f}%")

manager.add_alert_callback(budget_alert_handler)

# Track complex usage scenarios
manager.track_usage(
    budget_name="ai-research",
    cost=Decimal("15.75"),
    input_tokens=5000,
    output_tokens=2000,
    cache_read_tokens=500,
    cache_write_tokens=100,
    model="gpt-4",
    user_id="researcher-001",
    session_id="session-abc123",
    success=True,
    cached=True,
    latency=2.3,
    metadata={"experiment": "nlp-analysis", "dataset": "papers-2024"}
)
```

### Report Generation

```python
# Generate comprehensive reports
report = manager.generate_report(include_suggestions=True)

print(f"Total Budgets: {report['summary']['total_budgets']}")
print(f"Total Cost: ${report['summary']['total_cost']}")

for budget_name, data in report["budgets"].items():
    usage = data["usage"]
    print(f"\n{budget_name}:")
    print(f"  Usage: {usage['cost_percentage']:.1f}%")
    print(f"  Efficiency: {usage['efficiency_score']:.1f}/100")

    # Show optimization suggestions
    if "optimization_suggestions" in data:
        for suggestion in data["optimization_suggestions"][:3]:
            print(f"  💡 {suggestion['title']}")
```

### Model Cost Configuration

```python
from aii.budget.tracker import CostTracker

tracker = CostTracker()

# Update pricing for new models
tracker.update_pricing("claude-3-opus", {
    "input_tokens": Decimal("0.000015"),  # $15 per 1M tokens
    "output_tokens": Decimal("0.000075"), # $75 per 1M tokens
})

# Calculate costs
cost, breakdown = tracker.calculate_cost(
    model="claude-3-opus",
    input_tokens=1000,
    output_tokens=500
)

print(f"Total cost: ${cost}")
print(f"Input cost: ${breakdown['input_cost']}")
print(f"Output cost: ${breakdown['output_cost']}")
```

## Performance & Scalability

### Database Design

- **SQLite Backend**: Efficient local storage with ACID compliance
- **Indexed Queries**: Optimized for time-based and budget-based lookups
- **Concurrent Access**: Thread-safe operations with proper locking
- **Data Retention**: Configurable cleanup of historical records

### Memory Management

- **In-Memory Caching**: Active budgets and usage data cached for performance
- **Lazy Loading**: Historical data loaded on-demand
- **Bounded Collections**: Usage history limited to prevent memory leaks

### Monitoring & Observability

```python
# Get system statistics
stats = manager.get_stats()
print(f"Active budgets: {stats['active_budgets']}")
print(f"Total requests tracked: {stats['usage_tracker_stats']['total_requests']}")
print(f"Anomaly rate: {stats['usage_tracker_stats']['anomaly_rate']:.2%}")

# Clean up old records
deleted_count = manager.cleanup_old_records(days_to_keep=90)
print(f"Cleaned up {deleted_count} old records")
```

## Testing

The budget system includes comprehensive test coverage:

```bash
# Run all budget tests
uv run python -m pytest aii/tests/budget/ -v

# Run specific test categories
uv run python -m pytest aii/tests/budget/test_models.py -v
uv run python -m pytest aii/tests/budget/test_manager.py -v
uv run python -m pytest aii/tests/budget/test_handlers.py -v
```

## Security Considerations

### Data Protection
- **No Sensitive Data**: Budget system doesn't store API keys or credentials
- **User Privacy**: User IDs are treated as opaque identifiers
- **Access Control**: Database permissions should be restricted appropriately

### Cost Protection
- **Hard Limits**: Prevent runaway costs with enforced spending limits
- **Rate Limiting**: Protect against usage spikes and abuse
- **Anomaly Detection**: Identify unusual patterns that may indicate issues

### Validation
- **Input Sanitization**: All user inputs validated and sanitized
- **Schema Validation**: Pydantic models ensure data integrity
- **Error Handling**: Graceful handling of edge cases and failures

## Troubleshooting

### Common Issues

**Budget not found errors**
```python
# Ensure budget exists before tracking usage
budget = manager.get_budget("project-name")
if not budget:
    print("Budget does not exist - create it first")
```

**Database permission errors**
```bash
# Check database file permissions
ls -la budget.db
# Ensure write access for the application user
chmod 664 budget.db
```

**High memory usage**
```python
# Clean up old records periodically
manager.cleanup_old_records(days_to_keep=30)

# Reset usage tracker statistics
manager.usage_tracker.reset_statistics()
```

### Debug Mode

```python
import logging
logging.getLogger("aii.budget").setLevel(logging.DEBUG)
```

## Contributing

When contributing to the budget system:

1. **Add Tests**: All new features must include comprehensive tests
2. **Update Documentation**: Keep README and docstrings current
3. **Follow Patterns**: Use existing code patterns and conventions
4. **Performance**: Consider impact on database and memory usage
5. **Security**: Review for potential cost or data leakage issues

## Roadmap

### Planned Features

- **Cloud Integration**: Support for cloud-based budget storage
- **Advanced Analytics**: Machine learning-based usage predictions
- **Multi-Currency**: Support for different currency denominations
- **Budget Templates**: Pre-configured budgets for common use cases
- **Webhook Integration**: External notifications and integrations
- **Budget Sharing**: Team-based budget management and permissions

### API Evolution

The budget system API is designed for backward compatibility. Future versions will:

- Maintain existing model interfaces
- Add optional parameters for new features
- Provide migration utilities for schema changes
- Deprecate features gracefully with clear timelines

---

For more information, see the [Engineering Implementation Specification](../system-dev-docs/ENGINEERING_IMPLEMENTATION_SPEC.md) and [Product Specification](../system-design-docs/product-spec-use-cases-v3.md).