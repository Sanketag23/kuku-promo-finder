"""
Parser for Kuku microdrama screenplays.
Extracts episode metadata, scene structure, timestamps, dialogue, actions, camera, and sound cues.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional

def parse_time_to_seconds(ts_str: str) -> float:
    """Converts MM:SS.SS or (MM:SS.SS) or SS.SS to float seconds."""
    clean = ts_str.strip(" ()[]")
    if ":" in clean:
        parts = clean.split(":")
        minutes = float(parts[0])
        seconds = float(parts[1])
        return round(minutes * 60 + seconds, 2)
    else:
        return round(float(clean), 2)

def seconds_to_timestamp(sec: float) -> str:
    """Converts float seconds back to MM:SS.SS format."""
    minutes = int(sec // 60)
    remainder = sec % 60
    return f"{minutes:02d}:{remainder:05.2f}"

def parse_screenplay_text(raw_text: str, filename: str = "") -> Dict[str, Any]:
    lines = raw_text.splitlines()
    
    episode_num = None
    logline = ""
    continuity = ""
    
    # Parse header metadata
    script_start_idx = 0
    for idx, line in enumerate(lines):
        line_clean = line.strip()
        if line_clean.startswith("EPISODE NUMBER:"):
            match = re.search(r'\d+', line_clean)
            if match:
                episode_num = int(match.group(0))
        elif line_clean.startswith("EPISODE LOGLINE:"):
            logline = line_clean.replace("EPISODE LOGLINE:", "").strip()
        elif line_clean.startswith("CONTINUITY NOTES:"):
            continuity = line_clean.replace("CONTINUITY NOTES:", "").strip()
        elif "--- SCRIPT START ---" in line_clean:
            script_start_idx = idx + 1
            break

    if episode_num is None and filename:
        match = re.search(r'episode-(\d+)', filename, re.IGNORECASE)
        if match:
            episode_num = int(match.group(1))
        else:
            episode_num = 1

    # Parse body scenes and elements
    scenes: List[Dict[str, Any]] = []
    current_scene: Optional[Dict[str, Any]] = None
    
    # Element parsing regex patterns
    # e.g.: **CAMERA:** or **ACTION:** or **LADY JULIANA (Confused, Breathless):**
    elem_header_pattern = re.compile(r'^\*\*([^*]+)\*\*:?$')
    # e.g.: Start: (00:00.00) | End: (00:04.80) or Start: 00:00.00 | End: 00:04.80
    time_pattern = re.compile(r'Start:\s*\(?([\d:.]+)\)?\s*\|\s*End:\s*\(?([\d:.]+)\)?')
    scene_start_pattern = re.compile(r'Scene start:\s*([\d:.]+)')
    scene_end_pattern = re.compile(r'Scene end:\s*([\d:.]+)')
    scene_heading_pattern = re.compile(r'Scene heading:\s*(.*)')

    i = script_start_idx
    max_len = len(lines)
    
    pending_type = None
    pending_character = None
    pending_emotion = None
    pending_start_sec = 0.0
    pending_end_sec = 0.0
    pending_text_lines = []

    def commit_pending_element():
        nonlocal pending_type, pending_character, pending_emotion, pending_start_sec, pending_end_sec, pending_text_lines
        if pending_type and current_scene is not None:
            text = " ".join([l.strip() for l in pending_text_lines if l.strip()])
            elem = {
                "type": pending_type,
                "start_sec": pending_start_sec,
                "end_sec": pending_end_sec,
                "start_ts": seconds_to_timestamp(pending_start_sec),
                "end_ts": seconds_to_timestamp(pending_end_sec),
                "duration_sec": round(pending_end_sec - pending_start_sec, 2),
                "text": text
            }
            if pending_character:
                elem["character"] = pending_character
            if pending_emotion:
                elem["emotion"] = pending_emotion
            current_scene["elements"].append(elem)
        
        pending_type = None
        pending_character = None
        pending_emotion = None
        pending_start_sec = 0.0
        pending_end_sec = 0.0
        pending_text_lines = []

    while i < max_len:
        line = lines[i].strip()
        
        if line.startswith("SCENE ") and not line.startswith("SCENE START"):
            commit_pending_element()
            scene_name = line
            scene_heading = ""
            s_start = 0.0
            s_end = 0.0
            
            # Look ahead for heading, start, end
            j = i + 1
            while j < min(i + 7, max_len):
                ahead = lines[j].strip()
                if ahead.startswith("Scene heading:"):
                    scene_heading = scene_heading_pattern.sub(r'\1', ahead).strip()
                elif ahead.startswith("Scene start:"):
                    m = scene_start_pattern.search(ahead)
                    if m:
                        s_start = parse_time_to_seconds(m.group(1))
                elif ahead.startswith("Scene end:"):
                    m = scene_end_pattern.search(ahead)
                    if m:
                        s_end = parse_time_to_seconds(m.group(1))
                elif ahead.startswith("Actions and dialogue:"):
                    j += 1
                    break
                j += 1
            
            current_scene = {
                "scene_name": scene_name,
                "heading": scene_heading,
                "start_sec": s_start,
                "end_sec": s_end,
                "elements": []
            }
            scenes.append(current_scene)
            i = j
            continue

        if "--- SCRIPT END ---" in line:
            commit_pending_element()
            break

        # Check for element header
        elem_match = elem_header_pattern.match(line)
        if elem_match:
            commit_pending_element()
            raw_tag = elem_match.group(1).strip().rstrip(":")
            
            # Determine type
            if raw_tag == "CAMERA":
                pending_type = "CAMERA"
            elif raw_tag == "ACTION":
                pending_type = "ACTION"
            elif raw_tag.startswith("SOUND"):
                pending_type = "SOUND"
            else:
                # Dialogue: Character (Emotion)
                pending_type = "DIALOGUE"
                if "(" in raw_tag and raw_tag.endswith(")"):
                    char_part, emot_part = raw_tag[:-1].split("(", 1)
                    pending_character = char_part.strip()
                    pending_emotion = emot_part.strip()
                else:
                    pending_character = raw_tag
                    pending_emotion = ""
            
            # Read next line for timestamps
            if i + 1 < max_len:
                time_line = lines[i+1].strip()
                tm = time_pattern.search(time_line)
                if tm:
                    pending_start_sec = parse_time_to_seconds(tm.group(1))
                    pending_end_sec = parse_time_to_seconds(tm.group(2))
                    i += 1  # Skip the timestamp line
            i += 1
            continue

        # Content line for pending element
        if pending_type:
            if line:
                pending_text_lines.append(line)
        
        i += 1

    commit_pending_element()

    # Calculate total duration
    total_duration_sec = 0.0
    for sc in scenes:
        if sc.get("end_sec", 0.0) > total_duration_sec:
            total_duration_sec = sc["end_sec"]
        for el in sc.get("elements", []):
            if el.get("end_sec", 0.0) > total_duration_sec:
                total_duration_sec = el["end_sec"]

    return {
        "episode_number": episode_num,
        "filename": filename,
        "logline": logline,
        "continuity": continuity,
        "total_duration_sec": round(total_duration_sec, 2),
        "total_duration_ts": seconds_to_timestamp(total_duration_sec),
        "scene_count": len(scenes),
        "scenes": scenes
    }

def parse_screenplay_file(filepath: str) -> Dict[str, Any]:
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    filename = os.path.basename(filepath)
    return parse_screenplay_text(text, filename)

def parse_all_episodes(scripts_dir: str) -> List[Dict[str, Any]]:
    files = sorted([f for f in os.listdir(scripts_dir) if f.endswith(".txt")])
    episodes = []
    for f in files:
        full_path = os.path.join(scripts_dir, f)
        ep_data = parse_screenplay_file(full_path)
        episodes.append(ep_data)
    return episodes

if __name__ == "__main__":
    from config import SCRIPTS_DIR, RAW_OUTPUTS_DIR
    print(f"Parsing all episodes from {SCRIPTS_DIR}...")
    episodes = parse_all_episodes(SCRIPTS_DIR)
    print(f"Successfully parsed {len(episodes)} episodes.")
    
    out_file = os.path.join(RAW_OUTPUTS_DIR, "all_parsed_episodes.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2)
    print(f"Saved parsed episodes to {out_file} (Sample: Ep 1 has {len(episodes[0]['scenes'])} scenes, total duration {episodes[0]['total_duration_ts']})")
