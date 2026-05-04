import React, { useState } from 'react';
import { EnvelopeIcon, LockClosedIcon } from '@heroicons/react/24/outline';

const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const isActive = email.trim() !== '' && password.trim() !== '';

  return (
    <div className="w-full flex flex-col items-center justify-center gap-6">
      <h2 className="text-2xl font-bold mb-4">Login to OSSN</h2>
      <form className="flex flex-col gap-4 w-full max-w-sm">
        <div className="relative">
          <span className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <EnvelopeIcon className="h-5 w-5 text-gray-400" />
          </span>
          <input
            type="email"
            className="pl-10 p-2 border rounded w-full"
            aria-label="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="relative">
          <span className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <LockClosedIcon className="h-5 w-5 text-gray-400" />
          </span>
          <input
            type="password"
            className="pl-10 p-2 border rounded w-full"
            aria-label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <button
          type="submit"
          className={`py-2 rounded ${isActive ? 'bg-blue-600 text-white hover:bg-blue-700 cursor-pointer' : 'bg-gray-300 text-gray-500 cursor-not-allowed'}`}
          disabled={!isActive}
        >
          Login
        </button>
      </form>
    </div>
  );
};

export default LoginForm;
