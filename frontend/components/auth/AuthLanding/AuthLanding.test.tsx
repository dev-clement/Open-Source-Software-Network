import { render, screen } from '@testing-library/react';
import AuthLanding from './AuthLanding';

describe('AuthLanding', () => {
  it('renders both sign up and login buttons', () => {
    render(<AuthLanding onLoginClick={() => {}} />);
    // Adjust the button text below if your actual button labels differ
    expect(screen.getByRole('button', { name: /sign up/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });
});
