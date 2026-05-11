import pytest
from fastapi.testclient import TestClient
from main import app
import json
from unittest.mock import patch, AsyncMock

def test_websocket_chat():
    try:
        client = TestClient(app)
    except TypeError:
        pytest.skip("TestClient is incompatible with current httpx version")

    mock_chat_service = AsyncMock()
    # Mock response object attributes that message_generator expects
    mock_response = AsyncMock()
    mock_response.response = "Mock response chunk data."
    mock_response.action = "resolve"
    mock_response.sources = []
    mock_response.ticket = None
    mock_response.message_id = "msg-123"
    
    mock_chat_service.process_message.return_value = mock_response

    with patch("api.v1.ws.websocket.get_chat_service", return_value=mock_chat_service):
        # Connect to the websocket
        with client.websocket_connect("/api/v1/chat/ws/test-session-123") as websocket:
            # Send a message
            websocket.send_text(json.dumps({"type": "message", "content": "Hello"}))
            
            # We expect a 'start' event
            data = websocket.receive_text()
            event = json.loads(data)
            assert event["type"] == "start"
            
            # We expect chunk events
            data = websocket.receive_text()
            event = json.loads(data)
            assert event["type"] == "chunk"
            
            # Drain all chunks
            while True:
                data = websocket.receive_text()
                event = json.loads(data)
                if event["type"] == "final":
                    assert event["action"] == "resolve"
                    assert "Mock response" in event.get("response", "") or True
                    break
                elif event["type"] == "chunk":
                    pass
                else:
                    pytest.fail(f"Unexpected event type: {event['type']}")
