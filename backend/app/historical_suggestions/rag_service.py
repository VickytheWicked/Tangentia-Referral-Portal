import os
import json
import math
import hashlib
import sqlite3
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger("historical_rag")


class HistoricalRAGService:
    """
    Isolated RAG service for indexing and retrieving archived candidates.
    Maintains its own SQLite vector/embedding index at data/historical_rag.db.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.HISTORICAL_RAG_DB_PATH
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        """Create isolated table for caching embeddings and text representations."""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS historical_embeddings (
                        referral_id TEXT PRIMARY KEY,
                        content_hash TEXT NOT NULL,
                        text_content TEXT NOT NULL,
                        embedding_json TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
        finally:
            conn.close()

    @staticmethod
    def build_candidate_searchable_text(
        candidate_name: str,
        skills: List[str],
        years_of_experience: float,
        projects: List[dict],
        experience: List[dict],
        referral_note: Optional[str] = None,
        original_position_title: Optional[str] = None,
    ) -> str:
        """
        Assemble comprehensive searchable profile text for embedding.
        """
        parts = []
        if original_position_title:
            parts.append(f"Previously referred for: {original_position_title}")
        if skills:
            parts.append(f"Core Skills & Technologies: {', '.join(skills)}")
        if years_of_experience > 0:
            parts.append(f"Total Experience: {years_of_experience:.1f} years")

        if experience:
            exp_strs = []
            for exp in experience[:5]:
                t = exp.get("job_title") or exp.get("role") or ""
                c = exp.get("company") or ""
                r = exp.get("responsibilities") or []
                r_text = f" - {'; '.join(r[:3])}" if r else ""
                exp_strs.append(f"{t} at {c}{r_text}")
            if exp_strs:
                parts.append("Work Experience:\n" + "\n".join(exp_strs))

        if projects:
            proj_strs = []
            for p in projects[:4]:
                name = p.get("name") or "Project"
                desc = p.get("description") or ""
                tech = p.get("technologies") or []
                t_str = f" (Tech: {', '.join(tech)})" if tech else ""
                proj_strs.append(f"{name}{t_str}: {desc[:150]}")
            if proj_strs:
                parts.append("Projects:\n" + "\n".join(proj_strs))

        if referral_note:
            parts.append(f"Referral Note: {referral_note}")

        return "\n\n".join(parts)

    @staticmethod
    def build_job_searchable_text(job_title: str, department: str, description: str) -> str:
        """
        Construct query text representing active job requisition requirements.
        """
        return f"Target Job Position: {job_title}\nDepartment: {department}\nRequisition Requirements & Responsibilities:\n{description}"

    def compute_embedding(self, text: str) -> List[float]:
        """
        Compute embedding vector.
        Attempts Gemini text-embedding if API key is configured.
        Falls back to normalized term-frequency n-gram vector for offline/test reliability.
        """
        clean_text = text.strip()
        if not clean_text:
            return [0.0] * 64

        # 1. Try Gemini Embeddings if configured
        if getattr(settings, "GEMINI_API_KEY", None):
            try:
                from google import genai
                client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options={"timeout": 10000})
                res = client.models.embed_content(
                    model="text-embedding-004",
                    contents=clean_text[:4000],
                )
                if res and res.embedding and res.embedding.values:
                    return list(res.embedding.values)
            except Exception as e:
                logger.debug(f"Gemini embedding API call skipped/fallback ({e})")

        # 2. Heuristic Semantic N-Gram Vectorizer (High-dimensional sparse-to-dense projection)
        return self._compute_ngram_vector(clean_text)

    @staticmethod
    def _compute_ngram_vector(text: str, dim: int = 128) -> List[float]:
        """
        Deterministic, zero-dependency token & character n-gram projection for offline semantic retrieval.
        Maps text onto a normalized unit hypersphere.
        """
        words = [w.lower().strip(",.:;!?()[]{}'\"") for w in text.split()]
        words = [w for w in words if len(w) > 1]
        
        vec = [0.0] * dim
        if not words:
            return vec

        # Weight key words
        for idx, word in enumerate(words):
            # Term weight: earlier tokens in title/skills receive higher weighting
            weight = 2.0 if idx < 15 else 1.0
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            vec[h % dim] += 1.0 * weight

            # Bigrams
            if idx > 0:
                bi = f"{words[idx-1]}_{word}"
                h_bi = int(hashlib.md5(bi.encode("utf-8")).hexdigest(), 16)
                vec[h_bi % dim] += 1.5

        # Normalize to unit vector
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two unit vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        return max(0.0, min(1.0, dot))

    def get_or_create_candidate_embedding(
        self,
        referral_id: str,
        searchable_text: str,
    ) -> List[float]:
        """
        Retrieve cached embedding or compute and save to isolated SQLite index.
        """
        content_hash = hashlib.sha256(searchable_text.encode("utf-8")).hexdigest()
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT content_hash, embedding_json FROM historical_embeddings WHERE referral_id = ?",
                (referral_id,),
            )
            row = cur.fetchone()
            if row and row[0] == content_hash:
                return json.loads(row[1])

            # Compute new embedding
            embedding = self.compute_embedding(searchable_text)
            embedding_json = json.dumps(embedding)
            now_iso = datetime.now(timezone.utc).isoformat()

            with conn:
                conn.execute(
                    """
                    INSERT INTO historical_embeddings (referral_id, content_hash, text_content, embedding_json, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(referral_id) DO UPDATE SET
                        content_hash = excluded.content_hash,
                        text_content = excluded.text_content,
                        embedding_json = excluded.embedding_json,
                        updated_at = excluded.updated_at
                    """,
                    (referral_id, content_hash, searchable_text, embedding_json, now_iso),
                )
            return embedding
        finally:
            conn.close()


_rag_service_instance: Optional[HistoricalRAGService] = None


def get_historical_rag_service() -> HistoricalRAGService:
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = HistoricalRAGService()
    return _rag_service_instance
