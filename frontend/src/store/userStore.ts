import { create } from 'zustand'
import axios from 'axios'
import { API_BASE_URL } from '../config/api'

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
  availableSources: { id: string; title?: string; url: string; status: string }[]
  selectedSources: string[] // Array of selected source IDs
  
  // Actions
  setSessionId: (id: string) => void
  addMessage: (message: Message) => void
  updateLastMessage: (content: string) => void
  setStreaming: (isStreaming: boolean) => void
  setHistoryLoading: (isLoading: boolean) => void
  setConnected: (isConnected: boolean) => void
  clearMessages: () => void
  setMessages: (messages: Message[]) => void
  fetchAvailableSources: () => Promise<void>
  toggleSourceSelection: (sourceId: string) => void
}

const api = axios.create({
  baseURL: API_BASE_URL,
})

export const useUserStore = create<UserState>((set) => ({
  sessionId: null,
  messages: [],
  isStreaming: false,
  isHistoryLoading: false,
  isConnected: true, // Default to true, update on error
  availableSources: [],
  selectedSources: [],

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

  fetchAvailableSources: async () => {
    try {
      const response = await api.get('/knowledge/sources')
      const sources = response.data.sources || response.data
      // Filter out only indexed/ready sources if needed, or show all
      set({ availableSources: sources })
    } catch (err) {
      console.error('Failed to load knowledge sources', err)
    }
  },

  toggleSourceSelection: (sourceId) => set((state) => {
    const isSelected = state.selectedSources.includes(sourceId)
    return {
      selectedSources: isSelected
        ? state.selectedSources.filter(id => id !== sourceId)
        : [...state.selectedSources, sourceId]
    }
  }),
}))
