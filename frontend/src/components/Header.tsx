import { Bot, ShieldCheck } from 'lucide-react'
import { KnowledgeSourceSelector } from './KnowledgeSourceSelector'

export const Header = () => {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 glass-panel border-b border-white/10 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3 min-w-[240px]">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-nebula-purple to-nebula-blue flex items-center justify-center shadow-lg shadow-nebula-purple/20 animate-pulse-glow">
            <Bot className="text-white w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">Support Copilot</h1>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] uppercase tracking-widest text-emerald-500/80 font-bold">System Online</span>
            </div>
          </div>
        </div>

        <div className="flex-1 flex justify-center">
          <KnowledgeSourceSelector />
        </div>
        
        <div className="flex items-center gap-4 min-w-[240px] justify-end">
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
            <ShieldCheck className="w-4 h-4 text-nebula-blue" />
            <span className="text-xs text-white/60 font-medium">L2 Secure AI Agent</span>
          </div>
        </div>
      </div>
    </header>
  )
}
