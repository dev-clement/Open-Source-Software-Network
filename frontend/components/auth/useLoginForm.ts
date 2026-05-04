import { useState } from 'react';

export interface LoginFormState {
  email: string;
  password: string;
}

export interface LoginFormValidation {
  email?: string;
  password?: string;
}

export function useLoginForm(
  initialState: LoginFormState = { email: '', password: '' }
) {
  const [values, setValues] = useState<LoginFormState>(initialState);
  const [errors, setErrors] = useState<LoginFormValidation>({});

  const validate = (fieldValues = values): LoginFormValidation => {
    const temp: LoginFormValidation = {};
    if (!fieldValues.email) temp.email = 'Email is required.';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(fieldValues.email))
      temp.email = 'Please enter a valid email address.';
    if (!fieldValues.password) temp.password = 'Password is required.';
    else if (fieldValues.password.length < 6)
      temp.password = 'Password must be at least 6 characters.';
    return temp;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setValues({ ...values, [name]: value });
    setErrors({ ...errors, [name]: undefined });
  };

  const validateForm = () => {
    const validationErrors = validate();
    setErrors(validationErrors);
    return Object.keys(validationErrors).length === 0;
  };

  const resetForm = () => {
    setValues(initialState);
    setErrors({});
  };

  return {
    values,
    setValues,
    errors,
    setErrors,
    handleChange,
    validateForm,
    resetForm,
  };
}
