"""
Target Synthesis Agent Package

An intelligent agent for creating and synthesizing target variables for machine learning tasks.
Uses LLM intelligence to analyze data and generate optimal target variables.
"""

from .sql_agent import TargetSynthesisAgent
from .models import (
    TargetVariable, 
    TargetSynthesisResult, 
    SynthesisStrategy,
    TargetType,
    ColumnAnalysis,
    BusinessContext,
    DomainInfo,
    MLApproachInfo,
    DatasetColumnInsight,
    DatasetInsights,
    AgentInputsResult,
    AgentInputsRequest,
    DataFrameInputsRequest
)

__version__ = "1.0.0"
__all__ = [
    "TargetSynthesisAgent",
    "TargetVariable",
    "TargetSynthesisResult", 
    "SynthesisStrategy",
    "TargetType",
    "ColumnAnalysis",
    "BusinessContext",
    "DomainInfo",
    "MLApproachInfo",
    "DatasetColumnInsight",
    "DatasetInsights",
    "AgentInputsResult",
    "AgentInputsRequest",
    "DataFrameInputsRequest"
]
