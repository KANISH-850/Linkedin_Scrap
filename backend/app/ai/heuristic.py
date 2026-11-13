"""Deterministic heuristic scoring and intelligence engine."""

from datetime import datetime, timezone
import re
from typing import List, Tuple

from app.ai.schemas import (
    AIDraftMessageResult,
    AIEligibilityResult,
    AIExtractionResult,
    AIReplyAnalysisResult,
    AIScoringResult,
    BaseLLMClient,
)

CORE_SKILLS_LOOKUP = [
    "python",
    "machine learning",
    "deep learning",
    "nlp",
    "generative ai",
    "fastapi",
    "react",
    "typescript",
    "sql",
    "data structures",
    "algorithms",
    "git",
    "docker",
    "aws",
    "pytorch",
    "tensorflow",
]


def _detect_skills(text: str) -> List[str]:
    found = []
    text_lower = text.lower()
    for sk in CORE_SKILLS_LOOKUP:
        pattern = r"\b" + re.escape(sk) + r"\b"
        if re.search(pattern, text_lower):
            found.append(sk.title())
    return found


def _detect_referral_classification(text: str) -> Tuple[str, float, str | None]:
    """
    Evidence-based classification:
      - CONFIRMED_REFERRAL_OFFER: Author explicitly offers to refer candidates.
      - EXPLICIT_REFERRAL_REQUEST: Candidate explicitly asking for referral.
      - HIRING_ANNOUNCEMENT: Team/recruiter hiring announcement with direct message call-to-action.
      - GENERAL_JOB_POST: Standard job listing without employee referral offer.
      - UNCLEAR: Ambiguous or insufficient evidence.
    """
    t = text.lower()

    # Disqualification: mentions receiving a referral in the past
    if re.search(r"\b(i received a referral|got a referral from|referred by|my referral was)\b", t):
        return ("UNCLEAR", 0.15, "Past referral mention by applicant; not an offer to refer candidates.")

    # Disqualification: generic company referral program mention without author offer
    if re.search(r"\b(referral program available|company has a referral policy|referral bonus)\b", t) and not re.search(r"\b(dm me|reach out|contact me|message me|i can refer|happy to refer)\b", t):
        return ("UNCLEAR", 0.20, "General mention of corporate referral program without explicit personal referral offer.")

    # 1. Confirmed referral offer requires explicit author commitment
    offer_patterns = [
        (r"\b(i('m| am) referring|i can refer|happy to refer|willing to refer|ready to refer|offering referrals?)\b", "Direct referral offer"),
        (r"\b(dm me (?:for|if you need|to get)?\s*(?:a\s+)?referral)\b", "Direct message referral invitation"),
        (r"\b(reach out (?:for|if you need)?\s*(?:a\s+)?referral)\b", "Reach out for referral invitation"),
        (r"\b(message me (?:for|if you need)?\s*(?:a\s+)?referral)\b", "Message invitation for referral"),
        (r"\b(send (?:me )?(?:your )?resume (?:for|to get)?\s*(?:a\s+)?referral)\b", "Resume request for referral"),
        (r"\b(drop (?:your )?resume (?:for|to get)?\s*(?:a\s+)?referral)\b", "Resume submission for referral"),
    ]
    for pat, label in offer_patterns:
        match = re.search(pat, t)
        if match:
            return ("CONFIRMED_REFERRAL_OFFER", 0.95, f"Explicit author referral offer verified: '{match.group(0)}' ({label}).")

    # 2. Explicit referral request from candidate
    request_patterns = [
        r"\b(does anyone have a referral|can anyone refer me|looking for a referral|seeking a referral|need a referral|anyone can refer)\b",
        r"\b(could someone refer me|any referrals? available for)\b"
    ]
    for pat in request_patterns:
        match = re.search(pat, t)
        if match:
            return ("EXPLICIT_REFERRAL_REQUEST", 0.85, f"Explicit request for referral from candidate: '{match.group(0)}'.")

    # If explicit online application link is given (e.g. "apply at ...", "careers.company.com") and no DM invitation:
    # it is a standard job post / listing.
    if re.search(r"\b(apply (?:at|online|via|through)|careers?\.[a-z0-9\.\-]+)\b", t) and not re.search(r"\b(dm me|reach out directly|send message|message me)\b", t):
        match = re.search(r"\b(apply (?:at|online|via|through)|careers?\.[a-z0-9\.\-]+)\b", t)
        return ("GENERAL_JOB_POST", 0.50, f"Standard job post directing to online application: '{match.group(0)}'.")

    # 3. Hiring announcement (team/company hiring announcement)
    hiring_patterns = [
        r"\b(we are hiring|my team is hiring|i am hiring|our team has an opening)\b",
        r"\b([a-z0-9\.\-]+ is hiring|now hiring|hiring for multiple|startup is hiring)\b",
        r"\b(excited to announce (?:that )?(?:we are|our|startup)?\s*hiring)\b",
        r"\b(dm (?:me )?if interested|reach out directly if interested|interested candidates can dm)\b"
    ]
    for pat in hiring_patterns:
        match = re.search(pat, t)
        if match:
            return ("HIRING_ANNOUNCEMENT", 0.70, f"Team hiring announcement verified: '{match.group(0)}'.")

    # 4. General job post (advertisement, corporate announcement, application instructions)
    general_patterns = [
        r"\b(role open|job opening|job post|job description|apply here|apply now|recruiting for)\b",
    ]
    for pat in general_patterns:
        match = re.search(pat, t)
        if match:
            return ("GENERAL_JOB_POST", 0.35, f"General job posting verified: '{match.group(0)}'.")

    return ("UNCLEAR", 0.10, "Insufficient evidence to classify referral availability.")


