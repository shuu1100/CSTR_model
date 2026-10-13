import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { HealthResponse } from '../api/types';

interface SidebarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onTabChange }) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await api.getHealth();
        setHealth(res);
        setIsOnline(true);
      } catch {
        setIsOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'overview', label: 'Overview', icon: 'grid_view' },
    { id: 'steady-state', label: 'Steady-State Simulator', icon: 'balance' },
    { id: 'dynamic', label: 'Dynamic Simulation', icon: 'timeline' },
    { id: 'thermal', label: 'Thermal CSTR', icon: 'device_thermostat' },
    { id: 'sweeps', label: 'Parameter Sweeps', icon: 'tune' },
    { id: 'experiments', label: 'Data & Experiments', icon: 'experiment' },
    { id: 'estimation', label: 'Parameter Estimation', icon: 'query_stats' },
    { id: 'ml', label: 'Machine Learning', icon: 'hub' },
    { id: 'history', label: 'Run History', icon: 'history' },
    { id: 'reports', label: 'Reports & Exports', icon: 'description' },
    { id: 'status', label: 'System Status', icon: 'monitor_heart' },
  ];

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-[#E4EDF6] border-r border-[#CBD9E8] z-50 flex flex-col justify-between select-none shadow-sm">
      <div className="flex flex-col">
        {/* Brand Header */}
        <div className="h-14 px-4 border-b border-[#CBD9E8] flex items-center justify-between bg-[#DAE8F4]">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded border border-[#CBD9E8] flex items-center justify-center bg-white shadow-2xs">
              <span className="material-symbols-outlined text-primary text-[18px]">science</span>
            </div>
            <div>
              <span className="font-semibold text-xs text-[#0F1E2E] tracking-tight block">CSTR Lab</span>
              <span className="font-mono text-[10px] text-[#4E657E] block leading-none">v2.4-SciML</span>
            </div>
          </div>
          <span className="px-1.5 py-0.5 rounded font-bold text-[10px] bg-white text-primary border border-[#CBD9E8] uppercase shadow-2xs tracking-wider">
            PROD
          </span>
        </div>

        {/* Navigation Items */}
        <nav className="py-2 flex flex-col gap-0.5 px-1.5">
          {navItems.map((item) => {
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`flex items-center gap-2.5 px-3 py-1.5 rounded transition-all text-left text-xs ${
                  isActive
                    ? 'bg-white text-primary border-l-[3px] border-primary font-semibold shadow-2xs'
                    : 'text-[#4E657E] hover:bg-white/70 hover:text-[#0F1E2E]'
                }`}
              >
                <span className={`material-symbols-outlined text-[18px] ${isActive ? 'text-primary' : 'text-[#4E657E]'}`}>
                  {item.icon}
                </span>
                <span className="truncate">{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Telemetry & Daemon Status Box */}
      <div className="p-3 border-t border-[#CBD9E8] bg-[#DAE8F4] font-mono text-[11px] space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-[#4E657E]">DAEMON</span>
          <div className="flex items-center gap-1.5">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isOnline ? 'bg-status-success animate-pulse' : 'bg-status-critical'
              }`}
            />
            <span className="text-[#0F1E2E] font-medium">
              {isOnline ? `${health?.status || 'ONLINE'} :8001` : 'OFFLINE'}
            </span>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[#4E657E]">LOCAL DB</span>
          <span className="text-secondary font-semibold">SYNCED (SQLite)</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-[#4E657E]">SOLVER</span>
          <span className="text-tertiary font-semibold truncate max-w-[110px]">RK45 / Grey-Box</span>
        </div>
      </div>
    </aside>
  );
};
