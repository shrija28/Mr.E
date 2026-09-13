import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const InstitutionRegister = () => {
  const [institutionName, setInstitutionName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }

    if (!/\d/.test(password)) {
      setError('Password must contain at least one number (0–9). For example: SMVITM@2026 or Password123');
      return;
    }

    const cleanPhone = phone.replace(/\D/g, '');
    if (cleanPhone.length < 10 || cleanPhone.length > 15) {
      setError('Contact phone must be between 10 and 15 digits.');
      return;
    }

    setLoading(true);

    try {
      const payload = {
        name: institutionName.trim(),
        admin_email: email.trim().toLowerCase(),
        contact_phone: cleanPhone,
        admin_password: password
      };

      const res = await fetch('/api/institution/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok) {
        if (res.status === 409 || data.error === 'duplicate_email') {
          setError('This institution email is already registered. Please sign in instead.');
        } else {
          setError(data.message || 'Registration failed. Please check your inputs.');
        }
        return;
      }

      setSuccess(`Institution "${data.institution_name || institutionName}" registered successfully! You can now log in with your email and password.`);
    } catch (err) {
      setError('Network error. Please make sure the server is reachable.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="bg-mesh"></div>

      <main style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 'calc(100vh - 60px)', padding: '20px' }}>
        <div className="section-card" style={{ maxWidth: '440px', width: '100%', padding: '32px' }}>
          <h2 style={{ marginBottom: '8px' }}>Register Your Institution</h2>
          <p className="input-label" style={{ marginBottom: '24px', textTransform: 'none', fontSize: '0.9rem' }}>
            Create an admin account for your school, college, or coaching center
          </p>

          {error && (
            <div style={{ background: 'rgba(220,38,38,0.1)', border: '1px solid var(--red)', borderRadius: 'var(--rs)', padding: '10px 14px', marginBottom: '16px', fontSize: '0.85rem', color: 'var(--red-l)' }}>
              {error}
            </div>
          )}

          {success && (
            <div style={{ background: 'rgba(5,150,105,0.12)', border: '1px solid var(--green)', borderRadius: 'var(--rs)', padding: '14px 16px', marginBottom: '20px', fontSize: '0.88rem', color: 'var(--green-l)', lineHeight: '1.5' }}>
              <div style={{ fontWeight: '700', marginBottom: '6px' }}>✓ Registration Complete!</div>
              {success}
              <div style={{ marginTop: '14px' }}>
                <button
                  type="button"
                  className="btn-primary"
                  style={{ width: '100%', justifyContent: 'center', padding: '9px' }}
                  onClick={() => navigate('/login')}
                >
                  Go to Sign In →
                </button>
              </div>
            </div>
          )}

          {!success && (
            <form id="registerForm" autoComplete="off" onSubmit={handleSubmit}>
              <div className="input-group" style={{ marginBottom: '16px' }}>
                <label className="input-label" htmlFor="institutionName">Institution Name</label>
                <input
                  className="text-input"
                  type="text"
                  id="institutionName"
                  placeholder="e.g., National Institute of Technology"
                  required
                  minLength="1"
                  maxLength="100"
                  value={institutionName}
                  onChange={(e) => setInstitutionName(e.target.value)}
                />
              </div>

              <div className="input-group" style={{ marginBottom: '16px' }}>
                <label className="input-label" htmlFor="email">Institution Admin Email</label>
                <input
                  className="text-input"
                  type="email"
                  id="email"
                  placeholder="admin@institution.edu"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>

              <div className="input-group" style={{ marginBottom: '16px' }}>
                <label className="input-label" htmlFor="phone">Contact Phone</label>
                <input
                  className="text-input"
                  type="tel"
                  id="phone"
                  placeholder="e.g. 9876543210"
                  required
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
                <small style={{ color: 'var(--muted)', fontSize: '0.75rem', marginTop: '4px', display: 'block' }}>
                  10-15 digits
                </small>
              </div>

              <div className="input-group" style={{ marginBottom: '16px' }}>
                <label className="input-label" htmlFor="password">Password</label>
                <input
                  className="text-input"
                  type="password"
                  id="password"
                  placeholder="Min 8 characters, at least 1 digit"
                  required
                  minLength="8"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <small style={{ color: 'var(--muted)', fontSize: '0.75rem', marginTop: '4px', display: 'block' }}>
                  Must be at least 8 characters and include at least one number (0–9)
                </small>
              </div>

              <div className="input-group" style={{ marginBottom: '24px' }}>
                <label className="input-label" htmlFor="confirmPassword">Confirm Password</label>
                <input
                  className="text-input"
                  type="password"
                  id="confirmPassword"
                  placeholder="Re-enter password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>

              <button
                type="submit"
                className="btn-primary"
                style={{ width: '100%', justifyContent: 'center' }}
                disabled={loading}
              >
                {loading ? 'Registering...' : 'Register Institution'}
              </button>
            </form>
          )}

          <div style={{ marginTop: '20px', textAlign: 'center' }}>
            <p style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
              Already registered? <Link to="/login" style={{ color: 'var(--purple-l)' }}>Sign in</Link>
            </p>
            <p style={{ fontSize: '0.85rem', color: 'var(--muted)', marginTop: '12px' }}>
              Looking to register as a student? <Link to="/register" style={{ color: 'var(--purple-l)' }}>Register here</Link>
            </p>
          </div>
        </div>
      </main>
    </>
  );
};

export default InstitutionRegister;
