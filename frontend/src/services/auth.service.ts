import { apiClient } from './api';
import type { AuthResponse, LoginPayload, RegisterPayload, User } from '../types/auth';

export const authService = {
  async register(payload: RegisterPayload): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/register', payload);
    if (response.data.access_token) {
      localStorage.setItem('legalease_token', response.data.access_token);
      localStorage.setItem('legalease_user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  async login(payload: LoginPayload): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', payload);
    if (response.data.access_token) {
      localStorage.setItem('legalease_token', response.data.access_token);
      localStorage.setItem('legalease_user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me');
    localStorage.setItem('legalease_user', JSON.stringify(response.data));
    return response.data;
  },

  logout(): void {
    localStorage.removeItem('legalease_token');
    localStorage.removeItem('legalease_user');
  },

  getStoredUser(): User | null {
    const stored = localStorage.getItem('legalease_user');
    if (!stored) return null;
    try {
      return JSON.parse(stored) as User;
    } catch {
      return null;
    }
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('legalease_token');
  },
};
