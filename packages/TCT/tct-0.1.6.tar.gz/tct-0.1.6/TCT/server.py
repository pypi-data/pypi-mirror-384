"""
Translator Component Toolkit MCP Server

This server provides access to biomedical translator tools including:
- Name resolution and lookup
- Node normalization 
- Knowledge provider information
- Meta knowledge graph operations
- Query orchestration
- TRAPI protocol support
"""

from fastmcp import FastMCP
from mcp.shared.exceptions import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

# Import functions from translator_component_toolkit modules using relative imports
from .name_resolver import lookup, synonyms, batch_lookup
from .node_normalizer import get_normalized_nodes
from .translator_kpinfo import get_translator_kp_info
from .translator_metakg import get_KP_metadata, add_new_API_for_query, add_plover_API
from .translator_query import get_translator_API_predicates, optimize_query_json, query_KP, parallel_api_query
from .trapi import query as trapi_query

# Create unified MCP server
mcp = FastMCP("translator-toolkit")

# Name Resolver Tools
@mcp.tool()
def name_lookup(query: str, return_top_response: bool = True, return_synonyms: bool = False):
    """
    Look up a name/term and return normalized TranslatorNode information.
    
    Args:
        query: Query string to look up
        return_top_response: If true, returns only the top response; if false, returns all responses
        return_synonyms: If true, includes synonyms in the result
        
    Returns:
        TranslatorNode object(s) with curie, label, types, and optional synonyms
    """
    try:
        return lookup(query, return_top_response, return_synonyms)
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Name lookup error: {str(e)}")) from e

@mcp.tool()
def get_name_synonyms(query: str):
    """
    Get synonyms for a given CURIE.
    
    Args:
        query: Query CURIE to get synonyms for
        
    Returns:
        Dictionary of CURIE id to TranslatorNode information
    """
    try:
        return synonyms(query)
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Synonyms lookup error: {str(e)}")) from e

@mcp.tool()
def batch_name_lookup(strings: list[str], size: int = 25, return_top_response: bool = True, return_synonyms: bool = False):
    """
    Batch lookup multiple names/terms and return normalized TranslatorNode information.
    
    Args:
        strings: List of query strings to look up
        size: Chunking size for batch processing (default: 25)
        return_top_response: If true, returns only the top response per string
        return_synonyms: If true, includes synonyms in the results
        
    Returns:
        Dictionary mapping strings to their TranslatorNode information
    """
    try:
        return batch_lookup(strings, size, return_top_response, return_synonyms)
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Batch lookup error: {str(e)}")) from e

# Node Normalizer Tools
@mcp.tool()
def normalize_nodes(query: str, return_equivalent_identifiers: bool = False, conflate: bool = True, drug_chemical_conflate: bool = False):
    """
    Normalize node CURIEs using the Node Normalizer API.
    
    Args:
        query: CURIE string or list of CURIEs to normalize
        return_equivalent_identifiers: Whether to return equivalent identifiers
        conflate: Enable gene-protein conflation (default: True)
        drug_chemical_conflate: Enable drug-chemical conflation (default: False)
        
    Returns:
        Normalized TranslatorNode(s) with curie, label, types, and optional synonyms
    """
    try:
        return get_normalized_nodes(query, return_equivalent_identifiers, conflate=conflate, drug_chemical_conflate=drug_chemical_conflate)
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Node normalization error: {str(e)}")) from e

# Knowledge Provider Info Tools
@mcp.tool()
def get_kp_info():
    """
    Get SmartAPI Translator Knowledge Provider information.
    
    Returns:
        Tuple of (DataFrame with KP info, Dictionary mapping API names to URLs)
    """
    try:
        return get_translator_kp_info()
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"KP info error: {str(e)}")) from e

# Meta Knowledge Graph Tools
@mcp.tool()
def get_metakg_data(api_names: dict):
    """
    Get metadata for Knowledge Providers including predicates, subjects, and objects.
    
    Args:
        api_names: Dictionary mapping API names to URLs
        
    Returns:
        DataFrame containing MetaKG information
    """
    try:
        return get_KP_metadata(api_names)
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"MetaKG data error: {str(e)}")) from e

