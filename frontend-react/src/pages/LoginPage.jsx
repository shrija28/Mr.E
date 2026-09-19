import React, { useState, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import Navbar from '../components/Navbar'; // We can use a public layout or just Navbar

const LoginPage = () => {
  const [role, setRole] = useState('student');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
<<<<<<< HEAD:frontend-react/src/pages/LoginPage.jsx
=======
  const [info, setInfo] = useState(() => {
    if (location.state?.subscriptionSuccess) {
      return `Subscription active for ${location.state.planName || 'Plan'}! Sign in to enter your dashboard.`;
    }
    if (location.state?.fromSubscription) {
      return 'Subscription complete! Sign in to enter your dashboard.';
    }
    if (location.state?.registered) {
      return 'Account created! Please sign in to continue.';
    }
    return '';
  });
>>>>>>> ec47da2 (updated few features):frontend/src/pages/LoginPage.jsx
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!email || !password) {
      setError('Please fill in all fields.');
      return;
    }

    try {
      let endpoint = '/api/auth/login';
      if (role === 'admin') endpoint = '/api/auth/admin/login';
      else if (role === 'institution') endpoint = '/api/auth/institution/login';

      const res = await fetch(endpoint, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();

      if (!res.ok) {
        // Handle generic auth failure or lockout
        if (data.error === 'account_locked') {
          setError(data.message || 'Account temporarily locked. Try again later.');
        } else {
          setError('Invalid credentials. Please try again.');
        }
        return;
      }

      // Successful login
      login(data);
      
      // Redirect based on role or explicit redirect from backend
      if (data.redirect) navigate(data.redirect);
      else if (role === 'admin') navigate('/admin/dashboard');
      else if (role === 'institution') navigate('/institution/dashboard');
      else navigate('/dashboard');
      
    } catch (err) {
      setError('Network error. Ensure the backend is running.');
    }
  };

  const publicLinks = [
    { to: '/login', label: 'Login' },
    { to: '/register', label: 'Register' }
  ];

  return (
    <>
      <div className="bg-mesh"></div>
      
      {/* We can use a simpler Navbar or reuse the main one without role */}
      

      <main style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 'calc(100vh - 60px)', padding: '20px' }}>
        <div className="section-card login-card" style={{ width: '100%' }}>
          <h2 style={{ marginBottom: '4px' }}>Welcome Back</h2>
          <p className="input-label" style={{ marginBottom: '20px', textTransform: 'none', fontSize: '0.9rem' }}>Sign in to your account</p>

          <div style={{ display: 'flex', gap: '0', border: '1px solid var(--border)', borderRadius: 'var(--rs)', overflow: 'hidden', marginBottom: '24px' }}>
            <button 
              className={`role-tab ${role === 'student' ? 'active' : ''}`}
              style={{ flex: 1, padding: '9px 12px', background: role === 'student' ? 'rgba(124,58,237,0.15)' : 'transparent', border: 'none', color: role === 'student' ? 'var(--purple-l)' : 'var(--muted)', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer', borderRight: '1px solid var(--border)' }}
              onClick={() => setRole('student')}
            >
              Student
            </button>
            <button 
              className={`role-tab ${role === 'institution' ? 'active' : ''}`}
              style={{ flex: 1, padding: '9px 12px', background: role === 'institution' ? 'rgba(124,58,237,0.15)' : 'transparent', border: 'none', color: role === 'institution' ? 'var(--purple-l)' : 'var(--muted)', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer', borderRight: '1px solid var(--border)' }}
              onClick={() => setRole('institution')}
            >
              Institution
            </button>
            <button 
              className={`role-tab ${role === 'admin' ? 'active' : ''}`}
              style={{ flex: 1, padding: '9px 12px', background: role === 'admin' ? 'rgba(124,58,237,0.15)' : 'transparent', border: 'none', color: role === 'admin' ? 'var(--purple-l)' : 'var(--muted)', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer' }}
              onClick={() => setRole('admin')}
            >
              Platform Admin
            </button>
          </div>

          {error && <div style={{ background: 'rgba(220,38,38,0.1)', border: '1px solid var(--red)', borderRadius: 'var(--rs)', padding: '10px 14px', marginBottom: '16px', fontSize: '0.85rem', color: 'var(--red-l)' }}>{error}</div>}

          <form className="login-form" onSubmit={handleLogin}>
            <div className="input-group">
              <label className="input-label" htmlFor="email">Email</label>
              <input 
                type="email" 
                id="email" 
                className="input-field" 
                placeholder="you@example.com" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required 
              />
            </div>
            
            <div className="input-group">
              <label className="input-label" htmlFor="password">Password</label>
              <input 
                type="password" 
                id="password" 
                className="input-field" 
                placeholder="••••••••" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required 
              />
            </div>

            <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '8px' }}>
              Sign In
            </button>
          </form>

          <p style={{ textAlign: 'center', marginTop: '24px', fontSize: '0.85rem', color: 'var(--muted)' }}>
            {role === 'institution' ? (
              <>
                Onboarding your school or college?{' '}
                <Link to="/institution/register" style={{ color: 'var(--purple-l)', textDecoration: 'none', fontWeight: 600 }}>
                  Register Institution →
                </Link>
              </>
            ) : (
              <>
                Don't have an account?{' '}
                <Link to="/register" style={{ color: 'var(--purple-l)', textDecoration: 'none' }}>
                  Register
                </Link>
              </>
            )}
          </p>
        </div>
      </main>
    </>
  );
};

export default LoginPage;
