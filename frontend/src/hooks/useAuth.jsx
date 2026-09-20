import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [officer, setOfficer] = useState(() => {
    const saved = localStorage.getItem('tracelink_officer_profile');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('tracelink_officer_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      if (token) {
        try {
          const res = await authApi.getMe();
          setOfficer(res.data);
          localStorage.setItem('tracelink_officer_profile', JSON.stringify(res.data));
        } catch (err) {
          console.error("Failed to verify officer session:", err);
          logout();
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, [token]);

  const login = async (badgeNumber, password, station) => {
    const res = await authApi.login({
      badge_number: badgeNumber,
      password: password,
      station: station
    });
    const data = res.data;
    localStorage.setItem('tracelink_officer_token', data.access_token);
    const profile = {
      badge_number: data.badge_number,
      rank: data.rank,
      police_station: data.station,
      clearance_level: data.clearance_level
    };
    localStorage.setItem('tracelink_officer_profile', JSON.stringify(profile));
    setToken(data.access_token);
    setOfficer(profile);
    return data;
  };

  const logout = () => {
    localStorage.removeItem('tracelink_officer_token');
    localStorage.removeItem('tracelink_officer_profile');
    setToken(null);
    setOfficer(null);
  };

  return (
    <AuthContext.Provider
      value={{
        officer,
        token,
        isAuthenticated: !!token,
        loading,
        login,
        logout,
        clearanceLevel: officer?.clearance_level || 'L1_INVESTIGATOR'
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
