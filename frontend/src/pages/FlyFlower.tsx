import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import { flyFlowerApi } from '../api';

const KEYWORDS_BY_DIFFICULTY = {
  easy: ['花', '月', '风', '春', '山', '水', '云', '雨', '酒', '雪', '天', '江', '夜', '人'],
  normal: ['柳', '荷', '梅', '兰', '舟', '楼', '烟', '霞', '琴', '书', '君', '客', '梦', '情', '秋'],
  hard: ['笛', '雁', '帆', '尘', '路', '乡', '寒', '暖', '霜', '露']
};

const DIFFICULTY_INFO = {
  easy: { label: '简单', desc: '常见字，适合初学者' },
  normal: { label: '普通', desc: '有一定诗意，考验功底' },
  hard: { label: '困难', desc: '意境深远，挑战极限' }
};

interface GameResponse {
  ai_line: string;
  ai_position: number;
  user_position: number;
  current_round: number;
  is_game_over: boolean;
  message: string;
  total_rounds: number;
  stats: any;
  user_fail_count: number;
  is_user_win: boolean;
  is_position_valid: boolean;
}

export default function FlyFlower() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [gameStarted, setGameStarted] = useState(false);
  const [keyword, setKeyword] = useState('');
  const [difficulty, setDifficulty] = useState<string | null>(null);
  const [userLine, setUserLine] = useState('');
  const [aiLine, setAiLine] = useState('');
  const [message, setMessage] = useState('');
  const [aiPosition, setAiPosition] = useState(1);
  const [userPosition, setUserPosition] = useState(2);
  const [currentRound, setCurrentRound] = useState(1);
  const [gameOver, setGameOver] = useState(false);
  const [totalRounds, setTotalRounds] = useState(0);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [userFailCount, setUserFailCount] = useState(0);
  const [isUserWin, setIsUserWin] = useState(false);

  const startGame = async (kw: string) => {
    if (!token || !difficulty) return;
    setLoading(true);
    try {
      const res: GameResponse = await flyFlowerApi.start(kw, difficulty, token);
      setKeyword(kw);
      setAiLine(res.ai_line);
      setMessage(res.message);
      setAiPosition(res.ai_position);
      setUserPosition(res.user_position);
      setCurrentRound(res.current_round);
      setGameStarted(true);
      setGameOver(false);
      setUserFailCount(0);
      setIsUserWin(false);
    } catch (err) {
      alert('开始游戏失败，请检查网络');
    } finally {
      setLoading(false);
    }
  };

  const submitLine = async () => {
    if (!token || !userLine.trim()) return;
    setLoading(true);
    try {
      const res: GameResponse = await flyFlowerApi.play(
        keyword, userLine, userPosition, currentRound, difficulty!, userFailCount, false, token!
      );
      
      setAiLine(res.ai_line);
      setMessage(res.message);
      setAiPosition(res.ai_position);
      setUserPosition(res.user_position);
      setCurrentRound(res.current_round);
      setTotalRounds(res.total_rounds);
      setUserLine('');
      setUserFailCount(res.user_fail_count);
      setIsUserWin(res.is_user_win);
      
      if (res.is_game_over) {
        setGameOver(true);
        if (res.stats) {
          setStats(res.stats);
        }
      }
    } catch (err) {
      alert('提交失败');
    } finally {
      setLoading(false);
    }
  };

  const endGame = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res: GameResponse = await flyFlowerApi.play(
        keyword, '', userPosition, currentRound, difficulty!, userFailCount, true, token!
      );
      setMessage(res.message);
      setTotalRounds(res.total_rounds);
      setStats(res.stats);
      setGameOver(true);
      setIsUserWin(false);
    } finally {
      setLoading(false);
    }
  };

  const resetGame = () => {
    setGameStarted(false);
    setGameOver(false);
    setAiLine('');
    setMessage('');
    setUserLine('');
    setKeyword('');
    setTotalRounds(0);
    setAiPosition(1);
    setUserPosition(2);
    setCurrentRound(1);
    setUserFailCount(0);
    setIsUserWin(false);
  };

  const goBackToDifficulty = () => {
    setDifficulty(null);
    resetGame();
  };

  const renderDifficultySelect = () => (
    <div className="start-section">
      <p className="instruction">请先选择难度等级：</p>
      <div className="difficulty-cards">
        {Object.entries(DIFFICULTY_INFO).map(([key, info]) => (
          <div 
            key={key} 
            className={`difficulty-card ${key}`}
            onClick={() => setDifficulty(key)}
          >
            <h3>{info.label}</h3>
            <p>{info.desc}</p>
            <span className="keyword-count">{KEYWORDS_BY_DIFFICULTY[key as keyof typeof KEYWORDS_BY_DIFFICULTY].length}个关键字</span>
          </div>
        ))}
      </div>
    </div>
  );

  const renderKeywordSelect = () => (
    <div className="start-section">
      <div className="difficulty-badge">
        难度：{DIFFICULTY_INFO[difficulty as keyof typeof DIFFICULTY_INFO]?.label}
        <button className="change-difficulty" onClick={goBackToDifficulty}>切换</button>
      </div>
      <p className="instruction">选择一个关键字开始游戏：</p>
      <div className="keyword-grid">
        {KEYWORDS_BY_DIFFICULTY[difficulty as keyof typeof KEYWORDS_BY_DIFFICULTY]?.map(kw => (
          <button
            key={kw}
            className="keyword-btn"
            onClick={() => startGame(kw)}
            disabled={loading}
          >
            {kw}
          </button>
        ))}
      </div>
    </div>
  );

  const getTurnHint = () => {
    if (gameOver) {
      if (isUserWin) {
        return <span className="win-hint">恭喜！你战胜了颦儿！</span>;
      } else {
        return <span className="lose-hint">颦儿获胜，再接再厉！</span>;
      }
    }
    return <span>轮到你了，请对第{userPosition}字</span>;
  };

  return (
    <div className="flyflower-container">
      <header className="page-header">
        <button onClick={() => navigate('/ldy')}>返回</button>
        <h2>飞花令</h2>
      </header>
      
      <main className="flyflower-main">
        {!gameStarted ? (
          <>
            {!difficulty ? renderDifficultySelect() : renderKeywordSelect()}
          </>
        ) : (
          <div className="game-section">
            <div className="keyword-display">
              难度：<strong>{DIFFICULTY_INFO[difficulty as keyof typeof DIFFICULTY_INFO]?.label}</strong>
              &nbsp;&nbsp;关键字：<strong>{keyword}</strong>
            </div>
            <div className="position-hint">
              {getTurnHint()}
            </div>
            
            <div className="poem-display">
              <div className="ai-poem">
                <span className="label">颦儿：</span>
                <p>{aiLine || '...'}</p>
              </div>
            </div>
            
            {message && <p className="game-message">{message}</p>}
            
            {gameOver ? (
              <div className="game-over">
                <p>本局共对了 <strong>{totalRounds}</strong> 轮</p>
                {stats && (
                  <div className="stats">
                    <p>历史最佳：{stats.best_rounds} 轮</p>
                    <p>总游戏次数：{stats.total_games}</p>
                    <p>成功次数：{stats.success_games}</p>
                  </div>
                )}
                <div className="game-over-btns">
                  <button onClick={goBackToDifficulty}>重新选择</button>
                  <button onClick={() => {
                    setDifficulty(difficulty!);
                    setGameStarted(false);
                  }}>再玩一局</button>
                </div>
              </div>
            ) : (
              <div className="input-section">
                <input
                  type="text"
                  placeholder={`请输入含有"${keyword}"的七言诗句（第${userPosition}字）`}
                  value={userLine}
                  onChange={e => setUserLine(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && submitLine()}
                />
                <div className="btn-group">
                  <button onClick={submitLine} disabled={loading}>提交</button>
                  <button onClick={endGame} disabled={loading} className="give-up">结束</button>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
