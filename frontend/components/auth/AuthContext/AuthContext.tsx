'use client';
import { createContext, useContext, useState, ReactNode } from 'react';

/**
 * @typedef {Object} AuthContextType
 * @property {boolean} isLoggedIn - Whether the user is logged in
 * @property {() => void} login - Function to log in the user
 * @property {() => void} logout - Function to log out the user
 */

interface AuthContextType {
  isLoggedIn: boolean;
  login: () => void;
  logout: () => void;
}

export type { AuthContextType };

/**
 * React Context for authentication state and actions.
 *
 * This context is created using React's createContext function, which allows you to
 * share authentication state (such as isLoggedIn, login, and logout) across your component tree
 * without having to pass props down manually at every level.
 *
 * The context is initialized with undefined, and its value is provided by the AuthProvider component.
 *
 * @type {React.Context<AuthContextType | undefined>}
 */
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * AuthProvider component to wrap your app and provide authentication state.
 * @param {Object} props - Component props
 * @param {ReactNode} props.children - Child components
 * @returns {JSX.Element}
 */
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  /**
   * Log in the user (mock implementation).
   * Replace with real backend call later.
   */
  const login = () => {
    setIsLoggedIn(true);
  };

  /**
   * Log out the user.
   */
  const logout = () => {
    setIsLoggedIn(false);
  };

  return (
    <AuthContext.Provider value={{ isLoggedIn, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Custom hook to access authentication state and actions.
 * @returns {AuthContextType} The authentication context value
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
