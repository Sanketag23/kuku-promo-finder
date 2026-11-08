"""
Candidate Window Generator for Microdrama Promos.
Extracts 20-60 second candidate segments across episodes using heuristic pre-filtering.
"""

import os
import json
import re
from typing import List, Dict, Any
from config import MIN_PROMO_DURATION, MAX_PROMO_DURATION, STEP_SIZE, MAX_CANDIDATES_PER_EPISODE
from parser import seconds_to_timestamp

# High-voltage emotion keywords
STRONG_EMOTIONS = {
    "shocked", "furious", "desperate", "betrayed", "trembling", "crying",
    "cold", "commanding", "malicious", "smug", "shaken", "heartbroken",
    "gasping", "devastated", "outraged", "accusing", "choking", "piercing",
    "mocking", "horrified", "unapologetic", "begging", "disgusted", "haughty",
    "raw", "painful", "venomous", "scornful", "hard", "arrogant", "defiance",
    "menacing", "lethal", "ruthless", "rage", "grief", "terror", "scared"
}

# High-conflict dialogue/action keywords
CONFLICT_TERMS = {
    "marry", "marriage", "wedding", "betrayal", "traitor", "affair", "sister",
    "duke", "soldier", "kill", "die", "bastard", "liar", "shame", "worthless",
    "slap", "kiss", "blood", "kneel", "proposal", "divorce", "money", "ruined",
    "embarrassed", "changed my mind", "leave", "disgrace", "revenge", "secret"
}

