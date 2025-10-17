"""
Tests for the main SQL TargetSynthesisAgent implementation in sql_agent.py
"""
import pytest
import pandas as pd
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text

from target_synthesis_agent.sql_agent import TargetSynthesisAgent
from target_synthesis_agent.models import AgentInputsRequest

class TestSQLTargetSynthesisAgent:
    """Test cases for the SQL TargetSynthesisAgent implementation."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        print("\n[FIXTURE] Setting up sample_data...")
        return pd.DataFrame({
            'customer_id': [f'CUST_{i:03d}' for i in range(1, 6)],
            'age': [25, 30, 35, 40, 45],
            'total_purchases': [10, 15, 5, 20, 8],
            'total_spent': [1000, 1500, 500, 2000, 800],
            'status': ['active', 'inactive', 'active', 'churned', 'active'],
            'support_tickets': [1, 3, 0, 5, 2],
            'days_since_last_login': [10, 5, 45, 60, 2]
        })
    
    @pytest.fixture
    def db_engine(self, sample_data):
        """Set up an in-memory SQLite database with sample data."""
        print("\n[FIXTURE] Setting up db_engine...")
        try:
            engine = create_engine('sqlite:///:memory:')
            sample_data.to_sql('customer_data', engine, index=False, if_exists='replace')
            
            # Add some indexes
            with engine.connect() as conn:
                conn.execute(text('CREATE INDEX idx_customer_id ON customer_data(customer_id)'))
                conn.execute(text('CREATE INDEX idx_status ON customer_data(status)'))
                conn.execute(text('CREATE INDEX idx_days_since_login ON customer_data(days_since_last_login)'))
                conn.commit()
            print("[FIXTURE] db_engine set up successfully")
            return engine
        except Exception as e:
            print(f"Failed to set up db_engine: {e}")
    
    @pytest.fixture
    def agent(self):
        """Create a test agent instance."""
        print("\n[FIXTURE] Creating agent instance...")
        try:
            agent = TargetSynthesisAgent()
            print("[FIXTURE] Agent instance created")
            return agent
        except Exception as e:
            print(f"Failed to create agent instance: {e}")
    
    @pytest.fixture
    def sample_request(self, db_engine):
        """Create a sample request object."""
        with db_engine.connect() as conn:
            return AgentInputsRequest(
                conn=conn,
                customer_id="test_customer",
                auth_service_base_url="http://test.com",
                project_name="test_project",
                schema=None,
                table_name="customer_data",
                mappings={
                    "customer_id": "customer_id",
                    "status": "status",
                    "days_since_last_login": "days_since_last_login"
                },
                use_case="churn_prediction",
                ml_approach="binary_classification",
                experiment_type="classification"
            )
    
    @pytest.mark.asyncio
    async def test_check_columns(self, agent, sample_request):
        """Test the column checking functionality."""
        print("\n[TEST] Running test_check_columns...")
        # Test with valid columns
        result = await agent.check_columns(
            request=sample_request,
            definition="Churn prediction based on login activity",
            mapping_response={
                "customer_id": "customer_id",
                "status": "status",
                "days_since_last_login": "days_since_last_login"
            }
        )
        
        assert isinstance(result, dict)
        assert 'required_columns' in result
        assert 'message' in result
        print("[TEST] test_check_columns completed successfully")
    
    @pytest.mark.asyncio
    async def test_generate_approach(self, agent, sample_request):
        """Test the approach generation functionality."""
        # Mock the AI response
        mock_response = {
            "target_logic": "Churn if not logged in for 30+ days or status is 'churned'",
            "sql_logic_explanation": "Check if days_since_last_login > 30 or status = 'churned'",
            "create_table_query": """
            CREATE TABLE churn_prediction_target AS
            SELECT 
                customer_id,
                CASE 
                    WHEN days_since_last_login > 30 OR status = 'churned' THEN 1
                    ELSE 0 
                END AS target
            FROM customer_data
            """,
            "confidence_score": 0.95
        }
        
        with patch.object(agent.ai_handler, 'route_to', return_value=mock_response) as mock_route_to:
            result = await agent.generate_approach(
                request=sample_request,
                definition="Churn prediction based on login activity",
                mapped_columns=["customer_id", "status", "days_since_last_login"],
                dataset_insights={
                    "table_name": "customer_data",
                    "column_info": {
                        "customer_id": {"dtype": "object", "null_count": 0},
                        "status": {"dtype": "object", "null_count": 0},
                        "days_since_last_login": {"dtype": "int64", "null_count": 0}
                    },
                    "row_count": 5
                }
            )
            print("[TEST] 111 test_generate_approach completed successfully", result, type(result))
            assert isinstance(result, dict)
            assert 'target_logic' in result
            assert 'sql_logic' in result
            assert 'create_table_query' in result
            assert 'confidence_score' in result
            
            # Verify the SQL query was generated
            assert "CREATE TABLE" in result['create_table_query']
            assert "churn_prediction_target" in result['create_table_query']
    
    @pytest.mark.asyncio
    async def test_execute_sql(self, agent, db_engine, sample_request):
        """Test SQL execution with a simple query."""
        with db_engine.connect() as conn:
            result = await agent.execute_sql(
                conn=conn,
                target_logic="Churn prediction based on login activity",
                sql_logic="SELECT * FROM customer_data LIMIT 1",
                ml_target_constraints="Churn if not logged in for 30+ days",
                dataset_columns_info={"table_name": "customer_data"},
                input_query="SELECT * FROM customer_data"
            )
            print('111',result, type(result))
            assert isinstance(result, dict)
            assert 'status' in result
            assert result['status'] == 'success'
            assert 'execution_details' in result
    
    @pytest.mark.asyncio
    async def test_execute_pipeline(self, agent, sample_request):
        """Test the complete pipeline execution."""
        # Mock the AI responses for each step
        mock_check_columns = {
            "required_columns": ["customer_id", "status", "days_since_last_login"],
            "missing_columns": [],
            "messages": ["All required columns are present"]
        }
        
        mock_generate_approach = {
            "target_logic": "Churn if not logged in for 30+ days or status is 'churned'",
            "sql_logic_explanation": "Check if days_since_last_login > 30 or status = 'churned'",
            "create_table_query": """
            CREATE TABLE churn_prediction_target AS
            SELECT 
                customer_id,
                CASE 
                    WHEN days_since_last_login > 30 OR status = 'churned' THEN 1
                    ELSE 0 
                END AS target
            FROM customer_data
            """,
            "confidence_score": 0.95
        }
        
        # Patch the agent methods
        with patch.object(agent, 'check_columns', return_value=mock_check_columns), \
             patch.object(agent, 'generate_approach', return_value=mock_generate_approach), \
             patch.object(agent, 'execute_sql', return_value={"success": True, "rows_affected": 5}):
            
            result = await agent.execute_pipeline(
                request=sample_request,
                definition="Churn prediction based on login activity",
                mapping_response={
                    "customer_id": "customer_id",
                    "status": "status",
                    "days_since_last_login": "days_since_last_login"
                }
            )
            
            assert isinstance(result, dict)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
