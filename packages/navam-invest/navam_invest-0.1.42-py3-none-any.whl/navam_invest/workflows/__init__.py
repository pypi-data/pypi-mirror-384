"""Multi-agent workflows for comprehensive investment analysis."""

from navam_invest.workflows.idea_discovery import create_idea_discovery_workflow
from navam_invest.workflows.investment_analysis import create_investment_analysis_workflow
from navam_invest.workflows.portfolio_protection import create_portfolio_protection_workflow
from navam_invest.workflows.tax_optimization import create_tax_optimization_workflow

__all__ = [
    "create_investment_analysis_workflow",
    "create_idea_discovery_workflow",
    "create_portfolio_protection_workflow",
    "create_tax_optimization_workflow",
]
