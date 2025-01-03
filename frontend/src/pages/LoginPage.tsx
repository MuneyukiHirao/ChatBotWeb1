import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api/ApiClient'

export default function LoginPage() {
  const navigate = useNavigate()
  const [userId, setUserId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      const resp = await login(userId, password) // { sessionId: 'xxx' }
      if (resp.sessionId) {
        sessionStorage.setItem('sessionId', resp.sessionId)
        navigate('/select-user')
      } else {
        setError('ログインに失敗しました。')
      }
    } catch (err) {
      setError('ログインエラー: ' + String(err))
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '0 auto', textAlign: 'center' }}>
      <h1>ログイン</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label>ユーザID: </label>
          <input
            value={userId}
            onChange={e => setUserId(e.target.value)}
          />
        </div>
        <div>
          <label>パスワード: </label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
          />
        </div>
        <button type="submit">ログイン</button>
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <p>（デモ：userId=test, password=test）</p>
    </div>
  )
}
