import { act } from '@testing-library/react';
import { render, screen } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';

/**
 * Test component to consume useAuth and display login state.
 */
const TestComponent = () => {
  const { isLoggedIn, login, logout } = useAuth();
  return (
    <div>
      <span data-testid="status">
        {isLoggedIn ? 'logged-in' : 'logged-out'}
      </span>
      <button onClick={login}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

describe('AuthProvider and useAuth', () => {
  it('should default to logged out', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    expect(screen.getByTestId('status').textContent).toBe('logged-out');
  });

  it('should log in and log out', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    const status = screen.getByTestId('status');
    const loginBtn = screen.getByText('Login');
    const logoutBtn = screen.getByText('Logout');

    // Log in
    act(() => {
      loginBtn.click();
    });
    expect(status.textContent).toBe('logged-in');

    // Log out
    act(() => {
      logoutBtn.click();
    });
    expect(status.textContent).toBe('logged-out');
  });

  it('should throw if useAuth is used outside AuthProvider', () => {
    // Suppress error output for this test
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const BrokenComponent = () => {
      useAuth();
      return null;
    };
    expect(() => render(<BrokenComponent />)).toThrow(
      'useAuth must be used within an AuthProvider'
    );
    spy.mockRestore();
  });
});
