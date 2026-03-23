import { useEffect, useState, useCallback } from 'react';
import api, { OverviewStats } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import StatusCard from '../components/dashboard/StatusCard';
import ActivityFeed from '../components/dashboard/ActivityFeed';

export default function Dashboard() {
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = useCallback(async () => {
    try {
      const data = await api.getOverviewStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const handleWebSocketMessage = useCallback((message: { type: string; data: Record<string, unknown> }) => {
    if (message.type === 'run_completed' || message.type === 'run_started') {
      fetchStats();
    }
  }, [fetchStats]);

  useWebSocket(handleWebSocketMessage);

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
      </div>
    );
  }

  const successRate = stats && stats.total_runs > 0
    ? ((stats.successful_runs / stats.total_runs) * 100).toFixed(1)
    : '0';

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatusCard
          title="Total Workflows"
          value={stats?.total_workflows ?? 0}
          icon="workflow"
        />
        <StatusCard
          title="Enabled"
          value={stats?.enabled_workflows ?? 0}
          icon="check"
        />
        <StatusCard
          title="Total Runs"
          value={stats?.total_runs ?? 0}
          icon="clock"
        />
        <StatusCard
          title="Success Rate"
          value={`${successRate}%`}
          icon="chart"
        />
      </div>

      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <ActivityFeed runs={stats?.recent_runs || []} maxItems={10} />
        </div>
      </div>
    </div>
  );
}
