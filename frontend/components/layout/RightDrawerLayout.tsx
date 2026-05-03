import React from "react";

interface RightDrawerLayoutProps {
  children?: React.ReactNode;
}

const RightDrawerLayout: React.FC<RightDrawerLayoutProps> = ({ children }) => {
  return (
    <aside className="w-32 h-[calc(100vh-4rem)] bg-gray-900 text-white shadow-lg z-20 flex flex-col">
      {/* Additional info or widgets */}
      <div className="flex-1 p-4">
        <div className="mb-4 font-semibold">Widget 1</div>
        <div className="mb-4 font-semibold">Widget 2</div>
      </div>
      {children}
    </aside>
  );
};

export default RightDrawerLayout;
