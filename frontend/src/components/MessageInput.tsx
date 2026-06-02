import { useState, useRef, useEffect } from 'react'
import {
  Check,
  FileText,
  Image as ImageIcon,
  Loader2,
  Paperclip,
  Send,
  Sparkles,
  Square,
  Video,
  X,
  AlertCircle
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { api } from '@/config/api'

interface MessageInputProps {
  onSendMessage: (content: string, attachments?: ParsedAttachment[]) => void
  onStop?: () => void
  disabled?: boolean
  isStreaming?: boolean
}

type AttachmentKind = 'image' | 'pdf' | 'video'

interface AttachmentOption {
  kind: AttachmentKind
  label: string
  helper: string
  accept: string
  icon: React.ComponentType<{ className?: string }>
}

interface ParsedAttachment {
  attachment_type: string
  file_name: string
  mime_type: string
  issue_summary: string
  extracted_text: string
  detected_error?: string | null
  screen_or_area?: string | null
  visible_steps: string[]
  confidence: number
  warnings: string[]
}

interface InFlightAttachment {
  id: string
  file_name: string
  kind: AttachmentKind
  status: 'parsing' | 'success' | 'error'
  error?: string
  parsed?: ParsedAttachment
}

const attachmentOptions: AttachmentOption[] = [
  {
    kind: 'image',
    label: 'Image / Screenshot',
    helper: 'Parse visible UI errors',
    accept: 'image/png,image/jpeg,image/webp',
    icon: ImageIcon,
  },
  {
    kind: 'pdf',
    label: 'PDF / Log',
    helper: 'Extract logs or document text',
    accept: '.pdf,.log,.txt,.csv,text/plain,application/pdf',
    icon: FileText,
  },
  {
    kind: 'video',
    label: 'Video',
    helper: 'Summarize visible scenario steps',
    accept: 'video/mp4,video/webm,video/quicktime',
    icon: Video,
  },
]

export const MessageInput = ({ onSendMessage, onStop, disabled, isStreaming }: MessageInputProps) => {
  const [content, setContent] = useState('')
  const [isAttachmentMenuOpen, setIsAttachmentMenuOpen] = useState(false)
  const [selectedAttachmentKind, setSelectedAttachmentKind] = useState<AttachmentKind>('image')
  const [inFlightAttachments, setInFlightAttachments] = useState<InFlightAttachment[]>([])
  
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const selectedOption = attachmentOptions.find((option) => option.kind === selectedAttachmentKind) ?? attachmentOptions[0]

  const handleSend = () => {
    const userText = content.trim()
    const successfulParsed = inFlightAttachments
      .filter((att) => att.status === 'success' && att.parsed)
      .map((att) => att.parsed!)

    // Require either typed text or at least one fully parsed attachment
    if ((userText || successfulParsed.length > 0) && !disabled && !isStreaming) {
      onSendMessage(userText || 'Please investigate the attached issue details.', successfulParsed)
      setContent('')
      setInFlightAttachments([])
    }
  }

  const handleSelectAttachment = (kind: AttachmentKind) => {
    setSelectedAttachmentKind(kind)
    setIsAttachmentMenuOpen(false)
    fileInputRef.current?.click()
  }

  const handleAttachmentChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    const newId = Date.now().toString()
    const kind = selectedAttachmentKind === 'pdf' && !file.name.toLowerCase().endsWith('.pdf') ? 'log' : selectedAttachmentKind
    
    // Add to in-flight queue in 'parsing' state
    const newInFlight: InFlightAttachment = {
      id: newId,
      file_name: file.name,
      kind: selectedAttachmentKind,
      status: 'parsing'
    }
    
    setInFlightAttachments((prev) => [...prev, newInFlight])

    try {
      const formData = new FormData()
      formData.append('file', file)
      const response = await api.post<ParsedAttachment>(
        `/chat/attachments/parse?attachment_type=${kind}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      )
      
      setInFlightAttachments((prev) =>
        prev.map((att) =>
          att.id === newId
            ? { ...att, status: 'success', parsed: response.data }
            : att
        )
      )
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Could not parse attachment.'
      setInFlightAttachments((prev) =>
        prev.map((att) =>
          att.id === newId
            ? { ...att, status: 'error', error: message }
            : att
        )
      )
    }
  }

  const removeAttachment = (id: string) => {
    setInFlightAttachments((prev) => prev.filter((att) => att.id !== id))
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

  // Get matching styles & icon for specific attachment type
  const getAttachmentKindSpecs = (kind: AttachmentKind) => {
    switch (kind) {
      case 'image':
        return {
          icon: ImageIcon,
          colorClass: 'text-purple-600 bg-purple-50 border-purple-200 dark:bg-purple-950/20 dark:border-purple-900/30'
        }
      case 'pdf':
        return {
          icon: FileText,
          colorClass: 'text-rose-600 bg-rose-50 border-rose-200 dark:bg-rose-950/20 dark:border-rose-900/30'
        }
      case 'video':
        return {
          icon: Video,
          colorClass: 'text-amber-600 bg-amber-50 border-amber-200 dark:bg-amber-950/20 dark:border-amber-900/30'
        }
    }
  }

  // Check if any attachment is currently parsing
  const isCurrentlyParsing = inFlightAttachments.some((att) => att.status === 'parsing')

  return (
    <div className="relative group">
      <input
        ref={fileInputRef}
        type="file"
        accept={selectedOption.accept}
        className="hidden"
        onChange={handleAttachmentChange}
      />

      {isAttachmentMenuOpen && (
        <div className="absolute bottom-[calc(100%+12px)] left-0 w-full max-w-[520px] rounded-2xl bg-white dark:bg-slate-900 border border-[#e0e0e0] dark:border-slate-800 shadow-xl p-4 z-20 transition-all duration-200 scale-100">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-xs font-semibold text-[#161616] dark:text-white">Attach evidence</p>
              <p className="text-[11px] text-[#6f6f6f] dark:text-slate-400">Files are parsed securely in-memory to inject perfect diagnostic context.</p>
            </div>
            <button
              type="button"
              onClick={() => setIsAttachmentMenuOpen(false)}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-[#525252] dark:text-slate-400 hover:bg-[#f4f4f4] dark:hover:bg-slate-800"
              aria-label="Close attachment menu"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {attachmentOptions.map((option) => {
              const Icon = option.icon
              return (
                <button
                  key={option.kind}
                  type="button"
                  onClick={() => handleSelectAttachment(option.kind)}
                  className="text-left rounded-xl border border-[#e0e0e0] dark:border-slate-800 hover:border-[#0f62fe] dark:hover:border-blue-400 hover:bg-[#f4f8ff] dark:hover:bg-slate-800 px-3.5 py-3 transition-all duration-200 hover:-translate-y-0.5"
                >
                  <Icon className="w-4.5 h-4.5 text-[#0f62fe] dark:text-blue-400 mb-2" />
                  <span className="block text-xs font-semibold text-[#161616] dark:text-white">{option.label}</span>
                  <span className="block text-[10px] text-[#6f6f6f] dark:text-slate-400 mt-1">{option.helper}</span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Modern Integrated Chat Box Container */}
      <div className="relative bg-[#ffffff] dark:bg-slate-900 border border-[#e0e0e0] dark:border-slate-800 shadow-md rounded-[24px] p-2 flex flex-col focus-within:border-[#0f62fe] dark:focus-within:border-blue-500 focus-within:shadow-lg focus-within:shadow-[#0f62fe]/5 transition-all duration-300">
        
        {/* Compact Glowing Attachment Capsules Row */}
        {inFlightAttachments.length > 0 && (
          <div className="flex flex-wrap gap-2 px-3 pt-2 pb-1 border-b border-[#f4f4f4] dark:border-slate-800 mb-1">
            {inFlightAttachments.map((att) => {
              const specs = getAttachmentKindSpecs(att.kind)
              const Icon = specs.icon
              
              return (
                <div
                  key={att.id}
                  className={cn(
                    "flex items-center gap-2 px-2.5 py-1.5 rounded-xl border text-xs font-medium max-w-[240px] transition-all duration-300 scale-100",
                    att.status === 'parsing' && 'border-gray-200 dark:border-slate-850 bg-gray-50/50 dark:bg-slate-800/50 text-gray-500 dark:text-slate-400 animate-pulse',
                    att.status === 'success' && specs.colorClass,
                    att.status === 'error' && 'border-rose-200 bg-rose-50 text-rose-600'
                  )}
                >
                  <Icon className="w-3.5 h-3.5 flex-shrink-0" />
                  
                  <span className="truncate flex-1 max-w-[140px]" title={att.file_name}>
                    {att.file_name}
                  </span>

                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    {att.status === 'parsing' && (
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-[#0f62fe]" />
                    )}
                    {att.status === 'success' && (
                      <div className="w-3.5 h-3.5 rounded-full bg-emerald-500 text-white flex items-center justify-center scale-100 transition-transform duration-300">
                        <Check className="w-2.5 h-2.5 stroke-[3]" />
                      </div>
                    )}
                    {att.status === 'error' && (
                      <div title={att.error}>
                        <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
                      </div>
                    )}
                    
                    <button
                      type="button"
                      onClick={() => removeAttachment(att.id)}
                      className="w-4 h-4 rounded-full flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
                      title="Remove attachment"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Input Bar Row */}
        <div className="flex items-end gap-2 pr-2">
          <button
            type="button"
            onClick={() => setIsAttachmentMenuOpen((open) => !open)}
            disabled={disabled || isStreaming || isCurrentlyParsing}
            className={cn(
              "w-10 h-10 rounded-xl flex items-center justify-center transition-all flex-shrink-0",
              disabled || isStreaming || isCurrentlyParsing
                ? "bg-[#e0e0e0] dark:bg-slate-800 text-[#a8a8a8] dark:text-slate-600 cursor-not-allowed"
                : "bg-[#f4f4f4] dark:bg-slate-800 text-[#525252] dark:text-slate-300 hover:bg-[#e8f0ff] dark:hover:bg-slate-700 hover:text-[#0f62fe] dark:hover:text-blue-400"
            )}
            aria-label="Attach issue evidence"
            title="Attach issue evidence"
          >
            <Paperclip className="w-5 h-5" />
          </button>
 
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your issue, or attach screenshot, PDF/log, or video..."
              disabled={disabled}
              className="w-full bg-transparent border-none focus:ring-0 text-[#161616] dark:text-white placeholder:text-[#a8a8a8] dark:placeholder:text-slate-500 text-sm py-3 px-4 resize-none outline-none overflow-y-auto max-h-[200px]"
              rows={1}
            />
          </div>
          
          <button
            onClick={isStreaming ? onStop : handleSend}
            disabled={
              (isStreaming ? false : (!content.trim() && inFlightAttachments.filter((a) => a.status === 'success').length === 0)) ||
              disabled ||
              isCurrentlyParsing
            }
            className={cn(
              "w-10 h-10 rounded-xl flex items-center justify-center transition-all flex-shrink-0",
              isStreaming || ((content.trim() || inFlightAttachments.some((a) => a.status === 'success')) && !disabled && !isCurrentlyParsing)
                ? "bg-[#0f62fe] dark:bg-blue-600 text-white shadow-md shadow-[#0f62fe]/20 dark:shadow-blue-500/10 scale-100 hover:bg-[#0353e9] dark:hover:bg-blue-500"
                : "bg-[#e0e0e0] dark:bg-slate-800 text-[#a8a8a8] dark:text-slate-600 scale-95 cursor-not-allowed"
            )}
            aria-label={isStreaming ? 'Stop response' : 'Send message'}
          >
            {isStreaming ? (
              <Square className="w-4 h-4 fill-current animate-pulse" />
            ) : disabled ? (
              <Sparkles className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
