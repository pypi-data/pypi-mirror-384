"""
Hybrid Retrieval: RRF + MMR for DSPy RAG
Combines BM25 + Vector Search with Reciprocal Rank Fusion and Maximal Marginal Relevance

References:
- RRF: https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf
- MMR: https://www.cs.cmu.edu/~jgc/publication/The_Use_MMR_Diversity_Based_LTMIR_1998.pdf
"""

from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScoredDoc:
    """Document with retrieval score"""
    id: str
    text: str
    score: float
    meta: Dict[str, Any]


def reciprocal_rank_fusion(
    ranklists: List[List[ScoredDoc]],
    k: int = 60,
    top_n: int = 24
) -> List[ScoredDoc]:
    """
    Reciprocal Rank Fusion: Combine multiple ranked lists.

    Formula: score(doc) = Σ (1 / (k + rank_i + 1))

    Args:
        ranklists: List of ranked document lists (e.g., [bm25_results, vector_results])
        k: Constant for RRF formula (default: 60)
        top_n: Number of documents to return

    Returns:
        Fused and re-ranked document list

    Reference: Cormack et al., "Reciprocal rank fusion outperforms condorcet"
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, ScoredDoc] = {}

    for ranklist in ranklists:
        for rank, doc in enumerate(ranklist):
            doc_id = doc.id
            # RRF score accumulation
            rrf_score = 1.0 / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0.0) + rrf_score

            # Keep first occurrence for metadata
            if doc_id not in doc_map:
                doc_map[doc_id] = doc

    # Sort by fused score and return top_n
    ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_n]

    result = []
    for doc_id, fused_score in ranked:
        doc = doc_map[doc_id]
        result.append(ScoredDoc(
            id=doc.id,
            text=doc.text,
            score=fused_score,
            meta=doc.meta
        ))

    logger.debug(f"RRF: Fused {len(ranklists)} ranklists → {len(result)} docs")
    return result


def maximal_marginal_relevance(
    query_vec: np.ndarray,
    doc_vecs: np.ndarray,
    doc_ids: List[str],
    lambda_param: float = 0.5,
    top_n: int = 12
) -> List[int]:
    """
    Maximal Marginal Relevance: Select diverse, relevant documents.

    Formula: MMR = λ * Sim(D, Q) - (1-λ) * max(Sim(D, D_i))

    Args:
        query_vec: Query embedding vector (normalized)
        doc_vecs: Document embedding vectors (normalized), shape (N, dim)
        doc_ids: Document IDs corresponding to doc_vecs
        lambda_param: Balance between relevance (1.0) and diversity (0.0)
        top_n: Number of documents to select

    Returns:
        Indices of selected documents

    Reference: Carbonell & Goldstein, "The Use of MMR, Diversity-Based Reranking"
    """
    if len(doc_vecs) == 0:
        return []

    selected: List[int] = []
    candidates = list(range(len(doc_vecs)))

    # Compute relevance scores (cosine similarity with query)
    relevance_scores = np.dot(doc_vecs, query_vec)

    while candidates and len(selected) < top_n:
        # First selection: most relevant
        if not selected:
            best_idx = int(np.argmax(relevance_scores[candidates]))
            selected.append(candidates.pop(best_idx))
            continue

        # Subsequent selections: balance relevance and novelty
        mmr_scores = []
        for idx in candidates:
            relevance = relevance_scores[idx]

            # Redundancy: maximum similarity to any selected document
            redundancy = max(
                np.dot(doc_vecs[idx], doc_vecs[selected_idx])
                for selected_idx in selected
            )

            # MMR formula
            mmr_score = lambda_param * relevance - (1 - lambda_param) * redundancy
            mmr_scores.append((mmr_score, idx))

        # Select document with highest MMR score
        best_score, best_idx = max(mmr_scores, key=lambda x: x[0])
        selected.append(best_idx)
        candidates.remove(best_idx)

    logger.debug(f"MMR: Selected {len(selected)}/{len(doc_vecs)} docs (λ={lambda_param})")
    return selected


def hybrid_search(
    query: str,
    vector_search_fn: callable,
    bm25_search_fn: Optional[callable] = None,
    embed_fn: callable = None,
    k_vector: int = 24,
    k_bm25: int = 24,
    rrf_k: int = 60,
    mmr_lambda: float = 0.6,
    final_k: int = 12
) -> List[Dict[str, Any]]:
    """
    Hybrid search combining vector and BM25 with RRF fusion and MMR diversity.

    Pipeline:
    1. Run vector search
    2. Run BM25 search (if available)
    3. Fuse with RRF
    4. Apply MMR for diversity

    Args:
        query: Search query
        vector_search_fn: Function(query, k) -> List[ScoredDoc]
        bm25_search_fn: Optional function(query, k) -> List[ScoredDoc]
        embed_fn: Function(text) -> np.ndarray for MMR
        k_vector: Number of results from vector search
        k_bm25: Number of results from BM25 search
        rrf_k: RRF constant
        mmr_lambda: MMR relevance vs diversity balance
        final_k: Final number of documents to return

    Returns:
        List of selected documents with metadata
    """
    ranklists = []

    # Vector search
    vector_results = vector_search_fn(query, k=k_vector)
    ranklists.append(vector_results)
    logger.debug(f"Vector search: {len(vector_results)} results")

    # BM25 search (if available)
    if bm25_search_fn:
        bm25_results = bm25_search_fn(query, k=k_bm25)
        ranklists.append(bm25_results)
        logger.debug(f"BM25 search: {len(bm25_results)} results")

    # RRF Fusion
    if not ranklists:
        return []

    fused = reciprocal_rank_fusion(ranklists, k=rrf_k, top_n=final_k * 2)

    # MMR Diversity (if embed function provided)
    if embed_fn and len(fused) > final_k:
        # Get embeddings for query and documents
        query_vec = embed_fn(query)
        doc_texts = [doc.text for doc in fused]
        doc_vecs = np.array([embed_fn(text) for text in doc_texts])
        doc_ids = [doc.id for doc in fused]

        # Apply MMR
        selected_indices = maximal_marginal_relevance(
            query_vec=query_vec,
            doc_vecs=doc_vecs,
            doc_ids=doc_ids,
            lambda_param=mmr_lambda,
            top_n=min(final_k, len(fused))
        )

        # Reorder by MMR selection
        result = [fused[i] for i in selected_indices]
    else:
        # No MMR, just take top-k from fusion
        result = fused[:final_k]

    logger.info(f"Hybrid search: {len(result)} final docs (RRF+MMR)")

    # Convert to dict format
    return [
        {
            'id': doc.id,
            'text': doc.text,
            'score': doc.score,
            'meta': doc.meta
        }
        for doc in result
    ]


# Utility: Normalize vectors for cosine similarity
def normalize_vectors(vecs: np.ndarray) -> np.ndarray:
    """Normalize vectors to unit length for cosine similarity"""
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1  # Avoid division by zero
    return vecs / norms
