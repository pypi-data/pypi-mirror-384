"""
Prompt Constants for TargetSynthesisAgent

This file contains all prompts used by the TargetSynthesisAgent.
All prompts are centralized here for easy review and maintenance.

Prompt Types:
- PROMPT_TEMPLATE_*: Templates for dynamic content formatting
- SYSTEM_PROMPT_*: Role definitions and system instructions
"""

from typing import Optional, Dict, List, Any

# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

PROMPT_TEMPLATE_BUSINESS_CONTEXT_ANALYSIS = """
    Analyze the following business context and data characteristics to understand target synthesis requirements.

    Business Context: {business_context}

    Data Characteristics:
    - Shape: {data_characteristics_shape}
    - Columns: {data_characteristics_columns}
    - Data Types: {data_characteristics_data_types}
    - Missing Values: {data_characteristics_missing_values}

    Provide business analysis in JSON format:
    {{
        "domain": "business domain",
        "problem_statement": "clear problem description",
        "success_metrics": ["metric1", "metric2"],
        "constraints": {{"constraint1": "description"}},
        "stakeholders": ["stakeholder1", "stakeholder2"],
        "timeline": "project timeline",
        "resources": {{"resource1": "description"}}
    }}
    """

PROMPT_TEMPLATE_TARGET_VARIABLE_GENERATION = """
    Generate target variables for the following dataset and business context.

    Dataset Info:
    - Shape: {data_characteristics_shape}
    - Columns: {data_characteristics_columns}
    - Data Types: {data_characteristics_data_types}
    - Missing Values: {data_characteristics_missing_values}
    - Correlations: {data_characteristics_correlations}

    Business Context:
    - Domain: {business_analysis_domain}
    - Problem: {business_analysis_problem}
    - Success Metrics: {business_analysis_success_metrics}
    - Constraints: {constraints}

    Target Requirements: {target_requirements}

    Generate {max_targets} target variables with:
    1. Target name and type
    2. Description and business justification
    3. Synthesis strategy
    4. Source columns and transformation logic
    5. Confidence score
    6. Data quality metrics
    7. Validation rules
    8. Potential issues

    Respond with valid JSON:
    {{
        "targets": [
            {{
                "name": "target_name",
                "target_type": "binary|multiclass|regression|time_series|multi_label",
                "description": "Description",
                "synthesis_strategy": "rule_based|threshold_based|clustering_based|ml_based|hybrid",
                "source_columns": ["col1", "col2"],
                "transformation_logic": "Logic description",
                "confidence_score": 0.85,
                "business_justification": "Business reason",
                "data_quality_metrics": {{"metric": "value"}},
                "validation_rules": ["rule1", "rule2"],
                "potential_issues": ["issue1", "issue2"]
            }}
        ]
    }}
    """



# =============================================================================
# PROMPT FORMATTING FUNCTIONS
# =============================================================================

def format_business_context_analysis_prompt(
    business_context: dict,
    data_characteristics: dict
) -> str:
    """
    Format the business context analysis prompt with dynamic content.
    
    Args:
        business_context: Business context dictionary
        data_characteristics: Data characteristics dictionary
        
    Returns:
        Formatted prompt string
    """
    return PROMPT_TEMPLATE_BUSINESS_CONTEXT_ANALYSIS.format(
        business_context=business_context,
        data_characteristics_shape=data_characteristics.get('shape', ''),
        data_characteristics_columns=list(data_characteristics.get('data_types', {}).keys()),
        data_characteristics_data_types=data_characteristics.get('data_types', {}),
        data_characteristics_missing_values=data_characteristics.get('missing_values', {})
    )


def format_target_variable_generation_prompt(
    data_characteristics: dict,
    business_analysis: dict,
    constraints: dict,
    target_requirements: dict,
    max_targets: int
) -> str:
    """
    Format the target variable generation prompt with dynamic content.
    
    Args:
        data_characteristics: Data characteristics dictionary
        business_analysis: Business analysis dictionary
        constraints: Constraints dictionary
        target_requirements: Target requirements dictionary
        max_targets: Maximum number of targets to generate
        
    Returns:
        Formatted prompt string
    """
    return PROMPT_TEMPLATE_TARGET_VARIABLE_GENERATION.format(
        data_characteristics_shape=data_characteristics.get('shape', ''),
        data_characteristics_columns=list(data_characteristics.get('data_types', {}).keys()),
        data_characteristics_data_types=data_characteristics.get('data_types', {}),
        data_characteristics_missing_values=data_characteristics.get('missing_values', {}),
        data_characteristics_correlations=data_characteristics.get('correlation_matrix', {}),
        business_analysis_domain=business_analysis.get('domain', 'general'),
        business_analysis_problem=business_analysis.get('problem_statement', 'Target synthesis'),
        business_analysis_success_metrics=business_analysis.get('success_metrics', []),
        constraints=constraints,
        target_requirements=target_requirements,
        max_targets=max_targets
    )


