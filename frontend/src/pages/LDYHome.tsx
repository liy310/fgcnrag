import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import { chatApi } from '../api';
import './LDYHome.css';

type FeatureType = 'couplet' | 'flyflower' | 'poetry' | 'essay' | null;
type RightPanelType = 'intro' | 'chat';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  empathy?: string;
}

const FEATURES: { key: FeatureType; label: string; icon: string }[] = [
  { key: 'couplet', label: '对对联', icon: '/picture/对对联图标.png' },
  { key: 'flyflower', label: '飞花令', icon: '/picture/飞花令图标.png' },
  { key: 'poetry', label: '诗词鉴赏', icon: '/picture/诗词鉴赏图标.png' },
  { key: 'essay', label: '作文点评', icon: '/picture/作文点评图标.png' },
];

export default function LDYHome() {
  const { token, user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeFeature, setActiveFeature] = useState<FeatureType>(null);
  const [rightPanel, setRightPanel] = useState<RightPanelType>('intro');

  // Chat states
  const [chatQuery, setChatQuery] = useState('');
  const [chatMessages, setChatMessages] = useState<Message[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Feature content states
  const [featureInput, setFeatureInput] = useState('');
  const [featureResult, setFeatureResult] = useState('');
  const [featureLoading, setFeatureLoading] = useState(false);
  const [featureError, setFeatureError] = useState('');
  const [coupletType, setCoupletType] = useState<'上联' | '下联'>('上联');
  const [essayFileName, setEssayFileName] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // FlyFlower game states
  const [ffKeyword, setFfKeyword] = useState('');
  const [ffDifficulty, setFfDifficulty] = useState<string | null>(null);
  const [ffGameStarted, setFfGameStarted] = useState(false);
  const [ffUserLine, setFfUserLine] = useState('');
  const [ffAiLine, setFfAiLine] = useState('');
  const [ffMessage, setFfMessage] = useState('');
  const [ffUserPosition, setFfUserPosition] = useState(2);
  const [ffCurrentRound, setFfCurrentRound] = useState(1);
  const [ffGameOver, setFfGameOver] = useState(false);
  const [ffUserFailCount, setFfUserFailCount] = useState(0);
  const [ffIsUserWin, setFfIsUserWin] = useState(false);
  const [ffTotalRounds, setFfTotalRounds] = useState(0);
  const [ffStats, setFfStats] = useState<any>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handleFeatureClick = (key: FeatureType) => {
    setActiveFeature(key);
    setFeatureInput('');
    setFeatureResult('');
    setFeatureError('');
    setEssayFileName('');
    // Reset flyflower
    setFfKeyword('');
    setFfDifficulty(null);
    setFfGameStarted(false);
    setFfGameOver(false);
    setFfAiLine('');
    setFfMessage('');
    setFfUserLine('');
    setFfCurrentRound(1);
    setFfUserFailCount(0);
    setFfIsUserWin(false);
    setFfTotalRounds(0);
    setFfStats(null);
  };

  const openChat = () => {
    setRightPanel('chat');
  };

  const closeChat = () => {
    setRightPanel('intro');
  };

  const sendChatMessage = async () => {
    if (!chatQuery.trim() || !token) return;
    const userMsg = { role: 'user' as const, content: chatQuery };
    setChatMessages(prev => [...prev, userMsg]);
    setChatQuery('');
    setChatLoading(true);
    try {
      const res = await chatApi.chat(chatQuery, '小友', token);
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: res.answer,
        empathy: res.empathy
      }]);
    } catch {
      setChatMessages(prev => prev.slice(0, -1));
      alert('发送失败，请检查网络或重新登录');
    } finally {
      setChatLoading(false);
    }
  };

  const handleCoupletSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!featureInput.trim() || !token) return;
    setFeatureLoading(true);
    setFeatureError('');
    try {
      const res = await fetch('/ldy/poetry/couplet', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ couplet: featureInput, couplet_type: coupletType })
      });
      if (!res.ok) throw new Error('对对联失败');
      const data = await res.json();
      setFeatureResult(data.matched_line);
    } catch (err: any) {
      setFeatureError(err.message);
    } finally {
      setFeatureLoading(false);
    }
  };

  const handlePoetrySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!featureInput.trim() || !token) return;
    setFeatureLoading(true);
    setFeatureError('');
    try {
      const res = await fetch('/ldy/poetry/appreciate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ poetry_text: featureInput })
      });
      if (!res.ok) throw new Error('鉴赏失败');
      const data = await res.json();
      setFeatureResult(data.result);
    } catch (err: any) {
      setFeatureError(err.message);
    } finally {
      setFeatureLoading(false);
    }
  };

  const handleEssaySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!featureInput.trim() && !essayFileName) return;
    setFeatureLoading(true);
    setFeatureError('');
    try {
      const formData = new FormData();
      if (essayFileName && fileInputRef.current?.files?.[0]) {
        formData.append('file', fileInputRef.current.files[0]);
      }
      if (featureInput.trim()) {
        formData.append('essay_content', featureInput);
      }
      const res = await fetch('/ldy/academic/essay_review', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      if (!res.ok) throw new Error('点评失败');
      const data = await res.json();
      setFeatureResult(data.review);
    } catch (err: any) {
      setFeatureError(err.message);
    } finally {
      setFeatureLoading(false);
    }
  };

  // FlyFlower helpers
  const KEYWORDS_BY_DIFFICULTY = {
    easy: ['花', '月', '风', '春', '山', '水', '云', '雨', '酒', '雪', '天', '江', '夜', '人'],
    normal: ['柳', '荷', '梅', '兰', '舟', '楼', '烟', '霞', '琴', '书', '君', '客', '梦', '情', '秋'],
    hard: ['笛', '雁', '帆', '尘', '路', '乡', '故国', '流年', '寒', '暖', '霜', '露']
  };
  const DIFFICULTY_INFO: Record<string, { label: string; desc: string }> = {
    easy: { label: '简单', desc: '常见字，适合初学者' },
    normal: { label: '普通', desc: '有一定诗意，考验功底' },
    hard: { label: '困难', desc: '意境深远，挑战极限' }
  };

  const startFlyFlower = async (kw: string) => {
    if (!token || !ffDifficulty) return;
    setFeatureLoading(true);
    try {
      const res = await fetch('/ldy/poetry/flyflower/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ keyword: kw, difficulty: ffDifficulty })
      });
      const data = await res.json();
      setFfKeyword(kw);
      setFfAiLine(data.ai_line);
      setFfMessage(data.message);
      setFfUserPosition(data.user_position);
      setFfCurrentRound(data.current_round);
      setFfGameStarted(true);
      setFfGameOver(false);
      setFfUserFailCount(0);
      setFfIsUserWin(false);
    } catch {
      alert('开始游戏失败');
    } finally {
      setFeatureLoading(false);
    }
  };

  const submitFlyFlower = async () => {
    if (!token || !ffUserLine.trim()) return;
    setFeatureLoading(true);
    try {
      const res = await fetch('/ldy/poetry/flyflower', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          keyword: ffKeyword,
          user_line: ffUserLine,
          user_position: ffUserPosition,
          current_round: ffCurrentRound,
          difficulty: ffDifficulty,
          fail_count: ffUserFailCount,
          is_give_up: false
        })
      });
      const data = await res.json();
      setFfAiLine(data.ai_line);
      setFfMessage(data.message);
      setFfUserPosition(data.user_position);
      setFfCurrentRound(data.current_round);
      setFfTotalRounds(data.total_rounds);
      setFfUserLine('');
      setFfUserFailCount(data.user_fail_count);
      setFfIsUserWin(data.is_user_win);
      if (data.is_game_over) {
        setFfGameOver(true);
        setFfStats(data.stats);
      }
    } catch {
      alert('提交失败');
    } finally {
      setFeatureLoading(false);
    }
  };

  const renderFeatureContent = () => {
    if (!activeFeature) {
      return (
        <div className="feature-welcome">
          <p className="welcome-text">「小友，请选择一个功能，颦儿在此候教。」</p>
        </div>
      );
    }

    switch (activeFeature) {
      case 'couplet':
        return (
          <div className="feature-panel">
            <h3><img src="/picture/对对联图标.png" alt="" className="feature-title-icon" /> 对对联</h3>
            <p className="feature-desc">「小友出句，颦儿来对。」</p>
            <form onSubmit={handleCoupletSubmit} className="feature-form">
              <div className="type-selector">
                <label><input type="radio" value="上联" checked={coupletType === '上联'} onChange={() => setCoupletType('上联')} /> 我出上联</label>
                <label><input type="radio" value="下联" checked={coupletType === '下联'} onChange={() => setCoupletType('下联')} /> 我出下联</label>
              </div>
              <input
                type="text"
                placeholder={coupletType === '上联' ? '请输入上联...' : '请输入下联...'}
                value={featureInput}
                onChange={e => setFeatureInput(e.target.value)}
                required
              />
              <button type="submit" disabled={featureLoading}>
                {featureLoading ? '颦儿思索中...' : '开始对联'}
              </button>
            </form>
            {featureError && <div className="error-msg">{featureError}</div>}
            {featureResult && (
              <div className="result-box">
                <div><span className="label">小友：</span>{featureInput}</div>
                <div><span className="label">颦儿：</span>{featureResult}</div>
              </div>
            )}
          </div>
        );

      case 'flyflower':
        return (
          <div className="feature-panel">
            <h3><img src="/picture/飞花令图标.png" alt="" className="feature-title-icon" /> 飞花令</h3>
            {!ffGameStarted ? (
              !ffDifficulty ? (
                <div className="ff-start">
                  <p className="feature-desc">请选择难度：</p>
                  <div className="difficulty-btns">
                    {Object.entries(DIFFICULTY_INFO).map(([key, info]) => (
                      <button key={key} className={`diff-btn ${key}`} onClick={() => setFfDifficulty(key)}>
                        <strong>{info.label}</strong>
                        <span>{info.desc}</span>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="ff-start">
                  <p className="feature-desc">难度：{DIFFICULTY_INFO[ffDifficulty]?.label} — 选择一个关键字：</p>
                  <div className="keyword-grid">
                    {KEYWORDS_BY_DIFFICULTY[ffDifficulty as keyof typeof KEYWORDS_BY_DIFFICULTY]?.map(kw => (
                      <button key={kw} className="keyword-btn" onClick={() => startFlyFlower(kw)} disabled={featureLoading}>
                        {kw}
                      </button>
                    ))}
                  </div>
                  <button className="back-diff" onClick={() => setFfDifficulty(null)}>← 返回选择难度</button>
                </div>
              )
            ) : (
              <div className="ff-game">
                <div className="ff-info">关键字：<strong>{ffKeyword}</strong> | 第{ffCurrentRound}轮</div>
                <div className="ff-ai-line">
                  <span className="label">颦儿：</span>{ffAiLine || '...'}
                </div>
                {ffMessage && <div className="ff-msg">{ffMessage}</div>}
                {ffGameOver ? (
                  <div className="ff-over">
                    <p>{ffIsUserWin ? '恭喜！你战胜了颦儿！' : '颦儿获胜，再接再厉！'}</p>
                    <p>本局共对了 <strong>{ffTotalRounds}</strong> 轮</p>
                    <button onClick={() => { setFfGameStarted(false); setFfGameOver(false); }}>再玩一局</button>
                  </div>
                ) : (
                  <div className="ff-input">
                    <input
                      type="text"
                      placeholder={`请输入含有"${ffKeyword}"的诗句（第${ffUserPosition}字）`}
                      value={ffUserLine}
                      onChange={e => setFfUserLine(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && submitFlyFlower()}
                    />
                    <div className="ff-btns">
                      <button onClick={submitFlyFlower} disabled={featureLoading}>提交</button>
                      <button className="give-up" onClick={() => setFfGameOver(true)}>结束</button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );

      case 'poetry':
        return (
          <div className="feature-panel">
            <h3><img src="/picture/诗词鉴赏图标.png" alt="" className="feature-title-icon" /> 诗词鉴赏</h3>
            <p className="feature-desc">「小友若有佳作，颦儿愿为品鉴。」</p>
            <form onSubmit={handlePoetrySubmit} className="feature-form">
              <textarea
                placeholder="在此输入诗词..."
                value={featureInput}
                onChange={e => setFeatureInput(e.target.value)}
                rows={5}
                required
              />
              <button type="submit" disabled={featureLoading}>
                {featureLoading ? '颦儿品鉴中...' : '请求鉴赏'}
              </button>
            </form>
            {featureError && <div className="error-msg">{featureError}</div>}
            {featureResult && (
              <div className="result-box">
                <h4>颦儿点评：</h4>
                <div className="result-content">{featureResult}</div>
              </div>
            )}
          </div>
        );

      case 'essay':
        return (
          <div className="feature-panel">
            <h3><img src="/picture/作文点评图标.png" alt="" className="feature-title-icon" /> 作文点评</h3>
            <p className="feature-desc">「小友若有文章，颦儿愿为批阅。」</p>
            <form onSubmit={handleEssaySubmit} className="feature-form">
              <label className="file-upload">
                <input ref={fileInputRef} type="file" accept=".txt,.docx,.pdf" style={{ display: 'none' }}
                  onChange={e => { const f = e.target.files?.[0]; if (f) { setEssayFileName(f.name); setFeatureInput(''); } }} />
                {essayFileName ? `已选择: ${essayFileName}` : '选择文件上传'}
              </label>
              {essayFileName && <button type="button" className="clear-file" onClick={() => { setEssayFileName(''); if (fileInputRef.current) fileInputRef.current.value = ''; }}>清除</button>}
              <div className="divider"><span>或</span></div>
              <textarea
                placeholder="或者在此直接输入作文内容..."
                value={featureInput}
                onChange={e => { setFeatureInput(e.target.value); if (e.target.value) setEssayFileName(''); }}
                rows={6}
              />
              <button type="submit" disabled={featureLoading || (!featureInput.trim() && !essayFileName)}>
                {featureLoading ? '颦儿批阅中...' : '提交点评'}
              </button>
            </form>
            {featureError && <div className="error-msg">{featureError}</div>}
            {featureResult && (
              <div className="result-box">
                <h4>颦儿批语：</h4>
                <div className="result-content">{featureResult}</div>
              </div>
            )}
          </div>
        );
    }
  };

  return (
    <div className="ldy-container">
      <header className="ldy-header">
        <button className="back-btn" onClick={() => navigate('/select')}>返回</button>
        <div className="ldy-title">
          <h1>林黛玉</h1>
          <p className="quote">「花谢花飞飞满天，红消香断有谁怜」</p>
        </div>
        <div className="user-info">
          <span>欢迎，{user?.username}</span>
          <button onClick={logout} className="logout-btn">退出</button>
        </div>
      </header>

      <main className="ldy-main">
        {/* 中间：功能按钮 + 内容区 */}
        <section className="ldy-center">
          <div className="feature-tabs">
            {FEATURES.map(f => (
              <button
                key={f.key}
                className={`feature-tab ${activeFeature === f.key ? 'active' : ''}`}
                onClick={() => handleFeatureClick(f.key)}
              >
                <img src={f.icon} alt={f.label} className="tab-icon-img" />
                <span className="tab-label">{f.label}</span>
              </button>
            ))}
          </div>

          <div className="feature-content">
            {renderFeatureContent()}
          </div>
        </section>

        {/* 右侧：人物介绍 / 聊天 */}
        <aside className={`ldy-right ${rightPanel === 'chat' ? 'chat-open' : ''}`}>
          {rightPanel === 'intro' ? (
            <div className="intro-panel">
              <div className="intro-header">
                <h3>人物介绍</h3>
                <img src="/picture/黛玉头像.jpg" alt="林黛玉" className="intro-avatar" />
              </div>
              <div className="intro-content">
                <p><strong>姓名：</strong>林黛玉</p>
                <p><strong>别号：</strong>颦儿、潇湘妃子</p>
                <p><strong>居所：</strong>潇湘馆</p>
                <p><strong>性格：</strong>敏感细腻、才情横溢、孤高自许、多愁善感</p>
                <div className="intro-divider"></div>
                <p className="intro-quote">「质本洁来还洁去，强于污淖陷渠沟」</p>
                <p className="intro-quote">「一年三百六十日，风刀霜剑严相逼」</p>
                <div className="intro-divider"></div>
                <p>林黛玉，金陵十二钗之首，贾宝玉的表妹。她自幼聪慧，博览群书，诗词造诣极高。其诗风清丽婉约，情感真挚动人，是大观园中公认的才女。</p>
                <p>她生性敏感，体弱多病，却有一颗纯净高洁的心灵。她与宝玉情深意切，却因种种缘由未能终成眷属，最终泪尽而逝，令人扼腕叹息。</p>
              </div>
              {/* 底部聊天输入框 */}
              <div className="intro-chat-bar" onClick={openChat}>
                <span className="chat-bar-text">点击与颦儿对话...</span>
                <span className="chat-bar-arrow">→</span>
              </div>
            </div>
          ) : (
            <div className="chat-panel">
              <div className="chat-header">
                <div className="chat-header-left">
                  <img src="/picture/黛玉头像.jpg" alt="颦儿" className="chat-header-avatar" />
                  <div className="chat-header-name">
                    <span className="name">林黛玉</span>
                    <span className="sub">在线</span>
                  </div>
                </div>
                <button className="close-chat" onClick={closeChat}>✕</button>
              </div>
              <div className="chat-messages">
                {chatMessages.length === 0 && (
                  <div className="chat-welcome">
                    <img src="/picture/黛玉头像.jpg" alt="颦儿" className="chat-welcome-avatar" />
                    <span className="chat-welcome-name">林黛玉</span>
                    <p>颦儿在此恭候，小友有何心事，不妨说来听听。</p>
                  </div>
                )}
                {chatMessages.map((msg, idx) => (
                  <div key={idx} className={`chat-msg ${msg.role}`}>
                    {msg.role === 'assistant' ? (
                      <img src="/picture/黛玉头像.jpg" alt="颦儿" className="msg-avatar" />
                    ) : (
                      <img src="/picture/用户头像.png" alt="小友" className="msg-avatar" />
                    )}
                    <div className="msg-content">
                      {msg.empathy && <div className="empathy-tag">{msg.empathy}</div>}
                      <div className="msg-bubble">{msg.content}</div>
                    </div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="chat-msg assistant">
                    <img src="/picture/黛玉头像.jpg" alt="颦儿" className="msg-avatar" />
                    <div className="msg-content">
                      <div className="msg-bubble loading">颦儿正在思索...</div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
              <div className="chat-input-area">
                <input
                  type="text"
                  placeholder="输入你的问题或心事..."
                  value={chatQuery}
                  onChange={e => setChatQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && sendChatMessage()}
                  disabled={chatLoading}
                />
                <button onClick={sendChatMessage} disabled={chatLoading}>发送</button>
              </div>
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}
