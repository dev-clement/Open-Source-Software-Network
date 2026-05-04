import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import LoginForm from './LoginForm';

const loginMock = jest.fn();
const handleChangeMock = jest.fn();
const resetFormMock = jest.fn();

let mockValues = { email: '', password: '' };
let mockErrors: { email?: string; password?: string } = {};
let mockValidateForm = jest.fn(() => true);
let mockLoading = false;

jest.mock('@auth/useLogin', () => ({
  useLogin: () => ({
    login: loginMock,
    loading: mockLoading,
  }),
}));

jest.mock('@auth/useLoginForm', () => ({
  useLoginForm: () => ({
    values: mockValues,
    errors: mockErrors,
    handleChange: handleChangeMock,
    validateForm: mockValidateForm,
    resetForm: resetFormMock,
  }),
}));

jest.mock('@shared/NotificationBadge', () => (props: { message: string }) => (
  <div data-testid="notification-badge">{props.message}</div>
));

jest.mock(
  '@shared/InputWithIcon',
  () =>
    (props: {
      name: string;
      value: string;
      onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
    }) => (
      <input
        data-testid={props.name}
        value={props.value}
        onChange={props.onChange}
      />
    )
);

describe('LoginForm', () => {
  beforeEach(() => {
    mockValues = { email: '', password: '' };
    mockErrors = {};
    mockValidateForm = jest.fn(() => true);
    mockLoading = false;

    loginMock.mockReset();
    loginMock.mockResolvedValue({ status: 'success' });
    handleChangeMock.mockReset();
    resetFormMock.mockReset();
  });

  it('renders email and password fields and login button', () => {
    render(<LoginForm />);

    expect(screen.getByTestId('email')).toBeInTheDocument();
    expect(screen.getByTestId('password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('disables login button when fields are empty', () => {
    render(<LoginForm />);

    expect(screen.getByRole('button', { name: /login/i })).toBeDisabled();
  });

  it('shows an error badge when validation fails', async () => {
    mockErrors = { email: 'Email required' };
    mockValidateForm = jest.fn(() => false);

    render(<LoginForm />);

    const form = screen.getByRole('button', { name: /login/i }).closest('form');
    expect(form).not.toBeNull();

    if (form) {
      fireEvent.submit(form);
    }

    await waitFor(() => {
      expect(screen.getByTestId('notification-badge')).toHaveTextContent(
        'Email required'
      );
    });
    expect(loginMock).not.toHaveBeenCalled();
  });

  it('calls login with correct values', async () => {
    mockValues = { email: 'test@example.com', password: 'pass' };

    render(<LoginForm />);

    const form = screen.getByRole('button', { name: /login/i }).closest('form');
    expect(form).not.toBeNull();

    if (form) {
      fireEvent.submit(form);
    }

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith('test@example.com', 'pass');
    });
    expect(resetFormMock).toHaveBeenCalled();
  });
});
