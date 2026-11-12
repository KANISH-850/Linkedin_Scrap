import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Power } from 'lucide-react';
import { api } from '../services/api';

export function SourcesPage() {
  const queryClient = useQueryClient();
  const { data: sources, isLoading } = useQuery({
    queryKey: ['discoverySources'],
    queryFn: api.getSources,
  });

  const toggleSourceMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) => api.updateSource(id, { enabled }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['discoverySources'] }),
  });

  if (isLoading) return <div className="text-center py-20 text-slate-400">Loading discovery sources...</div>;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-black text-slate-900 dark:text-slate-100">Discovery Sources</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Configure active opportunity adapters. Complies strictly with permitted public RSS, APIs, and scraping policies.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sources?.map((s) => (
          <div
            key={s.id}
            className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">{s.name}</h3>
                <span className="text-[11px] font-mono text-slate-400 block mt-0.5">
                  Adapter: {s.adapter_key} ({s.source_type})
                </span>
              </div>
              <button
                onClick={() => toggleSourceMutation.mutate({ id: s.id, enabled: !s.enabled })}
                className={`p-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                  s.enabled
                    ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-emerald-500/20'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-400 hover:bg-slate-200'
                }`}
              >
                <Power className="w-3.5 h-3.5" />
                {s.enabled ? 'Enabled' : 'Disabled'}
              </button>
            </div>

            <div className="text-xs space-y-1 text-slate-500 pt-2 border-t border-slate-100 dark:border-slate-800">
              <div className="flex justify-between">
                <span>Frequency:</span>
                <span className="font-semibold text-slate-700 dark:text-slate-300">Every {s.frequency_hours} hours</span>
              </div>
              <div className="flex justify-between">
                <span>Last run:</span>
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  {s.last_run_at ? new Date(s.last_run_at).toLocaleString() : 'Never'}
                </span>
              </div>
              {s.last_error && (
                <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-500 text-[11px]">
                  {s.last_error}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