# =============================================================================
# SYSTEM PROMPTS TEMPLATE
# =============================================================================

SYSTEM_PROMPT_COLUMN_CHECKER = """
    You are an expert data analyst and business domain specialist. Your role is to analyze business optimization problems and identify the required dataset columns needed to implement specific business logic.

    Your responsibilities include:
    1. Understanding the business optimization problem and its context
    2. Identifying all necessary dataset columns required to implement the given problem definition
    3. Ensuring only existing columns from the dataset are suggested
    4. Providing clear, concise output in the specified JSON format

    Output must be valid JSON with the following structure:
    {
        "message": "<brief explanation of identified columns>",
        "required_columns": ["list", "of", "required", "columns"]
    }
    """

SYSTEM_PROMPT_APPROACH_GENERATOR = """
    You are a highly skilled data scientist and SQL expert with deep knowledge of business domains, optimization problems, and machine learning target preparation.  

    Your role:  
    - Read the provided context (target definition, mapped columns, required columns, dataset insights, and ML approach).  
    - Understand how the business defines the target and translate it into both a strategy explanation and executable SQL.    
    - Ensure the SQL query satisfies approach-specific constraints. 
    - Ensure the created table has all mapped columns (without alias), required columns along with target column named as TARGET. 

    Provide outputs strictly in the following JSON format:
    {
        "target_logic": "<short strategy of how target is defined for each customer/month>",
        "sql_logic_explanation": "<plain English explanation of how the SQL query implements target definition>",
        "create_table_query": "<executable CREATE TABLE AS SELECT query using the provided schema and table name>",
        "confidence_score": <float between 0 and 1>
    }

    Be concise, accurate, and ensure outputs are self-contained and executable.
    """

SYSTEM_PROMPT_SQL_REFACTOR = """
    You are a SQL expert. Refactor SQL queries to fix errors, but do NOT change the logic, columns, or tables.
    Only adjust datatype casts, value formats, or other syntax/formatting issues as required by the error.
    Return only the corrected, executable SQL query, no explanation.
    """

# =============================================================================
# USER PROMPT TEMPLATES
# =============================================================================

USER_PROMPT_COLUMN_CHECKER = """
    You are analyzing a {use_case} definition based on the available dataset columns.
    {use_case} Description: {usecase_description}

    * User's Definition of {use_case} (which is business optimization problem): 
    {definition}

    * Business Domain Info (business domain info for the customer's domain): 
    {domain_info}

    * ML Approach (user decided way to model the problem using machine learning): 
    {ml_approach}

    * User Response for mappings (user mapped identifier fields in dataset): 
    {mapping_response}

    * Dataset Insights (insights about the dataset columns): 
    {dataset_insights}

    Your task:
    1. Analyse the given inputs looking at given business optimization problem, its description, and user's definition of the problem.
    2. Identify the dataset columns required to implement the {use_case} definition. 
    3. Only suggest columns that actually exist in the dataset.
    4. Only return the JSON. Do not add extra explanation or commentary.

    ** Example 1:
    Business Domain : SaaS
    Problem Definition : For a customer, if count of active devices for any month tends to 0, mark that customer as Inactive.
    Mappings - ['account_id', 'usage_month']
    dataset columns - ['revenue', 'devices_in_use', 'logging_days', 'usage_in_hrs', 'pages_visited']
    {{
    "message": "Identified columns account_id, usage_month, devices_in_use as active_devices. Please verify and confirm.",
    "required_columns": ['account_id', 'usage_month', 'devices_in_use']
    }}

    ** Example 2:
    Business Domain : Automotive warranty
    Problem Definition : If a customer submits more than 2 warranty claims for the same vehicle part within a short period (e.g., 3 months), flag it as "Potential Warranty Fraud".
    Mappings: ['customer_id', 'vehicle_id', 'claim_date', 'part_id']
    Dataset Columns: ['customer_id', 'vehicle_id', 'claim_id', 'claim_date', 'part_id', 'part_category', 'claim_amount', 'repair_cost', 'service_center_id', 'mileage_at_claim', 'warranty_status']
    {{
    "message": "Identified columns customer_id, vehicle_id, claim_date, part_id for given Warranty Fraud usecase. Please verify and confirm.",
    "required_columns": ['customer_id', 'vehicle_id', 'claim_date', 'part_id']
    }}
    """

