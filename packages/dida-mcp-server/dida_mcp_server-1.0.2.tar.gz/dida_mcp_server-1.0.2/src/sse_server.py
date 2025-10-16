# # src/sse_server.py
# import asyncio
# import json
# import os
# from typing import Optional
# from fastapi import FastAPI, Request, HTTPException, Header
# from fastapi.responses import StreamingResponse
# from fastapi.middleware.cors import CORSMiddleware
# from sse_starlette.sse import EventSourceResponse
# from mcp.server import Server
# from mcp.types import Tool, TextContent
# from dotenv import load_dotenv
# import src.hotel_data as hotel_data

# load_dotenv()

# app = FastAPI(title="Dida MCP Server (SSE)")

# # Add CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Authentication
# AUTH_TOKEN = os.getenv("AUTH_TOKEN", "demo-token-123")


# def verify_token(authorization: Optional[str] = Header(None)):
#     """Verify bearer token."""
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Missing authorization header")
    
#     if not authorization.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Invalid authorization format")
    
#     token = authorization.replace("Bearer ", "")
#     if token != AUTH_TOKEN:
#         raise HTTPException(status_code=401, detail="Invalid token")
    
#     return token


# @app.get("/health")
# async def health():
#     """Health check endpoint."""
#     return {"status": "ok", "server": "dida-mcp-server"}


# @app.get("/")
# async def root():
#     """Root endpoint."""
#     return {
#         "name": "dida-mcp-server",
#         "version": "1.0.0",
#         "endpoints": {
#             "health": "/health",
#             "sse": "/sse"
#         }
#     }


# @app.get("/sse")
# async def sse_endpoint(request: Request, authorization: str = Header(None)):
#     """SSE endpoint for MCP communication."""
#     verify_token(authorization)
    
#     print(f"New SSE connection from {request.client.host}")
    
#     # SSE stream generator
#     async def event_generator():
#         try:
#             # Send endpoint info
#             yield {
#                 "event": "endpoint",
#                 "data": json.dumps({"endpoint": "/message"})
#             }
            
#             # Keep connection alive
#             while True:
#                 if await request.is_disconnected():
#                     print("Client disconnected")
#                     break
#                 await asyncio.sleep(30)  # Send keepalive every 30s
#                 yield {
#                     "event": "ping",
#                     "data": json.dumps({"time": asyncio.get_event_loop().time()})
#                 }
        
#         except asyncio.CancelledError:
#             print("Connection cancelled")
#         except Exception as e:
#             print(f"Error in event generator: {e}")
    
#     return EventSourceResponse(event_generator())


# @app.post("/message")
# async def message_endpoint(
#     request: Request,
#     authorization: str = Header(None)
# ):
#     """Handle MCP messages."""
#     verify_token(authorization)
    
#     body = await request.json()
#     print(f"Received message: {body.get('method')}")
    
#     # Create MCP server for this request
#     server = Server("dida-mcp-server")
    
#     # Handle different methods
#     method = body.get("method")
    
#     if method == "initialize":
#         return {
#             "jsonrpc": "2.0",
#             "id": body.get("id"),
#             "result": {
#                 "protocolVersion": "2024-11-05",
#                 "capabilities": {
#                     "tools": {}
#                 },
#                 "serverInfo": {
#                     "name": "dida-mcp-server",
#                     "version": "1.0.0"
#                 }
#             }
#         }
    
#     elif method == "tools/list":
#         return {
#             "jsonrpc": "2.0",
#             "id": body.get("id"),
#             "result": {
#                 "tools": [
#                     {
#                         "name": "search_hotels",
#                         "description": "Search for hotels",
#                         "inputSchema": {
#                             "type": "object",
#                             "properties": {
#                                 "city": {"type": "string"},
#                                 "max_price": {"type": "number"},
#                                 "min_rating": {"type": "number"}
#                             }
#                         }
#                     },
#                     {
#                         "name": "book_hotel",
#                         "description": "Book a hotel room",
#                         "inputSchema": {
#                             "type": "object",
#                             "properties": {
#                                 "hotel_id": {"type": "string"},
#                                 "guest_name": {"type": "string"},
#                                 "guest_email": {"type": "string"},
#                                 "check_in": {"type": "string"},
#                                 "check_out": {"type": "string"}
#                             },
#                             "required": ["hotel_id", "guest_name", "guest_email", "check_in", "check_out"]
#                         }
#                     },
#                     {
#                         "name": "get_hotel_reviews",
#                         "description": "Get hotel reviews",
#                         "inputSchema": {
#                             "type": "object",
#                             "properties": {
#                                 "hotel_id": {"type": "string"}
#                             },
#                             "required": ["hotel_id"]
#                         }
#                     }
#                 ]
#             }
#         }
    
#     elif method == "tools/call":
#         params = body.get("params", {})
#         name = params.get("name")
#         arguments = params.get("arguments", {})
        
#         try:
#             if name == "search_hotels":
#                 results = hotel_data.search_hotels(
#                     city=arguments.get("city"),
#                     max_price=arguments.get("max_price"),
#                     min_rating=arguments.get("min_rating")
#                 )
#                 return {
#                     "jsonrpc": "2.0",
#                     "id": body.get("id"),
#                     "result": {
#                         "content": [
#                             {
#                                 "type": "text",
#                                 "text": json.dumps(results, indent=2)
#                             }
#                         ]
#                     }
#                 }
            
#             elif name == "book_hotel":
#                 booking = hotel_data.book_hotel(
#                     hotel_id=arguments["hotel_id"],
#                     guest_name=arguments["guest_name"],
#                     guest_email=arguments["guest_email"],
#                     guest_phone=arguments.get("guest_phone", ""),
#                     check_in=arguments["check_in"],
#                     check_out=arguments["check_out"]
#                 )
#                 return {
#                     "jsonrpc": "2.0",
#                     "id": body.get("id"),
#                     "result": {
#                         "content": [
#                             {
#                                 "type": "text",
#                                 "text": f"✅ Booking Confirmed!\n\n{json.dumps(booking, indent=2)}"
#                             }
#                         ]
#                     }
#                 }
            
#             elif name == "get_hotel_reviews":
#                 reviews = hotel_data.get_hotel_reviews(arguments["hotel_id"])
#                 return {
#                     "jsonrpc": "2.0",
#                     "id": body.get("id"),
#                     "result": {
#                         "content": [
#                             {
#                                 "type": "text",
#                                 "text": json.dumps(reviews, indent=2)
#                             }
#                         ]
#                     }
#                 }
            
#             else:
#                 return {
#                     "jsonrpc": "2.0",
#                     "id": body.get("id"),
#                     "error": {
#                         "code": -32601,
#                         "message": f"Unknown tool: {name}"
#                     }
#                 }
        
#         except Exception as e:
#             return {
#                 "jsonrpc": "2.0",
#                 "id": body.get("id"),
#                 "error": {
#                     "code": -32603,
#                     "message": str(e)
#                 }
#             }
    
#     return {"status": "received"}


# def main():
#     """Run the SSE server."""
#     import uvicorn
#     port = int(os.getenv("PORT", 3000))
    
#     print(f"🚀 Dida MCP Server (SSE) starting on port {port}")
#     print(f"   Health: http://localhost:{port}/health")
#     print(f"   SSE: http://localhost:{port}/sse")
    
#     uvicorn.run(app, host="0.0.0.0", port=port)


# if __name__ == "__main__":
#     main()