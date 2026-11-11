# Software Requirements Specification

**Project:** Inbox-Integrated AI Agent (Agentic Automation)  
**Product name:** PinnacleOS (internal use)  
**Version:** 1.0  
**Status:** Phase 1 lock — MVP contract  
**Primary actor:** Alex Quinn, Founder, Pinnacle Marketing  
**Companion case:** `docs/01-case-scenario-agency-founder.md`  
**Phase plan:** `docs/00-phases.md`

---

## 1. Introduction

### 1.1 Purpose

This SRS defines the requirements for an AI agent that functions as an **Autonomous Chief of Staff** for a small marketing-agency founder. The system exists to remove operational friction by managing **email triage**, **calendar orchestration**, and **client communication**, so the founder is no longer the switchboard operator.

The north-star quantitative aim is to cut the founder’s administrative workload by **on the order of 90%** (from ~3.3 hours/weekday of email-calendar admin toward a ~20–30 minute review window). That figure is a product goal, not an acceptance test for v1. MVP acceptance is the behavior in §3 and §5, measured against the golden email corpus in the case document.

### 1.2 Scope

The agent integrates with the founder’s **Gmail or Outlook inbox** and **Google or Outlook Calendar**. It does not replace human decision-making for high-level strategy. It acts as:

- a **gatekeeper** (what is this email, and who should see it),
- an **information retriever** (what is already true in the CRM/KB/report),
- an **action executor** (draft/send, book/move/refuse meetings),
- a **safety net** (escalate, digest, undo, audit).

**In MVP scope**

- Automated email categorization and draft (or held) response generation
- Dynamic calendar scheduling and rescheduling without double-booking
- Meeting-type classification (15-minute stand-up vs 45-minute deep dive vs no meeting)
- Client-context injection from a knowledge base / CRM projection
- Redaction of internal financials and proprietary team notes in outbound drafts
- Escalation triggers for negative sentiment and human-only phrases
- End-of-day executive digest
- OAuth, audit log, 5-minute undo, tone profiles

**Out of MVP scope (see §6)**

- Live Meta/Google Ads API as the only source of spend (KB/report snapshot is sufficient for UC-01 in MVP)
- Automatic ClickUp/Asana/Trello card creation and freelancer assignment
- Proactive weekly client “risk reports” from project boards
- Replacing Slack as a full workplace; Slack is an **alarm channel**, not a second inbox to run
- Training a custom fine-tuned classifier as a must-have (a prompted LLM plus rules is acceptable if the golden set passes)

### 1.3 Definitions

| Term | Meaning |
| ---- | ------- |
| **Founder** | Primary user (Alex). Only human who authorizes auto-send policies and tone. |
| **Agent** | PinnacleOS decision-and-action loop. |
| **Drafts / Outbox (Pending Approval)** | Holding area for outbound mail the Founder must approve. |
| **Allow-list** | Per-client (or per-category) permission to send without approval when confidence ≥ threshold. MVP default: empty (everything held). |
| **Confidence score** | Model/system score 0–100 for “this draft is factually grounded and intent-correct.” |
| **Pending Human** | State: no auto-send, summary written for Founder, optional Slack. |
| **Client Brief** | Structured snapshot: client, campaign performance pointers, recent deliverables, open risks, last touch. |
| **Human-only trigger** | Phrase or intent that forces Pending Human regardless of confidence. |
| **Undo window** | 5 minutes after send or calendar mutate during which Founder can retract/recover. |

### 1.4 Assumptions and constraints

- Founder is non-technical and will abandon the product after one high-visibility wrong send.
- Clients must not be told they are talking to an AI except where scheduling logistics make a generic coordinator voice acceptable.
- Business hours for uptime: **8:00 AM–8:00 PM America/New_York**.
- Founder working hours for booking (initial): **8:00 AM–6:00 PM founder-local**, no new external meetings Friday after 4:00 PM, **15-minute buffer** between meetings. Adjustable in Phase 2 without changing FR IDs.
- Passwords are never stored. OAuth 2.0 only.
- The agent must not be the legal sender of healthcare/compliance advice for Solstice-class clients without Founder send.

