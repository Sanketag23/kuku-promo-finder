"""
Multi-Model Promo Scorer for Kuku Microdrama.
Supports:
1. Gemini API (via google-generativeai — free tier, 15 RPM)
2. Context-Aware Expert Heuristic Evaluator (offline / zero cost / fallback)

Each candidate's actual dialogue lines, character emotions, and camera cues
are extracted and analyzed to produce unique, episode-specific evaluations.
"""

import os
import re
import json
import time
from typing import Dict, Any, Optional, List, Tuple
from config import GEMINI_API_KEY, MODEL_NAME, DEFAULT_WEIGHTS


# ---------------------------------------------------------------------------
# Excerpt text analysis helpers
# ---------------------------------------------------------------------------

def _parse_excerpt_elements(excerpt: str) -> List[Dict[str, Any]]:
    """Parse the formatted excerpt back into structured element dicts."""
    elements = []
    for line in excerpt.splitlines():
        line = line.strip()
        if not line:
            continue
        # Format: [MM:SS.SS - MM:SS.SS] CHARACTER (Emotion): "text"
        #     or: [MM:SS.SS - MM:SS.SS] [ACTION]: text
        m = re.match(
            r'\[([^\]]+)\s*-\s*([^\]]+)\]\s*(.*)', line
        )
        if not m:
            continue
        ts_start, ts_end, rest = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()

        if rest.startswith("[ACTION]:"):
            elements.append({"type": "ACTION", "text": rest[9:].strip(), "ts": ts_start})
        elif rest.startswith("[CAMERA]:"):
            elements.append({"type": "CAMERA", "text": rest[9:].strip(), "ts": ts_start})
        elif rest.startswith("[SOUND FX]:"):
            elements.append({"type": "SOUND", "text": rest[11:].strip(), "ts": ts_start})
        else:
            # Dialogue: CHARACTER (Emotion): "text"
            dm = re.match(r'([A-Z][A-Z\s\'.]+?)(?:\s*\(([^)]*)\))?\s*:\s*"?(.*?)"?\s*$', rest)
            if dm:
                elements.append({
                    "type": "DIALOGUE",
                    "character": dm.group(1).strip(),
                    "emotion": (dm.group(2) or "").strip(),
                    "text": dm.group(3).strip().strip('"'),
                    "ts": ts_start
                })
            else:
                elements.append({"type": "OTHER", "text": rest, "ts": ts_start})
    return elements


def _get_dialogue_lines(elements: List[Dict]) -> List[Dict]:
    return [e for e in elements if e["type"] == "DIALOGUE"]


def _get_first_n_elements(elements: List[Dict], n: int = 3) -> List[Dict]:
    return elements[:n]


def _get_last_n_elements(elements: List[Dict], n: int = 3) -> List[Dict]:
    return elements[-n:] if len(elements) >= n else elements


def _extract_hook_description(elements: List[Dict]) -> str:
    """Build a unique, specific description of the hook based on actual opening content."""
    first_elems = _get_first_n_elements(elements, 4)
    parts = []

    for el in first_elems:
        if el["type"] == "DIALOGUE":
            char = el["character"].title()
            emo = f" ({el['emotion'].lower()})" if el.get("emotion") else ""
            line = el["text"]
            if len(line) > 60:
                line = line[:57] + "..."
            parts.append(f'{char}{emo} says: "{line}"')
        elif el["type"] == "ACTION":
            txt = el["text"]
            if len(txt) > 50:
                txt = txt[:47] + "..."
            parts.append(f"Visual action: {txt}")
        elif el["type"] == "CAMERA":
            txt = el["text"]
            if "close-up" in txt.lower() or "extreme" in txt.lower():
                parts.append(f"Cinematic punch: {txt[:50]}")

    if not parts:
        return "Opens with immediate dramatic tension"

    return "; ".join(parts[:2])


def _extract_cliff_description(elements: List[Dict]) -> str:
    """Build a unique, specific description of the cliffhanger based on actual ending content."""
    last_elems = _get_last_n_elements(elements, 4)
    parts = []

    for el in last_elems:
        if el["type"] == "DIALOGUE":
            char = el["character"].title()
            line = el["text"]
            if len(line) > 55:
                line = line[:52] + "..."
            if "?" in el["text"]:
                parts.append(f'Cuts on unanswered question — {char}: "{line}"')
            else:
                parts.append(f'{char} delivers: "{line}" — then cut')
        elif el["type"] == "SOUND":
            if any(w in el["text"].lower() for w in ["drone", "swell", "cliffhanger", "ominous"]):
                parts.append("Ominous audio swell into hard cut")
        elif el["type"] == "CAMERA":
            if "black" in el["text"].lower():
                parts.append("Smash cut to black")
            elif any(w in el["text"].lower() for w in ["close-up", "tears", "fury", "defiance"]):
                parts.append(f"Final frame: {el['text'][:45]}")

    if not parts:
        return "Cuts at peak unresolved tension"

    return "; ".join(parts[:2])


