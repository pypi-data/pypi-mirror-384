"""
Table Categorization Agent

An LLM-driven agent that analyzes data tables and categorizes them based on
domain schemas. This agent identifies entities, attributes, and relationships
from data and maps them to domain concepts.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from sfn_blueprint import MODEL_CONFIG, SFNAIHandler, SFNDataLoader

from .constants import (
    format_categorization_prompt,
    format_column_details,
    format_single_categorization_prompt,
)
from .models import CategorizationResult, TableCategory
from .config import TableCategorizationConfig


class TableCategorizationAgent:
    """
    LLM-driven agent for categorizing data tables based on domain schemas.

    This agent analyzes table structure, content, and patterns to identify
    which domain entities they represent and how they relate to other tables.
    """

    def __init__(self, domain_schema_path: Optional[str] = None, config: Optional[TableCategorizationConfig] = None):
        """
        Initialize the Table Categorization Agent.

        Args:
            domain_schema_path: Path to the domain schema JSON file
        """
        self.logger = logging.getLogger(__name__)
        self.ai_handler = SFNAIHandler()
        self.data_loader = SFNDataLoader()
        self.config = config or TableCategorizationConfig()

        # Load domain schema if provided
        self.domain_schema = {}

        if domain_schema_path:
            self.load_domain_schema(domain_schema_path)

    def load_domain_schema(self, schema_path: str):
        """Load and parse domain schema from JSON file"""
        try:
            with open(schema_path, "r") as f:
                self.domain_schema = json.load(f)

            self.logger.info(f"Loaded domain schema from {schema_path}")
        except Exception as e:
            self.logger.error(f"Failed to load domain schema: {e}")
            self.domain_schema = {}

    def analyze_table_structure(
        self, df: pd.DataFrame, table_name: str
    ) -> Dict[str, Any]:
        """
        Analyze the structure of a data table.

        Args:
            df: Pandas DataFrame to analyze
            table_name: Name of the table

        Returns:
            Dictionary containing structural analysis
        """
        analysis = {
            "table_name": table_name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": [],
            "data_types": {},
            "null_counts": {},
            "unique_counts": {},
            "sample_values": {},
        }

        for col in df.columns:
            col_analysis = {
                "name": col,
                "data_type": str(df[col].dtype),
                "null_count": df[col].isnull().sum(),
                "unique_count": df[col].nunique(),
                "sample_values": df[col].dropna().head(3).tolist(),
            }

            analysis["columns"].append(col_analysis)
            analysis["data_types"][col] = str(df[col].dtype)
            analysis["null_counts"][col] = df[col].isnull().sum()
            analysis["unique_counts"][col] = df[col].nunique()
            analysis["sample_values"][col] = df[col].dropna().head(3).tolist()

        return analysis

    def generate_categorization_prompt(
        self,
        analysis: Dict[str, Any],
        enriched_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate LLM prompt for table categorization with enriched context.

        Args:
            analysis: Table structure analysis
            enriched_context: Optional enriched context from problem orchestrator

        Returns:
            Formatted prompt string
        """
        domain_context = ""
        if self.domain_schema:
            domain_context = f"""
            DOMAIN SCHEMA CONTEXT:
            {self.domain_schema}
            """

        # Add enriched context if available
        if enriched_context:
            domain_context += f"""
            
            ENRICHED CONTEXT:
            - Domain: {enriched_context.get('domain_knowledge', {}).get('domain', 'Unknown')}
            - Workflow Goal: {enriched_context.get('workflow_context', {}).get('goal', 'Unknown')}
            - Business Context: {enriched_context.get('domain_knowledge', {}).get('business_context', {}).get('industry', 'Unknown')}
            - Compliance: {enriched_context.get('domain_knowledge', {}).get('business_context', {}).get('compliance', 'None')}
            - Data Sensitivity: {enriched_context.get('domain_knowledge', {}).get('business_context', {}).get('data_sensitivity', 'Unknown')}
            """

        # Use constants and utility functions for prompt generation
        column_details = format_column_details(analysis["columns"])

        return format_single_categorization_prompt(
            domain_context=domain_context,
            table_name=analysis["table_name"],
            row_count=analysis["row_count"],
            column_count=analysis["column_count"],
            column_details=column_details,
        )

    def categorize_table(
        self, tables_metadata: Dict[str, Any], entity_block: Dict[str, Any], max_try=3
    ) -> TableCategory:
        """
        Categorize a single table using LLM analysis with enriched context.

        Args:
            df: Pandas DataFrame to categorize
            table_name: Name of the table
            enriched_context: Optional enriched context from problem orchestrator

        Returns:
            TableCategory object with categorization results
        """

        for _ in range(max_try):
            try:
                # Analyze table structure
                # analysis = self.analyze_table_structure(df, table_name)

                # Generate LLM prompt with enriched context if available
                # if enriched_context:
                #     prompt = self.generate_categorization_prompt(analysis, enriched_context)
                # else:
                #     prompt = self.generate_categorization_prompt(analysis)

                # Get LLM response

                system_prompt, user_prompt = format_categorization_prompt(
                    table_block=tables_metadata, entity_block=entity_block
                )

                response, cost_summary = self.ai_handler.route_to(
                    llm_provider=self.config.table_ai_provider,
                    configuration={
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "max_tokens": self.config.table_max_tokens,
                        "temperature": self.config.table_temperature,
                    },
                    model=self.config.table_model,
                )

                # Clean the response - remove markdown code blocks if present
                clean_response = response.strip()
                if clean_response.startswith("```json"):
                    clean_response = clean_response[7:]  # Remove ```json
                if clean_response.endswith("```"):
                    clean_response = clean_response[:-3]  # Remove ```
                clean_response = clean_response.strip()

                llm_result = json.loads(clean_response)
                return CategorizationResult.from_raw_json(llm_result), cost_summary

            except Exception as e:
                self.logger.error(f"Error categorizing tables {e} ")

        return None, None

    def _fallback_categorization(self, analysis: Dict[str, Any]) -> TableCategory:
        """Provide fallback categorization when LLM fails"""
        return TableCategory(
            table_name=analysis.get("table_name", "Unknown"),
            primary_entity="Unknown",
            confidence_score=0.0,
            mapped_attributes={},
            suggested_relationships=[],
            data_quality_score=0.0,
            recommendations=["LLM analysis failed - manual review required"],
        )

        # def categorize_multiple_tables(self, tables: Dict[str, str]) -> CategorizationResult:
        # """
        # Categorize multiple tables and provide overall analysis with enriched context.

        # Args:
        #     tables: Dictionary mapping table names to DataFrames
        #     enriched_context: Optional enriched context from problem orchestrator

        # Returns:
        #     CategorizationResult with comprehensive analysis
        # """
        # table_categories = []

        # for table_name, df in tables.items():
        #     self.logger.info(f"Categorizing table: {table_name}")
        #     category = self.categorize_table(df, table_name, enriched_context)
        #     table_categories.append(category)

        # Calculate domain coverage
        # domain_coverage = self._calculate_domain_coverage(table_categories)

        # Generate insights
        # data_insights = self._generate_data_insights(table_categories)

        # Suggest next steps
        # next_steps = self._suggest_next_steps(table_categories)

        # return CategorizationResult(
        #     table_categories=table_categories,
        #     domain_coverage=domain_coverage,
        #     data_insights=data_insights,
        #     next_steps=next_steps
        # )

    def _calculate_domain_coverage(
        self, table_categories: List[TableCategory]
    ) -> float:
        """Calculate how well the tables cover the domain entities."""
        if not self.domain_schema or "entities" not in self.domain_schema:
            return 1.0  # Assume full coverage if no schema

        domain_entities = self.domain_schema["entities"]

        if isinstance(domain_entities, list):
            expected_entities = domain_entities
        elif isinstance(domain_entities, dict):
            expected_entities = list(domain_entities.keys())
        else:
            return 1.0

        found_entities = set()

        for cat in table_categories:
            if cat.primary_entity and cat.primary_entity != "Unknown":
                found_entities.add(cat.primary_entity)

        if not expected_entities:
            return 1.0

        return len(found_entities) / len(expected_entities)

    def _generate_data_insights(
        self, table_categories: List[TableCategory]
    ) -> List[str]:
        """Generate insights from the categorized tables."""
        insights = []

        # Analyze data quality
        avg_quality = sum(cat.data_quality_score for cat in table_categories) / len(
            table_categories
        )
        insights.append(f"Average data quality score: {avg_quality:.1%}")

        # Analyze entity distribution
        entities = [
            cat.primary_entity
            for cat in table_categories
            if cat.primary_entity != "Unknown"
        ]
        if entities:
            # Convert entities to strings for set operations
            entity_strings = [str(entity) for entity in entities]
            unique_entities = set(entity_strings)
            insights.append(f"Identified entities: {', '.join(unique_entities)}")

        # Analyze confidence levels
        avg_confidence = sum(cat.confidence_score for cat in table_categories) / len(
            table_categories
        )
        insights.append(f"Average categorization confidence: {avg_confidence:.1%}")

        return insights

    def _suggest_next_steps(self, table_categories: List[TableCategory]) -> List[str]:
        """Suggest next steps based on categorization results."""
        steps = []

        # Check for low confidence categorizations
        low_confidence = [cat for cat in table_categories if cat.confidence_score < 0.7]
        if low_confidence:
            steps.append("Review low-confidence categorizations manually")

        # Check for data quality issues
        low_quality = [cat for cat in table_categories if cat.data_quality_score < 0.8]

        if low_quality:
            steps.append("Address data quality issues before proceeding")

        # Suggest workflow order
        steps.append("Process tables in order of data dependencies")
        steps.append("Apply cleaning and mapping based on entity types")

        return steps

    def generate_summary(self, result: CategorizationResult) -> str:
        """
        Generate a human-readable summary of categorization results.

        Args:
            result: CategorizationResult to summarize

        Returns:
            Formatted summary string
        """
        summary = f"""
        TABLE CATEGORIZATION SUMMARY
        ===========================
        
        Total Tables Analyzed: {len(result.table_categories)}
        Domain Coverage: {result.domain_coverage:.1%}
        
        TABLE BREAKDOWN:
        """

        for cat in result.table_categories:
            summary += f"""
            - {cat.table_name}:
                - Primary Entity: {cat.primary_entity}
                - Confidence: {cat.confidence_score:.1%}
                - Data Quality: {cat.data_quality_score:.1%}
                - Mapped Attributes: {len(cat.mapped_attributes)}
                - Suggested Relationships: {len(cat.suggested_relationships)}
            """

        summary += f"""
        
        DATA INSIGHTS:
        {chr(10).join(f"- {insight}" for insight in result.data_insights)}
        
        RECOMMENDED NEXT STEPS:
        {chr(10).join(f"- {step}" for step in result.next_steps)}
        """

        return summary

    def _analyze_entity_coverage(
        self, table_categories: List[TableCategory]
    ) -> Dict[str, Any]:
        """
        Analyze how well the available datasets cover the domain entities.

        Args:
            table_categories: List of categorized tables

        Returns:
            Dictionary with entity coverage analysis
        """

        entity_analysis = {
            "entities_found": [],
            "entities_missing": [],
            "coverage_percentage": 0.0,
            "recommendations": [],
        }

        # Extract entities from domain schema if available
        if self.domain_schema and "entities" in self.domain_schema:
            domain_entities = self.domain_schema["entities"]
            if isinstance(domain_entities, list):
                expected_entities = domain_entities
            elif isinstance(domain_entities, dict):
                expected_entities = list(domain_entities.keys())
            else:
                expected_entities = []
        else:
            expected_entities = []

        # Analyze found entities
        found_entities = set()

        for cat in table_categories:
            if cat.primary_entity and cat.primary_entity != "Unknown":
                found_entities.add(cat.primary_entity)

        entity_analysis["entities_found"] = list(found_entities)

        # Identify missing entities
        if expected_entities:
            # Convert expected entities to strings for set operations
            expected_entity_strings = [str(entity) for entity in expected_entities]
            missing_entities = set(expected_entity_strings) - found_entities
            entity_analysis["entities_missing"] = list(missing_entities)
            entity_analysis["coverage_percentage"] = (
                len(found_entities) / len(expected_entities) * 100
            )
        else:
            entity_analysis["coverage_percentage"] = 100.0 if found_entities else 0.0

        # Generate recommendations
        if entity_analysis["entities_missing"]:
            entity_analysis["recommendations"].append(
                f"Missing entities: {', '.join(entity_analysis['entities_missing'])} - consider adding datasets for these entities"
            )

        if len(table_categories) < len(expected_entities):
            entity_analysis["recommendations"].append(
                f"Only {len(table_categories)} datasets available for {len(expected_entities)} expected entities"
            )

        return entity_analysis

    def _generate_workflow_recommendations(
        self, dataset_entity_mapping: Dict[str, Any]
    ) -> List[str]:
        """
        Generate workflow recommendations based on dataset-entity mapping.

        Args:
            dataset_entity_mapping: Mapping of datasets to entities

        Returns:
            List of workflow recommendations
        """

        recommendations = []

        # Analyze dataset distribution
        datasets = list(dataset_entity_mapping.keys())

        entities = [
            mapping["primary_entity"] for mapping in dataset_entity_mapping.values()
        ]

        # Convert entities to strings for set operations
        entity_strings = [str(entity) for entity in entities]
        unique_entities = set(entity_strings)

        if len(datasets) == 1 and len(unique_entities) > 1:
            recommendations.append(
                f"Single dataset contains multiple entities: {', '.join(unique_entities)}. "
                "Process this dataset once but analyze multiple entities within it."
            )
        elif len(datasets) == len(unique_entities):
            recommendations.append(
                "Each dataset maps to a unique entity. Create separate workflows for each entity."
            )
        else:
            recommendations.append(
                f"Mixed entity distribution: {len(datasets)} datasets for {len(unique_entities)} entities. "
                "Create focused workflows based on entity relationships."
            )

        # Generate domain-agnostic recommendations using LLM intelligence
        # Let the LLM analyze the entities and provide intelligent workflow suggestions
        if entities and len(entities) > 1:

            recommendations.append(
                "Analyze entity relationships to determine optimal processing order"
            )

            recommendations.append(
                "Identify foundational entities that other entities depend on"
            )

            recommendations.append(
                "Consider data dependencies when planning workflow execution"
            )

        # Generic workflow principles that apply to any domain
        recommendations.append(
            "Process data in order of dependencies (foundational → dependent)"
        )

        recommendations.append(
            "Apply data quality checks before mapping and joining operations"
        )

        recommendations.append(
            "Consider business rules and compliance requirements for the domain"
        )

        return recommendations

    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a table categorization task with the given task data.
        This method provides a standard interface for the orchestrator.

        Args:
            task_data: Dictionary containing task information
                - file: File path or data source
                - problem_context: Context about the categorization task
                - domain_schema: Optional domain schema path
                - enriched_context: Enriched context from orchestrator

        Returns:
            Dictionary with execution results
        """

        try:
            # Extract parameters from task_data
            tables_metadata = task_data.get("tables_metadata")
            entity_block = task_data.get("entity_block", None)

            if entity_block:
                entity_block = "\n".join(
                            [
                                f"{i+1}. {item.get('name', item.get('label', item.get('iri', '')))}: {item.get('description', item.get('comment', ''))}"
                                for i, item in enumerate(entity_block )
                            ]
                        )
            else:
                # problem_context = task_data.get('problem_context', 'Table categorization task')
                domain_schema = task_data.get("domain_schema")
                if not tables_metadata:
                    return {
                        "success": False,
                        "error": "No mapping_table provided in task data",
                        "agent": "table_categorization_agent",
                    }

                # Load domain schema if provided
                if domain_schema:
                    self.load_domain_schema(domain_schema)

                if not self.domain_schema:
                    return {
                        "success": False,
                        "error": "No valid domain schema loaded",
                        "agent": "table_categorization_agent",
                    }

                entity_block = "\n".join(
                    [
                        f"{i+1}. {entity.get('label', entity.get('iri', ''))}: {entity.get('comment', '')}"
                        for i, entity in enumerate(
                            self.domain_schema.get("entities", [])
                        )
                    ]
                )
            table_block = "\n".join(
                [
                    f"{i+1}. Table Name: {name}\n   Description: {description}"
                    for i, (name, description) in enumerate(tables_metadata.items())
                ]
            )

            # self.logger.info(f"Executing table categorization task: {problem_context}")

            # Extract and analyze context for intelligent decision making
            # context_info = None
            # context_recommendations = None

            # try:
            #     # Extract context information
            #     context_info = extract_context_info(task_data)
            #     if context_info:
            #         self.logger.info(f"Context extracted for domain: {context_info.domain}")

            #         # Validate context quality
            #         validation_result = validate_context(context_info, ['domain', 'workflow_goal', 'data_sensitivity'])
            #         if not validation_result['is_valid']:
            #             self.logger.warning(f"Context validation issues: {validation_result['recommendations']}")

            #         # Get AI-powered recommendations
            #         context_recommendations = get_context_recommendations(context_info, 'table_categorization_agent')
            #         self.logger.info(f"Generated {len(context_recommendations.data_processing)} data processing recommendations")

            #         # Log context usage
            #         log_context_usage(context_info, 'table_categorization_agent', ['domain', 'workflow_goal', 'compliance_requirements'])

            # except Exception as e:
            #     self.logger.warning(f"Context analysis failed, proceeding with basic execution: {e}")

            # Load datasets
            # tables = {}
            # if isinstance(data_file, str):
            #     # Single file
            #     try:
            #         df = pd.read_csv(data_file)
            #         table_name = data_file.split('/')[-1].replace('.csv', '')
            #         tables[table_name] = df
            #         self.logger.info(f"Loaded dataset: {table_name} with {len(df)} rows and {len(df.columns)} columns")
            #     except Exception as e:
            #         return {
            #             "success": False,
            #             "error": f"Failed to load dataset: {e}",
            #             "agent": "table_categorization_agent"
            #         }
            # elif isinstance(data_file, list):
            #     # Multiple files
            #     for file_path in data_file:
            #         try:
            #             df = pd.read_csv(file_path)
            #             table_name = file_path.split('/')[-1].replace('.csv', '')
            #             tables[table_name] = df
            #             self.logger.info(f"Loaded dataset: {table_name} with {len(df)} rows and {len(df.columns)} columns")
            #         except Exception as e:
            #             self.logger.warning(f"Failed to load {file_path}: {e}")
            #             continue

            # if not tables:
            #     return {
            #         "success": False,
            #         "error": "No datasets could be loaded successfully",
            #         "agent": "table_categorization_agent"
            #     }

            # Execute comprehensive categorization
            categorization_result, cost_summary = self.categorize_table(
                table_block, entity_block
            )

            if categorization_result is None:
                return {
                    "success": False,
                    "error": "Table categorization failed.",
                    "agent": "table_categorization_agent",
                }

            # Create dataset-entity mapping
            # dataset_entity_mapping = {}
            # for cat in categorization_result.table_categories:
            #     dataset_entity_mapping[cat.table_name] = {
            #         "primary_entity": cat.primary_entity,
            #         "confidence_score": cat.confidence_score,
            #         "mapped_attributes": cat.mapped_attributes,
            #         "data_quality_score": cat.data_quality_score
            #     }

            # Generate comprehensive insights
            # entity_coverage = self._analyze_entity_coverage(categorization_result.table_categories)
            # workflow_recommendations = self._generate_workflow_recommendations(dataset_entity_mapping)

            # Save results to workflow storage if available
            try:
                # Check if we have workflow storage information
                if "workflow_storage_path" in task_data or "workflow_id" in task_data:
                    from sfn_blueprint import WorkflowStorageManager

                    # Determine workflow storage path
                    workflow_storage_path = task_data.get(
                        "workflow_storage_path", "outputs/workflows"
                    )

                    workflow_id = task_data.get("workflow_id", "unknown")

                    # Initialize storage manager
                    storage_manager = WorkflowStorageManager(
                        workflow_storage_path, workflow_id
                    )

                    # Create a comprehensive summary DataFrame for storage

                    # summary_data = pd.DataFrame([
                    #     {
                    #         'table_name': cat.table_name,
                    #         'primary_entity': cat.primary_entity,
                    #         'confidence_score': cat.confidence_score,
                    #         'data_quality_score': cat.data_quality_score,
                    #         'mapped_attributes_count': len(cat.mapped_attributes),
                    #         'domain': context_info.domain if context_info else 'unknown',
                    #         'workflow_goal': context_info.workflow_goal if context_info else 'unknown',
                    #         'context_quality_score': validation_result['quality_score'] if context_info else 0.0
                    #     }
                    #     for cat in categorization_result.table_categories
                    # ])

                    # Prepare metadata with context information
                    # metadata = {
                    #     "categorization_result": {
                    #         "datasets_analyzed": len(tables),
                    #         "entity_coverage": entity_coverage,
                    #         "domain_coverage": categorization_result.domain_coverage,
                    #         "workflow_recommendations": workflow_recommendations
                    #     },
                    #     "context_info": {
                    #         "domain": context_info.domain if context_info else 'unknown',
                    #         "workflow_goal": context_info.workflow_goal if context_info else 'unknown',
                    #         "data_sensitivity": context_info.data_sensitivity if context_info else 'medium',
                    #         "compliance_requirements": context_info.compliance_requirements if context_info else [],
                    #         "context_quality_score": validation_result['quality_score'] if context_info else 0.0
                    #     },
                    #     "ai_recommendations": {
                    #         "data_processing": context_recommendations.data_processing if context_recommendations else [],
                    #         "quality_checks": context_recommendations.quality_checks if context_recommendations else [],
                    #         "optimization_strategies": context_recommendations.optimization_strategies if context_recommendations else [],
                    #         "compliance_measures": context_recommendations.compliance_measures if context_recommendations else []
                    #     },
                    #     "problem_context": problem_context,
                    #     "domain_schema": domain_schema,
                    #     "execution_time": datetime.now().isoformat()
                    # }

                    # Save the categorization results
                    storage_result = storage_manager.save_agent_result(
                        agent_name="table_categorization_agent",
                        step_name="table_categorization",
                        data=categorization_result.model_dump(),
                        metadata={
                            "table_metadata": tables_metadata,
                            "domain_schema": self.domain_schema,
                            "execution_time": datetime.now().isoformat(),
                        },
                    )

                    self.logger.info(
                        f"Table categorization results saved to workflow storage: {storage_result['files']}"
                    )

            except ImportError:
                self.logger.warning(
                    "WorkflowStorageManager not available, skipping workflow storage"
                )
            except Exception as e:
                self.logger.warning(f"Failed to save to workflow storage: {e}")

            # Convert response to orchestrator format with context information
            return {
                "success": True,
                "result": {
                    "table_categories": categorization_result.model_dump(),
                    "cost_summary": cost_summary,
                    # "datasets_analyzed": len(tables),
                    # "dataset_entity_mapping": dataset_entity_mapping,
                    # "entity_coverage": entity_coverage,
                    # "domain_coverage": categorization_result.domain_coverage,
                    # "workflow_recommendations": workflow_recommendations,
                    # "data_insights": categorization_result.data_insights,
                    # "next_steps": categorization_result.next_steps,
                    # "summary": self.generate_summary(categorization_result),
                    # "context_analysis": {
                    #     "domain": context_info.domain if context_info else 'unknown',
                    #     "workflow_goal": context_info.workflow_goal if context_info else 'unknown',
                    #     "context_quality_score": validation_result['quality_score'] if context_info else 0.0
                    # },
                    # "ai_recommendations": {
                    #     "data_processing": context_recommendations.data_processing if context_recommendations else [],
                    #     "quality_checks": context_recommendations.quality_checks if context_recommendations else [],
                    #     "optimization_strategies": context_recommendations.optimization_strategies if context_recommendations else [],
                    #     "compliance_measures": context_recommendations.compliance_measures if context_recommendations else []
                    # }
                },
                "agent": "table_categorization_agent",
            }

        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")

            return {
                "success": False,
                "error": f"Task execution failed: {str(e)}",
                "agent": "table_categorization_agent",
            }
    def __call__(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.execute_task(task_data)
