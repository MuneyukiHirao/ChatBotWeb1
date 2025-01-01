import axios from 'axios'

// 環境変数からAPIのベースURLを取得 (ない場合はローカル)
const BASE_URL = 'https://upgraded-space-cod-6jwrvpw49j6cggr-5000.app.github.dev/'

export async function login(userId: string, password: string) {
  const resp = await axios.post(`${BASE_URL}/api/login`, {
    userId,
    password,
  })
  return resp.data  // {sessionId: "..."} など
}

export async function getUsers() {
  const resp = await axios.get(`${BASE_URL}/api/users`)
  return resp.data // { users: [ ... ] }
}

export async function selectUser(sessionId: string, userId: string) {
  const resp = await axios.post(`${BASE_URL}/api/select-user`, {
    sessionId,
    userId,
  })
  return resp.data
}

export async function postChatMessage(sessionId: string, message: string) {
  const resp = await axios.post(`${BASE_URL}/api/chat`, {
    sessionId,
    message,
  })
  return resp.data  // { reply: "...", conversation: [...] }
}

export async function resetChat(sessionId: string) {
  const resp = await axios.post(`${BASE_URL}/api/chat/reset`, {
    sessionId,
  })
  return resp.data // { message: "Chat history reset." }
}

export async function finishChat(sessionId: string) {
  const resp = await axios.post(`${BASE_URL}/api/chat/finish`, {
    sessionId,
  })
  return resp.data // { message: "Chat finished" }
}
