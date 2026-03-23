import { useEffect, useState } from 'react';
import api, { Workflow } from '../services/api';
import WorkflowList from '../components/workflows/WorkflowList';

export default function Workflows() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadWorkflows = async () => {
      try {
        const data = await api.getWorkflows();
        setWorkflows(data);
      } catch (err) {
        setError('Failed to load workflows');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadWorkflows();
  }, []);

  const handleTrigger = async (name: string) => {
    try {
      await api.triggerWorkflow(name);
    } catch (err) {
      console.error('Failed to trigger workflow:', err);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-600">
        {error}
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Workflows</h1>
        <p className="text-sm text-gray-500">
          {workflows.length} workflow{workflows.length !== 1 ? 's' : ''}
        </p>
      </div>

      <WorkflowList workflows={workflows} onTrigger={handleTrigger} />
    </div>
  );
}
