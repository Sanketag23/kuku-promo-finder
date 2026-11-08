# 🎬 3-Minute Walkthrough Video Script & Demo Guide
**Candidate:** Sanket Agarwal (Roll: 230920)  
**Assignment:** Kuku TV — Problem 1: Find the Promos (Ads)  
**Recommended Tool:** Loom, QuickTime Screen Recording, or OBS  

---

## ⏱️ Video Timeline (Target Duration: 2:30 - 3:00 minutes)

### Part 1: Problem Understanding & Architecture (0:00 - 0:45)
* **What to Show on Screen:** Keep [`README.md`](file:///Users/sanketagarwal/Desktop/Kuku_Technologies_Assignment/README.md) open or show the Architecture diagram.
* **What to Say (in your own voice):**
  > *"Hi everyone, I'm Sanket Agarwal. For this assignment, I tackled Problem 1: Building an automated AI Promo and Ad Finder for Kuku's microdrama shows.
  > Today, editors spend 4 to 6 hours scrubbing episodes manually for 20-to-60 second clips. My goal was to build a production-grade system that finds these clips in under 30 seconds at near-zero cost.
  > Rather than naively dumping raw screenplays into an expensive LLM, I built a **Two-Stage Hybrid Engine**:
  > Stage 1 parses the non-standard screenplay format into structured JSON and uses a heuristic sliding window filter to detect emotional peaks, physical actions, and character conflict. This reduces the search space by 95% and cuts token costs down to just **1.5 cents per show**.
  > Stage 2 evaluates candidates across 5 core dimensions: Hook strength, Cliffhanger cutoff, Standalone clarity, Emotional charge, and Visual appeal."*

---

### Part 2: Interactive Streamlit Studio & Phone Simulator (0:45 - 1:45)
* **What to Show on Screen:** Switch to the browser at `http://localhost:8501` (Tab 1 & Tab 2).
* **What to Say:**
  > *"Here is the interactive Streamlit Studio built for the editorial and marketing teams.
  > On Tab 1, we see the Top 15 Ranked Promos across all 50 episodes.
  > Our #1 Hero Promo is a **Cross-Episode Montage**: it takes Juliana's altar betrayal from Episode 1 (23s) and smash cuts to Episode 3 where the Scarred Duke intervenes and drops to one knee with a proposal (22s). This 45-second clip matches the quintessential ReelShort and DramaBox viral playbook.
  > On the right, notice our **9:16 Vertical Mobile Phone Simulator**. It gives editors an immediate preview of how the ad looks on TikTok or Instagram Reels, including the scroll-stopping text banner and the exact paywall smash cut point.
  > Over on Tab 2, our **A/B Testing Studio** generates 3 distinct psychological hook variants—Outrage, Curiosity, and Romance—along with a Creative Virality Index score so marketing teams can optimize ad spend."*

---

### Part 3: Live Ingest Mode (Interview Readiness) (1:45 - 2:20)
* **What to Show on Screen:** Click on **Tab 3: "Live Screenplay Ingest (Interview Mode)"**.
* **What to Say & Do:**
  > *"One critical requirement was making something that can run again on new inputs during the interview.
  > In Tab 3, an interviewer or editor can upload or paste any new unseen screenplay `.txt` file.
  > Let's click 'Find Promos for this Episode'..."*
  *(Click the button and show the success banner appear with ranked promo cuts and exact timestamps in under 10 seconds)*
  > *"In just a few seconds, it parses the new script, computes timestamps, scores the hooks, and provides ready-to-cut promo recommendations."*

---

### Part 4: Quality Limits & Scaling Wrap-up (2:20 - 2:45)
* **What to Show on Screen:** Switch briefly to **Tab 4: "Quality & Failure Analysis"** or show the PDF document.
* **What to Say:**
  > *"Finally, to answer the prompt honestly on where the tool struggles:
  > Because this analyzes screenplay text, it can under-rank silent visual tension or visual comedy where words are sparse. It also requires human-in-the-loop oversight on lore-heavy arguments where characters shout about complex wills that a cold viewer might not understand.
  > In production, this text pipeline would be paired with audio decibel peaks and computer vision frame analysis.
  > The full 2-page solution document and raw datasets in CSV and JSON are submitted. Thank you for your time!"*
