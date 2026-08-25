import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';

const Exam = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const examId = searchParams.get('set') || 'mock';
  const subject = searchParams.get('subject') || 'Biology';
  const examName = searchParams.get('name') || 'Practice Exam';
  
  const MOCK_QUESTIONS = React.useMemo(() => {
    const topics = {
      'Biology': ['Cell Biology', 'Genetics', 'Ecology', 'Human Anatomy'],
      'Physics': ['Mechanics', 'Thermodynamics', 'Electromagnetism', 'Optics'],
      'Chemistry': ['Organic', 'Inorganic', 'Physical', 'Biochemistry'],
      'Mathematics': ['Calculus', 'Algebra', 'Trigonometry', 'Geometry']
    };
    const topicList = topics[subject] || topics['Biology'];
    return Array.from({ length: 45 }, (_, i) => ({
      id: `q${i + 1}`,
      text: `Mock Question ${i + 1} for ${subject}: Which of the following is correct?`,
      options: ['Option A', 'Option B', 'Option C', 'Option D'],
      topic: topicList[i % topicList.length]
    }));
  }, [subject]);
  
  const [started, setStarted] = useState(false);
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState({});
  const [skipped, setSkipped] = useState(new Set());
  const [timeLeft, setTimeLeft] = useState(60 * 60);
  const videoRef = React.useRef(null);

  const [studentDetails, setStudentDetails] = useState({ name: 'Loading...', id: 'Loading...' });

  useEffect(() => {
    fetch('/api/auth/me')
      .then(res => res.json())
      .then(data => {
        if (data.user_id) {
          setStudentDetails({ name: data.name || 'Student', id: data.user_id });
        } else {
          setStudentDetails({ name: 'Guest Student', id: 'GST-001' });
        }
      })
      .catch(() => {
        setStudentDetails({ name: 'Student (Offline)', id: 'STD-123' });
      });
  }, []);

  useEffect(() => {
    if (!started) return;
    
    // Start Camera
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            videoRef.current.play().catch(e => console.error("Play error:", e));
          }
        })
        .catch(err => console.error("Camera error:", err));
    }

    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          endExam(answers);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [started]);

  // Cleanup camera on unmount
  useEffect(() => {
    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks();
        tracks.forEach(track => track.stop());
      }
    };
  }, []);

  const handleAnswer = (optionIdx) => {
    setAnswers(prev => ({ ...prev, [currentQ]: optionIdx }));
    setSkipped(prev => {
      const newSkipped = new Set(prev);
      newSkipped.delete(currentQ);
      return newSkipped;
    });
  };

  const handleSkip = () => {
    setSkipped(prev => new Set(prev).add(currentQ));
    if (currentQ < MOCK_QUESTIONS.length - 1) setCurrentQ(prev => prev + 1);
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const endExam = (finalAnswers) => {
    alert(`Exam Submitted Successfully! You answered ${Object.keys(finalAnswers).length} questions.`);
    navigate('/student/institution/dashboard');
  };

  return (
    <>
      <style>{`
        body { overflow: ${examId ? 'hidden' : 'auto'} !important; }
        .nav, .navbar { display: none !important; }
        .main-content { margin-left: 0 !important; padding: 0 !important; max-width: 100% !important; }
      `}</style>
      
      <div className="exam-topbar" id="examTopbar" style={{ display: examId ? "flex" : "none" }}>
        <div className="exam-topbar-left">
          <div className="brand-icon small">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          </div>
          <span className="exam-title-text" style={{ color: "#fff" }}>Mr.<span className="brand-ai">E</span></span>
        </div>
        <div className="exam-topbar-center">
          <span className="exam-badge set-badge" id="topbarSet">{examName}</span>
          <span className="exam-badge subject-badge" id="topbarSubject">{subject}</span>
        </div>
        <div className="exam-topbar-right">
          <div className="timer-block">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            <span id="timerDisplay" className="timer-text">{formatTime(timeLeft)}</span>
          </div>
        </div>
      </div>

      <div className="overlay" id="entryOverlay" style={{ display: examId && !started ? "flex" : "none" }}>
        <div className="entry-modal">
          <div className="entry-modal-top">
            <div className="entry-icon">🎓</div>
            <h2>Ready to Begin?</h2>
            <p>Verify your details to start the exam</p>
          </div>
          <div className="entry-form">
            <input type="hidden" id="studentName" />
            <input type="hidden" id="studentRoll" />

            <div className="candidate-profile-box" style={{"background":"var(--s2)","border":"1px solid var(--border)","borderRadius":"var(--r)","padding":"14px 16px","marginBottom":"16px"}}>
              <div style={{"display":"flex","justifyContent":"space-between","alignItems":"center","padding":"4px 0","fontSize":"0.88rem"}}>
                <span style={{"color":"var(--muted)"}}>👤 Student Name:</span>
                <span id="displayCandidateName" style={{"fontWeight":"700","color":"var(--text)"}}>{studentDetails.name}</span>
              </div>
              <div style={{"display":"flex","justifyContent":"space-between","alignItems":"center","padding":"4px 0","fontSize":"0.88rem"}}>
                <span style={{"color":"var(--muted)"}}>🆔 Student ID:</span>
                <span id="displayCandidateRoll" style={{"fontWeight":"700","color":"var(--purple-l)","fontFamily":"monospace"}}>{studentDetails.id}</span>
              </div>
            </div>

            <div className="exam-info-box" id="examInfoBox">
              <div className="info-row"><span>📚 Subject:</span><span id="infoSubject">{subject}</span></div>
              <div className="info-row"><span>❓ Questions:</span><span id="infoQCount">{MOCK_QUESTIONS.length}</span></div>
              <div className="info-row"><span>⏱ Time Limit:</span><span>60 minutes</span></div>
            </div>
            
            <button className="btn-generate" onClick={() => setStarted(true)}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              Begin Exam
            </button>
          </div>
        </div>
      </div>

      <div className="exam-layout" id="examLayout" style={{ display: started ? "flex" : "none" }}>

        <aside className="exam-sidebar">
          <div id="proctorContainer" style={{"marginBottom":"15px","borderRadius":"8px","overflow":"hidden","background":"#000","border":"1px solid var(--border)","aspectRatio":"4/3","display":"flex","alignItems":"center","justifyContent":"center"}}>
            <video id="proctorVideo" ref={videoRef} autoPlay muted playsInline style={{"width":"100%","height":"100%","objectFit":"cover","display":"block","transform":"scaleX(-1)"}}></video>
          </div>
          <div className="sidebar-student-info" id="sidebarStudentInfo"></div>
          <div className="sidebar-section-title">Question Navigator</div>
          <div className="q-grid" id="qGrid">
            {MOCK_QUESTIONS.map((q, i) => (
              <button
                key={q.id}
                onClick={() => setCurrentQ(i)}
                className={`q-grid-btn ${answers[i] !== undefined ? 'answered' : skipped.has(i) ? 'skipped' : ''} ${i === currentQ ? 'current' : ''}`.trim()}
              >
                {i + 1}
              </button>
            ))}
          </div>
          <div className="q-legend">
            <div className="legend-row"><span className="legend-box answered"></span>Answered</div>
            <div className="legend-row"><span className="legend-box skipped"></span>Skipped</div>
            <div className="legend-row"><span className="legend-box current"></span>Current</div>
            <div className="legend-row"><span className="legend-box unanswered"></span>Not visited</div>
          </div>
          <div className="sidebar-progress">
            <div className="sidebar-prog-label">
              <span id="answeredCount">{Object.keys(answers).length}</span> / <span id="totalCount">{MOCK_QUESTIONS.length}</span> answered
            </div>
            <div className="sidebar-prog-bar"><div className="sidebar-prog-fill" style={{ width: `${(Object.keys(answers).length / MOCK_QUESTIONS.length) * 100}%` }}></div></div>
          </div>
          <button className="btn-submit-exam" onClick={() => endExam(answers)}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
            Submit Paper
          </button>
        </aside>

        <div className="exam-content">
          <div className="exam-top-bar">
            <div className="exam-top-prog">
              <div className="exam-top-prog-fill" style={{ width: `${((currentQ + 1) / MOCK_QUESTIONS.length) * 100}%` }}></div>
            </div>
          </div>

          <div className="question-panel" id="questionPanel">
            <div className="q-meta-row">
              <span className="q-num-badge">Q {currentQ + 1}</span>
              <span className="q-type-chip">MCQ</span>
              <span className="q-topic-chip">{MOCK_QUESTIONS[currentQ].topic}</span>
              <span className="q-marks-chip">1 mark</span>
            </div>
            <div className="q-body" style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text)', marginBottom: '24px' }}>
              {MOCK_QUESTIONS[currentQ].text}
            </div>
            <div className="q-answer-area">
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {MOCK_QUESTIONS[currentQ].options.map((opt, idx) => (
                  <button 
                    key={idx}
                    onClick={() => handleAnswer(idx)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '16px', width: '100%',
                      padding: '16px', background: answers[currentQ] === idx ? 'rgba(124,58,237,0.1)' : 'var(--s2)',
                      border: `1.5px solid ${answers[currentQ] === idx ? 'var(--purple)' : 'var(--border)'}`,
                      borderRadius: '12px', cursor: 'pointer', textAlign: 'left',
                      transition: 'all 0.2s',
                      boxShadow: answers[currentQ] === idx ? '0 0 0 3px rgba(124,58,237,0.2)' : 'none'
                    }}
                  >
                    <span style={{
                      width: '32px', height: '32px', borderRadius: '50%',
                      background: answers[currentQ] === idx ? 'var(--purple)' : 'var(--s1)',
                      color: answers[currentQ] === idx ? '#fff' : 'var(--text)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontWeight: 600, fontSize: '0.9rem',
                      border: answers[currentQ] === idx ? 'none' : '1px solid var(--border)'
                    }}>{String.fromCharCode(65 + idx)}</span>
                    <span style={{ fontSize: '1rem', color: answers[currentQ] === idx ? 'var(--purple-l)' : 'var(--text)', fontWeight: answers[currentQ] === idx ? 600 : 400 }}>{opt}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="exam-nav-row">
            <button className="btn-outline exam-nav-btn" disabled={currentQ === 0} onClick={() => setCurrentQ(prev => prev - 1)}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6"/></svg>
              Previous
            </button>
            <div className="exam-nav-center">
              <button className="btn-skip" onClick={handleSkip}>Skip</button>
              <span className="q-position">{currentQ + 1} of {MOCK_QUESTIONS.length}</span>
            </div>
            <button className="btn-primary exam-nav-btn" disabled={currentQ === MOCK_QUESTIONS.length - 1} onClick={() => setCurrentQ(prev => prev + 1)}>
              Next
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
          </div>
        </div>
      </div>

    </>
  );
};

export default Exam;
