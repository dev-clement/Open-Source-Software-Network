import { act, renderHook, waitFor } from '@testing-library/react';
import axios from 'axios';
import { type LoginResult, useLogin } from './useLogin';

jest.mock('axios');

const mockedAxios = axios as jest.Mocked<typeof axios>;

function createDeferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;

  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });

  return { promise, resolve, reject };
}

describe('useLogin', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('sets loading while the login request is pending', async () => {
    const deferred = createDeferred<{ data: object }>();
    mockedAxios.post.mockReturnValueOnce(deferred.promise);

    const { result } = renderHook(() => useLogin());

    let loginPromise: Promise<{
      status: 'success' | 'error';
      message?: string;
    }>;

    act(() => {
      loginPromise = result.current.login('user@example.com', 'secret123');
    });

    expect(result.current.loading).toBe(true);

    deferred.resolve({ data: {} });

    await act(async () => {
      await loginPromise;
    });

    expect(result.current.loading).toBe(false);
  });

  it('returns a success result when the request resolves', async () => {
    mockedAxios.post.mockResolvedValueOnce({ data: {} });

    const { result } = renderHook(() => useLogin());

    let loginResult: LoginResult | undefined;

    await act(async () => {
      loginResult = await result.current.login('user@example.com', 'secret123');
    });

    expect(mockedAxios.post).toHaveBeenCalledWith('/api/auth/login', {
      email: 'user@example.com',
      password: 'secret123',
    });
    expect(loginResult).toEqual({ status: 'success' });
    expect(result.current.loading).toBe(false);
  });

  it('returns the API error message when the request fails', async () => {
    mockedAxios.post.mockRejectedValueOnce({
      response: { data: { message: 'Invalid credentials' } },
    });

    const { result } = renderHook(() => useLogin());

    let loginResult: LoginResult | undefined;

    await act(async () => {
      loginResult = await result.current.login(
        'user@example.com',
        'wrong-pass'
      );
    });

    expect(loginResult).toEqual({
      status: 'error',
      message: 'Invalid credentials',
    });
    expect(result.current.loading).toBe(false);
  });

  it('falls back to the thrown error message when no API message exists', async () => {
    mockedAxios.post.mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useLogin());

    let loginResult: LoginResult | undefined;

    await act(async () => {
      loginResult = await result.current.login('user@example.com', 'secret123');
    });

    await waitFor(() => {
      expect(loginResult).toEqual({
        status: 'error',
        message: 'Network error',
      });
    });
    expect(result.current.loading).toBe(false);
  });
});
