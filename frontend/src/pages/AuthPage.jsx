import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const PENDING_EMAIL_KEY = 'jobshield_pending_email';

export default function AuthPage() {
  const [tab, setTab] = useState('login'); // 'login' | 'register'
  const [step, setStep] = useState('credentials'); // 'credentials' | 'verify' | 'forgot' | 'reset'
  const [form, setForm] = useState(() => ({
    name: '',
    email: sessionStorage.getItem(PENDING_EMAIL_KEY) || '',
    password: '',
    newPassword: '',
    otp: '',
  }));
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);

  const auth = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from || '/dashboard';

  useEffect(() => {
    if ((step === 'verify' || step === 'reset') && form.email) {
      sessionStorage.setItem(PENDING_EMAIL_KEY, form.email);
    }
  }, [step, form.email]);

  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setInterval(() => {
      setResendCooldown((c) => (c > 0 ? c - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [resendCooldown]);

  function update(e) {
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  }

  function switchTab(t) {
    setTab(t);
    setStep('credentials');
    setError('');
    setInfo('');
    setForm((f) => ({ ...f, otp: '', password: t === 'login' ? f.password : '' }));
  }

  // Password validation helper
  const isPasswordStrong = (pwd) => {
    if (pwd.length < 8) return false;
    const hasLetter = /[a-zA-Z]/.test(pwd);
    const hasNumOrSpec = /[0-9!@#$%^&*(),.?":{}|<>]/.test(pwd);
    return hasLetter && hasNumOrSpec;
  };

  async function onSubmit(e) {
    e.preventDefault();
    setError('');
    setInfo('');
    setLoading(true);

    try {
      if (step === 'verify') {
        const cleanOtp = form.otp.trim();
        if (cleanOtp.length !== 6 || !/^\d+$/.test(cleanOtp)) {
          throw new Error('Verification code must be exactly 6 digits');
        }
        await auth.verifyEmail(form.email.trim(), cleanOtp);
        sessionStorage.removeItem(PENDING_EMAIL_KEY);
        navigate(from, { replace: true });
        return;
      }

      if (step === 'forgot') {
        if (!form.email.trim()) throw new Error('Email is required');
        const res = await auth.forgotPassword(form.email.trim());
        setStep('reset');
        setResendCooldown(60);
        setInfo(res.message || 'Password reset code sent. Check your inbox.');
        return;
      }

      if (step === 'reset') {
        const cleanOtp = form.otp.trim();
        if (cleanOtp.length !== 6 || !/^\d+$/.test(cleanOtp)) {
          throw new Error('Reset code must be exactly 6 digits');
        }
        if (!isPasswordStrong(form.newPassword)) {
          throw new Error('New password must be at least 8 characters and contain letters and numbers/symbols');
        }
        const res = await auth.resetPassword(form.email.trim(), cleanOtp, form.newPassword);
        setStep('credentials');
        setTab('login');
        setForm((f) => ({ ...f, password: '', otp: '', newPassword: '' }));
        setInfo(res.message || 'Password reset successfully! Please sign in with your new password.');
        return;
      }

      if (tab === 'login') {
        try {
          await auth.login(form.email.trim(), form.password);
          navigate(from, { replace: true });
        } catch (ex) {
          if (ex.code === 'EMAIL_NOT_VERIFIED') {
            setStep('verify');
            sessionStorage.setItem(PENDING_EMAIL_KEY, form.email.trim());
            setInfo('Your email is not verified yet. Enter the 6-digit OTP sent to your inbox, or click Resend code.');
            return;
          }
          throw ex;
        }
      } else {
        // Register flow
        if (form.name.trim().length < 2) {
          throw new Error('Name must be at least 2 characters');
        }
        if (!isPasswordStrong(form.password)) {
          throw new Error('Password must be at least 8 characters and contain letters and numbers/symbols');
        }
        const data = await auth.register(form.name.trim(), form.email.trim(), form.password);
        setStep('verify');
        setResendCooldown(60);
        sessionStorage.setItem(PENDING_EMAIL_KEY, form.email.trim());
        setInfo(data.message || 'Verification code sent. Check your email inbox to verify your account.');
      }
    } catch (ex) {
      setError(ex.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  }

  async function onResend() {
    const email = form.email.trim();
    if (!email) {
      setError('Email address is missing. Go back and enter your email.');
      return;
    }
    if (resendCooldown > 0) return;
    setError('');
    setInfo('');
    setLoading(true);
    try {
      const data =
        step === 'reset'
          ? await auth.forgotPassword(email)
          : await auth.resendOtp(email);
      setResendCooldown(60);
      setInfo(data.message || 'A fresh 6-digit code has been sent.');
    } catch (ex) {
      setError(ex.message || 'Could not resend verification code');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-[75vh] max-w-md items-center px-4 py-10">
      <div className="card-panel w-full animate-fade-up shadow-lg">
        <h1 className="font-display text-3xl font-bold">
          {step === 'verify' && 'Verify Email'}
          {step === 'forgot' && 'Reset Password'}
          {step === 'reset' && 'Set New Password'}
          {step === 'credentials' && (tab === 'login' ? 'Welcome Back' : 'Create Account')}
        </h1>
        <p className="mt-1 text-sm text-ink/60">
          {step === 'verify' && `Enter the 6-digit code sent to ${form.email}`}
          {step === 'forgot' && 'Enter your registered email to receive a password reset code'}
          {step === 'reset' && `Enter the code sent to ${form.email} and your new password`}
          {step === 'credentials' &&
            (tab === 'login'
              ? 'Sign in to access your scam detection dashboard'
              : 'Sign up to protect your career journey from job scams')}
        </p>

        {step === 'credentials' ? (
          <div className="mt-5 flex rounded-md bg-mist p-1">
            {['login', 'register'].map((t) => (
              <button
                key={t}
                type="button"
                className={`flex-1 rounded py-2 text-sm font-semibold capitalize transition ${
                  tab === t ? 'bg-white shadow-sm text-accent' : 'text-ink/60 hover:text-ink'
                }`}
                onClick={() => switchTab(t)}
              >
                {t}
              </button>
            ))}
          </div>
        ) : null}

        <form className="mt-5 space-y-4" onSubmit={onSubmit}>
          {step === 'credentials' && tab === 'register' && (
            <div>
              <label className="label" htmlFor="name">
                Full Name
              </label>
              <input
                id="name"
                name="name"
                className="input"
                required
                placeholder="John Doe"
                value={form.name}
                onChange={update}
              />
            </div>
          )}

          {(step === 'credentials' || step === 'forgot') && (
            <div>
              <label className="label" htmlFor="email">
                Email Address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                className="input"
                required
                placeholder="name@example.com"
                value={form.email}
                onChange={update}
              />
            </div>
          )}

          {step === 'credentials' && (
            <div>
              <div className="flex items-center justify-between">
                <label className="label" htmlFor="password">
                  Password
                </label>
                {tab === 'login' && (
                  <button
                    type="button"
                    className="text-xs text-accent hover:underline mb-1"
                    onClick={() => {
                      setStep('forgot');
                      setError('');
                      setInfo('');
                    }}
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <input
                id="password"
                name="password"
                type="password"
                className="input"
                required
                placeholder="••••••••"
                minLength={8}
                value={form.password}
                onChange={update}
              />
              {tab === 'register' && form.password && (
                <p className={`mt-1 text-xs ${isPasswordStrong(form.password) ? 'text-emerald-600' : 'text-amber-600'}`}>
                  {isPasswordStrong(form.password)
                    ? '✓ Strong password'
                    : '• Min 8 chars, including letters and numbers/symbols'}
                </p>
              )}
            </div>
          )}

          {(step === 'verify' || step === 'reset') && (
            <div>
              <label className="label" htmlFor="otp">
                6-Digit Verification Code
              </label>
              <input
                id="otp"
                name="otp"
                className="input tracking-widest text-center text-lg font-mono"
                required
                inputMode="numeric"
                autoComplete="one-time-code"
                pattern="[0-9]*"
                maxLength={6}
                placeholder="123456"
                value={form.otp}
                onChange={update}
              />
            </div>
          )}

          {step === 'reset' && (
            <div>
              <label className="label" htmlFor="newPassword">
                New Password
              </label>
              <input
                id="newPassword"
                name="newPassword"
                type="password"
                className="input"
                required
                placeholder="••••••••"
                minLength={8}
                value={form.newPassword}
                onChange={update}
              />
              {form.newPassword && (
                <p className={`mt-1 text-xs ${isPasswordStrong(form.newPassword) ? 'text-emerald-600' : 'text-amber-600'}`}>
                  {isPasswordStrong(form.newPassword)
                    ? '✓ Strong password'
                    : '• Min 8 chars, including letters and numbers/symbols'}
                </p>
              )}
            </div>
          )}

          {info ? (
            <div className="rounded-md bg-accent/10 p-3 text-sm text-accent font-medium">
              {info}
            </div>
          ) : null}
          {error ? (
            <div className="rounded-md bg-danger/10 p-3 text-sm text-danger font-medium">
              {error}
            </div>
          ) : null}

          <button type="submit" className="btn-primary w-full py-2.5" disabled={loading}>
            {loading ? (
              'Processing…'
            ) : step === 'verify' ? (
              'Verify & Sign In'
            ) : step === 'forgot' ? (
              'Send Reset Code'
            ) : step === 'reset' ? (
              'Save New Password'
            ) : tab === 'login' ? (
              'Sign In'
            ) : (
              'Create Account'
            )}
          </button>

          {(step === 'verify' || step === 'reset') && (
            <div className="flex gap-2 pt-2">
              <button
                type="button"
                className="btn-secondary flex-1 text-xs"
                disabled={loading || resendCooldown > 0}
                onClick={onResend}
              >
                {resendCooldown > 0 ? `Resend code in ${resendCooldown}s` : 'Resend code'}
              </button>
              <button
                type="button"
                className="btn-secondary flex-1 text-xs"
                disabled={loading}
                onClick={() => {
                  setStep('credentials');
                  setError('');
                  setInfo('');
                  setForm((f) => ({ ...f, otp: '' }));
                }}
              >
                Back to Sign in
              </button>
            </div>
          )}

          {step === 'forgot' && (
            <button
              type="button"
              className="btn-secondary w-full text-xs"
              onClick={() => {
                setStep('credentials');
                setError('');
                setInfo('');
              }}
            >
              Back to Sign in
            </button>
          )}
        </form>

        {step === 'credentials' && (
          <div className="mt-6 border-t border-ink/10 pt-4 text-center text-xs text-ink/50">
            Demo verified accounts: <code>demo@jobshield.local / demo1234</code> or <code>admin@jobshield.local / admin1234</code>
          </div>
        )}
      </div>
    </div>
  );
}
