export interface User {
  id: number;
  email: string;
  full_name: string;
  preferred_language: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  preferred_language?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}
