interface RunFiltersProps {
  workflows: string[];
  selectedWorkflow: string;
  selectedStatus: string;
  onWorkflowChange: (workflow: string) => void;
  onStatusChange: (status: string) => void;
  onReset: () => void;
}

export default function RunFilters({
  workflows,
  selectedWorkflow,
  selectedStatus,
  onWorkflowChange,
  onStatusChange,
  onReset,
}: RunFiltersProps) {
  const statuses = ['running', 'success', 'failed', 'timeout', 'retry'];

  return (
    <div className="bg-white p-4 rounded-lg shadow mb-6">
      <div className="flex flex-wrap items-end gap-4">
        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Workflow
          </label>
          <select
            value={selectedWorkflow}
            onChange={(e) => onWorkflowChange(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Workflows</option>
            {workflows.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1 min-w-[200px]">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            value={selectedStatus}
            onChange={(e) => onStatusChange(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="">All Statuses</option>
            {statuses.map((status) => (
              <option key={status} value={status}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <button
            onClick={onReset}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Reset Filters
          </button>
        </div>
      </div>
    </div>
  );
}
