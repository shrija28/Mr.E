import React, { createContext, useState, useEffect } from 'react';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('token');
        if (token === 'http-only-cookie') {
          localStorage.removeItem('token');
        }
        if (token) {
          // Verify token or get user info
          const storedUser = localStorage.getItem('user');
          if (storedUser) {
             setUser(JSON.parse(storedUser));
          }
<<<<<<< HEAD:frontend-react/src/contexts/AuthContext.jsx
=======
        } else if (res.status === 401) {
          setUser(null);
          localStorage.removeItem('user');
          localStorage.removeItem('token');
>>>>>>> ec47da2 (updated few features):frontend/src/contexts/AuthContext.jsx
        }
      } catch (error) {
        console.error('Auth error', error);
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, []);

  const login = (userData, token) => {
    if (token && token !== 'http-only-cookie') {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const logout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    } catch (e) {
      console.warn('Logout endpoint call failed:', e);
    }
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
