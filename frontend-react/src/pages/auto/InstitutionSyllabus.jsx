import React, { useState, useEffect, useMemo } from 'react';

const SUBJECT_CONFIG = {
  Physics: {
    name: 'Physics',
    icon: '⚡',
    color: '#38bdf8',
    bgBadge: 'rgba(56, 189, 248, 0.12)',
    borderBadge: 'rgba(56, 189, 248, 0.3)',
    gradient: 'linear-gradient(135deg, #0284c7, #2563eb)'
  },
  Chemistry: {
    name: 'Chemistry',
    icon: '🧪',
    color: '#34d399',
    bgBadge: 'rgba(52, 211, 153, 0.12)',
    borderBadge: 'rgba(52, 211, 153, 0.3)',
    gradient: 'linear-gradient(135deg, #059669, #0d9488)'
  },
  Mathematics: {
    name: 'Mathematics',
    icon: '📐',
    color: '#c084fc',
    bgBadge: 'rgba(192, 132, 252, 0.12)',
    borderBadge: 'rgba(192, 132, 252, 0.3)',
    gradient: 'linear-gradient(135deg, #7c3aed, #4f46e5)'
  },
  Biology: {
    name: 'Biology',
    icon: '🌱',
    color: '#fbbf24',
    bgBadge: 'rgba(251, 191, 36, 0.12)',
    borderBadge: 'rgba(251, 191, 36, 0.3)',
    gradient: 'linear-gradient(135deg, #d97706, #b45309)'
  }
};

