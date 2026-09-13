import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const InstitutionStudents = () => {
  const [batches, setBatches] = useState([]);
  const [students, setStudents] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Modals
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [newBatchName, setNewBatchName] = useState('');
  const [newBatchDesc, setNewBatchDesc] = useState('');
  const [creatingBatch, setCreatingBatch] = useState(false);

  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteBatchId, setInviteBatchId] = useState('');
  const [generatingInvite, setGeneratingInvite] = useState(false);
  const [generatedInvite, setGeneratedInvite] = useState(null);
  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);

  // Filter
  const [selectedBatchFilter, setSelectedBatchFilter] = useState('all');

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      // 1. Fetch Batches
      const batchRes = await fetch('/api/institution/batches', { credentials: 'include' });
      if (batchRes.ok) {
        const bData = await batchRes.json();
        setBatches(bData.batches || []);
      }

      // 2. Fetch Students
      const stuRes = await fetch('/api/institution/students', { credentials: 'include' });
      if (stuRes.ok) {
        const sData = await stuRes.json();
        setStudents(sData.students || []);
      }

      // 3. Fetch Invitations
      const invRes = await fetch('/api/institution/invitations', { credentials: 'include' });
      if (invRes.ok) {
        const iData = await invRes.json();
        setInvitations(iData.invitations || []);
      }
    } catch (err) {
      setError('Unable to load institution data. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateBatch = async (e) => {
    e.preventDefault();
    if (!newBatchName.trim()) return;
    setCreatingBatch(true);
    setError('');
    try {
      const res = await fetch('/api/institution/batches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ name: newBatchName.trim(), description: newBatchDesc.trim() }),
      });
      const data = await res.json();
      if (res.ok) {
        setSuccessMsg(`Batch "${data.name}" created successfully!`);
        setShowBatchModal(false);
        setNewBatchName('');
        setNewBatchDesc('');
        fetchData();
      } else {
        setError(data.message || 'Failed to create batch');
      }
    } catch {
      setError('Network error creating batch');
    } finally {
      setCreatingBatch(false);
    }
  };

  const handleDeleteBatch = async (batchId, batchName) => {
    if (!window.confirm(`Are you sure you want to delete "${batchName}"? Students in this batch will be unassigned.`)) return;
    try {
      const res = await fetch(`/api/institution/batches/${batchId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (res.ok) {
        setSuccessMsg(`Batch "${batchName}" deleted.`);
        fetchData();
      } else {
        const data = await res.json();
        setError(data.message || 'Failed to delete batch');
      }
    } catch {
      setError('Network error deleting batch');
    }
  };

  const handleAssignBatch = async (studentId, batchId) => {
    try {
      const res = await fetch(`/api/institution/students/${studentId}/batch`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ batch_id: batchId || null }),
      });
      if (res.ok) {
        const data = await res.json();
        setSuccessMsg(`Student batch updated to "${data.batch_name || 'Unassigned'}"`);
        setStudents((prev) =>
          prev.map((s) =>
            s.user_id === studentId ? { ...s, batch_id: data.batch_id, batch_name: data.batch_name } : s
          )
        );
      }
    } catch {
      setError('Failed to update student batch');
    }
  };

  const handleRemoveStudent = async (studentId, studentName) => {
    if (!window.confirm(`Remove ${studentName} from your institution?`)) return;
    try {
      const res = await fetch(`/api/institution/students/${studentId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (res.ok) {
        setSuccessMsg(`Student removed from institution.`);
        fetchData();
      }
    } catch {
      setError('Failed to remove student');
    }
  };

  const handleGenerateInvite = async () => {
    setGeneratingInvite(true);
    setError('');
    try {
      const res = await fetch('/api/institution/invitations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ batch_id: inviteBatchId || null }),
      });
      const data = await res.json();
      if (res.ok) {
        setGeneratedInvite(data);
        fetchData();
      } else {
        setError(data.message || 'Failed to generate invitation');
      }
    } catch {
      setError('Network error generating invitation');
    } finally {
      setGeneratingInvite(false);
    }
  };

  const copyToClipboard = (text, type) => {
    navigator.clipboard.writeText(text);
    if (type === 'link') {
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    } else {
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  };

  const filteredStudents = selectedBatchFilter === 'all'
    ? students
    : selectedBatchFilter === 'unassigned'
      ? students.filter(s => !s.batch_id)
      : students.filter(s => s.batch_id === selectedBatchFilter);

  return (
    <>
      <div className="bg-mesh"></div>

      <main className="institution-page" id="studentsPage">
        <header className="institution-page-header">
          <div>
            <h1 className="institution-page-title">
              Manage <span className="institution-page-title-accent">Batches & Students</span>
            </h1>
            <p className="institution-page-sub">
              Organize classes into batches, assign weekly tests, and onboard students
            </p>
          </div>
          <div className="institution-page-actions" style={{ display: 'flex', gap: '12px' }}>
            <button
              type="button"
              className="btn-institution-outline"
              onClick={() => setShowBatchModal(true)}
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '16px', height: '16px' }}><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              + Create Batch
            </button>
            <button
              type="button"
              className="btn-institution"
              onClick={() => {
                setGeneratedInvite(null);
                setShowInviteModal(true);
              }}
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '16px', height: '16px' }}><path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>
              Invite Student
            </button>
          </div>
        </header>

        {error && (
          <div role="alert" style={{ background: 'rgba(220,38,38,0.1)', border: '1px solid var(--red)', borderRadius: '8px', padding: '12px 16px', marginBottom: '20px', color: 'var(--red-l)' }}>
            {error}
          </div>
        )}

        {successMsg && (
          <div role="status" style={{ background: 'rgba(5,150,105,0.1)', border: '1px solid var(--green)', borderRadius: '8px', padding: '12px 16px', marginBottom: '20px', color: 'var(--green-l)' }}>
            {successMsg}
          </div>
        )}

        {/* 1. Batches Overview */}
        <section className="section-card" style={{ marginBottom: '24px' }}>
          <div className="section-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div className="section-icon" style={{ background: 'linear-gradient(135deg, rgba(124,58,237,0.2), rgba(59,130,246,0.2))' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
              </div>
              <div>
                <h2>Institution Batches / Sections</h2>
                <p className="section-sub">Classes and cohorts for targeted testing and rank tracking</p>
              </div>
            </div>
            <span style={{ fontSize: '0.85rem', color: 'var(--muted)', background: 'rgba(255,255,255,0.05)', padding: '6px 12px', borderRadius: '20px' }}>
              {batches.length} Active {batches.length === 1 ? 'Batch' : 'Batches'}
            </span>
          </div>

          <div className="section-body">
            {batches.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px 10px', color: 'var(--muted)' }}>
                <p>No batches created yet. Create sections like "PUC-II Section A" to assign tests to specific classes.</p>
                <button
                  type="button"
                  className="btn-institution-outline"
                  style={{ marginTop: '12px' }}
                  onClick={() => setShowBatchModal(true)}
                >
                  + Create First Batch
                </button>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '16px' }}>
                {batches.map((b) => (
                  <div
                    key={b.id}
                    style={{
                      border: selectedBatchFilter === b.id ? '1px solid var(--purple-l)' : '1px solid var(--border)',
                      borderRadius: '8px',
                      padding: '16px',
                      background: selectedBatchFilter === b.id ? 'rgba(167, 139, 250, 0.08)' : 'rgba(255,255,255,0.02)',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <h3 style={{ fontSize: '1.05rem', margin: 0, color: 'var(--text)' }}>{b.name}</h3>
                      <button
                        type="button"
                        onClick={() => handleDeleteBatch(b.id, b.name)}
                        title="Delete Batch"
                        style={{ background: 'none', border: 'none', color: 'var(--muted)', cursor: 'pointer', padding: '2px 4px' }}
                      >
                        ✕
                      </button>
                    </div>
                    {b.description && (
                      <p style={{ fontSize: '0.82rem', color: 'var(--muted)', margin: '6px 0 12px' }}>{b.description}</p>
                    )}
                    <div style={{ display: 'flex', gap: '16px', fontSize: '0.82rem', marginTop: '12px', borderTop: '1px solid var(--border)', paddingTop: '10px' }}>
                      <span>👥 <strong style={{ color: 'var(--text)' }}>{b.student_count}</strong> Students</span>
                      <span>📝 <strong style={{ color: 'var(--text)' }}>{b.exam_count}</strong> Tests</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* 2. Linked Students Table */}
        <section className="section-card">
          <div className="section-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div className="section-icon" style={{ background: 'rgba(16, 185, 129, 0.2)' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
              </div>
              <div>
                <h2>Enrolled Students ({students.length})</h2>
                <p className="section-sub">View students and assign them to specific batches</p>
              </div>
            </div>

            {/* Filter by Batch */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>Filter by Batch:</span>
              <select
                className="text-input"
                style={{ padding: '6px 12px', fontSize: '0.85rem' }}
                value={selectedBatchFilter}
                onChange={(e) => setSelectedBatchFilter(e.target.value)}
              >
                <option value="all">All Batches ({students.length})</option>
                <option value="unassigned">Unassigned ({students.filter(s => !s.batch_id).length})</option>
                {batches.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} ({b.student_count})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="section-body" style={{ padding: 0 }}>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--muted)' }}>Loading students...</div>
            ) : filteredStudents.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--muted)' }}>
                No students found in this filter. Click "Invite Student" to add members.
              </div>
            ) : (
              <div className="responsive-table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Student Name</th>
                      <th>Email</th>
                      <th>Assigned Batch</th>
                      <th>Linked Date</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredStudents.map((s) => (
                      <tr key={s.user_id}>
                        <td>
                          <div style={{ fontWeight: 600, color: 'var(--text)' }}>{s.display_name}</div>
                          {s.kcet_student_id && (
                            <span style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>ID: {s.kcet_student_id}</span>
                          )}
                        </td>
                        <td style={{ color: 'var(--muted)', fontSize: '0.88rem' }}>{s.email}</td>
                        <td>
                          <select
                            className="text-input"
                            style={{ padding: '4px 8px', fontSize: '0.82rem', width: 'auto', minWidth: '160px' }}
                            value={s.batch_id || ''}
                            onChange={(e) => handleAssignBatch(s.user_id, e.target.value)}
                          >
                            <option value="">— Unassigned —</option>
                            {batches.map((b) => (
                              <option key={b.id} value={b.id}>{b.name}</option>
                            ))}
                          </select>
                        </td>
                        <td style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>
                          {s.linked_at ? new Date(s.linked_at).toLocaleDateString() : '—'}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <button
                            type="button"
                            onClick={() => handleRemoveStudent(s.user_id, s.display_name)}
                            style={{ background: 'none', border: 'none', color: 'var(--red-l)', cursor: 'pointer', fontSize: '0.82rem' }}
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>

        {/* 3. Pending Invitations Table */}
        <section className="section-card" style={{ marginTop: '24px' }}>
          <div className="section-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h2>Pending Invitations ({invitations.filter(i => i.status === 'pending').length})</h2>
              <p className="section-sub">Unclaimed invitation codes waiting for students to register</p>
            </div>
          </div>
          <div className="section-body" style={{ padding: 0 }}>
            {invitations.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px', color: 'var(--muted)' }}>
                No active invitations. Click "Invite Student" to generate a code or link.
              </div>
            ) : (
              <div className="responsive-table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Invite Code</th>
                      <th>Target Batch</th>
                      <th>Status</th>
                      <th>Expires At</th>
                      <th style={{ textAlign: 'right' }}>Copy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invitations.slice(0, 10).map((inv, idx) => {
                      const matchedBatch = batches.find(b => b.id === inv.batch_id);
                      return (
                        <tr key={idx}>
                          <td>
                            <span style={{ fontFamily: 'monospace', background: 'rgba(167, 139, 250, 0.1)', color: 'var(--purple-l)', padding: '3px 6px', borderRadius: '4px' }}>
                              {inv.code.slice(0, 16)}...
                            </span>
                          </td>
                          <td style={{ fontSize: '0.85rem' }}>
                            {matchedBatch ? <span style={{ color: 'var(--blue)' }}>{matchedBatch.name}</span> : <span style={{ color: 'var(--muted)' }}>General (Any Batch)</span>}
                          </td>
                          <td>
                            <span style={{
                              fontSize: '0.78rem',
                              padding: '2px 8px',
                              borderRadius: '12px',
                              background: inv.status === 'pending' ? 'rgba(234, 179, 8, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                              color: inv.status === 'pending' ? '#eab308' : '#10b981',
                            }}>
                              {inv.status}
                            </span>
                          </td>
                          <td style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>
                            {inv.expires_at ? new Date(inv.expires_at).toLocaleDateString() : '7 days'}
                          </td>
                          <td style={{ textAlign: 'right' }}>
                            <button
                              type="button"
                              className="btn-institution-outline"
                              style={{ padding: '4px 8px', fontSize: '0.78rem' }}
                              onClick={() => {
                                const url = `${window.location.origin}/invitation/accept?code=${inv.code}`;
                                copyToClipboard(url, 'link');
                              }}
                            >
                              Copy Link
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>
      </main>

      {/* Modal: Create Batch */}
      {showBatchModal && (
        <div className="modal-overlay" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="modal-dialog" style={{ width: '420px', maxWidth: '90vw', background: '#13141f', border: '1px solid var(--border)', borderRadius: '12px', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.2rem', margin: 0, color: 'var(--text)' }}>Create New Batch</h2>
              <button
                type="button"
                onClick={() => setShowBatchModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--muted)', fontSize: '1.4rem', cursor: 'pointer' }}
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleCreateBatch}>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', color: 'var(--muted)' }}>
                  Batch / Section Name *
                </label>
                <input
                  type="text"
                  className="text-input"
                  style={{ width: '100%' }}
                  placeholder="e.g. PUC-II Section A"
                  value={newBatchName}
                  onChange={(e) => setNewBatchName(e.target.value)}
                  required
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', color: 'var(--muted)' }}>
                  Description (Optional)
                </label>
                <input
                  type="text"
                  className="text-input"
                  style={{ width: '100%' }}
                  placeholder="e.g. Science Morning Cohort"
                  value={newBatchDesc}
                  onChange={(e) => setNewBatchDesc(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button
                  type="button"
                  className="btn-institution-outline"
                  onClick={() => setShowBatchModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-institution"
                  disabled={creatingBatch}
                >
                  {creatingBatch ? 'Creating...' : 'Create Batch'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Invite Student */}
      {showInviteModal && (
        <div className="modal-overlay" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="modal-dialog" style={{ width: '480px', maxWidth: '90vw', background: '#13141f', border: '1px solid var(--border)', borderRadius: '12px', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '1.2rem', margin: 0, color: 'var(--text)' }}>Invite Student to Institution</h2>
              <button
                type="button"
                onClick={() => setShowInviteModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--muted)', fontSize: '1.4rem', cursor: 'pointer' }}
              >
                &times;
              </button>
            </div>

            {!generatedInvite ? (
              <div>
                <p style={{ fontSize: '0.88rem', color: 'var(--muted)', marginBottom: '16px' }}>
                  Generate a single-use onboarding link for a student. You can pre-assign them to a specific batch.
                </p>

                <div style={{ marginBottom: '20px' }}>
                  <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', color: 'var(--muted)' }}>
                    Assign to Batch
                  </label>
                  <select
                    className="text-input"
                    style={{ width: '100%' }}
                    value={inviteBatchId}
                    onChange={(e) => setInviteBatchId(e.target.value)}
                  >
                    <option value="">— Unassigned (Student chooses or faculty assigns later) —</option>
                    {batches.map((b) => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                  </select>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                  <button
                    type="button"
                    className="btn-institution-outline"
                    onClick={() => setShowInviteModal(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="btn-institution"
                    onClick={handleGenerateInvite}
                    disabled={generatingInvite}
                  >
                    {generatingInvite ? 'Generating...' : 'Generate Invite Link'}
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--green)', borderRadius: '8px', padding: '12px', marginBottom: '16px', color: 'var(--green-l)', fontSize: '0.85rem' }}>
                  ✓ Invitation created! Valid for 7 days.
                </div>

                <div style={{ marginBottom: '16px' }}>
                  <label style={{ display: 'block', marginBottom: '4px', fontSize: '0.82rem', color: 'var(--muted)' }}>
                    Direct Student Invitation Link:
                  </label>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                      type="text"
                      className="text-input"
                      readOnly
                      style={{ flex: 1, fontSize: '0.82rem' }}
                      value={`${window.location.origin}/invitation/accept?code=${generatedInvite.code}`}
                    />
                    <button
                      type="button"
                      className="btn-institution"
                      style={{ padding: '6px 12px', fontSize: '0.82rem', whiteSpace: 'nowrap' }}
                      onClick={() => copyToClipboard(`${window.location.origin}/invitation/accept?code=${generatedInvite.code}`, 'link')}
                    >
                      {copiedLink ? 'Copied!' : 'Copy Link'}
                    </button>
                  </div>
                </div>

                <div style={{ marginBottom: '20px' }}>
                  <label style={{ display: 'block', marginBottom: '4px', fontSize: '0.82rem', color: 'var(--muted)' }}>
                    Invitation Code:
                  </label>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <input
                      type="text"
                      className="text-input"
                      readOnly
                      style={{ flex: 1, fontSize: '0.85rem', fontFamily: 'monospace' }}
                      value={generatedInvite.code}
                    />
                    <button
                      type="button"
                      className="btn-institution-outline"
                      style={{ padding: '6px 12px', fontSize: '0.82rem', whiteSpace: 'nowrap' }}
                      onClick={() => copyToClipboard(generatedInvite.code, 'code')}
                    >
                      {copiedCode ? 'Copied!' : 'Copy Code'}
                    </button>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    type="button"
                    className="btn-institution"
                    onClick={() => setShowInviteModal(false)}
                  >
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default InstitutionStudents;
