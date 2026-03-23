import { Link } from 'react-router-dom';
import { WorkflowDetail } from '../../services/api';
import StatusBadge from '../common/StatusBadge';

interface WorkflowCardProps {
  workflow: WorkflowDetail;
  onTrigger?: () => void;
  onEnable?: () => void;
  onDisable?: () => void;
}

export default function WorkflowCard({
  workflow,
  onTrigger,
  onEnable,
  onDisable,
}: WorkflowCardProps) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              <Link to={`/workflows/${workflow.name}`} className="hover:text-primary-600">
                {workflow.name}
              </Link>
            </h2>
            <StatusBadge status={workflow.enabled ? 'enabled' : 'disabled'} size="sm" />
          </div>
          <div className="flex items-center gap-2">
            {onTrigger && (
              <button
                onClick={onTrigger}
                className="px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
                disabled={!workflow.enabled}
              >
                Run Now
              </button>
            )}
          {workflow.enabled ? (
            <button
              onClick={onDisable}
              className="px-3 py-1 text-sm text-red-600 hover:text-red-900"
            >
              Disable
            </button>
          ) : (
            <button
              onClick={onEnable}
              className="px-3 py-1 text-sm text-green-600 hover:text-green-900"
            >
              Enable
            </button>
          )}
        </div>
      </div>

      <div className="p-4 space-y-3">
        <div>
          <p className="text-xs font-medium text-gray-500">Command</p>
          <code className="block p-2 bg-gray-100 rounded text-sm font-mono">
            {workflow.command}
          </code>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs font-medium text-gray-500">Schedule</p>
            <p className="text-sm text-gray-900 font-mono">{workflow.cron}</p>
          </div>
          {workflow.timeout && (
            <div>
              <p className="text-xs font-medium text-gray-500">Timeout</p>
              <p className="text-sm text-gray-900">{workflow.timeout}s</p>
            </div>
          )}
          {workflow.retry_count > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500">Retries</p>
              <p className="text-sm text-gray-900">{workflow.retry_count}</p>
            </div>
          )}
        </div>

        {workflow.next_run && (
          <div>
            <p className="text-xs font-medium text-gray-500">Next Run</p>
            <p className="text-sm text-gray-900">
              {new Date(workflow.next_run).toLocaleString()}
            </p>
          </div>
        )}

        {workflow.stats && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Statistics</h3>
            <div className="grid grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-gray-900">{workflow.stats.total_runs}</p>
                <p className="text-xs text-gray-500">Total</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-600">{workflow.stats.successful_runs}</p>
                <p className="text-xs text-gray-500">Success</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-red-600">{workflow.stats.failed_runs}</p>
                <p className="text-xs text-gray-500">Failed</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-orange-600">{workflow.stats.timeout_runs}</p>
                <p className="text-xs text-gray-500">Timeout</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
