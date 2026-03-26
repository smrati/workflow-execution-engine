import { Link } from 'react-router-dom';
import { Run } from '../../services/api';
import StatusBadge from '../common/StatusBadge';
import { useTimezone } from '../../hooks/useTimezone';

interface ActivityFeedProps {
  runs: Run[];
  maxItems?: number;
}

export default function ActivityFeed({ runs, maxItems = 10 }: ActivityFeedProps) {
  const { formatDateTime } = useTimezone();
  const items = runs.slice(0, maxItems);

  return (
    <div className="space-y-3">
      {items.map((run) => (
        <Link
          key={run.id}
          to={`/runs/${run.id}`}
          className="block p-3 hover:bg-gray-50 rounded-lg transition-colors border border-gray-100"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-900">{run.workflow_name}</span>
            <StatusBadge status={run.status} size="sm" />
          </div>
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span className="font-mono truncate max-w-xs">
              {run.command.length > 50 ? `${run.command.slice(0, 50)}...` : run.command}
            </span>
            <div className="flex items-center gap-2">
              <span>{formatDateTime(run.start_time)}</span>
              {run.duration_seconds !== null && run.duration_seconds !== undefined && (
                <span className="text-gray-400">({run.duration_seconds.toFixed(2)}s)</span>
              )}
            </div>
          </div>
        </Link>
      ))}
      {items.length === 0 && (
        <p className="text-sm text-gray-500 text-center py-4">No recent activity</p>
      )}
    </div>
  );
}
