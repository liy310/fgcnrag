import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import './SelectMode.css';

export default function SelectMode() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="select-container">
      <header className="select-header">
        <div className="ldy-title">
          <p className="quote">「腹有诗书气自华」</p>
        </div>
        <div className="user-info">
          <span>欢迎，{user?.username}</span>
          <button onClick={logout} className="logout-btn">退出</button>
        </div>
      </header>

      <main className="select-main">
        <h1 className="select-title">选择学习模块</h1>

        <div className="mode-cards">
          <div className="mode-card classic" onClick={() => navigate('/four-classic')}>
            <div className="card-icon">
              <img src="/picture/四大名著图标.png" alt="四大名著" />
            </div>
            <h2>四大名著知识问答</h2>
            <p>涵盖《红楼梦》《西游记》《水浒传》《三国演义》，颦儿与你畅游经典</p>
            <div className="card-tags">
              <span>红楼梦</span>
              <span>西游记</span>
              <span>水浒传</span>
              <span>三国演义</span>
            </div>
          </div>

          <div className="mode-card ldy" onClick={() => navigate('/ldy')}>
            <div className="card-icon">
              <img src="/picture/林黛玉图标.png" alt="林黛玉" />
            </div>
            <h2>林黛玉</h2>
            <p>与颦儿吟诗作对，谈古论今，体验大观园的诗意人生</p>
            <div className="card-tags">
              <span>飞花令</span>
              <span>诗词鉴赏</span>
              <span>对对联</span>
              <span>作文点评</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