def _generate_caption(elements: List[Dict], episode: int) -> str:
    """Generate a unique viral social media caption based on actual dialogue content."""
    dialogues = _get_dialogue_lines(elements)

    # Find the most shocking / emotionally charged line
    best_line = None
    best_score = 0
    shock_words = {"never", "betray", "marry", "love", "liar", "kill", "die", "hate",
                   "mine", "changed", "leave", "sister", "husband", "wife", "truth",
                   "secret", "father", "mother", "duke", "soldier", "broken", "worthless"}

    for d in dialogues:
        txt_lower = d["text"].lower()
        score = sum(1 for w in shock_words if w in txt_lower)
        if "!" in d["text"]:
            score += 1
        if "?" in d["text"]:
            score += 1
        emo = d.get("emotion", "").lower()
        if any(e in emo for e in ["devastat", "furious", "betray", "shocked", "crying", "cold", "cruel"]):
            score += 2
        if score > best_score:
            best_score = score
            best_line = d

    if best_line:
        line = best_line["text"]
        if len(line) > 50:
            line = line[:47] + "..."
        char = best_line["character"].title()
        emojis = ["💔", "😱", "🔥", "💀", "👀", "😤", "🥺", "⚡"]
        emoji = emojis[episode % len(emojis)]
        return f'"{line}" {emoji} #MicroDrama #ShortSeries'

    # Fallback: use character names
    chars = list(set(d["character"].title() for d in dialogues))
    if len(chars) >= 2:
        return f"{chars[0]} vs {chars[1]} — who will break first? 🔥 #MicroDrama"
    return f"Episode {episode} will leave you speechless 💔 #MicroDrama #ShortSeries"


def _compute_why_it_works(elements: List[Dict], hook_desc: str, cliff_desc: str) -> str:
    """Generate a unique 'why this promo works' line based on actual content analysis."""
    dialogues = _get_dialogue_lines(elements)
    chars = list(set(d["character"].title() for d in dialogues))
    emotions = [d.get("emotion", "") for d in dialogues if d.get("emotion")]

    has_confrontation = any("!" in d["text"] for d in dialogues)
    has_question = any("?" in d["text"] for d in dialogues)
    char_count = len(chars)

    parts = []
    if char_count >= 3:
        parts.append(f"Multi-character clash between {', '.join(chars[:3])}")
    elif char_count == 2:
        parts.append(f"Intense face-off between {chars[0]} and {chars[1]}")
    elif char_count == 1:
        parts.append(f"Raw solo emotional breakdown from {chars[0]}")

    if has_confrontation and has_question:
        parts.append("rapid accusation-and-denial rhythm keeps viewers locked in")
    elif has_confrontation:
        parts.append("explosive verbal confrontation creates instant dramatic stakes")
    elif has_question:
        parts.append("unanswered questions build mystery that demands resolution")

    if emotions:
        top_emos = list(set(e.lower() for e in emotions[:4]))
        parts.append(f"emotional range ({', '.join(top_emos[:3])})")

    return "; ".join(parts) if parts else "High dramatic density with clear conflict and unresolved tension"


# ---------------------------------------------------------------------------
# Gemini API Scorer
# ---------------------------------------------------------------------------

def score_with_gemini(candidate: Dict[str, Any], api_key: str) -> Optional[Dict[str, Any]]:
    """Evaluates a candidate using Gemini API with rich, episode-specific analysis."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(MODEL_NAME)

        prompt = f"""You are a senior social media creative director at a microdrama streaming app (like ReelShort, DramaBox, Kuku).
Evaluate this specific {candidate['duration_sec']}-second screenplay clip as a promo ad for TikTok, Instagram Reels, and YouTube Shorts.

EPISODE: {candidate['episode']}
CLIP: {candidate['start_ts']} to {candidate['end_ts']} (Duration: {candidate['duration_sec']}s)

FULL CLIP SCRIPT:
{candidate['excerpt']}

Score each dimension STRICTLY 1.0 to 10.0 with a SPECIFIC reason referencing actual dialogue or actions from this clip:

1. hook_score: Will the first 3 seconds stop a scrolling viewer? Reference the specific opening line or visual.
2. cliffhanger_score: Does the cut point create irresistible "need to know"? Reference what's unresolved.
3. standalone_score: Can someone who has NEVER seen this show understand the stakes? Why or why not?
4. emotional_intensity: How raw is the emotional charge? Reference specific character moments.
5. visual_cinematic: Based on camera directions, how visually gripping is this?

