import React from 'react';
import { Link } from 'react-router-dom';

const ContactUs = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `
    .contact-container {
      max-width: 900px;
      margin: 0 auto;
      padding: 40px 20px;
    }

    .contact-header {
      text-align: center;
      margin-bottom: 40px;
    }

    .contact-header h1 {
      font-size: 2rem;
      font-weight: 800;
      margin-bottom: 10px;
      background: linear-gradient(90deg, var(--purple-l, #a78bfa), var(--blue-l, #60a5fa));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .contact-header p {
      font-size: 1rem;
      color: var(--muted);
      max-width: 500px;
      margin: 0 auto;
    }

    .contact-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 30px;
      margin-bottom: 40px;
    }

    @media (max-width: 768px) {
      .contact-grid {
        grid-template-columns: 1fr;
      }
    }

    .contact-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--r);
      padding: 30px;
    }

    .contact-card h2 {
      font-size: 1.2rem;
      font-weight: 700;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .contact-card-icon {
      width: 30px;
      height: 30px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.2rem;
      background: rgba(167, 139, 250, 0.1);
    }

    .contact-item {
      margin-bottom: 20px;
    }

    .contact-item:last-child {
      margin-bottom: 0;
    }

    .contact-label {
      font-size: 0.85rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.3px;
      font-weight: 700;
      margin-bottom: 6px;
      display: block;
    }

    .contact-value {
      font-size: 1rem;
      color: var(--text);
      font-weight: 600;
    }

    .contact-link {
      color: var(--purple-l, #a78bfa);
      text-decoration: none;
      transition: opacity 0.2s;
    }

    .contact-link:hover {
      opacity: 0.8;
      text-decoration: underline;
    }

    .contact-copy-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      margin-top: 8px;
      padding: 6px 12px;
      background: rgba(167, 139, 250, 0.1);
      border: 1px solid rgba(167, 139, 250, 0.2);
      border-radius: 4px;
      color: var(--purple-l, #a78bfa);
      cursor: pointer;
      font-size: 0.8rem;
      font-weight: 600;
      transition: all 0.2s;
    }

    .contact-copy-btn:hover {
      background: rgba(167, 139, 250, 0.2);
      border-color: rgba(167, 139, 250, 0.4);
    }

    .contact-form {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--r);
      padding: 30px;
      margin-bottom: 40px;
    }

    .contact-form h2 {
      font-size: 1.2rem;
      font-weight: 700;
      margin-bottom: 20px;
    }

    .form-group {
      margin-bottom: 20px;
    }

    .form-group label {
      display: block;
      font-size: 0.9rem;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 8px;
    }

    .form-group input,
    .form-group textarea,
    .form-group select {
      width: 100%;
      padding: 10px 14px;
      border: 1px solid var(--border);
      border-radius: var(--rs);
      background: var(--s2);
      color: var(--text);
      font-size: 0.9rem;
      font-family: inherit;
      transition: all 0.2s;
    }

    .form-group input:focus,
    .form-group textarea:focus,
    .form-group select:focus {
      outline: none;
      border-color: var(--purple-l, #a78bfa);
      background: var(--s3);
    }

    .form-group textarea {
      resize: vertical;
      min-height: 120px;
    }

    .form-actions {
      display: flex;
      gap: 10px;
      justify-content: flex-end;
    }

    .faq-section {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--r);
      padding: 30px;
    }

    .faq-section h2 {
      font-size: 1.2rem;
      font-weight: 700;
      margin-bottom: 20px;
    }

    .faq-item {
      margin-bottom: 16px;
    }

    .faq-item:last-child {
      margin-bottom: 0;
    }

    .faq-question {
      background: rgba(167, 139, 250, 0.05);
      border: 1px solid rgba(167, 139, 250, 0.1);
      border-radius: var(--rs);
      padding: 14px;
      cursor: pointer;
      font-weight: 600;
      color: var(--text);
      display: flex;
      align-items: center;
      justify-content: space-between;
      transition: all 0.2s;
    }

    .faq-question:hover {
      background: rgba(167, 139, 250, 0.1);
      border-color: rgba(167, 139, 250, 0.2);
    }

    .faq-toggle {
      font-size: 1.2rem;
      color: var(--muted);
      transition: transform 0.2s;
    }

    .faq-item.open .faq-toggle {
      transform: rotate(180deg);
    }

    .faq-answer {
      max-height: 0;
      overflow: hidden;
      transition: max-height 0.3s;
    }

    .faq-item.open .faq-answer {
      max-height: 500px;
    }

    .faq-answer-text {
      padding: 12px 14px;
      color: var(--muted);
      font-size: 0.9rem;
      line-height: 1.6;
    }

    .response-message {
      padding: 16px;
      border-radius: var(--rs);
      margin-bottom: 20px;
      display: none;
      font-size: 0.9rem;
    }

    .response-message.success {
      background: rgba(5, 150, 105, 0.1);
      border: 1px solid rgba(5, 150, 105, 0.2);
      color: var(--green-l);
      display: block;
    }

    .response-message.error {
      background: rgba(220, 38, 38, 0.1);
      border: 1px solid rgba(220, 38, 38, 0.2);
      color: var(--red-l);
      display: block;
    }

    .breadcrumb {
      margin-bottom: 20px;
    }

    .breadcrumb a {
      color: var(--purple-l, #a78bfa);
      text-decoration: none;
      font-size: 0.85rem;
    }

    .breadcrumb a:hover {
      text-decoration: underline;
    }

    .breadcrumb span {
      color: var(--muted);
      margin: 0 6px;
    }
  
` }} />
      
  <div className="bg-mesh"></div>

  
  

  <div className="contact-container">

    
    <div className="breadcrumb">
      <Link to="/dashboard">Dashboard</Link>
      <span>→</span>
      <span>Contact Us</span>
    </div>

    
    <div className="contact-header">
      <h1>Get in Touch</h1>
      <p>Have a question or need assistance? We're here to help. Reach out to us through any of the channels below.</p>
    </div>

    
    <div className="contact-grid">
      
      <div className="contact-card">
        <h2>
          <div className="contact-card-icon">📧</div>
          Email Support
        </h2>
        <div className="contact-item">
          <span className="contact-label">Support Email</span>
          <div className="contact-value">
            <a href="mailto:support@vyasaprep.com" className="contact-link">support@vyasaprep.com</a>
          </div>
          <button className="contact-copy-btn" >
            📋 Copy
          </button>
        </div>
        <div className="contact-item">
          <span className="contact-label">General Inquiries</span>
          <div className="contact-value">
            <a href="mailto:info@vyasaprep.com" className="contact-link">info@vyasaprep.com</a>
          </div>
          <button className="contact-copy-btn" >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{"width":"12px","height":"12px"}}><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>
            Copy
          </button>
        </div>
      </div>

      
      <div className="contact-card">
        <h2>
          <div className="contact-card-icon">📞</div>
          Support Hours
        </h2>
        <div className="contact-item">
          <span className="contact-label">Response Time</span>
          <div className="contact-value">Within 24 hours</div>
        </div>
        <div className="contact-item">
          <span className="contact-label">Available Days</span>
          <div className="contact-value">Monday - Friday, 9 AM - 6 PM IST</div>
        </div>
        <div className="contact-item">
          <span className="contact-label">Expected Resolution</span>
          <div className="contact-value">2-3 business days</div>
        </div>
      </div>
    </div>

    
    <div className="contact-form">
      <h2>Send us a Message</h2>
      <div id="responseMessage" className="response-message"></div>
      
      <form id="contactForm" onsubmit="submitContactForm(event)">
        <div className="form-group">
          <label htmlFor="contactName">Full Name *</label>
          <input type="text" id="contactName" name="name" required placeholder="Your name"/>
        </div>

        <div className="form-group">
          <label htmlFor="contactEmail">Email Address *</label>
          <input type="email" id="contactEmail" name="email" required placeholder="your@email.com"/>
        </div>

        <div className="form-group">
          <label htmlFor="contactSubject">Subject *</label>
          <select id="contactSubject" name="subject" required>
            <option value="">Select a subject...</option>
            <option value="subscription">Subscription Issue</option>
            <option value="payment">Payment Issue</option>
            <option value="technical">Technical Issue</option>
            <option value="exam">Exam Problem</option>
            <option value="account">Account Help</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="contactMessage">Message *</label>
          <textarea id="contactMessage" name="message" required placeholder="Describe your issue or question..."></textarea>
        </div>

        <div className="form-actions">
          <button type="button" className="btn-outline" >Clear</button>
          <button type="submit" className="btn-primary">Send Message</button>
        </div>
      </form>
    </div>

    
    <div className="faq-section">
      <h2>Frequently Asked Questions</h2>
      
      <div className="faq-item" >
        <div className="faq-question">
          <span>How do I reset my password?</span>
          <span className="faq-toggle">▼</span>
        </div>
        <div className="faq-answer">
          <div className="faq-answer-text">
            To reset your password, click on the "Forgot Password" link on the login page. Enter your email address and follow the instructions sent to your inbox. You'll receive a password reset link valid for 24 hours.
          </div>
        </div>
      </div>

      <div className="faq-item" >
        <div className="faq-question">
          <span>Can I cancel my subscription?</span>
          <span className="faq-toggle">▼</span>
        </div>
        <div className="faq-answer">
          <div className="faq-answer-text">
            Yes, you can cancel your subscription anytime from the Subscription page. Your access will continue until the end of your current billing period. No refunds are provided for partial months.
          </div>
        </div>
      </div>

      <div className="faq-item" >
        <div className="faq-question">
          <span>What payment methods do you accept?</span>
          <span className="faq-toggle">▼</span>
        </div>
        <div className="faq-answer">
          <div className="faq-answer-text">
            We accept all major credit/debit cards (Visa, Mastercard, American Express), UPI, net banking, and digital wallets through Razorpay. All payments are secure and encrypted.
          </div>
        </div>
      </div>

      <div className="faq-item" >
        <div className="faq-question">
          <span>How many exams can I take with a subscription?</span>
          <span className="faq-toggle">▼</span>
        </div>
        <div className="faq-answer">
          <div className="faq-answer-text">
            The number of exams depends on your subscription plan. Check your plan details on the Subscription page to see your exam limits. Most plans include unlimited practice exams.
          </div>
        </div>
      </div>

      <div className="faq-item" >
        <div className="faq-question">
          <span>How do I report a technical issue?</span>
          <span className="faq-toggle">▼</span>
        </div>
        <div className="faq-answer">
          <div className="faq-answer-text">
            Please use the contact form above and select "Technical Issue" as the subject. Include as much detail as possible, such as your browser, device type, and steps to reproduce the issue. Our team will investigate and get back to you within 24 hours.
          </div>
        </div>
      </div>
    </div>

  </div>

  
  

    </>
  );
};

export default ContactUs;
