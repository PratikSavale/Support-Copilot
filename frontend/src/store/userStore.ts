import { create } from 'zustand'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  action?: 'resolve' | 'clarification' | 'escalated'
  suggestions?: string[]
}

interface UserState {
  sessionId: string | null
  messages: Message[]
  isStreaming: boolean
  isHistoryLoading: boolean
  isConnected: boolean
  
  // Actions
  setSessionId: (id: string) => void
  addMessage: (message: Message) => void
  updateLastMessage: (content: string) => void
  setStreaming: (isStreaming: boolean) => void
  setHistoryLoading: (isLoading: boolean) => void
  setConnected: (isConnected: boolean) => void
  clearMessages: () => void
  setMessages: (messages: Message[]) => void
}

export const useUserStore = create<UserState>((set) => ({
  sessionId: null,
  messages: [],
  isStreaming: false,
  isHistoryLoading: false,
  isConnected: true, // Default to true, update on error

  setSessionId: (id) => set({ sessionId: id }),
  
  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message] 
  })),

  updateLastMessage: (content) => set((state) => {
    const newMessages = [...state.messages]
    if (newMessages.length > 0) {
      const lastMessage = newMessages[newMessages.length - 1]
      if (lastMessage.role === 'assistant') {
        newMessages[newMessages.length - 1] = { 
          ...lastMessage, 
          content: lastMessage.content + content 
        }
      }
    }
    return { messages: newMessages }
  }),

  setStreaming: (isStreaming) => set({ isStreaming }),
  
  setHistoryLoading: (isLoading) => set({ isHistoryLoading: isLoading }),

  setConnected: (isConnected) => set({ isConnected }),

  clearMessages: () => set({ messages: [] }),

  setMessages: (messages) => set({ messages }),
}))
