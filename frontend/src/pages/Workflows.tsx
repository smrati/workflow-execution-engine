import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { Workflow } from '../../services/api';
import StatusBadge from '../components/common/StatusBadge';

export default function Workflows() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(  useEffect(() => {
    const loadWorkflows = async () => {
      try {
        const data = await api.getWorkflows();
        setWorkflows(data);
      } catch (err) {
        setError('Failed to load workflows');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadWorkflows();
  }, []);

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

  return (
    <div>
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold text-gray-900">Workflows</h1>
        </div>

        <div className="bg-white shadow overflow-hidden rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Schedule
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Next Run
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {workflows.map((workflow) => (
                <tr key={workflow.name} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      to={`/workflows/${workflow.name}`}
                      className="text-primary-600 hover:text-primary-900 font-medium"
                    >
                      {workflow.name}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <code className="text-sm text-gray-600">{workflow.cron}</code>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={workflow.enabled ? 'enabled' : 'disabled'} size="sm" />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {workflow.next_run
                      ? new Date(workflow.next_run).toLocaleString()
                      : 'Not scheduled'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => api.triggerWorkflow(workflow.name)}
                      disabled={!workflow.enabled}
                      className="text-primary-600 hover:text-primary-900 disabled:opacity-50 disabled:cursor-not-allowed mr-3"
                    >
                      Run Now
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
