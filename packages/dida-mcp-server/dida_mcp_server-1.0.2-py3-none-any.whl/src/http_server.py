# src/http_server.py
import json
import os
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.types import Tool, TextContent
from dotenv import load_dotenv
import src.hotel_data as hotel_data

load_dotenv()

app = FastAPI(title="Dida MCP Server (HTTP)")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "demo-token-123")


def verify_token(authorization: Optional[str] = Header(None)):
    """Verify bearer token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token = authorization.replace("Bearer ", "")
    if token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return token


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "server": "dida-mcp-server"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "dida-mcp-server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "initialize": "/initialize",
            "tools": "/tools",
            "search_hotels": "/search_hotels",
            "book_hotel": "/book_hotel",
            "get_hotel_reviews": "/get_hotel_reviews"
        }
    }


@app.post("/initialize")
async def initialize(authorization: str = Header(None)):
    """Initialize MCP connection."""
    verify_token(authorization)
    
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "dida-mcp-server",
            "version": "1.0.0"
        }
    }


@app.get("/tools")
async def list_tools(authorization: str = Header(None)):
    """List available tools."""
    verify_token(authorization)
    
    return {
        "tools": [
            {
                "name": "search_hotels",
                "description": "Search for hotels",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "max_price": {"type": "number"},
                        "min_rating": {"type": "number"}
                    }
                }
            },
            {
                "name": "book_hotel",
                "description": "Book a hotel room",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "hotel_id": {"type": "string"},
                        "guest_name": {"type": "string"},
                        "guest_email": {"type": "string"},
                        "check_in": {"type": "string"},
                        "check_out": {"type": "string"}
                    },
                    "required": ["hotel_id", "guest_name", "guest_email", "check_in", "check_out"]
                }
            },
            {
                "name": "get_hotel_reviews",
                "description": "Get hotel reviews",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "hotel_id": {"type": "string"}
                    },
                    "required": ["hotel_id"]
                }
            }
        ]
    }


@app.post("/search_hotels")
async def search_hotels(
    request: Request,
    authorization: str = Header(None)
):
    """Search for hotels."""
    verify_token(authorization)
    
    try:
        body = await request.json()
        results = hotel_data.search_hotels(
            city=body.get("city"),
            max_price=body.get("max_price"),
            min_rating=body.get("min_rating")
        )
        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/book_hotel")
async def book_hotel(
    request: Request,
    authorization: str = Header(None)
):
    """Book a hotel room."""
    verify_token(authorization)
    
    try:
        body = await request.json()
        
        # Validate required fields
        required_fields = ["hotel_id", "guest_name", "guest_email", "check_in", "check_out"]
        for field in required_fields:
            if field not in body:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        booking = hotel_data.book_hotel(
            hotel_id=body["hotel_id"],
            guest_name=body["guest_name"],
            guest_email=body["guest_email"],
            guest_phone=body.get("guest_phone", ""),
            check_in=body["check_in"],
            check_out=body["check_out"]
        )
        return {
            "success": True,
            "message": "Booking confirmed!",
            "data": booking
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get_hotel_reviews")
async def get_hotel_reviews(
    request: Request,
    authorization: str = Header(None)
):
    """Get hotel reviews."""
    verify_token(authorization)
    
    try:
        body = await request.json()
        
        if "hotel_id" not in body:
            raise HTTPException(status_code=400, detail="Missing required field: hotel_id")
        
        reviews = hotel_data.get_hotel_reviews(body["hotel_id"])
        return {
            "success": True,
            "data": reviews
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Legacy MCP message endpoint for backward compatibility
@app.post("/message")
async def message_endpoint(
    request: Request,
    authorization: str = Header(None)
):
    """Handle MCP messages (legacy compatibility)."""
    verify_token(authorization)
    
    body = await request.json()
    print(f"Received legacy MCP message: {body.get('method')}")
    
    method = body.get("method")
    
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "dida-mcp-server",
                    "version": "1.0.0"
                }
            }
        }
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "result": {
                "tools": [
                    {
                        "name": "search_hotels",
                        "description": "Search for hotels",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "city": {"type": "string"},
                                "max_price": {"type": "number"},
                                "min_rating": {"type": "number"}
                            }
                        }
                    },
                    {
                        "name": "book_hotel",
                        "description": "Book a hotel room",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "hotel_id": {"type": "string"},
                                "guest_name": {"type": "string"},
                                "guest_email": {"type": "string"},
                                "check_in": {"type": "string"},
                                "check_out": {"type": "string"}
                            },
                            "required": ["hotel_id", "guest_name", "guest_email", "check_in", "check_out"]
                        }
                    },
                    {
                        "name": "get_hotel_reviews",
                        "description": "Get hotel reviews",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "hotel_id": {"type": "string"}
                            },
                            "required": ["hotel_id"]
                        }
                    }
                ]
            }
        }
    
    elif method == "tools/call":
        params = body.get("params", {})
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if name == "search_hotels":
                results = hotel_data.search_hotels(
                    city=arguments.get("city"),
                    max_price=arguments.get("max_price"),
                    min_rating=arguments.get("min_rating")
                )
                return {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(results, indent=2)
                            }
                        ]
                    }
                }
            
            elif name == "book_hotel":
                booking = hotel_data.book_hotel(
                    hotel_id=arguments["hotel_id"],
                    guest_name=arguments["guest_name"],
                    guest_email=arguments["guest_email"],
                    guest_phone=arguments.get("guest_phone", ""),
                    check_in=arguments["check_in"],
                    check_out=arguments["check_out"]
                )
                return {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"✅ Booking Confirmed!\n\n{json.dumps(booking, indent=2)}"
                            }
                        ]
                    }
                }
            
            elif name == "get_hotel_reviews":
                reviews = hotel_data.get_hotel_reviews(arguments["hotel_id"])
                return {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(reviews, indent=2)
                            }
                        ]
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {name}"
                    }
                }
        
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    return {"status": "received"}


def main():
    """Run the HTTP server."""
    import uvicorn
    port = int(os.getenv("PORT", 3001))
    
    print(f"🚀 Dida MCP Server (HTTP) starting on port {port}")
    print(f"   Health: http://localhost:{port}/health")
    print(f"   Tools: http://localhost:{port}/tools")
    print(f"   Search Hotels: http://localhost:{port}/search_hotels")
    print(f"   Book Hotel: http://localhost:{port}/book_hotel")
    print(f"   Get Reviews: http://localhost:{port}/get_hotel_reviews")
    
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