@mcp.tool()
def add_custom_api_to_metakg(api_names: dict, metakg_df, new_api_name: str, new_api_url: str, 
                             new_api_predicate: str, new_api_subject: str, new_api_object: str):
    """
    Add a custom API to the knowledge graph metadata.
    
    Args:
        api_names: Current API names dictionary
        metakg_df: Current MetaKG DataFrame
        new_api_name: Name of the new API
        new_api_url: URL of the new API
        new_api_predicate: Predicate for the new API
        new_api_subject: Subject type for the new API
        new_api_object: Object type for the new API
        
    Returns:
        Tuple of (updated api_names dict, updated metakg DataFrame)
    """
    try:
        return add_new_API_for_query(api_names, metakg_df, new_api_name, new_api_url, 
                                     new_api_predicate, new_api_subject, new_api_object)
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Add custom API error: {str(e)}")) from e

@mcp.tool()
def add_plover_apis_to_metakg(api_names: dict, metakg_df):
    """
    Add Plover APIs (CATRAX team APIs) to the knowledge graph metadata.
    
    Args:
        api_names: Current API names dictionary
        metakg_df: Current MetaKG DataFrame
        
    Returns:
        Tuple of (updated api_names dict, updated metakg DataFrame)
    """
    try:
        return add_plover_API(api_names, metakg_df)
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Add Plover APIs error: {str(e)}")) from e

# Query Tools
@mcp.tool()
def get_api_predicates():
    """
    Get the predicates supported by each Translator API.
    
    Returns:
        Tuple of (API names dict, MetaKG DataFrame, API predicates dict)
    """
    try:
        return get_translator_API_predicates()
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"API predicates error: {str(e)}")) from e

@mcp.tool()
def optimize_query_for_api(query_json: dict, api_name: str, api_predicates: dict):
    """
    Optimize a query JSON by removing predicates not supported by the selected API.
    
    Args:
        query_json: TRAPI 1.5.0 format query
        api_name: Name of the API to query
        api_predicates: Dictionary of API names and their predicates
        
    Returns:
        Modified query JSON with only supported predicates
    """
    try:
        return optimize_query_json(query_json, api_name, api_predicates)
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Query optimization error: {str(e)}")) from e

@mcp.tool()
def query_knowledge_provider(api_name: str, query_json: dict, api_names: dict, api_predicates: dict):
    """
    Query an individual Knowledge Provider API with a TRAPI 1.5.0 query.
    
    Args:
        api_name: Name of the API to query
        query_json: TRAPI 1.5.0 format query
        api_names: Dictionary mapping API names to URLs
        api_predicates: Dictionary of API names and their predicates
        
    Returns:
        Query result from the API or None if no results
    """
    try:
        return query_KP(api_name, query_json, api_names, api_predicates)
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"KP query error: {str(e)}")) from e

@mcp.tool()
def parallel_query_apis(query_json: dict, selected_apis: list[str], api_names: dict, api_predicates: dict, max_workers: int = 1):
    """
    Query multiple APIs in parallel and merge results into a single knowledge graph.
    
    Args:
        query_json: TRAPI 1.5.0 format query
        selected_apis: List of API names to query
        api_names: Dictionary mapping API names to URLs
        api_predicates: Dictionary of API names and their predicates
        max_workers: Number of parallel workers (default: 1)
        
    Returns:
        Merged knowledge graph from all successful API responses
    """
    try:
        return parallel_api_query(query_json, selected_apis, api_names, api_predicates, max_workers)
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"Parallel query error: {str(e)}")) from e

# TRAPI Tools
@mcp.tool()
def trapi_query_endpoint(url: str):
    """
    Query a TRAPI endpoint (currently unimplemented - placeholder).
    
    Args:
        url: The URL for the TRAPI API endpoint
        
    Returns:
        TODO: Implementation needed
    """
    try:
        return trapi_query(url)
    except Exception as e:
        raise McpError(ErrorData(INTERNAL_ERROR, f"TRAPI query error: {str(e)}")) from e
    
