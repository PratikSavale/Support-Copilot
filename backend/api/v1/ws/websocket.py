"""
WebSocket Handler
Provides real-time streaming for chat responses.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime, timezone

from services.chat_service import ChatService
from services.confidence_service import ConfidenceService
from services.ticket_service import TicketService

router = APIRouter()

# Global service instances (initialized here or in main.py)
chat_service = ChatService()
confidence_service = ConfidenceService()
ticket_service = TicketService()

async def message_generator(session_id: str, user_message: str):
    """
    Generator that yields chunks of the response as they are generated.
    Enables streaming to the frontend.
    """
    # Send start signal
    yield json.dumps({
        "type": "start",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    
    try:
        # Process the message
        response = await chat_service.process_message(
            db=None,  # Will be passed via WebSocket auth or db dependency
            session_id=session_id,
            user_message=user_message,
        )
        
        # Stream the response text
        response_text = response.response
        chunk_size = 20  # Characters per chunk
        
        for i in range(0, len(response_text), chunk_size):
            chunk = response_text[i:i + chunk_size]
            yield json.dumps({
                "type": "chunk",
                "content": chunk,
                "is_final": i + chunk_size >= len(response_text),
            })
            await asyncio.sleep(0.05)  # Simulate typing effect
        
        # Send final response metadata
        yield json.dumps({
            "type": "final",
            "action": response.action,
            "sources": response.sources,
            "ticket": response.ticket,
            "message_id": response.message_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
    except Exception as e:
        yield json.dumps({
            "type": "error",
            "message": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time chat.
    
    Client sends: {"type": "message", "content": "user message"}
    Server sends: JSON events (start, chunk, final, error)
    """
    await websocket.accept()
    
    try:
        # We don't generate message on connect in this design unless we want to load history.
        # But per the plan, we just wait for user messages.
        
        while True:
            raw_message = await websocket.receive_text()
            client_message = json.loads(raw_message)
            
            if client_message.get("type") == "message":
                user_message = client_message.get("content", "")
                
                # Send response chunks
                async for event in message_generator(session_id, user_message):
                    await websocket.send_text(event)
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e),
            }))
        except:
            pass
