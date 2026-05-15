import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import { chatApi } from '../api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  empathy?: string;
}

export default function Chat() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!query.trim() || !token) return;
    
    const userMsg = { role: 'user' as const, content: query };
    setMessages(prev => [...prev, userMsg]);
    setQuery('');
    setLoading(true);
    
    try {
      const res = await chatApi.chat(query, '小友', token);
      const assistantMsg = { 
        role: 'assistant' as const, 
        content: res.answer,
        empathy: res.empathy
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err) {
      // 移除失败的消息
      setMessages(prev => prev.slice(0, -1));
      alert('发送失败，请检查网络或重新登录');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <header className="header">
        <button onClick={() => navigate('/ldy')}>返回首页</button>
        <span>林黛玉 · 对话</span>
      </header>
      
      <main className="chat-main">
        <div className="messages">
          {messages.length === 0 && (
            <div className="welcome-message">
              <p>颦儿在此恭候，小友有何心事，不妨说来听听。</p>
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              {msg.empathy && (
                <div className="empathy">{msg.empathy}</div>
              )}
              <div className="content">{msg.content}</div>
            </div>
          ))}
          
          {loading && (
            <div className="message assistant loading">
              <div className="content">颦儿正在思索...</div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        <div className="input-area">
          <input
            type="text"
            placeholder="输入你的问题或心事..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendMessage()}
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading}>发送</button>
        </div>
      </main>
    </div>
  );
}
