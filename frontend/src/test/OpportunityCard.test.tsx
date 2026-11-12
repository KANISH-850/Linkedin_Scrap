import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { OpportunityCard } from '../components/OpportunityCard';
import type { OpportunitySummary } from '../types';

const mockOpp: OpportunitySummary = {
  id: 1,
  title: 'AI Engineering Intern',
  organization: 'NeuralTech India',
  category: 'internships',
  description: 'Build LLM agents with Python and FastAPI.',
  location: 'Remote',
  is_remote: true,
  is_hybrid: false,
  deadline: null,
  discovered_at: new Date().toISOString(),
  active_status: 'active',
  verification_status: 'verified',
  source_url: 'https://example.com/job/1',
  required_skills: ['Python', 'FastAPI', 'Generative AI'],
  preferred_skills: [],
  ai_status: 'completed',
  tracking_status: 'NEW',
  is_interested: false,
  score: {
    overall_score: 92.0,
    skill_score: 95,
    eligibility_score: 95,
    relevance_score: 90,
    location_score: 100,
    referral_freshness_score: 75,
    explanation: 'Strong match',
    recommended_action: 'Apply now',
    scoring_model: 'job_internship',
    scored_at: new Date().toISOString(),
  },
  eligibility: {
    status: 'Eligible',
    matched_requirements: ['Python'],
    missing_requirements: [],
    disqualifying_requirements: [],
    verification_questions: [],
    summary: 'Eligible',
    assessed_at: new Date().toISOString(),
  },
};

describe('OpportunityCard', () => {
  it('renders title, organization, score, and unspecified deadline safely', () => {
    render(
      <MemoryRouter>
        <OpportunityCard opp={mockOpp} />
      </MemoryRouter>
    );

    expect(screen.getByText('AI Engineering Intern')).toBeInTheDocument();
    expect(screen.getByText('NeuralTech India')).toBeInTheDocument();
    expect(screen.getByText('92')).toBeInTheDocument();
    expect(screen.getByText('Deadline not specified')).toBeInTheDocument();
    expect(screen.getByText('Verified')).toBeInTheDocument();
  });
});

