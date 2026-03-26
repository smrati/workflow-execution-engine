import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api, { Run, RunListResponse, Workflow } from '../../services/api';
import StatusBadge from '../common/StatusBadge';
import Pagination from '../common/Pagination';
import RunFilters from './RunFilters';
import CleanupRunsModal from './CleanupRunsModal';
import { useTimezone } from '../../hooks/useTimezone';
import { useAuth } from '../../hooks/useAuth';

export default function RunList() {
  const { formatDateTime } = useTimezone();
  const { isAdmin } = useAuth();
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [workflows, setWorkflows] = useState<string[]>([]);
  const [workflowObjects, setWorkflowObjects] = useState<Workflow[]>([]);
  const [filters, setFilters] = useState({
    workflow: '',
    status: '',
  });
  const [showCleanup, setShowCleanup] = useState(false);

  // Load workflows for filter dropdown
  useEffect(() => {
    const loadWorkflows = async () => {
      try {
        const data = await api.getWorkflows();
        setWorkflowObjects(data);
        setWorkflows(data.map((w: Workflow) => w.name));
      } catch (err) {
        console.error('Failed to load workflows:', err);
      }
    };
    loadWorkflows();
  }, []);

  // Load runs
  useEffect(() => {
    const loadRuns = async () => {
      setLoading(true);
      try {
        const data: RunListResponse = await api.getRuns({
          workflow_name: filters.workflow || undefined,
          status: filters.status || undefined,
          page: currentPage,
          page_size: 20,
        });
        setRuns(data.runs);
        setTotalPages(data.total_pages);
      } catch (err) {
        console.error('Failed to load runs:', err);
      } finally {
        setLoading(false);
      }
    };
    loadRuns();
  }, [filters, currentPage]);

  const handleWorkflowChange = (workflow: string) => {
    setFilters((prev) => ({ ...prev, workflow }));
    setCurrentPage(1);
  };

  const handleStatusChange = (status: string) => {
    setFilters((prev) => ({ ...prev, status }));
    setCurrentPage(1);
  };

  const handleReset = () => {
    setFilters({ workflow: '', status: '' });
    setCurrentPage(1);
  };

  const handleDeleted = () => {
    setShowCleanup(false);
    setCurrentPage(1);
    const loadRuns = async () => {
      setLoading(true);
      try {
        const data: RunListResponse = await api.getRuns({
          workflow_name: filters.workflow || undefined,
          status: filters.status || undefined,
          page: 1,
          page_size: 20,
        });
        setRuns(data.runs);
        setTotalPages(data.total_pages);
      } catch (err) {
        console.error('Failed to load runs:', err);
      } finally {
        setLoading(false);
      }
    };
    loadRuns();
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Run History</h1>
        {isAdmin && (
          <button
            onClick={() => setShowCleanup(true)}
            className="px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700"
          >
            Cleanup Runs
          </button>
        )}
      </div>

      <RunFilters
        workflows={workflows}
        selectedWorkflow={filters.workflow}
        selectedStatus={filters.status}
        onWorkflowChange={handleWorkflowChange}
        onStatusChange={handleStatusChange}
        onReset={handleReset}
      />

      {runs.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
          No runs found
        </div>
      ) : (
        <>
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Workflow
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Command
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Started
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Triggered By
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {runs.map((run) => (
                  <tr key={run.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        to={`/runs/${run.id}`}
                        className="text-primary-600 hover:text-primary-900"
                      >
                        #{run.id}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        to={`/workflows/${run.workflow_name}`}
                        className="text-gray-900 hover:text-gray-600"
                      >
                        {run.workflow_name}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <code className="text-sm text-gray-600 bg-gray-50 px-2 py-1 rounded">
                        {run.command.length > 40 ? `${run.command.slice(0, 40)}...` : run.command}
                      </code>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={run.status} size="sm" />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDateTime(run.start_time)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {run.duration_seconds !== null && run.duration_seconds !== undefined
                        ? `${run.duration_seconds.toFixed(2)}s`
                        : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {run.triggered_by || <span className="text-gray-400">cron</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4">
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
            />
          </div>
        </>
      )}
      <CleanupRunsModal
        isOpen={showCleanup}
        onClose={() => setShowCleanup(false)}
        onDeleted={handleDeleted}
        workflows={workflowObjects}
      />
    </div>
  );
}
