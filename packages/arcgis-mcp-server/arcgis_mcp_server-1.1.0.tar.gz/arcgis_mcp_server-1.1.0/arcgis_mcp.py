# mcp_server/server.py

import logging, json, os, sys, io, datetime
from pathlib import Path
from typing import Optional, Any
from arcgis.gis import GIS
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

def setup_unicode_logging():
    Path("logs").mkdir(exist_ok=True)
    logger = logging.getLogger('ArcGIS_MCP_Server')
    if logger.hasHandlers(): logger.handlers.clear()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    if os.getenv("MCP_RUNNING_AS_TOOL") != "true":
        try:
            handler = logging.StreamHandler(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace'))
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

def connect_to_arcgis() -> GIS:
    """
    Establishes a secure connection to ArcGIS. This is the final, unified logic.
    It prioritizes a secure token (for GPT) and falls back to user/pass (for the local agent).
    """
    portal_url = os.getenv('ARCGIS_URL')
    token = os.getenv('ARCGIS_TOKEN')
    username = os.getenv('ARCGIS_USERNAME')
    password = os.getenv('ARCGIS_PASSWORD')
    
    try:
        logger.info(f"Attempting to connect to portal: {portal_url}...")
        # --- THIS IS THE KEY ENHANCEMENT ---
        if portal_url and token:
            gis = GIS(portal_url, token=token)
            logger.info(f"Successfully connected via token to {gis.properties.portalName}.")
        elif portal_url and username and password:
            gis = GIS(portal_url, username, password)
            logger.info(f"Successfully connected as '{username}'.")
        else:
            raise ConnectionError("ArcGIS credentials (Token or User/Pass) were not provided in the environment.")
        return gis
    except Exception as e:
        raise ConnectionError(f"Portal connection failed: {str(e)}")

# --- Your powerful tool definition remains the same ---
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
    operation_id = f"search_{int(datetime.datetime.now().timestamp())}"
    try:
        gis = connect_to_arcgis()
        if item_type and item_type.lower().strip() == 'feature layer':
            item_type = 'Feature Service'
        query_components = []
        if exact_name: query_components.append(f'title:"{exact_name.strip()}"')
        if query: query_components.append(f'(title:{query}* OR tags:{query}* OR description:{query}*)')
        if item_type: query_components.append(f'type:"{item_type}"')
        if owner:
            if owner.lower() == 'me' and gis.users.me: query_components.append(f'owner:{gis.users.me.username}')
            elif owner.lower() in ['org', 'organization']: query_components.append(f'orgid:{gis.properties.id}')
            else: query_components.append(f'owner:"{owner}"')
        final_query = ' AND '.join(query_components) if query_components else '*'
        results = gis.content.search(query=final_query, max_items=max_results, sort_field=sort_by, outside_org=not organization_filter)
        formatted_results = [{"title": item.title, "type": item.type, "owner": item.owner, "summary": BeautifulSoup(item.description or item.snippet or "", "html.parser").get_text(separator=' ').strip()[:300], "tags": item.tags, "url": item.homepage or f"{gis.url}/home/item.html?id={item.id}"} for item in results]
        return json.dumps({"status": "success", "operation_id": operation_id, "results": formatted_results}, default=str)
    except ConnectionError as e:
        return json.dumps({"status": "error", "message": "Could not connect to ArcGIS. Please ensure the user has authenticated."})
    except Exception as e:
        return json.dumps({"status": "error", "error": {"type": type(e).__name__, "message": str(e)}})

def run_server():
    return mcp

def run_server_main():
    mcp.run()

if __name__ == "__main__":
    run_server_main()

