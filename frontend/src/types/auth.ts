export interface UserProfile {
  id: string;
  firebase_uid?: string | null;
  email: string;
  display_name?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string) => Promise<void>;
  loginWithCredentials: (email: string, password: string) => Promise<void>;
  registerWithCredentials: (email: string, password: string, name: string) => Promise<void>;
  loginAsDemoAttorney: () => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
}
