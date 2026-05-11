import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { UserLayout } from './layouts/UserLayout'
import { AdminLayout } from './layouts/AdminLayout'
import { ChatPage } from './pages/ChatPage'
import { AdminDashboard, KnowledgePage, TicketsPage } from './pages/AdminPages'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route 
          path="/chat" 
          element={
            <UserLayout>
              <ChatPage />
            </UserLayout>
          } 
        />
        <Route 
          path="/chat/:sessionId" 
          element={
            <UserLayout>
              <ChatPage />
            </UserLayout>
          } 
        />
        
        {/* Admin Routes */}
        <Route 
          path="/admin" 
          element={
            <AdminLayout>
              <AdminDashboard />
            </AdminLayout>
          } 
        />
        <Route 
          path="/admin/knowledge" 
          element={
            <AdminLayout>
              <KnowledgePage />
            </AdminLayout>
          } 
        />
        <Route 
          path="/admin/tickets" 
          element={
            <AdminLayout>
              <TicketsPage />
            </AdminLayout>
          } 
        />
      </Routes>
    </Router>
  )
}

export default App
