"use client";

import React, { useEffect, useState } from "react";
import DashboardLayout from "@layouts/DashboardLayout";
import { getUsers } from "./../../services/userServices";

type User = {
  id: number;
  username: string;
  email: string;
  role?: string;
  status?: string;
};

const UsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getUsers()
    .then((data) => {
        setUsers(data);
        setLoading(false);
    })
    .catch(() => {
        setError("Error loading users");
        setLoading(false);
    });
  }, []);

  const handleDelete = (id: number) => {
  setUsers((prevUsers) => prevUsers.filter((user) => user.id !== id));
};

  return (
    <DashboardLayout>
      <div className="flex flex-col flex-1 items-center justify-start bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 px-3 py-6 sm:px-4 sm:py-8 md:px-6 md:py-10 lg:px-8 w-full min-h-screen pb-20">
        <main className="w-full max-w-6xl">
          <div className="text-center mb-6 sm:mb-8 md:mb-10 lg:mb-12">
            <h1 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3 sm:mb-4">User List</h1>
            <div className="w-10 sm:w-12 md:w-14 lg:w-16 h-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full mx-auto"></div>
          </div>

          {loading && (
            <div className="flex justify-center items-center py-16 sm:py-20">
              <p className="text-sm sm:text-base md:text-lg text-gray-500">Loading users...</p>
            </div>
          )}
          {error && (
            <div className="text-center py-10 sm:py-12">
              <p className="text-sm sm:text-base md:text-lg text-red-500 bg-red-50 dark:bg-red-900/20 px-4 py-3 sm:px-6 sm:py-4 rounded-lg inline-block">{error}</p>
            </div>
          )}

          {!loading && !error && (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 sm:gap-4 md:gap-5 lg:gap-6">
              {users.map((user) => (
                <div
                  key={user.id}
                  className="group relative p-3 sm:p-4 md:p-5 lg:p-6 bg-white dark:bg-slate-800 rounded-lg md:rounded-xl shadow-md hover:shadow-xl transition-all duration-300 ease-out cursor-default border border-slate-200 dark:border-slate-700"
                >
                  <div className="flex flex-col h-full">
                    <div className="mb-3 sm:mb-4">
                      <p className="text-base sm:text-lg md:text-xl font-bold text-gray-800 dark:text-white mb-1 line-clamp-1">{user.username}</p>
                      <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 line-clamp-1">{user.email}</p>
                    </div>

                    <div className="mb-3 sm:mb-4 md:mb-5 p-2 sm:p-2.5 md:p-3 bg-slate-50 dark:bg-slate-700 rounded-lg flex-grow">
                      <p className="text-xs sm:text-sm text-gray-700 dark:text-gray-300">
                        <span className="font-semibold block sm:inline">{user.role || "N/A"}</span>
                        <span className="hidden sm:inline mx-1">•</span>
                        <span className="font-semibold">{user.status || "N/A"}</span>
                      </p>
                    </div>

                    <div className="flex flex-col md:flex-row gap-2 sm:gap-2 md:gap-3 mt-auto">
                      <button className="flex-1 px-2 sm:px-3 md:px-4 py-1.5 sm:py-2 text-xs sm:text-sm md:text-base bg-teal-500 text-white font-medium rounded hover:bg-teal-600 hover:shadow-md transition-all duration-200 cursor-pointer">
                        View
                      </button>
                      <button className="flex-1 px-2 sm:px-3 md:px-4 py-1.5 sm:py-2 text-xs sm:text-sm md:text-base bg-amber-500 text-white font-medium rounded hover:bg-amber-600 hover:shadow-md transition-all duration-200 cursor-pointer">
                        Edit
                      </button>
                      <button onClick={() => handleDelete(user.id)} className="flex-1 px-2 sm:px-3 md:px-4 py-1.5 sm:py-2 text-xs sm:text-sm md:text-base bg-rose-500 text-white font-medium rounded hover:bg-rose-600 hover:shadow-md transition-all duration-200 cursor-pointer">
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
        </main>
      </div>
    </DashboardLayout>
  );
};

export default UsersPage;