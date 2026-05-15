import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect, createContext, useContext } from 'react';
import { User, authApi, tokenManager } from './api';
import Login from './pages/Login';
import SelectMode from './pages/SelectMode';
import FourClassicQA from './pages/FourClassicQA';
import LDYHome from './pages/LDYHome';
import FlyFlower from './pages/FlyFlower';
import Chat from './pages/Chat';
import PoetryAppreciate from './pages/PoetryAppreciate';
import Couplet from './pages/Couplet';
import EssayReview from './pages/EssayReview';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedToken = tokenManager.getToken();
    if (savedToken) {
      setToken(savedToken);
      authApi.getMe(savedToken)
        .then(setUser)
        .catch(() => tokenManager.removeToken())
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (username: string, password: string) => {
    const { access_token } = await authApi.login(username, password);
    tokenManager.setToken(access_token);
    setToken(access_token);
    const userData = await authApi.getMe(access_token);
    setUser(userData);
  };

  const register = async (username: string, email: string, password: string) => {
    await authApi.register(username, email, password);
    await login(username, password);
  };

  const logout = () => {
    tokenManager.removeToken();
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { token, isLoading } = useAuth();
  
  // 加载中时保持当前页面，不进行重定向
  if (isLoading) {
    return null;
  }
  
  // 加载完成后，有 token 则显示内容，否则重定向到登录
  return token ? <>{children}</> : <Navigate to="/login" />;
}

function RootRedirect() {
  const { token, isLoading } = useAuth();
  
  // 加载中时保持当前页面
  if (isLoading) {
    return null;
  }
  
  // 加载完成后，有 token 重定向到 /select，否则到 /login
  return <Navigate to={token ? "/select" : "/login"} replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <HashRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          {/* 主选择页 */}
          <Route path="/select" element={
            <ProtectedRoute>
              <SelectMode />
            </ProtectedRoute>
          } />
          
          {/* 四大名著问答 */}
          <Route path="/four-classic" element={
            <ProtectedRoute>
              <FourClassicQA />
            </ProtectedRoute>
          } />
          
          {/* 林黛玉首页 */}
          <Route path="/ldy" element={
            <ProtectedRoute>
              <LDYHome />
            </ProtectedRoute>
          } />
          
          {/* 林黛玉子功能 */}
          <Route path="/ldy/flyflower" element={
            <ProtectedRoute>
              <FlyFlower />
            </ProtectedRoute>
          } />
          <Route path="/ldy/chat" element={
            <ProtectedRoute>
              <Chat />
            </ProtectedRoute>
          } />
          <Route path="/ldy/poetry" element={
            <ProtectedRoute>
              <PoetryAppreciate />
            </ProtectedRoute>
          } />
          <Route path="/ldy/couplet" element={
            <ProtectedRoute>
              <Couplet />
            </ProtectedRoute>
          } />
          <Route path="/ldy/essay" element={
            <ProtectedRoute>
              <EssayReview />
            </ProtectedRoute>
          } />
          
          {/* 根路径重定向 */}
          <Route path="/" element={<RootRedirect />} />
        </Routes>
      </HashRouter>
    </AuthProvider>
  );
}
