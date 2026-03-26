// ============================================================
// Ha_Chain - Auth Context (React Context for auth state)
// ============================================================

import React, { createContext, useContext, useEffect, useReducer, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../services/api';
import { ApiResponse, AuthTokens, User } from '../types';
import { STORAGE_KEYS } from '../utils/constants';

// --- State ---

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// --- Actions ---

type AuthAction =
  | { type: 'RESTORE_SESSION'; user: User }
  | { type: 'LOGIN_SUCCESS'; user: User }
  | { type: 'LOGOUT' }
  | { type: 'SET_LOADING'; isLoading: boolean }
  | { type: 'SET_ERROR'; error: string }
  | { type: 'CLEAR_ERROR' }
  | { type: 'UPDATE_USER'; user: User };

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'RESTORE_SESSION':
      return { ...state, user: action.user, isAuthenticated: true, isLoading: false };
    case 'LOGIN_SUCCESS':
      return { ...state, user: action.user, isAuthenticated: true, isLoading: false, error: null };
    case 'LOGOUT':
      return { ...initialState, isLoading: false };
    case 'SET_LOADING':
      return { ...state, isLoading: action.isLoading };
    case 'SET_ERROR':
      return { ...state, error: action.error, isLoading: false };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    case 'UPDATE_USER':
      return { ...state, user: action.user };
    default:
      return state;
  }
}

// --- Context ---

interface AuthContextValue extends AuthState {
  requestOTP: (phone: string, countryCode: string) => Promise<void>;
  verifyOTP: (phone: string, countryCode: string, otp: string) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// --- Provider ---

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Restore session on app start
  useEffect(() => {
    const restoreSession = async () => {
      try {
        const [token, userJson] = await AsyncStorage.multiGet([
          STORAGE_KEYS.ACCESS_TOKEN,
          STORAGE_KEYS.USER,
        ]);

        if (token[1] && userJson[1]) {
          const user: User = JSON.parse(userJson[1]);
          dispatch({ type: 'RESTORE_SESSION', user });
        } else {
          dispatch({ type: 'SET_LOADING', isLoading: false });
        }
      } catch {
        dispatch({ type: 'SET_LOADING', isLoading: false });
      }
    };

    restoreSession();
  }, []);

  const requestOTP = async (phone: string, countryCode: string): Promise<void> => {
    dispatch({ type: 'SET_LOADING', isLoading: true });
    dispatch({ type: 'CLEAR_ERROR' });

    try {
      await api.post('/auth/request-otp', { phone, countryCode });
      dispatch({ type: 'SET_LOADING', isLoading: false });
    } catch (err: any) {
      const message = err?.response?.data?.message || 'Failed to send OTP. Please try again.';
      dispatch({ type: 'SET_ERROR', error: message });
      throw err;
    }
  };

  const verifyOTP = async (phone: string, countryCode: string, otp: string): Promise<void> => {
    dispatch({ type: 'SET_LOADING', isLoading: true });
    dispatch({ type: 'CLEAR_ERROR' });

    try {
      const { data } = await api.post<ApiResponse<{ tokens: AuthTokens; user: User }>>(
        '/auth/verify-otp',
        { phone, countryCode, otp },
      );

      const { tokens, user } = data.data;

      await AsyncStorage.multiSet([
        [STORAGE_KEYS.ACCESS_TOKEN, tokens.accessToken],
        [STORAGE_KEYS.REFRESH_TOKEN, tokens.refreshToken],
        [STORAGE_KEYS.USER, JSON.stringify(user)],
      ]);

      dispatch({ type: 'LOGIN_SUCCESS', user });
    } catch (err: any) {
      const message = err?.response?.data?.message || 'Invalid OTP. Please try again.';
      dispatch({ type: 'SET_ERROR', error: message });
      throw err;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Logout even if the API call fails
    }

    await AsyncStorage.multiRemove([
      STORAGE_KEYS.ACCESS_TOKEN,
      STORAGE_KEYS.REFRESH_TOKEN,
      STORAGE_KEYS.USER,
    ]);

    dispatch({ type: 'LOGOUT' });
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  return (
    <AuthContext.Provider
      value={{
        ...state,
        requestOTP,
        verifyOTP,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// --- Hook ---

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
