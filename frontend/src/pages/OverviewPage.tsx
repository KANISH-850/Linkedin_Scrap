import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  Users2,
  Send,
  Clock,
  ArrowUpRight,
  TrendingUp,
  BookOpen,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import { api } from '../services/api';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

export function OverviewPage() {
  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ['dashboardSummary'],
    queryFn: api.getSummary,
  });

  const { data: analytics, isLoading: loadingAnalytics } = useQuery({
    queryKey: ['dashboardAnalytics'],
    queryFn: api.getAnalytics,
  });

  if (loadingSummary || loadingAnalytics) {
    return <div className="text-center py-20 text-slate-400">Loading dashboard metrics...</div>;
  }

  const statCards = [
    { label: 'Active Vacancies', value: summary?.active_vacancies ?? summary?.new_opportunities ?? 0, icon: Sparkles, color: 'text-indigo-500' },
    { label: 'High-Match (>=75)', value: summary?.high_match_opportunities ?? 0, icon: TrendingUp, color: 'text-emerald-500' },
    { label: 'Referrals In Progress', value: summary?.referrals_in_progress ?? 0, icon: Users2, color: 'text-amber-500' },
    { label: 'Applications Submitted', value: summary?.applications_submitted ?? 0, icon: Send, color: 'text-sky-500' },
    { label: 'AI/ML Research Preprints', value: summary?.research_papers ?? 0, icon: BookOpen, color: 'text-purple-500' },
    { label: 'Follow-ups Due', value: summary?.follow_ups_due ?? 0, icon: Clock, color: 'text-rose-500' },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner / Candidate Target */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-900/40 via-purple-900/20 to-slate-900/40 border border-indigo-500/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs uppercase font-black tracking-wider text-indigo-400">Target Career Positioning</span>
          <h2 className="text-2xl font-black text-slate-100">AI Engineer • 20+ LPA Placement Target</h2>
          <p className="text-xs text-slate-400 mt-1">
            Bannari Amman Institute of Technology • Batch 2028 • Coimbatore, India
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/referrals"
            className="px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-1 shadow-sm transition"
          >
            Explore Referrals <ArrowUpRight className="w-4 h-4" />
          </Link>
          <Link
            to="/internships"
            className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
          >
            View Internships
          </Link>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 truncate">{card.label}</span>
                <Icon className={`w-4 h-4 ${card.color}`} />
              </div>
              <p className="text-2xl font-black mt-2 text-slate-900 dark:text-slate-100">{card.value}</p>
            </div>
          );
        })}
      </div>

      {/* Discovery Run Status Banner */}
      {summary?.latest_run && (
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-xs flex flex-col md:flex-row md:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span
              className={`w-2.5 h-2.5 rounded-full ${
                summary.latest_run.status === 'completed' ? 'bg-emerald-500' : 'bg-rose-500'
              }`}
            />
            <span className="font-semibold">Latest Discovery Run:</span>
            <span className="text-slate-500 dark:text-slate-400">
              {summary.latest_run.summary_text || `Run #${summary.latest_run.id} (${summary.latest_run.status})`}
            </span>
          </div>
          <span className="text-slate-400">
            Started: {new Date(summary.latest_run.started_at).toLocaleTimeString()}
          </span>
        </div>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <h3 className="font-bold text-sm mb-4 text-slate-800 dark:text-slate-200">Opportunities by Category</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics?.by_category || []} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#94a3b8' }} angle={-25} textAnchor="end" />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Score Distribution */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <h3 className="font-bold text-sm mb-4 text-slate-800 dark:text-slate-200">Match Score Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={analytics?.score_distribution || []}
                  dataKey="count"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                >
                  {(analytics?.score_distribution || []).map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Discovery Over Time */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <h3 className="font-bold text-sm mb-4 text-slate-800 dark:text-slate-200">Discovered Over Last 7 Days</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analytics?.discovered_over_time || []} margin={{ top: 10, right: 10, left: -20, bottom: 10 }}>
                <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }}
                />
                <Line type="monotone" dataKey="count" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Application Pipeline */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <h3 className="font-bold text-sm mb-4 text-slate-800 dark:text-slate-200">Opportunity Lifecycle Status</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={analytics?.application_pipeline || []}
                margin={{ top: 10, right: 20, left: 30, bottom: 10 }}
              >
                <XAxis type="number" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <YAxis dataKey="label" type="category" tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: 8, fontSize: 12 }}
                />
                <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
