import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext({
  isAuthenticated: false,
  user: null,
  login: () => {},
  logout: () => {},
});

export const useAuth = () => {
  return useContext(AuthContext);
};

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for auth token on mount
    const token = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('user');
    if (token) {
      setIsAuthenticated(true);
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      }
    }
    setLoading(false);
  }, []);

  const login = (token, userData = null) => {
    localStorage.setItem('auth_token', token);
    if (userData) {
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
    }
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;