import React from "react";
import TopHeaderLayout from "@layouts/TopHeaderLayout";
import LeftDrawerLayout from "@layouts/LeftDrawerLayout";
import RightDrawerLayout from "@layouts/RightDrawerLayout";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  return (
    <div className="flex flex-col min-h-screen bg-gray-900">
      <TopHeaderLayout />
      <div className="flex-1 pt-16 grid grid-cols-[8rem_1fr_8rem] min-h-0">
        <LeftDrawerLayout />
        <div className="flex flex-col col-start-2 w-full">
          <main className="flex-1 flex flex-col justify-center w-full">
            {children}
          </main>
          <footer className="h-12 bg-gray-900 text-white flex items-center justify-between w-full px-4 text-sm">
            <span>OSSN © {new Date().getFullYear()}</span>
            <span className="opacity-80">Open Source Social Network – A platform for collaborative project management and contributions.</span>
          </footer>
        </div>
        <RightDrawerLayout />
      </div>
    </div>
  );
};

export default DashboardLayout;
