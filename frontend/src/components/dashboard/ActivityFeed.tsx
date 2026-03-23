import { Link } from 'react-router-dom';
import { Run } from '../../services/api';
import StatusBadge from '../common/StatusBadge';

interface ActivityFeedProps {
  runs: Run[];
  maxItems?: number;
}

export default function ActivityFeed({ runs, maxItems = 10 }: ActivityFeedProps) {
  const items = runs.slice(0, maxItems);

  return (
    <div className="space-y-3">
      {items.map((run) => (
        <Link
          key={run.id}
          to={`/runs/${run.id}`}
          className="block p-3 hover:bg-gray-50 rounded-lg transition-colors"
        >
          <div className="flex items-center justify-between">
            <StatusBadge status={run.status} size="sm" />
            <div>
              <p className="text-sm font-medium text-gray-900">
                {run.workflow_name}
              </p>
              <p className="text-xs text-gray-500">
                {run.command.length > 50 ? `${run.command.slice(0, 50)}...` : run.command}
              </p>
              <div className="text-xs text-gray-500">
                {new Date(run.start_time).toLocaleString()}
              </p>
              {run.duration_seconds && (
                <span className="text-xs text-gray-400">
                  {run.duration_seconds.toFixed(2)}s
                </span>
              )}
            </p>
          ))}
        </Link>
      ))}
      {items.length === 0 && (
        <p className="text-sm text-gray-500 text-center py-2">No recent activity</p>
      )}
    </div>
  );
}
