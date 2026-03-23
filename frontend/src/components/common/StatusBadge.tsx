interface StatusBadgeProps {
  status: 'running' | 'success' | 'failed' | 'timeout' | 'retry' | 'enabled' | 'disabled';
  size?: 'sm' | 'md';
}

const statusConfig = {
  running: {
    label: 'Running',
    className: 'bg-blue-100 text-blue-800',
    dotClassName: 'bg-blue-500 animate-pulse',
  },
  success: {
    label: 'Success',
    className: 'bg-green-100 text-green-800',
    dotClassName: 'bg-green-500',
  },
  failed: {
    label: 'Failed',
    className: 'bg-red-100 text-red-800',
    dotClassName: 'bg-red-500',
  },
  timeout: {
    label: 'Timeout',
    className: 'bg-orange-100 text-orange-800',
    dotClassName: 'bg-orange-500',
  },
  retry: {
    label: 'Retry',
    className: 'bg-yellow-100 text-yellow-800',
    dotClassName: 'bg-yellow-500',
  },
  enabled: {
    label: 'Enabled',
    className: 'bg-green-100 text-green-800',
    dotClassName: 'bg-green-500',
  },
  disabled: {
    label: 'Disabled',
    className: 'bg-gray-100 text-gray-800',
    dotClassName: 'bg-gray-500',
  },
};

export default function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const config = statusConfig[status];
  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${sizeClasses} ${config.className}`}
    >
      <span className={`w-2 h-2 rounded-full ${config.dotClassName}`} />
      {config.label}
    </span>
  );
}
