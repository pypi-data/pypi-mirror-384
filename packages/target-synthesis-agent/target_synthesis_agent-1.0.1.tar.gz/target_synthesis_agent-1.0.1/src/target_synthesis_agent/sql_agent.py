"""
Target Synthesis Agent - Integrated approach for target variable creation and validation.

This agent combines column checking, approach generation, and SQL execution
in a streamlined pipeline for target variable synthesis using sfn_blueprint patterns.
"""

import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Import sfn_blueprint components
from sfn_blueprint import (
    SFNAIHandler,
    SFNConfigManager,
    setup_logger,
    Task,
    WorkflowStorageManager,
    SFNDataLoader,
    SFNDataPostProcessor
)
from sfn_blueprint.utils.context_utils import (
    extract_context_info,
    get_context_recommendations,
    validate_context,
    log_context_usage
)

# Import from local modules
from target_synthesis_agent.models import (
    AgentInputsRequest,
    AgentInputsResult,
    DomainInfo,
    MLApproachInfo,
    DatasetInsights,
    DatasetColumnInsight
)
from target_synthesis_agent.config import TargetSynthesisConfig
from target_synthesis_agent.constants import (
    format_system_prompt_column_checker,
    format_user_prompt_column_checker,
    format_system_prompt_approach_generator,
    format_user_prompt_approach_generator,
    format_system_prompt_sql_refactor,
    format_user_prompt_sql_refactor
)

# Constants
DEFAULT_CONFIG = {
    "model": "gpt-4.1-mini",
    "temperature": 0.2,
    "max_retries": 3,
    "timeout": 300,
    "max_tokens": 4000
}


