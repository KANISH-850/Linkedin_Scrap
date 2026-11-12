import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search } from 'lucide-react';
import { OpportunityCard } from '../components/OpportunityCard';
import { api } from '../services/api';
import type { OpportunityCategory } from '../types';

interface OpportunityListTabProps {
  category?: OpportunityCategory;
  title: string;
  subtitle: string;
}

export function OpportunityListTab({ category, title, subtitle }: OpportunityListTabProps) {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [minScore, setMinScore] = useState<number | undefined>(undefined);
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ['opportunities', category, search, minScore, statusFilter, page],
    queryFn: () =>
      api.getOpportunities({
        category,
        search: search || undefined,
        min_score: minScore,
        tracking_status: statusFilter !== 'all' ? statusFilter : undefined,
        page,
        page_size: 12,
      }),
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ id, newStatus }: { id: number; newStatus: string }) =>
      api.updateOpportunityStatus(id, { tracking_status: newStatus }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['opportunities'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
    },
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h2 className="text-xl font-black text-slate-900 dark:text-slate-100">{title}</h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{subtitle}</p>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search role, skills, company..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-500">Min Score:</span>
          <select
            value={minScore ?? ''}
            onChange={(e) => setMinScore(e.target.value ? Number(e.target.value) : undefined)}
            className="text-xs py-1.5 px-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
          >
            <option value="">All Scores</option>
            <option value="90">90+ (Excellent)</option>
            <option value="75">75+ (Strong)</option>
            <option value="60">60+ (Review)</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-500">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs py-1.5 px-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
          >
            <option value="all">All Statuses</option>
            <option value="NEW">NEW</option>
            <option value="INTERESTED">INTERESTED</option>
            <option value="CONNECTION_PENDING">CONNECT PENDING</option>
            <option value="CONNECTED">CONNECTED</option>
            <option value="REFERRAL_RECEIVED">REFERRAL RECVD</option>
            <option value="APPLIED">APPLIED</option>
          </select>
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="text-center py-20 text-slate-400">Loading opportunities...</div>
      ) : data?.items.length === 0 ? (
        <div className="text-center py-20 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8">
          <p className="font-semibold text-slate-600 dark:text-slate-400">No opportunities found matching this filter.</p>
          <p className="text-xs text-slate-400 mt-1">Try clearing filters or click "Run Discovery Now" in the sidebar.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data?.items.map((opp) => (
            <OpportunityCard
              key={opp.id}
              opp={opp}
              onStatusChange={(id, st) => updateStatusMutation.mutate({ id, newStatus: st })}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between pt-4">
          <span className="text-xs text-slate-500">
            Page {data.page} of {data.total_pages} ({data.total} total)
          </span>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="px-3 py-1 rounded bg-slate-200 dark:bg-slate-800 text-xs font-semibold disabled:opacity-40"
            >
              Previous
            </button>
            <button
              disabled={page >= data.total_pages}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1 rounded bg-slate-200 dark:bg-slate-800 text-xs font-semibold disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
