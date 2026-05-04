import React, { useState, useEffect } from 'react';
import { EnvelopeIcon, LockClosedIcon } from '@heroicons/react/24/outline';
import { useLogin } from '@auth/useLogin';
import { useLoginForm } from '@auth/useLoginForm';
import NotificationBadge from '@shared/NotificationBadge';
import InputWithIcon from '@shared/InputWithIcon';

interface LoginStatus {
  type: 'success' | 'error';
  message: string;
}

const LoginForm: React.FC = () => {
  const [loginStatus, setLoginStatus] = useState<null | LoginStatus>(null);
  const [showBadge, setShowBadge] = useState(false);

  const { values, errors, handleChange, validateForm, resetForm } =
    useLoginForm();

  // Animate badge appearance/disappearance and auto-hide after 10 seconds
  useEffect(() => {
    if (loginStatus) {
      setShowBadge(true);
      const hideTimer = setTimeout(() => setShowBadge(false), 9500); // Start fade-out before removal
      const removeTimer = setTimeout(() => setLoginStatus(null), 10000);
      return () => {
        clearTimeout(hideTimer);
        clearTimeout(removeTimer);
      };
    }
  }, [loginStatus]);

  const isActive = values.email.trim() !== '' && values.password.trim() !== '';

  const { login, loading } = useLogin();

  const handleSubmit = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoginStatus(null);

    if (!validateForm()) {
      // Show first error found
      const firstError = errors.email || errors.password || 'Invalid form';
      setLoginStatus({ type: 'error', message: firstError });
      return;
    }

    const result = await login(values.email, values.password);
    if (result.status === 'success') {
      setLoginStatus({ type: 'success', message: 'Login successful!' });
      resetForm();
    } else {
      setLoginStatus({
        type: 'error',
        message: result.message || 'Login failed',
      });
    }
  };

  return (
    <div className="w-full flex flex-col items-center justify-center gap-6">
      <h2 className="text-2xl font-bold mb-4">Login to OSSN</h2>
      {loginStatus && (
        <NotificationBadge
          type={loginStatus.type}
          message={loginStatus.message}
          show={showBadge}
          style={{
            minWidth: '400px',
            maxWidth: '40vw',
            right: '11rem',
            bottom: '5.5rem',
          }}
        />
      )}
      <form
        className="flex flex-col gap-4 w-full max-w-sm"
        onSubmit={handleSubmit}
      >
        <InputWithIcon
          type="email"
          name="email"
          value={values.email}
          onChange={handleChange}
          icon={<EnvelopeIcon className="h-5 w-5 text-gray-400" />}
          ariaLabel="Email"
          placeholder="Email"
          autoComplete="email"
        />
        <InputWithIcon
          type="password"
          name="password"
          value={values.password}
          onChange={handleChange}
          icon={<LockClosedIcon className="h-5 w-5 text-gray-400" />}
          ariaLabel="Password"
          placeholder="Password"
          autoComplete="current-password"
        />
        <button
          type="submit"
          className={`py-2 rounded ${isActive ? 'bg-blue-600 text-white hover:bg-blue-700 cursor-pointer' : 'bg-gray-300 text-gray-500 cursor-not-allowed'}`}
          disabled={!isActive || loading}
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
};

export default LoginForm;
