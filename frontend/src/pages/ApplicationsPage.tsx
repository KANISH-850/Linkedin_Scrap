import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { ExternalLink } from 'lucide-react';
import { api } from '../services/api';

export function ApplicationsPage() {
  const { data: apps, isLoading } = useQuery({
    queryKey: ['applications'],
    queryFn: api.getApplications,
  });

  if (isLoading) return <div className="text-center py-20 text-slate-400">Loading applications...</div>;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-black text-slate-900 dark:text-slate-100">Submitted Applications</h2>
        <p className="text-xs text-slate-500 mt-0.5">Verified record of applications you have manually submitted.</p>
      </div>

      {!apps || apps.length === 0 ? (
        <div className="p-10 text-center bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl text-slate-400 text-sm">
          No applications recorded yet.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {apps.map((a) => (
            <div
              key={a.id}
              className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-between gap-4"
            >
              <div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-500 uppercase">
                  {a.status}
                </span>
                <Link to={`/opportunities/${a.opportunity_id}`} className="font-bold text-sm hover:text-indigo-500 block mt-1">
                  {a.opportunity_title || `Opportunity #${a.opportunity_id}`} — {a.organization}
                </Link>
                <p className="text-xs text-slate-500 mt-0.5">
                  Resume: {a.resume_version || 'Not specified'} • Applied:{' '}
                  {a.applied_at ? new Date(a.applied_at).toLocaleDateString() : 'N/A'}
                </p>
              </div>
              {a.portal_url && (
                <a
                  href={a.portal_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
