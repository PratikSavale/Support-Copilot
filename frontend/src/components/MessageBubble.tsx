import { motion } from 'framer-motion'
import { Bot, User, CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Message } from '../store/userStore'
import { ClarificationChips } from './ClarificationChips'
import { useWebSocket } from '../hooks/useWebSocket'
import { useParams } from 'react-router-dom'

interface MessageBubbleProps {
  message: Message
}

export const MessageBubble = ({ message }: MessageBubbleProps) => {
  const isAI = message.role === 'assistant'
  const { sessionId } = useParams<{ sessionId: string }>()
  const { sendMessage } = useWebSocket(sessionId || null)

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
        <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center flex-shrink-0 mt-1">
          <Bot className="w-5 h-5 text-nebula-blue" />
        </div>
      )}

      <div className="flex flex-col gap-1 max-w-[80%]">
        <div
          className={cn(
            "px-5 py-3.5 rounded-2xl relative transition-all",
            isAI 
              ? "glass-panel text-white/90" 
              : "bg-gradient-to-br from-nebula-blue to-nebula-purple text-white shadow-lg shadow-nebula-blue/10"
          )}
        >
          <div className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
            {!message.content && isAI && (
              <div className="flex gap-1 items-center py-2">
                <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce [animation-delay:-0.3s]" />
                <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <span className="w-1.5 h-1.5 bg-white/40 rounded-full animate-bounce" />
              </div>
            )}
          </div>

          {/* Action Indicators */}
          {isAI && message.action && (
            <div className={cn(
              "mt-3 pt-3 border-t border-white/10 flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider",
              message.action === 'resolve' && "text-emerald-400",
              message.action === 'clarification' && "text-amber-400",
              message.action === 'escalated' && "text-rose-400"
            )}>
              {message.action === 'resolve' && <CheckCircle2 className="w-3.5 h-3.5" />}
              {message.action === 'clarification' && <HelpCircle className="w-3.5 h-3.5" />}
              {message.action === 'escalated' && <AlertCircle className="w-3.5 h-3.5" />}
              {message.action}
            </div>
          )}
          
          <span className="text-[10px] text-white/30 absolute bottom-[-18px] right-2 font-medium">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
        <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center flex-shrink-0 mt-1">
          <User className="w-5 h-5 text-white/60" />
        </div>
      )}
    </motion.div>
  )
}