class TargetSynthesisAgent:
    """
    Integrated agent for target synthesis with column checking, approach generation,
    and SQL execution capabilities using sfn_blueprint patterns.
    """
    
    def __init__(self, config: Optional[TargetSynthesisConfig] = None):
        """
        Initialize the agent with configuration.
        
        Args:
            config: Optional TargetSynthesisConfig instance. If not provided, a default will be used.
        """
        # Initialize configuration
        self.config = config or TargetSynthesisConfig()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:  # Only add handlers if none exist
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Initialize sfn_blueprint components
        self.ai_handler = SFNAIHandler()
        self.config_manager = SFNConfigManager()
        
        # Initialize workflow storage with default paths
        workflow_base_path = "workflows"  # Default workflow storage directory
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"  # Generate a unique workflow ID
        
        # Create the workflow directory if it doesn't exist
        os.makedirs(workflow_base_path, exist_ok=True)
        
        self.workflow_storage = WorkflowStorageManager(
            workflow_base_path=workflow_base_path,
            workflow_id=workflow_id
        )
        
        self.data_loader = SFNDataLoader()
        # self.data_processor = SFNDataPostProcessor()
        
        # Load configuration from sfn_blueprint config manager
        self._load_config()
        
        # Initialize execution tracking
        self.execution_history: List[Dict[str, Any]] = []
        self.current_task: Optional[Task] = None
    
    def _load_config(self) -> None:
        """Load configuration from sfn_blueprint config manager."""
        # Ensure logger is properly initialized
        if not hasattr(self, 'logger') or not isinstance(self.logger, logging.Logger):
            self.logger = logging.getLogger(__name__)
            
        # Set default config
        self.llm_config = DEFAULT_CONFIG.copy()
        
        try:
            # Try to get config from config manager if available
            if hasattr(self.config_manager, 'config'):
                # Access config as a dictionary if available
                model_config = self.config_manager.config.get('model_config', {})
                if model_config:
                    self.llm_config.update(model_config)
                    self.logger.info("Updated configuration with model-specific settings")
            
            self.logger.info(f"Using configuration: {self.llm_config}")
            
        except Exception as e:
            # Make sure we have a logger before trying to log
            if hasattr(self, 'logger') and isinstance(self.logger, logging.Logger):
                self.logger.warning(f"Could not load external config: {e}")
            # Fall back to default config
            self.llm_config = DEFAULT_CONFIG
    
    async def check_columns(
        self,
        request: AgentInputsRequest,
        definition: str,
        mapping_response: Dict[str, Any],
        task_id: Optional[str] = None,
        required_columns: List[str] = None
    ) -> Dict[str, Any]:
        """
        Check if the provided columns meet the requirements for the target definition.
        
        Args:
            request: Agent input request containing connection and context
            definition: Definition of the target variable
            mapping_response: Dictionary mapping logical names to physical columns
            task_id: Optional task ID for workflow tracking
            
        Returns:
            Dictionary with analysis results including required columns and messages
        """
        print("\n\n *** Request received in check_columns.", request,type(request))
        # Create or update task
        self.current_task = Task(
            description=f"Column analysis for target definition: {definition[:100]}...",
            task_type="column_analysis",
            category="data_validation",
            data={
                "definition": definition,
                "mapping_response": mapping_response,
                "task_id": task_id or f"col_check_{hash(str((definition, json.dumps(mapping_response))))}"
            }
        )
        
        try:
            
            # Format prompts using sfn_blueprint patterns
            system_prompt = format_system_prompt_column_checker()
            # print("\n\n *** System prompt in column check:", system_prompt)
            user_prompt = format_user_prompt_column_checker(
                use_case=request.get("use_case"),
                usecase_description=definition,
                definition=definition,
                domain_info={"name": request.get("project_name")},
                ml_approach=request.get("ml_approach"),
                mapping_response=mapping_response,
                dataset_insights=request.get("dataset_insights", {})            )
            # print("\n\n *** User prompt in column check:", user_prompt)            
            # Log the task details
            self.current_task.metadata = {
                "use_case": request.get("use_case"),
                "definition": definition,
                "mapping_response": mapping_response
            }
            # print("\n\n *** Task metadata in column check:", self.current_task.metadata)
            if required_columns is None:

                # Get LLM response using sfn_blueprint handler
                response = self.ai_handler.route_to(
                    llm_provider=self.config.ai_provider,
                    configuration={
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "model": self.config.model_name,
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                        "api_key": self.config.api_key
                    },
                    model=self.llm_config["model"]
                )
            
                # Process response using sfn_blueprint formatter
                formatted_response = self._process_llm_response(response[0])
            
            # Update task status and store results
            self.current_task.status = "completed"
            self.current_task.result = {
                "status": "success",
                "required_columns": formatted_response.get("required_columns", []),
                "message": formatted_response.get("message", ""),
                "analysis": formatted_response
            }

            # Log successful completion
            # log_context_usage(context_info, "column_check_success", self.current_task.result)
            # print("\n\n *** Task result in column check:", self.current_task.result)
            return self.current_task.result
            
        except Exception as e:
            error_msg = f"Error in check_columns: {str(e)}"
            self.logger.error(f"{error_msg}\n{traceback.format_exc()}")
            
            # Update task with error
            if self.current_task:
                self.current_task.status = "failed"
                self.current_task.error = error_msg
                # log_context_usage(context_info, "column_check_error", {"error": error_msg})
            
            return {
                "status": "error",
                "message": error_msg
            }
    
    async def generate_approach(
        self,
        request: AgentInputsRequest,
        definition: str,
        mapped_columns: List[str],
        dataset_insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate an approach for creating the target variable.
        
        Args:
            request: Agent input request
            definition: Definition of the target variable
            mapped_columns: List of mapped column names
            dataset_insights: Insights about the dataset
            
        Returns:
            Dictionary with the generated approach details
        """
        try:
            # Format prompts
            system_prompt = format_system_prompt_approach_generator()
            user_prompt = format_user_prompt_approach_generator(
                definition=definition,
                mapped_columns=mapped_columns,
                domain_info={"name": request.get("project_name")},
                usecase_info={"use_case": request.get("use_case")},
                ml_approach=request.get("ml_approach"),
                required_columns_list=mapped_columns,
                dataset_column_insights=dataset_insights.get("columns", {}),
                dataset_insights=dataset_insights,
                db_schema_table_details={
                    "schema": request.get("schema"),
                    "table": f"{request.get('use_case', '')}_target"
                }
            )

            approach_response = self.ai_handler.route_to(
                llm_provider=self.config.ai_provider,
                configuration={
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "model": self.config.model_name,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    "api_key": self.config.api_key
                },
                model=self.config.model_name
            )
            
            if not isinstance(approach_response, dict):
                approach_response = json.loads(approach_response[0])

            # Parse response (assuming it's in JSON format)
            try:
                return {
                    "status": "success",
                    "target_logic": approach_response.get("target_logic", ""),
                    "sql_logic": approach_response.get("sql_logic_explanation", ""),
                    "create_table_query": approach_response.get("create_table_query", ""),
                    "confidence_score": approach_response.get("confidence_score", 0.0)
                }
            except Exception as e:
                traceback.print_exc()
                self.logger.error(f"Failed to parse approach generator response: {e}")
                return {
                    "status": "error",
                    "message": f"Failed to parse approach generator response: {e}"
                }
                
        except Exception as e:
            self.logger.error(f"Error in generate_approach: {str(e)}\n{traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Error in approach generation: {str(e)}"
            }
    
    async def execute_sql(
        self,
        conn: Any,
        target_logic: str,
        sql_logic: str,
        ml_target_constraints: str,
        dataset_columns_info: Dict[str, Any],
        input_query: str,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Execute SQL with retry logic and error handling.
        
        Args:
            conn: Database connection
            target_logic: Description of the target logic
            sql_logic: SQL logic to execute
            ml_target_constraints: ML target constraints
            dataset_columns_info: Information about dataset columns
            input_query: The SQL query to execute
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with execution results
        """
        from sqlalchemy import text
        
        print("\n\n *** input query in execute_sql:", input_query, type(input_query))
        execution_details = {}
        execution_history = []
        last_query = input_query
        
        for attempt in range(1, max_retries + 1):
            self.logger.info(f"Execution attempt {attempt}/{max_retries}")
            
            try:
                # Execute the query using SQLAlchemy text() for raw SQL
                result = conn.execute(text(last_query))
                conn.commit()
                
                # Get the result if it's a SELECT query
                if result.returns_rows:
                    rows = result.fetchall()
                    status = f"Successfully retrieved {len(rows)} rows"
                else:
                    status = "Query executed successfully"
                
                print("\n\n *** SQL execution status:", status)
                
                execution_details[f"attempt{attempt}"] = {
                    "query": last_query,
                    "success_status": True,
                    "status": status,
                    "error": None,
                }
                
                self.logger.info("SQL execution successful")
                return {
                    "status": "success",
                    "target_logic": target_logic,
                    "sql_query_logic": sql_logic,
                    "execution_details": execution_details,
                    "result": status
                }

                
            except Exception as e:
                print("\n\n *** Error in execute_sql:\n", traceback.format_exc()[:1000])
                error_msg = str(e)
                if len(error_msg) > 400:
                    error_msg = error_msg[:400] + "..."
                
                execution_details[f"attempt{attempt}"] = {
                    "query": last_query,
                    "success_status": False,
                    "error": error_msg,
                }
                
                execution_history.append({
                    "query": last_query,
                    "error": error_msg
                })
                
                # If we have retries left, try to fix the query
                if attempt < max_retries:
                    try:
                        system_prompt = format_system_prompt_sql_refactor()
                        user_prompt = format_user_prompt_sql_refactor(
                            sql_logic=sql_logic,
                            ml_target_constraints=ml_target_constraints,
                            dataset_columns_info=dataset_columns_info,
                            execution_history=execution_history,
                            executed_query=last_query,
                            error=error_msg
                        )
                        
                        response = self.ai_handler.route_to(
                            llm_provider=self.config.ai_provider,
                            configuration={
                                "messages": [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt}
                                ],
                                "model": self.config.model_name,
                                "temperature": self.config.temperature,
                                "max_tokens": self.config.max_tokens,
                                "api_key": self.config.api_key
                            },
                            model=self.config.model_name
                        )
                        
                        # Extract the fixed query from the response
                        # This assumes the response is in a specific format
                        last_query = self._extract_sql_from_response(response)
                        
                    except Exception as fix_error:
                        self.logger.error(f"Error fixing query: {fix_error}")
                        continue
                
                self.logger.error(f"SQL execution failed on attempt {attempt}: {error_msg}")
        
        # If we get here, all retries failed
        return {
            "status": "error",
            "message": f"Failed to execute SQL after {max_retries} attempts",
            "execution_details": execution_details
        }
    
    async def execute_pipeline(
        self,
        request: AgentInputsRequest,
        definition: str,
        mapping_response: Dict[str, Any],
        required_columns: List[str]
    ) -> Dict[str, Any]:
        """
        Execute the complete target synthesis pipeline using sfn_blueprint workflow patterns.
        
        Args:
            request: Agent input request
            definition: Definition of the target variable
            mapping_response: Dictionary mapping logical names to physical columns
            
        Returns:
            Dictionary with results from all pipeline steps
        """
        # Create a workflow context
        workflow_id = f"target_synth_{hash(str((definition, json.dumps(mapping_response))))}"
        workflow_ctx = {
            "workflow_id": workflow_id,
            "status": "started",
            "steps": {}
        }
        
        try:
            # Store workflow context as a step result
            self.workflow_storage.save_step_result(
                step_id=f"{workflow_id}_init",
                data=workflow_ctx,
                step_type="workflow_init",
                metadata={"workflow_id": workflow_id, "status": "started"}
            )
            
            # Step 1: Column checking
            self.logger.info("Starting column checking...")
            column_check_result = await self.check_columns(
                request=request,
                definition=definition,
                mapping_response=mapping_response,
                task_id=f"{workflow_id}_col_check",
                required_columns = required_columns
            )
            print("\n\n *** Column check result:", column_check_result)
            
            # Update workflow context
            workflow_ctx["steps"]["column_check"] = {
                "status": column_check_result.get("status"),
                "result": column_check_result
            }
            workflow_ctx["status"] = "in_progress"
            
            # Save the updated workflow context
            self.workflow_storage.save_step_result(
                step_id=f"{workflow_id}_after_col_check",
                data=workflow_ctx,
                step_type="workflow_update",
                metadata={"workflow_id": workflow_id, "status": "in_progress"}
            )
            
            if column_check_result.get("status") != "success":
                workflow_ctx["status"] = "failed"
                workflow_ctx["error"] = "Column check failed"
                # self.workflow_storage.update_workflow(workflow_id, workflow_ctx)
                
                return {
                    "status": "error",
                    "workflow_id": workflow_id,
                    "step": "column_check",
                    "details": column_check_result
                }
            
            # Step 2: Generate approach
            self.logger.info("Generating approach...")
            print('\n\n *** request in generate approach:',request, type(request))
            dataset_insights = request.get("dataset_insights", {})
            # print("\n\n *** Dataset insights:\n", dataset_insights)
            
            approach_result = await self.generate_approach(
                request=request,
                definition=definition,
                mapped_columns=column_check_result.get("required_columns", []),
                dataset_insights=dataset_insights,
                # task_id=f"{workflow_id}_approach_gen"
            )
            
            # Update workflow context
            workflow_ctx["steps"]["approach_generation"] = {
                "status": approach_result.get("status"),
                "result": approach_result
            }
            # self.workflow_storage.update_workflow(workflow_id, workflow_ctx)
            self.workflow_storage.save_step_result(
                step_id=f"{workflow_id}_after_approach_gen",
                data=workflow_ctx,
                step_type="workflow_update",
                metadata={"workflow_id": workflow_id, "status": "in_progress"}
            )
            
            if approach_result.get("status") != "success":
                workflow_ctx["status"] = "failed"
                workflow_ctx["error"] = "Approach generation failed"
                self.workflow_storage.save_step_result(
                    step_id=f"{workflow_id}_after_approach_gen",
                    data=workflow_ctx,
                    step_type="workflow_update",
                    metadata={"workflow_id": workflow_id, "status": "in_progress"}
                )
                
                return {
                    "status": "error",
                    "workflow_id": workflow_id,
                    "step": "approach_generation",
                    "details": approach_result
                }
            
            # Step 3: Execute SQL
            self.logger.info("Executing SQL...")
            sql_result = await self.execute_sql(
                conn=request.get("conn", None),
                target_logic=approach_result.get("target_logic", ""),
                sql_logic=approach_result.get("sql_logic", ""),
                ml_target_constraints="",  # Add appropriate constraints
                dataset_columns_info=dataset_insights,
                input_query=approach_result.get("create_table_query", ""),
                # task_id=f"{workflow_id}_sql_exec"
            )
            
            # Update workflow context with final results
            workflow_ctx["steps"]["sql_execution"] = {
                "status": sql_result.get("status"),
                "result": sql_result
            }
            
            if sql_result.get("status") != "success":
                workflow_ctx["status"] = "failed"
                workflow_ctx["error"] = "SQL execution failed"
            # Update workflow context with success
            workflow_ctx["status"] = "completed"
            workflow_ctx["completed_at"] = datetime.now().isoformat()
            
            try:
                # Save the final workflow state
                self.workflow_storage.save_step_result(
                    step_id=f"{workflow_id}_completed",
                    data=workflow_ctx,
                    step_type="workflow_complete",
                    metadata={
                        "workflow_id": workflow_id,
                        "status": "completed",
                        "completed_at": workflow_ctx["completed_at"]
                    }
                )
            except Exception as e:
                self.logger.error(f"Failed to save completed workflow state: {e}")
            
            # Return combined results
            result = {
                "status": "success",
                "workflow_id": workflow_id,
                "results": {
                    "column_check": column_check_result,
                    "approach_generation": approach_result,
                    "sql_execution": sql_result
                }
            }
            
            return result
            
        except Exception as e:

            error_msg = f"Pipeline execution failed: {str(e)}"
            self.logger.error(f"{error_msg}\n{traceback.format_exc()}")
            
            # Update workflow context with error
            workflow_ctx.update({
                "status": "failed",
                "error": error_msg,
                "traceback": traceback.format_exc()
            })
            
            try:
                # Save the error state as a step result
                self.workflow_storage.save_step_result(
                    step_id=f"{workflow_id}_error",
                    data=workflow_ctx,
                    step_type="workflow_error",
                    metadata={
                        "workflow_id": workflow_id,
                        "status": "failed",
                        "error": error_msg
                    }
                )
            except Exception as storage_error:
                self.logger.error(f"Failed to save workflow error status: {storage_error}")
            
            raise RuntimeError(error_msg) from e
    
    
    def _process_llm_response(self, response: Union[str, Dict]) -> Dict[str, Any]:
        """
        Process and validate the LLM response using sfn_blueprint patterns.
        
        Args:
            response: Raw response from the LLM
            
        Returns:
            Processed response as a dictionary
        """
        try:
            # Handle different response formats
            if isinstance(response, dict):
                return response
                
            if not isinstance(response, str):
                response = str(response)
                
            # Try to parse as JSON first
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
                
            # Try to extract code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
                
            # if "```" in response:
            #     code_block = response.split("```")[1].split("```")[0].strip()
            #     if code_block.startswith("{") and code_block.endswith("}"):
            #         return json.loads(code_block)
            #     return {"code": code_block}
                
            # Default: return as text
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing LLM response: {e}")
            return {"error": str(e), "raw_response": response}
    
    def _extract_sql_from_response(self, response: str) -> str:
        """
        Extract SQL query from LLM response.
        
        Args:
            response: LLM response text
            
        Returns:
            Extracted SQL query
        """
        try:
            # Try to process as structured response first
            processed = self._process_llm_response(response)
            if isinstance(processed, dict) and "sql" in processed:
                return processed["sql"]
                
            # Fallback to text extraction
            if "```sql" in response:
                return response.split("```sql")[1].split("```")[0].strip()
            if "```" in response:
                return response.split("```")[1].split("```")[0].strip()
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Error extracting SQL: {e}")
            return response.strip()


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Initialize agent
        agent = TargetSynthesisAgent()
        
        # Example request
        request = AgentInputsRequest(
            conn=None,  # Replace with actual connection
            customer_id="example_customer",
            auth_service_base_url="",
            project_name="example_project",
            schema=None,
            table_name="example_table",
            mappings={},
            use_case="churn_prediction",
            ml_approach="binary_classification",
            experiment_type=None,
        )
        
        # Example definition and mapping
        definition = "Predict customer churn in the next 30 days"
        mapping_response = {
            "customer_id": "id",
            "signup_date": "created_at",
            # Add more mappings as needed
        }
        
        # Execute pipeline
        result = await agent.execute_pipeline(request, definition, mapping_response)
        print("Pipeline result:", result)
    
    asyncio.run(main())
