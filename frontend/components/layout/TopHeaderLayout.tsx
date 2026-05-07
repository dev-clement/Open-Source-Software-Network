import React from "react";
import { Squares2X2Icon, UserCircleIcon } from "@heroicons/react/24/solid";

interface TopHeaderLayoutProps {
  children?: React.ReactNode;
}

const TopHeaderLayout: React.FC<TopHeaderLayoutProps> = ({ children }) => {
  return (
    <header className="w-full h-16 bg-gray-900 text-white flex items-center px-6 shadow-md fixed top-0 left-0 z-30">
      <div className="flex-1 flex items-center gap-3">
        <Squares2X2Icon className="h-7 w-7 text-white" />
        <span className="font-bold text-lg">OSSN Dashboard</span>
      </div>
      <button
        className="ml-4 p-1 rounded-full hover:bg-gray-800 transition-colors duration-200 cursor-pointer"
        aria-label="User Profile"
      >
        <UserCircleIcon className="h-8 w-8 text-white" />
      </button>
      {children}
    </header>
  );
};

export default TopHeaderLayout;
