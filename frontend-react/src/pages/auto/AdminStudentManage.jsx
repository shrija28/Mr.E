import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';

const AdminStudentManage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const action = searchParams.get('action');
  const userId = searchParams.get('userId') || searchParams.get('id');
  const isCreate = action === 'create' || !userId;

  // General state
  const [loading, setLoading] = useState(!isCreate);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [plans, setPlans] = useState([]);

  // Create Form state
  const [createName, setCreateName] = useState('');
  const [createEmail, setCreateEmail] = useState('');
  const [createPassword, setCreatePassword] = useState('');
  const [createConfirmPassword, setCreateConfirmPassword] = useState('');
  const [createKcetId, setCreateKcetId] = useState('');
  const [createPlanId, setCreatePlanId] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Edit / View state
  const [student, setStudent] = useState(null);
  const [editPlanId, setEditPlanId] = useState('');
  const [editDuration, setEditDuration] = useState('1');
  const [editRenewFrom, setEditRenewFrom] = useState('');

  // Password reset state for existing student
  const [showResetSection, setShowResetSection] = useState(false);
  const [resetPassword, setResetPassword] = useState('');
  const [resetConfirmPassword, setResetConfirmPassword] = useState('');
  const [resetSubmitting, setResetSubmitting] = useState(false);

  // Load individual subscription plans
  const loadPlans = useCallback(async () => {
    try {
      const res = await fetch('/api/admin/subscription-plans?plan_type=individual', {
        credentials: 'include',
      });
      if (res.ok) {
        const data = await res.json();
        setPlans(Array.isArray(data) ? data : data.plans || []);
      }
    } catch (err) {
      console.error('Failed to load plans:', err);
    }
  }, []);

  // Load student details for edit mode
  const loadStudent = useCallback(async (id) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/admin/students/${id}`, { credentials: 'include' });
      if (!res.ok) {
        // Fallback to searching from student list if single endpoint differs
        const listRes = await fetch('/api/admin/students?student_type=direct', { credentials: 'include' });
        if (listRes.ok) {
          const listData = await listRes.json();
          const found = (listData.students || []).find((s) => s.id === id);
          if (found) {
            setStudent(found);
            setEditPlanId(found.plan_id || '');
            return;
          }
        }
        throw new Error(`Student not found (ID: ${id})`);
      }
      const data = await res.json();
      setStudent(data);
      setEditPlanId(data.plan_id || '');
    } catch (err) {
      console.error('Failed to load student:', err);
      setError(err.message || 'Could not load student information');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPlans();
    if (!isCreate && userId) {
      loadStudent(userId);
    }
  }, [loadPlans, isCreate, userId, loadStudent]);

  // Handle student creation
  const handleCreateStudent = async (e) => {
    e.preventDefault();
    setError(null);

    const name = createName.trim();
    const email = createEmail.trim().toLowerCase();
    const password = createPassword.trim();
    const confirmPwd = createConfirmPassword.trim();

    if (!name) {
      alert('Please enter student name.');
      return;
    }
    if (!email || !email.includes('@')) {
      alert('Please enter a valid email address.');
      return;
    }
    if (!password || password.length < 6) {
      alert('Password must be at least 6 characters long.');
      return;
    }
    if (password !== confirmPwd) {
      alert('Password and Confirm Password do not match.');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        name,
        email,
        password,
        kcet_student_id: createKcetId.trim() || undefined,
        plan_id: createPlanId || undefined,
      };

      const res = await fetch('/api/admin/students', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || 'Failed to create student');
      }

      alert(`✓ Student "${name}" created successfully!\n\nEmail: ${email}\nStudent ID: ${data.student?.kcet_student_id || 'Assigned'}\nPassword: Set as specified.`);
      navigate('/admin/students');
    } catch (err) {
      console.error('Error creating student:', err);
      alert(`✗ Error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  // Handle password reset for existing student
  const handleResetPassword = async () => {
    if (!student || !student.id) return;
    const pwd = resetPassword.trim();
    const conf = resetConfirmPassword.trim();

    if (!pwd || pwd.length < 6) {
      alert('New password must be at least 6 characters.');
      return;
    }
    if (pwd !== conf) {
      alert('Passwords do not match.');
      return;
    }

    setResetSubmitting(true);
    try {
      const res = await fetch(`/api/admin/students/${student.id}/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ password: pwd }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || 'Failed to reset password');
      }

      alert(`✓ Password updated successfully for ${student.email}! The student can now log in with this new password.`);
      setShowResetSection(false);
      setResetPassword('');
      setResetConfirmPassword('');
    } catch (err) {
      console.error('Reset error:', err);
      alert(`✗ Error: ${err.message}`);
    } finally {
      setResetSubmitting(false);
    }
  };

  // Handle subscription update
  const handleManageSubscription = async (actionType) => {
    if (!student || !student.id) return;

    if (actionType === 'remove') {
      if (!window.confirm(`Remove active subscription for ${student.name}? Account status will be set to INACTIVE.`)) {
        return;
      }
    }

    setSubmitting(true);
    try {
      const payload = {
        action: actionType,
        plan_id: actionType === 'update' ? editPlanId || undefined : undefined,
        duration_months: parseInt(editDuration, 10) || 1,
        renew_from: editRenewFrom || undefined,
      };

      const res = await fetch(`/api/admin/students/${student.id}/subscription/manage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || 'Failed to update subscription');
      }

      alert(`✓ ${data.message || 'Subscription updated successfully!'}`);
      loadStudent(student.id);
    } catch (err) {
      console.error('Subscription error:', err);
      alert(`✗ Error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const fmtDate = (iso) => {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return '—';
    }
  };

  return (
    <>
      <style
        dangerouslySetInnerHTML={{
          __html: `
    .form-section {
      background: var(--card-bg, #1e293b);
      border: 1px solid var(--border, rgba(255,255,255,0.1));
      border-radius: var(--r, 8px);
      padding: 20px;
      margin-bottom: 20px;
    }
    .form-section h3 {
      margin: 0 0 16px;
      font-size: 1rem;
      font-weight: 600;
    }
    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 16px;
    }
    .form-row.full {
      grid-template-columns: 1fr;
    }
    .form-group {
      display: flex;
      flex-direction: column;
    }
    .form-group label {
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text, #f8fafc);
      margin-bottom: 6px;
    }
    .form-group input,
    .form-group select {
      padding: 10px 14px;
      border: 1px solid var(--border, rgba(255,255,255,0.15));
      border-radius: var(--rs, 6px);
      background: var(--s2, #0f172a);
      color: var(--text, #f8fafc);
      font-size: 0.9rem;
    }
    .form-group input:focus,
    .form-group select:focus {
      outline: none;
      border-color: var(--primary, #6366f1);
      background: var(--s3, #1e293b);
    }
    .form-group small {
      font-size: 0.75rem;
      color: var(--muted, #94a3b8);
      margin-top: 4px;
    }
    .info-tile {
      background: var(--card-bg, #1e293b);
      border: 1px solid var(--border, rgba(255,255,255,0.1));
      border-radius: var(--r, 8px);
      padding: 16px;
    }
    .info-tile-label {
      font-size: 0.75rem;
      color: var(--muted, #94a3b8);
      text-transform: uppercase;
      letter-spacing: 0.3px;
      font-weight: 700;
      margin-bottom: 4px;
    }
    .info-tile-value {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text, #f8fafc);
    }
    .status-badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: capitalize;
    }
    .status-badge.active { background: rgba(5,150,105,0.15); color: var(--green-l, #10b981); }
    .status-badge.trial { background: rgba(5,150,105,0.1); color: var(--green-l, #10b981); }
    .status-badge.no_subscription { background: rgba(107,114,128,0.15); color: var(--muted, #94a3b8); }
    .status-badge.cancelled { background: rgba(220,38,38,0.12); color: var(--red-l, #ef4444); }
    .status-badge.expired { background: rgba(220,38,38,0.12); color: var(--red-l, #ef4444); }
    @media (max-width: 768px) {
      .form-row { grid-template-columns: 1fr; }
    }
`,
        }}
      />

      <div className="bg-mesh"></div>

      <div className="main-wrap" style={{ maxWidth: '1000px', margin: '0 auto', padding: '24px 28px 80px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
          <div>
            <h1 style={{ fontSize: '1.6rem', fontWeight: '800', margin: '0 0 4px' }}>
              {isCreate ? 'Add New Student' : 'Manage Student'}
            </h1>
            <p style={{ color: 'var(--muted)', margin: 0, fontSize: '0.85rem' }}>
              {isCreate
                ? 'Create a student account with real, authentic login credentials'
                : `Student account and subscription settings for ${student?.name || 'student'}`}
            </p>
          </div>
          <button
            className="btn-outline"
            onClick={() => navigate('/admin/students')}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}
          >
            ← Back to Students
          </button>
        </div>

        {/* LOADING STATE FOR EDIT MODE */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '80px 20px', color: 'var(--muted)' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '12px' }}>⏳</div>
            <div style={{ fontSize: '1.1rem', fontWeight: '600' }}>Loading student information…</div>
          </div>
        )}

        {/* ERROR STATE FOR EDIT MODE */}
        {!loading && error && (
          <div
            style={{
              background: 'rgba(220, 38, 38, 0.1)',
              border: '1px solid rgba(220, 38, 38, 0.3)',
              borderRadius: '8px',
              padding: '24px',
              textAlign: 'center',
              margin: '20px 0',
            }}
          >
            <div style={{ fontSize: '2rem', marginBottom: '8px' }}>⚠️</div>
            <div style={{ color: 'var(--red-l, #ef4444)', fontWeight: '600', marginBottom: '12px' }}>
              {error}
            </div>
            <button className="btn-outline small" onClick={() => navigate('/admin/students')}>
              Return to Students List
            </button>
          </div>
        )}

        {/* CREATE STUDENT FORM */}
        {isCreate && (
          <form onSubmit={handleCreateStudent} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="form-section">
              <h3>Personal Information</h3>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="createName">Student Full Name *</label>
                  <input
                    type="text"
                    id="createName"
                    value={createName}
                    onChange={(e) => setCreateName(e.target.value)}
                    placeholder="e.g. Rahul Sharma"
                    required
                  />
                  <small>Full name displayed on reports and leaderboards.</small>
                </div>
                <div className="form-group">
                  <label htmlFor="createEmail">Email Address (Login Username) *</label>
                  <input
                    type="email"
                    id="createEmail"
                    value={createEmail}
                    onChange={(e) => setCreateEmail(e.target.value)}
                    placeholder="e.g. rahul@example.com"
                    required
                  />
                  <small>The student will use this email address to log in.</small>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="createKcetId">KCET Student ID</label>
                  <input
                    type="text"
                    id="createKcetId"
                    value={createKcetId}
                    onChange={(e) => setCreateKcetId(e.target.value)}
                    placeholder="Leave blank to auto-generate (e.g. VP0002)"
                  />
                  <small>Optional custom registration code or student roll number.</small>
                </div>
                <div className="form-group">
                  <label htmlFor="createPlanId">Initial Subscription Plan</label>
                  <select
                    id="createPlanId"
                    value={createPlanId}
                    onChange={(e) => setCreatePlanId(e.target.value)}
                  >
                    <option value="">No Subscription (Free Access)</option>
                    {plans.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} - ₹{p.price} ({p.billing_period})
                      </option>
                    ))}
                  </select>
                  <small>Grants immediate full test access upon account creation.</small>
                </div>
              </div>
            </div>

            <div className="form-section">
              <h3>Login Credentials & Security</h3>
              <div
                style={{
                  background: 'rgba(99, 102, 241, 0.08)',
                  border: '1px solid rgba(99, 102, 241, 0.2)',
                  borderRadius: '6px',
                  padding: '12px 16px',
                  marginBottom: '16px',
                }}
              >
                <div style={{ fontWeight: '600', color: 'var(--primary-l, #818cf8)', fontSize: '0.85rem' }}>
                  🔑 Real Student Password
                </div>
                <p style={{ margin: '4px 0 0', fontSize: '0.8rem', color: 'var(--muted)' }}>
                  Set an authentic, permanent password for this student. No dummy or placeholder credentials are stored.
                  This password will be securely hashed with bcrypt in the database so the student can log in right away.
                </p>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="createPassword">Password *</label>
                  <div style={{ position: 'relative' }}>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      id="createPassword"
                      value={createPassword}
                      onChange={(e) => setCreatePassword(e.target.value)}
                      placeholder="Enter a secure password (min 6 chars)"
                      style={{ width: '100%', paddingRight: '40px' }}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      style={{
                        position: 'absolute',
                        right: '10px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        background: 'none',
                        border: 'none',
                        color: 'var(--muted)',
                        cursor: 'pointer',
                        fontSize: '0.85rem',
                      }}
                    >
                      {showPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                  <small>Minimum 6 characters. Avoid simple patterns.</small>
                </div>

                <div className="form-group">
                  <label htmlFor="createConfirmPassword">Confirm Password *</label>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="createConfirmPassword"
                    value={createConfirmPassword}
                    onChange={(e) => setCreateConfirmPassword(e.target.value)}
                    placeholder="Re-enter the password"
                    required
                  />
                  <small>Must match the password entered on the left.</small>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '10px' }}>
              <button
                type="button"
                className="btn-outline"
                onClick={() => navigate('/admin/students')}
                style={{ cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary"
                disabled={submitting}
                style={{ cursor: 'pointer', minWidth: '140px' }}
              >
                {submitting ? 'Creating Student…' : '✓ Create Student'}
              </button>
            </div>
          </form>
        )}

        {/* EDIT / MANAGE EXISTING STUDENT */}
        {!isCreate && !loading && student && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="form-section">
              <h3>Student Information</h3>
              <div className="form-row">
                <div className="form-group">
                  <label>Full Name</label>
                  <input type="text" value={student.name || ''} readOnly style={{ opacity: 0.9 }} />
                </div>
                <div className="form-group">
                  <label>Email Address</label>
                  <input type="email" value={student.email || ''} readOnly style={{ opacity: 0.9 }} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>KCET Student ID</label>
                  <input type="text" value={student.kcet_student_id || '—'} readOnly style={{ opacity: 0.9 }} />
                </div>
                <div className="form-group">
                  <label>User System ID</label>
                  <input
                    type="text"
                    value={student.id || ''}
                    readOnly
                    style={{ background: 'var(--s1, #090d16)', color: 'var(--muted)', fontSize: '0.8rem' }}
                  />
                </div>
              </div>
            </div>

            {/* PASSWORD & SECURITY */}
            <div className="form-section">
              <h3>Password & Security</h3>
              <div
                style={{
                  background: 'rgba(37,99,235,0.08)',
                  border: '1px solid rgba(37,99,235,0.2)',
                  borderRadius: '6px',
                  padding: '14px',
                  marginBottom: '16px',
                }}
              >
                <div style={{ fontWeight: '600', color: 'var(--blue-l, #60a5fa)', marginBottom: '4px' }}>
                  🔐 Reset Student Password
                </div>
                <p style={{ fontSize: '0.82rem', color: 'var(--muted)', margin: 0 }}>
                  Passwords are encrypted with bcrypt and cannot be viewed. If the student forgot their password or needs
                  an update, you can set an authentic, real password for them below.
                </p>
              </div>

              {!showResetSection ? (
                <button
                  type="button"
                  className="btn-outline small"
                  onClick={() => setShowResetSection(true)}
                  style={{ color: 'var(--primary, #6366f1)', borderColor: 'var(--primary, #6366f1)', cursor: 'pointer' }}
                >
                  Set New Password for Student
                </button>
              ) : (
                <div
                  style={{
                    border: '1px solid rgba(220,38,38,0.3)',
                    borderRadius: '8px',
                    padding: '16px',
                    background: 'rgba(220,38,38,0.04)',
                  }}
                >
                  <div style={{ fontWeight: '600', color: 'var(--red-l, #ef4444)', marginBottom: '12px' }}>
                    Set Authentic Password
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="resetPwd">New Password *</label>
                      <input
                        type="password"
                        id="resetPwd"
                        value={resetPassword}
                        onChange={(e) => setResetPassword(e.target.value)}
                        placeholder="Enter new password (min 6 chars)"
                      />
                    </div>
                    <div className="form-group">
                      <label htmlFor="resetConfPwd">Confirm New Password *</label>
                      <input
                        type="password"
                        id="resetConfPwd"
                        value={resetConfirmPassword}
                        onChange={(e) => setResetConfirmPassword(e.target.value)}
                        placeholder="Confirm new password"
                      />
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '12px' }}>
                    <button
                      type="button"
                      className="btn-outline small"
                      onClick={() => {
                        setShowResetSection(false);
                        setResetPassword('');
                        setResetConfirmPassword('');
                      }}
                      style={{ cursor: 'pointer' }}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="btn-primary small"
                      disabled={resetSubmitting}
                      onClick={handleResetPassword}
                      style={{
                        background: 'var(--red, #dc2626)',
                        borderColor: 'var(--red, #dc2626)',
                        cursor: 'pointer',
                      }}
                    >
                      {resetSubmitting ? 'Updating Password…' : 'Confirm Password Update'}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* SUBSCRIPTION STATUS TILES */}
            <div className="form-section">
              <h3>Subscription Status</h3>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '12px',
                  marginBottom: '16px',
                }}
              >
                <div className="info-tile">
                  <div className="info-tile-label">Current Status</div>
                  <div className="info-tile-value">
                    <span className={`status-badge ${student.subscription_status || 'no_subscription'}`}>
                      {(student.subscription_status || 'No Subscription').replace('_', ' ')}
                    </span>
                  </div>
                </div>
                <div className="info-tile">
                  <div className="info-tile-label">Active Plan</div>
                  <div className="info-tile-value">{student.plan_name || 'Free Plan'}</div>
                </div>
                <div className="info-tile">
                  <div className="info-tile-label">Next Renewal Date</div>
                  <div className="info-tile-value">{fmtDate(student.next_renewal_date)}</div>
                </div>
              </div>
            </div>

            {/* MANAGE SUBSCRIPTION */}
            <div className="form-section">
              <h3>Manage Subscription</h3>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="editPlanSelect">Select Plan</label>
                  <select
                    id="editPlanSelect"
                    value={editPlanId}
                    onChange={(e) => setEditPlanId(e.target.value)}
                  >
                    <option value="">Select a subscription plan…</option>
                    {plans.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} - ₹{p.price} ({p.billing_period})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="editDuration">Duration</label>
                  <select
                    id="editDuration"
                    value={editDuration}
                    onChange={(e) => setEditDuration(e.target.value)}
                  >
                    <option value="1">1 Month</option>
                    <option value="3">3 Months</option>
                    <option value="6">6 Months</option>
                    <option value="12">1 Year</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="editRenewFrom">Renewal From</label>
                  <input
                    type="date"
                    id="editRenewFrom"
                    value={editRenewFrom}
                    onChange={(e) => setEditRenewFrom(e.target.value)}
                  />
                  <small>Leave empty to renew starting from today.</small>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'space-between', marginTop: '16px', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className="btn-outline small"
                  onClick={() => handleManageSubscription('remove')}
                  disabled={submitting}
                  style={{ color: 'var(--red-l, #ef4444)', borderColor: 'var(--red-l, #ef4444)', cursor: 'pointer' }}
                >
                  🚫 Cancel / Remove Subscription
                </button>
                <button
                  type="button"
                  className="btn-primary small"
                  disabled={submitting || !editPlanId}
                  onClick={() => handleManageSubscription('update')}
                  style={{ cursor: 'pointer' }}
                >
                  {submitting ? 'Updating…' : 'Save Plan Changes'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default AdminStudentManage;
