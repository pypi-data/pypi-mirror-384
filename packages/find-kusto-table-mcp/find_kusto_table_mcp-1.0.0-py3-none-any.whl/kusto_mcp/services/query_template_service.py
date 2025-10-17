"""
Query Template Service

Allows users to save and reuse common queries and multi-query workflows
with parameterization. Inspired by SQL prepared statements but for KQL.
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict, field
from enum import Enum


class ParameterType(Enum):
    """Parameter types for query templates"""
    STRING = "string"
    NUMBER = "number"
    DATETIME = "datetime"
    TIMESPAN = "timespan"
    BOOLEAN = "boolean"
    LIST = "list"


@dataclass
class QueryParameter:
    """Definition of a query parameter"""
    name: str
    type: ParameterType
    description: str
    default_value: Optional[Any] = None
    required: bool = True
    validation_regex: Optional[str] = None
    
    def validate(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate parameter value"""
        if value is None:
            if self.required and self.default_value is None:
                return False, f"Parameter '{self.name}' is required"
            return True, None
        
        # Type validation
        if self.type == ParameterType.STRING:
            if not isinstance(value, str):
                return False, f"Parameter '{self.name}' must be a string"
            if self.validation_regex:
                if not re.match(self.validation_regex, value):
                    return False, f"Parameter '{self.name}' does not match required pattern"
        
        elif self.type == ParameterType.NUMBER:
            try:
                float(value)
            except (ValueError, TypeError):
                return False, f"Parameter '{self.name}' must be a number"
        
        elif self.type == ParameterType.BOOLEAN:
            if not isinstance(value, bool):
                return False, f"Parameter '{self.name}' must be a boolean"
        
        elif self.type == ParameterType.LIST:
            if not isinstance(value, list):
                return False, f"Parameter '{self.name}' must be a list"
        
        return True, None


@dataclass
class QueryTemplate:
    """A reusable query template"""
    name: str
    description: str
    query: str  # Query with {parameter_name} placeholders
    parameters: List[QueryParameter]
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: Optional[str] = None
    use_count: int = 0
    estimated_execution_time_ms: Optional[float] = None
    example_values: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def get_parameter_names(self) -> Set[str]:
        """Extract parameter names from query"""
        return set(re.findall(r'\{(\w+)\}', self.query))
    
    def validate_parameters(self) -> tuple[bool, List[str]]:
        """Validate that all template parameters are defined in the query"""
        query_params = self.get_parameter_names()
        defined_params = {p.name for p in self.parameters}
        
        errors = []
        
        # Check for undefined parameters in query
        undefined = query_params - defined_params
        if undefined:
            errors.append(f"Query uses undefined parameters: {', '.join(undefined)}")
        
        # Check for unused parameter definitions
        unused = defined_params - query_params
        if unused:
            errors.append(f"Defined parameters not used in query: {', '.join(unused)}")
        
        return len(errors) == 0, errors
    
    def render(self, parameter_values: Dict[str, Any]) -> tuple[bool, str, List[str]]:
        """
        Render query with parameter values
        
        Returns:
            (success, rendered_query, errors)
        """
        errors = []
        
        # Validate template first
        valid, template_errors = self.validate_parameters()
        if not valid:
            return False, "", template_errors
        
        # Validate and apply parameters
        rendered_query = self.query
        
        for param in self.parameters:
            value = parameter_values.get(param.name)
            
            # Use default if value not provided
            if value is None:
                value = param.default_value
            
            # Validate parameter
            valid, error = param.validate(value)
            if not valid:
                errors.append(error)
                continue
            
            # Format value based on type
            if param.type == ParameterType.STRING:
                # Don't add quotes if it looks like a Kusto function/expression
                if (isinstance(value, str) and 
                    ('(' in value and ')' in value) or  # Function call like ago(24h)
                    value.startswith('now') or 
                    value.startswith('ago') or
                    value.startswith('datetime') or
                    value == 'now()'):
                    formatted_value = str(value)
                else:
                    formatted_value = f"'{value}'"
            elif param.type == ParameterType.DATETIME:
                # Datetime parameters should not be quoted - they're KQL expressions
                formatted_value = str(value)
            elif param.type == ParameterType.LIST:
                formatted_items = [f"'{item}'" if isinstance(item, str) else str(item) for item in value]
                formatted_value = f"({', '.join(formatted_items)})"
            else:
                formatted_value = str(value)
            
            # Replace in query
            rendered_query = rendered_query.replace(f"{{{param.name}}}", formatted_value)
        
        if errors:
            return False, "", errors
        
        # Update usage statistics
        self.use_count += 1
        self.last_used = datetime.now().isoformat()
        
        return True, rendered_query, []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['parameters'] = [
            {**asdict(p), 'type': p.type.value}
            for p in self.parameters
        ]
        return result


