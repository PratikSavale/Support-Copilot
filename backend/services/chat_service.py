"""
Chat Service Stub
"""

class ChatResponse:
    def __init__(self, response, action, sources, ticket, message_id):
        self.response = response
        self.action = action
        self.sources = sources
        self.ticket = ticket
        self.message_id = message_id

class ChatService:
    async def process_message(self, db, session_id, user_message):
        # Stub implementation
        return ChatResponse(
            response=f"Mock response for: {user_message}",
            action="resolve",
            sources=[],
            ticket=None,
            message_id="mock-message-id"
        )
