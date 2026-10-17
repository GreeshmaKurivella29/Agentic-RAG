import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag_engine import LegalRetriever, load_corpus, run_agent

retriever = LegalRetriever(load_corpus())

print("==================================================")
print("TEST 1: Article 21 (Supported / Grounded Query)")
print("==================================================")
q1 = "What does Article 21 of the Constitution protect?"
res1 = run_agent(q1, retriever)
print(f"User Query: {q1}")
print(f"Reformulated Search Query: {res1['query_used']} (Was Reformulated: {res1['was_reformulated']})")
print(f"Query Quality Passed: {res1['good_query']}")
print(f"Quality Reason: {res1['quality_reason']}")
print(f"Retrieval Route: {res1['route']}")
print(f"Route Rationale: {res1['route_reason']}")
print(f"Evidence Gate Passed: {res1['enough']}")
print(f"Gate Decision Reason: {res1['evidence_reason']}")
print(f"Retry Step Invoked: {res1['retried']}")
print(f"Total Authorities Cited: {len(res1['evidence'])}")
for i, ev in enumerate(res1['evidence'], 1):
    print(f"  [S{i}] {ev['title']} | Source: {ev['source']} | Relevance: {ev['relevance']:.1%} | Score: {ev['score']:.4f}")
    print(f"       URL: {ev['url']}")
    print(f"       Text: {ev['text'].replace('\n', ' ')[:140]}...")
print("\n--- SYNTHESIZED ANSWER / CORE AUTHORITY ---")
print(res1['answer'])

print("\n==================================================")
print("TEST 2: IT Act Query")
print("==================================================")
q2 = "What is the latest amendment to the IT Act?"
res2 = run_agent(q2, retriever)
print(f"User Query: {q2}")
print(f"Reformulated Search Query: {res2['query_used']} (Was Reformulated: {res2['was_reformulated']})")
print(f"Retrieval Route: {res2['route']}")
print(f"Evidence Gate Passed: {res2['enough']}")
print(f"Gate Decision Reason: {res2['evidence_reason']}")
print("\n--- SYNTHESIZED ANSWER / DECLARATION ---")
print(res2['answer'])

print("\n==================================================")
print("TEST 3: Maritime Admiralty (Completely Unsupported Query -> Safe No-Answer)")
print("==================================================")
q3 = "What are the maritime admiralty cargo salvage jurisdiction rules in Mumbai harbour?"
res3 = run_agent(q3, retriever)
print(f"User Query: {q3}")
print(f"Reformulated Search Query: {res3['query_used']} (Was Reformulated: {res3['was_reformulated']})")
print(f"Query Quality Passed: {res3['good_query']}")
print(f"Quality Reason: {res3['quality_reason']}")
print(f"Retrieval Route: {res3['route']}")
print(f"Evidence Gate Passed: {res3['enough']}")
print(f"Gate Decision Reason: {res3['evidence_reason']}")
print(f"Retry Step Invoked: {res3['retried']}")
print("\n--- SYNTHESIZED ANSWER / DECLARATION ---")
print(res3['answer'])
print("Guided Primary Next-Step Actions (No Hallucination):")
for act in res3['actions']:
    print(f"  - {act['label']}: {act['url']}")

