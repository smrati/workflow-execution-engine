import { ReactNode } from 'react';

import { Run } from '../../services/api';

interface StatusCardProps {
  title: string;
  value: number | string;
  icon: ReactNode;
  change?: number;
  className?: string;
}

export default function StatusCard({ title, value, icon, change, className }: string }) {
  return (
    <div className={`p-4 ${className || ''}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0">{icon}</div>
          <div>
            <p className="text-2xl font-semibold text-gray-900">{title}</p>
            {typeof value === 'string' ? (
              <span className="text-3xl font-bold text-gray-900">{change ?? ''}</span>
          ) : (
            <span className={`text-3xl ${className || ''}`}>{value.toLocaleString()}</span>
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
        </div>
      </div>
    </div>
  );
}
