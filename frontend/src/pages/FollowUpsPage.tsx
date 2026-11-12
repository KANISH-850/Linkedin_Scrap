import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Clock, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

export function FollowUpsPage() {
  const queryClient = useQueryClient();
  const { data: followUps, isLoading } = useQuery({
    queryKey: ['followUps'],
    queryFn: api.getFollowUps,
  });

  const completeMutation = useMutation({
    mutationFn: (id: number) => api.updateFollowUp(id, { status: 'completed' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['followUps'] }),
  });

  if (isLoading) return <div className="text-center py-20 text-slate-400">Loading follow-ups...</div>;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-black text-slate-900 dark:text-slate-100">Follow-up Schedule</h2>
        <p className="text-xs text-slate-500 mt-0.5">Track pending outreach follow-ups and reminders.</p>
      </div>

      {!followUps || followUps.length === 0 ? (
        <div className="p-10 text-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl text-slate-400 text-sm">
          No follow-ups scheduled yet. Open an opportunity to add a follow-up reminder.
        </div>
      ) : (
        <div className="space-y-3">
          {followUps.map((f) => (
            <div
              key={f.id}
              className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                      f.status === 'completed'
                        ? 'bg-emerald-500/10 text-emerald-500'
                        : 'bg-amber-500/10 text-amber-500'
                    }`}
                  >
                    {f.status}
                  </span>
                  <span className="text-xs font-semibold text-slate-500 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" /> Due: {f.due_date}
                  </span>
                </div>
                <Link to={`/opportunities/${f.opportunity_id}`} className="font-bold text-sm hover:text-indigo-500 block">
                  {f.opportunity_title || `Opportunity #${f.opportunity_id}`} — {f.organization}
                </Link>
                {f.notes && <p className="text-xs text-slate-500">{f.notes}</p>}
              </div>

              {f.status !== 'completed' && (
                <button
                  onClick={() => completeMutation.mutate(f.id)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shrink-0"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" /> Mark Done
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
