import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import type { WorkflowDetail as WorkflowDetailType } from '../services/api';
import StatusBadge from '../components/common/StatusBadge';
import { useAuth } from '../hooks/useAuth';

export default function WorkflowDetail() {
  const { name } = useParams<{ name: string }>();
  const { isViewer } = useAuth();
  const [workflow, setWorkflow] = useState<WorkflowDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);

  useEffect(() => {
    const loadWorkflow = async () => {
      try {
        const data = await api.getWorkflow(name!);
        setWorkflow(data);
      } catch (err) {
        setError('Failed to load workflow');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadWorkflow();
  }, [name]);

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      await api.triggerWorkflow(name!);
      // Refresh workflow data
      const data = await api.getWorkflow(name!);
      setWorkflow(data);
    } catch (err) {
      console.error('Failed to trigger workflow:', err);
    } finally {
      setTriggering(false);
    }
  };

  const handleToggleEnabled = async () => {
    try {
      if (workflow?.enabled) {
        await api.disableWorkflow(name!);
      } else {
        await api.enableWorkflow(name!);
      }
      // Refresh workflow data
      const data = await api.getWorkflow(name!);
      setWorkflow(data);
    } catch (err) {
      console.error('Failed to toggle workflow:', err);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-600">
        {error}
      </div>
    );
  }

  if (!workflow) {
    return (
      <div className="text-center py-8 text-gray-500">
        Workflow not found
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <Link to="/workflows" className="text-sm text-gray-600 hover:text-gray-800">
          ← Back to Workflows
        </Link>
      </div>

      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">{workflow.name}</h1>
              <p className="text-sm text-gray-500 mt-1">{workflow.cron}</p>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge status={workflow.enabled ? 'enabled' : 'disabled'} />
              {!isViewer && (
                <>
                  <button
                    onClick={handleTrigger}
                    disabled={triggering || !workflow.enabled}
                    className="ml-2 px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {triggering ? 'Running...' : 'Run Now'}
                  </button>
                  <button
                    onClick={handleToggleEnabled}
                    className={`ml-2 px-3 py-1 text-sm rounded ${
                      workflow.enabled
                        ? 'bg-red-100 text-red-700 hover:bg-red-200'
                        : 'bg-green-100 text-green-700 hover:bg-green-200'
                    }`}
                  >
                    {workflow.enabled ? 'Disable' : 'Enable'}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="px-6 py-4 space-y-4">
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-2">Command</h3>
            <p className="text-sm text-gray-600 font-mono bg-gray-50 p-2 rounded">{workflow.command}</p>
          </div>

          {workflow.timeout && (
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-1">Timeout</h3>
              <p className="text-sm text-gray-600">{workflow.timeout} seconds</p>
            </div>
          )}

          {workflow.retry_count > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-1">Retries</h3>
              <p className="text-sm text-gray-600">{workflow.retry_count} (delay: {workflow.retry_delay}s)</p>
            </div>
          )}

          {workflow.working_dir && (
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-1">Working Directory</h3>
              <p className="text-sm text-gray-600">{workflow.working_dir}</p>
            </div>
          )}
        </div>

        {workflow.stats && (
          <div className="px-6 py-4 border-t border-gray-200">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Statistics</h3>
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-2xl font-bold text-gray-900">{workflow.stats.total_runs}</p>
                <p className="text-xs text-gray-500">Total Runs</p>
              </div>
              <div className="bg-green-50 p-3 rounded">
                <p className="text-2xl font-bold text-green-700">{workflow.stats.successful_runs}</p>
                <p className="text-xs text-gray-500">Successful</p>
              </div>
              <div className="bg-red-50 p-3 rounded">
                <p className="text-2xl font-bold text-red-700">{workflow.stats.failed_runs}</p>
                <p className="text-xs text-gray-500">Failed</p>
              </div>
              <div className="bg-orange-50 p-3 rounded">
                <p className="text-2xl font-bold text-orange-700">{workflow.stats.timeout_runs}</p>
                <p className="text-xs text-gray-500">Timeouts</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
