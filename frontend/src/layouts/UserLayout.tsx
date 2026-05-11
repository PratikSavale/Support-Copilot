import type { ReactNode } from 'react'
import { Header } from '../components/Header'

interface UserLayoutProps {
  children: ReactNode
}

export const UserLayout = ({ children }: UserLayoutProps) => {
  return (
    <div className="relative min-h-screen flex flex-col">
      {/* Background Decor */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-nebula-purple/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[10%] left-[-5%] w-[30%] h-[30%] bg-nebula-blue/10 blur-[100px] rounded-full" />
      </div>

      <Header />
      
      <main className="flex-1 pt-24 pb-12 px-4 md:px-6 relative z-10">
        <div className="max-w-4xl mx-auto h-[calc(100vh-160px)]">
          {children}
        </div>
      </main>
      
      <footer className="py-4 text-center border-t border-white/5 relative z-10">
        <p className="text-[10px] uppercase tracking-[0.2em] text-white/20 font-medium">
          Powered by Gemini AI & ChromaDB
        </p>
      </footer>
    </div>
  )
}
