"""
Configuration for the Target Synthesis Agent.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
import os
from typing import Dict, Any, Optional, List


class TargetSynthesisConfig(BaseSettings):
    """Configuration settings for the Target Synthesis Agent."""
    
    # AI Provider Configuration
    ai_provider: str = Field(
        default=os.getenv("LLM_PROVIDER", "openai"),
        env="LLM_PROVIDER",
        description="AI provider to use (e.g., openai, anthropic, etc.)"
    )
    ai_task_type: str = Field(
        default="suggestions_generator",
        description="Task type for AI requests"
    )
    model_name: str = Field(
        default=os.getenv("LLM_MODEL", "gpt-4.1-mini"),
        env="LLM_MODEL",
        description="AI model to use (e.g., gpt-4, claude-2, etc.)"
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="AI model temperature"
    )
    max_tokens: int = Field(
        default=4000,
        ge=100,
        le=8000,
        description="Maximum tokens for AI response"
    )
    api_key: str = Field(
        default=os.getenv("LLM_API_KEY", ""),
        env="LLM_API_KEY",
        description="API key for the LLM provider"
    )
    
    # Supported Target Types
    supported_target_types: List[str] = Field(
        default=["binary", "multiclass", "regression", "time_series", "multi_label"],
        description="Supported target variable types"
    )
    
    # Synthesis Strategies
    synthesis_strategies: Dict[str, List[str]] = Field(
        default={
            "rule_based": ["threshold", "categorization", "combination", "derivation"],
            "threshold_based": ["percentile", "statistical", "business_rules", "domain_knowledge"],
            "clustering_based": ["kmeans", "dbscan", "hierarchical", "gaussian_mixture"],
            "ml_based": ["supervised", "unsupervised", "semi_supervised", "reinforcement"],
            "hybrid": ["rule_ml", "threshold_clustering", "multi_strategy"]
        },
        description="Available synthesis strategies by type"
    )
    
    # Output Settings
    output_format: str = Field(default="json", description="Output format")
    include_visualizations: bool = Field(default=False, description="Include visualization recommendations")
    detailed_reasoning: bool = Field(default=True, description="Include detailed reasoning")
    
    class Config:
        env_prefix = "TARGET_SYNTHESIS_"
        case_sensitive = False