---

## 2. Overall description

### 2.1 Product perspective

PinnacleOS is a cloud service that watches the Founder’s mailbox and calendar, writes drafts and events, and logs every action. It is not an IDE plugin and not a generic chat app. Chat (or “email the agent”) is a **control surface** (UC-03), not the product.

### 2.2 User characteristics

| User | Characteristics | Relationship to the agent |
| ---- | ---------------- | ------------------------- |
| **Founder (primary)** | Non-technical, extremely busy, demands high accuracy (target 99% on golden-set critical paths), needs **trust but verify**. | Approves drafts, sets tone, reviews digest, uses undo, receives Slack fires. |
| **Team (secondary)** | Designer, Copywriter, Ads Manager, PM, freelancers. | Receive notifications when work is extracted from email (Slack/email). They do not configure the agent in MVP. |
| **Client (external)** | Expects sub-15-minute replies, human warmth, factual numbers. | Must not need to change behavior. Interaction feels like Alex (or Alex’s desk). |

### 2.3 Operating environment

- **Compute:** Secure cloud (AWS or GCP).
- **Email:** Gmail API or Microsoft Graph mail.
- **Calendar:** Google Calendar API or Graph calendar.
- **CRM / memory:** HubSpot and/or Notion via API or webhook; MVP may use a structured fixture store that mimics those records.
- **Alarms:** Slack incoming webhook or bot for Urgent Escalation.
- **LLM:** Cloud LLM with no credential material in prompts (tokens stay in a secret store / isolated executor).

### 2.4 Design principles (non-negotiable)

1. **Draft, do not send** is the default. Auto-send is an explicit, per-client privilege.
2. **Negative sentiment never auto-replies.**
3. **A meeting is a last resort**, not a courtesy.
4. **Every mutate is logged and undoable for 5 minutes.**
5. **The model never receives raw OAuth tokens or passwords.**

---

## 3. Functional requirements (swim lanes)

Priorities: **M** Must (MVP), **S** Should (MVP if time), **C** Could (post-MVP).

### 3.1 Inbox automation and triage — “Gatekeeper”

#### FR-01 Email categorization — **M**

The agent shall analyze inbound email (current message + thread history) and assign exactly one primary bucket:

1. Scheduling / Rescheduling  
2. Urgent Delivery Issue (client angry, ads account paused, missed deadline)  
3. General Client Question (how do I / what did we spend / where is the file)  
4. Freelancer / Team Availability  
5. Spam / Newsletter (auto-archive)

**Acceptance**

- Golden corpus in the case §7 is labeled with ≥ 90% exact-bucket match.
- Multi-intent messages (reschedule **and** delivery complaint) set primary bucket to the **higher-risk** intent (Urgent Delivery or Scheduling with a linked delivery flag). Delivery flag must not be dropped.

#### FR-02 Auto-response (written) — **M**

For **General Client Question**, the agent shall generate a draft using the Knowledge Base (FAQs, reports, Client Brief).

**Constraints**

- Attach a **confidence score**.
- If confidence **< 85%**, place in Founder’s **Drafts / Outbox (Pending Approval)**. Never send.
- If confidence **≥ 85%** and client/category is **not** allow-listed, still hold for approval (MVP default).
- If confidence **≥ 85%** and allow-listed, send may occur; undo window still applies.

**Acceptance**

- UC-01 produces a draft containing the KB figure, not an invented figure.
- Empty KB → confidence below 85% and a held draft that states the gap internally to the Founder, not a guessed number to the client.

#### FR-03 Sentiment analysis — **M**

The agent shall score client-facing inbound tone. If sentiment is **negative**, it **must not auto-respond**. It shall mark **Urgent Escalation** and ping the Founder on Slack.

**Acceptance**

- UC-02 (unhappy with creative quality) never sends mail.
- Slack payload includes client, quoted trigger, thread link, and a ≤ 8-line summary.

