"""
WebSocket Handler
Provides real-time streaming for chat responses.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime, timezone

from config.database import async_session_factory
from services.service_factory import get_chat_service

router = APIRouter()

@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time chat.
    
    Client sends: {"type": "message", "content": "user message"}
    Server sends: JSON events (start, chunk, final, error)
    """
    await websocket.accept()
    chat_service = get_chat_service()
    
    try:
        while True:
            raw_message = await websocket.receive_text()
            client_message = json.loads(raw_message)
            
            if client_message.get("type") == "message":
                user_message = client_message.get("content", "")
                
                async with async_session_factory() as db:
                    try:
                        async for event in chat_service.stream_message(
                            db=db,
                            session_id=session_id,
                            user_message=user_message,
                        ):
                            # Add timestamp if missing
                            if "timestamp" not in event:
                                event["timestamp"] = datetime.now(timezone.utc).isoformat()
                            
                            # Handle serialization of Pydantic/Enum types
                            if event["type"] == "final":
                                if "action" in event and hasattr(event["action"], "value"):
                                    event["action"] = event["action"].value
                                if "sources" in event:
                                    event["sources"] = [
                                        s.model_dump() if hasattr(s, "model_dump") else s 
                                        for s in event["sources"]
                                    ]
                                if "ticket" in event and event["ticket"]:
                                    event["ticket"] = (
                                        event["ticket"].model_dump() 
                                        if hasattr(event["ticket"], "model_dump") 
                                        else event["ticket"]
                                    )

                            await websocket.send_text(json.dumps(event))
                        
                        await db.commit()
                        
                    except Exception as e:
                        await db.rollback()
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": str(e),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }))
                    
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
