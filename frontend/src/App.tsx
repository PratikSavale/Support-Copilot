import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { UserLayout } from './layouts/UserLayout'
import { ChatPage } from './pages/ChatPage'

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
      </Routes>
    </Router>
  )
}

export default App
