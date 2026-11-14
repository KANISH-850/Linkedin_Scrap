import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { DashboardLayout } from './layouts/DashboardLayout';

import { OverviewPage } from './pages/OverviewPage';
import { OpportunityListTab } from './pages/OpportunityListTab';
import { OpportunityDetailPage } from './pages/OpportunityDetailPage';
import { FollowUpsPage } from './pages/FollowUpsPage';
import { ApplicationsPage } from './pages/ApplicationsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SourcesPage } from './pages/SourcesPage';
import { SettingsPage } from './pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 60 * 2,
    },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { loading } = useAuth();
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-400">Loading ReferralPilot AI...</div>;
  }
  return <>{children}</>;
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<Navigate to="/" replace />} />
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <DashboardLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<OverviewPage />} />
                <Route
                  path="referrals"
                  element={
                    <OpportunityListTab
                      category="referrals"
                      title="Referral Opportunities"
                      subtitle="Discover employee referral posts and direct outreach opportunities."
                    />
                  }
                />
                <Route
                  path="internships"
                  element={
                    <OpportunityListTab
                      category="internships"
                      title="Internship Openings"
                      subtitle="AI/ML, Python, and Software Engineering internships filtered for your background."
                    />
                  }
                />
                <Route
                  path="jobs"
                  element={
                    <OpportunityListTab
                      category="fresher_jobs"
                      title="Fresher & Trainee Roles"
                      subtitle="Associate Software Engineer, GET, and entry-level positions."
                    />
                  }
                />
                <Route
                  path="hackathons"
                  element={
                    <OpportunityListTab
                      category="hackathons"
                      title="Hackathons & Challenges"
                      subtitle="National and international hackathons, AI challenges, and innovation contests."
                    />
                  }
                />
                <Route
                  path="scholarships"
                  element={
                    <OpportunityListTab
                      category="scholarships"
                      title="Scholarships & Grants"
                      subtitle="Academic merit scholarships, government grants, and research fellowships."
                    />
                  }
                />
                <Route
                  path="courses"
                  element={
                    <OpportunityListTab
                      category="courses"
                      title="Courses & Certifications"
                      subtitle="Industry certifications, deep learning courses, and practical skill paths."
                    />
                  }
                />
                <Route
                  path="research"
                  element={
                    <OpportunityListTab
                      category="research"
                      title="Research & Academic Opportunities"
                      subtitle="arXiv AI preprints, university research programs, and faculty openings."
                    />
                  }
                />
                <Route path="opportunities/:id" element={<OpportunityDetailPage />} />
                <Route path="followups" element={<FollowUpsPage />} />
                <Route path="applications" element={<ApplicationsPage />} />
                <Route path="analytics" element={<AnalyticsPage />} />
                <Route path="sources" element={<SourcesPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;

