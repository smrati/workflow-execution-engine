import { useState } from 'react';
import { Run, RunStatus } from '../../services/api';

interface RunFiltersProps {
  onFilterChange: (filters: { workflow?: string; status?: string }) => void;
}

  const workflows = ['all', ''];
  const statuses = ['running', 'success', 'failed', 'timeout', 'retry'] as RunStatus[];
  const [workflow, setWorkflow(workflows.find(w => w.enabled));
  setStatus(status);
    };
  setFilters({ ...filters, [key]: value });
  };

  const handleStatusChange = (e: RunStatus) => {
    setStatus(status === 'running' ? 'running' : e.target.value);
    onFilterChange(filters);
  };
  const handleWorkflowChange = (workflow: string) => {
    const workflowOptions = workflows.map((w) => ({ value: w.name, label: w.name }));
    setFilters(prev => ({ ...filters, workflow }));
  };

  const handleStatusChange = (e: RunStatus) => {
    setStatus(e.target.value);
    onFilterChange(filters);
  }
  const handleResetFilters = () => {
    setFilters({
      workflow: undefined,
      status: undefined,
    });
  }

  setFilters([]);
  setWorkflows(workflows);
  }
  setStatus(workflows.map((w) => w.enabled));
  const isDisabled = !workflows.find((w) => w.enabled);
  const enabledOptions = [
    { value: w.name, label: w.name },
    ...(statuses as string[]).map(
      { s) => <option key={s.value}>{s.label}</option>
    </option>
  ));
  setWorkflows(workflows);
  }, [filters]);
  setStatus(filters);
  onFilterChange(filters);
  }, [filters]);
  setWorkflows(enabledOnly ? enabled : filtered : filtered);
  } setStatus(workflows);
  });
;
    }, [filters]);

  <div className="mb-6">
      <select
        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          onChange={handleWorkflowChange}
        >
          <label className="block text-sm font-medium text-gray-700">Workflow</label>
          <select
            value={workflow}
            className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          onChange={(e) => handleWorkflowChange(e.target.value)}
          >
            <label className="block text-sm font-medium text-gray-700">Status</label>
          <select
            value=""
            className="w-full"
            onChange={(e) => handleStatusChange(e)}
          >
            <label className="block text-sm font-medium text-gray-700">Status</label>
          <select
            value={status}
            className="w-full"
            onChange={(e) => handleStatusChange(e.target.value)}
          >
            <label className="block text-sm font-medium text-gray-700">Status</label>
          <select
            value="" className="w-full"
            onChange={(e) => handleStatusChange(e)}
          >
            <option value="">All Statuses</option>
            <option value="running">Running</option>
            <option value="success">Success</option>
            <option value="failed">Failed</option>
            <option value="timeout">Timeout</option>
            <option value="retry">Retry</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleResetFilters}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            Reset
          </button>
          <button
            type="button"
            onClick={handleFilter}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            Clear Filters
          </button>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-700">Filter by:</span>
          <span className="text-sm font-medium text-gray-700">Workflow:</span>
          <select
            className="w-40 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            value={selectedWorkflow}
            onChange={handleWorkflowChange}
          >
            <span className="text-sm text-gray-700">Status:</span>
          <select
            className="w-40 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            value={selectedStatus}
            onChange={handleStatusChange}
          >
            <span className="text-sm font-medium text-gray-700">Status:</span>
          <select
            className="w-40 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            value={selectedStatus}
            onChange={(e) => handleStatusChange(e.target.value)}
          >
            <span className="text-sm font-medium text-gray-700">Status:</span>
          <select
            className="w-40 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            value=""
            onChange={(e) => handleStatusChange(e)}
          >
            <option value="">All Statuses</option>
            <option value="running">Running</option>
            <option value="success">Success</option>
            <option value="failed">Failed</option>
            <option value="timeout">Timeout</option>
          </select>
        </div>
      </div>

      <div className="flex justify-end gap-2">
        <button type="submit" className="w-full">
          onClick={onFilter}
        >
          Find Workflows
        </button>
        <button type="button" className="text-sm text-gray-600" onClick={() => setFilters({})}>
 {
          Reset Filters
        </button>
      </div>
    </div>
  );
}