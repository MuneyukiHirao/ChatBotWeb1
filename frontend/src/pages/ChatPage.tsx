import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { postChatMessage, resetChat, finishChat } from '../api/ApiClient'

interface Message {
  role: string
  content: string
}

export default function ChatPage() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<Message[]>([])
  const [inputText, setInputText] = useState('')
  const [error, setError] = useState('')

  const sessionId = sessionStorage.getItem('sessionId')

  useEffect(() => {
    if (!sessionId) {
      navigate('/login')
      return
    }
    // 初回読み込みで何か履歴を取得したい場合はここで API 呼ぶ
    // 現在は特にしない
  }, [navigate, sessionId])

  const handleSend = async () => {
    if (!sessionId) return
    setError('')
    try {
      const data = await postChatMessage(sessionId, inputText) 
      // data.reply, data.conversation
      setInputText('')
      setMessages(data.conversation) 
    } catch (err) {
      setError('送信エラー: ' + String(err))
    }
  }

  const handleReset = async () => {
    if (!sessionId) return
    setError('')
    try {
      const resp = await resetChat(sessionId)
      console.log(resp)
      setMessages([])
    } catch (err) {
      setError('リセットエラー: ' + String(err))
    }
  }

  const handleFinish = async () => {
    if (!sessionId) return
    setError('')
    try {
      await finishChat(sessionId)
      // セッションID破棄
      sessionStorage.removeItem('sessionId')
      navigate('/select-user')
    } catch (err) {
      setError('終了エラー: ' + String(err))
    }
  }

  return (
    <div style={{maxWidth: 600, margin: '0 auto'}}>
      <h1>チャット</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}

      <div style={{border: '1px solid #ccc', height: '300px', overflowY: 'auto', padding: '5px'}}>
        {messages.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.role === 'user' ? 'right' : 'left' }}>
            <div 
              style={{
                display: 'inline-block',
                margin: '4px',
                padding: '8px',
                borderRadius: '8px',
                backgroundColor: msg.role === 'user' ? '#cef' : '#eee'
              }}
            >
              {msg.role === 'system' 
                ? <i>{msg.content}</i>
                : msg.content
              }
            </div>
          </div>
        ))}
      </div>

      <div style={{marginTop: '10px'}}>
        <input 
          style={{width: '80%'}} 
          value={inputText} 
          onChange={e => setInputText(e.target.value)} 
          onKeyDown={e => e.key === 'Enter' && handleSend()}
        />
        <button onClick={handleSend}>送信</button>
      </div>

      <div style={{marginTop: '10px'}}>
        <button onClick={handleReset}>リセット</button>
        <button onClick={handleFinish}>終了</button>
      </div>
    </div>
  )
}
