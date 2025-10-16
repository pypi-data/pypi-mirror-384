# server.py
# This unified server works for both local agent and MCP registry publishing

import logging
import json
import os
import sys
import io
import datetime
from pathlib import Path
from typing import Optional, Any
from arcgis.gis import GIS
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

# --- Professional Logging Setup ---
def setup_unicode_logging():
    Path("logs").mkdir(exist_ok=True)
    logger = logging.getLogger('ArcGIS_MCP_Server')
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Only add console handler if not running as a tool
    if os.getenv("MCP_RUNNING_AS_TOOL") != "true":
        try:
            if sys.platform.startswith('win'):
                handler = logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace'))
            else:
                handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        except (TypeError, ValueError):
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    
    file_handler = logging.FileHandler('logs/arcgis_server.log', mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_unicode_logging()
mcp = FastMCP(name="arcgis-mcp-server")

# --- Core Logic: Secure ArcGIS Connection with Token Support ---
def connect_to_arcgis() -> GIS:
    """
    Establishes a secure connection to ArcGIS Portal/Online.
    Supports both token-based (for ChatGPT/external clients) and username/password auth.
    """
    portal_url = os.getenv('ARCGIS_URL')
    token = os.getenv('ARCGIS_TOKEN')
    username = os.getenv('ARCGIS_USERNAME')
    password = os.getenv('ARCGIS_PASSWORD')
    
    try:
        logger.info(f"Attempting to connect to portal: {portal_url}...")
        
        # Priority 1: Token-based authentication (for external clients like ChatGPT)
        if portal_url and token:
            gis = GIS(portal_url, token=token)
            logger.info(f"Successfully connected via token to {gis.properties.portalName}.")
        # Priority 2: Username/Password authentication (for local agent)
        elif portal_url and username and password:
            gis = GIS(portal_url, username, password)
            logger.info(f"Successfully connected as '{username}'.")
        else:
            raise ConnectionError("ArcGIS credentials (Token or User/Pass) were not provided in the environment.")
        
        return gis
    except Exception as e:
        logger.error(f"Portal connection failed: {str(e)}")
        raise ConnectionError(f"Portal connection failed: {str(e)}")

# --- Main Search Tool ---
@mcp.tool(
    name="search_arcgis_content",
    description="Searches a connected ArcGIS Portal or ArcGIS Online organization for content such as feature layers, web maps, dashboards, or other GIS items. Use this to find, search for, or look up geographic data or maps."
)
def search_content(
    exact_name: Optional[str] = None,
    query: Optional[str] = None,
    item_type: Optional[str] = None,
    owner: Optional[str] = None,
    tags: Optional[Any] = None,
    created_after: Optional[str] = None,
    max_results: int = 10,
    sort_by: str = "relevance",
    organization_filter: bool = False
) -> str:
    """
    Searches for content in the authenticated ArcGIS environment.
    
    Args:
        exact_name: Exact title to search for
        query: Keywords to search in titles, tags, descriptions
        item_type: Type of item (e.g., "Feature Service", "Web Map")
        owner: Username of content owner, or "me" for current user, "org" for organization
        tags: Tags to filter by
        created_after: Date filter (ISO format)
        max_results: Maximum number of results to return
        sort_by: Sort field ("relevance", "modified", "created")
        organization_filter: Whether to search only within organization
    
    Returns:
        JSON string with search results
    """
    operation_id = f"search_{int(datetime.datetime.now().timestamp())}"
    logger.info(f"[{operation_id}] Starting search operation")
    
    try:
        gis = connect_to_arcgis()
        
        # Handle "feature layer" -> "Feature Service" conversion
        if item_type and item_type.lower().strip() == 'feature layer':
            item_type = 'Feature Service'
        
        # Build query components
        query_components = []
        
        if exact_name:
            query_components.append(f'title:"{exact_name.strip()}"')
        
        if query:
            query_components.append(f'(title:{query}* OR tags:{query}* OR description:{query}*)')
        
        if item_type:
            query_components.append(f'type:"{item_type}"')
        
        if owner:
            if owner.lower() == 'me' and gis.users.me:
                query_components.append(f'owner:{gis.users.me.username}')
            elif owner.lower() in ['org', 'organization']:
                query_components.append(f'orgid:{gis.properties.id}')
            else:
                query_components.append(f'owner:"{owner}"')
        
        # Construct final query
        final_query = ' AND '.join(query_components) if query_components else '*'
        logger.info(f"[{operation_id}] Executing search with query: {final_query}")
        
        # Execute search
        results = gis.content.search(
            query=final_query,
            max_items=max_results,
            sort_field=sort_by,
            outside_org=not organization_filter
        )
        
        # Format results
        formatted_results = []
        for item in results:
            # Clean description/snippet
            description = item.description or item.snippet or ""
            clean_desc = BeautifulSoup(description, "html.parser").get_text(separator=' ').strip()[:300]
            
            formatted_results.append({
                "title": item.title,
                "type": item.type,
                "owner": item.owner,
                "summary": clean_desc,
                "tags": item.tags,
                "url": item.homepage or f"{gis.url}/home/item.html?id={item.id}",
                "id": item.id
            })
        
        logger.info(f"[{operation_id}] Found {len(formatted_results)} items")
        
        return json.dumps({
            "status": "success",
            "operation_id": operation_id,
            "results": formatted_results,
            "count": len(formatted_results)
        }, default=str)
        
    except ConnectionError as e:
        logger.error(f"[{operation_id}] Connection error: {str(e)}")
        return json.dumps({
            "status": "error",
            "operation_id": operation_id,
            "message": "Could not connect to ArcGIS. Please ensure you have authenticated."
        })
    except Exception as e:
        logger.error(f"[{operation_id}] Unexpected error: {str(e)}", exc_info=True)
        return json.dumps({
            "status": "error",
            "operation_id": operation_id,
            "error": {
                "type": type(e).__name__,
                "message": str(e)
            }
        })

# --- Server Initialization Functions (The key to unification) ---
def run_server():
    """Returns the MCP server instance (for local agent use)"""
    logger.info("[SUCCESS] ArcGIS MCP Server instance is ready for agent.")
    return mcp

def run_server_main():
    """Runs the MCP server in standalone mode (for MCP registry use)"""
    logger.info("[SUCCESS] ArcGIS MCP Server is starting in standalone mode...")
    mcp.run()

if __name__ == "__main__":
    run_server_main()