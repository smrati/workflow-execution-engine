import { ReactNode } from 'react';

interface StatusCardProps {
  title: string;
  value: number | string;
  icon: ReactNode;
  change?: number;
}

export default function StatusCard({ title, value, icon, change }: StatusCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex-shrink-0 text-gray-400">
            {icon}
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">{title}</p>
            <p className="text-2xl font-semibold text-gray-900">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </p>
          </div>
        </div>
        {change !== undefined && (
          <div className={`text-sm ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {change >= 0 ? '+' : ''}{change}
          </div>
        )}
      </div>
    </div>
  );
}
