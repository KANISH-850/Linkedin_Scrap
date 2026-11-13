import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import {
  LayoutDashboard,
  Users2,
  GraduationCap,
  Briefcase,
  Trophy,
  Award,
  BookOpen,
  Microscope,
  Clock,
  Send,
  BarChart3,
  Radio,
  Settings,
  Sun,
  Moon,
  LogOut,
  Menu,
  X,
  PlusCircle,
  PlayCircle,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { api } from '../services/api';

const navItems = [
  { to: '/', label: 'Overview', icon: LayoutDashboard },
  { to: '/referrals', label: 'Referrals', icon: Users2 },
  { to: '/internships', label: 'Internships', icon: GraduationCap },
  { to: '/jobs', label: 'Fresher Jobs', icon: Briefcase },
  { to: '/hackathons', label: 'Hackathons', icon: Trophy },
  { to: '/scholarships', label: 'Scholarships', icon: Award },
  { to: '/courses', label: 'Courses & Certs', icon: BookOpen },
  { to: '/research', label: 'Research', icon: Microscope },
  { to: '/followups', label: 'Follow-ups', icon: Clock },
  { to: '/applications', label: 'Applications', icon: Send },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/sources', label: 'Sources', icon: Radio },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export function DashboardLayout() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [runningDiscovery, setRunningDiscovery] = useState(false);
  const [submitModalOpen, setSubmitModalOpen] = useState(false);
  const [manualForm, setManualForm] = useState({ url: '', raw_text: '', organization_hint: '', category_hint: 'referrals' });
  const [submitError, setSubmitError] = useState('');
  const [submitSuccess, setSubmitSuccess] = useState('');
  const navigate = useNavigate();

  const queryClient = useQueryClient();
  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const showToast = (text: string, type: 'success' | 'error' = 'success') => {
    setToastMessage({ text, type });
    setTimeout(() => setToastMessage(null), 5000);
  };

  const handleRunDiscovery = async () => {
    try {
      setRunningDiscovery(true);
      await api.runDiscovery();
      await queryClient.invalidateQueries();
      showToast('Live discovery completed! Opportunities updated.', 'success');
    } catch (err: any) {
      showToast(`Discovery run failed: ${err.message}`, 'error');
    } finally {
      setRunningDiscovery(false);
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError('');
    setSubmitSuccess('');
    try {
      const opp = await api.submitManualOpportunity(manualForm);
      setSubmitSuccess(`Created: ${opp.title} (${opp.organization})`);
      setTimeout(() => {
        setSubmitModalOpen(false);
        navigate(`/opportunities/${opp.id}`);
      }, 1000);
    } catch (err: any) {
      setSubmitError(err.message || 'Submission failed');
    }
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-slate-100">
      {/* Mobile Header */}
      <header className="md:hidden flex items-center justify-between p-4 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-sm">
            RP
          </div>
          <span className="font-bold text-base tracking-tight">ReferralPilot AI</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
            aria-label="Open menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </header>

      {/* Sidebar Navigation */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col transition-transform duration-200 ease-in-out md:static md:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-5 flex items-center justify-between border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white font-black text-base shadow-sm">
              RP
            </div>
            <div>
              <h1 className="font-bold text-base leading-tight">ReferralPilot AI</h1>
              <span className="text-[11px] text-indigo-600 dark:text-indigo-400 font-medium">Kanish K • 2028</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="p-3 space-y-2 border-b border-slate-200 dark:border-slate-800">
          <button
            onClick={() => setSubmitModalOpen(true)}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 text-xs font-semibold rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 transition"
          >
            <PlusCircle className="w-4 h-4" />
            Submit URL / Post
          </button>
          <button
            disabled={runningDiscovery}
            onClick={handleRunDiscovery}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition disabled:opacity-50"
          >
            <PlayCircle className="w-4 h-4" />
            {runningDiscovery ? 'Discovering...' : 'Run Discovery Now'}
          </button>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
          <div className="truncate text-xs text-slate-500">
            <p className="font-semibold text-slate-800 dark:text-slate-200 truncate">{user?.full_name || 'Admin'}</p>
            <p className="truncate text-[11px]">{user?.email}</p>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={toggleTheme}
              className="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
              title="Toggle theme"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
            <button
              onClick={logout}
              className="p-1.5 rounded-lg text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40"
              title="Sign out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Pane */}
      <main className="flex-1 overflow-y-auto p-4 md:p-8 relative">
        {toastMessage && (
          <div
            className={`fixed top-4 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg border text-sm font-medium transition-all ${
              toastMessage.type === 'success'
                ? 'bg-emerald-950/90 border-emerald-500/40 text-emerald-200'
                : 'bg-rose-950/90 border-rose-500/40 text-rose-200'
            }`}
          >
            {toastMessage.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
            )}
            <span>{toastMessage.text}</span>
          </div>
        )}
        <Outlet />
      </main>

      {/* Manual Submit Modal */}
      {submitModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-lg">Submit Public Opportunity / Post</h3>
              <button
                onClick={() => setSubmitModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleManualSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
                  Public URL (Career page / Public post)
                </label>
                <input
                  type="url"
                  placeholder="https://company.com/jobs/123 or public LinkedIn link"
                  value={manualForm.url}
                  onChange={(e) => setManualForm({ ...manualForm, url: e.target.value })}
                  className="w-full px-3 py-2 text-sm rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <p className="text-[11px] text-slate-500 mt-1">
                  * Note: LinkedIn URLs are never scraped. Paste the post text below when submitting LinkedIn posts.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">
                  Pasted Text / Announcement
                </label>
                <textarea
                  rows={4}
                  placeholder="Paste the recruiter's message, referral instructions, or job description here..."
                  value={manualForm.raw_text}
                  onChange={(e) => setManualForm({ ...manualForm, raw_text: e.target.value })}
                  className="w-full px-3 py-2 text-sm rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Company / Organization</label>
                  <input
                    type="text"
                    placeholder="e.g. Google, DeepTech"
                    value={manualForm.organization_hint}
                    onChange={(e) => setManualForm({ ...manualForm, organization_hint: e.target.value })}
                    className="w-full px-3 py-2 text-sm rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase text-slate-500 mb-1">Category</label>
                  <select
                    value={manualForm.category_hint}
                    onChange={(e) => setManualForm({ ...manualForm, category_hint: e.target.value })}
                    className="w-full px-3 py-2 text-sm rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="referrals">Referrals</option>
                    <option value="internships">Internships</option>
                    <option value="fresher_jobs">Fresher Jobs</option>
                    <option value="hackathons">Hackathons</option>
                    <option value="scholarships">Scholarships</option>
                    <option value="courses">Courses & Certs</option>
                    <option value="research">Research</option>
                  </select>
                </div>
              </div>

              {submitError && <p className="text-xs text-rose-500 font-medium">{submitError}</p>}
              {submitSuccess && <p className="text-xs text-emerald-500 font-medium">{submitSuccess}</p>}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSubmitModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  Process with AI
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

