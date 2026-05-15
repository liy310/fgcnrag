import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import './FourClassicQA.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function FourClassicQA() {
  const { token, user, logout } = useAuth();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await fetch('/fgcn/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ query: userMessage })
      });

      if (!response.ok) throw new Error('请求失败');
      const data = await response.json();

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response || data.answer || data.result || JSON.stringify(data)
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '咨询人员过多，请稍后重试'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="qa-container">
      <header className="qa-header">
        <button className="back-btn" onClick={() => navigate('/select')}>
          返回
        </button>
        <div className="qa-title">
          <h1>四大名著知识问答</h1>
          <p className="quote">「读万卷书，行万里路」</p>
        </div>
        <div className="user-info">
          <span>欢迎，{user?.username}</span>
          <button onClick={logout} className="logout-btn">退出</button>
        </div>
      </header>

      <div className="book-icons">
        <img src="/picture/红楼梦.png" alt="红楼梦" className="book-icon" title="红楼梦" />
        <img src="/picture/西游记.png" alt="西游记" className="book-icon" title="西游记" />
        <img src="/picture/水浒传.png" alt="水浒传" className="book-icon" title="水浒传" />
        <img src="/picture/三国演义.png" alt="三国演义" className="book-icon" title="三国演义" />
      </div>

      <main className="qa-main">
        <div className="scroll-outer">
          <div className="scroll-left-pillar"></div>
          <div className="scroll-container">
            <div className="scroll-content">
              <div className="scroll-corner top-left"></div>
              <div className="scroll-corner top-right"></div>
              <div className="scroll-corner bottom-left"></div>
              <div className="scroll-corner bottom-right"></div>
              <div className="scroll-seal"></div>
              <div className="messages">
                {messages.length === 0 && (
                  <div className="welcome-message">
                    <div className="welcome-icon">
                      <img src="/picture/书籍2.png" alt="书籍" />
                    </div>
                    <p>欢迎来到四大名著知识问答</p>
                    <p className="welcome-sub">红楼梦 · 西游记 · 水浒传 · 三国演义</p>
                  </div>
                )}

                {messages.map((msg, index) => (
                  <div key={index} className={`message ${msg.role}`}>
                    <div className="avatar">
                      {msg.role === 'user' ? (
                        <img src="/picture/用户头像.png" alt="用户" className="avatar-img" />
                      ) : (
                        <img src="/picture/四大名著知识问答头像.png" alt="" className="avatar-img" />
                      )}
                    </div>
                    <div className="content">
                      <div className="bubble">{msg.content}</div>
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="message assistant">
                    <div className="avatar">
                      <img src="/picture/四大名著知识问答头像.png" alt="" className="avatar-img" />
                    </div>
                    <div className="content">
                      <div className="bubble loading">
                        <span>.</span><span>.</span><span>.</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>
          <div className="scroll-right-pillar"></div>
        </div>

        <form className="input-area" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="请输入何疑问，尽管道来..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            {loading ? '...' : '发送'}
          </button>
        </form>
      </main>
    </div>
  );
}
