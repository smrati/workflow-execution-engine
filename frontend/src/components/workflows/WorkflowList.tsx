import { Link } from 'react-router-dom';
import { Workflow } from '../../services/api';
import StatusBadge from '../common/StatusBadge';

interface WorkflowListProps {
  workflows: Workflow[];
}

export default function WorkflowList({ workflows }: WorkflowListProps) {
  return (
    <div className="bg-white rounded-lg shadow">
 overflow-hidden">
      <table className="min-w-full divide-y">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Name
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Command
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Schedule
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Next Run
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y">
          {workflows.map((workflow) => (
            <tr key={workflow.name} className="hover:bg-gray-50">
              <td className="px-4 py-3">
                <Link
                  to={`/workflows/${workflow.name}`}
                  className="text-primary-600 hover:text-primary-900 font-medium"
                >
                  {workflow.name}
                </Link>
              </td>
              <td className="px-4 py-3">
                <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">
                  {workflow.command.length > 50 ? `${workflow.command.slice(0, 50)}...` : workflow.command}
                </code>
              </td>
              <td className="px-4 py-3">
                <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">
                  {workflow.cron}
                </code>
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={workflow.enabled ? 'enabled' : 'disabled'} size="sm" />
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {workflow.next_run
                  ? new Date(workflow.next_run).toLocaleString()
                  : 'Not scheduled'}
                </td>
              <td className="px-4 py-3 text-right">
                <button
                  onClick={() => {}}
                  className="text-primary-600 hover:text-primary-900"
                >
                  Trigger
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