Reply ONLY in valid JSON:
{{
  "hook_score": 8.5,
  "hook_reason": "Opens with [specific line/action from this clip]...",
  "cliffhanger_score": 9.0,
  "cliffhanger_reason": "Cuts right as [specific unresolved moment]...",
  "standalone_score": 8.0,
  "standalone_reason": "A viewer instantly understands [specific conflict]...",
  "emotional_intensity": 9.0,
  "emotional_reason": "[Character] delivers [specific line] with [emotion]...",
  "visual_cinematic": 8.0,
  "visual_reason": "[Specific camera direction] creates visual impact...",
  "why_it_works": "One compelling sentence about why THIS specific clip converts viewers",
  "suggested_caption": "A unique, viral TikTok/IG caption using a quote or hook from this clip"
}}"""

        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"  [Gemini API fallback] {e}")
        return None


# ---------------------------------------------------------------------------
# Context-Aware Expert Heuristic Scorer (offline fallback)
# ---------------------------------------------------------------------------

def score_with_expert_heuristics(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Context-aware deterministic scorer that reads actual dialogue/actions
    from the clip excerpt to produce unique, episode-specific evaluations.
    """
    excerpt = candidate.get("excerpt", "")
    elements = _parse_excerpt_elements(excerpt)
    dialogues = _get_dialogue_lines(elements)
    chars = list(set(d["character"].title() for d in dialogues))
    episode = candidate.get("episode", 0)

    # --- Hook Score ---
    first_elems = _get_first_n_elements(elements, 4)
    hook_score = 6.5
    for el in first_elems:
        if el["type"] == "DIALOGUE":
            hook_score += 1.0
            emo = el.get("emotion", "").lower()
            if any(w in emo for w in ["shocked", "furious", "desperate", "cold", "smug",
                                       "devastated", "gasping", "mocking", "malicious",
                                       "commanding", "heartbroken", "trembling", "crying"]):
                hook_score += 1.2
            txt = el.get("text", "").lower()
            if any(w in txt for w in ["marry", "betray", "kill", "never", "mine", "leave"]):
                hook_score += 0.8
            if "!" in el.get("text", ""):
                hook_score += 0.5
        elif el["type"] == "ACTION":
            if any(w in el["text"].lower() for w in ["slap", "grab", "shove", "tears", "kneel",
                                                       "blood", "sword", "collapse", "terrified"]):
                hook_score += 1.5
        elif el["type"] == "CAMERA":
            if any(w in el["text"].lower() for w in ["close-up", "extreme", "push-in"]):
                hook_score += 0.6

    hook_score = min(round(hook_score, 1), 9.8)
    hook_reason = _extract_hook_description(elements)

    # --- Cliffhanger Score ---
    last_elems = _get_last_n_elements(elements, 4)
    cliff_score = 6.5
    for el in last_elems:
        if el["type"] == "DIALOGUE":
            cliff_score += 0.8
            if "?" in el.get("text", ""):
                cliff_score += 1.8
            emo = el.get("emotion", "").lower()
            if any(w in emo for w in ["desperate", "trembling", "furious", "horrified",
                                       "cold", "defiant", "begging"]):
                cliff_score += 1.0
            txt = el.get("text", "").lower()
            if any(w in txt for w in ["who", "why", "what", "how long", "never"]):
                cliff_score += 0.6
        elif el["type"] == "SOUND":
            if any(w in el["text"].lower() for w in ["drone", "swell", "cliffhanger", "ominous"]):
                cliff_score += 1.5
        elif el["type"] == "CAMERA":
            if "black" in el["text"].lower():
                cliff_score += 1.0
            if any(w in el["text"].lower() for w in ["fury", "defiance", "tears", "knuckles"]):
                cliff_score += 0.8

    cliff_score = min(round(cliff_score, 1), 9.9)
    cliff_reason = _extract_cliff_description(elements)

    # --- Standalone Score ---
    standalone_score = 7.0
    standalone_parts = []
    if len(chars) >= 2:
        standalone_score += 1.0
        standalone_parts.append(f"Clear conflict between {chars[0]} and {chars[1]}")
    relationship_words = ["sister", "father", "mother", "husband", "wife", "fiancé",
                          "groom", "bride", "duke", "soldier", "brother"]
    found_rels = [w for w in relationship_words if w in excerpt.lower()]
    if found_rels:
        standalone_score += 1.0
        standalone_parts.append(f"Universally understood relationship ({', '.join(found_rels[:2])})")
    else:
        standalone_score -= 0.8
        standalone_parts.append("May require some character context for cold viewers")
    standalone_score = min(round(standalone_score, 1), 9.5)
    standalone_reason = "; ".join(standalone_parts) if standalone_parts else "Self-contained dramatic beat"

    # --- Emotional Intensity ---
    emotional_score = 6.8
    hot_emotions = {"devastated", "furious", "heartbroken", "crying", "choking",
                    "trembling", "outraged", "desperate", "cold", "cruel", "malicious",
                    "scornful", "arrogant", "begging", "piercing", "shaken", "horrified"}
    found_emotions = set()
    for d in dialogues:
        emo = d.get("emotion", "").lower()
        for he in hot_emotions:
            if he in emo:
                emotional_score += 0.5
                found_emotions.add(he)
        if "!" in d.get("text", ""):
            emotional_score += 0.2
    emotional_score = min(round(emotional_score, 1), 9.8)
    if found_emotions:
        emotional_reason = f"Carries intense emotional palette: {', '.join(list(found_emotions)[:4])}"
    else:
        emotional_reason = "Steady dramatic tension throughout the clip"

    # --- Visual / Cinematic ---
    visual_score = 7.0
    cam_elements = [e for e in elements if e["type"] == "CAMERA"]
    if any("close-up" in e["text"].lower() for e in cam_elements):
        visual_score += 0.8
    if any("tracking" in e["text"].lower() for e in cam_elements):
        visual_score += 0.5
    if any("extreme" in e["text"].lower() for e in cam_elements):
        visual_score += 0.7
    visual_score = min(round(visual_score, 1), 9.5)
    visual_reason = f"{len(cam_elements)} camera setups with varied framing" if cam_elements else "Standard coverage"

    why_it_works = _compute_why_it_works(elements, hook_reason, cliff_reason)
    caption = _generate_caption(elements, episode)

    return {
        "hook_score": hook_score,
        "hook_reason": hook_reason,
        "cliffhanger_score": cliff_score,
        "cliffhanger_reason": cliff_reason,
        "standalone_score": standalone_score,
        "standalone_reason": standalone_reason,
        "emotional_intensity": emotional_score,
        "emotional_reason": emotional_reason,
        "visual_cinematic": visual_score,
        "visual_reason": visual_reason,
        "why_it_works": why_it_works,
        "target_audience_appeal": "High drama, revenge romance, social video audiences",
        "suggested_caption": caption
    }


