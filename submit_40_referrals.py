#!/usr/bin/env python3
"""
Script to submit 40 diverse candidate referrals to the Tangentia Referral Portal.
Uses very few common employees (@tangentia.com) while each referral candidate has
distinct personal details, experience, position, and country-coded phone number.
"""

import sys
import time
import httpx

API_BASE = "https://tangentia-referral-api.azurewebsites.net/api"

# 5 common employees at Tangentia
EMPLOYEES = [
    {
        "name": "Sarah Jenkins",
        "email": "sarah.jenkins@tangentia.com",
        "phone": "+1 416 555 0123",
    },
    {
        "name": "Arun Kumar",
        "email": "arun.kumar@tangentia.com",
        "phone": "+91 98201 45678",
    },
    {
        "name": "David Miller",
        "email": "david.miller@tangentia.com",
        "phone": "+1 647 889 2314",
    },
    {
        "name": "Priya Sharma",
        "email": "priya.sharma@tangentia.com",
        "phone": "+91 98450 11223",
    },
    {
        "name": "Rohit Verma",
        "email": "rohit.verma@tangentia.com",
        "phone": "+91 99887 76655",
    },
]

# 40 distinct candidates
CANDIDATES = [
    # 1 - 8 (Referred by Sarah Jenkins)
    {
        "emp_idx": 0,
        "name": "Michael Chen",
        "email": "michael.chen.dev@gmail.com",
        "phone": "+1 416 302 4491",
        "position_id": "job-001",
        "years": 5.5,
        "rel": "Former Colleague",
        "note": "Exceptional Python backend engineer with extensive FastAPI and microservices design experience at a high-growth fintech.",
    },
    {
        "emp_idx": 0,
        "name": "Emily Watson",
        "email": "emily.watson.cloud@outlook.com",
        "phone": "+1 647 912 8840",
        "position_id": "job-003",
        "years": 8.0,
        "rel": "Industry Peer",
        "note": "AWS certified Solutions Architect with deep Kubernetes, Terraform, and cloud networking implementation track record.",
    },
    {
        "emp_idx": 0,
        "name": "Lucas Tremblay",
        "email": "lucas.tremblay.tech@gmail.com",
        "phone": "+1 514 821 7733",
        "position_id": "cats-16849726",
        "years": 4.0,
        "rel": "Former Colleague",
        "note": "Solid AWS sysops and cloud automation background. Expert in IAM, VPCs, and serverless architectures.",
    },
    {
        "emp_idx": 0,
        "name": "Sophia Rodriguez",
        "email": "sophia.rodriguez.ai@gmail.com",
        "phone": "+1 647 500 1289",
        "position_id": "job-002",
        "years": 3.5,
        "rel": "Mentee",
        "note": "Brilliant machine learning researcher and engineer. Built RAG pipelines and vector database evaluations in PyTorch.",
    },
    {
        "emp_idx": 0,
        "name": "James MacLeod",
        "email": "james.macleod.arch@outlook.com",
        "phone": "+1 416 499 6620",
        "position_id": "cats-16699887",
        "years": 11.0,
        "rel": "Industry Peer",
        "note": "Proven Senior Business Architect with extensive banking transformation experience and enterprise business modeling skills.",
    },
    {
        "emp_idx": 0,
        "name": "Chloe Lefebvre",
        "email": "chloe.lefebvre.front@gmail.com",
        "phone": "+1 438 901 3321",
        "position_id": "job-004",
        "years": 6.0,
        "rel": "Former Colleague",
        "note": "Senior React/TypeScript specialist. Created accessible component libraries and state management architectures.",
    },
    {
        "emp_idx": 0,
        "name": "Liam Gallagher",
        "email": "liam.gallagher.uk@gmail.com",
        "phone": "+44 7700 900142",
        "position_id": "job-001",
        "years": 4.5,
        "rel": "Ex-Team Member",
        "note": "High-throughput asynchronous Python developer, skilled with Celery, Redis caching, and PostgreSQL schema optimization.",
    },
    {
        "emp_idx": 0,
        "name": "Olivia Smith",
        "email": "olivia.smith.ca@outlook.com",
        "phone": "+1 905 441 5562",
        "position_id": "cats-16850937",
        "years": 3.0,
        "rel": "College Alum",
        "note": "Experienced RPA builder specializing in Microsoft Power Automate Desktop and Cloud flows.",
    },

    # 9 - 17 (Referred by Arun Kumar)
    {
        "emp_idx": 1,
        "name": "Vikram Malhotra",
        "email": "vikram.malhotra.rpa@gmail.com",
        "phone": "+91 98200 44112",
        "position_id": "cats-16855742",
        "years": 4.0,
        "rel": "Former Colleague",
        "note": "4+ years of hands-on Document Automation and RPA development with UiPath and Automation Anywhere Enterprise.",
    },
    {
        "emp_idx": 1,
        "name": "Ananya Kulkarni",
        "email": "ananya.kulkarni.bot@gmail.com",
        "phone": "+91 98451 22334",
        "position_id": "cats-16855743",
        "years": 3.5,
        "rel": "Ex-Team Member",
        "note": "Specialist in Advanced Process Automation (APA), OCR integration, and workflow orchestration for enterprise operations.",
    },
    {
        "emp_idx": 1,
        "name": "Karthik Sundaram",
        "email": "karthik.sundaram.aa@outlook.com",
        "phone": "+91 98840 99881",
        "position_id": "cats-16855744",
        "years": 5.0,
        "rel": "Former Colleague",
        "note": "Extensive expertise combining Automation Anywhere A360 bot building with custom Python scripting modules.",
    },
    {
        "emp_idx": 1,
        "name": "Sneha Patil",
        "email": "sneha.patil.rpa@gmail.com",
        "phone": "+91 83224 55667",
        "position_id": "cats-16846695",
        "years": 4.5,
        "rel": "Industry Peer",
        "note": "Led several enterprise RPA deployments using Automation Anywhere and custom Python automation libraries.",
    },
    {
        "emp_idx": 1,
        "name": "Nikhil Deshpande",
        "email": "nikhil.deshpande.dev@gmail.com",
        "phone": "+91 98221 77665",
        "position_id": "cats-16850937",
        "years": 3.0,
        "rel": "Mentee",
        "note": "Certified Microsoft Power Platform developer, experienced in Power Automate desktop bots, APIs, and Dataverse.",
    },
    {
        "emp_idx": 1,
        "name": "Pooja Hegde",
        "email": "pooja.hegde.cloud@outlook.com",
        "phone": "+91 94480 33445",
        "position_id": "cats-16849726",
        "years": 4.0,
        "rel": "Former Colleague",
        "note": "Strong AWS cloud engineering expertise with Terraform, CloudWatch, ECS, and Linux systems administration.",
    },
    {
        "emp_idx": 1,
        "name": "Gaurav Joshi",
        "email": "gaurav.joshi.auto@gmail.com",
        "phone": "+91 99701 23456",
        "position_id": "cats-16855742",
        "years": 5.0,
        "rel": "Former Colleague",
        "note": "Demonstrated track record delivering end-to-end intelligent document processing bots for global logistics clients.",
    },
    {
        "emp_idx": 1,
        "name": "Tanvi Sawant",
        "email": "tanvi.sawant.tech@gmail.com",
        "phone": "+91 83227 88990",
        "position_id": "job-004",
        "years": 4.0,
        "rel": "College Alum",
        "note": "Talented frontend engineer with great design taste and deep modern React, Tailwind, and TypeScript capability.",
    },
    {
        "emp_idx": 1,
        "name": "Aditya Rao",
        "email": "aditya.rao.backend@outlook.com",
        "phone": "+91 98452 66778",
        "position_id": "job-001",
        "years": 6.5,
        "rel": "Former Colleague",
        "note": "Seasoned backend specialist, strong in API architecture, async event-driven queues, and SQL performance tuning.",
    },

    # 18 - 25 (Referred by David Miller)
    {
        "emp_idx": 2,
        "name": "Alexander Wright",
        "email": "alex.wright.architect@gmail.com",
        "phone": "+1 416 881 2234",
        "position_id": "cats-16699887",
        "years": 12.0,
        "rel": "Former Colleague",
        "note": "Senior Enterprise Business Architect with 12 years guiding C-suite stakeholders through large-scale digitalization.",
    },
    {
        "emp_idx": 2,
        "name": "Jessica Taylor",
        "email": "jessica.taylor.cloud@outlook.com",
        "phone": "+1 647 332 9901",
        "position_id": "job-003",
        "years": 9.5,
        "rel": "Industry Peer",
        "note": "Enterprise Cloud Solutions Architect who led multi-cloud migrations on AWS and Azure with zero unplanned downtime.",
    },
    {
        "emp_idx": 2,
        "name": "Marcus Aurelius Campbell",
        "email": "marcus.campbell.dev@gmail.com",
        "phone": "+1 416 774 1109",
        "position_id": "job-001",
        "years": 7.0,
        "rel": "Former Colleague",
        "note": "Strong background in building secure financial messaging gateways with Python, Docker, and REST/gRPC.",
    },
    {
        "emp_idx": 2,
        "name": "Tariq Mansoor",
        "email": "tariq.mansoor.ae@gmail.com",
        "phone": "+971 50 123 4567",
        "position_id": "cats-16699887",
        "years": 10.0,
        "rel": "Industry Peer",
        "note": "Enterprise business architect based in Dubai, experienced in supply chain, EDI, and global logistics workflows.",
    },
    {
        "emp_idx": 2,
        "name": "Natasha Romanova",
        "email": "natasha.romanova.fe@gmail.com",
        "phone": "+1 647 220 9845",
        "position_id": "job-004",
        "years": 7.5,
        "rel": "Former Colleague",
        "note": "Frontend Lead who specializes in design systems, micro-frontends, web accessibility, and performance optimization.",
    },
    {
        "emp_idx": 2,
        "name": "Daniel Kim",
        "email": "daniel.kim.aws@outlook.com",
        "phone": "+1 416 905 4488",
        "position_id": "cats-16849726",
        "years": 5.0,
        "rel": "Mentee",
        "note": "Hands-on AWS engineer with solid experience in CloudFormation, Lambda, API Gateway, and automated CI/CD pipelines.",
    },
    {
        "emp_idx": 2,
        "name": "Hannah Abbott",
        "email": "hannah.abbott.rpa@gmail.com",
        "phone": "+44 7911 123456",
        "position_id": "cats-16850937",
        "years": 4.0,
        "rel": "Former Colleague",
        "note": "London-based Power Automate specialist who automated over 50 mission-critical back-office operational flows.",
    },
    {
        "emp_idx": 2,
        "name": "Gabriel Santos",
        "email": "gabriel.santos.ai@gmail.com",
        "phone": "+1 647 662 1190",
        "position_id": "job-002",
        "years": 4.0,
        "rel": "Former Colleague",
        "note": "AI engineer skilled in LangChain, LangGraph, agentic loops, and production fine-tuning of open-source models.",
    },

    # 26 - 33 (Referred by Priya Sharma)
    {
        "emp_idx": 3,
        "name": "Sameer Sengupta",
        "email": "sameer.sengupta.ml@gmail.com",
        "phone": "+91 98301 22998",
        "position_id": "job-002",
        "years": 6.0,
        "rel": "Former Colleague",
        "note": "Senior ML Engineer with multiple papers published. Expert in computer vision, transformer architectures, and TensorRT.",
    },
    {
        "emp_idx": 3,
        "name": "Meera Nambiar",
        "email": "meera.nambiar.ai@gmail.com",
        "phone": "+91 94470 12345",
        "position_id": "job-002",
        "years": 4.5,
        "rel": "Mentee",
        "note": "Outstanding data scientist and LLM developer who built agentic evaluation pipelines and automated prompt tuning.",
    },
    {
        "emp_idx": 3,
        "name": "Kunal Singhania",
        "email": "kunal.singhania.dev@outlook.com",
        "phone": "+91 98110 55443",
        "position_id": "job-001",
        "years": 5.0,
        "rel": "Former Colleague",
        "note": "Full-stack and backend engineer with strong Python FastAPI, async SQLAlchemy, and Redis experience.",
    },
    {
        "emp_idx": 3,
        "name": "Divya Krishnan",
        "email": "divya.krishnan.front@gmail.com",
        "phone": "+91 98410 77889",
        "position_id": "job-004",
        "years": 5.5,
        "rel": "Former Colleague",
        "note": "Lead frontend developer with extensive React 19, TypeScript, and responsive UI architectural experience.",
    },
    {
        "emp_idx": 3,
        "name": "Rahul Kapoor",
        "email": "rahul.kapoor.rpa@gmail.com",
        "phone": "+91 98205 33441",
        "position_id": "cats-16855744",
        "years": 4.0,
        "rel": "College Alum",
        "note": "Skilled Automation Anywhere A360 automation developer with strong Python algorithm scripting skills.",
    },
    {
        "emp_idx": 3,
        "name": "Ayesha Siddiqui",
        "email": "ayesha.siddiqui.auto@gmail.com",
        "phone": "+971 52 987 6543",
        "position_id": "cats-16855743",
        "years": 4.5,
        "rel": "Industry Peer",
        "note": "UAE-based intelligent automation specialist with APA and document understanding workflow mastery.",
    },
    {
        "emp_idx": 3,
        "name": "Prashant Nair",
        "email": "prashant.nair.cloud@outlook.com",
        "phone": "+91 98460 88992",
        "position_id": "job-003",
        "years": 8.0,
        "rel": "Former Colleague",
        "note": "Senior Cloud Architect skilled in multi-region failover, AWS Well-Architected frameworks, and FinOps practices.",
    },
    {
        "emp_idx": 3,
        "name": "Bhavna Patel",
        "email": "bhavna.patel.rpa@gmail.com",
        "phone": "+91 98250 11447",
        "position_id": "cats-16846695",
        "years": 3.5,
        "rel": "Former Colleague",
        "note": "Specialist in Automation Anywhere A360 bot migration, credential vaults, and SAP automated data feeds.",
    },

    # 34 - 40 (Referred by Rohit Verma)
    {
        "emp_idx": 4,
        "name": "Arjun Chawla",
        "email": "arjun.chawla.fullstack@gmail.com",
        "phone": "+91 98100 22331",
        "position_id": "job-001",
        "years": 4.5,
        "rel": "Former Colleague",
        "note": "High-velocity backend developer with clean code habits, unit test discipline, and FastAPI production expertise.",
    },
    {
        "emp_idx": 4,
        "name": "Rhea D'Souza",
        "email": "rhea.dsouza.ui@gmail.com",
        "phone": "+91 83222 44556",
        "position_id": "job-004",
        "years": 5.0,
        "rel": "Former Colleague",
        "note": "Goa-based senior UI engineer with stunning portfolio in modern React, Vite, CSS design systems, and micro-interactions.",
    },
    {
        "emp_idx": 4,
        "name": "Varun Bhatt",
        "email": "varun.bhatt.rpa@outlook.com",
        "phone": "+91 97270 33221",
        "position_id": "cats-16855742",
        "years": 3.5,
        "rel": "Mentee",
        "note": "Fast-learning RPA and Document Automation developer with hands-on OCR model training and exception handling experience.",
    },
    {
        "emp_idx": 4,
        "name": "Siddharth Menon",
        "email": "siddharth.menon.aws@gmail.com",
        "phone": "+65 9123 4567",
        "position_id": "cats-16849726",
        "years": 5.0,
        "rel": "Industry Peer",
        "note": "Singapore-based Cloud Infrastructure Engineer with proven experience automating AWS infrastructure with Ansible and Terraform.",
    },
    {
        "emp_idx": 4,
        "name": "Pallavi Reddy",
        "email": "pallavi.reddy.power@gmail.com",
        "phone": "+91 98490 88776",
        "position_id": "cats-16850937",
        "years": 4.0,
        "rel": "College Alum",
        "note": "Microsoft Certified Power Automate developer who designed multi-stage approval flows and automated invoice reconciliations.",
    },
    {
        "emp_idx": 4,
        "name": "Devendra Tiwari",
        "email": "devendra.tiwari.aa@outlook.com",
        "phone": "+91 94150 99887",
        "position_id": "cats-16855744",
        "years": 4.5,
        "rel": "Former Colleague",
        "note": "Solid Automation Anywhere A360 automation engineer with strong custom Python DLL integration skills.",
    },
    {
        "emp_idx": 4,
        "name": "Ananya Sen",
        "email": "ananya.sen.ai@gmail.com",
        "phone": "+91 98310 44556",
        "position_id": "job-002",
        "years": 3.0,
        "rel": "Mentee",
        "note": "Passionate AI engineer skilled in prompt engineering, embeddings, semantic retrieval, and agent evaluation frameworks.",
    },
]


