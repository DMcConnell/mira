/**
 * Authentication service for managing JWT tokens
 */

const TOKEN_KEY = 'mira_token';

export interface LoginResponse {
  token: string;
  capabilities: string[];
}

export const authService = {
  setToken(token: string) {
    localStorage.setItem(TOKEN_KEY, token);
  },

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  },

  isAuthenticated(): boolean {
    return this.getToken() !== null;
  },
};

export const login = async (pin: string): Promise<LoginResponse> => {
  const formData = new FormData();
  formData.append('pin', pin);

  const response = await fetch('/auth/pin', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || 'Invalid PIN');
  }

  const data: LoginResponse = await response.json();
  authService.setToken(data.token);
  return data;
};

export const logout = () => {
  authService.clearToken();
  // Optionally reload the page to reset state
  window.location.reload();
};
