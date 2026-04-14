"""
SkillForge Brain Analyzer
Reads brain_data.json → outputs insights.json
Run automatically by server.js on startup and every hour
"""

import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import math

DATA_FILE  = os.path.join(os.path.dirname(__file__), "data", "brain_data.json")
OUT_FILE   = os.path.join(os.path.dirname(__file__), "data", "insights.json")

# ── helpers ──────────────────────────────────────────────────────────────────

def load():
    if not os.path.exists(DATA_FILE):
        return None
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)

def save(obj):
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def pct(n, total):
    return round((n / total) * 100, 1) if total else 0

def mean(lst):
    return sum(lst) / len(lst) if lst else 0

def std(lst):
    if len(lst) < 2: return 0
    m = mean(lst)
    return math.sqrt(mean([(x - m) ** 2 for x in lst]))

# ── sleep mapper ─────────────────────────────────────────────────────────────

SLEEP_MAP = {"3-5": 4, "6": 6, "7-8": 7.5, "8+": 9}

def sleep_val(s):
    return SLEEP_MAP.get(str(s), 7)

# ── core analysis ─────────────────────────────────────────────────────────────

def analyze():
    raw = load()
    if not raw or not isinstance(raw, dict):
        save({"error": "no_data", "generated": datetime.now().isoformat()})
        return

    habits  = raw.get("habits", [])
    sides   = raw.get("sides",  [])
    all_tasks = habits + sides
    total_tasks = len(all_tasks)
    days_raw = raw.get("allDays", {})

    if not days_raw or total_tasks == 0:
        save({"error": "insufficient_data", "generated": datetime.now().isoformat()})
        return

    # ── build day records ────────────────────────────────────────────────────
    records = []
    for date_str, entry in sorted(days_raw.items()):
        done      = entry.get("done", [])
        sessions  = entry.get("sessions", [])
        study_sec = sum(s.get("dur", 0) for s in sessions)
        score_pct = pct(len(done), total_tasks)
        sl        = sleep_val(entry.get("sleep", "7-8"))
        screen    = float(entry.get("screen", 0) or 0)
        mood      = int(entry.get("mood", 3) or 3)

        # which tasks completed
        completed_tasks = set()
        for d in done:
            t = d[0]
            try:
                idx = int(d[1:])
                arr = habits if t == "h" else sides
                if idx < len(arr):
                    completed_tasks.add(arr[idx])
            except Exception:
                pass

        records.append({
            "date":        date_str,
            "done_count":  len(done),
            "score_pct":   score_pct,
            "study_sec":   study_sec,
            "sleep":       sl,
            "screen":      screen,
            "mood":        mood,
            "tasks":       completed_tasks,
            "n_sessions":  len(sessions),
        })

    n = len(records)
    if n == 0:
        save({"error": "no_records", "generated": datetime.now().isoformat()})
        return

    scores     = [r["score_pct"]  for r in records]
    sleeps     = [r["sleep"]       for r in records]
    screens    = [r["screen"]      for r in records]
    moods      = [r["mood"]        for r in records]
    study_hrs  = [r["study_sec"] / 3600 for r in records]

    # ── 1. BURNOUT RISK ──────────────────────────────────────────────────────
    # last 3 days: low score + bad sleep + high screen → burnout warning
    recent = records[-3:] if n >= 3 else records
    burn_score = 0
    if mean([r["score_pct"] for r in recent]) < 45:   burn_score += 35
    if mean([r["sleep"]     for r in recent]) < 6:     burn_score += 30
    if mean([r["screen"]    for r in recent]) > 5:     burn_score += 20
    if mean([r["mood"]      for r in recent]) <= 2:    burn_score += 15
    burn_score = min(burn_score, 100)

    if   burn_score >= 70: burnout_level = "high"
    elif burn_score >= 40: burnout_level = "medium"
    else:                  burnout_level = "low"

    burnout_msg = {
        "high":   "⚠ burnout signal detected — rest, reduce screen time, fix sleep",
        "medium": "take care — patterns suggest rising fatigue",
        "low":    "you're maintaining well — keep the momentum"
    }[burnout_level]

    # ── 2. MOMENTUM SCORE (0-100) ────────────────────────────────────────────
    # weighted: score trend (40%) + streak (30%) + sleep quality (20%) + mood (10%)
    last7  = records[-7:] if n >= 7 else records
    last14 = records[-14:] if n >= 14 else records

    # score trend: is the last 7d average better than the 14d average?
    avg7   = mean([r["score_pct"] for r in last7])
    avg14  = mean([r["score_pct"] for r in last14])
    trend  = min(max((avg7 / 100) * 40, 0), 40)

    # streak of consecutive days with score > 50%
    streak = 0
    for r in reversed(records):
        if r["score_pct"] > 50: streak += 1
        else: break
    streak_pts = min((streak / 7) * 30, 30)

    sleep_pts = min(((mean(sleeps) - 4) / 5) * 20, 20)
    mood_pts  = ((mean(moods) - 1) / 3) * 10

    momentum = round(trend + streak_pts + sleep_pts + mood_pts, 1)
    momentum = min(max(momentum, 0), 100)

    if   momentum >= 75: momentum_label = "🔥 on fire"
    elif momentum >= 50: momentum_label = "📈 building"
    elif momentum >= 30: momentum_label = "💤 sluggish"
    else:                momentum_label = "🧊 cold start"

    # ── 3. HABIT CORRELATION (best habits for high-score days) ───────────────
    high_days = [r for r in records if r["score_pct"] >= 70]
    low_days  = [r for r in records if r["score_pct"] <  40]

    task_lift = {}
    for task in all_tasks:
        h_rate = mean([1 if task in r["tasks"] else 0 for r in high_days]) if high_days else 0
        l_rate = mean([1 if task in r["tasks"] else 0 for r in low_days])  if low_days  else 0
        lift   = h_rate - l_rate
        if h_rate > 0.1:
            task_lift[task] = round(lift * 100, 1)

    top_habits = sorted(task_lift.items(), key=lambda x: x[1], reverse=True)[:5]
    top_habits = [{"name": t, "lift": l} for t, l in top_habits]

    # ── 4. SKILL TRAJECTORY (days until unlock at current pace) ─────────────
    SKILL_DEFS = [
        {"name": "Cyber Discipline",  "req": ["HackTheBox", "Focus 25min", "Research"]},
        {"name": "Cognitive Monk",    "req": ["Reading",    "Focus 25min", "Book Reading"]},
        {"name": "Physical Master",   "req": ["Exercise",   "Wake up early", "Sleep before 12"]},
        {"name": "Spiritual Anchor",  "req": ["Prayer",     "Quran", "Dhikr"]},
        {"name": "Systems Engineer",  "req": ["PFA Progress","Systems Thinking","Research"]},
        {"name": "Digital Minimalist","req": ["No phone before sleep","No phone after wakeup","No bad habits"]},
    ]

    skill_progress = []
    for sk in SKILL_DEFS:
        rates = []
        for req in sk["req"]:
            rate = mean([1 if req in r["tasks"] else 0 for r in records])
            rates.append(rate)
        avg_rate = mean(rates)
        days_to_60 = None
        if avg_rate > 0 and avg_rate < 0.6:
            days_to_60 = round((0.6 - avg_rate) / (avg_rate / max(n, 1)), 1)
        skill_progress.append({
            "name":       sk["name"],
            "rate":       round(avg_rate * 100, 1),
            "ready":      avg_rate >= 0.6,
            "days_to_60": days_to_60,
        })
    skill_progress.sort(key=lambda x: -x["rate"])

    # ── 5. ANOMALY DETECTION ─────────────────────────────────────────────────
    anomalies = []
    if n >= 5:
        score_mean = mean(scores)
        score_std  = std(scores)
        for r in records[-7:]:
            z = (r["score_pct"] - score_mean) / score_std if score_std else 0
            if z < -1.5:
                anomalies.append({
                    "date": r["date"],
                    "type": "low_score",
                    "msg":  f"score dropped to {r['score_pct']}% (well below your average {round(score_mean)}%)"
                })
            if r["sleep"] < 5 and r["screen"] > 5:
                anomalies.append({
                    "date": r["date"],
                    "type": "bad_combo",
                    "msg":  f"bad sleep ({r['sleep']}h) + high screen ({r['screen']}h) on same day"
                })

    # ── 6. BEST DAY PATTERN ──────────────────────────────────────────────────
    if high_days:
        best_sleep  = round(mean([r["sleep"]  for r in high_days]), 1)
        best_screen = round(mean([r["screen"] for r in high_days]), 1)
        best_study  = round(mean([r["study_sec"] / 3600 for r in high_days]), 1)
        best_pattern = {
            "sleep_h":   best_sleep,
            "screen_h":  best_screen,
            "study_h":   best_study,
            "msg": f"on your best days: {best_sleep}h sleep · {best_screen}h screen · {best_study}h study"
        }
    else:
        best_pattern = None

    # ── 7. WEEKLY SUMMARY ────────────────────────────────────────────────────
    week_days = records[-7:] if n >= 7 else records
    weekly = {
        "avg_score":  round(mean([r["score_pct"]  for r in week_days]), 1),
        "avg_sleep":  round(mean([r["sleep"]       for r in week_days]), 1),
        "avg_screen": round(mean([r["screen"]      for r in week_days]), 1),
        "avg_study":  round(mean([r["study_sec"] / 3600 for r in week_days]), 1),
        "avg_mood":   round(mean([r["mood"]        for r in week_days]), 1),
        "total_study_h": round(sum([r["study_sec"] / 3600 for r in week_days]), 1),
    }

    # ── 8. SIMPLE NEXT-DAY PREDICTION ────────────────────────────────────────
    # based on sleep quality + momentum: predict tomorrow's likely score range
    last_sleep = records[-1]["sleep"] if records else 7
    predicted_score = min(100, round(avg7 * (last_sleep / 7.5) * (momentum / 60 + 0.5)))
    if predicted_score >= 70:   pred_label = "strong day ahead 💪"
    elif predicted_score >= 45: pred_label = "moderate day — push harder"
    else:                       pred_label = "rough day possible — sleep early tonight"

    # ── assemble output ───────────────────────────────────────────────────────
    out = {
        "generated":       datetime.now().isoformat(),
        "days_analyzed":   n,
        "burnout": {
            "score":   burn_score,
            "level":   burnout_level,
            "message": burnout_msg,
        },
        "momentum": {
            "score":  momentum,
            "label":  momentum_label,
            "streak": streak,
        },
        "top_habits": top_habits,
        "skill_progress": skill_progress,
        "anomalies": anomalies[-5:],
        "best_pattern": best_pattern,
        "weekly": weekly,
        "prediction": {
            "score": predicted_score,
            "label": pred_label,
        },
        "totals": {
            "avg_score":      round(mean(scores), 1),
            "avg_sleep":      round(mean(sleeps), 1),
            "avg_screen":     round(mean(screens), 1),
            "total_study_h":  round(sum(study_hrs), 1),
            "total_sessions": sum(r["n_sessions"] for r in records),
        }
    }

    save(out)
    print(f"[analyze] ✓ insights written — {n} days analyzed")

if __name__ == "__main__":
    analyze()