USER_PROMPT_APPROACH_GENERATOR = """
    Below is the context and requirements for preparing the ML target table.

        1. User Definition of Target:
        {definition}

        2. User Mapped Columns:
        {mapped_columns}

        3. Business Domain and description:
        {domain_info}

        4. Business Optimization Problem and Description:
        {usecase_info}

        5. ML Approach Selected and target constraints:
        {ml_approach}

        6. Required Columns and Insights:
        {required_columns_list}

        7. Dataset Column Insights:
        {dataset_column_insights}

        8. Dataset Insights (row counts, etc.):
        {dataset_insights}

        9. source and target table details:
        {db_schema_table_details}
    
    ---
    Now, based on the above, generate the JSON output with the following keys:
    1. "target_logic"  
    2. "sql_logic_explanation"  
    3. "create_table_query"  
    4. "confidence_score"
    """

USER_PROMPT_SQL_REFACTOR = """
    SQL Logic: {sql_logic}
    ML Target Constraints: {ml_target_constraints}
    Dataset Columns Info: {dataset_columns_info}
    Previous Execution History: {execution_history}
    Query:
    {executed_query}
    Error:
    {error}
    """

# =============================================================================
# PROMPT FORMATTING FUNCTIONS
# =============================================================================

def format_system_prompt_column_checker() -> str:
    """
    Returns the system prompt for the column checker tool.
    """
    return SYSTEM_PROMPT_COLUMN_CHECKER

def format_user_prompt_column_checker(
    use_case: str,
    usecase_description: str,
    definition: str,
    domain_info: dict[str, any],
    ml_approach: str,
    mapping_response: dict[str, str],
    dataset_insights: dict[str, any]
) -> str:
    """
    Format the column checker user prompt with dynamic content.
    
    Args:
        use_case: The business use case name
        usecase_description: Description of the use case
        definition: User's definition of the target
        domain_info: Business domain information
        ml_approach: Selected ML approach
        mapping_response: User's column mappings
        dataset_insights: Insights about the dataset columns
        
    Returns:
        Formatted prompt string
    """
    return USER_PROMPT_COLUMN_CHECKER.format(
        use_case=use_case,
        usecase_description=usecase_description,
        definition=definition,
        domain_info=domain_info,
        ml_approach=ml_approach,
        mapping_response=mapping_response,
        dataset_insights=dataset_insights
    )

def format_system_prompt_approach_generator() -> str:
    """
    Returns the system prompt for the approach generator tool.
    """
    return SYSTEM_PROMPT_APPROACH_GENERATOR

def format_user_prompt_approach_generator(
    definition: str,
    mapped_columns: list[str],
    domain_info: dict[str, any],
    usecase_info: dict[str, str],
    ml_approach: str,
    required_columns_list: list[str],
    dataset_column_insights: dict[str, any],
    dataset_insights: dict[str, any],
    db_schema_table_details: dict[str, str]
) -> str:
    """
    Format the approach generator user prompt with dynamic content.
    
    Args:
        definition: User definition of the target
        mapped_columns: List of mapped columns
        domain_info: Business domain information
        usecase_info: Business optimization problem info
        ml_approach: Selected ML approach
        required_columns_list: List of required columns
        dataset_column_insights: Insights about dataset columns
        dataset_insights: General dataset insights
        db_schema_table_details: Database schema and table details
        
    Returns:
        Formatted prompt string
    """
    return USER_PROMPT_APPROACH_GENERATOR.format(
        definition=definition,
        mapped_columns=mapped_columns,
        domain_info=domain_info,
        usecase_info=usecase_info,
        ml_approach=ml_approach,
        required_columns_list=required_columns_list,
        dataset_column_insights=dataset_column_insights,
        dataset_insights=dataset_insights,
        db_schema_table_details=db_schema_table_details
    )

def format_system_prompt_sql_refactor() -> str:
    """
    Returns the system prompt for the SQL refactoring tool.
    """
    return SYSTEM_PROMPT_SQL_REFACTOR

def format_user_prompt_sql_refactor(
    sql_logic: str,
    ml_target_constraints: str,
    dataset_columns_info: dict[str, any],
    execution_history: Optional[list[dict[str, any]]],
    executed_query: str,
    error: str
) -> str:
    """
    Format the SQL refactoring user prompt with dynamic content.
    
    Args:
        sql_logic: Description of the SQL logic
        ml_target_constraints: Constraints for ML target
        dataset_columns_info: Information about dataset columns
        execution_history: History of previous execution attempts
        executed_query: The SQL query that failed
        error: Error message from the failed execution
        
    Returns:
        Formatted prompt string
    """
    return USER_PROMPT_SQL_REFACTOR.format(
        sql_logic=sql_logic,
        ml_target_constraints=ml_target_constraints,
        dataset_columns_info=dataset_columns_info,
        execution_history=execution_history or [],
        executed_query=executed_query,
        error=error
    )
