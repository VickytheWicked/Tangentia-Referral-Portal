import html
import logging
import re
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy.orm import Session

from app.models.job_position import JobPosition
from app.models.referral import Referral, ReferralStatus

logger = logging.getLogger("referral_portal.cats_scraper")

CATS_BASE_URL = "https://tangentia.catsone.com"
CATS_GENERAL_PORTAL_URL = f"{CATS_BASE_URL}/careers/9463-General"
DEFAULT_TIMEOUT = 15.0


def clean_html(raw_html: str) -> str:
    """Convert raw HTML markup to clean, formatted plain text."""
    if not raw_html:
        return ""

    # Unescape first so that escaped tags (e.g., &lt;style&gt;) become standard tags
    text = html.unescape(raw_html)

    # Completely remove style and script tags and their contents
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Replace breaks and list items with newline structure
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "• ", text, flags=re.IGNORECASE)

    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Normalize whitespace while preserving bullet structure
    lines = [line.strip() for line in text.split("\n")]
    clean_lines: List[str] = []
    prev_blank = False

    for line in lines:
        if line:
            clean_lines.append(line)
            prev_blank = False
        elif not prev_blank:
            clean_lines.append("")
            prev_blank = True

    return "\n".join(clean_lines).strip()


def summarize_to_one_or_two_liner(text: str, title: str = "", location: str = "") -> str:
    """Condense a multi-paragraph job description into a clean, impactful 1-2 liner summary."""
    if not text:
        return f"Seeking a skilled {title} to join Tangentia's team in {location}." if title else "Open role at Tangentia."

    filtered_lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Skip pure section headers
        if re.match(r"^(key responsibilities|responsibilities|required skills|skills|job summary|role overview|position summary|position overview|overview|requirements|role\s*:|job description|role summary\s*:?):?$", line, re.IGNORECASE):
            continue
        cleaned = re.sub(r"^[•\-\*]\s*", "", line)
        if cleaned:
            filtered_lines.append(cleaned)

    combined = " ".join(filtered_lines)
    # Strip leading generic headers if embedded at start
    combined = re.sub(r"^(Role Overview|Role Summary|Position Overview|Job Summary|Job Description)\s*", "", combined, flags=re.IGNORECASE).strip()

    sentences = re.split(r"(?<=[.!?])\s+", combined)
    if len(sentences) >= 2 and len(sentences[0]) < 100:
        summary = f"{sentences[0]} {sentences[1]}"
    elif len(sentences) >= 1 and sentences[0]:
        summary = sentences[0]
    else:
        summary = combined[:180]

    # Cap length around 200 chars for a true 1-2 liner
    if len(summary) > 200:
        cut = summary[:197]
        last_space = cut.rfind(" ")
        if last_space > 130:
            summary = cut[:last_space] + "..."
        else:
            summary = cut + "..."

    return summary.strip()


def infer_department(title: str, description: str = "") -> str:
    """Intelligently infer department from job title and description."""
    t = title.lower()
    d = description.lower() if description else ""

    # 1. Primary classification by title
    if re.search(r"\b(rpa|automate|automation|power automate|a360)\b", t):
        return "Intelligent Automation"
    if re.search(r"\b(databricks|power bi|data|analytics|bi developer)\b", t):
        return "Data & Analytics"
    if re.search(r"\b(boomi|integration|aws|cloud|azure|devops|sre|infrastructure|it engineer)\b", t):
        return "Cloud & Integration"
    if re.search(r"\b(sap|fico|finance|accounting|testing lead)\b", t):
        return "Finance & Enterprise"
    if re.search(r"\b(sales|business development|account executive)\b", t):
        return "Global Sales"
    if re.search(r"\b(project manager|program manager|product manager|scrum master|architect - senior|business architect)\b", t):
        return "Project & Product Management"
    if re.search(r"\b(ai|machine learning|llm|deep learning)\b", t):
        return "AI Innovations"
    if re.search(r"\b(developer|engineer|software|java|spring boot|oms|frontend|backend)\b", t):
        return "Engineering"

    # 2. Fallback to description keywords
    if re.search(r"\b(rpa|automation anywhere|power automate)\b", d):
        return "Intelligent Automation"
    if re.search(r"\b(databricks|power bi)\b", d):
        return "Data & Analytics"
    if re.search(r"\b(boomi|aws|cloud|azure)\b", d):
        return "Cloud & Integration"
    if re.search(r"\b(sap|fico|finance)\b", d):
        return "Finance & Enterprise"

    return "Engineering"


