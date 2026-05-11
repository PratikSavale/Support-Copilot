import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MessageInputProps {
  onSendMessage: (content: string) => void
  disabled?: boolean
}

export const MessageInput = ({ onSendMessage, disabled }: MessageInputProps) => {
  const [content, setContent] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    if (content.trim() && !disabled) {
      onSendMessage(content.trim())
      setContent('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'inherit'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [content])

  return (
    <div className="relative group">
      <div className="absolute inset-[-2px] bg-gradient-to-r from-nebula-blue/20 via-nebula-purple/20 to-nebula-pink/20 rounded-[22px] blur-md opacity-0 group-focus-within:opacity-100 transition-opacity duration-500" />
      
      <div className="relative glass-panel rounded-[20px] p-2 flex items-end gap-2 pr-4">
        <div className="flex-1 min-h-[48px] max-h-[150px] flex items-center">
          <textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your support request..."
            disabled={disabled}
            className="w-full bg-transparent border-none focus:ring-0 text-white/90 placeholder:text-white/20 text-sm py-3 px-4 resize-none outline-none overflow-y-auto"
            rows={1}
          />
        </div>
        
        <button
          onClick={handleSend}
          disabled={!content.trim() || disabled}
          className={cn(
            "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
            content.trim() && !disabled
              ? "bg-gradient-to-br from-nebula-blue to-nebula-purple text-white shadow-lg shadow-nebula-blue/20 scale-100"
              : "bg-white/5 text-white/10 scale-95 cursor-not-allowed"
          )}
        >
          {disabled ? (
            <Sparkles className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
    </div>
  )
}