class HeuristicIntelligenceEngine(BaseLLMClient):
    """Deterministic rule-based AI engine that operates with zero API cost and 100% offline reliability."""

    async def extract_and_classify(self, text: str, title: str, context: dict) -> AIExtractionResult:
        full_text = f"{title}\n{text}".strip()
        skills = _detect_skills(full_text)
        cat = context.get("category_hint") or "internships"

        ref_class, ref_conf, ref_note = _detect_referral_classification(full_text)

        # Check graduation year restrictions
        grad_year_match = re.search(r"\b(202[4-9]|2030)\s*(batch|graduates?|passouts?|only)\b", full_text, re.IGNORECASE)
        grad_req = grad_year_match.group(0) if grad_year_match else None

        # Check experience requirement
        exp_match = re.search(r"(\d+[\-\+]?\s*(?:to\s*\d+)?\s*(?:years?|yrs?))\s*(?:of\s+)?experience", full_text, re.IGNORECASE)
        exp_req = exp_match.group(0) if exp_match else None

        # Check location
        is_remote = bool(re.search(r"\b(remote|work from home|wfh)\b", full_text, re.IGNORECASE))
        is_hybrid = bool(re.search(r"\b(hybrid)\b", full_text, re.IGNORECASE))

        loc = "Remote" if is_remote else ("Hybrid" if is_hybrid else "Not specified")
        if re.search(r"\b(india|bangalore|bengaluru|hyderabad|coimbatore|chennai|pune|mumbai|delhi|gurgaon|noida)\b", full_text, re.IGNORECASE):
            loc = "India" if is_remote else f"India ({loc})"

        return AIExtractionResult(
            category=cat,
            role_or_title=title[:250],
            organization=context.get("organization") or "Not specified",
            location=loc,
            is_remote=is_remote,
            is_hybrid=is_hybrid,
            deadline=None,
            referral_classification=ref_class,
            referral_confidence=ref_conf,
            referral_instructions=ref_note,
            referral_evidence_excerpt=ref_note,
            required_skills=skills[:8],
            graduation_year_requirement=grad_req,
            experience_requirement=exp_req,
        )

    async def evaluate_eligibility_and_score(
        self, candidate_profile: dict, opportunity_data: dict, weights: dict
    ) -> tuple[AIEligibilityResult, AIScoringResult]:
        candidate_skills = {s.lower() for s in candidate_profile.get("skills", [])}
        opp_skills = [s.lower() for s in opportunity_data.get("required_skills", [])]
        matched_skills = [s for s in opp_skills if any(cs in s or s in cs for cs in candidate_skills)]
        missing_skills = [s for s in opp_skills if s not in matched_skills]

        cand_grad_year = candidate_profile.get("graduation_year", 2028)
        grad_req = opportunity_data.get("graduation_year_requirement") or ""
        exp_req = opportunity_data.get("experience_requirement") or ""
        desc_lower = (opportunity_data.get("description") or "").lower()

        disqualifying = []
        questions = []
        status = "Eligible"

        # Check graduation year conflict
        if grad_req:
            allowed_years = [int(y) for y in re.findall(r"\b(202[4-9]|2030)\b", grad_req)]
            if allowed_years and cand_grad_year not in allowed_years:
                disqualifying.append(
                    f"Graduation year mismatch: requires {grad_req}, candidate graduates in {cand_grad_year}."
                )

        # Check experience conflict (Candidate is a 3rd year student)
        if exp_req:
            exp_nums = [int(n) for n in re.findall(r"\b(\d+)\b", exp_req)]
            if exp_nums and max(exp_nums) >= 3 and "intern" not in opportunity_data.get("category", ""):
                disqualifying.append(
                    f"Mandatory experience required: {exp_req} (candidate is currently an undergraduate student)."
                )

        # Check senior positions conflict
        title_lower = (opportunity_data.get("title") or "").lower()
        senior_title_pattern = r"\b(senior|sr\.?|lead|staff|principal|director|head of|vp|vice president|architect|engineering manager)\b"
        is_senior_title = bool(re.search(senior_title_pattern, title_lower))
        senior_exp_pattern = r"\b([4-9]|\d{2})\+?\s*(?:years?|yrs?)\b"
        has_senior_exp = bool(re.search(senior_exp_pattern, exp_req or desc_lower[:800]))

        if (is_senior_title or has_senior_exp) and "intern" not in title_lower and "intern" not in opportunity_data.get("category", ""):
            disqualifying.append(
                f"Role targets senior/experienced professionals ({opportunity_data.get('title')}); candidate is a 2028 undergraduate."
            )

        # Immediate joining requirement flag
        if re.search(r"\b(immediate joiner|can join immediately|available immediately)\b", desc_lower):
            questions.append("Requires immediate joining. Verify if student schedule / college NOC permits.")

        if disqualifying:
            status = "Not eligible"
        elif missing_skills and len(missing_skills) > len(matched_skills):
            status = "Potentially eligible"
            questions.append(f"Missing verified skills: {', '.join(missing_skills[:4])}")
        elif questions:
            status = "Likely eligible — verify missing information"

        # --- Component Scoring ---
        # 1. Skill Score (0 - 100)
        skill_score = (len(matched_skills) / max(len(opp_skills), 1)) * 100 if opp_skills else 70.0
        # 2. Eligibility Score (0 - 100)
        elig_score = 0.0 if status == "Not eligible" else (65.0 if status == "Potentially eligible" else 95.0)
        # 3. Role Relevance
        pos = candidate_profile.get("target_career_positioning", "AI Engineer").lower()
        title_lower = opportunity_data.get("title", "").lower()
        relevance_score = 95.0 if any(k in title_lower for k in ["ai", "machine learning", "python", "nlp", "genai", "deep learning"]) else 65.0
        
        # Intern / Student / 2028 batch boost
        is_student_friendly = any(k in title_lower or k in desc_lower[:500] for k in ["intern", "internship", "fresher", "trainee", "student", "2028", "pre-final", "undergraduate", "campus", "scholarship", "hackathon"])
        if is_student_friendly and status != "Not eligible":
            relevance_score = min(100.0, relevance_score + 10.0)
            elig_score = min(100.0, elig_score + 5.0)

        # 4. Location Score (Indian candidate: Coimbatore, TN, Bangalore, Hyderabad, Chennai, Pune, Mumbai, Delhi-NCR, Remote)
        loc_str = (opportunity_data.get("location") or "").lower()
        is_rem = opportunity_data.get("is_remote", False) or "remote" in loc_str
        indian_cities = [
            "coimbatore", "tamil nadu", "bengaluru", "bangalore", "chennai",
            "hyderabad", "pune", "mumbai", "delhi", "noida", "gurgaon", "gurugram", "india"
        ]
        is_indian_loc = any(c in loc_str for c in indian_cities)

        if "coimbatore" in loc_str or "tamil nadu" in loc_str:
            location_score = 100.0  # Home institution region (Bannari Amman Institute of Technology)
        elif is_rem or is_indian_loc:
            location_score = 95.0
        elif any(f in loc_str for f in ["us", "usa", "united states", "uk", "germany", "europe", "london", "canada", "singapore"]):
            location_score = 30.0  # Onsite abroad role without remote option
        else:
            location_score = 65.0

        # 5. Referral & Freshness
        ref_class = opportunity_data.get("referral_classification") or ""
        ref_fresh_score = (
            95.0
            if ref_class == "CONFIRMED_REFERRAL_OFFER"
            else (75.0 if ref_class == "HIRING_ANNOUNCEMENT" else 50.0)
        )

        # Configurable Weighted Overall
        w_skill = weights.get("skill_match", 0.30)
        w_elig = weights.get("eligibility_match", 0.25)
        w_rel = weights.get("role_relevance", 0.20)
        w_loc = weights.get("location_preference", 0.10)
        w_ref = weights.get("referral_freshness", 0.15)

        overall = (
            (skill_score * w_skill)
            + (elig_score * w_elig)
            + (relevance_score * w_rel)
            + (location_score * w_loc)
            + (ref_fresh_score * w_ref)
        )
        if status == "Not eligible":
            overall = min(overall, 45.0)

        matched_reqs = [f"Matches target positioning: {pos}"]
        if matched_skills:
            matched_reqs.append(f"Skills matched: {', '.join(matched_skills)}")

        elig_summary = (
            f"Candidate meets requirements for {opportunity_data.get('title')}. "
            f"Skills matched: {len(matched_skills)}/{len(opp_skills) or 1}."
            if status != "Not eligible"
            else f"Disqualified due to: {'; '.join(disqualifying)}"
        )

        eligibility_result = AIEligibilityResult(
            status=status,
            matched_requirements=matched_reqs,
            missing_requirements=missing_skills,
            disqualifying_requirements=disqualifying,
            verification_questions=questions,
            summary=elig_summary,
        )

        opp_type = (opportunity_data.get("opportunity_type") or "").upper()
        if opp_type == "RESEARCH_PAPER":
            action = "Read research preprint / study architecture"
        elif status == "Not eligible":
            action = "Review disqualifying requirements"
        elif ref_class in {"CONFIRMED_REFERRAL_OFFER", "HIRING_ANNOUNCEMENT"}:
            action = "Request employee referral with tailored pitch"
        else:
            action = "Review opportunity details and apply"

        scoring_result = AIScoringResult(
            overall_score=round(overall, 1),
            skill_score=round(skill_score, 1),
            eligibility_score=round(elig_score, 1),
            relevance_score=round(relevance_score, 1),
            location_score=round(location_score, 1),
            referral_freshness_score=round(ref_fresh_score, 1),
            explanation=f"Scored {overall:.1f}/100 based on {len(matched_skills)} matching core skills and {status.lower()} eligibility.",
            recommended_action=action,
        )

        return eligibility_result, scoring_result

    async def draft_message(
        self, candidate_profile: dict, opportunity_data: dict, draft_type: str, custom_context: str | None = None
    ) -> AIDraftMessageResult:
        name = candidate_profile.get("full_name", "Kanish K")
        college = candidate_profile.get("institution", "Bannari Amman Institute of Technology")
        target_role = opportunity_data.get("title", "the open role")
        company = opportunity_data.get("organization", "your team")
        contact_name = opportunity_data.get("contact_name") or "there"

        # Projects strictly verified from candidate profile
        key_project = "Smart India Hackathon winning Digital Twin project and NLP dispatch framework"

        if draft_type == "connection_request":
            # LinkedIn connection limit is <= 300 characters
            subject = None
            body = (
                f"Hi {contact_name}, I'm Kanish, a 3rd-year CS student at {college} exploring {target_role} roles at {company}. "
                f"I've worked extensively on Python and AI projects. I'd love to connect and follow your work!"
            )
            if len(body) > 300:
                body = body[:297] + "..."
        elif draft_type == "referral_request":
            subject = f"Inquiry regarding Referral for {target_role} at {company}"
            body = (
                f"Dear {contact_name},\n\n"
                f"I hope this message finds you well. I am a 3rd-year Computer Science student at {college} graduating in 2028, "
                f"actively targeting AI and backend engineering opportunities.\n\n"
                f"I noticed the {target_role} opening at {company} and believe my technical background aligns well with the team's work. "
                f"Recently, I built {key_project} using Python, FastAPI, and machine learning models.\n\n"
                f"If you consider my profile a potential fit, would you be open to providing a referral for this opening? "
                f"I would be glad to share my resume and relevant project demos for your review.\n\n"
                f"Thank you for your time and guidance.\n\n"
                f"Best regards,\n{name}"
            )
        elif draft_type == "recruiter_outreach":
            subject = f"Candidate Application: {target_role} - {name}"
            body = (
                f"Hi {contact_name},\n\n"
                f"I hope you are having a productive week. I am reaching out to express my strong interest in the {target_role} role at {company}.\n\n"
                f"As a CS student at {college} focused on AI and Python development, I have built practical systems including our {key_project}. "
                f"My focus is on developing robust, production-ready AI solutions.\n\n"
                f"Could you let me know if applications for this cohort are currently being reviewed? I would be delighted to share my resume.\n\n"
                f"Warm regards,\n{name}"
            )
        elif draft_type == "follow_up":
            subject = f"Following up: {target_role} inquiry - {name}"
            body = (
                f"Hi {contact_name},\n\n"
                f"I wanted to briefly follow up on my earlier note regarding the {target_role} opening at {company}. "
                f"I recognize how busy your schedule must be, and I wanted to reiterate my enthusiasm for contributing to the team.\n\n"
                f"Please let me know if any additional details or code samples would be helpful.\n\n"
                f"Thank you again for your consideration,\n{name}"
            )
        else:
            subject = f"Thank you - {target_role} conversation"
            body = (
                f"Hi {contact_name},\n\n"
                f"Thank you so much for taking the time to connect regarding {company}. I truly appreciate your insights and support!\n\n"
                f"Best regards,\n{name}"
            )

        return AIDraftMessageResult(draft_type=draft_type, subject=subject, body=body)

    async def analyze_reply(
        self, reply_text: str, opportunity_data: dict | None, candidate_profile: dict
    ) -> AIReplyAnalysisResult:
        t = reply_text.lower()
        if any(k in t for k in ["send your resume", "share your cv", "send over your resume", "drop your resume"]):
            return AIReplyAnalysisResult(
                classification="Resume requested",
                explanation="The recipient is interested and has explicitly requested your resume.",
                recommended_next_step="Send your updated resume immediately with a polite, professional reply highlighting your relevant AI projects.",
                suggested_response="Hi! Thank you for the positive response. Please find attached my updated resume. I have highlighted my work on Python and GenAI. Looking forward to your thoughts!",
                suggested_follow_up_days=3,
            )
        if any(k in t for k in ["happy to refer", "submitted the referral", "referred you", "can refer"]):
            return AIReplyAnalysisResult(
                classification="Referral possible",
                explanation="The employee has offered or initiated a referral.",
                recommended_next_step="Acknowledge the referral with gratitude, confirm the requisition ID, and update tracking status to REFERRAL_RECEIVED.",
                suggested_response="Thank you so much for supporting my application with a referral! I really appreciate your time. I will keep you posted on my progress.",
                suggested_follow_up_days=7,
            )
        if any(k in t for k in ["apply on the portal", "apply online", "careers page", "apply via the link"]):
            return AIReplyAnalysisResult(
                classification="Apply through official portal",
                explanation="The contact advised routing your application directly through the official career portal.",
                recommended_next_step="Submit your official application on the portal, then send a polite confirmation note to this contact.",
                suggested_response="Thank you for the guidance! I will submit my application directly through the official portal today. Thank you for your time.",
                suggested_follow_up_days=5,
            )
        if any(k in t for k in ["not hiring", "filled the position", "no openings", "cannot refer", "unfortunately"]):
            return AIReplyAnalysisResult(
                classification="Rejection",
                explanation="The recipient indicated no current openings or inability to assist at this moment.",
                recommended_next_step="Respond gracefully, thank them for their time, and keep the connection warm for future opportunities.",
                suggested_response="Thank you for letting me know. I truly appreciate your time and wish you and the team continued success. Let's stay connected for future opportunities!",
                suggested_follow_up_days=None,
            )

        return AIReplyAnalysisResult(
            classification="Unclear response",
            explanation="The response does not explicitly commit to next steps.",
            recommended_next_step="Send a gentle clarifying message to confirm next steps.",
            suggested_response="Thank you for getting back to me! Please let me know if there are any specific details or materials I can provide.",
            suggested_follow_up_days=4,
        )

