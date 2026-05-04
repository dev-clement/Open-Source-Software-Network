import { useState } from 'react';
import axios from 'axios';

export interface LoginResult {
  status: 'success' | 'error';
  message?: string;
}

export interface UseLoginResult {
  login: (email: string, password: string) => Promise<LoginResult>;
  loading: boolean;
}

export function useLogin(): UseLoginResult {
  const [loading, setLoading] = useState(false);

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
