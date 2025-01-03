
import { Routes, Route } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import SelectUserPage from './pages/SelectUserPage'
import ChatPage from './pages/ChatPage'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/select-user" element={<SelectUserPage />} />
      <Route path="/chat" element={<ChatPage />} />
      {/* デフォルトで /login に飛ばす */}
      <Route path="*" element={<LoginPage />} />
    </Routes>
  )
}

export default App