def make_pdf_resume(candidate_name: str, position_title: str) -> bytes:
    """Generate a valid PDF file with candidate details."""
    clean_name = candidate_name.replace("(", "").replace(")", "")
    clean_title = position_title.replace("(", "").replace(")", "")
    return f"""%PDF-1.4
1 0 obj
<<
  /Title (Resume - {clean_name})
  /Author ({clean_name})
  /Subject (Application for {clean_title} at Tangentia)
  /Creator (Tangentia Employee Referral System)
>>
endobj
2 0 obj
<<
  /Type /Catalog
  /Pages 3 0 R
>>
endobj
3 0 obj
<<
  /Type /Pages
  /Kids [4 0 R]
  /Count 1
>>
endobj
4 0 obj
<<
  /Type /Page
  /Parent 3 0 R
  /MediaBox [0 0 612 792]
>>
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000150 00000 n 
0000000200 00000 n 
0000000260 00000 n 
trailer
<<
  /Size 5
  /Root 2 0 R
>>
startxref
340
%%EOF""".encode("utf-8")


def main():
    client = httpx.Client(timeout=45.0)
    print(f"Starting submission of {len(CANDIDATES)} referrals to {API_BASE}/referrals...")
    print(f"Common Referring Employees ({len(EMPLOYEES)}):")
    for emp in EMPLOYEES:
        print(f"  - {emp['name']} <{emp['email']}> ({emp['phone']})")
    print("-" * 70)

    success_count = 0
    failed_count = 0

    for i, item in enumerate(CANDIDATES, 1):
        emp = EMPLOYEES[item["emp_idx"]]
        pdf_bytes = make_pdf_resume(item["name"], item["position_id"])
        file_name = f"{item['name'].lower().replace(' ', '_')}_resume.pdf"

        files = {
            "file": (file_name, pdf_bytes, "application/pdf")
        }
        data = {
            "candidate_name": item["name"],
            "candidate_email": item["email"],
            "candidate_phone": item["phone"],
            "referred_by_name": emp["name"],
            "referred_by": emp["name"],
            "referred_by_email": emp["email"],
            "employee_email": emp["email"],
            "referred_by_phone": emp["phone"],
            "employee_phone": emp["phone"],
            "position_id": item["position_id"],
            "years_of_experience": str(item["years"]),
            "relationship": item["rel"],
            "referral_note": item["note"],
            "candidate_consent": "true",
        }

        try:
            res = client.post(f"{API_BASE}/referrals", data=data, files=files)
            if res.status_code == 201:
                ref_json = res.json()
                success_count += 1
                print(f"[{i:02d}/40] SUCCESS: {ref_json['referral_number']} | {item['name']} ({item['phone']}) -> {ref_json.get('position_title', item['position_id'])} (by {emp['name']})")
            else:
                failed_count += 1
                print(f"[{i:02d}/40] FAILED ({res.status_code}): {item['name']} -> {res.text}")
        except Exception as e:
            failed_count += 1
            print(f"[{i:02d}/40] ERROR: {item['name']} -> {e}")

        # Small pause between requests to prevent network bursting
        time.sleep(0.3)

    print("-" * 70)
    print(f"Referral Submissions Finished: {success_count} Succeeded, {failed_count} Failed.")


if __name__ == "__main__":
    main()
