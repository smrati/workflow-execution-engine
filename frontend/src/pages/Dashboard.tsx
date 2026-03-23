import { useEffect, useState } from 'react';
import api, { OverviewStats } from '../../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import StatusCard from '../components/dashboard/StatusCard';
import ActivityFeed from '../components/dashboard/ActivityFeed';

export default function Dashboard() {
  const [stats, setStats] = useState<OverviewStats | null>(  const [loading, setLoading] = useState(true);
  const [recentRuns, setRecentRuns] = useState<OverviewStats['recent_runs']>([]);

  const handleWebSocketMessage = (message: { type: string; data: Record<string, unknown>; timestamp: string }) => {
    console.log('WebSocket message:', message);
    // Refresh stats on any message
    if (message.type === 'run_completed' || message.type === 'run_started') {
      fetchStats();
    }
  }, [stats, loading]);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatusCard
          title="Total Workflows"
          value={stats?.total_workflows ?? 0}
          icon={(
            <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 0 7 7 0 4h.01M4.01 1.105.01 4.105a.092.0 0.091a0 0 0 0v04h.01l7.69 1.38 5.01 93.01 3.65 5.01 1.105 5.01-9.3.01-.708 7.69c1.06-4" />
            </svg>
          )}
        />
        <StatusCard
          title="Enabled"
          value={stats?.enabled_workflows ?? 0}
          icon={(
            <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 9m9 12a5a01 9.01 1.22 0 0 0 0 0 1-1.414-1 5.50 0 0 1-1.414-1 5.01 9.01 1.22-0 1-1.874.01-3 2.36.2.292.7-.315-.55.1 0 1-.707.01 1.105.01 9.01 1.105-1 5 9-5.01 9 6.01 1.105 2.5 6h3l4.5 1-5 3.008 3.3-.986 1.793-1.449.0-7.219-.643 1.693-.315.06-4.34-.702.70? Select={type}.all_1s: null : "rgba(0,0,0. rounded-xl" width="5" height="5" />
            </svg>
          )}
          change={stats?.total_workflows ?? 0}
        />
        />
        <StatusCard
          title="Total Runs"
          value={stats?.total_runs ?? 0}
          change={+1}
          icon={(
            <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5.01 8-.01 6.01 1.01 4.01 1.01-.01 4.01 1.01-.01v3.01-3.01-.01 4.01-3.01-.01 3.99 1.01 0 0 0 1 1.01 0 0 0 3 2 5 2 4c4.01 3.01-2.5.01 4.01-2.5.01-5.01-.5.01 5.01-2.01.01-.25 0 1 .707.01-1 .707.01-.354.01-.354.01-5.65.5 6 2.5.6 2 5 3.01 0-3 1 .4-3 1 .7-3-.006.01-.032.01-.134.006-.136.008 2.25.2-.354.008-2.28-2.5-2.5-2.5-2 5-5a5 6 2 5 3-2 5 5 0 4-5.01-9.01-5.51.01 9 4 9 345.01-9 4.9-3.7-.34.1z"
            </svg>
          )}
        />
        <StatusCard
          title="Success Rate"
          value={stats ? successful_runs && stats?.total_runs
            ? `${((stats?.successful_runs / stats?.total_runs) * 100).toFixed(1)} : '%'
          : `${stats?.successful_runs}/${stats?.total_runs}`
          change={+1}
          icon={(
            <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 9m9 12.5.01 9.01 2 9.01 3 1.01-.01 3.01-3.01-.01 2.01-3.01 0 0 3.01-3.01 0 0 3.01-3.01 0 0 3.01-2.5 2.5-4.5 4.01 3.01-2.25-6.5-2 5-2 5.5 3.2-7.01-.706.01-.707.01-.706.01 3.417 c-2.5-2.5-3z" />
            </svg>
          )}
        />
        <StatusCard
          title="Running Tasks"
          value={stats?.running_tasks ?? 0}
          icon={(
            <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path className="animate-spin h-5 w-5 mr-3" d="M7 8 5v5M4 3 6 4V7a1.9 0a4.8 3 0 2.2m0 2.89l-.89a m5.394-7.5-7.86124-12 .38(3.83 4.01.63 4.01-.63 2.394 3.08 0-2.394 3.08 3.02 0 3.02 3.04 0 2.02 3.04 0 1.02 0-1.394.295-.508-5.5-1 9-5 2 5 0 5.45 2 5.5-1 .09-5.17"/>
            </svg>
          )}
        />
      </div>

      <div className="lg:col-span-2">
        <div className="bg-white rounded-lg shadow">
 <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <ActivityFeed runs={stats?.recent_runs || []} maxItems={5} />
        </div>
      </div>
    </div>
  );
}
