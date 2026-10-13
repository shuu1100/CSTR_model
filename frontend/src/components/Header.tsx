import React, { useEffect, useState } from 'react';
import {
  FlaskConical,
  PlayCircle,
  Compass,
  FileSpreadsheet,
  Sliders,
  BrainCircuit,
  BookOpen,
  Radio,
} from 'lucide-react';
import { api } from '../api/client';
import { HealthResponse } from '../api/types';

interface HeaderProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ currentTab, onTabChange }) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(false);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const h = await api.getHealth();
        setHealth(h);
        setIsOnline(true);
      } catch {
        setIsOnline(false);
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'simulator', label: 'Simulator', icon: PlayCircle },
    { id: 'sweeps', label: 'Sensitivity Sweeps', icon: Compass },
    { id: 'ingestion', label: 'Data Ingestion', icon: FileSpreadsheet },
    { id: 'estimation', label: 'Parameter Estimation', icon: Sliders },
    { id: 'ml', label: 'Neural ODE & PINN', icon: BrainCircuit },
    { id: 'overview', label: 'Theory & Oracles', icon: BookOpen },
  ];

  return (
    <header className="border-b border-slate-800/80 bg-slate-950/75 backdrop-blur-xl sticky top-0 z-50 shadow-2xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Digital Twin Title */}
          <div
            className="flex items-center space-x-3 cursor-pointer group"
            onClick={() => onTabChange('simulator')}
          >
            <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 group-hover:bg-emerald-500/20 group-hover:border-emerald-500/50 transition-all duration-300 shadow-[0_0_15px_rgba(16,185,129,0.15)]">
              <FlaskConical className="w-5 h-5 group-hover:scale-105 transition-transform" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-base font-extrabold tracking-tight text-white group-hover:text-emerald-300 transition-colors">
                  CSTR Lab
                </span>
                <span className="text-[10px] font-mono uppercase bg-emerald-950/80 text-emerald-400 border border-emerald-800/80 px-1.5 py-0.5 rounded shadow-sm">
                  v{health?.version || '0.1.0'}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                Industrial Chemical Reactor Digital Twin
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden lg:flex items-center space-x-1.5">
            {navItems.map(item => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 flex items-center space-x-2 ${
                    isActive
                      ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-[0_0_12px_rgba(16,185,129,0.2)]'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Mobile / Compact Navigation Selector */}
          <div className="lg:hidden flex items-center">
            <select
              value={currentTab}
              onChange={e => onTabChange(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 px-2 py-1.5 font-medium"
            >
              {navItems.map(item => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          {/* Real-Time Health Badge */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 bg-slate-900/80 border border-slate-800/80 backdrop-blur-md px-3 py-1.5 rounded-lg text-xs shadow-inner">
              <span
                className={`w-2 h-2 rounded-full ${
                  isOnline ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse' : 'bg-rose-500'
                }`}
              />
              <span className="text-slate-300 font-mono text-[11px] flex items-center space-x-1">
                <Radio className="w-3 h-3 text-slate-500 inline mr-0.5" />
                <span>{isOnline ? 'Core Online' : 'Core Offline'}</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
