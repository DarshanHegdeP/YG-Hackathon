import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Bell, Shield } from 'lucide-react';

export const Navbar = ({ title }) => {
  const { user } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-10 shadow-xs">
      <div>
        <h2 className="text-xl font-bold text-slate-800">{title || 'LOD2 Evidence Platform'}</h2>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 text-xs text-slate-600 bg-slate-100 px-3 py-1.5 rounded-full border border-slate-200">
          <Shield className="w-3.5 h-3.5 text-blue-600" />
          <span>Second Line of Defense (LOD2) Testing</span>
        </div>

        {user && (
          <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
            <span className="text-xs font-medium text-slate-700">{user.name}</span>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
              {user.role}
            </span>
          </div>
        )}
      </div>
    </header>
  );
};
