import pytest
from unittest.mock import patch, MagicMock
import json
import tempfile
import os
from table_categorization_agent import TableCategorizationAgent

@pytest.fixture
def domain_schema_file():
    """Fixture that creates a temporary domain schema file."""
    schema_content = {
        "entities": [
            {"label": "Patient", "iri": "p", "comment": "p"},
            {"label": "Encounter", "iri": "e", "comment": "e"},
            {"label": "Claim", "iri": "c", "comment": "c"}
        ]
    }
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
        json.dump(schema_content, tmp)
        tmp_path = tmp.name
    
    yield tmp_path
    
    os.unlink(tmp_path)

@patch('table_categorization_agent.agent.SFNAIHandler')
def test_execute_task_success(mock_sfnhandler_class, domain_schema_file):
    """Test successful execution of the categorization task."""
    agent = TableCategorizationAgent()
    # Mock the instance and its route_to method
    mock_handler_instance = mock_sfnhandler_class.return_value
    mock_response = {
        "Patient": ["table1"],
        "Encounter": ["table2"],
        "Claim": ["table3"],
        "Unassigned": []
    }
    mock_handler_instance.route_to.return_value = (json.dumps(mock_response), {"total_cost": 0.0})

    task_data = {
        "domain_schema": domain_schema_file,
        "tables_metadata": {
            "table1": "This table stores patient demographics.",
            "table2": "This table stores patient encounter information.",
            "table3": "This table stores claim information."
        }
    }

    result = agent.execute_task(task_data)

    assert result["success"] is True
    assert result["agent"] == "table_categorization_agent"
    assert "result" in result
    assert "table_categories" in result["result"]
    assert result["result"]["table_categories"] == {
        'entities': [
            {'entity_name': 'Patient', 'tables': ['table1']},
            {'entity_name': 'Encounter', 'tables': ['table2']},
            {'entity_name': 'Claim', 'tables': ['table3']}
        ],
        'unassigned': []
    }
    mock_handler_instance.route_to.assert_called_once()

def test_execute_task_no_tables_metadata(domain_schema_file):
    """Test task execution failure when tables_metadata is missing."""
    agent = TableCategorizationAgent()
    task_data = {
        "domain_schema": domain_schema_file
    }

    result = agent.execute_task(task_data)

    assert result["success"] is False
    assert result["error"] == "No mapping_table provided in task data"
    assert result["agent"] == "table_categorization_agent"

def test_execute_task_no_domain_schema():
    """Test task execution failure when domain_schema is missing or invalid."""
    agent = TableCategorizationAgent()
    task_data = {
        "tables_metadata": {
            "table1": "This table stores patient demographics."
        }
    }
    # Here we are not passing domain_schema path, so it should fail
    result = agent.execute_task(task_data)

    assert result["success"] is False
    assert result["error"] == "No valid domain schema loaded"
    assert result["agent"] == "table_categorization_agent"

@patch('table_categorization_agent.agent.TableCategorizationAgent.categorize_table')
def test_execute_task_categorize_table_failure(mock_categorize_table, domain_schema_file):
    """Test task execution when categorize_table fails."""
    agent = TableCategorizationAgent()
    mock_categorize_table.side_effect = Exception("Categorization error")

    task_data = {
        "domain_schema": domain_schema_file,
        "tables_metadata": {
            "table1": "This table stores patient demographics."
        }
    }

    result = agent.execute_task(task_data)

    assert result["success"] is False
    assert "Task execution failed: Categorization error" in result["error"]
    assert result["agent"] == "table_categorization_agent"

def test_load_domain_schema_success():
    """Test loading a valid domain schema."""
    agent = TableCategorizationAgent()
    schema_content = {"entities": [{"label": "Patient"}]}
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
        json.dump(schema_content, tmp)
        tmp_path = tmp.name
    
    agent.load_domain_schema(tmp_path)
    os.unlink(tmp_path)
    
    assert agent.domain_schema == schema_content

def test_load_domain_schema_file_not_found():
    """Test loading a non-existent domain schema file."""
    agent = TableCategorizationAgent()
    agent.load_domain_schema("non_existent_file.json")
    assert agent.domain_schema == {}

def test_load_domain_schema_invalid_json():
    """Test loading a domain schema with invalid JSON."""
    agent = TableCategorizationAgent()
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
        tmp.write("{'invalid': 'json'}")
        tmp_path = tmp.name
        
    agent.load_domain_schema(tmp_path)
    os.unlink(tmp_path)
    
    assert agent.domain_schema == {}

@patch('table_categorization_agent.agent.SFNAIHandler')
def test_categorize_table(mock_sfnhandler_class):
    """Test the categorize_table method directly."""
    agent = TableCategorizationAgent()
    mock_handler_instance = mock_sfnhandler_class.return_value
    mock_response = {"Patient": ["table1"], "Unassigned": []}
    mock_handler_instance.route_to.return_value = (f"```json\n{json.dumps(mock_response)}\n```", {"total_cost": 0.0})

    agent.domain_schema = {
        "entities": [
            {
                "label": "Patient",
                "iri": "http://example.com/Patient",
                "comment": "Represents a patient"
            }
        ]
    }
    tables_metadata = {"table1": "Patient data"}
    entity_block = "1. Patient: Represents a patient"
    
    result, _ = agent.categorize_table(tables_metadata, entity_block)
    
    assert result.dict() == {'entities': [{'entity_name': 'Patient', 'tables': ['table1']}], 'unassigned': []}
    mock_handler_instance.route_to.assert_called_once()
