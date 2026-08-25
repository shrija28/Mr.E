import React from 'react';
import { Link } from 'react-router-dom';

const ContactUsPage = () => {
  return (
    <>
      <div className="bg-mesh"></div>
      
      {/* Navbar (Public view, since anyone can contact) */}
      

      <main className="contact-container" style={{ maxWidth: '900px', margin: '0 auto', padding: '40px 20px' }}>
        <div className="contact-header" style={{ textAlign: 'center', marginBottom: '40px' }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '10px' }}>Contact Us</h1>
          <p style={{ fontSize: '1rem', color: 'var(--muted)', maxWidth: '500px', margin: '0 auto' }}>
            We'd love to hear from you. Please fill out this form or reach out via email.
          </p>
        </div>

        <div className="section-card" style={{ padding: '32px' }}>
          <form onSubmit={(e) => e.preventDefault()}>
            <div className="input-group" style={{ marginBottom: '16px' }}>
              <label className="input-label" htmlFor="name">Name</label>
              <input type="text" id="name" className="input-field" placeholder="Your name" required />
            </div>

            <div className="input-group" style={{ marginBottom: '16px' }}>
              <label className="input-label" htmlFor="email">Email</label>
              <input type="email" id="email" className="input-field" placeholder="Your email address" required />
            </div>

            <div className="input-group" style={{ marginBottom: '24px' }}>
              <label className="input-label" htmlFor="message">Message</label>
              <textarea id="message" className="input-field" rows="5" placeholder="How can we help you?" required></textarea>
            </div>

            <button type="submit" className="btn-primary" style={{ width: '100%' }}>Send Message</button>
          </form>
        </div>
      </main>
    </>
  );
};

export default ContactUsPage;
