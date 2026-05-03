import React from "react";

interface LeftDrawerLayoutProps {
  children?: React.ReactNode;
}

const LeftDrawerLayout: React.FC<LeftDrawerLayoutProps> = ({ children }) => {
  return (
    <aside className="w-36 h-[calc(100vh-4rem)] bg-gray-900 text-white shadow-lg z-20 flex flex-col">
      {/* Navigation or menu items */}
      <nav className="flex-1 m-0 p-0">
        <ul className="w-full m-0 p-0">
          <li className="py-4 font-semibold transition-colors duration-500 hover:bg-gray-800 hover:rounded hover:text-gray-50 cursor-pointer w-full block rounded-none text-center">
            Menu Item 1
          </li>
          <li className="py-4 font-semibold transition-colors duration-500 hover:bg-gray-800 hover:rounded hover:text-gray-50 cursor-pointer w-full block rounded-none text-center">
            Menu Item 2
          </li>
          <li className="py-4 font-semibold transition-colors duration-500 hover:bg-gray-800 hover:rounded hover:text-gray-50 cursor-pointer w-full block rounded-none text-center">
            Menu Item 3
          </li>
        </ul>
      </nav>
      {children}
    </aside>
  );
};

export default LeftDrawerLayout;
