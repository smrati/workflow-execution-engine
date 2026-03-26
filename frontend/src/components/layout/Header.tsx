import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useTimezone, TIMEZONES } from '../../hooks/useTimezone';

export default function Header() {
  const { user, logout, isAdmin } = useAuth();
  const { timezone, setTimezone } = useTimezone();

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-50">
      <div className="flex items-center justify-between h-full px-6">
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2">
            <svg
              className="w-8 h-8 text-primary-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            <span className="text-xl font-semibold text-gray-900">Workflow Engine</span>
          </Link>
        </div>
        <div className="flex items-center gap-4">
          <a
            href="/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            API Docs
          </a>
          {isAdmin && (
            <Link
              to="/admin/users"
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              User Management
            </Link>
          )}
          <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
            <select
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="text-xs text-gray-600 bg-gray-50 border border-gray-200 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-primary-500"
            >
              {TIMEZONES.map((tz) => (
                <option key={tz.value} value={tz.value}>
                  {tz.label}
                </option>
              ))}
            </select>
            <div className="flex flex-col items-end">
              <span className="text-sm text-gray-900 font-medium">
                {user?.username}
              </span>
              <span className="text-xs text-gray-500 capitalize">
                {user?.role}
              </span>
            </div>
            <button
              onClick={logout}
              className="text-sm text-red-600 hover:text-red-700 font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
