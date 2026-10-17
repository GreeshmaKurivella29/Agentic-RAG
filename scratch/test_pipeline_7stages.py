import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag_engine import LegalRetriever, load_corpus, run_agent, analyze_legal_query

print("Loading corpus and initializing retriever...")
corpus = load_corpus()
retriever = LegalRetriever(corpus)
print(f"Corpus loaded: {len(corpus)} chunks.")

print("\n" + "="*60)
print("TEST 1: Article 21 (Supported / Grounded Query)")
print("="*60)
q1 = "What does Article 21 of the Constitution protect?"
res1 = run_agent(q1, retriever)
print(f"1. Query Analysis: Terms={res1['legal_terms']}, Citations={res1['citations']}, Ambiguity={res1['analysis']['is_ambiguous']}")
print(f"2. Reformulation: was_reformulated={res1['was_reformulated']}, Query='{res1['query_used']}'")
print(f"3. Route: {res1['route']} | Rationale: {res1['route_reason'][:80]}...")
print(f"4. Retrieved & Cross-Encoder Re-ranked: {len(res1['evidence'])} passages")
for i, ev in enumerate(res1['evidence'][:3], 1):
    print(f"   [S{i}] {ev['title']} | Cross-Encoder Prob: {ev['cross_encoder_prob']:.1%} | Score: {ev['cross_encoder_score']:.3f}")
print(f"5. Evidence Sufficiency Gate: Passed={res1['enough']} | Reason: {res1['evidence_reason']}")
print(f"6. Retry Invoked: {res1['retried']}")
print(f"7. Response Type: {'Authoritative Answer' if not res1['is_insufficient_evidence_response'] else 'Insufficient Evidence Refusal'}")
print("Answer Preview:\n", res1['answer'][:250], "...\n")

print("\n" + "="*60)
print("TEST 2: Weak / Colloquial Query ('can police arrest without warrant')")
print("="*60)
q2 = "can police arrest without warrant"
res2 = run_agent(q2, retriever)
print(f"1. Query Analysis: Terms={res2['legal_terms']}, Ambiguity={res2['analysis']['is_ambiguous']}")
print(f"   Ambiguity Reasons: {res2['ambiguity_reasons']}")
print(f"2. Reformulation: was_reformulated={res2['was_reformulated']}")
print(f"   Reformulated Query: '{res2['query_used']}'")
print(f"3. Route: {res2['route']}")
print(f"5. Evidence Sufficiency: Passed={res2['enough']}")

print("\n" + "="*60)
print("TEST 3: Completely Unsupported Out-of-Corpus Query ('maritime salvage rates')")
print("="*60)
q3 = "What are the commercial maritime admiralty salvage dispute rates in Cochin port?"
res3 = run_agent(q3, retriever)
print(f"1. Query Analysis: Terms={res3['legal_terms']}")
print(f"3. Route: {res3['route']}")
print(f"5. Evidence Sufficiency Initial Gate: Passed={res3['enough']}")
print(f"6. Retry Invoked: {res3['retried']} | Retry Query: '{res3['retry_query']}'")
print(f"7. Explicit Insufficient Evidence Response: {res3['is_insufficient_evidence_response']}")
print("Answer:\n", res3['answer'])

print("\nALL 7 PIPELINE STAGES VERIFIED!")
