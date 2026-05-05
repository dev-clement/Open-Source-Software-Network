import { act, renderHook } from '@testing-library/react';
import { useLoginForm } from './useLoginForm';

describe('useLoginForm', () => {
  it('initializes with default values and no errors', () => {
    const { result } = renderHook(() => useLoginForm());

    expect(result.current.values).toEqual({ email: '', password: '' });
    expect(result.current.errors).toEqual({});
  });

  it('returns validation errors for empty fields', () => {
    const { result } = renderHook(() => useLoginForm());

    let isValid = false;

    act(() => {
      isValid = result.current.validateForm();
    });

    expect(isValid).toBe(false);
    expect(result.current.errors).toEqual({
      email: 'Email is required.',
      password: 'Password is required.',
    });
  });

  it('validates email format and password length', () => {
    const { result } = renderHook(() => useLoginForm());

    act(() => {
      result.current.setValues({ email: 'invalid-email', password: '123' });
    });

    let isValid = false;

    act(() => {
      isValid = result.current.validateForm();
    });

    expect(isValid).toBe(false);
    expect(result.current.errors).toEqual({
      email: 'Please enter a valid email address.',
      password: 'Password must be at least 6 characters.',
    });
  });

  it('updates a field and clears the matching error on change', () => {
    const { result } = renderHook(() => useLoginForm());

    act(() => {
      result.current.setErrors({ email: 'Email is required.' });
    });

    act(() => {
      result.current.handleChange({
        target: { name: 'email', value: 'user@example.com' },
      } as React.ChangeEvent<HTMLInputElement>);
    });

    expect(result.current.values.email).toBe('user@example.com');
    expect(result.current.errors.email).toBeUndefined();
  });

  it('resets values and errors back to the initial state', () => {
    const initialState = { email: 'seed@example.com', password: 'secret123' };
    const { result } = renderHook(() => useLoginForm(initialState));

    act(() => {
      result.current.setValues({
        email: 'changed@example.com',
        password: 'abcdef',
      });
      result.current.setErrors({ password: 'Password is required.' });
    });

    act(() => {
      result.current.resetForm();
    });

    expect(result.current.values).toEqual(initialState);
    expect(result.current.errors).toEqual({});
  });
});
