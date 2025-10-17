
import pytest
from unittest.mock import patch
import json
import tempfile
import os
from table_categorization_agent import TableCategorizationAgent
from table_categorization_agent.constants import format_categorization_prompt

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
def test_categorize_table_with_empty_metadata(mock_sfnhandler_class, domain_schema_file):
    """Test categorize_table with empty tables_metadata."""
    agent = TableCategorizationAgent(domain_schema_path=domain_schema_file)
    mock_handler_instance = mock_sfnhandler_class.return_value
    
    tables_metadata = {}
    entity_block = "1. Patient: p\n2. Encounter: e\n3. Claim: c"
    
    system_prompt, user_prompt = format_categorization_prompt(table_block=tables_metadata, entity_block=entity_block)

    mock_response = {
        "Patient": [],
        "Encounter": [],
        "Claim": [],
        "Unassigned": []
    }
    mock_handler_instance.route_to.return_value = (json.dumps(mock_response), {"total_cost": 0.0})

    result, _ = agent.categorize_table(tables_metadata, entity_block)

    assert result.dict() == {'entities': [{'entity_name': 'Patient', 'tables': []}, {'entity_name': 'Encounter', 'tables': []}, {'entity_name': 'Claim', 'tables': []}], 'unassigned': []}
    mock_handler_instance.route_to.assert_called_once_with(
        llm_provider="openai",
        configuration={
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 4000,
        "temperature": 0.3
        },
        model="gpt-4o"
    )
