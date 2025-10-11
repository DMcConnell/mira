import { useState, useEffect, useRef } from 'react';
import { login } from '../lib/auth';
import './LoginModal.css';

interface LoginModalProps {
  isOpen: boolean;
  onSuccess: () => void;
}

export const LoginModal = ({ isOpen, onSuccess }: LoginModalProps) => {
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      // Focus input when modal opens
      inputRef.current?.focus();
      // Clear previous state
      setPin('');
      setError('');
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!pin) {
      setError('Please enter a PIN');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await login(pin);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid PIN');
      setPin('');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className='login-modal-overlay'>
      <div className='login-modal'>
        <div className='login-modal-header'>
          <h2>🔐 Authentication Required</h2>
          <p>Please enter your PIN to continue</p>
        </div>

        <form onSubmit={handleSubmit} className='login-form'>
          <div className='pin-input-group'>
            <input
              ref={inputRef}
              type='password'
              inputMode='numeric'
              pattern='[0-9]*'
              placeholder='Enter PIN'
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              disabled={isLoading}
              className='pin-input'
              autoComplete='off'
            />
          </div>

          {error && <div className='error-message'>{error}</div>}

          <button
            type='submit'
            disabled={isLoading || !pin}
            className='login-button'
          >
            {isLoading ? 'Authenticating...' : 'Login'}
          </button>
        </form>

        <div className='login-modal-footer'>
          <small>Default PIN for development: 1234</small>
        </div>
      </div>
    </div>
  );
};
