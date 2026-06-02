import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Bot, LogOut, LayoutGrid, User, ShieldCheck, Sun, Moon } from 'lucide-react'
import { KnowledgeSourceSelector } from './KnowledgeSourceSelector'
import { useAuthStore } from '../store/authStore'

export const Header = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const isChat = location.pathname.includes('/chat/')
  const { user, logout } = useAuthStore()

  const [theme, setTheme] = useState<'light' | 'dark'>(
    (localStorage.getItem('theme') as 'light' | 'dark') || 'light'
  )

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'))
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-slate-900 border-b border-[#e0e0e0] dark:border-slate-800 px-6 py-4 shadow-sm transition-colors duration-300">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 min-w-[240px] group">
          <div className="w-10 h-10 rounded-xl bg-[#0f62fe] flex items-center justify-center shadow-md shadow-[#0f62fe]/20 group-hover:scale-110 transition-transform">
            <Bot className="text-white w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-[#161616] dark:text-white group-hover:text-[#0f62fe] dark:group-hover:text-blue-400 transition-colors">EscalateAI</h1>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#24a148] animate-pulse" />
              <span className="text-[10px] uppercase tracking-widest text-[#24a148] font-bold">System Online</span>
            </div>
          </div>
        </Link>

        <div className="flex-1 flex justify-center">
          {isChat && <KnowledgeSourceSelector />}
        </div>

        <div className="flex items-center gap-4 min-w-[240px] justify-end">
          {isChat && (
            <Link
              to="/"
              className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#ffffff] dark:bg-slate-800 border border-[#e0e0e0] dark:border-slate-700 text-xs text-[#525252] dark:text-slate-300 hover:text-[#161616] dark:hover:text-white hover:bg-[#f4f4f4] dark:hover:bg-slate-700 transition-all"
            >
              <LayoutGrid className="w-4 h-4" />
              <span>History</span>
            </Link>
          )}

          {user?.role === 'admin' && (
            <Link
              to="/admin"
              className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-50 border border-indigo-200 text-xs font-bold text-indigo-700 hover:bg-indigo-100 transition-all"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Admin Panel</span>
            </Link>
          )}

          <div className="h-8 w-px bg-[#e0e0e0] dark:bg-slate-800 mx-2" />

          <div className="flex items-center gap-3 pl-2">
            <div className="flex flex-col items-end hidden sm:flex">
              <p className="text-xs font-bold text-[#161616] dark:text-white tracking-tight">{user?.name || 'User'}</p>
              <p className="text-[10px] text-[#525252] dark:text-slate-400 font-medium truncate max-w-[100px]">{user?.email}</p>
            </div>
            <div className="w-8 h-8 rounded-full border border-[#e0e0e0] dark:border-slate-700 overflow-hidden bg-[#f4f4f4] dark:bg-slate-800">
              {user?.avatar ? (
                <img src={user.avatar} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <User className="w-4 h-4 text-[#a8a8a8] dark:text-slate-500" />
                </div>
              )}
            </div>

            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl bg-[#ffffff] dark:bg-slate-800 border border-[#e0e0e0] dark:border-slate-700 text-[#525252] dark:text-slate-300 hover:text-blue-500 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-slate-700 transition-all group"
              title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
            >
              {theme === 'light' ? (
                <Moon className="w-4 h-4 group-hover:scale-110 transition-transform" />
              ) : (
                <Sun className="w-4 h-4 group-hover:scale-110 transition-transform text-amber-400" />
              )}
            </button>

            <button
              onClick={handleLogout}
              className="p-2 rounded-xl bg-[#ffffff] dark:bg-slate-800 border border-[#e0e0e0] dark:border-slate-700 text-[#525252] dark:text-slate-300 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 hover:border-rose-200 dark:hover:border-rose-900 transition-all group"
              title="Logout"
            >
              <LogOut className="w-4 h-4 group-hover:scale-110 transition-transform" />
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
