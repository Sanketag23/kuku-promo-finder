# Kuku Microdrama Promo Finder (Problem 1)

Automated AI Promo / Ad Detector engineered for microdrama streaming platforms (like Kuku, ReelShort, DramaBox). Parses screenplay scripts across 50 episodes, identifies high-energy 20–60 second windows, scores hook and cliffhanger strength, and ranks top viral ad cuts.

---

## 🌟 Key Features

1. **Two-Stage Hybrid Architecture:**
   - **Stage 1 (Rule-based Pre-Filter):** Extracts sliding candidate windows and evaluates emotional density, character conflict, and camera actions.
   - **Stage 2 (LLM / Semantic Scorer):** Scores candidates across 5 weighted dimensions (Hook, Cliffhanger, Standalone clarity, Emotional charge, Visual punch).
2. **Interactive Streamlit Web Dashboard:**
   - Real-time weight tuning (adjust Hook vs. Cliffhanger importance).
   - Instant search, playback excerpt inspection, and CSV export.
   - **Live Screenplay Ingest Mode:** Paste or upload any new screenplay during an interview to extract promos in < 15 seconds.
3. **Transparent Failure Analysis:** Identifies edge cases (visual humor, complex lineage lore) where text-only analysis requires human-in-the-loop oversight.

---

## 🚀 Quickstart & Installation

### 1. Clone & Install Dependencies
```bash
git clone <repo-url>
cd Kuku_Technologies_Assignment
python3 -m pip install -r requirements.txt
```

### 2. Run the Full Batch Pipeline
Processes all 50 episodes and outputs clean JSON & CSV rankings into `raw_outputs/`:
```bash
python3 src/pipeline.py
```

### 3. Launch the Interactive Web Dashboard
```bash
streamlit run app.py
```

---

## 📁 Repository Structure

```
Kuku_Technologies_Assignment/
├── src/
│   ├── parser.py              # Parses .txt screenplay structure, scenes, dialogues & timestamps
│   ├── window_generator.py    # Sliding window generator (20-60s) with emotion heuristic filters
│   ├── scorer.py              # Multi-model scorer (Gemini API + fallback heuristic evaluation)
│   ├── ranker.py              # Deduplicates temporal overlaps, balances diversity, exports CSV
│   ├── pipeline.py            # End-to-end pipeline orchestrator
│   └── config.py              # Hyperparameters, paths, and scoring weights
├── raw_outputs/
│   ├── all_parsed_episodes.json    # Structured JSON of all 50 episodes
│   ├── all_candidate_windows.json  # 167 pre-filtered candidate windows
│   ├── all_scored_promos.json      # Full scored candidates
│   ├── final_ranked_promos.json    # Curated Top 15 promos with reasons & strategies
│   ├── final_ranked_promos.csv     # Exportable spreadsheet for editorial team
│   └── failure_analysis.json       # Structural edge-case documentation
├── app.py                     # Streamlit web app
├── solution_doc.md            # 2-Page Executive Solution Document
├── requirements.txt           # Dependencies
└── README.md                  # Project documentation
```

---

## ⚖️ Composite Scoring Formula

$$\text{Composite Score} = 0.35 \times \text{Hook} + 0.35 \times \text{Cliffhanger} + 0.15 \times \text{Standalone} + 0.10 \times \text{Emotional} + 0.05 \times \text{Visual}$$

- **Hook:** Stopping power in the first 3 seconds (shocking reveal, slap, harsh accusation).
- **Cliffhanger:** Peak tension cutoff before resolution.
- **Standalone:** Comprehensibility for a cold user who has never seen the series.

