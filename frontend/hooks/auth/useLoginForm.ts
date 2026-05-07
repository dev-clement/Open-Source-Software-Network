import { useState } from 'react';

/**
 * Represents the controlled values managed by the login form.
 */
export interface LoginFormState {
  email: string;
  password: string;
}

/**
 * Contains validation messages for each login form field.
 */
export interface LoginFormValidation {
  email?: string;
  password?: string;
}

/**
 * Manages login form values, validation state, and common form handlers.
 *
 * @param initialState Initial values used to seed and reset the form state.
 * @returns Form values, validation errors, and state management helpers.
 */
export function useLoginForm(
  initialState: LoginFormState = { email: '', password: '' }
) {
  const [values, setValues] = useState<LoginFormState>(initialState);
  const [errors, setErrors] = useState<LoginFormValidation>({});

  /**
   * Validates login form fields and returns the matching error messages.
   *
   * @param fieldValues Form values to validate. Defaults to the current form state.
   * @returns A collection of validation messages keyed by field name.
   */
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

  /**
   * Updates the targeted field value and clears any existing error for that field.
   *
   * @param e Change event emitted by a login form input.
   */
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setValues({ ...values, [name]: value });
    setErrors({ ...errors, [name]: undefined });
  };

  /**
   * Runs validation against the current form values and stores the resulting errors.
   *
   * @returns True when the form is valid, otherwise false.
   */
  const validateForm = () => {
    const validationErrors = validate();
    setErrors(validationErrors);
    return Object.keys(validationErrors).length === 0;
  };

  /**
   * Restores the form values and validation state to their initial configuration.
   */
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
