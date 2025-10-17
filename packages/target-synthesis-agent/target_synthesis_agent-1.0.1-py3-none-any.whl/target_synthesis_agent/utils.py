"""
Utility functions for the Target Synthesis Agent.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import traceback
import pandas as pd
from dataclasses import asdict

from .models import (
    AgentInputsResult, DomainInfo, MLApproachInfo, 
    DatasetInsights, DatasetColumnInsight
)

logger = logging.getLogger(__name__)

def prepare_agents_input_by_sql(
    conn: Any,
    customer_id: str,
    auth_service_base_url: str,
    project_name: str,
    table_name: str,
    mappings: Dict[str, Any],
    use_case: str,
    ml_approach: str,
    experiment_type: Optional[str] = None,
    schema: Optional[str] = None
) -> AgentInputsResult:
    """
    Prepare inputs for agent operations by combining functionality from column checker
    and approach generator input preparation.
    
    Args:
        conn: Database connection object
        customer_id: ID of the customer
        auth_service_base_url: Base URL for authentication service
        project_name: Name of the project
        table_name: Name of the table to analyze
        mappings: Column mappings provided by the user
        use_case: Business use case name
        ml_approach: Selected ML approach
        experiment_type: Type of experiment (optional)
        schema: Database schema (optional)
        
    Returns:
        AgentInputsResult containing all prepared inputs and any failures
    """
    result = AgentInputsResult()
    
    try:
        # Clean and validate mappings
        cleaned_mappings = _clean_mappings(mappings)
        
        # Get domain and use case info
        result.domain_info, result.usecase_info = _get_domain_and_usecase_info(
            conn, customer_id, use_case, result
        )
        
        # Get ML approach info
        result.ml_approach = _get_ml_approach_info(ml_approach, result)
        
        # Get required columns
        result.required_columns = _get_required_columns(conn, project_name, result)
        
        # Get dataset insights
        dataset_insights = _get_dataset_insights(conn, project_name, table_name, result)
        if dataset_insights:
            result.dataset_insights = dataset_insights
        
        # Get column insights
        result.dataset_column_insights = _get_column_insights(
            conn, project_name, table_name, cleaned_mappings, 
            result.required_columns, result
        )
        
    except Exception as e:
        error_msg = f"Unexpected error in prepare_agents_input: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        result.failed_operations["prepare_agents_input"] = error_msg
    
    return result

def _clean_mappings(mappings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and validate the column mappings.
    
    Args:
        mappings: Raw column mappings
        
    Returns:
        Cleaned and validated mappings
    """
    cleaned = mappings.copy()
    keys_to_drop = ['primary_category', 'categories_present']
    
    try:
        # If mappings is a string, try to evaluate it
        if isinstance(mappings, str):
            try:
                import ast
                cleaned = ast.literal_eval(mappings)
                if not isinstance(cleaned, dict):
                    logger.warning(f"String evaluation resulted in {type(cleaned)}, not a dictionary")
                    cleaned = {}
            except (ValueError, SyntaxError) as e:
                logger.warning(f"Failed to convert string to dictionary: {e}")
                cleaned = {}
        
        # Remove unwanted keys
        for key in list(cleaned.keys()):
            if key.lower() in keys_to_drop:
                del cleaned[key]
                
    except Exception as e:
        logger.error(f"Error cleaning mappings: {str(e)}")
        logger.error(traceback.format_exc())
        cleaned = {}
        
    return cleaned

def _get_domain_and_usecase_info(
    conn: Any, 
    customer_id: str,
    use_case: str,
    result: AgentInputsResult
) -> Tuple[DomainInfo, Dict[str, Any]]:
    """
    Get domain and use case information.
    
    Args:
        conn: Database connection
        customer_id: ID of the customer
        use_case: Business use case name
        result: AgentInputsResult to track failures
        
    Returns:
        Tuple of (DomainInfo, usecase_info)
    """
    domain_info = DomainInfo()
    usecase_info = {}
    
    try:
        query = f"""
            SELECT name as domain_name, description, use_case_pack 
            FROM public.domains
            WHERE id IN (
                SELECT domain_id
                FROM public.customer_domain
                WHERE customer_id = {customer_id}
            )
            AND status = 'Completed';
        """
        
        domain_data = _fetch_data(conn, query, fetch="all", mappings=True)
        
        if domain_data:
            domain = domain_data[0]  # Single domain assumption
            domain_info.business_domain_name = domain.get("domain_name")
            domain_info.business_domain_info = domain.get("description")
            
            # Extract use case info
            if "use_case_pack" in domain and "use_case" in domain["use_case_pack"]:
                usecases = domain["use_case_pack"]["use_case"]
                domain_info.business_optimization_problems = {
                    uc["label"]: uc["labels"] for uc in usecases.values()
                }
                
                # Get specific use case info if available
                usecase_info = domain_info.business_optimization_problems.get(use_case, {})
                
    except Exception as e:
        error_msg = f"Failed to get domain and use case info: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        result.failed_operations["get_domain_and_usecase_info"] = error_msg
    
    return domain_info, usecase_info

