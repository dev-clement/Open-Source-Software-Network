import { useState } from 'react';
import axios from 'axios';

/**
 * Describes the outcome of a login attempt.
 */
export interface LoginResult {
  status: 'success' | 'error';
  message?: string;
}

/**
 * Exposes the login action and its loading state.
 */
export interface UseLoginResult {
  login: (email: string, password: string) => Promise<LoginResult>;
  loading: boolean;
}

/**
 * Provides login submission state and an async action for authenticating a user.
 *
 * @returns Hook state containing the login action and loading flag.
 */
export function useLogin(): UseLoginResult {
  const [loading, setLoading] = useState(false);

  /**
   * Attempts to authenticate the user with the provided credentials.
   *
   * @param email User email address.
   * @param password User password.
   * @returns The login result status and an optional error message.
   */
  const login = async (
    email: string,
    password: string
  ): Promise<LoginResult> => {
    setLoading(true);
    try {
      await axios.post('/api/auth/login', { email, password });
      setLoading(false);
      return { status: 'success' };
    } catch (error: any) {
      setLoading(false);
      let message = 'Login failed';
      if (error.response?.data?.message) {
        message = error.response.data.message;
      } else if (error.message) {
        message = error.message;
      }
      return { status: 'error', message };
    }
  };

  return { login, loading };
}
