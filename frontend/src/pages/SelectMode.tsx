import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import './SelectMode.css';

export default function SelectMode() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="select-container">
      <header className="select-header">
        <div className="select-title-text">
          <p className="quote">「腹有诗书气自华」</p>
        </div>
        <div className="user-info">
          <span>欢迎，{user?.username}</span>
          <button onClick={logout} className="logout-btn">退出</button>
        </div>
      </header>

      <main className="select-main">
        <h1 className="select-title">四大名著</h1>

        <div className="mode-cards">
          <div className="mode-card classic" onClick={() => navigate('/four-classic')}>
            <div className="card-icon">
              <img src="/picture/四大名著图标.png" alt="四大名著" />
            </div>
            <h2>四大名著知识问答</h2>
            <p>涵盖《红楼梦》《西游记》《水浒传》《三国演义》，一起畅游经典</p>
            <div className="card-tags">
              <span>红楼梦</span>
              <span>西游记</span>
              <span>水浒传</span>
              <span>三国演义</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