def _get_ml_approach_info(ml_approach: str, result: AgentInputsResult) -> MLApproachInfo:
    """
    Get ML approach information.
    
    Args:
        ml_approach: Name of the ML approach
        result: AgentInputsResult to track failures
        
    Returns:
        MLApproachInfo object
    """
    approach_info = MLApproachInfo(name=ml_approach)
    
    try:
        # This is a placeholder - in a real implementation, you would fetch this from a config or database
        approach_info.description = f"ML approach: {ml_approach}"
        approach_info.constraints = [
            "Must maintain data integrity",
            "Should be compatible with the selected algorithm"
        ]
    except Exception as e:
        error_msg = f"Failed to get ML approach info: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        result.failed_operations["get_ml_approach_info"] = error_msg
    
    return approach_info

def _get_required_columns(
    conn: Any, 
    project_name: str, 
    result: AgentInputsResult
) -> List[str]:
    """
    Get list of required columns for the project.
    
    Args:
        conn: Database connection
        project_name: Name of the project
        result: AgentInputsResult to track failures
        
    Returns:
        List of required column names
    """
    required_columns = []
    
    try:
        query = f"""
            SELECT required_columns 
            FROM public.projects 
            WHERE name = '{project_name}';
        """
        
        project_data = _fetch_data(conn, query, fetch="one")
        if project_data and "required_columns" in project_data:
            required_columns = project_data["required_columns"]
            
    except Exception as e:
        error_msg = f"Failed to get required columns: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        result.failed_operations["get_required_columns"] = error_msg
    
    return required_columns

def _get_dataset_insights(
    conn: Any, 
    project_name: str, 
    table_name: str, 
    result: AgentInputsResult
) -> Optional[DatasetInsights]:
    """
    Get general insights about the dataset.
    
    Args:
        conn: Database connection
        project_name: Name of the project
        table_name: Name of the table
        result: AgentInputsResult to track failures
        
    Returns:
        DatasetInsights object or None if failed
    """
    insights = DatasetInsights()
    
    try:
        # Get row count
        count_query = f"SELECT COUNT(*) as count FROM {table_name};"
        count_data = _fetch_data(conn, count_query, fetch="one")
        if count_data and "count" in count_data:
            insights.total_row_count = count_data["count"]
            
        # Get column statistics
        # This is a simplified example - in a real implementation, you would gather more statistics
        column_query = f"DESCRIBE TABLE {table_name};"
        columns_data = _fetch_data(conn, column_query, fetch="all")
        
        if columns_data:
            for col in columns_data:
                col_name = col.get("name", "")
                if col_name:
                    col_insight = DatasetColumnInsight(column_name=col_name)
                    col_insight.data_type = col.get("type", "")
                    insights.column_insights[col_name] = col_insight
                    
    except Exception as e:
        error_msg = f"Failed to get dataset insights: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        result.failed_operations["get_dataset_insights"] = error_msg
        return None
    
    return insights

def _get_column_insights(
    conn: Any,
    project_name: str,
    table_name: str,
    mappings: Dict[str, Any],
    required_columns: List[str],
    result: AgentInputsResult
) -> Dict[str, Any]:
    """
    Get detailed insights about specific columns.
    
    Args:
        conn: Database connection
        project_name: Name of the project
        table_name: Name of the table
        mappings: Column mappings
        required_columns: List of required columns
        result: AgentInputsResult to track failures
        
    Returns:
        Dictionary of column insights
    """
    column_insights = {}
    
    try:
        # Get all columns to analyze (mapped columns + required columns)
        columns_to_analyze = list(set(list(mappings.values()) + required_columns))
        
        for col in columns_to_analyze:
            if not col:  # Skip empty column names
                continue
                
            try:
                # Basic column info
                col_query = f"""
                    SELECT 
                        COUNT(DISTINCT {col}) as unique_count,
                        COUNT(CASE WHEN {col} IS NULL THEN 1 END) as null_count,
                        COUNT(*) as total_count,
                        MIN({col}) as min_value,
                        MAX({col}) as max_value,
                        AVG(TRY_CAST({col} AS FLOAT)) as avg_value
                    FROM {table_name};
                """
                
                col_data = _fetch_data(conn, col_query, fetch="one")
                
                if col_data:
                    col_insight = {
                        "unique_count": col_data.get("unique_count"),
                        "null_count": col_data.get("null_count"),
                        "total_count": col_data.get("total_count"),
                        "null_percentage": (col_data.get("null_count", 0) / 
                                          (col_data.get("total_count", 1) or 1)) * 100,
                        "min_value": col_data.get("min_value"),
                        "max_value": col_data.get("max_value"),
                        "avg_value": col_data.get("avg_value")
                    }
                    column_insights[col] = col_insight
                    
            except Exception as col_error:
                error_msg = f"Error analyzing column {col}: {str(col_error)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                result.failed_operations[f"analyze_column_{col}"] = error_msg
                
    except Exception as e:
        error_msg = f"Failed to get column insights: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        result.failed_operations["get_column_insights"] = error_msg
    
    return column_insights

