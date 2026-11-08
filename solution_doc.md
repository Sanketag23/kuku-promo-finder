# KUKU AI GENERALIST ASSIGNMENT — SOLUTION DOCUMENT
**Candidate Name:** Sanket Agarwal  
**Roll No:** 230920  
**Problem Selected:** Problem 1 — Find the Promos (Ads)  
**Prototype Link:** [GitHub Repository / Streamlit App]  
**Raw Outputs Directory:** `/raw_outputs/` (includes `final_ranked_promos.json`, `final_ranked_promos.csv`, `failure_analysis.json`)

---

## 1. Problem Framing & Assumptions
Microdrama platforms (like Kuku, ReelShort) win or lose based on TikTok and Instagram Reels customer acquisition. Today, editors manually scrub through hours of footage to find 20–60 second clips. 
An automated system must identify clips that satisfy three essential criteria:
1. **Hook (First 3 seconds):** Visceral disruption that stops scroll behavior (e.g., betrayal at the altar, unexpected proposal, violent confrontation).
2. **Cliffhanger Cutoff:** Cuts at the maximum tension peak, compelling the viewer to download the app.
3. **Standalone Comprehensibility:** A stranger with zero prior context must understand the core stakes immediately.

### Key Working Assumptions:
- **Duration Constraint:** Strictly between 20.0s and 60.0s. Sweet spot is 30–50s.
- **Continuous vs. Multi-segment:** Prioritize single continuous high-tension scenes to preserve organic dramatic rhythm, with cleanly snapped boundaries to avoid mid-word or awkward visual cuts.
- **Model Agnosticism:** Cost-efficiency matters. Running heavy LLM prompts across entire 50-episode scripts is financially prohibitive. A smart hybrid design (rule filter + LLM scoring) is mandatory for production.

---

## 2. Technical Architecture & Approach

Our solution employs a **Two-Stage Hybrid Pipeline** designed for high throughput and near-zero cost:

```
[Raw Screenplays (.txt)] 
       │
       ▼
[Stage 1: State-Machine Parser] 
  ──> Converts non-standard script text into structured scenes, timestamps, camera cues & dialogue tags
       │
       ▼
[Stage 2: Sliding Window Generator & Heuristic Filter]
  ──> Tests 25s, 35s, 45s, 55s windows; scores emotional density, dialogue clashes & physical actions
  ──> Reduces search space from 2,000+ possibilities down to top candidate windows
       │
       ▼
[Stage 3: Multi-Dimensional Scorer (LLM / Semantic Evaluator)]
  ──> Evaluates 5 dimensions: Hook (35%), Cliffhanger (35%), Standalone (15%), Emotion (10%), Visual (5%)
       │
       ▼
[Stage 4: Temporal Deduplication & Diversity Ranker]
  ──> Suppresses >40% temporal overlap, balances episode representation, outputs Top 15 Ranked Promos
```

### Composite Scoring Equation:
$$\text{Score} = 0.35 \times \text{Hook} + 0.35 \times \text{Cliffhanger} + 0.15 \times \text{Standalone} + 0.10 \times \text{Emotional} + 0.05 \times \text{Visual}$$

---

## 3. Top Ranked Promos & Strategic Editorial Order

Across all 50 episodes of *"I Married a Broken Soldier. He was a Duke"*, the tool extracted 167 viable candidate windows and ranked the top promos. The top 3 ranked clips are:

1. **Rank #1 — Episode 1 (`00:40.00 - 01:15.00` | 35.0s | Score: 9.65/10)**
   - **Hook:** Lady In Gold Gown gloats: *"Because he is marrying me."* Juliana gasps: *"No..."*
   - **Cliffhanger:** Juliana demands: *"How long?"* Cuts on an unanswered question right before the conspiracy is revealed.
   - **Why Post First (Primary Acquisition):** Betrayal at the altar is the universal archetype in romance microdrama. Instant hook, zero backstory needed, universal emotional trigger across cold social feeds.
2. **Rank #2 — Episode 11 (`00:20.00 - 01:05.00` | 45.0s | Score: 9.65/10)**
   - **Hook:** Juliana recoils in utter disbelief; Gerald and Alexander clash over concealed evidence.
   - **Cliffhanger:** Cuts on Juliana crawling and desperately pleading: *"Please! There is nothing here!"* — smash cut.
   - **Strategy:** Retargeting ad for high-intent drama viewers who respond to intense interpersonal conflict and stakes.
3. **Rank #3 — Episode 45 (`00:30.00 - 01:25.00` | 55.0s | Score: 9.65/10)**
   - **Hook:** Alexander tenderly cradles Juliana, delivering explosive accusations: *"You poisoned my mother. You tortured my wife."*
   - **Cliffhanger:** Alexander delivers the ultimate identity reveal: *"Lady Juliana Ashcroft is my lawful wife... and the Duchess..."* — cut to black.
   - **Strategy:** Climax identity-reveal ad — highest conversion rate for romance/status drama fans.

*(The complete Top 15 ranked dataset with exact millisecond timestamps and rationale is available in `raw_outputs/final_ranked_promos.csv`)*.

---

## 4. Quality & Failure Analysis: Where Does the Tool Pick Badly?

Every production AI system has known blind spots. In our evaluation, the tool falters in three distinct patterns:

1. **Visual Humor & Silent Tension:**
   - *Failure:* Scenes where characters exchange long, pregnant pauses or silent glares have low word count and emotion tags. The parser underrates them even if the visual framing is gripping.
   - *Example:* Episode 12 standoff with silent royal guards.
2. **Lore-Heavy Arguments (The "Standalone" Failure):**
   - *Failure:* High shouting matches regarding complex family wills or royal lineage score 9+ on emotion keywords, but completely baffle a cold viewer scrolling on TikTok.
   - *Example:* Episode 34 inheritance dispute.
3. **Slow Escalation vs. Immediate Explosions:**
   - *Failure:* Psychological manipulation that builds slowly over 50 seconds gets cut off prematurely because the first 3 seconds lack high-energy keywords.

**Mitigation:** The Streamlit dashboard includes a **Human-in-the-Loop review interface** with live weight adjustment sliders, allowing editors to review, adjust, and approve AI picks in seconds.

---

## 5. Scaling Economics & Model Swappability

| Metric | Manual Editor | Our Automated Pipeline |
|---|---|---|
| **Turnaround per Show (50 eps)** | 4 – 6 Hours | **< 30 Seconds** |
| **Indexing Cost** | \$50 – \$100 labor | **\$0.015** (Gemini 1.5 Flash API) |
| **Model Swappability** | N/A | Modular (`scorer.py` supports Gemini, GPT-4o, Claude, or local Llama) |
| **Interview Readiness** | N/A | **Live Ingest Tab** in Streamlit accepts any new `.txt` script instantly |

