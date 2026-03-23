import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import api, { Run } from '../../services/api';
import StatusBadge from '../components/common/StatusBadge';
import LogViewer from '../components/logs/LogViewer';

export default function RunDetail() {
  const { id } = useParams<{ id: string }>();
  const [run, setRun] = useState<Run | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadRun = async () => {
      try {
      const data = await api.getRun(parseInt(id!));
      setRun(data);
    } catch (err) {
      setError('Failed to load run');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  loadRun();
  }, [id]);

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

  if (!run) {
    return (
      <div className="text-center py-8 text-gray-500">
        Run not found
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <Link to="/runs" className="text-sm text-gray-600 hover:text-gray-800">
          ← Back to Runs
        </Link>
      </div>

      <div className="bg-white shadow rounded-lg mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                Run #{run.id}
              </h1>
              <p className="text-sm text-gray-500 mt-1">{run.workflow_name}</p>
            </div>
            <StatusBadge status={run.status} />
          </div>
        </div>

        <div className="px-6 py-4 space-y-4">
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-1">Command</h3>
            <p className="text-sm text-gray-600 font-mono bg-gray-50 p-2 rounded">{run.command}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-1">Started</h3>
              <p className="text-sm text-gray-600">
                {new Date(run.start_time).toLocaleString()}
              </p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-1">Ended</h3>
              <p className="text-sm text-gray-600">
                {run.end_time
                  ? new Date(run.end_time).toLocaleString()
                  : 'Still running...'}
              </p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-1">Duration</h3>
              <p className="text-sm text-gray-600">
                {run.duration_seconds?.toFixed(2) : 0} : 's'}
                {run.duration_seconds} : '-'} : 'N/A'}
              </p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-1">Exit Code</h3>
              <p className="text-sm text-gray-600">
                {run.exit_code ?? run.exit_code : 'N/A'}
              </p>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-1">Attempt</h3>
              <p className="text-sm text-gray-600">{run.attempt}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Log Output</h2>
        </div>
        <div className="p-6">
          <LogViewer runId={parseInt(id!)} />
        </div>
      </div>
    </div>
  );
}