# ---------------------------------------------------------------------------
# Public scoring API
# ---------------------------------------------------------------------------

def score_candidate(candidate: Dict[str, Any], api_key: str = GEMINI_API_KEY) -> Dict[str, Any]:
    """Scores candidate using Gemini API if key exists, otherwise falls back to context-aware heuristics."""
    evaluation = None
    scoring_method = "heuristic"

    if api_key and len(api_key.strip()) > 5:
        evaluation = score_with_gemini(candidate, api_key)
        if evaluation:
            scoring_method = "gemini"

    if not evaluation:
        evaluation = score_with_expert_heuristics(candidate)

    # Compute composite score
    weights = DEFAULT_WEIGHTS
    composite = round(
        (evaluation.get("hook_score", 7.0) * weights["hook"]) +
        (evaluation.get("cliffhanger_score", 7.0) * weights["cliffhanger"]) +
        (evaluation.get("standalone_score", 7.0) * weights["standalone"]) +
        (evaluation.get("emotional_intensity", 7.0) * weights["emotional"]) +
        (evaluation.get("visual_cinematic", 7.0) * weights["visual"]),
        2
    )

    result = dict(candidate)
    result["scores"] = evaluation
    result["composite_score"] = composite
    result["hook"] = evaluation.get("hook_reason", "")
    result["cliffhanger"] = evaluation.get("cliffhanger_reason", "")
    result["why_it_works"] = evaluation.get("why_it_works", "")
    result["scoring_method"] = scoring_method
    return result


def score_all_candidates(candidates: list, api_key: str = GEMINI_API_KEY) -> list:
    scored = []
    for i, c in enumerate(candidates):
        sc = score_candidate(c, api_key=api_key)
        scored.append(sc)
        if api_key and len(api_key.strip()) > 5 and sc.get("scoring_method") == "gemini":
            # Respect Gemini free tier rate limit (15 RPM)
            if (i + 1) % 14 == 0:
                print(f"  Rate limit pause after {i+1} API calls...")
                time.sleep(62)
    return scored


if __name__ == "__main__":
    from config import RAW_OUTPUTS_DIR
    in_file = os.path.join(RAW_OUTPUTS_DIR, "all_candidate_windows.json")
    with open(in_file, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    print(f"Scoring {len(candidates)} candidate promos...")
    scored = score_all_candidates(candidates)

    out_file = os.path.join(RAW_OUTPUTS_DIR, "all_scored_promos.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(scored, f, indent=2)

    method = scored[0].get("scoring_method", "heuristic") if scored else "N/A"
    print(f"Saved scored promos to {out_file} (Method: {method}, Sample composite: {scored[0]['composite_score']})")
