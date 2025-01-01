import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getUsers, selectUser } from '../api/ApiClient'

interface UserItem {
  userId: string
  userName: string
  companyId: string
  companyName: string
  machineCount: number
}

export default function SelectUserPage() {
  const navigate = useNavigate()
  const [users, setUsers] = useState<UserItem[]>([])
  const [error, setError] = useState('')

  const sessionId = sessionStorage.getItem('sessionId')

  useEffect(() => {
    
    // 未ログインなら /login に飛ばす
    if (!sessionId) {
      navigate('/login')
      return
    }

    // ユーザ一覧取得
    getUsers()
      .then(data => {
        setUsers(data.users || [])
      })
      .catch(err => {
        setError('ユーザ一覧取得エラー: ' + String(err))
      })
  }, [navigate, sessionId])

  const handleSelect = async (userId: string) => {
    if (!sessionId) return
    try {
      await selectUser(sessionId, userId)
      // 成功で /chat へ
      navigate('/chat')
    } catch (err) {
      setError('ユーザ選択エラー: ' + String(err))
    }
  }

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <h1>ユーザ一覧</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <table border={1} style={{ width: '100%' }}>
        <thead>
          <tr>
            <th>ユーザID</th>
            <th>氏名</th>
            <th>会社ID</th>
            <th>会社名</th>
            <th>車両数</th>
            <th>選択</th>
          </tr>
        </thead>
        <tbody>
          {users.map(u => (
            <tr key={u.userId}>
              <td>{u.userId}</td>
              <td>{u.userName}</td>
              <td>{u.companyId}</td>
              <td>{u.companyName}</td>
              <td>{u.machineCount}</td>
              <td>
                <button onClick={() => handleSelect(u.userId)}>選択</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
