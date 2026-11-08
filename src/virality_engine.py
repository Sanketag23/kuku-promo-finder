"""
Virality Prediction and A/B Creative Testing Engine for Kuku Microdrama Promos.
Models performance marketing dynamics (ReelShort / DramaBox advertising playbook):
1. Viral Emotion Archetype Classification (Betrayal, Revenge, Identity Reveal, Status Shock)
2. A/B Text Overlay Hooks (Curiosity, Outrage, Romance)
3. Platform Optimization Recommendations (TikTok, Meta Reels, YouTube Shorts)
"""

from typing import Dict, Any, List

# Core Microdrama Viral Tropes
VIRAL_ARCHETYPES = {
    "altar_betrayal": {
        "name": "Altar Humiliation & Betrayal",
        "primary_trigger": "Moral Outrage / Empathy",
        "best_platform": "TikTok & Meta Reels (Broadest Demographics)",
        "expected_ctr": "High (4.8% - 6.2%)",
        "hook_variants": [
            "WHEN YOUR OWN SISTER MARRIES YOUR FIANCÉ AT THE ALTAR 💔",
            "She thought it was her wedding day... until she saw who was holding his hand 😱",
            "'I changed my mind.' The 4 words that ruined her life 😭"
        ]
    },
    "secret_identity": {
        "name": "Hidden Identity / Royal Reveal",
        "primary_trigger": "Catharsis & Status Inversion",
        "best_platform": "YouTube Shorts & Meta Ads (High Retention)",
        "expected_ctr": "Very High (5.2% - 7.0%)",
        "hook_variants": [
            "HE THOUGHT SHE WAS A BEGGAR... UNTIL THE DUKE ARRIVED 👑",
            "'She is my lawful wife and the Duchess.' The truth comes out 🔥",
            "They kicked her out of the church... then a billionaire Duke knelt before her 💍"
        ]
    },
    "power_revenge": {
        "name": "Retribution & Slap-back Revenge",
        "primary_trigger": "Schadenfreude / Justified Revenge",
        "best_platform": "TikTok (Fast Paced / Viral Audio)",
        "expected_ctr": "High (4.5% - 5.8%)",
        "hook_variants": [
            "YOU TOLERATED HER... NOW WATCH HER TAKE EVERYTHING 💀",
            "Never underestimate the daughter everyone ignored 💅",
            "The revenge she spent 5 years planning starts NOW 🔥"
        ]
    },
    "intrigue_accusation": {
        "name": "High-Stakes Accusation & Scandal",
        "primary_trigger": "Curiosity & High Stakes Drama",
        "best_platform": "Meta Reels & TikTok Mid-Funnel",
        "expected_ctr": "Above Average (3.8% - 4.9%)",
        "hook_variants": [
            "'YOU POISONED MY MOTHER.' The confrontation you can't miss 😱",
            "The secret they tried to bury is finally exposed 🩸",
            "Everyone in this room has blood on their hands ⚠️"
        ]
    }
}

def analyze_virality_and_ab_testing(promo: Dict[str, Any]) -> Dict[str, Any]:
    """Generates viral marketing metadata and A/B test creatives for any promo candidate."""
    excerpt = promo.get("script_excerpt", "") or promo.get("excerpt", "")
    excerpt_lower = excerpt.lower()
    hook_lower = promo.get("hook", "").lower()

    # Determine Archetype
    if any(k in excerpt_lower or k in hook_lower for k in ["altar", "wedding", "gown", "sister", "changed my mind"]):
        archetype_key = "altar_betrayal"
    elif any(k in excerpt_lower or k in hook_lower for k in ["duke", "wife", "duchess", "lawful", "kneel", "proposal", "ring"]):
        archetype_key = "secret_identity"
    elif any(k in excerpt_lower or k in hook_lower for k in ["poison", "killed", "court", "judge", "herbs", "trial", "testimony"]):
        archetype_key = "intrigue_accusation"
    else:
        archetype_key = "power_revenge"

    arch = VIRAL_ARCHETYPES[archetype_key]

    # Generate custom variant titles based on character context
    chars = promo.get("characters_involved", []) or promo.get("characters", [])
    custom_hooks = list(arch["hook_variants"])
    if chars:
        c1 = chars[0].title()
        custom_hooks[0] = custom_hooks[0] + f" | feat. {c1}"

    # Calculate Creative Virality Index (CVI) 0-100
    base_comp = promo.get("composite_score", 9.0)
    cvi = min(round(base_comp * 10 + 2.5, 1), 99.4)

    return {
        "archetype_name": arch["name"],
        "primary_trigger": arch["primary_trigger"],
        "recommended_platform": arch["best_platform"],
        "expected_ctr_range": arch["expected_ctr"],
        "creative_virality_index": cvi,
        "ab_test_hook_overlays": [
            {"variant": "A (Outrage / Shock)", "headline": custom_hooks[0], "target": "Top of Funnel (Cold Audience)"},
            {"variant": "B (Curiosity / Suspense)", "headline": custom_hooks[1], "target": "Retargeting / Drama Buffs"},
            {"variant": "C (Romantic Revenge)", "headline": custom_hooks[2], "target": "Female 18-35 Core Microdrama Demo"}
        ],
        "paywall_cut_moment": f"Hard cutoff at {promo.get('end_time', 'End')} prevents viewer closure, driving app install conversions."
    }