def _fetch_data(conn, query: str, fetch: str = "all", **kwargs):
    """
    Helper function to fetch data from the database.
    
    Args:
        conn: Database connection
        query: SQL query to execute
        fetch: 'all' to fetch all rows, 'one' to fetch one row
        **kwargs: Additional arguments for the fetch method
        
    Returns:
        Query result as a dictionary or list of dictionaries
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        
        if fetch.lower() == "all":
            columns = [col[0] for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            if "mappings" in kwargs and kwargs["mappings"]:
                # For compatibility with existing code expecting mappings
                return [dict(zip(columns, row)) for row in rows]
            return rows
            
        elif fetch.lower() == "one":
            row = cursor.fetchone()
            if row and cursor.description:
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
            return row
            
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        logger.error(traceback.format_exc())
        raise
    finally:
        cursor.close()

#========================================================
# utils for dealing with dataframe as input
#========================================================
def prepare_agents_input_by_df(
    df: Any,
    customer_id: str,
    project_name: str,
    mappings: Dict[str, Any],
    use_case: str,
    ml_approach: str,
    experiment_type: Optional[str] = None
) -> AgentInputsResult:
    """
    Prepare inputs for agent operations using a DataFrame instead of SQL.
    
    Args:
        df: Input pandas DataFrame
        customer_id: ID of the customer
        project_name: Name of the project
        mappings: Column mappings provided by the user
        use_case: Business use case name
        ml_approach: ML approach to use
        experiment_type: Type of experiment (optional)
        
    Returns:
        AgentInputsResult with prepared inputs
    """
    result = AgentInputsResult()
    
    try:
        # Clean and validate mappings
        mappings = _clean_mappings(mappings)
        
        # Get domain and use case info (without DB)
        domain_info, usecase_info = _get_domain_and_usecase_info_df(
            customer_id, use_case, result
        )
        result.domain_info = domain_info
        result.usecase_info = usecase_info
        
        # Get ML approach info
        result.ml_approach = _get_ml_approach_info(ml_approach, result)
        
        # Get required columns (from mappings)
        result.required_columns = list(mappings.keys())
        
        # Get dataset insights from DataFrame
        result.dataset_insights = _get_dataset_insights_df(df, result)
        
        # Get column insights
        result.dataset_column_insights = _get_column_insights_df(
            df, mappings, result.required_columns, result
        )
        
    except Exception as e:
        error_msg = f"Error in prepare_agents_input_by_df: {str(e)}"
        result.failed_operations["prepare_agents_input"] = error_msg
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
    
    return result

def _get_dataset_insights_df(
    df: Any, 
    result: AgentInputsResult
) -> DatasetInsights:
    """
    Get dataset insights from a pandas DataFrame.
    
    Args:
        df: Input DataFrame
        result: AgentInputsResult to track failures
        
    Returns:
        DatasetInsights object
    """
    insights = DatasetInsights()
    
    try:
        insights.total_row_count = len(df)
        insights.column_insights = {}
        
        for col in df.columns:
            col_insight = DatasetColumnInsight(column_name=col)
            try:
                col_insight.data_type = str(df[col].dtype)
                col_insight.unique_values = df[col].nunique()
                col_insight.missing_percentage = df[col].isna().mean() * 100
                
                if pd.api.types.is_numeric_dtype(df[col]):
                    col_insight.min_value = float(df[col].min())
                    col_insight.max_value = float(df[col].max())
                    col_insight.mean = float(df[col].mean())
                    col_insight.median = float(df[col].median())
                    col_insight.std_dev = float(df[col].std())
                
                insights.column_insights[col] = col_insight
                
            except Exception as e:
                error_msg = f"Error analyzing column {col}: {str(e)}"
                result.failed_operations[f"analyze_column_{col}"] = error_msg
                logger.warning(f"{error_msg}\n{traceback.format_exc()}")
                
    except Exception as e:
        error_msg = f"Error getting dataset insights: {str(e)}"
        result.failed_operations["get_dataset_insights"] = error_msg
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
    
    return insights

def _get_domain_and_usecase_info_df(
    customer_id: str,
    use_case: str,
    result: AgentInputsResult
) -> Tuple[DomainInfo, Dict[str, Any]]:
    """
    Get domain and use case info without DB access.
    """
    domain_info = DomainInfo(
        business_domain_name="Default Domain",
        business_domain_info="Domain information not available in DataFrame mode"
    )
    
    usecase_info = {
        "name": use_case,
        "description": f"Use case: {use_case} (running in DataFrame mode)"
    }
    
    return domain_info, usecase_info

def _get_column_insights_df(
    df: Any,
    mappings: Dict[str, Any],
    required_columns: List[str],
    result: AgentInputsResult
) -> Dict[str, Any]:
    """
    Get column insights from DataFrame.
    """
    insights = {}
    
    for col in required_columns:
        if col not in df.columns:
            result.failed_operations[f"column_not_found_{col}"] = f"Column {col} not found in DataFrame"
            continue
            
        col_insight = {
            "mapped_to": mappings.get(col, col),
            "present": True,
            "data_type": str(df[col].dtype),
            "sample_values": df[col].dropna().head(5).tolist()
        }
        insights[col] = col_insight
    
    return insights