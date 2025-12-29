#!/usr/bin/env python3
"""
Evaluation script for GraphRAG /query endpoint.

Evaluates retrieval quality against golden queries.
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Tuple

try:
    import requests
except ImportError:
    print("Error: 'requests' library is required. Install with: pip install requests", file=sys.stderr)
    sys.exit(2)


def read_golden_queries(filepath: str) -> List[Dict[str, Any]]:
    """Read golden queries from JSONL file."""
    queries = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if 'query' not in obj or 'expected_incident_ids' not in obj:
                        print(f"Warning: Line {line_num} missing required fields, skipping", file=sys.stderr)
                        continue
                    queries.append(obj)
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON on line {line_num}: {e}", file=sys.stderr)
                    sys.exit(2)
    except FileNotFoundError:
        print(f"Error: Golden queries file not found: {filepath}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error reading golden queries file: {e}", file=sys.stderr)
        sys.exit(2)
    
    return queries


def query_api(base_url: str, question: str) -> Tuple[List[str], bool]:
    """
    Query the /query endpoint.
    
    Returns:
        (predicted_incident_ids, success_flag)
    """
    url = f"{base_url}/query"
    payload = {"question": question}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract evidence.incident_ids
        if 'evidence' in data and isinstance(data['evidence'], dict):
            incident_ids = data['evidence'].get('incident_ids', [])
            if isinstance(incident_ids, list):
                # Ensure all are strings
                return [str(id) for id in incident_ids], True
            else:
                print(f"Warning: evidence.incident_ids is not a list, got {type(incident_ids)}", file=sys.stderr)
                return [], True
        else:
            # Missing evidence field, treat as empty
            return [], True
            
    except requests.exceptions.Timeout:
        print(f"Error: Request timeout for query: {question[:50]}...", file=sys.stderr)
        return [], False
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {base_url}", file=sys.stderr)
        return [], False
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP {e.response.status_code} for query: {question[:50]}...", file=sys.stderr)
        return [], False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON response for query: {question[:50]}...", file=sys.stderr)
        return [], False
    except Exception as e:
        print(f"Error: Unexpected error for query: {question[:50]}...: {e}", file=sys.stderr)
        return [], False


def query_ask_api(base_url: str, question: str) -> Tuple[Dict[str, Any], bool]:
    """
    Query the /ask endpoint to get structured response with incident cards.
    
    Returns:
        (structured_data, success_flag)
        structured_data contains:
        - incident_ids: List[str]
        - components: Set[str]
        - failure_modes: Set[str]
        - root_causes: Set[str]
        - triggers: Set[str]
        - concepts: Set[str]
        - artifacts: Set[str]
        - facts: List[Dict] with from, rel, to
    """
    url = f"{base_url}/ask"
    payload = {"question": question}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract structured fields
        structured = {
            "incident_ids": [],
            "components": set(),
            "failure_modes": set(),
            "root_causes": set(),
            "triggers": set(),
            "concepts": set(),
            "artifacts": set(),
            "facts": [],
            "warnings": [],
            "refusal": None
        }
        
        # Extract incident IDs
        if 'evidence' in data and isinstance(data['evidence'], dict):
            incident_ids = data['evidence'].get('incident_ids', [])
            if isinstance(incident_ids, list):
                structured["incident_ids"] = [str(id) for id in incident_ids]
        
        # Extract from incident_cards
        if 'incident_cards' in data and isinstance(data['incident_cards'], list):
            for card in data['incident_cards']:
                if isinstance(card, dict):
                    # Components
                    if 'affects' in card and isinstance(card['affects'], list):
                        structured["components"].update(str(c) for c in card['affects'])
                    # Failure modes
                    if 'failure_modes' in card and isinstance(card['failure_modes'], list):
                        structured["failure_modes"].update(str(fm) for fm in card['failure_modes'])
                    # Root causes
                    if 'root_causes' in card and isinstance(card['root_causes'], list):
                        structured["root_causes"].update(str(rc) for rc in card['root_causes'])
                    # Triggers
                    if 'triggers' in card and isinstance(card['triggers'], list):
                        structured["triggers"].update(str(t) for t in card['triggers'])
                    # Concepts
                    if 'concepts' in card and isinstance(card['concepts'], list):
                        structured["concepts"].update(str(c) for c in card['concepts'])
                    # Artifacts
                    if 'artifacts' in card and isinstance(card['artifacts'], list):
                        structured["artifacts"].update(str(a) for a in card['artifacts'])
        
        # Extract warnings and refusal
        if 'warnings' in data and isinstance(data['warnings'], list):
            structured["warnings"] = data['warnings']
        if 'refusal' in data:
            structured["refusal"] = data['refusal']
        
        # Extract from key_facts
        if 'key_facts' in data and isinstance(data['key_facts'], list):
            for fact in data['key_facts']:
                if isinstance(fact, dict):
                    structured["facts"].append({
                        "from": str(fact.get('from', fact.get('from_id', ''))),
                        "rel": str(fact.get('rel', '')),
                        "to": str(fact.get('to', fact.get('to_id', ''))),
                        "evidence_refs": fact.get('evidence_refs', [])
                    })
        
        # Extract tier1_facts and tier2_context
        if 'tier1_facts' in data and isinstance(data['tier1_facts'], list):
            structured["tier1_facts"] = data['tier1_facts']
        if 'tier2_context' in data and isinstance(data['tier2_context'], list):
            structured["tier2_context"] = data['tier2_context']
        
        # Extract runbook format fields
        if 'summary' in data:
            structured["summary"] = data['summary']
        if 'evidence_bullets' in data and isinstance(data['evidence_bullets'], list):
            structured["evidence_bullets"] = data['evidence_bullets']
        if 'context_concepts' in data and isinstance(data['context_concepts'], list):
            structured["context_concepts"] = data['context_concepts']
        
        # Extract answer text for tiering check
        if 'answer' in data:
            structured["answer_text"] = data['answer']
        
        # Convert sets to lists for JSON serialization
        structured["components"] = list(structured["components"])
        structured["failure_modes"] = list(structured["failure_modes"])
        structured["root_causes"] = list(structured["root_causes"])
        structured["triggers"] = list(structured["triggers"])
        structured["concepts"] = list(structured["concepts"])
        structured["artifacts"] = list(structured["artifacts"])
        
        return structured, True
            
    except requests.exceptions.Timeout:
        print(f"Error: Request timeout for ask: {question[:50]}...", file=sys.stderr)
        return {}, False
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {base_url}", file=sys.stderr)
        return {}, False
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP {e.response.status_code} for ask: {question[:50]}...", file=sys.stderr)
        return {}, False
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON response for ask: {question[:50]}...: {e}", file=sys.stderr)
        return {}, False
    except Exception as e:
        print(f"Error: Unexpected error for ask: {question[:50]}...: {e}", file=sys.stderr)
        return {}, False


def check_negative_evidence(
    structured_data: Dict[str, Any],
    forbidden_root_causes: List[str],
    forbidden_failure_modes: List[str],
    forbidden_components: List[str],
    forbidden_incidents: List[str]
) -> Tuple[bool, List[str]]:
    """
    Check if any forbidden items appear in the structured response.
    
    Returns:
        (passed, violations) where violations is a list of violation messages
    """
    violations = []
    
    # Check forbidden incidents
    for forbidden_incident in forbidden_incidents:
        if forbidden_incident in structured_data.get("incident_ids", []):
            violations.append(f"Forbidden incident '{forbidden_incident}' found in response")
    
    # Check forbidden components
    for forbidden_comp in forbidden_components:
        if forbidden_comp in structured_data.get("components", []):
            violations.append(f"Forbidden component '{forbidden_comp}' found in response")
    
    # Check forbidden failure modes
    for forbidden_fm in forbidden_failure_modes:
        if forbidden_fm in structured_data.get("failure_modes", []):
            violations.append(f"Forbidden failure_mode '{forbidden_fm}' found in response")
    
    # Check forbidden root causes
    for forbidden_rc in forbidden_root_causes:
        if forbidden_rc in structured_data.get("root_causes", []):
            violations.append(f"Forbidden root_cause '{forbidden_rc}' found in response")
    
    return len(violations) == 0, violations


def check_api_health(base_url: str) -> bool:
    """Check if API is reachable."""
    try:
        health_url = f"{base_url}/health"
        response = requests.get(health_url, timeout=5)
        response.raise_for_status()
        return True
    except Exception:
        return False


def evaluate_queries(base_url: str, golden_queries: List[Dict[str, Any]], k: int) -> Tuple[List[Dict[str, Any]], int, int, int]:
    """
    Evaluate queries against API.
    
    Returns:
        (failures_list, correct_at_1_count, hits_at_k_count, negative_evidence_failures_count)
    """
    failures = []
    correct_at_1 = 0
    hits_at_k = 0
    negative_evidence_failures = 0
    
    # Check API health first
    if not check_api_health(base_url):
        print(f"Error: API at {base_url} is not reachable. Check /health endpoint.", file=sys.stderr)
        sys.exit(2)
    
    print(f"Evaluating {len(golden_queries)} queries against {base_url}...")
    
    for item in golden_queries:
        query = item['query']
        expected_ids = [str(id) for id in item['expected_incident_ids']]
        
        # Get forbidden fields (backwards compatible - defaults to empty lists)
        forbidden_root_causes = item.get('forbidden_root_causes', [])
        forbidden_failure_modes = item.get('forbidden_failure_modes', [])
        forbidden_components = item.get('forbidden_components', [])
        forbidden_incidents = item.get('forbidden_incidents', [])
        require_provenance = item.get('require_provenance', False)
        require_tiering = item.get('require_tiering', False)
        require_runbook_format = item.get('require_runbook_format', False)
        
        has_forbidden_fields = (
            len(forbidden_root_causes) > 0 or
            len(forbidden_failure_modes) > 0 or
            len(forbidden_components) > 0 or
            len(forbidden_incidents) > 0
        )
        
        # Query API for incident IDs (for existing metrics)
        predicted_ids, success = query_api(base_url, query)
        
        if not success:
            # If query failed completely, record as failure with empty predictions
            predicted_ids = []
        
        # Get top-k slice
        top_k_predicted = predicted_ids[:k] if len(predicted_ids) >= k else predicted_ids
        
        # Calculate metrics for this query
        top1_correct = len(predicted_ids) > 0 and predicted_ids[0] in expected_ids
        hit_at_k = any(pred_id in expected_ids for pred_id in top_k_predicted)
        
        # Check negative evidence if forbidden fields are present
        negative_checks_passed = True
        negative_violations = []
        provenance_checks_passed = True
        provenance_violations = []
        tiering_checks_passed = True
        tiering_violations = []
        runbook_format_checks_passed = True
        runbook_format_violations = []
        
        if has_forbidden_fields or require_provenance or require_tiering or require_runbook_format:
            structured_data, ask_success = query_ask_api(base_url, query)
            if ask_success:
                if has_forbidden_fields:
                    negative_checks_passed, negative_violations = check_negative_evidence(
                        structured_data,
                        forbidden_root_causes,
                        forbidden_failure_modes,
                        forbidden_components,
                        forbidden_incidents
                    )
                
                # Check provenance if required
                if require_provenance:
                    required_edge_types = ['AFFECTS', 'EXHIBITS', 'CAUSED_BY', 'TRIGGERED_BY', 'USES']
                    facts = structured_data.get('facts', [])
                    
                    # Check for uncited facts in key_facts
                    for fact in facts:
                        rel_type = fact.get('rel', '')
                        if rel_type in required_edge_types:
                            evidence_refs = fact.get('evidence_refs', [])
                            if not evidence_refs or len(evidence_refs) == 0:
                                provenance_checks_passed = False
                                provenance_violations.append(
                                    f"Fact ({fact.get('from')}, {rel_type}, {fact.get('to')}) missing evidence_refs"
                                )
                    
                    # Check for warnings about missing citations
                    warnings = structured_data.get('warnings', [])
                    if warnings:
                        for warning in warnings:
                            if isinstance(warning, dict):
                                rel_type = warning.get('rel', '')
                                if rel_type in required_edge_types:
                                    provenance_checks_passed = False
                                    provenance_violations.append(
                                        f"Warning: {warning.get('reason', 'Missing citation')} for ({warning.get('from')}, {rel_type}, {warning.get('to')})"
                                    )
                    
                    # Check for refusal (should not happen if dataset is complete)
                    refusal = structured_data.get('refusal')
                    if refusal and isinstance(refusal, dict) and refusal.get('is_refusal', False):
                        provenance_checks_passed = False
                        provenance_violations.append(
                            f"Refusal response: {refusal.get('reason', 'Insufficient evidence')}"
                        )
                
                # Check tiering if required
                if require_tiering:
                    # Check that tier1_facts excludes INVOLVES
                    tier1_facts = structured_data.get('tier1_facts', [])
                    tier2_context = structured_data.get('tier2_context', [])
                    
                    # Check key_facts (should equal tier1_facts, no INVOLVES)
                    key_facts = structured_data.get('facts', [])  # This is from key_facts field
                    for fact in key_facts:
                        if fact.get('rel') == 'INVOLVES':
                            tiering_checks_passed = False
                            tiering_violations.append(
                                f"key_facts contains Tier-2 fact: ({fact.get('from')}, INVOLVES, {fact.get('to')})"
                            )
                    
                    # Check tier1_facts for INVOLVES
                    for fact in tier1_facts:
                        if fact.get('rel') == 'INVOLVES':
                            tiering_checks_passed = False
                            tiering_violations.append(
                                f"tier1_facts contains Tier-2 fact: ({fact.get('from')}, INVOLVES, {fact.get('to')})"
                            )
                    
                    # Check tier2_context only contains INVOLVES
                    for fact in tier2_context:
                        if fact.get('rel') != 'INVOLVES':
                            tiering_checks_passed = False
                            tiering_violations.append(
                                f"tier2_context contains non-INVOLVES fact: ({fact.get('from')}, {fact.get('rel')}, {fact.get('to')})"
                            )
                    
                    # Check that answer string doesn't contain Tier-2 concept IDs
                    answer_text = structured_data.get('answer_text', '')
                    if answer_text:
                        # Extract Tier-2 concept IDs from tier2_context
                        tier2_concept_ids = {fact.get('to') for fact in tier2_context if fact.get('rel') == 'INVOLVES'}
                        
                        # Check if any Tier-2 concept ID appears in answer (excluding the phrase "Context concepts:")
                        answer_lower = answer_text.lower()
                        # Remove "Context concepts:" line if present for checking
                        answer_for_check = answer_lower.split('context concepts:')[0] if 'context concepts:' in answer_lower else answer_lower
                        
                        for concept_id in tier2_concept_ids:
                            if concept_id and concept_id.lower() in answer_for_check:
                                tiering_checks_passed = False
                                tiering_violations.append(
                                    f"Answer contains Tier-2 concept ID '{concept_id}' (should only appear in tier2_context)"
                                )
                
                # Check runbook format if required
                if require_runbook_format:
                    # Check that summary exists and doesn't contain Tier-2 concept IDs
                    summary_text = structured_data.get('summary', '')
                    if not summary_text:
                        runbook_format_checks_passed = False
                        runbook_format_violations.append("Summary field is missing")
                    else:
                        # Extract Tier-2 concept IDs from tier2_context
                        tier2_context = structured_data.get('tier2_context', [])
                        tier2_concept_ids = {fact.get('to') for fact in tier2_context if fact.get('rel') == 'INVOLVES'}
                        
                        # Check if any Tier-2 concept ID appears in summary
                        for concept_id in tier2_concept_ids:
                            if concept_id and concept_id.lower() in summary_text.lower():
                                runbook_format_checks_passed = False
                                runbook_format_violations.append(
                                    f"Summary contains Tier-2 concept ID '{concept_id}' (should only appear in context_concepts)"
                                )
                    
                    # Check that evidence_bullets count equals len(tier1_facts)
                    evidence_bullets = structured_data.get('evidence_bullets', [])
                    tier1_facts = structured_data.get('tier1_facts', [])
                    if len(evidence_bullets) != len(tier1_facts):
                        runbook_format_checks_passed = False
                        runbook_format_violations.append(
                            f"evidence_bullets count ({len(evidence_bullets)}) does not equal tier1_facts count ({len(tier1_facts)})"
                        )
            else:
                # If /ask failed, we can't check, so mark as failed
                if has_forbidden_fields:
                    negative_checks_passed = False
                    negative_violations = ["Failed to query /ask endpoint for negative evidence check"]
                if require_provenance:
                    provenance_checks_passed = False
                    provenance_violations = ["Failed to query /ask endpoint for provenance check"]
                if require_tiering:
                    tiering_checks_passed = False
                    tiering_violations = ["Failed to query /ask endpoint for tiering check"]
                if require_runbook_format:
                    runbook_format_checks_passed = False
                    runbook_format_violations = ["Failed to query /ask endpoint for runbook format check"]
        
        # Update counters
        if top1_correct:
            correct_at_1 += 1
        if hit_at_k:
            hits_at_k += 1
        if not negative_checks_passed:
            negative_evidence_failures += 1
        if not provenance_checks_passed:
            negative_evidence_failures += 1  # Count provenance failures in same counter
        if not tiering_checks_passed:
            negative_evidence_failures += 1  # Count tiering failures in same counter
        if not runbook_format_checks_passed:
            negative_evidence_failures += 1  # Count runbook format failures in same counter
        
        # Record failure if not correct OR if negative evidence check failed OR if provenance check failed OR if tiering check failed OR if runbook format check failed
        if not top1_correct or not hit_at_k or not negative_checks_passed or not provenance_checks_passed or not tiering_checks_passed or not runbook_format_checks_passed:
            failure_entry = {
                "query": query,
                "expected_incident_ids": expected_ids,
                "predicted_incident_ids": predicted_ids,
                "top1_correct": top1_correct,
                "hit_at_k": hit_at_k,
                "negative_checks_passed": negative_checks_passed,
                "negative_violations": negative_violations,
                "provenance_checks_passed": provenance_checks_passed,
                "provenance_violations": provenance_violations,
                "tiering_checks_passed": tiering_checks_passed,
                "tiering_violations": tiering_violations,
                "runbook_format_checks_passed": runbook_format_checks_passed,
                "runbook_format_violations": runbook_format_violations
            }
            failures.append(failure_entry)
    
    return failures, correct_at_1, hits_at_k, negative_evidence_failures


def write_results(output_file: str, base_url: str, k: int, n: int, 
                  accuracy_at_1: float, recall_at_k: float, failures: List[Dict[str, Any]]):
    """Write evaluation results to JSON file."""
    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "base_url": base_url,
        "k": k,
        "n": n,
        "accuracy_at_1": accuracy_at_1,
        "recall_at_k": recall_at_k,
        "failures": failures
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing results file: {e}", file=sys.stderr)
        sys.exit(2)


def print_summary(n: int, accuracy_at_1: float, recall_at_k: float, failures: List[Dict[str, Any]], negative_evidence_failures: int = 0):
    """Print evaluation summary and failures."""
    print("\n" + "=" * 60)
    print("Evaluation Summary")
    print("=" * 60)
    print(f"Total queries: {n}")
    print(f"Accuracy@1: {accuracy_at_1:.4f} ({accuracy_at_1 * 100:.2f}%)")
    print(f"Recall@k: {recall_at_k:.4f} ({recall_at_k * 100:.2f}%)")
    print(f"Retrieval failures: {len([f for f in failures if not f.get('top1_correct') or not f.get('hit_at_k')])}")
    print(f"Negative-evidence failures: {negative_evidence_failures}")
    print(f"Total failures: {len(failures)}")
    
    if failures:
        print("\nFirst up to 5 failures:")
        print("-" * 60)
        for i, failure in enumerate(failures[:5], 1):
            print(f"\nFailure {i}:")
            print(f"  Query: {failure['query']}")
            print(f"  Expected: {failure['expected_incident_ids']}")
            print(f"  Predicted: {failure['predicted_incident_ids']}")
            if 'top1_correct' in failure:
                print(f"  Top1 correct: {failure['top1_correct']}")
            if 'hit_at_k' in failure:
                print(f"  Hit@k: {failure['hit_at_k']}")
            if 'negative_checks_passed' in failure and not failure.get('negative_checks_passed', True):
                print(f"  Negative evidence check: FAILED")
                if 'negative_violations' in failure:
                    for violation in failure['negative_violations']:
                        print(f"    - {violation}")
            elif 'negative_checks_passed' in failure:
                print(f"  Negative evidence check: PASSED")
            if 'provenance_checks_passed' in failure and not failure.get('provenance_checks_passed', True):
                print(f"  Provenance check: FAILED")
                if 'provenance_violations' in failure:
                    for violation in failure['provenance_violations']:
                        print(f"    - {violation}")
            elif 'provenance_checks_passed' in failure:
                print(f"  Provenance check: PASSED")
            if 'tiering_checks_passed' in failure and not failure.get('tiering_checks_passed', True):
                print(f"  Tiering check: FAILED")
                if 'tiering_violations' in failure:
                    for violation in failure['tiering_violations']:
                        print(f"    - {violation}")
            elif 'tiering_checks_passed' in failure:
                print(f"  Tiering check: PASSED")
            if 'runbook_format_checks_passed' in failure and not failure.get('runbook_format_checks_passed', True):
                print(f"  Runbook format check: FAILED")
                if 'runbook_format_violations' in failure:
                    for violation in failure['runbook_format_violations']:
                        print(f"    - {violation}")
            elif 'runbook_format_checks_passed' in failure:
                print(f"  Runbook format check: PASSED")
    print("=" * 60)


def get_output_filename(gold_file: str) -> str:
    """Generate output filename from golden file path."""
    import os
    base_name = os.path.basename(gold_file)
    stem = os.path.splitext(base_name)[0]  # Remove .jsonl extension
    return f"eval/results_{stem}.json"


def evaluate_single_file(base_url: str, gold_file: str, k: int) -> Tuple[str, Dict[str, Any]]:
    """
    Evaluate a single golden file and return results.
    
    Returns:
        (output_file, results_dict)
    """
    # Read golden queries
    golden_queries = read_golden_queries(gold_file)
    if not golden_queries:
        print(f"Error: No valid queries found in {gold_file}", file=sys.stderr)
        sys.exit(2)
    
    n = len(golden_queries)
    
    # Evaluate queries
    failures, correct_at_1, hits_at_k, negative_evidence_failures = evaluate_queries(base_url, golden_queries, k)
    
    # Calculate metrics
    accuracy_at_1 = correct_at_1 / n if n > 0 else 0.0
    recall_at_k = hits_at_k / n if n > 0 else 0.0
    
    # Generate output filename
    output_file = get_output_filename(gold_file)
    
    # Prepare results
    results = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "base_url": base_url,
        "k": k,
        "n": n,
        "accuracy_at_1": accuracy_at_1,
        "recall_at_k": recall_at_k,
        "negative_evidence_failures": negative_evidence_failures,
        "failures": failures
    }
    
    # Write results
    write_results(output_file, base_url, k, n, accuracy_at_1, recall_at_k, failures)
    
    return output_file, results


def print_combined_summary(all_results: List[Tuple[str, Dict[str, Any]]]):
    """Print combined summary for multiple evaluation files."""
    print("\n" + "=" * 70)
    print("Combined Evaluation Summary")
    print("=" * 70)
    
    total_failures = 0
    for gold_file, results in all_results:
        n = results['n']
        accuracy_at_1 = results['accuracy_at_1']
        recall_at_k = results['recall_at_k']
        failures_count = len(results['failures'])
        total_failures += failures_count
        
        print(f"\n{gold_file}:")
        print(f"  Total queries: {n}")
        print(f"  Accuracy@1: {accuracy_at_1:.4f} ({accuracy_at_1 * 100:.2f}%)")
        print(f"  Recall@k: {recall_at_k:.4f} ({recall_at_k * 100:.2f}%)")
        print(f"  Failures: {failures_count}")
        
        # Print first 3 failures for this file
        if results['failures']:
            print(f"  First failures:")
            for i, failure in enumerate(results['failures'][:3], 1):
                print(f"    {i}. Query: {failure['query'][:60]}...")
                print(f"       Expected: {failure['expected_incident_ids']}, "
                      f"Predicted: {failure['predicted_incident_ids'][:3]}")
    
    print("\n" + "=" * 70)
    print(f"Total failures across all files: {total_failures}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate GraphRAG /query endpoint against golden queries"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://127.0.0.1:8000",
        help="Base URL of the API (default: http://127.0.0.1:8000)"
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Value of k for recall@k metric (default: 5)"
    )
    parser.add_argument(
        "--gold",
        type=str,
        action="append",
        default=None,
        help="Path to golden queries JSONL file (can be provided multiple times)"
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Path to output results JSON file (deprecated: auto-generated from gold file name)"
    )
    
    args = parser.parse_args()
    
    # Validate k
    if args.k < 1:
        print("Error: --k must be >= 1", file=sys.stderr)
        sys.exit(2)
    
    # Determine which golden files to use
    if args.gold:
        gold_files = args.gold
    else:
        # Default behavior: use single default file
        gold_files = ["eval/golden_queries.jsonl"]
    
    # Check API health once before starting
    if not check_api_health(args.base_url):
        print(f"Error: API at {args.base_url} is not reachable. Check /health endpoint.", file=sys.stderr)
        sys.exit(2)
    
    # Evaluate each file
    all_results = []
    all_output_files = []
    
    for gold_file in gold_files:
        print(f"\n{'='*70}")
        print(f"Evaluating: {gold_file}")
        print(f"{'='*70}")
        
        output_file, results = evaluate_single_file(args.base_url, gold_file, args.k)
        all_results.append((gold_file, results))
        all_output_files.append(output_file)
        
        # Print summary for this file
        print_summary(
            results['n'],
            results['accuracy_at_1'],
            results['recall_at_k'],
            results['failures'],
            results.get('negative_evidence_failures', 0)
        )
    
    # Print combined summary if multiple files
    if len(gold_files) > 1:
        print_combined_summary(all_results)
    
    # Determine exit code: 0 if no failures in any file, 1 if any failures
    total_failures = sum(len(r['failures']) for _, r in all_results)
    exit_code = 0 if total_failures == 0 else 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

