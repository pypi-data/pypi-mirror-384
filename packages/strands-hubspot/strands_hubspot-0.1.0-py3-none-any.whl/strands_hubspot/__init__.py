"""HubSpot CRM tool for Strands Agents SDK.

This package provides a comprehensive HubSpot CRM integration for Strands agents,
enabling read-only CRM operations for contacts, deals, companies, and more.

Example usage:
    ```python
    from strands import Agent
    from strands_hubspot import hubspot

    agent = Agent(tools=[hubspot])
    agent("search for contacts created in the last 30 days")
    ```
"""

from .hubspot import hubspot

__version__ = "0.1.0"
__all__ = ["hubspot"]

