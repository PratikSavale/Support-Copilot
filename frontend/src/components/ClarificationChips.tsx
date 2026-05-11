import { motion } from 'framer-motion'
import { MessageSquare } from 'lucide-react'

interface ClarificationChipsProps {
  suggestions: string[]
  onSuggestionClick: (suggestion: string) => void
  disabled?: boolean
}

export const ClarificationChips = ({ suggestions, onSuggestionClick, disabled }: ClarificationChipsProps) => {
  return (
    <div className="flex flex-wrap gap-2 mt-4">
      {suggestions.map((suggestion, index) => (
        <motion.button
          key={index}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.1 }}
          onClick={() => onSuggestionClick(suggestion)}
          disabled={disabled}
          className="px-3 py-1.5 rounded-full glass-panel text-[11px] font-medium text-white/70 hover:text-white hover:bg-white/10 transition-all border border-white/5 flex items-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <MessageSquare className="w-3 h-3 text-nebula-blue group-hover:scale-110 transition-transform" />
          {suggestion}
        </motion.button>
      ))}
    </div>
  )
}
