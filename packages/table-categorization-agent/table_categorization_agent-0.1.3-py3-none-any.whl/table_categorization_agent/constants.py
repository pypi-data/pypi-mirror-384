"""
Prompt Constants for TableCategorizationAgent

This file contains all prompts used by the TableCategorizationAgent.
All prompts are centralized here for easy review and maintenance.

Prompt Types:
- SYSTEM_PROMPT_*: Role definitions and system instructions
- USER_PROMPT_*: Task-specific user instructions
- PROMPT_TEMPLATE_*: Templates for dynamic content formatting
"""

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

SYSTEM_PROMPT_CATEGORIZATION = """You are an expert data categorizer and domain analyst. Analyze tables intelligently to identify entities, relationships, and workflow patterns for ANY domain (healthcare, retail, finance, manufacturing, etc.). Use the domain schema context to provide accurate, domain-aware categorizations and recommendations."""

SYSTEM_PROMPT_MULTIPLE_CATEGORIZATION = """You are an expert data categorizer and domain analyst. Analyze multiple tables intelligently to identify entities, relationships, and workflow patterns for ANY domain (healthcare, retail, finance, manufacturing, etc.). Use the domain schema context to provide accurate, domain-aware categorizations and recommendations."""


SYSTEM_PROMPT_TABLE_CATEGORIZATION = """
    You are an highly expert data modeling assistant.Your task is to analyze the semantic relationship between each table and the given entities and assign it to **exactly one of the provided entities**, or mark it as `"Unassigned"` if there is no strong match.
    
    You will be given:
    - A list of entities, each with a name and a clear description
    - A batch of database tables, each with a name and description

    Evaluation Instructions: 
    - Carefully consider **all entities** when analyzing each table
    - A table must be assigned to an entity only if:
    1. The table name explicitly mentions the entity name or clearly implies association
    2. The table description semantically aligns with the entity's domain, scope, or purpose
    - If multiple entities are possible, choose the most **specific and direct** match
    - If none of the entities fit clearly, assign the table to `"Unassigned"`

    Important:
    - Every entity must be considered. Do not skip any entity.
    - Every table must be assigned to only one entity, or `"Unassigned"`

    Output Format:
    Return a single, valid JSON object like this:
    {
        "EntityA": ["table_name_1"],
        "EntityB": ["table_name_2", "table_name_3"],
        ...
        ...
        "Unassigned": ["table_name_4"]
    }

    Rules:
    - Do not omit any entity key from the JSON, even if it has no tables (use an empty list)
    - Do not assign the same table to multiple entities
    - Do not include any commentary, explanation, or extra text — only the raw JSON
    """

# =============================================================================
# USER PROMPT TEMPLATES
# =============================================================================

PROMPT_TEMPLATE_SINGLE_CATEGORIZATION = """
You are an expert data categorizer and domain analyst. Analyze the following table and categorize it based on the domain schema for ANY domain (healthcare, retail, finance, manufacturing, etc.).

{domain_context}

TABLE ANALYSIS:
- Table Name: {table_name}
- Rows: {row_count}
- Columns: {column_count}

COLUMN DETAILS:
{column_details}

Based on this analysis, provide a JSON response with:
1. primary_entity: The main domain entity this table represents (use domain-appropriate naming)
2. confidence_score: Confidence level (0.0 to 1.0)
3. mapped_attributes: Dictionary mapping column names to domain attributes
4. suggested_relationships: List of suggested relationships with other entities in this domain
5. data_quality_score: Overall data quality score (0.0 to 1.0)
6. recommendations: List of domain-appropriate recommendations for data processing

IMPORTANT: Be domain-agnostic and intelligent. Analyze the actual data content and domain schema to provide accurate categorizations for ANY domain (healthcare, retail, finance, manufacturing, etc.).

Respond with only valid JSON, no additional text.
"""