### 3.2 Calendar orchestration — “Traffic Controller”

#### FR-04 Proactive booking — **M**

When intent is a real meeting (not FR-06 text-refuse), the agent shall offer **three specific times** with **context in the copy** (e.g. Q3 planning, 45 minutes), not only a generic scheduling link.

**Acceptance**

- Times respect working hours, buffers, and existing events.
- Invite/description includes meeting type and original ask.

#### FR-05 Automated rescheduling — **M**

On “move this call to [day]”:

1. Confirm cancellation of the original event (in-thread + calendar).  
2. Check Founder availability on the requested day.  
3. Propose the next valid slot of the correct duration (default 30 minutes if type unknown; else FR-06 duration).  
4. **Must not double-book** (including races).

**Acceptance**

- Case scenario: tomorrow 11:00 moved to Thursday; Thursday morning occupied → a later free slot (e.g. 2:00 PM) is proposed; conflicting events untouched.
- Concurrent reschedule requests cannot create two events in the same slot.

#### FR-06 Meeting type classifier — **M**

Before booking, the agent shall classify purpose from the thread:

| Classification | Action |
| -------------- | ------ |
| Status Update | Book **15-minute** “Stand-up” |
| Strategy Review | Book **45-minute** “Deep Dive” |
| Question answerable in text | **Do not book.** Written reply instead (FR-02 path). |
| Human-only / strategy logic (FR-09) | Do not book autonomously; Pending Human |

**Acceptance**

- “How do I download the report?” → zero new events.
- “Q3 planning” → 45-minute Deep Dive options.
- “5-minute status” → 15-minute Stand-up, not 30-minute default.

### 3.3 Information retrieval — “Memory”

#### FR-07 Context injection — **M** (fixture OK)

When drafting a client email, the agent shall pull **current campaign performance** and **recent deliverables** from CRM / PM / KB so answers are factual.

**Acceptance**

- Drafts that cite spend, dates, or asset names must be traceable to a KB/CRM record ID in the audit log.
- MVP may use Notion/HubSpot **or** a seeded store with the same fields.

#### FR-08 Data privacy / redaction — **M**

Outbound client drafts shall **not** include internal agency financials (margins, freelancer rates, payroll) or proprietary team notes (e.g. “raising rates in Q3,” “we want to fire this client”).

**Acceptance**

- A planted internal note in the retrieval set never appears in the client-facing body.
- Redaction events are logged.

### 3.4 Escalation and handover — “Safety net”

#### FR-09 Human-only triggers — **M**

If the agent detects phrases or intents including (not limited to):

- “Let’s jump on a call about this”
- “Can you explain the logic behind this strategy?”

it shall set **Pending Human** and write a Founder summary. It shall not produce a strategy defense to the client.

**Acceptance**

- Those phrases in the golden set always Pending Human even if sentiment is neutral and confidence is high.

#### FR-10 End-of-day digest — **M**

At **5:00 PM founder-local** (configurable), send the Founder a Daily Executive Summary:

1. Count of emails handled autonomously  
2. Emails awaiting Founder approval (list of links)  
3. Tomorrow’s **top 3** must-do items derived from calendar bookings  

**Acceptance**

- Digest arrives even if counts are zero.
- Approval items link to the actual draft/thread.

### 3.5 Additional MVP functional requirements (from case, not numbered in the original brief)

#### FR-11 Team notify — **S**

When a client request implies delivery work (new asset, copy change, spend pause), the agent shall notify the relevant role via Slack or email (e.g. “Design: new asset requested by Harbor & Pine”).

Not required to write ClickUp cards (that is §6).

#### FR-12 Founder query — **M**

The Founder may ask the agent (email or in-app): “What’s my schedule like today?” The agent replies with a bulleted calendar summary and a link to the full calendar (UC-03).

#### FR-13 Client Brief object — **S**

The agent shall be able to produce a Client Brief from unstructured thread data for Founder review (used internally on escalation and optionally attached to Deep Dive invites).

