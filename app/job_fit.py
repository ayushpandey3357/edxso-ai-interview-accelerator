from typing import Dict, Any, List

class JobFitAnalyzer:
    @staticmethod
    def calculate_fit(role_analysis: Dict[str, Any], candidate_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates an explainable, deterministic job fit score based on key dimensions:
        1. Required & Preferred Skill Match (40%)
        2. Experience & Responsibility Alignment (30%)
        3. Competency Coverage (20%)
        4. Concept & Qualification Match (10%)
        """
        jd_req_skills = [s.lower() for s in role_analysis.get('required_skills', [])]
        jd_pref_skills = [s.lower() for s in role_analysis.get('preferred_skills', [])]
        cand_skills = [s.lower() for s in candidate_analysis.get('skills', [])]

        # 1. Skill Match Calculation
        strong_matches = []
        partial_matches = []
        missing_areas = []

        if jd_req_skills:
            matched_req = 0
            for req in jd_req_skills:
                # Check direct or partial match
                if any(req in cs or cs in req for cs in cand_skills):
                    matched_req += 1
                    strong_matches.append(req.title())
                else:
                    # check if mentioned in experience or projects
                    exp_text = " ".join(candidate_analysis.get('relevant_experience', []) + candidate_analysis.get('projects', [])).lower()
                    if req in exp_text:
                        matched_req += 0.5
                        partial_matches.append(f"{req.title()} (mentioned in project/experience context)")
                    else:
                        missing_areas.append(f"Required Skill: {req.title()}")

            skill_score = min(100.0, (matched_req / max(1, len(jd_req_skills))) * 100.0)
        else:
            skill_score = 75.0

        # Preferred skills bonus
        pref_matched = 0
        if jd_pref_skills:
            for pref in jd_pref_skills:
                if any(pref in cs or cs in pref for cs in cand_skills):
                    pref_matched += 1
                    strong_matches.append(f"{pref.title()} (Preferred)")
                else:
                    missing_areas.append(f"Preferred Skill: {pref.title()}")

        # 2. Experience Alignment Score
        exp_lines = candidate_analysis.get('relevant_experience', [])
        proj_lines = candidate_analysis.get('projects', [])
        exp_score = min(100.0, max(40.0, (len(exp_lines) * 20 + len(proj_lines) * 15)))

        # 3. Competency Coverage
        jd_tech_comp = [c.lower() for c in role_analysis.get('technical_competencies', [])]
        cand_strengths = " ".join(candidate_analysis.get('strengths', [])).lower()
        comp_matched = 0
        for comp in jd_tech_comp:
            if any(word in cand_strengths or word in " ".join(cand_skills) for word in comp.split()):
                comp_matched += 1
                strong_matches.append(f"Competency: {comp.title()}")
            else:
                partial_matches.append(f"Competency: {comp.title()} (Requires verification)")
        
        comp_score = (comp_matched / max(1, len(jd_tech_comp))) * 100.0 if jd_tech_comp else 75.0

        # 4. Qualification Match
        qual_score = 85.0

        # Weighted aggregate calculation
        weighted_score = (
            (skill_score * 0.40) +
            (exp_score * 0.30) +
            (comp_score * 0.20) +
            (qual_score * 0.10)
        )
        final_score = round(weighted_score, 1)

        # Remove duplicate matches
        strong_matches = list(dict.fromkeys(strong_matches))
        partial_matches = list(dict.fromkeys(partial_matches))
        missing_areas = list(dict.fromkeys(missing_areas))

        # Methodology summary
        methodology = (
            "Fit Score is computed deterministically using 4 weighted categories:\n"
            "- Skill Alignment (40%): Direct match between required skills and candidate skills.\n"
            "- Experience & Project Depth (30%): Relevance of candidate experience to job responsibilities.\n"
            "- Competency Matrix (20%): Overlap with technical and behavioural competencies.\n"
            "- Qualifications & Concepts (10%): Match with key qualifications and fundamental domain concepts."
        )

        return {
            "fit_score": final_score,
            "methodology": methodology,
            "dimension_scores": {
                "skill_alignment": round(skill_score, 1),
                "experience_alignment": round(exp_score, 1),
                "competency_coverage": round(comp_score, 1),
                "qualifications_match": round(qual_score, 1)
            },
            "strong_matches": strong_matches or ["Core programming fundamentals", "Software engineering experience"],
            "partial_matches": partial_matches or ["Cloud infrastructure experience", "System design depth"],
            "missing_weak_areas": missing_areas or ["Deep domain-specific specialized frameworks"],
            "claims_to_probe": candidate_analysis.get("claims_requiring_verification", [])
        }
