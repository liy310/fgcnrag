import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';

export default function Couplet() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [coupletType, setCoupletType] = useState<'上联' | '下联'>('上联');
  const [result, setResult] = useState('');
  const [history, setHistory] = useState<Array<{user: string, ldy: string}>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    setLoading(true);
    setError('');

    try {
      const res = await fetch('/ldy/poetry/couplet', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          couplet: input,
          couplet_type: coupletType
        })
      });

      if (!res.ok) throw new Error('对对联失败');
      const data = await res.json();
      setResult(data.matched_line);
      setHistory([...history, { user: input, ldy: data.matched_line }]);
      setInput('');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <header className="page-header">
        <button onClick={() => navigate('/ldy')}>返回</button>
        <h2>对对联</h2>
      </header>

      <div className="page-content">
        <div className="intro-section">
          <p>「小友出句，颦儿来对。」</p>
          <p>输入上联或下联，颦儿为你对上另一句。</p>
        </div>

        <form onSubmit={handleSubmit} className="couplet-form">
          <div className="type-selector">
            <label>
              <input
                type="radio"
                value="上联"
                checked={coupletType === '上联'}
                onChange={() => setCoupletType('上联')}
              />
              我出上联
            </label>
            <label>
              <input
                type="radio"
                value="下联"
                checked={coupletType === '下联'}
                onChange={() => setCoupletType('下联')}
              />
              我出下联
            </label>
          </div>

          <div className="input-group">
            <span className="input-label">{coupletType === '上联' ? '上联' : '下联'}：</span>
            <input
              type="text"
              placeholder={coupletType === '上联' ? '请输入上联...' : '请输入下联...'}
              value={input}
              onChange={e => setInput(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="form-btn" disabled={loading}>
            {loading ? '颦儿思索中...' : '开始对联'}
          </button>
        </form>

        {error && <div className="error-message">{error}</div>}

        {result && (
          <div className="result-section couplet-result">
            <div className="couplet-display">
              <div className="couplet-user">
                <span className="label">小友：</span>
                <span className="text">{history[history.length - 1]?.user}</span>
              </div>
              <div className="couplet-ldy">
                <span className="label">颦儿：</span>
                <span className="text">{result}</span>
              </div>
            </div>
          </div>
        )}

        {history.length > 1 && (
          <div className="history-section">
            <h3>对联记录</h3>
            {history.slice(0, -1).map((item, index) => (
              <div key={index} className="history-item">
                <div className="history-pair">
                  <span className="label">小友：</span>
                  <span>{item.user}</span>
                </div>
                <div className="history-pair">
                  <span className="label">颦儿：</span>
                  <span>{item.ldy}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
