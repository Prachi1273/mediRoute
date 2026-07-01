# Triage Skill
<!-- Day 3 concept: Agent Skills — loaded on demand, keeps base prompt lightweight -->

## Purpose
Classify symptom urgency using a structured clinical triage framework.

## When this skill is loaded
This skill is loaded by the orchestrator ONLY when the triage_agent is
invoked. It is NOT part of the base system prompt — this is the
progressive disclosure pattern from the Day 3 whitepaper.

## Triage protocol

### Step 1: Red flag screening
Check for any of the following before any other analysis:
- Chest pain or pressure
- Difficulty breathing or shortness of breath
- Sudden severe headache ("worst headache of my life")
- Facial drooping, arm weakness, speech difficulty (FAST stroke signs)
- Loss of consciousness or unresponsiveness
- Severe allergic reaction (anaphylaxis)
- Heavy uncontrolled bleeding
- Suspected poisoning or overdose

If ANY red flag is present → EMERGENCY. Skip remaining steps.

### Step 2: Urgency scoring
Score the following dimensions 1-3 (1=mild, 3=severe):
- Pain intensity
- Symptom duration (longer = higher score for some conditions)
- Functional impairment (can the person walk, speak, breathe normally?)
- Fever height (>39°C scores 3)
- Pre-existing conditions that increase risk

Total score 7–9 → URGENT
Total score 4–6 → may be URGENT or ROUTINE depending on trend
Total score 1–3 → ROUTINE

### Step 3: Special populations
- Age > 65 or < 2: upgrade urgency by one level
- Known cardiac, respiratory, or immunocompromised conditions: upgrade by one level
- Pregnant: flag separately, route to obstetric care

### Step 4: Confidence calibration
If confidence < 0.7, add a note recommending the user call a nurse helpline
(e.g. NHS 111 or India's 104 helpline) before deciding on care pathway.

## Output format
Always return the exact JSON schema defined in triage_agent.py.
Never include free text outside the JSON.
