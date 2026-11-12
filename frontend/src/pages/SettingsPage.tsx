import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { User, Save, Sliders } from 'lucide-react';
import { api } from '../services/api';

export function SettingsPage() {
  const queryClient = useQueryClient();
  const { data: profile, isLoading } = useQuery({
    queryKey: ['candidateProfile'],
    queryFn: api.getProfile,
  });

  const { data: weights } = useQuery({
    queryKey: ['scoringWeights'],
    queryFn: api.getScoringWeights,
  });

  const [form, setForm] = useState<any>({});
  const [weightsForm, setWeightsForm] = useState<any>({});
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (profile) setForm(profile);
  }, [profile]);

  useEffect(() => {
    if (weights) setWeightsForm(weights);
  }, [weights]);

  const updateProfileMutation = useMutation({
    mutationFn: (data: any) => api.updateProfile(data),
    onSuccess: () => {
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
      queryClient.invalidateQueries({ queryKey: ['candidateProfile'] });
    },
  });

  const updateWeightsMutation = useMutation({
    mutationFn: (data: any) => api.updateScoringWeights(data),
    onSuccess: () => {
      alert('Scoring weights saved!');
      queryClient.invalidateQueries({ queryKey: ['scoringWeights'] });
    },
  });

  if (isLoading) return <div className="text-center py-20 text-slate-400">Loading settings...</div>;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h2 className="text-xl font-black text-slate-900 dark:text-slate-100">Candidate Profile & Settings</h2>
        <p className="text-xs text-slate-500 mt-0.5">
          All profile attributes are fully editable and used directly by the AI matching engine.
        </p>
      </div>

      {/* Editable Candidate Profile */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
        <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
          <User className="w-4 h-4 text-indigo-500" /> Candidate Details
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-500 mb-1">Full Name</label>
            <input
              type="text"
              value={form.full_name || ''}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-500 mb-1">Graduation Year</label>
            <input
              type="number"
              value={form.graduation_year || 2028}
              onChange={(e) => setForm({ ...form, graduation_year: Number(e.target.value) })}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-500 mb-1">Institution</label>
            <input
              type="text"
              value={form.institution || ''}
              onChange={(e) => setForm({ ...form, institution: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-500 mb-1">Education Degree</label>
            <input
              type="text"
              value={form.education || ''}
              onChange={(e) => setForm({ ...form, education: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-500 mb-1">Target Career Positioning</label>
            <input
              type="text"
              value={form.target_career_positioning || ''}
              onChange={(e) => setForm({ ...form, target_career_positioning: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-500 mb-1">Career Goal</label>
            <input
              type="text"
              value={form.career_goal || ''}
              onChange={(e) => setForm({ ...form, career_goal: e.target.value })}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1">Candidate Summary</label>
          <textarea
            rows={3}
            value={form.resume_summary || ''}
            onChange={(e) => setForm({ ...form, resume_summary: e.target.value })}
            className="w-full text-xs p-3 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-sans"
          />
        </div>

        <div className="flex items-center justify-between pt-2">
          {saveSuccess && <span className="text-xs text-emerald-500 font-bold">Profile updated successfully!</span>}
          <button
            onClick={() => updateProfileMutation.mutate(form)}
            className="ml-auto inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition"
          >
            <Save className="w-3.5 h-3.5" /> Save Profile
          </button>
        </div>
      </div>

      {/* Configurable Scoring Weights */}
      <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
        <h3 className="font-bold text-sm text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
          <Sliders className="w-4 h-4 text-emerald-500" /> Configurable Scoring Weights
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-500 mb-1">Skill Match (default 0.30)</label>
            <input
              type="number"
              step="0.05"
              value={weightsForm.skill_match ?? 0.3}
              onChange={(e) => setWeightsForm({ ...weightsForm, skill_match: Number(e.target.value) })}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-500 mb-1">Eligibility Match (default 0.25)</label>
            <input
              type="number"
              step="0.05"
              value={weightsForm.eligibility_match ?? 0.25}
              onChange={(e) => setWeightsForm({ ...weightsForm, eligibility_match: Number(e.target.value) })}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-500 mb-1">Role Relevance (default 0.20)</label>
            <input
              type="number"
              step="0.05"
              value={weightsForm.role_relevance ?? 0.2}
              onChange={(e) => setWeightsForm({ ...weightsForm, role_relevance: Number(e.target.value) })}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-500 mb-1">Location Preference (default 0.10)</label>
            <input
              type="number"
              step="0.05"
              value={weightsForm.location_preference ?? 0.1}
              onChange={(e) => setWeightsForm({ ...weightsForm, location_preference: Number(e.target.value) })}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-500 mb-1">Referral / Freshness (default 0.15)</label>
            <input
              type="number"
              step="0.05"
              value={weightsForm.referral_freshness ?? 0.15}
              onChange={(e) => setWeightsForm({ ...weightsForm, referral_freshness: Number(e.target.value) })}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            />
          </div>
          <div>
            <label className="block font-semibold text-slate-500 mb-1">High Match Threshold (default 75)</label>
            <input
              type="number"
              value={weightsForm.high_match_threshold ?? 75}
              onChange={(e) => setWeightsForm({ ...weightsForm, high_match_threshold: Number(e.target.value) })}
              className="w-full px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
            />
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={() => updateWeightsMutation.mutate(weightsForm)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition"
          >
            <Save className="w-3.5 h-3.5" /> Save Weights
          </button>
        </div>
      </div>
    </div>
  );
}
