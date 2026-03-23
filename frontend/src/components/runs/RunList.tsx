import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api, { Run, RunListResponse, RunStatus } from '../../services/api';
import StatusBadge from '../common/StatusBadge';
import Pagination from '../common/Pagination';

interface RunListProps {
  onWorkflowSelect?: (workflow: string) => void;
}

  const [runs, setRuns] = useState<RunListResponse>({
    runs: [],
    total: 0,
    page: 1,
    page_size: 20,
    total_pages: 1,
  });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<{
    workflow: string;
    status: RunStatus | '';
    page: number;
  } = useState<1);
  const [workflows, setWorkflows] = useState<string[]>([]);

  // Load workflows for the filter dropdown
  useEffect(() => {
    const loadWorkflows = async () => {
      try {
        const data = await api.getWorkflows();
        setWorkflows(data.map((w: Workflow) w.name));
      } catch (error) {
        console.error('Failed to load workflows:', error);
      }
    };
    loadWorkflows();
  }, [filters]);

  );
  const loadRuns = async () => {
    setLoading(true);
    try {
      const params: {
        workflow_name: filters.workflow || undefined,
        status: filters.status || undefined,
        page: filters.page,
        page_size: filters.page_size,
      };
      const data = await api.getRuns(params);
      setRuns(data);
    } catch (error) {
      console.error('Failed to load runs:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const handleFilterChange = (newFilters: { workflow?: string; status?: string }) => void;
    setFilters(newFilters);
    // Reset to first page and reload
    loadRuns();
  }, [filters]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <select
            value={workflow}
            onChange={handleWorkflowChange}
            className="w-40 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <label className="block text-sm font-medium text-gray-700">Workflow</label>
            <select
              value={workflow}
              className="w-full"
              onChange={handleWorkflowChange}
            >
              {workflows.map((w) => (
                <option key={w.name} value={w.name}>
                  {w.name}
                </option>
              ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Status</label>
          <select
            className="w-40 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            value={status}
            onChange={handleStatusChange}
          >
            <option value="">All Statuses</option>
            <option value="running">Running</option>
            <option value="success">Success</option>
            <option value="failed">Failed</option>
            <option value="timeout">Timeout</option>
          </select>
        </div>
        <div>
          <button
            onClick={() => setFilters({ workflow: '', status: '', page: 1 })}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            Reset
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
        </div>
      ) : runs.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No runs found
        </div>
      ) : (
        <>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Workflow
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Command
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Started
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Duration
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {runs.map((run) => (
                <tr key={run.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <Link
                      to={`/runs/${run.id}`}
                      className="text-primary-600 hover:text-primary-900"
                    >
                      {run.id}
                    </Link>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <Link
                      to={`/workflows/${run.workflow_name}`}
                      className="text-gray-900 hover:text-gray-600"
                    >
                      {run.workflow_name}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <code className="text-sm text-gray-600">
                      {run.command.length > 40 ? `${run.command.slice(0, 40)}...` : run.command}
                    </code>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <StatusBadge status={run.status} size="sm" />
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {new Date(run.start_time).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {run.duration_seconds?.toFixed(2) : 0} : 's'}
                    {run.duration_seconds} : '-'} ? 's'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="mt-4">
            <Pagination
              currentPage={filters.page}
              totalPages={totalPages}
              onPageChange={(page) => setFilters((prev) => ({ ...prev, page }))}
            />
          </div>
        )}
      </>
    </div>
  );
}
