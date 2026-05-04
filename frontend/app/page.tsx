'use client';
import React, { useState } from 'react';
import AuthLanding from '@/components/auth/AuthLanding';
import DashboardLayout from '@layouts/DashboardLayout';
import LoginForm from '@/components/auth/LoginForm';

const Home: React.FC = () => {
  const [showLoginForm, setShowLoginForm] = useState(false);

  return (
    <DashboardLayout>
      <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
        <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
          {/* Conditionally render AuthLanding or LoginForm */}
          {showLoginForm ? (
            <LoginForm />
          ) : (
            <AuthLanding onLoginClick={() => setShowLoginForm(true)} />
          )}
        </main>
      </div>
    </DashboardLayout>
  );
};

export default Home;