def flatten_episode_elements(episode_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flattens all elements in scenes into a chronological list."""
    elements = []
    for sc in episode_data.get("scenes", []):
        for el in sc.get("elements", []):
            el_copy = dict(el)
            el_copy["scene_name"] = sc.get("scene_name", "")
            el_copy["scene_heading"] = sc.get("heading", "")
            elements.append(el_copy)
    return sorted(elements, key=lambda x: x["start_sec"])

def calculate_heuristic_score(elements_in_window: List[Dict[str, Any]], window_duration: float) -> Dict[str, Any]:
    """Computes a rule-based heuristic score to rank promo candidates before LLM scoring."""
    if not elements_in_window:
        return {"total_score": 0.0, "reasons": []}

    score = 0.0
    reasons = []

    # 1. Hook evaluation (elements in the first 4.0 seconds)
    hook_elems = [e for e in elements_in_window if e["start_sec"] <= elements_in_window[0]["start_sec"] + 4.0]
    hook_score = 0.0
    for e in hook_elems:
        t = e.get("type", "")
        txt = e.get("text", "").lower()
        emo = e.get("emotion", "").lower()
        
        # Dialogue hook
        if t == "DIALOGUE":
            hook_score += 2.0
            if any(w in emo for w in STRONG_EMOTIONS):
                hook_score += 2.5
                reasons.append(f"Strong opening emotional tone: {e.get('emotion')}")
            if any(w in txt for w in CONFLICT_TERMS):
                hook_score += 2.0
                reasons.append("High-stakes conflict in opening line")
        # Visual/Camera hook
        elif t in ("CAMERA", "ACTION"):
            if any(term in txt for term in ["close-up", "extreme close-up", "slap", "drops", "intervene", "lethal", "kneel", "tears"]):
                hook_score += 2.0
                reasons.append(f"Visual punch in opening: {t}")

    # 2. Cliffhanger evaluation (elements in the last 4.5 seconds)
    cliff_elems = [e for e in elements_in_window if e["end_sec"] >= elements_in_window[-1]["end_sec"] - 4.5]
    cliff_score = 0.0
    for e in cliff_elems:
        txt = e.get("text", "").lower()
        emo = e.get("emotion", "").lower()
        t = e.get("type", "")
        
        if t == "DIALOGUE":
            cliff_score += 2.0
            if "?" in e.get("text", ""):
                cliff_score += 2.5
                reasons.append("Cliffhanger ends on provocative unanswered question")
            if any(w in emo for w in STRONG_EMOTIONS):
                cliff_score += 2.0
            if any(w in txt for w in CONFLICT_TERMS):
                cliff_score += 2.0
        elif t == "SOUND":
            if any(w in txt for w in ["drone", "swell", "cliffhanger", "ominous", "sharp"]):
                cliff_score += 3.0
                reasons.append("Audio cliffhanger swell at cutoff")
        elif t in ("CAMERA", "ACTION"):
            if any(w in txt for w in ["cut to black", "freeze", "tears", "defiance", "fury", "knuckles"]):
                cliff_score += 2.0
                reasons.append("Suspenseful visual posture at cut")

    # 3. Conflict and emotion density across whole window
    dialogue_count = 0
    characters = set()
    emotion_hits = 0
    conflict_hits = 0

    for e in elements_in_window:
        if e.get("type") == "DIALOGUE":
            dialogue_count += 1
            if e.get("character"):
                characters.add(e["character"])
            emo = e.get("emotion", "").lower()
            txt = e.get("text", "").lower()
            if any(w in emo for w in STRONG_EMOTIONS):
                emotion_hits += 1
            if any(w in txt for w in CONFLICT_TERMS):
                conflict_hits += 1

    # Bonus for 2 or 3 distinct characters actively interacting
    dialogue_score = min(dialogue_count * 0.8, 6.0)
    character_bonus = 3.0 if len(characters) >= 2 else 0.5
    emotion_bonus = min(emotion_hits * 1.5, 6.0)
    conflict_bonus = min(conflict_hits * 1.2, 6.0)

    # Ideal promo duration sweet spot: 30 - 50 seconds
    duration_factor = 1.0
    if 25.0 <= window_duration <= 55.0:
        duration_factor = 1.2

    total_score = round(
        (hook_score * 1.2 + cliff_score * 1.2 + dialogue_score + character_bonus + emotion_bonus + conflict_bonus) * duration_factor,
        2
    )

    return {
        "heuristic_score": total_score,
        "hook_heuristic": round(hook_score, 2),
        "cliff_heuristic": round(cliff_score, 2),
        "character_count": len(characters),
        "characters": list(characters),
        "dialogue_count": dialogue_count,
        "key_reasons": list(set(reasons))[:3]
    }

def format_window_excerpt(elements: List[Dict[str, Any]]) -> str:
    """Formats elements of a window into clean script text for LLM scoring or human review."""
    output_lines = []
    for el in elements:
        t = el.get("type")
        start_ts = el.get("start_ts", "")
        end_ts = el.get("end_ts", "")
        if t == "DIALOGUE":
            char = el.get("character", "SPEAKER")
            emo = f" ({el['emotion']})" if el.get("emotion") else ""
            txt = el.get("text", "")
            output_lines.append(f"[{start_ts} - {end_ts}] {char}{emo}: \"{txt}\"")
        elif t == "ACTION":
            output_lines.append(f"[{start_ts} - {end_ts}] [ACTION]: {el.get('text', '')}")
        elif t == "CAMERA":
            output_lines.append(f"[{start_ts} - {end_ts}] [CAMERA]: {el.get('text', '')}")
        elif t == "SOUND":
            output_lines.append(f"[{start_ts} - {end_ts}] [SOUND FX]: {el.get('text', '')}")
    return "\n".join(output_lines)

def generate_candidates_for_episode(episode_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generates and heuristic-scores candidate windows for a single episode."""
    elements = flatten_episode_elements(episode_data)
    if not elements:
        return []

    ep_total_sec = episode_data.get("total_duration_sec", 0.0)
    candidates = []

    # Slide start timestamp from 0 to ep_total_sec - MIN_PROMO_DURATION
    current_start = 0.0
    while current_start <= max(0.0, ep_total_sec - MIN_PROMO_DURATION):
        # Test varied window durations: 25s, 35s, 45s, 55s
        for dur in [25.0, 35.0, 45.0, 55.0]:
            candidate_end = min(current_start + dur, ep_total_sec)
            actual_dur = candidate_end - current_start
            if actual_dur < MIN_PROMO_DURATION or actual_dur > MAX_PROMO_DURATION:
                continue

            # Find matching elements
            window_elems = [
                e for e in elements
                if (e["start_sec"] >= current_start and e["start_sec"] <= candidate_end) or
                   (e["end_sec"] >= current_start and e["end_sec"] <= candidate_end) or
                   (e["start_sec"] <= current_start and e["end_sec"] >= candidate_end)
            ]

            if not window_elems or len(window_elems) < 3:
                continue

            # Snap exact start and end to element boundaries for clean cuts
            snapped_start_sec = max(current_start, window_elems[0]["start_sec"])
            snapped_end_sec = min(candidate_end, window_elems[-1]["end_sec"])
            final_dur = snapped_end_sec - snapped_start_sec
            
            if final_dur < MIN_PROMO_DURATION or final_dur > MAX_PROMO_DURATION:
                continue

            heur = calculate_heuristic_score(window_elems, final_dur)
            
            cand = {
                "episode": episode_data["episode_number"],
                "episode_filename": episode_data.get("filename", ""),
                "start_sec": round(snapped_start_sec, 2),
                "end_sec": round(snapped_end_sec, 2),
                "start_ts": seconds_to_timestamp(snapped_start_sec),
                "end_ts": seconds_to_timestamp(snapped_end_sec),
                "duration_sec": round(final_dur, 2),
                "heuristic_score": heur["heuristic_score"],
                "hook_heuristic": heur["hook_heuristic"],
                "cliff_heuristic": heur["cliff_heuristic"],
                "characters": heur["characters"],
                "dialogue_count": heur["dialogue_count"],
                "reasons": heur["key_reasons"],
                "excerpt": format_window_excerpt(window_elems),
                "element_count": len(window_elems)
            }
            candidates.append(cand)

        current_start += STEP_SIZE

    # Sort candidates by heuristic score descending
    candidates = sorted(candidates, key=lambda x: x["heuristic_score"], reverse=True)

    # Deduplicate overlapping candidates within the episode (keep highest scoring)
    filtered: List[Dict[str, Any]] = []
    for c in candidates:
        overlap = False
        for f in filtered:
            # Check overlap > 50%
            inter_start = max(c["start_sec"], f["start_sec"])
            inter_end = min(c["end_sec"], f["end_sec"])
            if inter_end > inter_start:
                inter_dur = inter_end - inter_start
                if inter_dur > 0.5 * min(c["duration_sec"], f["duration_sec"]):
                    overlap = True
                    break
        if not overlap:
            filtered.append(c)
        if len(filtered) >= MAX_CANDIDATES_PER_EPISODE:
            break

    return filtered

def generate_all_candidates(episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    all_cands = []
    for ep in episodes:
        cands = generate_candidates_for_episode(ep)
        all_cands.extend(cands)
    return all_cands

if __name__ == "__main__":
    from config import RAW_OUTPUTS_DIR
    in_file = os.path.join(RAW_OUTPUTS_DIR, "all_parsed_episodes.json")
    with open(in_file, "r", encoding="utf-8") as f:
        episodes = json.load(f)

    print(f"Generating candidate windows across {len(episodes)} episodes...")
    all_candidates = generate_all_candidates(episodes)
    print(f"Generated {len(all_candidates)} top candidate windows across 50 episodes.")

    out_file = os.path.join(RAW_OUTPUTS_DIR, "all_candidate_windows.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_candidates, f, indent=2)
    print(f"Saved candidate windows to {out_file}")
    
    # Print sample top candidate
    if all_candidates:
        top = all_candidates[0]
        print(f"\nTop Candidate: Ep {top['episode']} [{top['start_ts']} - {top['end_ts']}] "
              f"(Duration: {top['duration_sec']}s, Heuristic: {top['heuristic_score']})")
        print("Characters:", ", ".join(top["characters"]))
        print("Hook Reasons:", top["reasons"])

