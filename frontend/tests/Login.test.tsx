import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../src/context/AuthContext';
import { LoginPage } from '../src/pages/LoginPage';

const renderLogin = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('LoginPage Component', () => {
  it('renders login form with email and password inputs', () => {
    renderLogin();
    expect(screen.getByTestId('email-input')).toBeInTheDocument();
    expect(screen.getByTestId('password-input')).toBeInTheDocument();
    expect(screen.getByTestId('login-submit-btn')).toHaveTextContent('Sign In');
  });

  it('validates empty inputs on submit', async () => {
    renderLogin();
    const submitBtn = screen.getByTestId('login-submit-btn');
    fireEvent.click(submitBtn);

    const errorAlert = await screen.findByTestId('login-error');
    expect(errorAlert).toHaveTextContent('Both email and password are required');
  });

  it('validates malformed email address on submit', async () => {
    renderLogin();
    const emailInput = screen.getByTestId('email-input');
    const passwordInput = screen.getByTestId('password-input');
    const submitBtn = screen.getByTestId('login-submit-btn');

    fireEvent.change(emailInput, { target: { value: 'notanemail' } });
    fireEvent.change(passwordInput, { target: { value: 'somepass' } });
    fireEvent.click(submitBtn);

    const errorAlert = await screen.findByTestId('login-error');
    expect(errorAlert).toHaveTextContent('Please provide a valid email address');
  });

  it('updates form values as user types', () => {
    renderLogin();
    const emailInput = screen.getByTestId('email-input') as HTMLInputElement;
    const passwordInput = screen.getByTestId('password-input') as HTMLInputElement;

    fireEvent.change(emailInput, { target: { value: 'admin@phoenix.local' } });
    fireEvent.change(passwordInput, { target: { value: 'AdminPass123!' } });

    expect(emailInput.value).toBe('admin@phoenix.local');
    expect(passwordInput.value).toBe('AdminPass123!');
  });
});
