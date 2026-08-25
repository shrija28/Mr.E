import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';

const RegisterPage = () => {
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [joinType, setJoinType] = useState('independent');
  const [joinCode, setJoinCode] = useState('');
  
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    
    try {
      const payload = {
        display_name: displayName,
        email: email,
        password: password,
        role: "student",
        student_subtype: joinType === 'via_code' ? "institutional" : "independent",
        institution_id: joinType === 'via_code' ? joinCode : null
      };

      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();

      if (!res.ok) {
        if (data.field === "email") {
          setError('Email already exists. Please log in instead.');
        } else {
          setError(data.message || 'Registration failed. Please try again.');
        }
        return;
      }

      setSuccess('You have registered successfully. Please sign in to continue.');
    } catch (err) {
      setError('Network error. Ensure the backend is running.');
    }
  };

  return (
    <>
      <div className="bg-mesh"></div>
      

      <main style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 'calc(100vh - 60px)', padding: '20px' }}>
        <div className="section-card" style={{ maxWidth: '420px', width: '100%', padding: '32px' }}>
          <h2 style={{ marginBottom: '8px' }}>Create Account</h2>
          <p className="input-label" style={{ marginBottom: '24px', textTransform: 'none', fontSize: '0.9rem' }}>Register for Mr.E</p>

          {error && <div style={{ background: 'rgba(220,38,38,0.1)', border: '1px solid var(--red)', borderRadius: 'var(--rs)', padding: '10px 14px', marginBottom: '16px', fontSize: '0.85rem', color: 'var(--red-l)' }}>{error}</div>}
          {success && <div style={{ background: 'rgba(5,150,105,0.1)', border: '1px solid var(--green)', borderRadius: 'var(--rs)', padding: '10px 14px', marginBottom: '16px', fontSize: '0.85rem', color: 'var(--green-l)' }}>{success}</div>}

          <form onSubmit={handleRegister} autoComplete="off">
            <div className="input-group" style={{ marginBottom: '16px' }}>
              <label className="input-label" htmlFor="displayName">Display Name</label>
              <input 
                className="input-field" 
                type="text" 
                id="displayName" 
                placeholder="Your name" 
                required 
                minLength="1" 
                maxLength="50" 
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
            </div>
            
            <div className="input-group" style={{ marginBottom: '16px' }}>
              <label className="input-label" htmlFor="email">Email</label>
              <input 
                className="input-field" 
                type="email" 
                id="email" 
                placeholder="you@example.com" 
                required 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="input-group" style={{ marginBottom: '16px' }}>
              <label className="input-label" htmlFor="password">Password</label>
              <input 
                className="input-field" 
                type="password" 
                id="password" 
                placeholder="Min 8 chars, at least 1 digit" 
                required 
                minLength="8" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <div className="input-group" style={{ marginBottom: '24px' }}>
              <label className="input-label" htmlFor="confirmPassword">Confirm Password</label>
              <input 
                className="input-field" 
                type="password" 
                id="confirmPassword" 
                placeholder="Re-enter password" 
                required 
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label className="input-label" style={{ marginBottom: '8px', display: 'block' }}>How are you joining?</label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <label style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 14px', border: joinType === 'independent' ? '1px solid var(--primary)' : '1px solid var(--border)', borderRadius: 'var(--rs)', cursor: 'pointer', fontSize: '0.85rem', transition: 'border-color 0.15s' }}>
                  <input 
                    type="radio" 
                    name="joinType" 
                    value="independent" 
                    checked={joinType === 'independent'} 
                    onChange={() => setJoinType('independent')}
                    style={{ margin: 0 }}
                  /> 
                  <span>🎓 Personal Student</span>
                </label>
                <label style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 14px', border: joinType === 'via_code' ? '1px solid var(--primary)' : '1px solid var(--border)', borderRadius: 'var(--rs)', cursor: 'pointer', fontSize: '0.85rem', transition: 'border-color 0.15s' }}>
                  <input 
                    type="radio" 
                    name="joinType" 
                    value="via_code"
                    checked={joinType === 'via_code'} 
                    onChange={() => setJoinType('via_code')}
                    style={{ margin: 0 }}
                  /> 
                  <span>🏫 Through Institution</span>
                </label>
              </div>
            </div>            {joinType === 'via_code' && (
              <div className="input-group" style={{ marginBottom: '24px' }}>
                <label className="input-label" htmlFor="joinCode">Institution Code</label>
                <input 
                  className="input-field" 
                  type="text" 
                  id="joinCode" 
                  placeholder="Enter code (e.g., INST-1234)" 
                  required 
                  value={joinCode}
                  onChange={(e) => setJoinCode(e.target.value)}
                />
              </div>
            )}

            <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '8px' }} disabled={!!success}>
              Create Account
            </button>
          </form>

          <p style={{ textAlign: 'center', marginTop: '24px', fontSize: '0.85rem', color: 'var(--muted)' }}>
            Already have an account? <Link to="/login" style={{ color: 'var(--purple-l)', textDecoration: 'none' }}>Log in</Link>
          </p>
        </div>
      </main>
    </>
  );
};

export default RegisterPage;
