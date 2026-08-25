import React, { useState, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../../contexts/AuthContext';

const Login = () => {
  const [role, setRole] = useState('student');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    setError('');

    if (email && password) {
      try {
        const fakeToken = 'mock-jwt-token';
        const userData = { email, role };
        login(userData, fakeToken);
        
        alert('Login successful! Redirecting to dashboard...');
        
        if (role === 'admin') {
          window.location.href = '/admin/dashboard';
        } else if (role === 'institution') {
          window.location.href = '/institution/dashboard';
        } else {
          window.location.href = '/dashboard';
        }
        
      } catch (err) {
        setError('Login failed. Please check your credentials.');
      }
    } else {
      setError('Please fill in all fields.');
    }
  };

  return (
    <>
      <style>{`
        .role-tabs { display: flex; gap: 0; border: 1px solid var(--border); border-radius: var(--rs); overflow: hidden; margin-bottom: 24px; }
        .role-tab { flex: 1; padding: 9px 12px; background: transparent; border: none; color: var(--muted); font-size: 0.82rem; font-weight: 600; cursor: pointer; transition: background 0.15s, color 0.15s; border-right: 1px solid var(--border); }
        .role-tab:last-child { border-right: none; }
        .role-tab.active { background: rgba(124,58,237,0.15); color: var(--purple-l); }
        .role-tab:hover:not(.active) { background: var(--s2); color: var(--text); }
      `}</style>

      <main style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 'calc(100vh - 60px)', padding: '20px' }}>
        <div className="section-card" style={{ maxWidth: '420px', width: '100%', padding: '32px' }}>
          <h2 style={{ marginBottom: '4px' }}>Welcome Back</h2>
          <p className="input-label" style={{ marginBottom: '20px', textTransform: 'none', fontSize: '0.9rem' }}>Sign in to your account</p>

          <div className="role-tabs" role="tablist" aria-label="Login type">
            <button className={`role-tab ${role === 'student' ? 'active' : ''}`} onClick={() => setRole('student')}>Student</button>
            <button className={`role-tab ${role === 'institution' ? 'active' : ''}`} onClick={() => setRole('institution')}>Institution</button>
            <button className={`role-tab ${role === 'admin' ? 'active' : ''}`} onClick={() => setRole('admin')}>Platform Admin</button>
          </div>

          {error && <div id="loginError" style={{ background: 'rgba(220,38,38,0.1)', border: '1px solid var(--red)', borderRadius: 'var(--rs)', padding: '10px 14px', marginBottom: '16px', fontSize: '0.85rem', color: 'var(--red-l)' }}>{error}</div>}

          <form id="loginForm" autoComplete="off" onSubmit={handleLogin}>
            <div className="input-group" style={{ marginBottom: '16px' }}>
              <label className="input-label" htmlFor="email">Email</label>
              <input 
                className="text-input" 
                type="email" 
                id="email" 
                placeholder="you@example.com" 
                required 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="input-group" style={{ marginBottom: '24px' }}>
              <label className="input-label" htmlFor="password">Password</label>
              <input 
                className="text-input" 
                type="password" 
                id="password" 
                placeholder="Your password" 
                required 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <button type="submit" className="btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
              Sign In
            </button>
          </form>

          <p style={{ marginTop: '20px', textAlign: 'center', fontSize: '0.85rem', color: 'var(--muted)' }}>
            Don't have an account? <Link to="/register" style={{ color: 'var(--purple-l)' }}>Register</Link>
          </p>
        </div>
      </main>
    </>
  );
};

export default Login;
