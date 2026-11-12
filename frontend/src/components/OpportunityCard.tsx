import { Link } from 'react-router-dom';
import {
  ExternalLink,
  MapPin,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  Building,
  ArrowRight,
} from 'lucide-react';
import type { OpportunitySummary } from '../types';

interface OpportunityCardProps {
  opp: OpportunitySummary;
  onStatusChange?: (id: number, newStatus: string) => void;
}

export function OpportunityCard({ opp, onStatusChange }: OpportunityCardProps) {
  const score = opp.score?.overall_score ?? 0;
  const scoreColor =
    score >= 90
      ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30'
      : score >= 75
      ? 'bg-indigo-500/10 text-indigo-500 border-indigo-500/30'
      : score >= 60
      ? 'bg-amber-500/10 text-amber-500 border-amber-500/30'
      : 'bg-rose-500/10 text-rose-500 border-rose-500/30';

  const eligStatus = opp.eligibility?.status;
  const isDisqualified = eligStatus === 'Not eligible';

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 hover:border-indigo-500/50 transition-all flex flex-col justify-between shadow-sm hover:shadow-md">
      <div>
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 capitalize">
                {opp.category.replace('_', ' ')}
              </span>
              {opp.referral_classification === 'confirmed_referral_offer' && (
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/30">
                  Confirmed Referral
                </span>
              )}
              {opp.verification_status === 'verified' && (
                <span className="text-[11px] font-medium text-emerald-500 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Verified
                </span>
              )}
            </div>
            <Link to={`/opportunities/${opp.id}`}>
              <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 hover:text-indigo-600 dark:hover:text-indigo-400 transition truncate">
                {opp.title}
              </h3>
            </Link>
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400 flex items-center gap-1 mt-0.5">
              <Building className="w-3.5 h-3.5" />
              {opp.organization}
            </p>
          </div>

          <div className={`px-2.5 py-1 rounded-lg border font-black text-sm shrink-0 ${scoreColor}`}>
            {score.toFixed(0)}
          </div>
        </div>

        <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-2 my-2">{opp.description}</p>

        {/* Metadata Badges */}
        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400 my-2">
          <span className="flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5" />
            {opp.location}
          </span>
          <span className="flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5" />
            {opp.deadline ? `Due: ${opp.deadline}` : 'Deadline not specified'}
          </span>
        </div>

        {/* Eligibility Warning or Check */}
        {isDisqualified && (
          <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs flex items-center gap-1.5 my-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span className="truncate">{opp.eligibility?.summary || 'Not eligible based on requirements'}</span>
          </div>
        )}

        {/* Skills */}
        {opp.required_skills?.length > 0 && (
          <div className="flex flex-wrap gap-1 my-2">
            {opp.required_skills.slice(0, 4).map((sk, idx) => (
              <span
                key={idx}
                className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
              >
                {sk}
              </span>
            ))}
            {opp.required_skills.length > 4 && (
              <span className="text-[10px] text-slate-400 self-center">+{opp.required_skills.length - 4}</span>
            )}
          </div>
        )}
      </div>

      <div className="pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between gap-2 mt-2">
        <select
          value={opp.tracking_status}
          onChange={(e) => onStatusChange?.(opp.id, e.target.value)}
          className="text-xs font-semibold py-1 px-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300"
        >
          <option value="NEW">NEW</option>
          <option value="REVIEWED">REVIEWED</option>
          <option value="INTERESTED">INTERESTED</option>
          <option value="CONNECTION_PENDING">CONNECT PENDING</option>
          <option value="CONNECTED">CONNECTED</option>
          <option value="REPLY_RECEIVED">REPLY RECVD</option>
          <option value="REFERRAL_RECEIVED">REFERRAL RECVD</option>
          <option value="APPLIED">APPLIED</option>
          <option value="DISMISSED">DISMISSED</option>
        </select>

        <div className="flex items-center gap-2">
          {opp.source_url && (
            <a
              href={opp.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
              title="Open source URL"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
          <Link
            to={`/opportunities/${opp.id}`}
            className="flex items-center gap-1 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            Details <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
