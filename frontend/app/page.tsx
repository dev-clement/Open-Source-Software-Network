import React from 'react';
import DashboardLayout from '@layouts/DashboardLayout';

const Home: React.FC = () => {
  return (
    <DashboardLayout>
      <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
        <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
          {/* Example content inside the dashboard */}
          <h1 className="text-3xl font-bold mb-4">Welcome to OSSN Dashboard!</h1>
          <p className="text-lg text-gray-700">This is your main dashboard area. Replace this with your actual content.</p>
        </main>
      </div>
    </DashboardLayout>
  );
};

export default Home;
