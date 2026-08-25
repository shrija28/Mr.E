import React from 'react';

const Register = () => {
  return (
    <>
      
      <div dangerouslySetInnerHTML={{ __html: `
  

  <!-- Navbar -->
  

  <!-- Register Form -->
  <main style="display:flex;align-items:center;justify-content:center;min-height:calc(100vh - 60px);padding:20px;">
    <div class="section-card" style="max-width:420px;width:100%;padding:32px;">
      <h2 style="margin-bottom:8px;">Create Account</h2>
      <p class="input-label" style="margin-bottom:24px;text-transform:none;font-size:0.9rem;">Register for Mr.E</p>

      <div id="registerError" style="display:none;background:rgba(220,38,38,0.1);border:1px solid var(--red);border-radius:var(--rs);padding:10px 14px;margin-bottom:16px;font-size:0.85rem;color:var(--red-l);"></div>
      <div id="registerSuccess" style="display:none;background:rgba(5,150,105,0.1);border:1px solid var(--green);border-radius:var(--rs);padding:10px 14px;margin-bottom:16px;font-size:0.85rem;color:var(--green-l);"></div>

      <form id="registerForm" autocomplete="off">
        <!-- Hidden anti-autofill dummy trap -->
        <input type="text" name="fake_email_autofill" style="display:none" tabindex="-1" aria-hidden="true"/>
        <input type="password" name="fake_pwd_autofill" style="display:none" tabindex="-1" aria-hidden="true"/>

        <div class="input-group" style="margin-bottom:16px;">
          <label class="input-label" for="displayName">Display Name</label>
          <input class="text-input" type="text" id="displayName" name="displayName" placeholder="Your name" required minlength="1" maxlength="50" autocomplete="off"/>
        </div>
        <div class="input-group" style="margin-bottom:16px;">
          <label class="input-label" for="email">Email</label>
          <input class="text-input" type="email" id="email" name="user_reg_email" placeholder="you@example.com" required autocomplete="off" readonly onfocus="this.removeAttribute('readonly');"/>
        </div>
        <div class="input-group" style="margin-bottom:16px;">
          <label class="input-label" for="password">Password</label>
          <input class="text-input" type="password" id="password" name="user_reg_pwd" placeholder="Min 8 chars, at least 1 digit" required minlength="8" autocomplete="off" readonly onfocus="this.removeAttribute('readonly');"/>
        </div>
        <div class="input-group" style="margin-bottom:24px;">
          <label class="input-label" for="confirmPassword">Confirm Password</label>
          <input class="text-input" type="password" id="confirmPassword" name="user_reg_confirm_pwd" placeholder="Re-enter password" required autocomplete="off" readonly onfocus="this.removeAttribute('readonly');"/>
        </div>

        <!-- Join type selection -->
        <div style="margin-bottom:16px;">
          <label class="input-label" style="margin-bottom:8px;display:block;">How are you joining?</label>
          <div style="display:flex;gap:8px;">
            <label style="flex:1;display:flex;align-items:center;gap:8px;padding:10px 14px;border:1px solid var(--border);border-radius:var(--rs);cursor:pointer;font-size:0.85rem;transition:border-color 0.15s;" id="joinPersonalLabel">
              <input type="radio" name="joinType" value="personal" checked style="margin:0;" onchange="toggleInviteField()"/>
              <span>🎓 Personal Student</span>
            </label>
            <label style="flex:1;display:flex;align-items:center;gap:8px;padding:10px 14px;border:1px solid var(--border);border-radius:var(--rs);cursor:pointer;font-size:0.85rem;transition:border-color 0.15s;" id="joinInstitutionLabel">
              <input type="radio" name="joinType" value="institution" style="margin:0;" onchange="toggleInviteField()"/>
              <span>🏫 Through Institution</span>
            </label>
          </div>
        </div>

        <!-- Invite code field (shown only when "Through Institution" selected) -->
        <div class="input-group" id="inviteCodeGroup" style="margin-bottom:24px;display:none;">
          <label class="input-label" for="inviteCode">Institution Invite Code</label>
          <input class="text-input" type="text" id="inviteCode" name="inviteCode" placeholder="Paste the invite code from your institution" style="font-family:monospace;"/>
          <small style="color:var(--muted);font-size:0.75rem;margin-top:4px;display:block;">Get this code from your college/coaching center admin</small>
        </div>

        <button type="submit" class="btn-primary" style="width:100%;justify-content:center;" id="registerBtn">
          Create Account
        </button>
      </form>

      <div style="margin-top:20px;text-align:center;">
        <p style="font-size:0.85rem;color:var(--muted);">
          Already have an account? <a href="/login" style="color:var(--purple-l);">Sign in</a>
        </p>
      </div>
    </div>
  </main>

  
  
` }} />
    </>
  );
};

export default Register;
