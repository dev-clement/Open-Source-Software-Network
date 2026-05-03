'use client';

import {
  UserIcon,
  ArrowRightEndOnRectangleIcon,
} from '@heroicons/react/24/outline';

const AuthLanding = () => {
  const handleLogin = () => {
    alert('Login functionality is not implemented yet.');
  };

  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div className="bg-gray-900 rounded-xl shadow-lg p-10 flex flex-col items-center">
        <h1 className="text-3xl font-bold mb-6 text-white">
          Welcome to OSSN Dashboard!
        </h1>
        <div className="flex gap-6">
          <button
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition"
            onClick={handleLogin}
          >
            <ArrowRightEndOnRectangleIcon className="h-6 w-6" />
            Login
          </button>
          <button className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold transition">
            <UserIcon className="h-6 w-6" />
            Sign Up
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthLanding;
