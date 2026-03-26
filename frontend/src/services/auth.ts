import axios from 'axios';

const API_BASE = '/api/auth';

const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

export interface User {
  id: number;
  username: string;
  role: 'admin' | 'normal' | 'viewer';
  created_at: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  password: string;
}

export interface AdminCreateUser {
  username: string;
  password: string;
  role: 'admin' | 'normal' | 'viewer';
}

export interface UserListResponse {
  users: User[];
  total: number;
}

function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function setTokens(tokens: Token): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

function getAuthHeaders(): Record<string, string> {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const authApi = {
  async login(credentials: LoginCredentials): Promise<Token> {
    const response = await axios.post(`${API_BASE}/login`, credentials);
    const tokens = response.data;
    setTokens(tokens);
    return tokens;
  },

  async register(credentials: RegisterCredentials): Promise<User> {
    const response = await axios.post(`${API_BASE}/register`, credentials);
    return response.data;
  },

  async refreshToken(): Promise<Token> {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    const response = await axios.post(`${API_BASE}/refresh`, {
      refresh_token: refreshToken
    });
    const tokens = response.data;
    setTokens(tokens);
    return tokens;
  },

  async getCurrentUser(): Promise<User> {
    const response = await axios.get(`${API_BASE}/me`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async createUser(userData: AdminCreateUser): Promise<User> {
    const response = await axios.post(`${API_BASE}/users`, userData, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async getUsers(): Promise<UserListResponse> {
    const response = await axios.get(`${API_BASE}/users`, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async updateUserRole(userId: number, role: 'admin' | 'normal' | 'viewer'): Promise<User> {
    const response = await axios.put(`${API_BASE}/users/${userId}/role`, { role }, {
      headers: getAuthHeaders()
    });
    return response.data;
  },

  async deleteUser(userId: number): Promise<void> {
    await axios.delete(`${API_BASE}/users/${userId}`, {
      headers: getAuthHeaders()
    });
  },

  logout(): void {
    clearTokens();
  },

  isLoggedIn(): boolean {
    return !!getAccessToken();
  }
};

export default authApi;
