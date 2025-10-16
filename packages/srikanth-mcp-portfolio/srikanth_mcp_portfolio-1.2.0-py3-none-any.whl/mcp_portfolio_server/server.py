#!/usr/bin/env python3
"""Portfolio MCP Server implementation."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("portfolio-mcp-server")

class PortfolioMCPServer:
    """MCP Server for portfolio data."""
    
    def __init__(self):
        self.server = Server("portfolio-server")
        self.portfolio_data: List[Dict[str, Any]] = []
        self.setup_handlers()
        self.load_portfolio_data()
    
    def load_portfolio_data(self):
        """Load portfolio data from JSON file."""
        try:
            # Try different possible paths for the data file
            possible_paths = [
                Path(__file__).parent.parent.parent.parent / "db" / "sample-data.json",
                Path(__file__).parent.parent / "db" / "sample-data.json",
                Path("db/sample-data.json"),
                Path("../db/sample-data.json"),
            ]
            
            data_path = None
            for path in possible_paths:
                if path.exists():
                    data_path = path
                    break
            
            if data_path:
                with open(data_path, 'r', encoding='utf-8') as f:
                    self.portfolio_data = json.load(f)
                logger.info(f"Loaded {len(self.portfolio_data)} portfolio items from {data_path}")
            else:
                logger.error("Could not find portfolio data file")
                self.portfolio_data = []
                
        except Exception as e:
            logger.error(f"Failed to load portfolio data: {e}")
            self.portfolio_data = []
    
    def setup_handlers(self):
        """Set up MCP request handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="search_portfolio",
                    description="Search through Srikanth's portfolio data by keywords, category, or content",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query to find relevant portfolio information"
                            },
                            "category": {
                                "type": "string",
                                "description": "Filter by specific category (e.g., 'Tech Stack', 'Experience', 'Education')"
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of results to return (default: 10)",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="get_portfolio_categories",
                    description="Get all available categories in the portfolio data",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                types.Tool(
                    name="get_portfolio_item",
                    description="Get a specific portfolio item by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "number",
                                "description": "The ID of the portfolio item to retrieve"
                            }
                        },
                        "required": ["id"]
                    }
                ),
                types.Tool(
                    name="get_contact_info",
                    description="Get all contact information for Srikanth",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                types.Tool(
                    name="get_tech_stack",
                    description="Get detailed information about Srikanth's technical skills and tools",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "description": "Filter by specific tech type (e.g., 'Programming Languages', 'Cloud Platforms')"
                            }
                        }
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls."""
            
            if name == "search_portfolio":
                return await self.search_portfolio(arguments)
            elif name == "get_portfolio_categories":
                return await self.get_portfolio_categories()
            elif name == "get_portfolio_item":
                return await self.get_portfolio_item(arguments)
            elif name == "get_contact_info":
                return await self.get_contact_info()
            elif name == "get_tech_stack":
                return await self.get_tech_stack(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def search_portfolio(self, args: dict) -> list[types.TextContent]:
        """Search portfolio data."""
        query = args.get("query", "").lower()
        category = args.get("category")
        limit = args.get("limit", 10)
        
        results = []
        for item in self.portfolio_data:
            # Filter by category if specified
            if category and item["category"].lower() != category.lower():
                continue
            
            # Search in title, description, and keywords
            searchable_text = " ".join([
                item["title"],
                item["description"],
                *item["keywords"]
            ]).lower()
            
            if query in searchable_text:
                results.append(item)
        
        # Limit results
        results = results[:limit]
        
        response = {
            "query": args.get("query"),
            "category": category or "all",
            "resultsCount": len(results),
            "results": results
        }
        
        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]
    
    async def get_portfolio_categories(self) -> list[types.TextContent]:
        """Get all portfolio categories."""
        categories = list(set(item["category"] for item in self.portfolio_data))
        
        response = {
            "categories": categories,
            "totalItems": len(self.portfolio_data)
        }
        
        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]
    
    async def get_portfolio_item(self, args: dict) -> list[types.TextContent]:
        """Get specific portfolio item by ID."""
        item_id = args.get("id")
        
        item = next((item for item in self.portfolio_data if item["id"] == item_id), None)
        
        if not item:
            raise ValueError(f"Portfolio item with ID {item_id} not found")
        
        return [types.TextContent(type="text", text=json.dumps(item, indent=2))]
    
    async def get_contact_info(self) -> list[types.TextContent]:
        """Get all contact information."""
        contact_items = [item for item in self.portfolio_data if item["category"] == "Contact"]
        
        response = {"contact": contact_items}
        
        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]
    
    async def get_tech_stack(self, args: dict) -> list[types.TextContent]:
        """Get tech stack information."""
        tech_type = args.get("type")
        
        tech_items = [item for item in self.portfolio_data if item["category"] == "Tech Stack"]
        
        if tech_type:
            tech_items = [item for item in tech_items 
                         if tech_type.lower() in item["title"].lower()]
        
        response = {
            "techStack": tech_items,
            "filterType": tech_type or "all"
        }
        
        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]


async def main():
    """Main entry point for the MCP server."""
    server_instance = PortfolioMCPServer()
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream, 
            write_stream, 
            NotificationOptions()
        )


if __name__ == "__main__":
    asyncio.run(main())