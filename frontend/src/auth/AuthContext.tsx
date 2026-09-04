import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole } from '../types';
import { api, setDevRole, getStoredDevRole, setAuthToken } from '../services/api';

interface AuthContextType {
  user: User | null;
  role: UserRole;
  isLoading: boolean;
  isDevMode: boolean;
  switchRole: (newRole: UserRole) => Promise<void>;
  login: () => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [role, setRole] = useState<UserRole>(getStoredDevRole());
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isDevMode, setIsDevMode] = useState<boolean>(true);

  const fetchUser = async () => {
    setIsLoading(true);
    try {
      const config = await api.getAuthConfig();
      setIsDevMode(config.dev_mode);

      const profile = await api.getCurrentUser();
      setUser(profile);
      setRole(profile.role);
    } catch (err) {
      console.warn('Could not fetch user profile:', err);
      const currentRole = getStoredDevRole();
      setUser({
        id: 'dev-user-001',
        entra_user_id: 'entra-user-dev-001',
        name: currentRole === 'hr_admin' ? 'Marcus Vance (HR Admin)' : 'Vansh Rupesh (Employee)',
        email: currentRole === 'hr_admin' ? 'hr.lead@tangentia.com' : 'employee@tangentia.com',
        role: currentRole,
        created_at: new Date().toISOString(),
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const switchRole = async (newRole: UserRole) => {
    setDevRole(newRole);
    setRole(newRole);
    await fetchUser();
  };

  const login = async () => {
    // In production with MSAL, this triggers msalInstance.loginPopup / loginRedirect
    // In dev mode, we refresh user
    await fetchUser();
  };

  const logout = () => {
    setAuthToken(null);
    setUser(null);
    window.location.reload();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        isLoading,
        isDevMode,
        switchRole,
        login,
        logout,
        refreshUser: fetchUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
