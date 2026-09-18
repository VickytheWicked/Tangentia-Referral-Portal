#!/usr/bin/env python3
"""
Script to simulate realistic HR recruitment lifecycle transitions:
- Multiple status transitions (Under Review, Shortlisted, Interview, Selected, Hired, Rejected)
- 4 verified hires across multiple departments
- HR notes and audit logging
"""

import sys
import time
import httpx

API = "https://tangentia-referral-api.azurewebsites.net/api"

def main():
    client = httpx.Client(timeout=30.0)

    # 1. Login as HR Admin
    login_res = client.post(f"{API}/auth/login", json={
        "email": "hr.lead@tangentia.com",
        "password": "TangentiaHR@2026"
    })
    if login_res.status_code != 200:
        print(f"Failed to login as HR Admin: {login_res.text}")
        sys.exit(1)

    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("HR Admin logged in successfully.")

    # 2. Fetch all referrals
    refs = client.get(f"{API}/hr/referrals?limit=100", headers=headers).json()
    by_name = {r["candidate_name"]: r for r in refs}
    print(f"Found {len(refs)} total referrals in system.")

    # Define transitions
    transitions = [
        # HIRES (4)
        {
            "name": "Michael Chen",
            "stages": [
                ("Under Review", "Initial profile screening completed. Strong Python background."),
                ("Interview", "Technical round scheduled with Engineering Director."),
                ("Selected", "Cleared architecture and coding rounds with top ratings."),
                ("Hired", "Offer accepted. Joining as Senior Backend Developer on Oct 1st!"),
            ],
            "note": "Candidate negotiated standard package. Background verification completed. Laptop ordered."
        },
        {
            "name": "Vikram Malhotra",
            "stages": [
                ("Under Review", "Reviewed RPA & DA certifications. Matches client requirements."),
                ("Interview", "Completed UiPath live automation assessment with 95% score."),
                ("Selected", "Unanimous pass from the intelligent automation panel."),
                ("Hired", "Offer letter signed. Start date confirmed for Oct 15th."),
            ],
            "note": "Assigned to the North American banking logistics RPA delivery pod."
        },
        {
            "name": "Sameer Sengupta",
            "stages": [
                ("Under Review", "Profile shortlisted by AI Innovation Lab head."),
                ("Interview", "Deep dive on transformer architectures and LLM evaluation."),
                ("Selected", "Outstanding research and production deployment background."),
                ("Hired", "Offer accepted. Joining as Senior AI Engineer."),
            ],
            "note": "Will lead enterprise RAG implementation for key retail customer."
        },
        {
            "name": "Jessica Taylor",
            "stages": [
                ("Under Review", "AWS Architect credentials verified."),
                ("Interview", "Presented cloud modernization case study to executive panel."),
                ("Selected", "Selected for Senior Cloud Solutions Architect opening."),
                ("Hired", "Official offer accepted. Joining Toronto headquarters."),
            ],
            "note": "Will spearhead Tangentia Cloud Advisory practice."
        },

        # SELECTED (5)
        {
            "name": "Lucas Tremblay",
            "stages": [
                ("Under Review", "Screened for AWS DevOps skills."),
                ("Interview", "Completed technical interview with Cloud Lead."),
                ("Selected", "Candidate selected. Offer letter under preparation."),
            ],
            "note": "Compensation review in progress with HR."
        },
        {
            "name": "Ananya Kulkarni",
            "stages": [
                ("Under Review", "APA portfolio reviewed."),
                ("Interview", "Passed automation architecture test."),
                ("Selected", "Selected for Intelligent Automation team."),
            ],
            "note": "Drafting offer letter."
        },
        {
            "name": "Alexander Wright",
            "stages": [
                ("Under Review", "Senior architect profile reviewed."),
                ("Interview", "Executive interview with VP of Operations."),
                ("Selected", "Selected for Senior Business Architect."),
            ],
            "note": "Waiting on candidate sign-off on offer terms."
        },
        {
            "name": "Meera Nambiar",
            "stages": [
                ("Under Review", "LLM evaluation experience matches needs."),
                ("Interview", "Cracked technical interview on prompt evaluation pipelines."),
                ("Selected", "Selected for AI team."),
            ],
            "note": "Awaiting final approval."
        },
        {
            "name": "Rhea D'Souza",
            "stages": [
                ("Under Review", "UI/UX portfolio inspected. Very impressive work."),
                ("Interview", "Live frontend coding session completed smoothly."),
                ("Selected", "Selected as Frontend Lead."),
            ],
            "note": "Fast-tracked for Goa engineering center."
        },

        # INTERVIEW (6)
        {
            "name": "Sophia Rodriguez",
            "stages": [
                ("Under Review", "Screened resume."),
                ("Interview", "Technical round scheduled for Monday."),
            ],
            "note": None
        },
        {
            "name": "Karthik Sundaram",
            "stages": [
                ("Under Review", "Automation Anywhere experience checked."),
                ("Interview", "First round interview completed. Second round scheduled."),
            ],
            "note": None
        },
        {
            "name": "Natasha Romanova",
            "stages": [
                ("Under Review", "React 19 background verified."),
                ("Interview", "System design interview scheduled."),
            ],
            "note": None
        },
        {
            "name": "Divya Krishnan",
            "stages": [
                ("Under Review", "Reviewing frontend contributions."),
                ("Interview", "Interview scheduled with team lead."),
            ],
            "note": None
        },
        {
            "name": "Siddharth Menon",
            "stages": [
                ("Under Review", "Singapore credentials confirmed."),
                ("Interview", "Cloud infrastructure interview round."),
            ],
            "note": None
        },
        {
            "name": "Chloe Lefebvre",
            "stages": [
                ("Under Review", "Design system portfolio reviewed."),
                ("Interview", "Panel interview scheduled."),
            ],
            "note": None
        },

        # SHORTLISTED (7)
        {
            "name": "James MacLeod",
            "stages": [("Under Review", "Reviewing."), ("Shortlisted", "Shortlisted for interview.")],
            "note": None
        },
        {
            "name": "Sneha Patil",
            "stages": [("Under Review", "Reviewing."), ("Shortlisted", "Shortlisted for RPA role.")],
            "note": None
        },
        {
            "name": "Marcus Aurelius Campbell",
            "stages": [("Under Review", "Reviewing."), ("Shortlisted", "Shortlisted for backend.")],
            "note": None
        },
        {
            "name": "Rahul Kapoor",
            "stages": [("Under Review", "Reviewing."), ("Shortlisted", "Shortlisted for A360 role.")],
            "note": None
        },
        {
            "name": "Varun Bhatt",
            "stages": [("Under Review", "Reviewing."), ("Shortlisted", "Shortlisted for DA role.")],
            "note": None
        },
        {
            "name": "Liam Gallagher",
            "stages": [("Under Review", "Reviewing."), ("Shortlisted", "Shortlisted for Python role.")],
            "note": None
        },
        {
            "name": "Nikhil Deshpande",
            "stages": [("Under Review", "Reviewing."), ("Shortlisted", "Shortlisted for Power Automate.")],
            "note": None
        },

        # UNDER REVIEW (8)
        {
            "name": "Olivia Smith",
            "stages": [("Under Review", "Under initial review by HR recruiter.")],
            "note": None
        },
        {
            "name": "Pooja Hegde",
            "stages": [("Under Review", "Under initial review by HR recruiter.")],
            "note": None
        },
        {
            "name": "Tariq Mansoor",
            "stages": [("Under Review", "Under initial review by HR recruiter.")],
            "note": None
        },
        {
            "name": "Daniel Kim",
            "stages": [("Under Review", "Under initial review by HR recruiter.")],
            "note": None
        },
        {
            "name": "Kunal Singhania",
            "stages": [("Under Review", "Under initial review by HR recruiter.")],
            "note": None
        },
        {
            "name": "Ayesha Siddiqui",
            "stages": [("Under Review", "Under initial review by HR recruiter.")],
            "note": None
        },
        {
            "name": "Arjun Chawla",
            "stages": [("Under Review", "Under initial review by HR recruiter.")],
            "note": None
        },
        {
            "name": "Pallavi Reddy",
            "stages": [("Under Review", "Under initial review by HR recruiter.")],
            "note": None
        },

        # REJECTED (2)
        {
            "name": "Devendra Tiwari",
            "stages": [
                ("Under Review", "Reviewing."),
                ("Rejected", "Experience does not match current project timeline constraints."),
            ],
            "note": "Kept in talent pool for future openings."
        },
        {
            "name": "Hannah Abbott",
            "stages": [
                ("Under Review", "Reviewing."),
                ("Rejected", "Candidate accepted an alternative offer elsewhere."),
            ],
            "note": "Candidate withdrew candidacy due to location constraints."
        },
    ]

    print(f"\nProcessing {len(transitions)} candidates through realistic recruitment workflow...")

    for t in transitions:
        cand_name = t["name"]
        if cand_name not in by_name:
            print(f"Skipping {cand_name}: not found in referrals.")
            continue

        ref = by_name[cand_name]
        ref_id = ref["id"]

        for (st, comment) in t["stages"]:
            resp = client.put(f"{API}/hr/referrals/{ref_id}/status", json={
                "status": st,
                "comment": comment
            }, headers=headers)
            if resp.status_code == 200:
                print(f"  -> {cand_name}: Status updated to '{st}'")
            else:
                print(f"  FAILED updating {cand_name} to '{st}': {resp.text}")
            time.sleep(0.1)

        if t.get("note"):
            n_resp = client.post(f"{API}/hr/referrals/{ref_id}/notes", json={
                "note": t["note"]
            }, headers=headers)
            if n_resp.status_code == 201:
                print(f"     [Note added for {cand_name}]")

    print("\nWorkflow update complete!")

if __name__ == "__main__":
    main()
