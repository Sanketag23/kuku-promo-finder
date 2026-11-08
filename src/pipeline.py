"""
End-to-End Orchestrator Pipeline for Kuku Microdrama Promo Extraction.
Takes a folder of screenplays or single screenplay text and runs:
Parser -> Window Generator -> Scorer -> Ranker & Deduplicator
"""

import os
import sys
import json
from typing import List, Dict, Any, Optional

# Ensure src path is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from parser import parse_screenplay_text, parse_screenplay_file, parse_all_episodes
from window_generator import generate_candidates_for_episode, generate_all_candidates
from scorer import score_all_candidates, score_candidate
from ranker import rank_and_deduplicate, generate_failure_analysis, export_to_csv
from config import SCRIPTS_DIR, RAW_OUTPUTS_DIR, GEMINI_API_KEY

def run_pipeline_on_episodes(episodes: List[Dict[str, Any]], top_k: int = 15, api_key: str = GEMINI_API_KEY) -> Dict[str, Any]:
    """Runs promo detection and ranking on a list of parsed episodes."""
    # 1. Candidate Generation
    candidates = generate_all_candidates(episodes)
    
    # 2. Scoring
    scored = score_all_candidates(candidates, api_key=api_key)
    
    # 3. Ranking & Deduplication
    ranked = rank_and_deduplicate(scored, top_k=top_k)
    
    # 4. Failure analysis
    failures = generate_failure_analysis(scored)
    
    return {
        "total_episodes": len(episodes),
        "total_candidates": len(candidates),
        "ranked_promos": ranked,
        "failure_analysis": failures
    }

def run_pipeline_on_text(script_text: str, filename: str = "new_episode.txt", top_k: int = 3, api_key: str = GEMINI_API_KEY) -> Dict[str, Any]:
    """
    Runs promo detection on an uploaded screenplay text (ideal for the live interview).
    """
    ep = parse_screenplay_text(script_text, filename=filename)
    candidates = generate_candidates_for_episode(ep)
    scored = [score_candidate(c, api_key=api_key) for c in candidates]
    ranked = rank_and_deduplicate(scored, top_k=top_k)
    return {
        "episode_number": ep["episode_number"],
        "total_duration": ep["total_duration_ts"],
        "scene_count": ep["scene_count"],
        "ranked_promos": ranked
    }

def run_full_batch():
    """Batch run over all 50 show episodes."""
    print("=== STEP 1: PARSING SCREENPLAYS ===")
    episodes = parse_all_episodes(SCRIPTS_DIR)
    
    out_parsed = os.path.join(RAW_OUTPUTS_DIR, "all_parsed_episodes.json")
    with open(out_parsed, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2)

    print("=== STEP 2: GENERATING & SCORING CANDIDATES ===")
    results = run_pipeline_on_episodes(episodes, top_k=15)

    print("=== STEP 3: SAVING EXPORTS ===")
    out_ranked = os.path.join(RAW_OUTPUTS_DIR, "final_ranked_promos.json")
    with open(out_ranked, "w", encoding="utf-8") as f:
        json.dump(results["ranked_promos"], f, indent=2)

    out_csv = os.path.join(RAW_OUTPUTS_DIR, "final_ranked_promos.csv")
    export_to_csv(results["ranked_promos"], out_csv)

    out_failures = os.path.join(RAW_OUTPUTS_DIR, "failure_analysis.json")
    with open(out_failures, "w", encoding="utf-8") as f:
        json.dump(results["failure_analysis"], f, indent=2)

    print(f"Pipeline completed successfully! Top {len(results['ranked_promos'])} promos generated.")

if __name__ == "__main__":
    run_full_batch()

