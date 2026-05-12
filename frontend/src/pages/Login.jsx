import React, { useState } from 'react';
import { Code2, Eye, EyeOff, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { API_BASE_URL } from '../config/env';

const Login = () => {
  const [isRegister, setIsRegister] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();
  const { darkMode } = useTheme();

  const toggleMode = () => {
    setIsRegister(!isRegister);
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      let endpoint = isRegister ? '/api/auth/register' : '/api/auth/login';
      let body;

      if (isRegister) {
        body = JSON.stringify({ username, email, password });
      } else {
        // For login, use form-encoded data as required by OAuth2PasswordRequestForm
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        body = formData;
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: isRegister ? { 'Content-Type': 'application/json' } : { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      login(data.access_token, { username, email });
      navigate('/codegen');
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 relative overflow-hidden items-center justify-center p-12">
        {/* Background Effect */}
        <div className="absolute top-0 right-0 w-3/4 h-3/4 bg-gradient-to-br from-indigo-500/20 to-transparent rounded-full blur-3xl" />

        <div className="relative z-10 max-w-md">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-8">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Code2 size={32} className="text-white" />
            </div>
            <span className="text-3xl font-bold bg-gradient-to-r from-indigo-500 to-violet-600 bg-clip-text text-transparent">
              iSDS
            </span>
          </div>

          <h1 className="text-4xl font-bold text-white leading-tight mb-4">
            Intelligent Software<br />Development System
          </h1>
          <p className="text-slate-400 text-lg mb-8 leading-relaxed">
            Build, test, and deploy applications with AI-powered automation.
          </p>

          {/* Features List */}
          <div className="space-y-4">
            <div className="flex items-center gap-3 text-slate-300">
              <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span>Auto-generated project structure</span>
            </div>
            <div className="flex items-center gap-3 text-slate-300">
              <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span>Docker containerization</span>
            </div>
            <div className="flex items-center gap-3 text-slate-300">
              <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span>Real-time QA testing</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className={`w-full lg:w-1/2 flex items-center justify-center p-8 ${darkMode ? 'bg-slate-900' : 'bg-slate-50'}`}>
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-2 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Code2 size={24} className="text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-indigo-500 to-violet-600 bg-clip-text text-transparent">
              iSDS
            </span>
          </div>

          <div className={`p-8 rounded-2xl shadow-sm border ${darkMode ? 'bg-slate-800 border-slate-700' : 'bg-white border-slate-100'}`}>
            <h2 className={`text-2xl font-bold mb-1 ${darkMode ? 'text-white' : 'text-slate-800'}`}>
              {isRegister ? 'Create Account' : 'Welcome Back'}
            </h2>
            <p className={`text-sm mb-6 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
              {isRegister ? 'Start building with AI' : 'Enter your credentials'}
            </p>

            {error && (
              <div className={`flex items-center gap-2 p-3 mb-4 rounded-lg text-sm ${
                darkMode
                  ? 'bg-red-900/30 border border-red-700 text-red-400'
                  : 'bg-red-50 border border-red-200 text-red-600'
              }`}>
                <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {isRegister && (
                <div className="form-group">
                  <label className={`block text-sm font-medium mb-1 ${darkMode ? 'text-slate-300' : 'text-slate-700'}`}>Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={`w-full px-4 py-3 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all ${
                      darkMode
                        ? 'bg-slate-800 border-slate-600 text-white placeholder-slate-400'
                        : 'bg-white border-slate-200 text-slate-900 placeholder-slate-400'
                    }`}
                    placeholder="you@example.com"
                    required={isRegister}
                  />
                </div>
              )}

              <div className="form-group">
                <label className={`block text-sm font-medium mb-1 ${darkMode ? 'text-slate-300' : 'text-slate-700'}`}>Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className={`w-full px-4 py-3 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all ${
                    darkMode
                      ? 'bg-slate-800 border-slate-600 text-white placeholder-slate-400'
                      : 'bg-white border-slate-200 text-slate-900 placeholder-slate-400'
                  }`}
                  placeholder="Enter username"
                  required
                />
              </div>

              <div className="form-group">
                <label className={`block text-sm font-medium mb-1 ${darkMode ? 'text-slate-300' : 'text-slate-700'}`}>Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={`w-full px-4 py-3 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all pr-12 ${
                      darkMode
                        ? 'bg-slate-800 border-slate-600 text-white placeholder-slate-400'
                        : 'bg-white border-slate-200 text-slate-900 placeholder-slate-400'
                    }`}
                    placeholder="Enter password"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className={`absolute right-3 top-1/2 -translate-y-1/2 ${darkMode ? 'text-slate-400 hover:text-slate-300' : 'text-slate-400 hover:text-slate-600'}`}
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-6 bg-gradient-to-r from-indigo-500 to-violet-600 text-white rounded-lg font-medium text-sm flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-indigo-500/30 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    <span>Please wait...</span>
                  </>
                ) : (
                  <>{isRegister ? 'Create Account' : 'Sign In'}</>
                )}
              </button>
            </form>

            <div className={`text-center mt-6 text-sm ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
              {isRegister ? 'Already have an account?' : "Don't have an account?"}
              <button
                onClick={toggleMode}
                className="ml-1 text-indigo-500 font-medium hover:text-indigo-600"
              >
                {isRegister ? 'Sign In' : 'Create one'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;