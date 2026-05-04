import React, { useState } from 'react';
import AuthLanding from '@authlanding/AuthLanding';
import LoginForm from '@login/LoginForm';
import { useAuth } from '@authcontext/AuthContext';

const App: React.FC = () => {
  const [showLoginForm, setShowLoginForm] = useState(false);

  // Check if the user is logged in
  const { isLoggedIn } = useAuth();

  if (isLoggedIn) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <h1 className="text-3xl font-bold mb-6 text-white">
          Welcome back to OSSN Dashboard!
        </h1>
      </div>
    );
  }

  return (
    <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
      {/* Conditionally render AuthLanding or LoginForm */}
      {showLoginForm ? (
        <LoginForm />
      ) : (
        <AuthLanding onLoginClick={() => setShowLoginForm(true)} />
      )}
    </main>
  );
};

export default App;
