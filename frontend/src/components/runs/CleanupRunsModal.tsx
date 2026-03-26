import { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useToast } from '../../hooks/useToast';
import api, { DeleteRunsResponse, Workflow } from '../../services/api';

interface CleanupRunsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDeleted: () => void;
  workflows: Workflow[];
}

export default function CleanupRunsModal({ isOpen, onClose, onDeleted, workflows }: CleanupRunsModalProps) {
  const { isAdmin } = useAuth();
  const { showToast } = useToast();
  const [filterType, setFilterType] = useState<'before' | 'after' | 'between'>('before');
  const [before, setBefore] = useState('');
  const [after, setAfter] = useState('');
  const [workflowName, setWorkflowName] = useState('');
  const [confirmText, setConfirmText] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [result, setResult] = useState<DeleteRunsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleDelete = async () => {
    setError(null);
    setResult(null);

    const beforeVal = (filterType === 'before' || filterType === 'between') ? before : undefined;
    const afterVal = (filterType === 'after' || filterType === 'between') ? after : undefined;

    if (!beforeVal && !afterVal) {
      setError('Please select a date range');
      return;
    }

    setDeleting(true);
    try {
      const res = await api.deleteRuns({
        before: beforeVal,
        after: afterVal,
        workflow_name: workflowName || undefined,
      });
      setResult(res);
      onDeleted();
      showToast(
        `Deleted ${res.deleted_count} run(s) and ${res.deleted_log_files} log file(s)`,
        res.deleted_count > 0 ? 'success' : 'info'
      );
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to delete runs');
    } finally {
      setDeleting(false);
    }
  };

  const handleClose = () => {
    setResult(null);
    setError(null);
    setConfirmText('');
    setBefore('');
    setAfter('');
    setWorkflowName('');
    setFilterType('before');
    onClose();
  };

  const getConfirmPlaceholder = () => {
    if (filterType === 'before') return 'Type "delete" to confirm';
    if (filterType === 'after') return 'Type "delete" to confirm';
    return 'Type "delete" to confirm';
  };

  const isConfirmEnabled = confirmText.toLowerCase() === 'delete';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={handleClose} />
      <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Cleanup Run Logs</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {!isAdmin ? (
          <div className="text-sm text-red-600 bg-red-50 p-3 rounded">
            Admin access required to delete runs.
          </div>
        ) : result ? (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-green-800 mb-2">Deletion Complete</h3>
              <div className="space-y-1 text-sm text-green-700">
                <p>Runs deleted: <span className="font-semibold">{result.deleted_count}</span></p>
                <p>Log files deleted: <span className="font-semibold">{result.deleted_log_files}</span></p>
              </div>
            </div>
            {result.errors.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="text-sm font-medium text-yellow-800 mb-2">Warnings</h3>
                <ul className="text-sm text-yellow-700 space-y-1">
                  {result.errors.map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ul>
              </div>
            )}
            <button
              onClick={handleClose}
              className="w-full px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Close
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Filter Type</label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value as any)}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                <option value="before">Before a date/time</option>
                <option value="after">After a date/time</option>
                <option value="between">Between two dates/times</option>
              </select>
            </div>

            {(filterType === 'before' || filterType === 'between') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Before (runs started before this time will be deleted)
                </label>
                <input
                  type="datetime-local"
                  value={before}
                  onChange={(e) => setBefore(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
            )}

            {(filterType === 'after' || filterType === 'between') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  After (runs started after this time will be deleted)
                </label>
                <input
                  type="datetime-local"
                  value={after}
                  onChange={(e) => setAfter(e.target.value)}
                  className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Workflow (optional, leave empty for all)
              </label>
              <select
                value={workflowName}
                onChange={(e) => setWorkflowName(e.target.value)}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                <option value="">All Workflows</option>
                {workflows.map((w) => (
                  <option key={w.name} value={w.name}>{w.name}</option>
                ))}
              </select>
            </div>

            <div className="bg-red-50 border border-red-200 rounded p-3">
              <p className="text-sm text-red-700">
                This will permanently delete run records and their log files. This action cannot be undone.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type <span className="font-mono font-semibold">delete</span> to confirm
              </label>
              <input
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder={getConfirmPlaceholder()}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>

            {error && (
              <div className="text-sm text-red-600 bg-red-50 p-3 rounded">{error}</div>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleClose}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50 text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={!isConfirmEnabled || deleting}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                {deleting ? 'Deleting...' : 'Delete Runs'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