#### FR-14 Kill switch — **M**

The Founder shall be able to pause all sending and calendar writes without disconnecting OAuth. Inbound classification may continue in read-only mode.

---

## 4. Non-functional requirements (guardrails)

### 4.1 Performance

| ID | Requirement | Priority |
| -- | ----------- | -------- |
| **NFR-01** | Time from inbound-mail availability to **triage result persisted** < **3 seconds** at p95 under demo load (classification + routing, excluding LLM draft generation). Draft generation p95 < **15 seconds**. | M |
| **NFR-02** | **99.9%** uptime during 8 AM–8 PM ET for the ingestion and alerting path. | S (monitor in production; demo may be best-effort) |

### 4.2 Security

| ID | Requirement | Priority |
| -- | ----------- | -------- |
| **NFR-03** | OAuth 2.0 for all mailbox/calendar connections. **Never store user passwords.** Refresh tokens encrypted at rest. | M |
| **NFR-04** | Every agent action (draft created, email sent, event created/updated/deleted, Slack ping, archive) is written to an **Audit Log** the Founder can access. | M |
| **NFR-07** | Prompt injection via email body must not cause exfiltration of other clients’ data or secrets. Tool access is scoped; retrieval is per-client. | M |
| **NFR-08** | Credentials and API keys are **not** placed in the model context. | M |

### 4.3 Usability

| ID | Requirement | Priority |
| -- | ----------- | -------- |
| **NFR-05** | Founder can **Recover** a meeting or **Retract** an email within **5 minutes** of the action via a simple control (button or reply-command). After 5 minutes, retraction becomes a manual/Founder-only path. | M |
| **NFR-06** | Founder selects a **Tone Profile** (at least: Professional, Casual, Charming) applied to drafts. Per-client override is Should. | M |

### 4.4 Accuracy and trust

| ID | Requirement | Priority |
| -- | ----------- | -------- |
| **NFR-09** | On the golden corpus, **zero** auto-sends for negative-sentiment or FR-09 items. | M |
| **NFR-10** | Factual numbers in sent mail must match KB/CRM or the send is blocked. | M |

---

## 5. Specific feature details (MVP)

### 5.1 The Conscious Inbox (autonomous triage)

**Input:** Raw inbound text + previous thread history + client record id if known.  
**Process:** Intent classification → sentiment → retrieval → draft → confidence → policy (hold / send / escalate).  
**Output:**

- FAQ + grounded answer → Outbox (Pending Approval), or send if allow-listed  
- Negative / human-only → Pending Human + Slack  
- Newsletter → archive  
- Scheduling → calendar lane (§5.2)

The original note that a “fine-tuned classification model” *will* identify intent is **implementation guidance**, not a mandate. Any classifier that meets FR-01 acceptance is valid.

### 5.2 Smart Rescheduling protocol

**Scenario:** Client: “I need to move tomorrow’s 11 AM to Thursday.”

**Agent action**

1. Identify the event (attendee, time, title).  
2. Remove or cancel tomorrow 11:00.  
3. Scan Thursday for a valid slot (duration, buffers, hours).  
4. Find e.g. 2:00 PM free.  
5. Send calendar modification plus a human note: “Rescheduled per your request. Let me know if 2 PM doesn’t work.”  
6. Start 5-minute undo; write audit rows for delete + create/update.

If no slot exists that day, do **not** invent one. Reply with the next two valid options across the following two business days and mark for Founder if the client demanded that exact day.

---

## 6. Future scope (post-MVP)

These items are **explicitly not** in Phases 3–8 unless the Founder/stakeholder reopens the SRS.

- **Proactive insights:** Monitor project boards; send weekly Risk Reports to clients before they ask about delays.  
- **Task delegation:** Create Asana/Trello/ClickUp cards from email and assign freelancers.  
- **Live ad-platform pull:** Meta API as system of record for UC-01 instead of the weekly report snapshot.  
- **Multi-mailbox team mode:** Agent on `team@` rather than only the Founder’s personal inbox.

