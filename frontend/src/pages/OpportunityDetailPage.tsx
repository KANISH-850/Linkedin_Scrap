import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Building,
  ExternalLink,
  Sparkles,
  CheckCircle2,
  Copy,
  Clock,
  Send,
  HelpCircle,
} from 'lucide-react';
import { api } from '../services/api';

export function OpportunityDetailPage() {
  const { id } = useParams<{ id: string }>();
  const oppId = Number(id);
  const queryClient = useQueryClient();

  const [contactName, setContactName] = useState('');
  const [draftType, setDraftType] = useState('referral_request');
  const [copiedDraftId, setCopiedDraftId] = useState<number | null>(null);

  const [followUpDate, setFollowUpDate] = useState('');
  const [followUpNote, setFollowUpNote] = useState('');

  const [resumeVersion, setResumeVersion] = useState('AI_Engineer_v1.pdf');

  // Reply analysis state
  const [pastedReply, setPastedReply] = useState('');
  const [replyAnalysisResult, setReplyAnalysisResult] = useState<any>(null);

  const { data: opp, isLoading } = useQuery({
    queryKey: ['opportunity', oppId],
    queryFn: () => api.getOpportunity(oppId),
    enabled: !!oppId,
  });

  const updateStatusMutation = useMutation({
    mutationFn: (newStatus: string) => api.updateOpportunityStatus(oppId, { tracking_status: newStatus }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['opportunity', oppId] }),
  });

  const draftMutation = useMutation({
    mutationFn: () => api.draftMessage(oppId, draftType, contactName || undefined),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['opportunity', oppId] }),
  });

  const followUpMutation = useMutation({
    mutationFn: () => api.createFollowUp(oppId, followUpDate, followUpNote),
    onSuccess: () => {
      setFollowUpNote('');
      setFollowUpDate('');
      alert('Follow-up created!');
      queryClient.invalidateQueries({ queryKey: ['opportunity', oppId] });
    },
  });

  const applyMutation = useMutation({
    mutationFn: () =>
      api.createApplication({
        opportunity_id: oppId,
        status: 'APPLIED',
        resume_version: resumeVersion,
      }),
    onSuccess: () => {
      alert('Application recorded!');
      queryClient.invalidateQueries({ queryKey: ['opportunity', oppId] });
    },
  });

  const analyzeReplyMutation = useMutation({
    mutationFn: () => api.analyzeReply({ opportunity_id: oppId, reply_text: pastedReply }),
    onSuccess: (data) => setReplyAnalysisResult(data),
  });

  if (isLoading) return <div className="text-center py-20 text-slate-400">Loading opportunity details...</div>;
  if (!opp) return <div className="text-center py-20 text-slate-400">Opportunity not found.</div>;

  const score = opp.score?.overall_score ?? 0;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Back Link */}
      <Link to={-1 as any} className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 dark:hover:text-slate-200">
        <ArrowLeft className="w-4 h-4" /> Back to opportunities
      </Link>

      {/* Main Header Card */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 uppercase tracking-wide">
                {opp.category.replace('_', ' ')}
              </span>
              {opp.referral_classification && (
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                  {opp.referral_classification.replace(/_/g, ' ')}
                </span>
              )}
              <span className="text-xs text-slate-400">
                Discovered: {new Date(opp.discovered_at).toLocaleDateString()}
              </span>
            </div>
            <h1 className="text-2xl font-black text-slate-900 dark:text-slate-100">{opp.title}</h1>
            <p className="text-sm font-semibold text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
              <Building className="w-4 h-4" /> {opp.organization}
            </p>
          </div>

          <div className="flex flex-col items-end gap-2 shrink-0">
            <div className="px-4 py-2 rounded-xl bg-indigo-600 text-white font-black text-xl flex items-center gap-1 shadow-sm">
              <Sparkles className="w-4 h-4" /> {score.toFixed(0)} <span className="text-xs font-normal opacity-80">/100</span>
            </div>
            <select
              value={opp.tracking_status}
              onChange={(e) => updateStatusMutation.mutate(e.target.value)}
              className="text-xs font-bold py-1.5 px-3 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700"
            >
              <option value="NEW">NEW</option>
              <option value="REVIEWED">REVIEWED</option>
              <option value="INTERESTED">INTERESTED</option>
              <option value="CONNECTION_PENDING">CONNECTION PENDING</option>
              <option value="CONNECTED">CONNECTED</option>
              <option value="REPLY_RECEIVED">REPLY RECEIVED</option>
              <option value="REFERRAL_RECEIVED">REFERRAL RECEIVED</option>
              <option value="APPLIED">APPLIED</option>
              <option value="INTERVIEW">INTERVIEW</option>
              <option value="REJECTED">REJECTED</option>
              <option value="DISMISSED">DISMISSED</option>
            </select>
          </div>
        </div>

        {/* Quick Meta */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-slate-100 dark:border-slate-800 text-xs">
          <div>
            <span className="text-slate-400 block font-medium">Location</span>
            <span className="font-semibold text-slate-700 dark:text-slate-200">{opp.location}</span>
          </div>
          <div>
            <span className="text-slate-400 block font-medium">Deadline</span>
            <span className="font-semibold text-slate-700 dark:text-slate-200">
              {opp.deadline ? opp.deadline : 'Not specified'}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block font-medium">Compensation / Stipend</span>
            <span className="font-semibold text-slate-700 dark:text-slate-200">
              {opp.compensation_or_stipend || 'Not specified'}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block font-medium">Verification Status</span>
            <span className="font-semibold capitalize text-emerald-500">{opp.verification_status}</span>
          </div>
        </div>

        {/* Links */}
        <div className="flex flex-wrap gap-2 pt-2">
          {opp.source_url && (
            <a
              href={opp.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition"
            >
              <ExternalLink className="w-3.5 h-3.5" /> Source Link
            </a>
          )}
          {opp.application_url && opp.application_url !== opp.source_url && (
            <a
              href={opp.application_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900 transition"
            >
              <ExternalLink className="w-3.5 h-3.5" /> Official Application URL
            </a>
          )}
        </div>
      </div>

      {/* AI Intelligence & Eligibility Assessment */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Eligibility Card */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-indigo-500" /> Eligibility Assessment
            </h3>
            <span
              className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                opp.eligibility?.status === 'Eligible'
                  ? 'bg-emerald-500/10 text-emerald-500'
                  : opp.eligibility?.status === 'Not eligible'
                  ? 'bg-rose-500/10 text-rose-500'
                  : 'bg-amber-500/10 text-amber-500'
              }`}
            >
              {opp.eligibility?.status || 'Assessing'}
            </span>
          </div>

          <p className="text-xs text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-800/50 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
            {opp.eligibility?.summary}
          </p>

          {opp.eligibility?.matched_requirements && opp.eligibility.matched_requirements.length > 0 && (
            <div>
              <span className="text-[11px] font-bold uppercase text-slate-400">Matched Requirements:</span>
              <ul className="list-disc list-inside text-xs text-slate-600 dark:text-slate-300 mt-1 space-y-0.5">
                {opp.eligibility.matched_requirements.map((m, idx) => (
                  <li key={idx}>{m}</li>
                ))}
              </ul>
            </div>
          )}

          {opp.eligibility?.disqualifying_requirements && opp.eligibility.disqualifying_requirements.length > 0 && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs">
              <span className="font-bold block mb-1">Disqualifying Flags:</span>
              <ul className="list-disc list-inside space-y-0.5">
                {opp.eligibility.disqualifying_requirements.map((d, idx) => (
                  <li key={idx}>{d}</li>
                ))}
              </ul>
            </div>
          )}

          {opp.eligibility?.verification_questions && opp.eligibility.verification_questions.length > 0 && (
            <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-xs">
              <span className="font-bold flex items-center gap-1 mb-1">
                <HelpCircle className="w-3.5 h-3.5" /> Manual Verification Needed:
              </span>
              <ul className="list-disc list-inside space-y-0.5">
                {opp.eligibility.verification_questions.map((q, idx) => (
                  <li key={idx}>{q}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Score Breakdown */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3">
          <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-emerald-500" /> Match Score Breakdown
          </h3>

          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Skill Match (30%)</span>
              <span className="font-bold">{opp.score?.skill_score.toFixed(0)}/100</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Eligibility Match (25%)</span>
              <span className="font-bold">{opp.score?.eligibility_score.toFixed(0)}/100</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Role Relevance (20%)</span>
              <span className="font-bold">{opp.score?.relevance_score.toFixed(0)}/100</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Location Preference (10%)</span>
              <span className="font-bold">{opp.score?.location_score.toFixed(0)}/100</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Referral Evidence & Freshness (15%)</span>
              <span className="font-bold">{opp.score?.referral_freshness_score.toFixed(0)}/100</span>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
            <span className="text-[11px] font-bold uppercase text-slate-400">Recommended Action:</span>
            <p className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 mt-0.5">
              {opp.score?.recommended_action || 'Review details'}
            </p>
          </div>
        </div>
      </div>

      {/* Opportunity Description */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3">
        <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">Opportunity Description & Requirements</h3>
        <p className="text-xs leading-relaxed text-slate-700 dark:text-slate-300 whitespace-pre-line font-sans">
          {opp.description}
        </p>

        {opp.required_skills?.length > 0 && (
          <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
            <span className="text-xs font-bold text-slate-500 block mb-2">Required Skills:</span>
            <div className="flex flex-wrap gap-1.5">
              {opp.required_skills.map((s, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-medium"
                >
                  {s}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Message Drafting Tool */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
        <div>
          <h3 className="font-bold text-base text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
            <Send className="w-4 h-4 text-indigo-500" /> AI Message Drafter
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Generate professional, tailored messages. Review and send manually via your own accounts.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Draft Type</label>
            <select
              value={draftType}
              onChange={(e) => setDraftType(e.target.value)}
              className="w-full text-xs py-2 px-3 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            >
              <option value="connection_request">LinkedIn Connection Request (&le; 300 chars)</option>
              <option value="referral_request">Employee Referral Request</option>
              <option value="recruiter_outreach">Recruiter Outreach</option>
              <option value="follow_up">Polite Follow-up</option>
              <option value="thank_you">Thank-You Note</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 mb-1">Recipient Name (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Priya Sharma"
              value={contactName}
              onChange={(e) => setContactName(e.target.value)}
              className="w-full text-xs py-2 px-3 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => draftMutation.mutate()}
              disabled={draftMutation.isPending}
              className="w-full py-2 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition disabled:opacity-50"
            >
              {draftMutation.isPending ? 'Generating...' : 'Generate Personalized Draft'}
            </button>
          </div>
        </div>

        {/* Saved Drafts */}
        {opp.drafts && opp.drafts.length > 0 && (
          <div className="space-y-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <span className="text-xs font-bold text-slate-500">Generated Drafts:</span>
            {opp.drafts.map((draft) => (
              <div
                key={draft.id}
                className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase text-indigo-600 dark:text-indigo-400">
                    {draft.draft_type.replace(/_/g, ' ')}
                  </span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(draft.body);
                      setCopiedDraftId(draft.id);
                      setTimeout(() => setCopiedDraftId(null), 2000);
                    }}
                    className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 hover:bg-slate-100"
                  >
                    <Copy className="w-3 h-3" />
                    {copiedDraftId === draft.id ? 'Copied!' : 'Copy to Clipboard'}
                  </button>
                </div>
                {draft.subject && <p className="text-xs font-bold text-slate-800 dark:text-slate-200">Subject: {draft.subject}</p>}
                <p className="text-xs whitespace-pre-line text-slate-700 dark:text-slate-300 font-mono bg-white dark:bg-slate-900/60 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                  {draft.body}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Reply Intelligence & Follow-up Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Reply Intelligence Card */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3">
          <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">Reply Intelligence</h3>
          <p className="text-xs text-slate-500">Paste any message received from the company or recruiter to analyze it.</p>
          <textarea
            rows={3}
            placeholder="Paste recruiter's reply here..."
            value={pastedReply}
            onChange={(e) => setPastedReply(e.target.value)}
            className="w-full text-xs p-3 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-mono"
          />
          <button
            onClick={() => analyzeReplyMutation.mutate()}
            disabled={analyzeReplyMutation.isPending || !pastedReply}
            className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold transition disabled:opacity-40"
          >
            {analyzeReplyMutation.isPending ? 'Analyzing...' : 'Analyze Reply Intent'}
          </button>

          {replyAnalysisResult && (
            <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 text-xs space-y-1.5">
              <span className="font-bold text-purple-600 dark:text-purple-400 block">
                Intent: {replyAnalysisResult.classification}
              </span>
              <p className="text-slate-600 dark:text-slate-300">{replyAnalysisResult.explanation}</p>
              <p className="font-semibold text-slate-800 dark:text-slate-200">
                Next Step: {replyAnalysisResult.recommended_next_step}
              </p>
              <div className="pt-2">
                <span className="font-semibold text-slate-500 block">Suggested Response:</span>
                <p className="font-mono bg-white dark:bg-slate-900 p-2 rounded text-slate-700 dark:text-slate-300 mt-1">
                  {replyAnalysisResult.suggested_response}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Schedule Follow-up & Record Application */}
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
          <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100">Action & Tracking</h3>

          {/* Add Follow-up */}
          <div className="space-y-2">
            <span className="text-xs font-bold text-slate-500 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" /> Schedule Follow-up
            </span>
            <div className="flex gap-2">
              <input
                type="date"
                value={followUpDate}
                onChange={(e) => setFollowUpDate(e.target.value)}
                className="text-xs px-2 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
              />
              <input
                type="text"
                placeholder="Follow-up note..."
                value={followUpNote}
                onChange={(e) => setFollowUpNote(e.target.value)}
                className="flex-1 text-xs px-2 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
              />
              <button
                onClick={() => followUpMutation.mutate()}
                disabled={!followUpDate}
                className="px-3 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-800 text-xs font-semibold hover:bg-slate-300 disabled:opacity-40"
              >
                Set
              </button>
            </div>
          </div>

          {/* Record Application */}
          <div className="space-y-2 pt-3 border-t border-slate-100 dark:border-slate-800">
            <span className="text-xs font-bold text-slate-500 flex items-center gap-1">
              <Send className="w-3.5 h-3.5" /> Record Application Submission
            </span>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Resume version (e.g. AI_Resume_v2.pdf)"
                value={resumeVersion}
                onChange={(e) => setResumeVersion(e.target.value)}
                className="flex-1 text-xs px-2 py-1.5 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
              />
              <button
                onClick={() => applyMutation.mutate()}
                className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition"
              >
                Mark Applied
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
