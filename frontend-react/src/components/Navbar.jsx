import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';

const Navbar = ({ role, links }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    // In a real app we'd call the logout function from AuthContext
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <div className="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
        </div>
        <span className="brand-name">
          Mr.E{role && <span className="brand-ai">{role}</span>}
        </span>
      </div>
      <div className="nav-links">
        {links.map((link) => (
          <NavLink 
            key={link.to} 
            to={link.to} 
            className={({ isActive }) => `nav-pill ${isActive ? 'active' : ''}`}
          >
            {link.icon}
            {link.label}
          </NavLink>
        ))}
      </div>
      <div className="nav-actions">
        <button className="btn btn-outline" onClick={handleLogout}>Logout</button>
      </div>
    </nav>
  );
};

export default Navbar;
