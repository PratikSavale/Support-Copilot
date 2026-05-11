import { useEffect, useRef, useCallback } from 'react'
import { useUserStore } from '../store/userStore'

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/chat/ws'

// Singleton state to survive React re-renders and StrictMode
let globalSocket: WebSocket | null = null
let globalSessionId: string | null = null

export const useWebSocket = (sessionId: string | null) => {
  const { addMessage, updateLastMessage, setStreaming, setConnected } = useUserStore()
  
  // Use a ref to keep track of the current store functions (avoids stale closures)
  const storeRef = useRef({ addMessage, updateLastMessage, setStreaming, setConnected })
  useEffect(() => {
    storeRef.current = { addMessage, updateLastMessage, setStreaming, setConnected }
  }, [addMessage, updateLastMessage, setStreaming, setConnected])

  const connect = useCallback(() => {
    if (!sessionId) return
    
    // If we already have a socket for THIS session and it's alive, don't do anything
    if (globalSocket && globalSessionId === sessionId) {
      if (globalSocket.readyState <= 1) return
    }

    // Clean up any old mismatched socket
    if (globalSocket) {
      globalSocket.close()
      globalSocket = null
    }

    console.log('🌐 [WebSocket] Connecting to:', `${WS_BASE_URL}/${sessionId}`)
    globalSessionId = sessionId
    const ws = new WebSocket(`${WS_BASE_URL}/${sessionId}`)
    globalSocket = ws

    ws.onopen = () => {
      console.log('✅ [WebSocket] Connected')
      storeRef.current.setConnected(true)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('📥 [WebSocket] Message:', data.type)
      
      switch (data.type) {
        case 'start':
          storeRef.current.setStreaming(true)
          storeRef.current.addMessage({
            id: Date.now().toString(),
            role: 'assistant',
            content: '',
            timestamp: new Date().toISOString(),
          })
          break
        
        case 'chunk':
          storeRef.current.updateLastMessage(data.content)
          break
        
        case 'final':
          storeRef.current.setStreaming(false)
          if (data.action || data.suggestions) {
             useUserStore.setState((state) => {
               const newMessages = [...state.messages]
               if (newMessages.length > 0) {
                 const lastIdx = newMessages.length - 1
                 newMessages[lastIdx] = {
                   ...newMessages[lastIdx],
                   action: data.action,
                   suggestions: data.suggestions
                 }
               }
               return { messages: newMessages }
             })
          }
          break
        
        case 'error':
          storeRef.current.setStreaming(false)
          console.error('❌ [WebSocket] Error:', data.message)
          break
      }
    }

    ws.onclose = () => {
      console.log('🔌 [WebSocket] Disconnected')
      storeRef.current.setStreaming(false)
      storeRef.current.setConnected(false)
      globalSocket = null
    }

    ws.onerror = (error) => {
      console.error('⚠️ [WebSocket] Socket Error:', error)
      storeRef.current.setStreaming(false)
      storeRef.current.setConnected(false)
    }
  }, [sessionId])

  useEffect(() => {
    connect()
    // We DON'T close the globalSocket on unmount here to avoid StrictMode issues.
    // It will be closed if the sessionId actually changes.
  }, [connect])

  const sendMessage = (content: string) => {
    if (globalSocket?.readyState === WebSocket.OPEN) {
      console.log('📤 [WebSocket] Sending:', content)
      const userMessage = {
        id: Date.now().toString(),
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      }
      storeRef.current.addMessage(userMessage as any)
      globalSocket.send(JSON.stringify({ 
        type: 'message',
        content 
      }))
    } else {
      console.error('🚫 [WebSocket] Cannot send. State:', globalSocket?.readyState ?? 'NULL')
    }
  }

  return { sendMessage }
}
