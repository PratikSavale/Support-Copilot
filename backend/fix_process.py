import re

with open("services/chat_service.py", "r") as f:
    content = f.read()

start_idx = content.find("        # ── 6. HIGH → resolve ──────────────────────────────────────────")
if start_idx != -1:
    end_idx = content.find("    async def stream_message(")
    
    new_block = """        # ── 6. HIGH → resolve ──────────────────────────────────────────
        if post["action"] == "resolve":
            response_text, sources = await self.rag_engine.generate_response(
                user_message, search_results
            )
            
            if "INSUFFICIENT_DOCUMENTATION" not in response_text:
                msg = await self._add_message(
                    db, session_id, "assistant", response_text,
                    confidence_score=post["score"],
                    sources=sources,
                )
                return ChatResponse(
                    session_id=str(session_id),
                    message_id=str(msg.id),
                    response=response_text,
                    sources=[SourceInfo(**s) for s in sources],
                    action=Action.resolve,
                    ticket=None,
                )

        # ── 7. Fallback to base LLM ──────────────────────────────────────
        fallback_prompt = (
            "Answer the following technical support or programming question based on your general knowledge. "
            "If you do not know the answer or are not highly confident, you MUST reply EXACTLY with 'I_DONT_KNOW'.\\n\\n"
            f"Question: {user_message}"
        )
        fallback_response = await self.rag_engine.llm_engine.generate_response([{"role": "user", "content": fallback_prompt}])
        
        if "I_DONT_KNOW" in fallback_response or "Mocked Response" in fallback_response:
            return await self._escalate(
                db, session_id, user_message, history, "high"
            )
        else:
            import time
            import uuid
            new_source_id = f"fallback_{int(time.time())}"
            await self.rag_engine.add_documents(new_source_id, f"Auto-generated answer for: {user_message}", [fallback_response])
            
            fb_sources = [{
                "source_id": new_source_id,
                "title": "AI Fallback Knowledge",
                "chunk_excerpt": fallback_response[:200]
            }]
            
            msg = await self._add_message(
                db, session_id, "assistant", fallback_response,
                confidence_score=0.8,
                sources=fb_sources,
            )
            return ChatResponse(
                session_id=str(session_id),
                message_id=str(msg.id),
                response=fallback_response,
                sources=[SourceInfo(**s) for s in fb_sources],
                action=Action.resolve,
                ticket=None,
            )

"""
    new_content = content[:start_idx] + new_block + content[end_idx:]
    with open("services/chat_service.py", "w") as f:
        f.write(new_content)
    print("Fixed process_message")
else:
    print("Could not find start idx")
