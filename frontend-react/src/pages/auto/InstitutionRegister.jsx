import React from 'react';
import { Link } from 'react-router-dom';

const InstitutionRegister = () => {
  return (
    <>
      {/* Auto-injected styles from HTML head */}
      <style dangerouslySetInnerHTML={{ __html: `` }} />
      
  <div className="bg-mesh"></div>

  
  

  
  <main style={{"display":"flex","alignItems":"center","justifyContent":"center","minHeight":"calc(100vh - 60px)","padding":"20px"}}>
    <div className="section-card" style={{"maxWidth":"420px","width":"100%","padding":"32px"}}>
      <h2 style={{"marginBottom":"8px"}}>Register Your Institution</h2>
      <p className="input-label" style={{"marginBottom":"24px","textTransform":"none","fontSize":"0.9rem"}}>Create an admin account for your institution</p>

      <div id="registerError" style={{"display":"none","background":"rgba(220,38,38,0.1)","border":"1px solid var(--red)","borderRadius":"var(--rs)","padding":"10px 14px","marginBottom":"16px","fontSize":"0.85rem","color":"var(--red-l)"}}></div>
      <div id="registerSuccess" style={{"display":"none","background":"rgba(5,150,105,0.1)","border":"1px solid var(--green)","borderRadius":"var(--rs)","padding":"10px 14px","marginBottom":"16px","fontSize":"0.85rem","color":"var(--green-l)"}}></div>

      <form id="registerForm" autocomplete="off">
        
        <input type="text" name="fake_email_autofill" style={{"display":"none"}} tabindex="-1" aria-hidden="true"/>
        <input type="password" name="fake_pwd_autofill" style={{"display":"none"}} tabindex="-1" aria-hidden="true"/>

        <div className="input-group" style={{"marginBottom":"16px"}}>
          <label className="input-label" htmlFor="institutionName">Institution Name</label>
          <input className="text-input" type="text" id="institutionName" name="institutionName" placeholder="e.g., ABC College of Engineering" required minlength="1" maxlength="100" autocomplete="off"/>
        </div>
        <div className="input-group" style={{"marginBottom":"16px"}}>
          <label className="input-label" htmlFor="email">Institution Email</label>
          <input className="text-input" type="email" id="email" name="inst_reg_email" placeholder="admin@institution.edu" required autocomplete="off" readonly onfocus="this.removeAttribute('readonly');"/>
        </div>
        <div className="input-group" style={{"marginBottom":"16px"}}>
          <label className="input-label" htmlFor="phone">Contact Phone</label>
          <input className="text-input" type="tel" id="phone" name="phone" placeholder="+91 9876543210" required pattern="[0-9]{10,15}" autocomplete="off"/>
          <small style={{"color":"var(--muted)","fontSize":"0.75rem","marginTop":"4px","display":"block"}}>10-15 digits including country code</small>
        </div>
        <div className="input-group" style={{"marginBottom":"16px"}}>
          <label className="input-label" htmlFor="password">Password</label>
          <input className="text-input" type="password" id="password" name="inst_reg_pwd" placeholder="Min 8 chars, at least 1 digit" required minlength="8" autocomplete="off" readonly onfocus="this.removeAttribute('readonly');"/>
        </div>
        <div className="input-group" style={{"marginBottom":"24px"}}>
          <label className="input-label" htmlFor="confirmPassword">Confirm Password</label>
          <input className="text-input" type="password" id="confirmPassword" name="inst_reg_confirm_pwd" placeholder="Re-enter password" required autocomplete="off" readonly onfocus="this.removeAttribute('readonly');"/>
        </div>

        <button type="submit" className="btn-primary" style={{"width":"100%","justifyContent":"center"}} id="registerBtn">
          Register Institution
        </button>
      </form>

      <div style={{"marginTop":"20px","textAlign":"center"}}>
        <p style={{"fontSize":"0.85rem","color":"var(--muted)"}}>
          Already have an account? <Link to="/login" style={{"color":"var(--purple-l)"}}>Sign in</Link>
        </p>
        <p style={{"fontSize":"0.85rem","color":"var(--muted)","marginTop":"12px"}}>
          Looking to register as a student? <Link to="/register" style={{"color":"var(--purple-l)"}}>Register here</Link>
        </p>
      </div>
    </div>
  </main>

  
  

    </>
  );
};

export default InstitutionRegister;
