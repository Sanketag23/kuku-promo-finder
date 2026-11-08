"""
Configuration for Kuku Microdrama Promo Detection Pipeline.
"""

import os

# Base paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "I Married a Broken Soldier. He was a Duke")
RAW_OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "raw_outputs")

# Promo constraints
MIN_PROMO_DURATION = 20.0  # seconds
MAX_PROMO_DURATION = 60.0  # seconds
HOOK_WINDOW_DURATION = 3.5  # first N seconds to evaluate hook
CLIFF_WINDOW_DURATION = 4.0  # last N seconds to evaluate cliffhanger

# Candidate generation settings
STEP_SIZE = 10.0  # seconds step for candidate window search
MAX_CANDIDATES_PER_EPISODE = 4  # top rule-filtered candidates to pass to scoring

# Default scoring weights (Composite score formula)
DEFAULT_WEIGHTS = {
    "hook": 0.35,
    "cliffhanger": 0.35,
    "standalone": 0.15,
    "emotional": 0.10,
    "visual": 0.05
}

# API configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL_NAME = "gemini-1.5-flash"

