# strands-hubspot

[![PyPI version](https://img.shields.io/pypi/v/strands-hubspot.svg)](https://pypi.org/project/strands-hubspot/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/strands-hubspot)](https://pypi.org/project/strands-hubspot/)
[![Python Support](https://img.shields.io/pypi/pyversions/strands-hubspot.svg)](https://pypi.org/project/strands-hubspot/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Workflow Status](https://github.com/eraykeskinmac/strands-hubspot/actions/workflows/publish.yml/badge.svg)](https://github.com/eraykeskinmac/strands-hubspot/actions)

**READ-ONLY** HubSpot CRM tool for [Strands Agents SDK](https://github.com/strands-agents/strands). Enables safe CRM data access for AI agents with **zero risk** of data modification.

## Features

- 🔍 **Universal READ-ONLY Access**: Safely search ANY HubSpot object type (contacts, deals, companies, tickets, etc.)
- 🔎 **Smart Search**: Advanced filtering with property-based queries and sorting
- 📄 **Object Retrieval**: Get detailed information for specific CRM objects by ID
- 🏷️ **Property Discovery**: List and explore all available properties for any object type
- 👤 **User Management**: Get HubSpot user/owner details and assignments
- 🎨 **Rich Console Output**: Beautiful table displays with Rich library formatting
- 🛡️ **100% Safe**: **NO CREATE, UPDATE, or DELETE** operations - read-only by design
- 🔧 **Easy Integration**: Drop-in tool for Strands agents
- 📝 **Type Safe**: Full type hints and comprehensive error handling

## Requirements

- Python 3.9+
- Strands Agents SDK 1.11.0+
- HubSpot API access

## Installation

```bash
pip install strands-hubspot
```

## Quick Start

```python
from strands import Agent
from strands_hubspot import hubspot

# Create an agent with HubSpot READ-ONLY tool
agent = Agent(tools=[hubspot])

# Search contacts (READ-ONLY)
agent("find all contacts created in the last 30 days")

# Get company details (READ-ONLY)
agent("get company information for ID 67890")

# List available properties (READ-ONLY)
agent("show me all available deal properties")

# Search with filters (READ-ONLY)
agent("search for deals with amount greater than 10000")
```

## Configuration

Set your HubSpot API key as an environment variable:

```bash
HUBSPOT_API_KEY=your_hubspot_api_key  # Required
HUBSPOT_DEFAULT_LIMIT=100              # Optional
```

Get your API key at: [app.hubspot.com/private-apps](https://app.hubspot.com/private-apps)

## Supported READ-ONLY Actions

> ⚠️ **Important**: This tool is designed for READ-ONLY operations only. It **CANNOT** create, update, or delete any HubSpot data, ensuring complete safety for your CRM.

### Search (`search`)

```python
agent("search for contacts with email containing '@example.com'")
```

**Features:**

- Search any HubSpot object type (contacts, deals, companies, tickets, etc.)
- Advanced filtering by property values
- Sorting and pagination support
- Property selection and customization

### Get (`get`)

```python
agent("get contact with ID 12345")
```

**Features:**

- Retrieve full object details by ID
- Specify which properties to return
- Works with any object type
- Comprehensive error handling

### List Properties (`list_properties`)

```python
agent("show me all available contact properties")
```

**Features:**

- Discover available fields for any object type
- Property metadata and type information
- Field types and available options

### Get Property Details (`get_property`)

```python
agent("get details about the 'email' property for contacts")
```

**Features:**

- Detailed property metadata
- Property type, options, and validation rules
- Useful for understanding data structure

### Get User Details (`get_user_details`)

```python
agent("get details for user ID 123")
```

**Features:**

- User profile information
- Owner assignment data
- Permission and role details

## Why READ-ONLY?

🛡️ **Safety First**: This tool is intentionally designed as READ-only to:

- **Prevent accidental data loss** or corruption in your HubSpot CRM
- **Enable safe AI exploration** of your customer data
- **Allow analytics and reporting** without modification risks
- **Perfect for research and insights** without affecting production data
- **Ideal for AI agents** that need CRM access but shouldn't modify records

## Use Cases

- 📊 **Analytics & Reporting**: Generate insights from CRM data
- 🔍 **Customer Research**: Search and analyze customer information
- 📋 **Data Discovery**: Explore available properties and data structure
- 🤖 **AI-Powered Insights**: Let agents analyze CRM data safely
- 📈 **Sales Intelligence**: Extract trends and patterns from deals/contacts
- 🎯 **Lead Analysis**: Research prospects and opportunities

## Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- **PyPI**: [pypi.org/project/strands-hubspot](https://pypi.org/project/strands-hubspot/)
- **GitHub**: [github.com/eraykeskinmac/strands-hubspot](https://github.com/eraykeskinmac/strands-hubspot)
- **Strands Agents SDK**: [github.com/strands-agents/strands](https://github.com/strands-agents/strands)
- **HubSpot API**: [developers.hubspot.com](https://developers.hubspot.com/)

---

**Built for the Strands community** 🚀
