import re

with open("services/chat_service.py", "r") as f:
    content = f.read()

# We want to replace the whole # 8. Resolve or Escalate? block up to the end of the function.
# Let's find the start.
start_idx = content.find("        # 8. Resolve or Escalate?")
if start_idx != -1:
    end_idx = content.find("    # ------------------------------------------------------------------\n    # Escalation helper")
    
    new_block = """        # 8. Attempt RAG if resolve
        if post["action"] == "resolve":
            full_response, sources = await self.rag_engine.generate_response(user_message, search_results)
            
            if "INSUFFICIENT_DOCUMENTATION" not in full_response:
                # Regular RAG worked!
                yield {"type": "start"}
                # To simulate streaming, just yield the whole chunk
                yield {"type": "chunk", "content": full_response}
                
                msg = await self._add_message(
                    db, session_id, "assistant", full_response,
                    confidence_score=post["score"],
                    sources=sources
                )
                yield {
                    "type": "final",
                    "action": Action.resolve,
                    "sources": [SourceInfo(**s) for s in sources],
                    "message_id": str(msg.id)
                }
                return

        # 9. Fallback: Either post["action"] != "resolve" OR INSUFFICIENT_DOCUMENTATION
        fallback_prompt = (
            "Answer the following technical support or programming question based on your general knowledge. "
            "If you do not know the answer or are not highly confident, you MUST reply EXACTLY with 'I_DONT_KNOW'.\\n\\n"
            f"Question: {user_message}"
        )
        fallback_response = await self.rag_engine.llm_engine.generate_response([{"role": "user", "content": fallback_prompt}])
        
        if "I_DONT_KNOW" in fallback_response or "Mocked Response" in fallback_response:
            # Base LLM also doesn't know -> Escalate to ticket
            resp = await self._escalate(db, session_id, user_message, history, "high")
            yield {"type": "start"}
            yield {"type": "chunk", "content": resp.response, "is_final": True}
            yield {
                "type": "final",
                "action": Action.escalated,
                "ticket": resp.ticket,
                "message_id": resp.message_id
            }
            return
        else:
            # Base model knows! Add to KC
            import time
            import uuid
            new_source_id = f"fallback_{int(time.time())}"
            await self.rag_engine.add_documents(new_source_id, f"Auto-generated answer for: {user_message}", [fallback_response])
            
            yield {"type": "start"}
            yield {"type": "chunk", "content": fallback_response}
            
            fb_sources = [{
                "source_id": new_source_id,
                "title": "AI Fallback Knowledge",
                "chunk_excerpt": fallback_response[:200]
            }]
            
            msg = await self._add_message(
                db, session_id, "assistant", fallback_response,
                confidence_score=0.8,
                sources=fb_sources
            )
            yield {
                "type": "final",
                "action": Action.resolve,
                "sources": [SourceInfo(**s) for s in fb_sources],
                "message_id": str(msg.id)
            }
            return

"""
    new_content = content[:start_idx] + new_block + content[end_idx:]
    with open("services/chat_service.py", "w") as f:
        f.write(new_content)
    print("Fixed stream_message")
else:
    print("Could not find start idx")
