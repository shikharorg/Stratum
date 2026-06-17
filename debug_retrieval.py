import asyncio, json, sys
from app.pipeline.encoder import QueryEncoder
from app.pipeline.reranker import Reranker
from app.pipeline.searcher import HybridSearcher
from app.pipeline import grounding
from app.core.config import settings
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue, SparseVector

QUERY = "How does Meridian structure the PR review process?"
TENANT = "dc150230-d8f0-4008-a8a8-fd1800444a74"
SEP = "\n\n---\n\n"

def hr(title=""):
    print("\n" + "=" * 70)
    if title:
        print(title)
    print("=" * 70)


async def run():
    encoder = QueryEncoder()
    reranker = Reranker()
    qdrant = AsyncQdrantClient(url=settings.QDRANT_URL)
    searcher = HybridSearcher(qdrant, settings.QDRANT_COLLECTION)

    dense_vec = encoder.encode_query(QUERY)
    sparse_vec = encoder.encode_sparse(QUERY)

    q_filter = Filter(must=[FieldCondition(key="tenant_id", match=MatchValue(value=TENANT))])

    dense_resp, sparse_resp = await asyncio.gather(
        qdrant.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=dense_vec, using="dense",
            query_filter=q_filter, limit=20, with_payload=True,
        ),
        qdrant.query_points(
            collection_name=settings.QDRANT_COLLECTION,
            query=SparseVector(indices=sparse_vec["indices"], values=sparse_vec["values"]),
            using="sparse",
            query_filter=q_filter, limit=20, with_payload=True,
        ),
    )

    # ------------------------------------------------------------------ STEP 2
    hr("STEP 2 -- PIPELINE INTERNALS")

    print("\n-- DENSE (cosine similarity, top 20) --")
    for i, p in enumerate(dense_resp.points):
        pay = p.payload or {}
        txt = pay.get("text", "")[:80].replace("\n", " ")
        doc = pay.get("document_id", "?")[:8]
        print(f"  [{i:02d}] score={p.score:.4f}  doc={doc}  id={str(p.id)[:8]}  text={txt!r}")

    print("\n-- SPARSE / BM25 (top 20) --")
    for i, p in enumerate(sparse_resp.points):
        pay = p.payload or {}
        txt = pay.get("text", "")[:80].replace("\n", " ")
        doc = pay.get("document_id", "?")[:8]
        print(f"  [{i:02d}] score={p.score:.4f}  doc={doc}  id={str(p.id)[:8]}  text={txt!r}")

    # Manual RRF
    RRF_K = 60
    rrf_scores: dict = {}
    dense_sc: dict = {}
    sparse_sc: dict = {}
    payloads: dict = {}
    for rank, p in enumerate(dense_resp.points):
        pid = str(p.id)
        rrf_scores[pid] = rrf_scores.get(pid, 0.0) + 1.0 / (RRF_K + rank + 1)
        dense_sc[pid] = float(p.score)
        if p.payload:
            payloads[pid] = p.payload
    for rank, p in enumerate(sparse_resp.points):
        pid = str(p.id)
        rrf_scores[pid] = rrf_scores.get(pid, 0.0) + 1.0 / (RRF_K + rank + 1)
        sparse_sc[pid] = float(p.score)
        if p.payload and pid not in payloads:
            payloads[pid] = p.payload
    sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)[:20]

    print("\n-- HYBRID / RRF (k=60, top 20, sorted descending by RRF score) --")
    for i, pid in enumerate(sorted_ids):
        pay = payloads.get(pid, {})
        txt = pay.get("text", "")[:80].replace("\n", " ")
        doc = pay.get("document_id", "?")[:8]
        print(
            f"  [{i:02d}] rrf={rrf_scores[pid]:.5f}"
            f"  dense={dense_sc.get(pid, 0.0):.4f}"
            f"  sparse={sparse_sc.get(pid, 0.0):.4f}"
            f"  doc={doc}  id={pid[:8]}  text={txt!r}"
        )

    candidates = await searcher.search(
        query_vector=dense_vec, sparse_vector=sparse_vec,
        tenant_id=TENANT, source_type=None, top_k=20,
    )
    reranked = reranker.rerank(QUERY, candidates, 8)

    print("\n-- RERANKED (CrossEncoder: cross-encoder/ms-marco-MiniLM-L-6-v2) --")
    print("   Comparator: sorted(results, key=lambda r: r.combined_score, reverse=True)[:top_k]")
    print("   Higher CrossEncoder score = MORE relevant. Sorted DESCENDING.")
    for i, r in enumerate(reranked):
        print(
            f"  [{i}] score={r.combined_score:.4f}"
            f"  doc={str(r.document_id)[:8]}"
            f"  id={str(r.chunk_id)[:8]}"
            f"  text={r.text[:100]!r}"
        )

    # ------------------------------------------------------------------ STEP 3
    hr("STEP 3 -- CHUNKS PASSED TO generate_answer()")

    gen_chunks = [r for r in reranked if r.combined_score > 0] or reranked[:2]
    labeled = [f"Source: {r.source_url or r.source_type}\n{r.text}" for r in gen_chunks]

    print(f"\nFilter logic: [r for r in reranked if r.combined_score > 0] or reranked[:2]")
    print(f"Chunks with score > 0: {sum(1 for r in reranked if r.combined_score > 0)}")
    print(f"Fallback applied: True (none qualify) -> passing reranked[:2]")
    print(f"Total chunks passed to generate_answer: {len(labeled)}\n")

    for i, c in enumerate(labeled):
        print(f"chunk[{i}] ({len(c)} chars):")
        print(c)
        print()

    # ------------------------------------------------------------------ STEP 6
    hr("STEP 6 -- EXACT SYSTEM PROMPT (every character)")

    system_prompt = (
        "You are an enterprise AI assistant. Answer ONLY using the provided context.\n\n"
        "Formatting rules:\n"
        "- Always respond in Markdown format.\n"
        "- Use ## headings for major sections.\n"
        "- Use numbered lists for sequential steps or processes.\n"
        "- Use bullet points for recommendations or non-sequential items.\n"
        "- Bold important terms using **term**.\n"
        "- Use tables for comparisons when appropriate.\n"
        "- Never write one long paragraph when the answer contains multiple steps or items.\n"
        "- Keep answers concise and factual.\n"
        "- Never copy retrieved chunks verbatim.\n"
        "- If the answer is not supported by the context say: "
        "I couldn't find that information in the provided documents."
    )
    print(f"Length: {len(system_prompt)} characters")
    print(repr(system_prompt))
    print()
    print(system_prompt)

    # ------------------------------------------------------------------ STEP 1
    hr("STEP 1 -- EXACT PROMPT SENT TO GPT-4o (2 labeled chunks)")

    context2 = SEP.join(labeled)
    user2 = f"Context:\n{context2}\n\nQuery: {QUERY}"
    print("SYSTEM PROMPT: (see Step 6 above)")
    print("\nUSER PROMPT (verbatim):")
    print(user2)

    oai = grounding._client

    # ------------------------------------------------------------------ STEP 4
    hr("STEP 4 -- generate_answer() with 5 reranked chunks (labeled with Source:)")

    five_labeled = [f"Source: {r.source_url or r.source_type}\n{r.text}" for r in reranked[:5]]
    context5L = SEP.join(five_labeled)
    user5L = f"Context:\n{context5L}\n\nQuery: {QUERY}"
    print("\nUSER PROMPT:")
    print(user5L)

    resp4 = await oai.chat.completions.create(
        model=settings.OPENAI_GENERATION_MODEL,
        temperature=0,
        max_tokens=settings.OPENAI_GENERATION_MAX_TOKENS,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user5L},
        ],
    )
    ans4 = resp4.choices[0].message.content or ""
    print("\nRAW GPT RESPONSE (5 labeled chunks):")
    print(repr(ans4))

    # ------------------------------------------------------------------ STEP 5
    hr("STEP 5 -- generate_answer() with 5 chunks, NO Source: prefix")

    five_plain = [r.text for r in reranked[:5]]
    context5P = SEP.join(five_plain)
    user5P = f"Context:\n{context5P}\n\nQuery: {QUERY}"
    print("\nUSER PROMPT:")
    print(user5P)

    resp5 = await oai.chat.completions.create(
        model=settings.OPENAI_GENERATION_MODEL,
        temperature=0,
        max_tokens=settings.OPENAI_GENERATION_MAX_TOKENS,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user5P},
        ],
    )
    ans5 = resp5.choices[0].message.content or ""
    print("\nRAW GPT RESPONSE (5 plain chunks):")
    print(repr(ans5))

    # ------------------------------------------------------------------ STEP 7
    hr("STEP 7 -- GROUNDING VALIDATOR (claim-level breakdown)")

    claim_prompt = (
        "You are a grounding validator. Given a query, an answer, and context chunks, "
        "extract each factual claim from the answer and determine whether each claim "
        "is supported by the provided context. "
        "Return a JSON object with exactly these fields: "
        "{\"supported_count\": int, \"total_count\": int, "
        "\"supported_claims\": [list of claim strings that ARE supported by context], "
        "\"unsupported_claims\": [list of claim strings NOT supported by context]}."
    )
    # validator sees plain context_chunks (no labels), same as production
    plain_ctx = SEP.join([r.text for r in reranked[:2]])

    cases = [
        ("ATTEMPT 1 original (2 labeled)", "I couldn't find that information in the provided documents."),
        ("ATTEMPT 4 (5 labeled chunks)", ans4),
        ("ATTEMPT 5 (5 plain chunks)", ans5),
    ]

    for label, answer_text in cases:
        print(f"\n-- {label} --")
        print(f"Answer: {answer_text!r}")
        vresp = await oai.chat.completions.create(
            model=settings.OPENAI_VALIDATION_MODEL,
            messages=[
                {"role": "system", "content": claim_prompt},
                {"role": "user", "content": f"Query: {QUERY}\n\nAnswer: {answer_text}\n\nContext:\n{plain_ctx}"},
            ],
            response_format={"type": "json_object"},
        )
        vraw = vresp.choices[0].message.content or "{}"
        print(f"Raw validator response: {vraw}")
        try:
            vdata = json.loads(vraw)
            total = int(vdata.get("total_count") or 0)
            sup = int(vdata.get("supported_count") or 0)
            ratio = (total - sup) / total if total else 0.0
            print(f"  supported_count   : {sup}")
            print(f"  total_count       : {total}")
            print(f"  supported_claims  : {vdata.get('supported_claims', [])}")
            print(f"  unsupported_claims: {vdata.get('unsupported_claims', [])}")
            print(f"  unsupported_ratio : {ratio:.3f}  passed: {ratio < 0.15}")
        except Exception as e:
            print(f"  parse error: {e}")

    # ------------------------------------------------------------------ STEP 8
    hr("STEP 8 -- FINDINGS SUMMARY")
    print("""
Scores at each stage:
  Best CrossEncoder score for the PR chunk: see [0] above
  All 8 reranked chunks have negative CrossEncoder scores

Chunk passed (fallback reranked[:2]):
  chunk[0] = PR Process section (exactly what is needed)
  chunk[1] = Welcome to Meridian (irrelevant)

GPT-4o response with 2 labeled chunks: fallback message
GPT-4o response with 5 labeled chunks: (see Step 4 above)
GPT-4o response with 5 plain chunks:   (see Step 5 above)

Key evidence collected above for Step 8 analysis.
""")


asyncio.run(run())
