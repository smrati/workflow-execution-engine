import { useEffect, useState } from 'react';
import api, { LogResponse } from '../../services/api';

interface LogViewerProps {
  runId: number;
}

export default function LogViewer({ runId }: LogViewerProps) {
  const [log, setLog] = useState<LogResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLog = async () => {
      try {
        setLoading(true);
        const data = await api.getRunLog(runId);
        setLog(data);
        setError(null);
      } catch (err) {
        setError('Failed to load log');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchLog();
  }, [runId]);

  if (loading) {
    return (
      <div className="text-center py-4">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-500 mx-auto"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-red-600 bg-red-50 rounded">
        {error}
      </div>
    );
  }

  if (!log) {
    return (
      <div className="p-4 text-gray-500">
        No log data available
      </div>
    );
  }

  if (!log.exists) {
    return (
      <div className="p-4 text-gray-500 bg-gray-50 rounded">
        <p>Log file not found</p>
        {log.log_file_path && (
          <p className="text-xs mt-1 text-gray-400">{log.log_file_path}</p>
        )}
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg p-4 overflow-auto max-h-96">
      <pre className="text-sm text-gray-100 font-mono whitespace-pre-wrap">
        {log.content || 'No output'}
      </pre>
    </div>
  );
}
