import { useState, useRef, useEffect } from 'react'
import {
  CheckCircle2,
  FileText,
  Image,
  Loader2,
  Paperclip,
  Send,
  Sparkles,
  Square,
  Video,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { api } from '@/config/api'

interface MessageInputProps {
  onSendMessage: (content: string) => void
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
  issue_summary: string
  detected_error?: string | null
  screen_or_area?: string | null
  visible_steps: string[]
  confidence: number
  warnings: string[]
}

const attachmentOptions: AttachmentOption[] = [
  {
    kind: 'image',
    label: 'Image / Screenshot',
    helper: 'Parse visible UI errors',
    accept: 'image/png,image/jpeg,image/webp',
    icon: Image,
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
  const [parsedAttachment, setParsedAttachment] = useState<ParsedAttachment | null>(null)
  const [attachmentError, setAttachmentError] = useState<string | null>(null)
  const [isParsingAttachment, setIsParsingAttachment] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const selectedOption = attachmentOptions.find((option) => option.kind === selectedAttachmentKind) ?? attachmentOptions[0]

  const handleSend = () => {
    const userText = content.trim()
    if ((userText || parsedAttachment) && !disabled && !isStreaming) {
      const finalMessage = parsedAttachment
        ? [
            userText || 'Please investigate this attached issue.',
            '',
            `Attachment summary (${parsedAttachment.file_name}):`,
            parsedAttachment.issue_summary,
          ].join('\n')
        : userText

      onSendMessage(finalMessage.trim())
      setContent('')
      setParsedAttachment(null)
      setAttachmentError(null)
    }
  }

  const handleSelectAttachment = (kind: AttachmentKind) => {
    setSelectedAttachmentKind(kind)
    setIsAttachmentMenuOpen(false)
    setAttachmentError(null)
    fileInputRef.current?.click()
  }

  const handleAttachmentChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    setIsParsingAttachment(true)
    setAttachmentError(null)
    setParsedAttachment(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      const kind = selectedAttachmentKind === 'pdf' && !file.name.toLowerCase().endsWith('.pdf') ? 'log' : selectedAttachmentKind
      const response = await api.post<ParsedAttachment>(
        `/chat/attachments/parse?attachment_type=${kind}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      )
      setParsedAttachment(response.data)
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Could not parse this attachment.'
      setAttachmentError(message)
    } finally {
      setIsParsingAttachment(false)
    }
  }

  const insertAttachmentSummary = () => {
    if (!parsedAttachment) return
    setContent((current) => {
      const prefix = current.trim() ? `${current.trim()}\n\n` : ''
      return `${prefix}${parsedAttachment.issue_summary}`
    })
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
      <input
        ref={fileInputRef}
        type="file"
        accept={selectedOption.accept}
        className="hidden"
        onChange={handleAttachmentChange}
      />

      {isAttachmentMenuOpen && (
        <div className="absolute bottom-[calc(100%+12px)] left-0 w-full max-w-[520px] rounded-xl bg-white border border-[#e0e0e0] shadow-lg p-3 z-20">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-xs font-semibold text-[#161616]">What do you want to attach?</p>
              <p className="text-[11px] text-[#6f6f6f]">The file becomes an issue summary, then KC search continues as usual.</p>
            </div>
            <button
              type="button"
              onClick={() => setIsAttachmentMenuOpen(false)}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-[#525252] hover:bg-[#f4f4f4]"
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
                  className="text-left rounded-lg border border-[#e0e0e0] hover:border-[#0f62fe] hover:bg-[#f4f8ff] px-3 py-3 transition-colors"
                >
                  <Icon className="w-4 h-4 text-[#0f62fe] mb-2" />
                  <span className="block text-xs font-semibold text-[#161616]">{option.label}</span>
                  <span className="block text-[10px] text-[#6f6f6f] mt-1">{option.helper}</span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {(isParsingAttachment || parsedAttachment || attachmentError) && (
        <div className="mb-3 rounded-xl bg-white border border-[#e0e0e0] shadow-sm p-3">
          {isParsingAttachment && (
            <div className="flex items-center gap-2 text-xs text-[#525252]">
              <Loader2 className="w-4 h-4 animate-spin text-[#0f62fe]" />
              Parsing attachment into an issue summary...
            </div>
          )}

          {parsedAttachment && (
            <div className="flex flex-col gap-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 text-xs font-semibold text-[#161616]">
                    <CheckCircle2 className="w-4 h-4 text-[#24a148] flex-shrink-0" />
                    Attachment parsed
                  </div>
                  <p className="text-[11px] text-[#6f6f6f] mt-1 truncate">{parsedAttachment.file_name}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setParsedAttachment(null)}
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-[#525252] hover:bg-[#f4f4f4] flex-shrink-0"
                  aria-label="Remove attachment summary"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="rounded-lg bg-[#f4f4f4] border border-[#e0e0e0] px-3 py-2">
                <p className="text-xs text-[#161616] leading-relaxed line-clamp-4 whitespace-pre-line">
                  {parsedAttachment.issue_summary}
                </p>
              </div>

              {parsedAttachment.warnings.length > 0 && (
                <p className="text-[11px] text-[#8a3800]">{parsedAttachment.warnings[0]}</p>
              )}

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={insertAttachmentSummary}
                  className="px-3 py-1.5 rounded-md bg-[#e8f0ff] text-[#0f62fe] text-[11px] font-semibold hover:bg-[#d0e2ff]"
                >
                  Use summary in message
                </button>
                <span className="text-[10px] text-[#6f6f6f]">
                  Sending will include this summary for KC search and ticket escalation.
                </span>
              </div>
            </div>
          )}

          {attachmentError && (
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs text-[#da1e28]">{attachmentError}</p>
              <button
                type="button"
                onClick={() => setAttachmentError(null)}
                className="text-[11px] font-semibold text-[#0f62fe]"
              >
                Dismiss
              </button>
            </div>
          )}
        </div>
      )}

      <div className="relative bg-[#ffffff] border border-[#e0e0e0] shadow-sm rounded-[20px] p-2 flex items-end gap-2 pr-4 focus-within:border-[#0f62fe] transition-all">
        <button
          type="button"
          onClick={() => setIsAttachmentMenuOpen((open) => !open)}
          disabled={disabled || isStreaming || isParsingAttachment}
          className={cn(
            "w-10 h-10 rounded-xl flex items-center justify-center transition-all flex-shrink-0",
            disabled || isStreaming || isParsingAttachment
              ? "bg-[#e0e0e0] text-[#a8a8a8] cursor-not-allowed"
              : "bg-[#f4f4f4] text-[#525252] hover:bg-[#e8f0ff] hover:text-[#0f62fe]"
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
            className="w-full bg-transparent border-none focus:ring-0 text-[#161616] placeholder:text-[#a8a8a8] text-sm py-3 px-4 resize-none outline-none overflow-y-auto max-h-[200px]"
            rows={1}
          />
        </div>
        
        <button
          onClick={isStreaming ? onStop : handleSend}
          disabled={(isStreaming ? false : (!content.trim() && !parsedAttachment)) || disabled || isParsingAttachment}
          className={cn(
            "w-10 h-10 rounded-xl flex items-center justify-center transition-all",
            (isStreaming || ((content.trim() || parsedAttachment) && !disabled && !isParsingAttachment))
              ? "bg-[#0f62fe] text-white shadow-md shadow-[#0f62fe]/20 scale-100"
              : "bg-[#e0e0e0] text-[#a8a8a8] scale-95 cursor-not-allowed"
          )}
          aria-label={isStreaming ? 'Stop response' : 'Send message'}
        >
          {isStreaming ? (
            <Square className="w-4 h-4 fill-current" />
          ) : disabled ? (
            <Sparkles className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
    </div>
  )
}