---

## 7. Use cases

| ID | Actor | Description | Agent action | Maps to |
| -- | ----- | ----------- | ------------ | ------- |
| **UC-01** | Client | “How much did we spend on Facebook ads last month?” | Pull figure from KB/report (MVP) or Meta API (future). Short reply with exact figure. Hold or send per policy. **No meeting.** | FR-01, FR-02, FR-06, FR-07 |
| **UC-02** | Client | “I am unhappy with the creative quality.” | **Block send.** Flag Emergency / Urgent Escalation. Slack Founder. Summary. | FR-03, FR-09 |
| **UC-03** | Founder | “What’s my schedule like today?” | Parse Calendar API; bulleted summary + link. | FR-12 |
| **UC-04** | Client | “Move tomorrow 11 AM to Thursday.” | Smart reschedule protocol; no double-book. | FR-05 |
| **UC-05** | Client | “How do I download last week’s report?” | Written FAQ; **zero** events. | FR-02, FR-06 |
| **UC-06** | Client | “Can we do Q3 planning?” | Three 45-minute Deep Dive options with context. | FR-04, FR-06 |
| **UC-07** | Client | “Can you explain the logic behind this strategy?” | Pending Human; Founder summary; no autonomous strategy essay. | FR-09 |
| **UC-08** | System | 5:00 PM | Daily Executive Summary. | FR-10 |
| **UC-09** | Founder | Wrong send or wrong booking | Retract/recover within 5 minutes. | NFR-05 |

---

## 8. Traceability (case → requirements)

| Case beat | Requirement IDs |
| --------- | ---------------- |
| 7:00–7:45 AM loop (report lookup, freelancer, reschedule) | FR-01, FR-02, FR-05, FR-07, FR-11 |
| 18-hour / 3.3-hour drain | FR-01–FR-06, FR-10, FR-14 |
| Context-switching tax | FR-06 (refuse meetings), FR-10 (batch review) |
| Happiness paradox (fast comms, slow delivery) | FR-03, FR-09, FR-11, FR-13 |
| Reactive calendar / all emails equal urgency | FR-04, FR-05, FR-06 |
| Breaking point: need Chief of Staff in the inbox, not a link | Product purpose §1.1; not Calendly-only (FR-04) |
| Trust but verify, 99% accuracy desire | FR-02 threshold, NFR-05, NFR-09, NFR-10, FR-14 |
| Team notified of new assets | FR-11 |
| Clients must feel human | NFR-06 |
| Wrong send is fatal | NFR-03, NFR-04, NFR-05, NFR-07, allow-list default off |

---

## 9. MVP build order (implements the phase plan)

1. OAuth, sync, audit, kill switch (Phase 3)  
2. FR-01, FR-02, FR-03, policy engine (Phase 4)  
3. FR-04, FR-05, FR-06 (Phase 5)  
4. FR-07, FR-08, FR-13 (Phase 6)  
5. FR-09, FR-10, FR-11, FR-12, NFR-05, NFR-06, audit UI (Phase 7)  
6. Seeded Pinnacle demo (Phase 8)

---

## 10. Open points (resolved in Phase 2)

Decisions live in `docs/03-architecture.md` §1. They do not change v1.0 requirement IDs.

- **Provider:** Gmail + Google Calendar first.  
- **Slack:** webhook alarm with in-app Bell fallback.  
- **Undo:** 5-minute **send delay** for mail; calendar mutates immediately and restores from snapshot.  
- **Confidence:** `min(citation_score, critic_score)`, not token logprobs.

---

## 11. Document control

| Version | Date | Notes |
| ------- | ---- | ----- |
| 1.0 | 2026-09-02 | Phase 1 lock from founder brief + expanded Pinnacle Marketing case. |
| 1.0.1 | 2026-09-02 | Pointer only: SRS §10 resolved by architecture. No FR/NFR ID changes. |

Changes after lock require a version bump and a note in `docs/00-phases.md`.