@dataclass
class QueryWorkflow:
    """A multi-query workflow"""
    name: str
    description: str
    queries: List[str]  # List of template names in execution order
    parameters: List[QueryParameter]  # Workflow-level parameters
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: Optional[str] = None
    use_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['parameters'] = [
            {**asdict(p), 'type': p.type.value}
            for p in self.parameters
        ]
        return result


class QueryTemplateService:
    """
    Service for managing query templates and workflows
    """
    
    def __init__(self, templates_file: str = "src/services/query_templates.json"):
        self.templates: Dict[str, QueryTemplate] = {}
        self.workflows: Dict[str, QueryWorkflow] = {}
        self.templates_file = templates_file
        
        # Load templates from disk
        self._load_templates()
    
    def validate_query_syntax(
        self,
        query: str,
        parameters: List[QueryParameter],
        cluster: str,
        database: str,
        connection_manager: Any
    ) -> tuple[bool, str]:
        """
        Validate query syntax by executing it with sample parameter values.
        Uses 'take 0' to check syntax without returning data.
        
        Returns:
            (is_valid, error_message)
        """
        import asyncio
        from ..core.logging_config import get_logger
        
        logger = get_logger("query_template_service")
        
        try:
            # Build sample parameter values for validation
            param_values = {}
            for param in parameters:
                if param.default_value is not None:
                    param_values[param.name] = param.default_value
                else:
                    # Provide sensible defaults for validation
                    if param.type == ParameterType.STRING:
                        param_values[param.name] = "test_value"
                    elif param.type == ParameterType.NUMBER:
                        param_values[param.name] = 0
                    elif param.type == ParameterType.DATETIME:
                        param_values[param.name] = "datetime(2024-01-01)"
                    elif param.type == ParameterType.TIMESPAN:
                        param_values[param.name] = "1h"
                    elif param.type == ParameterType.BOOLEAN:
                        param_values[param.name] = True
                    elif param.type == ParameterType.LIST:
                        param_values[param.name] = ["test"]
            
            # Create temporary template to render query
            temp_template = QueryTemplate(
                name="_validation_temp",
                description="Temporary template for validation",
                query=query,
                parameters=parameters,
                tags=[],
                metadata={}
            )
            
            # Render query with sample values
            success, rendered_query, errors = temp_template.render(param_values)
            if not success:
                return False, f"Failed to render query: {'; '.join(errors)}"
            
            # Wrap query in 'take 0' to check syntax without executing
            validation_query = f"{rendered_query}\n| take 0"
            
            # Get Kusto client and execute validation query
            try:
                client = connection_manager.get_client(cluster, database)
                
                # Execute in async context
                async def validate():
                    try:
                        await client.execute_query(validation_query, timeout_seconds=10)
                        return True, ""
                    except Exception as e:
                        error_msg = str(e)
                        # Extract meaningful error from Kusto error message
                        if "Semantic error" in error_msg or "Syntax error" in error_msg:
                            # Parse out the actual error message
                            lines = error_msg.split('\n')
                            for line in lines:
                                if "Semantic error" in line or "Syntax error" in line:
                                    return False, line.strip()
                        return False, f"Query validation failed: {error_msg}"
                
                # Run validation
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, create a new task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(asyncio.run, validate())
                        result = future.result(timeout=15)
                        return result
                else:
                    # If no loop is running, just run it
                    return asyncio.run(validate())
                    
            except Exception as e:
                logger.warning(f"Could not validate query syntax: {e}")
                # If validation fails due to connection issues, allow template creation
                # but warn the user
                return True, f"Warning: Could not validate query (connection issue): {str(e)}"
                
        except Exception as e:
            logger.error(f"Query syntax validation error: {e}", exc_info=True)
            return False, f"Validation error: {str(e)}"
    
    def create_template(
        self,
        name: str,
        description: str,
        query: str,
        parameters: List[QueryParameter],
        tags: Optional[List[str]] = None,
        example_values: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, str]:
        """
        Create a new query template
        
        Returns:
            (success, error_message)
        """
        if name in self.templates:
            return False, f"Template '{name}' already exists"
        
        template = QueryTemplate(
            name=name,
            description=description,
            query=query,
            parameters=parameters,
            tags=tags or [],
            example_values=example_values,
            metadata=metadata or {}
        )
        
        # Validate template
        valid, errors = template.validate_parameters()
        if not valid:
            return False, '; '.join(errors)
        
        self.templates[name] = template
        self._save_templates()
        
        return True, ""
    
    def get_template(self, name: str) -> Optional[QueryTemplate]:
        """Get template by name"""
        return self.templates.get(name)
    
    def list_templates(
        self,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List templates with optional filtering
        
        Args:
            tags: Filter by tags (OR logic)
            search: Search in name and description
        """
        results = []
        
        for template in self.templates.values():
            # Tag filtering
            if tags:
                if not any(tag in template.tags for tag in tags):
                    continue
            
            # Search filtering
            if search:
                search_lower = search.lower()
                if search_lower not in template.name.lower() and \
                   search_lower not in template.description.lower():
                    continue
            
            results.append({
                'name': template.name,
                'description': template.description,
                'parameters': [p.name for p in template.parameters],
                'tags': template.tags,
                'use_count': template.use_count,
                'last_used': template.last_used,
                'created_at': template.created_at,
                'metadata': template.metadata
            })
        
        # Sort by use count
        results.sort(key=lambda x: x['use_count'], reverse=True)
        
        return results
    
    def render_template(
        self,
        name: str,
        parameter_values: Dict[str, Any]
    ) -> tuple[bool, str, List[str]]:
        """
        Render a template with parameter values
        
        Returns:
            (success, rendered_query, errors)
        """
        template = self.templates.get(name)
        if not template:
            return False, "", [f"Template '{name}' not found"]
        
        success, query, errors = template.render(parameter_values)
        
        if success:
            self._save_templates()  # Save updated use statistics
        
        return success, query, errors
    
    def delete_template(self, name: str) -> bool:
        """Delete a template"""
        if name not in self.templates:
            return False
        
        del self.templates[name]
        self._save_templates()
        return True
    
    def create_workflow(
        self,
        name: str,
        description: str,
        query_templates: List[str],
        parameters: List[QueryParameter],
        tags: Optional[List[str]] = None
    ) -> tuple[bool, str]:
        """
        Create a multi-query workflow
        
        Returns:
            (success, error_message)
        """
        if name in self.workflows:
            return False, f"Workflow '{name}' already exists"
        
        # Validate that all referenced templates exist
        for template_name in query_templates:
            if template_name not in self.templates:
                return False, f"Template '{template_name}' not found"
        
        workflow = QueryWorkflow(
            name=name,
            description=description,
            queries=query_templates,
            parameters=parameters,
            tags=tags or []
        )
        
        self.workflows[name] = workflow
        self._save_templates()
        
        return True, ""
    
    def execute_workflow(
        self,
        name: str,
        parameter_values: Dict[str, Any]
    ) -> tuple[bool, List[str], List[str]]:
        """
        Execute a workflow by rendering all queries
        
        Returns:
            (success, rendered_queries, errors)
        """
        workflow = self.workflows.get(name)
        if not workflow:
            return False, [], [f"Workflow '{name}' not found"]
        
        rendered_queries = []
        errors = []
        
        for template_name in workflow.queries:
            success, query, template_errors = self.render_template(
                template_name,
                parameter_values
            )
            
            if not success:
                errors.extend(template_errors)
                continue
            
            rendered_queries.append(query)
        
        if errors:
            return False, rendered_queries, errors
        
        # Update workflow usage
        workflow.use_count += 1
        workflow.last_used = datetime.now().isoformat()
        self._save_templates()
        
        return True, rendered_queries, []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        total_uses = sum(t.use_count for t in self.templates.values())
        
        most_used = sorted(
            self.templates.values(),
            key=lambda t: t.use_count,
            reverse=True
        )[:5]
        
        return {
            'total_templates': len(self.templates),
            'total_workflows': len(self.workflows),
            'total_uses': total_uses,
            'most_used_templates': [
                {
                    'name': t.name,
                    'use_count': t.use_count,
                    'last_used': t.last_used
                }
                for t in most_used
            ]
        }
    
    def _load_templates(self):
        """Load templates from disk"""
        try:
            with open(self.templates_file, 'r') as f:
                data = json.load(f)
            
            # Load templates
            for item in data.get('templates', []):
                parameters = [
                    QueryParameter(
                        name=p['name'],
                        type=ParameterType(p['type']),
                        description=p['description'],
                        default_value=p.get('default_value'),
                        required=p.get('required', True),
                        validation_regex=p.get('validation_regex')
                    )
                    for p in item['parameters']
                ]
                
                template = QueryTemplate(
                    name=item['name'],
                    description=item['description'],
                    query=item['query'],
                    parameters=parameters,
                    tags=item.get('tags', []),
                    created_at=item['created_at'],
                    last_used=item.get('last_used'),
                    use_count=item.get('use_count', 0),
                    estimated_execution_time_ms=item.get('estimated_execution_time_ms'),
                    example_values=item.get('example_values'),
                    metadata=item.get('metadata', {})
                )
                
                self.templates[item['name']] = template
            
            # Load workflows
            for item in data.get('workflows', []):
                parameters = [
                    QueryParameter(
                        name=p['name'],
                        type=ParameterType(p['type']),
                        description=p['description'],
                        default_value=p.get('default_value'),
                        required=p.get('required', True)
                    )
                    for p in item['parameters']
                ]
                
                workflow = QueryWorkflow(
                    name=item['name'],
                    description=item['description'],
                    queries=item['queries'],
                    parameters=parameters,
                    tags=item.get('tags', []),
                    created_at=item['created_at'],
                    last_used=item.get('last_used'),
                    use_count=item.get('use_count', 0)
                )
                
                self.workflows[item['name']] = workflow
        
        except FileNotFoundError:
            pass  # No templates file yet
        except Exception as e:
            print(f"Warning: Failed to load templates: {e}")
    
    def _save_templates(self):
        """Save templates to disk"""
        try:
            data = {
                'version': '1.0',
                'saved_at': datetime.now().isoformat(),
                'templates': [t.to_dict() for t in self.templates.values()],
                'workflows': [w.to_dict() for w in self.workflows.values()]
            }
            
            with open(self.templates_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            print(f"Warning: Failed to save templates: {e}")
    
    def export_template(self, name: str) -> Optional[str]:
        """Export template as JSON string"""
        template = self.templates.get(name)
        if not template:
            return None
        
        return json.dumps(template.to_dict(), indent=2)
    
    def import_template(self, template_json: str) -> tuple[bool, str]:
        """Import template from JSON string"""
        try:
            data = json.loads(template_json)
            
            parameters = [
                QueryParameter(
                    name=p['name'],
                    type=ParameterType(p['type']),
                    description=p['description'],
                    default_value=p.get('default_value'),
                    required=p.get('required', True),
                    validation_regex=p.get('validation_regex')
                )
                for p in data['parameters']
            ]
            
            return self.create_template(
                name=data['name'],
                description=data['description'],
                query=data['query'],
                parameters=parameters,
                tags=data.get('tags'),
                example_values=data.get('example_values')
            )
        
        except Exception as e:
            return False, f"Failed to import template: {str(e)}"


# Singleton instance
_query_template_service = QueryTemplateService()


def get_query_template_service() -> QueryTemplateService:
    """Get the singleton query template service instance"""
    return _query_template_service
