"""
Data models for the Target Synthesis Agent.
"""

from typing import List, Dict, Any, Optional, Union, TypedDict
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


@dataclass
class DomainInfo:
    """Domain information for the customer."""
    business_domain_name: Optional[str] = None
    business_domain_info: Optional[str] = None
    business_optimization_problems: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "business_domain_name": self.business_domain_name,
            "business_domain_info": self.business_domain_info,
            "business_optimization_problems": self.business_optimization_problems
        }


@dataclass
class MLApproachInfo:
    """Machine learning approach information."""
    name: Optional[str] = None
    description: Optional[str] = None
    constraints: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "constraints": self.constraints
        }


@dataclass
class DatasetColumnInsight:
    """Insights about a dataset column."""
    column_name: str
    data_type: Optional[str] = None
    unique_values: Optional[int] = None
    missing_percentage: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean: Optional[float] = None
    median: Optional[float] = None
    mode: Optional[Any] = None
    std_dev: Optional[float] = None


@dataclass
class DatasetInsights:
    """General insights about the dataset."""
    total_row_count: Optional[int] = None
    column_insights: Dict[str, DatasetColumnInsight] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_row_count": self.total_row_count,
            "column_insights": {
                col: {
                    "data_type": insight.data_type,
                    "unique_values": insight.unique_values,
                    "missing_percentage": insight.missing_percentage,
                    "min_value": insight.min_value,
                    "max_value": insight.max_value,
                    "mean": insight.mean,
                    "median": insight.median,
                    "mode": insight.mode,
                    "std_dev": insight.std_dev
                }
                for col, insight in self.column_insights.items()
            }
        }


@dataclass
class AgentInputsResult:
    """Result of preparing agent inputs."""
    # Main data
    domain_info: DomainInfo = field(default_factory=DomainInfo)
    usecase_info: Dict[str, Any] = field(default_factory=dict)
    ml_approach: MLApproachInfo = field(default_factory=MLApproachInfo)
    required_columns: List[str] = field(default_factory=list)
    dataset_column_insights: Dict[str, Any] = field(default_factory=dict)
    dataset_insights: DatasetInsights = field(default_factory=DatasetInsights)
    
    # Tracking failed operations
    failed_operations: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain_info": self.domain_info.to_dict(),
            "usecase_info": self.usecase_info,
            "ml_approach": self.ml_approach.to_dict(),
            "required_columns": self.required_columns,
            "dataset_column_insights": self.dataset_column_insights,
            "dataset_insights": self.dataset_insights.to_dict(),
            "failed_operations": self.failed_operations
        }


class AgentInputsRequest(TypedDict, total=False):
    """Input parameters for prepare_agents_input function."""
    conn: Any  # Database connection
    # customer_id: str
    auth_service_base_url: str
    project_name: str
    schema: Optional[str] = None
    table_name: str
    mappings: Dict[str, Any]
    use_case: str
    ml_approach: str
    experiment_type: Optional[str] = None
    

@dataclass
class DataFrameInputsRequest:
    """Input parameters for prepare_agents_input function using DataFrame."""
    df: Any  # pandas DataFrame
    customer_id: str
    project_name: str
    mappings: Dict[str, Any]
    use_case: str
    ml_approach: str
    experiment_type: Optional[str] = None
    schema: Optional[str] = None  # Optional for compatibility


class TargetType(str, Enum):
    """Types of target variables."""
    BINARY = "binary"
    MULTICLASS = "multiclass"
    REGRESSION = "regression"
    TIME_SERIES = "time_series"
    MULTI_LABEL = "multi_label"

class SynthesisStrategy(str, Enum):
    """Strategies for target synthesis."""
    RULE_BASED = "rule_based"
    THRESHOLD_BASED = "threshold_based"
    CLUSTERING_BASED = "clustering_based"
    ML_BASED = "ml_based"
    HYBRID = "hybrid"


class TargetVariable(BaseModel):
    """Represents a synthesized target variable."""
    
    name: str = Field(..., description="Name of the target variable")
    target_type: TargetType = Field(..., description="Type of target variable")
    description: str = Field(..., description="Description of what the target represents")
    synthesis_strategy: SynthesisStrategy = Field(..., description="Strategy used for synthesis")
    source_columns: List[str] = Field(..., description="Source columns used for synthesis")
    transformation_logic: str = Field(..., description="Logic used to create the target")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in the synthesis")
    business_justification: str = Field(..., description="Business justification for the target")
    data_quality_metrics: Dict[str, Any] = Field(default_factory=dict, description="Quality metrics")
    validation_rules: List[str] = Field(default_factory=list, description="Validation rules")
    potential_issues: List[str] = Field(default_factory=list, description="Potential issues or risks")


class TargetSynthesisResult(BaseModel):
    """Complete result of target synthesis analysis."""
    
    dataset_name: str = Field(..., description="Name of the analyzed dataset")
    available_columns: List[str] = Field(..., description="All available columns in the dataset")
    synthesized_targets: List[TargetVariable] = Field(..., description="Generated target variables")
    recommended_target: TargetVariable = Field(..., description="Best recommended target variable")
    alternative_targets: List[TargetVariable] = Field(default_factory=list, description="Alternative options")
    synthesis_insights: List[str] = Field(default_factory=list, description="Key insights from synthesis")
    data_characteristics: Dict[str, Any] = Field(..., description="Dataset characteristics")
    business_context: Dict[str, Any] = Field(default_factory=dict, description="Business context analysis")
    implementation_plan: List[str] = Field(default_factory=list, description="Implementation steps")
    validation_approach: List[str] = Field(default_factory=list, description="Validation approach")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")
    timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")


class ColumnAnalysis(BaseModel):
    """Analysis of individual columns for target synthesis."""
    
    column_name: str = Field(..., description="Name of the column")
    data_type: str = Field(..., description="Data type of the column")
    unique_values: int = Field(..., description="Number of unique values")
    missing_percentage: float = Field(..., ge=0.0, le=1.0, description="Percentage of missing values")
    distribution_summary: Dict[str, Any] = Field(default_factory=dict, description="Distribution statistics")
    business_relevance: str = Field(..., description="Business relevance assessment")
    target_potential: str = Field(..., description="Potential as target variable")
    synthesis_complexity: str = Field(..., description="Complexity of synthesis")
    data_quality_score: float = Field(..., ge=0.0, le=1.0, description="Data quality score")


class BusinessContext(BaseModel):
    """Business context for target synthesis."""
    
    domain: str = Field(..., description="Business domain")
    problem_statement: str = Field(..., description="Problem to be solved")
    success_metrics: List[str] = Field(default_factory=list, description="Success metrics")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Business constraints")
    stakeholders: List[str] = Field(default_factory=list, description="Key stakeholders")
    timeline: str = Field(..., description="Project timeline")
    resources: Dict[str, Any] = Field(default_factory=dict, description="Available resources")
