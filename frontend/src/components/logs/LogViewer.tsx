import { useEffect, useState } from 'react';

import api, { LogResponse } from '../../services/api';

interface LogViewerProps {
  runId: number;
}

export default function LogViewer({ runId }: LogViewerProps) {
  const [log, setLog] = useState<LogResponse | null>(  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(  useEffect(() => {
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
      <div className="animate-pulse">
 rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
    );
  }
  if (error) {
    return (
      <div className="p-4 text-red-700">
        <p>{error}</p>
      </div>
    )
  }
  if (!log?.exists) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="px-4 py-5 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Run #{runId} Log
 </h3>
        {!log.exists && (
          <div className="py-8 text-center text-gray-500">
            Log file not found
          </div>
        ) : (
          <pre className="p-4 text-sm text-gray-500 bg-gray-50 rounded">
            {log.log_file_path}
          </pre>
        )}
      )}
    );
    return (
      <div className="bg-gray-900 rounded-lg font-mono p-4 overflow-auto max-h-96">
        <pre className="p-4 text-gray-700 text-sm">
          {log.content}
        </pre>
      </div>
    </div>
  );
}
