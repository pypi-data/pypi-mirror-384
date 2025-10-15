# strands-hubspot

[![PyPI version](https://img.shields.io/pypi/v/strands-hubspot.svg)](https://pypi.org/project/strands-hubspot/)
[![Python Support](https://img.shields.io/pypi/pyversions/strands-hubspot.svg)](https://pypi.org/project/strands-hubspot/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

HubSpot CRM tool for [Strands Agents SDK](https://github.com/strands-agents/strands). Enables powerful CRM operations for AI agents with read-only access for safety.

## Features

- **Universal CRM Access**: Works with ANY HubSpot object type
- **Smart Search**: Advanced filtering with property-based queries
- **CRUD Operations**: Create, read, update, and delete records
- **Property Discovery**: Automatic field detection and validation
- **Association Management**: Link related objects (contacts, deals, companies)
- **Rich Console Output**: Beautiful table displays with Rich library
- **Type Safe**: Full type hints and validation
- **Easy Integration**: Drop-in tool for Strands agents

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

# Create an agent with HubSpot tool
agent = Agent(tools=[hubspot])

# Search contacts
agent("find all contacts created in the last 30 days")

# Create a deal
agent("create a deal called 'Acme Corp Q4' with amount 50000")

# Get company details
agent("get company information for ID 67890")
```

## Configuration

Set your HubSpot API key as an environment variable:

```bash
HUBSPOT_API_KEY=your_hubspot_api_key  # Required
HUBSPOT_DEFAULT_LIMIT=100              # Optional
```

Get your API key at: [app.hubspot.com/private-apps](https://app.hubspot.com/private-apps)

## Supported Actions

### Search (`search`)

```python
agent("search for contacts with email containing '@example.com'")
```

**Features:**

- Search any HubSpot object type (contacts, deals, companies, tickets, etc.)
- Advanced filtering by property values
- Sorting and pagination
- Property selection

### Get (`get`)

```python
agent("get contact with ID 12345")
```

**Features:**

- Retrieve full object details
- Specify which properties to return
- Works with any object type

### Create (`create`)

```python
agent("create a contact with email john@example.com and name John Doe")
```

**Features:**

- Create any HubSpot object
- Set initial properties
- Handle associations

### Update (`update`)

```python
agent("update contact 12345 with lifecycle stage 'customer'")
```

**Features:**

- Update any property
- Partial updates supported
- Property validation

### List Properties (`list_properties`)

```python
agent("show me all available contact properties")
```

**Features:**

- Discover available fields
- Property metadata
- Field types and options

### Get User Details (`get_user_details`)

```python
agent("get details for user ID 123")
```

**Features:**

- User profile information
- Owner assignment data

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
