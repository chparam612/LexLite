export interface UserProfile {
  id: string;
  firebase_uid: string;
  email: string;
  display_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string) => Promise<void>;
  loginAsDemoAttorney: () => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
}
