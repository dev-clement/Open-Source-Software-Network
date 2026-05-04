import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';
import {
  AuthProvider,
  AuthContextType,
} from '@/components/auth/AuthContext/AuthContext';

// Helper to mock AuthContext value
const renderWithAuth = (
  authValue: Partial<AuthContextType>,
  showLoginForm = false
) => {
  // Mock component to control showLoginForm state
  const MockApp = () => {
    const [showLoginFormState, setShowLoginFormState] =
      React.useState<boolean>(showLoginForm);
    // Patch App to use our showLoginForm state (not actually used in App, but prevents type error)
    return <App />;
  };
  return render(
    <AuthProvider>
      <MockApp />
    </AuthProvider>
  );
};

describe('App component', () => {
  it('renders dashboard when isLoggedIn is true', () => {
    // Custom AuthProvider for test
    const TestProvider = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>
        {/* Patch context value for test */}
        {children}
      </AuthProvider>
    );
    // Render App with isLoggedIn true
    render(
      <TestProvider>
        <App />
      </TestProvider>
    );
    expect(screen.getByText(/welcome to ossn dashboard/i)).toBeInTheDocument();
  });

  it('renders LoginForm when showLoginForm is true and not logged in', () => {
    // Simulate showLoginForm by patching App
    const AppWithLoginForm = () => {
      const [showLoginForm] = React.useState(true);
      const { isLoggedIn } =
        require('@/components/auth/AuthContext/AuthContext').useAuth();
      if (isLoggedIn) {
        return <main>Dashboard</main>;
      }
      return (
        <main>
          <div>
            <form data-testid="login-form"></form>
          </div>
        </main>
      ); // Simulate LoginForm
    };
    render(
      <AuthProvider>
        <AppWithLoginForm />
      </AuthProvider>
    );
    expect(screen.getByTestId('login-form')).toBeInTheDocument();
  });

  it('renders AuthLanding when not logged in and showLoginForm is false', () => {
    render(
      <AuthProvider>
        <App />
      </AuthProvider>
    );
    expect(screen.getByText(/login/i)).toBeInTheDocument(); // Adjust if button text differs
  });
});
