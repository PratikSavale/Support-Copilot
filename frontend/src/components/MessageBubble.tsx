import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Bot,
  User,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  BrainCircuit,
  ExternalLink,
  ThumbsUp,
  ThumbsDown,
  Loader2
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Message } from '../store/userStore'
import { useUserStore } from '../store/userStore'
import { ClarificationChips } from './ClarificationChips'
import { useWebSocket } from '../hooks/useWebSocket'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '@/config/api'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { SourceChips, SourceDetailPanel } from './SourceChipPanel'

interface MessageBubbleProps {
  message: Message
}

export const MessageBubble = ({ message }: MessageBubbleProps) => {
  const isAI = message.role === 'assistant'
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const { sendMessage } = useWebSocket(sessionId || null)
  const [activePanelIdx, setActivePanelIdx] = useState<number | null>(null)
  const { messages } = useUserStore()

  // Feedback & Escalation states
  const [feedback, setFeedback] = useState<'none' | 'liked' | 'disliked'>('none')
  const [isEscating, setIsEscating] = useState(false)
  const [escalationResult, setEscalationResult] = useState<any>(null)

  // Find the user query that triggered this AI answer
  const userQuery = (() => {
    const idx = messages.findIndex(m => m.id === message.id)
    if (idx > 0 && messages[idx - 1].role === 'user') {
      return messages[idx - 1].content
    }
    return ''
  })()

  // Classify answer type
  const hasSources = isAI && message.sources && message.sources.length > 0
  const isGeminiFallback = hasSources && message.sources!.every(s => s.title === 'AI Fallback Knowledge')
  const isRagHit = hasSources && !isGeminiFallback
  const isEscalated = isAI && message.action === 'escalated'

  // Safe timestamp parse
  const displayTime = (() => {
    const d = new Date(message.timestamp)
    return isNaN(d.getTime())
      ? new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  })()

  const handleFeedback = async (status: 'success' | 'failed') => {
    if (!sessionId || !message.id) return
    try {
      await api.post(`/chat/sessions/${sessionId}/messages/${message.id}/feedback`, { status })
      setFeedback(status === 'success' ? 'liked' : 'disliked')
    } catch (err) {
      console.error('Failed to submit message feedback:', err)
    }
  }

  const handleEscalate = async () => {
    if (!sessionId) return
    setIsEscating(true)
    try {
      const response = await api.post('/tickets/escalate', { session_id: sessionId })
      setEscalationResult(response.data)
    } catch (err) {
      console.error('Failed to escalate session:', err)
    } finally {
      setIsEscating(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className={cn(
        "flex w-full gap-4 mb-6",
        isAI ? "justify-start" : "justify-end"
      )}
    >
      {isAI && (
        <div className="w-8 h-8 rounded-lg bg-[#ffffff] border border-[#e0e0e0] flex items-center justify-center flex-shrink-0 mt-1 shadow-sm">
          <Bot className="w-5 h-5 text-[#0f62fe]" />
        </div>
      )}

      <div className="flex flex-col gap-1 max-w-[80%] min-w-0">
        <div
          className={cn(
            "px-5 py-3.5 rounded-2xl relative transition-all",
            isAI 
              ? "bg-white border border-[#e0e0e0] text-[#161616] shadow-sm" 
              : "bg-[#0f62fe] text-white shadow-md shadow-[#0f62fe]/20"
          )}
        >
          <div className={cn(
            "text-sm leading-relaxed prose prose-sm max-w-none text-[#161616] break-words overflow-x-auto",
            "prose-p:leading-relaxed prose-pre:bg-[#f4f4f4] prose-pre:border prose-pre:border-[#e0e0e0] prose-pre:overflow-x-auto prose-p:text-[#161616] prose-strong:text-[#161616]",
            "prose-headings:text-[#161616] prose-headings:font-semibold prose-headings:mt-4 prose-headings:mb-2",
            "prose-a:text-[#0f62fe] hover:prose-a:text-[#0f62fe]/80",
            "prose-code:text-[#0f62fe] prose-code:bg-[#f4f4f4] prose-code:px-1 prose-code:rounded prose-code:before:content-none prose-code:after:content-none",
            !isAI && "prose-headings:text-white prose-p:text-white prose-strong:text-white prose-code:text-white prose-code:bg-black/20"
          )}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
            {!message.content && isAI && (
              <div className="flex gap-1 items-center py-2">
                <span className="w-1.5 h-1.5 bg-[#0f62fe] rounded-full animate-bounce [animation-delay:-0.3s]" />
                <span className="w-1.5 h-1.5 bg-[#0f62fe] rounded-full animate-bounce [animation-delay:-0.15s]" />
                <span className="w-1.5 h-1.5 bg-[#0f62fe] rounded-full animate-bounce" />
              </div>
            )}
          </div>

          {/* Action & Feedback Indicators */}
          {isAI && message.action && (
            <div className="mt-3 pt-3 border-t border-[#e0e0e0] flex items-center justify-between">
              <div className={cn(
                "flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider",
                message.action === 'resolve' && "text-[#24a148]",
                message.action === 'clarification' && "text-[#f1c21b]",
                message.action === 'escalated' && "text-[#da1e28]"
              )}>
                {message.action === 'resolve' && <CheckCircle2 className="w-3.5 h-3.5" />}
                {message.action === 'clarification' && <HelpCircle className="w-3.5 h-3.5" />}
                {message.action === 'escalated' && <AlertCircle className="w-3.5 h-3.5" />}
                {message.action}
              </div>

              {/* Feedback buttons for Resolved action */}
              {message.action === 'resolve' && feedback === 'none' && (
                <div className="flex items-center gap-1.5 bg-[#f4f4f4] rounded-lg p-0.5 border border-[#e0e0e0] dark:bg-black/10">
                  <button
                    onClick={() => handleFeedback('success')}
                    className="p-1 rounded hover:bg-[#e8f0ff] hover:text-[#0f62fe] text-[#525252] transition-colors"
                    title="This solved my issue"
                  >
                    <ThumbsUp className="w-3.5 h-3.5" />
                  </button>
                  <div className="w-[1px] h-3 bg-[#e0e0e0]" />
                  <button
                    onClick={() => handleFeedback('failed')}
                    className="p-1 rounded hover:bg-[#fff1f1] hover:text-[#da1e28] text-[#525252] transition-colors"
                    title="This did not work"
                  >
                    <ThumbsDown className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              {message.action === 'resolve' && feedback === 'liked' && (
                <span className="text-[10px] text-[#24a148] font-semibold flex items-center gap-1">
                  <ThumbsUp className="w-3 h-3 fill-current" /> Verified Solution
                </span>
              )}

              {message.action === 'resolve' && feedback === 'disliked' && !escalationResult && (
                <span className="text-[10px] text-[#da1e28] font-semibold flex items-center gap-1">
                  <ThumbsDown className="w-3 h-3 fill-current" /> Did not work
                </span>
              )}
            </div>
          )}

          {/* Feedback Escalation Prompt Card */}
          {feedback === 'disliked' && !escalationResult && (
            <div className="mt-3 pt-3 border-t border-[#e0e0e0] text-xs">
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 dark:bg-rose-950/10 dark:border-rose-900/30 flex flex-col gap-2">
                <span className="font-semibold text-rose-700 dark:text-rose-400">Sorry that didn't help!</span>
                <span className="text-[#525252] text-[11px]">Would you like to escalate this directly to our engineering support team on Jira?</span>
                <button
                  disabled={isEscating}
                  onClick={handleEscalate}
                  className="mt-1 self-start inline-flex items-center gap-2 bg-[#da1e28] hover:bg-[#b81b22] text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors shadow-sm disabled:bg-rose-300"
                >
                  {isEscating ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" /> Escalating...
                    </>
                  ) : (
                    <>Escalate to Jira</>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Inline Escalated Ticket Card (if manually escalated just now) */}
          {escalationResult && (
            <div className="mt-3 pt-3 border-t border-[#e0e0e0]">
              <div className="flex flex-col gap-2 px-3 py-2.5 rounded-md bg-[#fff1f1] border border-[#da1e28]/20 group cursor-pointer hover:bg-[#fff1f1]/80 transition-colors"
                onClick={() => {
                  if (escalationResult.ticket?.jira_url) {
                    window.open(escalationResult.ticket.jira_url, '_blank', 'noopener,noreferrer')
                  } else {
                    navigate('/tickets')
                  }
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-3.5 h-3.5 text-[#da1e28] flex-shrink-0" />
                    <div>
                      <span className="text-[11px] font-semibold text-[#161616] block">
                        Jira Ticket Created
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[9px] font-semibold uppercase tracking-wider text-[#da1e28] bg-[#da1e28]/10 px-2 py-0.5 rounded-full">
                      {escalationResult.ticket?.status || 'In Review'}
                    </span>
                    <div className="text-[#da1e28]">
                      <ExternalLink className="w-3.5 h-3.5" />
                    </div>
                  </div>
                </div>
                
                <div className="pl-[22px]">
                  <p className="text-[10px] text-[#525252] mb-1.5">
                    Your request has been escalated. Our engineering support team is on it!
                  </p>
                  <span className="text-[10px] font-mono font-medium text-[#161616] bg-white px-2 py-0.5 rounded border border-[#e0e0e0]">
                    {escalationResult.ticket?.jira_issue_key || escalationResult.jira_key}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* State 1: RAG hit — source chips */}
          {isRagHit && (
            <div className="mt-3 pt-3 border-t border-[#e0e0e0] text-xs">
              <span className="text-[#6f6f6f] text-[10px] font-normal mb-1 block">Sources consulted</span>
              <SourceChips
                sources={message.sources!}
                activeIndex={activePanelIdx}
                onChipClick={(idx) => setActivePanelIdx(prev => prev === idx ? null : idx)}
              />
            </div>
          )}

          {/* State 2: Gemini fallback — amber badge, no chips */}
          {isGeminiFallback && (
            <div className="mt-3 pt-3 border-t border-[#e0e0e0]">
              <div className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-[#fdf6e3] border border-[#f1c21b]/30">
                <BrainCircuit className="w-3.5 h-3.5 text-[#b28600] flex-shrink-0" />
                <span className="text-[11px] text-[#6e4b00] font-medium">
                  Answered from general knowledge · not from your docs
                </span>
              </div>
            </div>
          )}

          {/* State 3: Escalated ticket — card with ticket ID, no chips */}
          {isEscalated && (
            <div className="mt-3 pt-3 border-t border-[#e0e0e0]">
              <div className="flex flex-col gap-2 px-3 py-2.5 rounded-md bg-[#fff1f1] border border-[#da1e28]/20 group cursor-pointer hover:bg-[#fff1f1]/80 transition-colors"
                onClick={() => {
                  if (message.ticket?.jira_url) {
                    window.open(message.ticket.jira_url, '_blank', 'noopener,noreferrer')
                  } else {
                    navigate('/tickets')
                  }
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-3.5 h-3.5 text-[#da1e28] flex-shrink-0" />
                    <div>
                      <span className="text-[11px] font-semibold text-[#161616] block">
                        Ticket created
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[9px] font-semibold uppercase tracking-wider text-[#da1e28] bg-[#da1e28]/10 px-2 py-0.5 rounded-full">
                      {message.ticket?.status || 'In Review'}
                    </span>
                    <div className="text-[#da1e28] hover:text-[#da1e28]/80 transition-colors">
                      <ExternalLink className="w-3.5 h-3.5" />
                    </div>
                  </div>
                </div>
                
                <div className="pl-[22px]">
                  <p className="text-[10px] text-[#525252] mb-1.5">
                    Your request has been escalated. You can track the progress using the ticket ID below.
                  </p>
                  <span className="text-[10px] font-mono font-medium text-[#161616] bg-white px-2 py-0.5 rounded border border-[#e0e0e0]">
                    {message.ticket?.jira_issue_key || `TKT-${message.id?.slice(0, 8).toUpperCase()}`}
                  </span>
                </div>
              </div>
            </div>
          )}
          
          <span className="text-[10px] text-[#a8a8a8] absolute bottom-[-18px] right-2 font-medium">
            {displayTime}
          </span>
        </div>

        {isAI && message.suggestions && message.suggestions.length > 0 && (
          <ClarificationChips 
            suggestions={message.suggestions} 
            onSuggestionClick={sendMessage}
          />
        )}
      </div>

      {!isAI && (
        <div className="w-8 h-8 rounded-lg bg-[#ffffff] border border-[#e0e0e0] flex items-center justify-center flex-shrink-0 mt-1 shadow-sm">
          <User className="w-5 h-5 text-[#525252]" />
        </div>
      )}

      {isAI && (
        <SourceDetailPanel
          source={activePanelIdx !== null && message.sources ? message.sources[activePanelIdx] : null}
          isOpen={activePanelIdx !== null}
          onClose={() => setActivePanelIdx(null)}
          userQuery={userQuery}
          answerContent={message.content}
        />
      )}
    </motion.div>
  )
}