def infer_employment_type(title: str, description: str = "") -> str:
    """Infer employment type (Full-time, Contract, Internship, Part-time) using regex word boundaries."""
    combined = f"{title} {description}".lower()
    if re.search(r"\b(contract|contractor|freelance|\d+\s*months?\s*contract)\b", combined):
        return "Contract"
    if re.search(r"\b(intern|internship|co-op)\b", combined):
        return "Internship"
    if re.search(r"\bpart[- ]time\b", combined):
        return "Part-time"
    return "Full-time"


def fetch_cats_job_listings(client: Optional[httpx.Client] = None) -> List[Dict[str, Any]]:
    """
    Fetch the Tangentia CATS Careers general portal page and extract all open positions.
    Returns a list of dictionaries with job metadata.
    """
    close_client = False
    if client is None:
        client = httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True)
        close_client = True

    try:
        response = client.get(CATS_GENERAL_PORTAL_URL)
        response.raise_for_status()

        row_regex = re.compile(
            r'<a class="table-row" href="(/careers/9463/jobs/(\d+)-[^"]+)"[^>]*>'
            r'.*?<div class="data-cell title-cell">([^<]+)</div>'
            r'.*?<div class="data-cell" data-label="Location">([^<]*)</div>',
            re.DOTALL,
        )

        matches = row_regex.findall(response.text)
        jobs: List[Dict[str, Any]] = []

        for url_path, cats_job_id, title_raw, loc_raw in matches:
            title = html.unescape(title_raw).strip()
            location = html.unescape(loc_raw).strip() or "Remote / Location Not Specified"
            jobs.append({
                "cats_job_id": cats_job_id,
                "portal_id": f"cats-{cats_job_id}",
                "title": title,
                "location": location,
                "url_path": url_path,
                "full_url": f"{CATS_BASE_URL}{url_path}",
            })

        logger.info(f"Successfully scraped {len(jobs)} jobs from Tangentia CATS Careers portal")
        return jobs
    finally:
        if close_client:
            client.close()


def fetch_cats_job_detail(url_path: str, client: Optional[httpx.Client] = None) -> Dict[str, Any]:
    """Fetch an individual job listing page and extract full description and metadata."""
    close_client = False
    if client is None:
        client = httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True)
        close_client = True

    try:
        detail_url = f"{CATS_BASE_URL}{url_path}" if url_path.startswith("/") else url_path
        resp = client.get(detail_url)
        resp.raise_for_status()

        desc_match = re.search(
            r'<div class="job-description">(.*?)(?:</div>\s*</div>\s*</div>\s*<aside>|<aside>)',
            resp.text,
            re.DOTALL,
        )

        if desc_match:
            raw_desc = desc_match.group(1)
            description = clean_html(raw_desc)
        else:
            # Fallback if structure varies
            meta_desc_match = re.search(r'<meta\s+name="description"\s+property="og:description"\s+content="([^"]+)"', resp.text)
            if meta_desc_match:
                description = html.unescape(meta_desc_match.group(1)).strip()
            else:
                description = "See Tangentia Careers portal for full role requirements and qualifications."

        return {
            "description": description,
        }
    finally:
        if close_client:
            client.close()


def scrape_all_cats_jobs(client: Optional[httpx.Client] = None) -> List[Dict[str, Any]]:
    """Scrape the main listing and fetch complete job descriptions for all postings."""
    close_client = False
    if client is None:
        client = httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True)
        close_client = True

    try:
        listings = fetch_cats_job_listings(client=client)
        detailed_jobs: List[Dict[str, Any]] = []

        for job in listings:
            try:
                detail = fetch_cats_job_detail(job["url_path"], client=client)
                full_text = detail.get("description", "").strip()
                job["description"] = full_text or summarize_to_one_or_two_liner(
                    detail.get("description", ""),
                    job["title"],
                    job["location"],
                )
            except Exception as e:
                logger.warning(f"Failed to fetch job detail for {job['title']} ({job['url_path']}): {e}")
                job["description"] = f"Opportunity for a {job['title']} to join our team in {job['location']}."

            job["department"] = infer_department(job["title"], job["description"])
            job["employment_type"] = infer_employment_type(job["title"], job["description"])
            detailed_jobs.append(job)

        return detailed_jobs
    finally:
        if close_client:
            client.close()