PROMPT_TEMPLATE_MULTIPLE_CATEGORIZATION = """
You are an expert data categorizer and domain analyst. Analyze the following tables and categorize them based on the domain schema for ANY domain (healthcare, retail, finance, manufacturing, etc.).

{domain_context}

TABLES TO CATEGORIZE:
{tables_info}

For each table, provide a JSON response with:
1. primary_entity: The main domain entity this table represents (use domain-appropriate naming)
2. confidence_score: Confidence level (0.0 to 1.0)
3. mapped_attributes: Dictionary mapping column names to domain attributes
4. suggested_relationships: List of suggested relationships with other entities in this domain
5. data_quality_score: Overall data quality score (0.0 to 1.0)
6. recommendations: List of domain-appropriate recommendations for data processing

IMPORTANT: 
- Be domain-agnostic and intelligent
- Analyze the actual data content and domain schema
- Provide accurate categorizations for ANY domain (healthcare, retail, finance, manufacturing, etc.)
- Consider relationships between tables when categorizing
- Respond with only valid JSON, no additional text

Format your response as a JSON object with table names as keys:
{{
    "table_name_1": {{
        "primary_entity": "...",
        "confidence_score": 0.0,
        "mapped_attributes": {{}},
        "suggested_relationships": [],
        "data_quality_score": 0.0,
        "recommendations": []
    }},
    "table_name_2": {{
        ...
    }}
}}
"""

PROMPT_TEMPLATE_TABLES_CATEGORIZATION = """
== ENTITIES ==
The following is a list of entities with their names and descriptions:

{entities_block}

== TABLES ==
You are now given a new batch of database tables. Each has a name and a description:

{table_block}

== TASK ==
For each table, assign it to exactly one of the entities above if it strongly matches, or to "Unassigned" if no suitable entity is found.

Output the result in **strict JSON format** like this:
{{
    "EntityName1": ["table_name_a", "table_name_b"],
    "EntityName2": [],
    ...
    "Unassigned": ["table_name_x"]
}}

Rules:
- Every entity listed must appear as a key in the JSON, even if no tables match it (use an empty list).
- Each table must be assigned to only one entity or to "Unassigned".
- Do not include any explanations, comments, or extra text — only return the raw JSON object.
        """

# =============================================================================
# PROMPT UTILITIES
# =============================================================================


def format_categorization_prompt(entity_block, table_block):
    return (
        SYSTEM_PROMPT_TABLE_CATEGORIZATION,
        PROMPT_TEMPLATE_TABLES_CATEGORIZATION.format(
            entities_block=entity_block, table_block=table_block
        ),
    )


def format_single_categorization_prompt(
    domain_context: str,
    table_name: str,
    row_count: int,
    column_count: int,
    column_details: str,
) -> str:
    """
    Format the single table categorization prompt with dynamic content.

    Args:
        domain_context: Domain schema context information
        table_name: Name of the table to categorize
        row_count: Number of rows in the table
        column_count: Number of columns in the table
        column_details: Formatted column details string

    Returns:
        Formatted prompt string
    """

    return PROMPT_TEMPLATE_SINGLE_CATEGORIZATION.format(
        domain_context=domain_context,
        table_name=table_name,
        row_count=row_count,
        column_count=column_count,
        column_details=column_details,
    )


def format_multiple_categorization_prompt(domain_context: str, tables_info: str) -> str:
    """
    Format the multiple table categorization prompt with dynamic content.

    Args:
        domain_context: Domain schema context information
        tables_info: Formatted information about all tables to categorize

    Returns:
        Formatted prompt string
    """

    return PROMPT_TEMPLATE_MULTIPLE_CATEGORIZATION.format(
        domain_context=domain_context, tables_info=tables_info
    )


def format_column_details(columns: list) -> str:
    """
    Format column details for prompt inclusion.

    Args:
        columns: List of column analysis dictionaries

    Returns:
        Formatted column details string
    """
    column_details = ""

    for col in columns:
        column_details += f"""
        - {col['name']}:
            - Type: {col['data_type']}
            - Null Count: {col['null_count']}
            - Unique Values: {col['unique_count']}
            - Sample Values: {col['sample_values']}
        """

    return column_details


def format_tables_info(tables: dict, table_analyses: dict) -> str:
    """
    Format tables information for multiple categorization prompt.

    Args:
        tables: Dictionary of table names to DataFrames
        table_analyses: Dictionary of table analysis results

    Returns:
        Formatted tables information string
    """
    tables_info = ""

    for table_name in tables.keys():
        if table_name in table_analyses:
            analysis = table_analyses[table_name]
            tables_info += f"""
        Table: {table_name}
        - Rows: {analysis['row_count']}
        - Columns: {analysis['column_count']}
        - Column Names: {', '.join(analysis['columns'])}
        """

    return tables_info
