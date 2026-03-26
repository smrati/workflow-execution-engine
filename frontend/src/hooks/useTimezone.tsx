import { createContext, useContext, useState, ReactNode } from 'react';

const TIMEZONE_KEY = 'selected_timezone';

export const TIMEZONES = [
  { value: 'UTC', label: 'UTC' },
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'Europe/London', label: 'London (GMT/BST)' },
  { value: 'Europe/Paris', label: 'Paris (CET)' },
  { value: 'Europe/Berlin', label: 'Berlin (CET)' },
  { value: 'Asia/Kolkata', label: 'India (IST)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
  { value: 'Asia/Shanghai', label: 'Shanghai (CST)' },
  { value: 'Australia/Sydney', label: 'Sydney (AEST)' },
];

interface TimezoneContextType {
  timezone: string;
  setTimezone: (tz: string) => void;
  formatDateTime: (date: string | Date | null | undefined) => string;
}

const TimezoneContext = createContext<TimezoneContextType | null>(null);

export function TimezoneProvider({ children }: { children: ReactNode }) {
  const [timezone, setTimezoneState] = useState<string>(() => {
    const saved = localStorage.getItem(TIMEZONE_KEY);
    return saved || 'UTC';
  });

  const setTimezone = (tz: string) => {
    setTimezoneState(tz);
    localStorage.setItem(TIMEZONE_KEY, tz);
  };

  const formatDateTime = (date: string | Date | null | undefined): string => {
    if (!date) return '-';
    
    const d = typeof date === 'string' ? new Date(date) : date;
    if (isNaN(d.getTime())) return '-';
    
    try {
      return d.toLocaleString('en-US', {
        timeZone: timezone,
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return d.toLocaleString();
    }
  };

  return (
    <TimezoneContext.Provider value={{ timezone, setTimezone, formatDateTime }}>
      {children}
    </TimezoneContext.Provider>
  );
}

export function useTimezone() {
  const context = useContext(TimezoneContext);
  if (!context) {
    throw new Error('useTimezone must be used within a TimezoneProvider');
  }
  return context;
}
