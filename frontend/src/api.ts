const API_BASE = '/api/v1';

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
}

export interface Token {
  access_token: string;
  token_type: string;
}

// 认证API
export const authApi = {
  async login(username: string, password: string): Promise<Token> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const res = await fetch(`${API_BASE}/auth/login/access-token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });
    
    if (!res.ok) throw new Error('登录失败');
    return res.json();
  },

  async register(username: string, email: string, password: string): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password })
    });

    if (!res.ok) {
      let errMsg = '注册失败';
      try {
        const errData = await res.json();
        errMsg = errData.detail || errData.message || '注册失败';
      } catch {
        errMsg = res.statusText || `服务器错误 (${res.status})`;
      }
      throw new Error(errMsg);
    }

    return res.json();
  },

  async getMe(token: string): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (!res.ok) throw new Error('获取用户信息失败');
    return res.json();
  }
};

// 飞花令API
export const flyFlowerApi = {
  async start(keyword: string, difficulty: string, token: string) {
    const res = await fetch('/ldy/poetry/flyflower/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ keyword, difficulty })
    });
    
    if (!res.ok) throw new Error('开始游戏失败');
    return res.json();
  },

  async play(keyword: string, userLine: string, userPosition: number, 
             currentRound: number, difficulty: string, failCount: number,
             isGiveUp: boolean, token: string) {
    const res = await fetch('/ldy/poetry/flyflower', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        keyword,
        user_line: userLine,
        user_position: userPosition,
        current_round: currentRound,
        fail_count: failCount,
        difficulty,
        is_give_up: isGiveUp
      })
    });
    
    if (!res.ok) throw new Error('提交失败');
    return res.json();
  },

  async getStats(token: string) {
    const res = await fetch('/ldy/poetry/flyflower/stats', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (!res.ok) throw new Error('获取统计失败');
    return res.json();
  }
};

// 林黛玉对话API
export const chatApi = {
  async chat(query: string, userNickname: string, token: string) {
    const res = await fetch('/ldy/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ query, user_nickname: userNickname })
    });
    
    if (!res.ok) throw new Error('发送消息失败');
    return res.json();
  }
};

// Token管理
const TOKEN_KEY = 'auth_token';

export const tokenManager = {
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },
  
  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  },
  
  removeToken(): void {
    localStorage.removeItem(TOKEN_KEY);
  }
};
