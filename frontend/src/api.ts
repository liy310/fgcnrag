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