const InstitutionSyllabus = () => {
  const [syllabusSubjects, setSyllabusSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeSubject, setActiveSubject] = useState('Physics');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPuc, setSelectedPuc] = useState('ALL');

  useEffect(() => {
    const fetchSyllabus = async () => {
      setLoading(true);
      setError('');
      try {
        // Try /api/syllabus first, with fallback to /api/admin/syllabus
        let res = await fetch('/api/syllabus', { credentials: 'include' });
        if (!res.ok) {
          res = await fetch('/api/admin/syllabus', { credentials: 'include' });
        }
        const data = await res.json();
        if (data && data.subjects) {
          setSyllabusSubjects(data.subjects);
        } else {
          setError('Unable to parse syllabus data.');
        }
      } catch (err) {
        setError('Failed to connect to the syllabus API.');
      } finally {
        setLoading(false);
      }
    };

    fetchSyllabus();
  }, []);

  // Compute total counts
  const summaryStats = useMemo(() => {
    let total = 0;
    const perSubject = {};
    syllabusSubjects.forEach(s => {
      let p1 = 0;
      let p2 = 0;
      (s.puc_years || []).forEach(p => {
        if (p.puc_year === '1st PUC') p1 += (p.chapters?.length || 0);
        if (p.puc_year === '2nd PUC') p2 += (p.chapters?.length || 0);
      });
      total += (p1 + p2);
      perSubject[s.subject] = { p1, p2, total: p1 + p2 };
    });
    return { total, perSubject };
  }, [syllabusSubjects]);

  // Current active subject data
  const currentSubjectData = useMemo(() => {
    return syllabusSubjects.find(s => s.subject.toLowerCase() === activeSubject.toLowerCase());
  }, [syllabusSubjects, activeSubject]);

  // Filtered chapters for current subject
  const filteredPucYears = useMemo(() => {
    if (!currentSubjectData || !currentSubjectData.puc_years) return [];
    
    return currentSubjectData.puc_years
      .filter(puc => selectedPuc === 'ALL' || puc.puc_year === selectedPuc)
      .map(puc => {
        const matchingChapters = (puc.chapters || []).filter(ch => {
          if (!searchQuery.trim()) return true;
          const q = searchQuery.toLowerCase();
          return (
            (ch.chapter_name && ch.chapter_name.toLowerCase().includes(q)) ||
            (ch.description && ch.description.toLowerCase().includes(q)) ||
            String(ch.chapter_number).includes(q)
          );
        });
        return {
          ...puc,
          chapters: matchingChapters,
          matchCount: matchingChapters.length
        };
      });
  }, [currentSubjectData, selectedPuc, searchQuery]);

  const activeConfig = SUBJECT_CONFIG[activeSubject] || SUBJECT_CONFIG.Physics;

  return (
    <>
      <div className="bg-mesh"></div>

      <main className="main-wrap" style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px 20px 80px' }}>
        {/* Main Section Card */}
        <div className="section-card" style={{ padding: '24px', borderRadius: '16px', background: 'var(--s1)', border: '1px solid var(--border)' }}>
          {/* Header */}
          <div className="section-card-header" style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '20px' }}>
            <div className="section-icon" style={{ width: '42px', height: '42px', borderRadius: '10px', background: 'linear-gradient(135deg, rgba(124,58,237,0.25), rgba(37,99,235,0.25))', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '22px', height: '22px', color: 'var(--purple-l, #a78bfa)' }}>
                <path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/>
              </svg>
            </div>
            <div>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text)', margin: 0 }}>KCET Official Syllabus</h2>
              <p className="section-sub" style={{ fontSize: '0.86rem', color: 'var(--muted)', marginTop: '3px', marginBottom: 0 }}>
                Official Karnataka PUC syllabus — 1st &amp; 2nd PUC chapters for all subjects · Source: KEA / DPUE Karnataka
              </p>
            </div>
          </div>

          {/* Quick Summary Tiles */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '12px',
            marginBottom: '24px'
          }}>
            <div style={{ background: 'var(--s2)', border: '1px solid var(--border)', borderRadius: '12px', padding: '14px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text)' }}>
                {summaryStats.total || 124}
              </div>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--muted)', marginTop: '2px' }}>Total Chapters</div>
            </div>

            {Object.keys(SUBJECT_CONFIG).map(subjKey => {
              const cfg = SUBJECT_CONFIG[subjKey];
              const stat = summaryStats.perSubject[subjKey] || { p1: '?', p2: '?', total: '?' };
              const isSelected = activeSubject === subjKey;

              return (
                <div
                  key={subjKey}
                  onClick={() => setActiveSubject(subjKey)}
                  style={{
                    background: isSelected ? cfg.bgBadge : 'var(--s2)',
                    border: isSelected ? `1.5px solid ${cfg.color}` : '1px solid var(--border)',
                    borderRadius: '12px',
                    padding: '14px',
                    textAlign: 'center',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ fontSize: '1.35rem', fontWeight: 800, color: cfg.color }}>
                    {stat.p1}+{stat.p2}
                  </div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: isSelected ? cfg.color : 'var(--muted)', marginTop: '2px' }}>
                    {cfg.icon} {subjKey}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Subject Navigation Tabs & Controls Bar */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '14px',
            marginBottom: '24px',
            background: 'var(--s2)',
            padding: '12px 16px',
            borderRadius: '12px',
            border: '1px solid var(--border)'
          }}>
            {/* Subject Selector Tabs */}
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {Object.keys(SUBJECT_CONFIG).map(subj => {
                const cfg = SUBJECT_CONFIG[subj];
                const isActive = activeSubject === subj;
                return (
                  <button
                    key={subj}
                    type="button"
                    onClick={() => { setActiveSubject(subj); setSelectedPuc('ALL'); }}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '10px',
                      border: isActive ? 'none' : '1px solid var(--border)',
                      background: isActive ? cfg.gradient : 'var(--s1)',
                      color: isActive ? '#ffffff' : 'var(--muted)',
                      fontWeight: isActive ? 700 : 500,
                      fontSize: '0.88rem',
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      boxShadow: isActive ? '0 4px 12px rgba(0,0,0,0.15)' : 'none',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <span>{cfg.icon}</span>
                    <span>{subj}</span>
                  </button>
                );
              })}
            </div>

            {/* Filter by PUC and Search */}
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', gap: '4px', background: 'var(--s1)', padding: '3px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                {['ALL', '1st PUC', '2nd PUC'].map(puc => (
                  <button
                    key={puc}
                    type="button"
                    onClick={() => setSelectedPuc(puc)}
                    style={{
                      padding: '4px 10px',
                      borderRadius: '6px',
                      border: 'none',
                      background: selectedPuc === puc ? 'var(--purple, #7c3aed)' : 'transparent',
                      color: selectedPuc === puc ? '#fff' : 'var(--muted)',
                      fontSize: '0.78rem',
                      fontWeight: selectedPuc === puc ? 700 : 500,
                      cursor: 'pointer'
                    }}
                  >
                    {puc === 'ALL' ? 'Both PUC' : puc}
                  </button>
                ))}
              </div>

              <input
                type="text"
                placeholder={`Search ${activeSubject} chapters...`}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  padding: '7px 14px',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  background: 'var(--s1)',
                  border: '1px solid var(--border)',
                  color: 'var(--text)',
                  minWidth: '200px'
                }}
              />
            </div>
          </div>

          {/* Body / Chapters Listing */}
          <div id="syllabusContent">
            {loading && (
              <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--muted)' }}>
                <div style={{ fontSize: '2rem', marginBottom: '10px' }}>⏳</div>
                <div style={{ fontWeight: 600 }}>Loading official syllabus...</div>
              </div>
            )}

            {error && !loading && (
              <div style={{ padding: '16px 20px', background: 'rgba(239,68,68,0.1)', border: '1px solid var(--red)', borderRadius: '12px', color: 'var(--red)', textAlign: 'center' }}>
                <p style={{ fontWeight: 600, margin: 0 }}>⚠️ {error}</p>
                <button
                  type="button"
                  className="btn-outline small"
                  style={{ marginTop: '12px' }}
                  onClick={() => window.location.reload()}
                >
                  Retry Loading
                </button>
              </div>
            )}

            {!loading && !error && filteredPucYears.length === 0 && (
              <div style={{ textAlign: 'center', padding: '50px 20px', color: 'var(--muted)' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '8px' }}>🔍</div>
                <div style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text)' }}>No chapters found</div>
                <p style={{ fontSize: '0.86rem', marginTop: '4px' }}>No chapters match your search query "{searchQuery}".</p>
                <button
                  type="button"
                  className="btn-outline small"
                  style={{ marginTop: '10px' }}
                  onClick={() => { setSearchQuery(''); setSelectedPuc('ALL'); }}
                >
                  Clear Filters
                </button>
              </div>
            )}

            {!loading && !error && filteredPucYears.length > 0 && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: filteredPucYears.length === 1 ? '1fr' : 'repeat(auto-fit, minmax(360px, 1fr))',
                gap: '24px',
                alignItems: 'start'
              }}>
                {filteredPucYears.map(puc => {
                  const is1stPuc = puc.puc_year === '1st PUC';
                  const pucBadgeColor = is1stPuc
                    ? { bg: 'rgba(37, 99, 235, 0.15)', text: '#60a5fa', border: 'rgba(37, 99, 235, 0.3)' }
                    : { bg: 'rgba(168, 85, 247, 0.15)', text: '#c084fc', border: 'rgba(168, 85, 247, 0.3)' };

                  return (
                    <div
                      key={puc.puc_year}
                      style={{
                        background: 'var(--s2)',
                        border: '1px solid var(--border)',
                        borderRadius: '14px',
                        padding: '18px 20px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '12px'
                      }}
                    >
                      {/* Section Header */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '10px', borderBottom: '1px solid var(--border)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{
                            padding: '4px 10px',
                            borderRadius: '6px',
                            fontSize: '0.78rem',
                            fontWeight: 700,
                            background: pucBadgeColor.bg,
                            color: pucBadgeColor.text,
                            border: `1px solid ${pucBadgeColor.border}`
                          }}>
                            {puc.puc_year}
                          </span>
                          <span style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text)' }}>
                            {activeSubject} Syllabus
                          </span>
                        </div>
                        <span style={{ fontSize: '0.8rem', color: 'var(--muted)', fontWeight: 600 }}>
                          {puc.chapters.length} Chapters
                        </span>
                      </div>

                      {/* Chapters List */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {puc.chapters.map(ch => (
                          <div
                            key={ch.id || `${puc.puc_year}_${ch.chapter_number}`}
                            style={{
                              background: 'var(--s1)',
                              border: '1px solid var(--border)',
                              borderRadius: '10px',
                              padding: '12px 14px',
                              display: 'flex',
                              alignItems: 'flex-start',
                              gap: '12px',
                              transition: 'all 0.15s ease'
                            }}
                          >
                            {/* Chapter Number Badge */}
                            <div style={{
                              minWidth: '32px',
                              height: '32px',
                              borderRadius: '8px',
                              background: activeConfig.bgBadge,
                              border: `1px solid ${activeConfig.borderBadge}`,
                              color: activeConfig.color,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '0.8rem',
                              fontWeight: 800,
                              flexShrink: 0
                            }}>
                              {ch.chapter_number}
                            </div>

                            {/* Chapter Content */}
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text)', lineHeight: 1.35 }}>
                                {ch.chapter_name}
                              </div>
                              {ch.description && (
                                <div style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: '4px', lineHeight: 1.45 }}>
                                  {ch.description}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </main>
    </>
  );
};

export default InstitutionSyllabus;