def sync_cats_jobs_with_db(
    db: Session,
    deactivate_missing: bool = False,
    client: Optional[httpx.Client] = None,
) -> Dict[str, Any]:
    """
    Scrape all jobs from Tangentia CATS Careers and synchronize with the database
    and Excel storage.

    Returns:
        Dict with keys: success, total_scraped, created_count, updated_count, deactivated_count, jobs
    """
    from app.services.excel import get_excel_service

    scraped_jobs = scrape_all_cats_jobs(client=client)
    created_count = 0
    updated_count = 0
    deactivated_count = 0
    synced_jobs: List[JobPosition] = []
    excel_svc = get_excel_service()

    scraped_ids = set()

    for item in scraped_jobs:
        job_id = item["portal_id"]
        scraped_ids.add(job_id)

        existing_job = db.query(JobPosition).filter(JobPosition.id == job_id).first()

        # Check if this position has any referral that was already hired
        has_hired = db.query(Referral).filter(
            Referral.position_id == job_id,
            Referral.status == ReferralStatus.HIRED.value,
        ).first() is not None

        # Position should only be active if it hasn't been filled/hired
        target_is_active = False if has_hired else True

        if existing_job:
            # Update fields if changed
            existing_job.title = item["title"]
            existing_job.department = item["department"]
            existing_job.location = item["location"]
            existing_job.employment_type = item["employment_type"]
            existing_job.description = item["description"]
            # Do NOT reactivate a position that has already been filled/hired
            existing_job.is_active = target_is_active
            updated_count += 1
            synced_jobs.append(existing_job)
        else:
            new_job = JobPosition(
                id=job_id,
                title=item["title"],
                department=item["department"],
                location=item["location"],
                employment_type=item["employment_type"],
                description=item["description"],
                is_active=target_is_active,
            )
            db.add(new_job)
            created_count += 1
            synced_jobs.append(new_job)

        # Persist to Excel workbook
        try:
            excel_svc.save_job_position({
                "id": job_id,
                "title": item["title"],
                "department": item["department"],
                "location": item["location"],
                "employment_type": item["employment_type"],
                "is_active": target_is_active,
                "description": item["description"],
            })
        except Exception as ex:
            logger.warning(f"Failed to persist synced job {job_id} to Excel: {ex}")

    # Deactivate CATS positions that have been filled/hired or are missing from live site
    existing_cats_jobs = db.query(JobPosition).filter(
        JobPosition.id.like("cats-%"),
        JobPosition.is_active == True,
    ).all()
    for j in existing_cats_jobs:
        has_hired_ref = db.query(Referral).filter(
            Referral.position_id == j.id,
            Referral.status == ReferralStatus.HIRED.value,
        ).first() is not None

        should_deactivate = has_hired_ref or (deactivate_missing and j.id not in scraped_ids)
        if should_deactivate:
            j.is_active = False
            deactivated_count += 1
            try:
                excel_svc.save_job_position({
                    "id": j.id,
                    "title": j.title,
                    "department": j.department,
                    "location": j.location,
                    "employment_type": j.employment_type,
                    "is_active": False,
                    "description": j.description,
                })
            except Exception as ex:
                logger.warning(f"Failed to update deactivated job {j.id} in Excel: {ex}")

    db.commit()
    for j in synced_jobs:
        db.refresh(j)

    logger.info(
        f"CATS sync finished: {len(scraped_jobs)} scraped, {created_count} created, "
        f"{updated_count} updated, {deactivated_count} deactivated."
    )

    return {
        "success": True,
        "total_scraped": len(scraped_jobs),
        "created_count": created_count,
        "updated_count": updated_count,
        "deactivated_count": deactivated_count,
        "jobs": synced_jobs,
        "message": f"Successfully synchronized {len(scraped_jobs)} job openings from Tangentia CATS Careers.",
    }
