import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';

export default function EssayReview() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [essayContent, setEssayContent] = useState('');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fileName, setFileName] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!essayContent.trim() && !fileName) return;

    setLoading(true);
    setError('');
    setResult('');

    try {
      const formData = new FormData();
      
      if (fileName && fileInputRef.current?.files?.[0]) {
        formData.append('file', fileInputRef.current.files[0]);
      }
      if (essayContent.trim()) {
        formData.append('essay_content', essayContent);
      }

      const res = await fetch('/ldy/academic/essay_review', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!res.ok) throw new Error('点评失败');
      const data = await res.json();
      setResult(data.review);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      setEssayContent('');
    }
  };

  return (
    <div className="chat-container">
      <header className="page-header">
        <button onClick={() => navigate('/ldy')}>返回</button>
        <h2>作文点评</h2>
      </header>

      <div className="page-content">
        <div className="intro-section">
          <p>「小友若有文章，颦儿愿为批阅。」</p>
          <p>上传作文文件或直接输入文本，颦儿将为你细致点评。</p>
          <p className="file-hint">支持格式：.txt, .docx, .pdf（最大5MB）</p>
        </div>

        <form onSubmit={handleSubmit} className="essay-form">
          <div className="file-upload-section">
            <label className="file-upload-btn">
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.docx,.pdf"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              {fileName ? `已选择: ${fileName}` : '选择文件上传'}
            </label>
            {fileName && (
              <button type="button" className="clear-file" onClick={() => {
                setFileName('');
                if (fileInputRef.current) fileInputRef.current.value = '';
              }}>
                清除
              </button>
            )}
          </div>

          <div className="divider">
            <span>或</span>
          </div>

          <textarea
            placeholder="或者在此直接输入作文内容..."
            value={essayContent}
            onChange={e => {
              setEssayContent(e.target.value);
              if (e.target.value) setFileName('');
            }}
            rows={12}
          />

          <button type="submit" className="form-btn" disabled={loading || (!essayContent.trim() && !fileName)}>
            {loading ? '颦儿批阅中...' : '提交点评'}
          </button>
        </form>

        {error && <div className="error-message">{error}</div>}

        {result && (
          <div className="result-section essay-result">
            <h3>颦儿批语：</h3>
            <div className="result-content">{result}</div>
          </div>
        )}
      </div>
    </div>
  );
}
