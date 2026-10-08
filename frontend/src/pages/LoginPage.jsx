import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, Mail, ArrowRight, CheckCircle2 } from 'lucide-react';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoAccount = (demoEmail, demoPass = 'Password123!') => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError('');
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="mx-auto w-14 h-14 bg-blue-600 rounded-2xl flex items-center justify-center text-white shadow-xl shadow-blue-500/30 mb-4">
          <Shield className="w-8 h-8" />
        </div>
        <h2 className="text-3xl font-extrabold text-white tracking-tight">
          LOD2 Evidence Bot
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          AI-Powered Control Testing & Autonomous Evidence Collection
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-800/90 py-8 px-6 shadow-2xl rounded-2xl sm:px-10 border border-slate-700 backdrop-blur-sm">
          {error && (
            <div className="mb-5 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-medium">
              {error}
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Corporate Email Address
              </label>
              <div className="relative rounded-md shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="reviewer@example.com"
                  className="bg-slate-900/80 border border-slate-700 text-white rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-9 p-2.5 text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Password
              </label>
              <div className="relative rounded-md shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="bg-slate-900/80 border border-slate-700 text-white rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-9 p-2.5 text-sm"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center space-x-2 py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 focus:outline-hidden focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all disabled:opacity-50"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* 1-Click Demo Accounts */}
          <div className="mt-6 pt-6 border-t border-slate-700/80">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2 text-center">
              Quick 1-Click Demo Logins
            </span>
            <div className="grid grid-cols-1 gap-2">
              <button
                type="button"
                onClick={() => fillDemoAccount('reviewer@example.com')}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 hover:bg-slate-700 border border-slate-700 text-xs text-slate-300 transition-colors"
              >
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                  <span className="font-semibold text-white">Reviewer</span>
                  <span className="text-slate-500">(Full review & remind powers)</span>
                </div>
                <span className="text-[10px] text-blue-400 font-mono">Fill</span>
              </button>

              <button
                type="button"
                onClick={() => fillDemoAccount('admin@example.com')}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 hover:bg-slate-700 border border-slate-700 text-xs text-slate-300 transition-colors"
              >
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                  <span className="font-semibold text-white">Admin</span>
                  <span className="text-slate-500">(System management)</span>
                </div>
                <span className="text-[10px] text-purple-400 font-mono">Fill</span>
              </button>

              <button
                type="button"
                onClick={() => fillDemoAccount('business@example.com')}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-900/60 hover:bg-slate-700 border border-slate-700 text-xs text-slate-300 transition-colors"
              >
                <div className="flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                  <span className="font-semibold text-white">Business User</span>
                  <span className="text-slate-500">(Submitter role)</span>
                </div>
                <span className="text-[10px] text-emerald-400 font-mono">Fill</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
