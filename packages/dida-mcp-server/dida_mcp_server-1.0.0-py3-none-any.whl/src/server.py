# src/server.py - COMPLETE WORKING VERSION
import asyncio
import json
import sys
from typing import Any

# Make sure mcp is installed
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError as e:
    print(f"Error importing mcp: {e}", file=sys.stderr)
    print("Try: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Import hotel data
try:
    import src.hotel_data as hotel_data
except ImportError:
    try:
        import hotel_data
    except ImportError as e:
        print(f"Error importing hotel_data: {e}", file=sys.stderr)
        sys.exit(1)

# Create server instance
server = Server("dida-mcp-server")

print("Server instance created", file=sys.stderr)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    print("list_tools called", file=sys.stderr)
    return [
        Tool(
            name="search_hotels",
            description="Search for hotels based on various criteria like location, price, rating, and amenities. Returns detailed hotel information including 12+ fields.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name to search hotels in (e.g., 'New York', 'Miami')"
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price per night in USD"
                    },
                    "min_rating": {
                        "type": "number",
                        "description": "Minimum hotel rating (0-5)"
                    },
                    "amenities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Required amenities (e.g., ['WiFi', 'Pool', 'Gym'])"
                    },
                    "available_only": {
                        "type": "boolean",
                        "description": "Show only available hotels",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="book_hotel",
            description="Book a hotel room with guest information and dates",
            inputSchema={
                "type": "object",
                "properties": {
                    "hotel_id": {
                        "type": "string",
                        "description": "Hotel ID (e.g., 'H001')"
                    },
                    "guest_name": {
                        "type": "string",
                        "description": "Guest's full name"
                    },
                    "guest_email": {
                        "type": "string",
                        "description": "Guest's email address"
                    },
                    "guest_phone": {
                        "type": "string",
                        "description": "Guest's phone number"
                    },
                    "check_in": {
                        "type": "string",
                        "description": "Check-in date (YYYY-MM-DD)"
                    },
                    "check_out": {
                        "type": "string",
                        "description": "Check-out date (YYYY-MM-DD)"
                    }
                },
                "required": ["hotel_id", "guest_name", "guest_email", "check_in", "check_out"]
            }
        ),
        Tool(
            name="get_hotel_reviews",
            description="Get customer reviews for a specific hotel",
            inputSchema={
                "type": "object",
                "properties": {
                    "hotel_id": {
                        "type": "string",
                        "description": "Hotel ID (e.g., 'H001')"
                    }
                },
                "required": ["hotel_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    print(f"call_tool: {name} with {arguments}", file=sys.stderr)
    
    try:
        if name == "search_hotels":
            results = hotel_data.search_hotels(
                city=arguments.get("city"),
                max_price=arguments.get("max_price"),
                min_rating=arguments.get("min_rating"),
                amenities=arguments.get("amenities"),
                available_only=arguments.get("available_only", True)
            )
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]
        
        elif name == "book_hotel":
            booking = hotel_data.book_hotel(
                hotel_id=arguments["hotel_id"],
                guest_name=arguments["guest_name"],
                guest_email=arguments["guest_email"],
                guest_phone=arguments.get("guest_phone", ""),
                check_in=arguments["check_in"],
                check_out=arguments["check_out"]
            )
            return [TextContent(
                type="text",
                text=f"✅ Booking Confirmed!\n\n{json.dumps(booking, indent=2)}"
            )]
        
        elif name == "get_hotel_reviews":
            reviews = hotel_data.get_hotel_reviews(arguments["hotel_id"])
            return [TextContent(
                type="text",
                text=json.dumps(reviews, indent=2)
            )]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        print(f"Error in call_tool: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Run the server using stdio transport."""
    print("🚀 Dida MCP Server starting...", file=sys.stderr)
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            print("✅ STDIO transport ready", file=sys.stderr)
            print("✅ Dida MCP Server running on stdio", file=sys.stderr)
            
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        print(f"❌ Server error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    print("Starting main()...", file=sys.stderr)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)