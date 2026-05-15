import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';

export default function PoetryAppreciate() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [poetry, setPoetry] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!poetry.trim()) return;

    setLoading(true);
    setError('');
    setResult('');

    try {
      const res = await fetch('/ldy/poetry/appreciate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ poetry_text: poetry })
      });

      if (!res.ok) throw new Error('鉴赏失败');
      const data = await res.json();
      setResult(data.result);
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
        <h2>诗词鉴赏</h2>
      </header>

      <div className="page-content">
        <div className="intro-section">
          <p>「小友若有佳作，颦儿愿为品鉴。」</p>
          <p>请输入你想要鉴赏的诗词，颦儿将为你细细点评。</p>
        </div>

        <form onSubmit={handleSubmit} className="poetry-form">
          <textarea
            placeholder="在此输入诗词..."
            value={poetry}
            onChange={e => setPoetry(e.target.value)}
            rows={6}
            required
          />
          <button type="submit" className="form-btn" disabled={loading}>
            {loading ? '颦儿品鉴中...' : '请求鉴赏'}
          </button>
        </form>

        {error && <div className="error-message">{error}</div>}

        {result && (
          <div className="result-section">
            <h3>颦儿点评：</h3>
            <div className="result-content">{result}</div>
          </div>
        )}
      </div>
    </div>
  );
}
