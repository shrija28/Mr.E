import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/Navbar';

const StudentLayout = () => {
  const studentLinks = [
    {
      to: '/dashboard',
      label: 'Dashboard',
      icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
    },
    {
      to: '/exam',
      label: 'Exam',
      icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
    },
    {
      to: '/subscription',
      label: 'Subscription',
      icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
    },
    {
      to: '/contact-us',
      label: 'Contact',
      icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
    }
  ];

  return (
    <>
      <div className="bg-mesh"></div>
      <Navbar role="" links={studentLinks} />
      {/* Subscription Banner Placeholder */}
      <div id="subscription-banner-mount" role="region" aria-label="Subscription status"></div>
      <div className="main-content">
        <Outlet />
      </div>
    </>
  );
};

export default StudentLayout;
