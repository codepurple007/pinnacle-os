# PinnacleOS — Work Phases

**Product:** Inbox-integrated AI Chief of Staff for a boutique agency founder  
**Internal name:** PinnacleOS  
**Current phase:** Phase 3 (Foundation) — complete. Next: Phase 4 after explicit continue.  
**Rule:** Do not start the next phase until the current phase’s exit criteria are met.

This file is the contract for how the project is built. Each phase has a goal, deliverables, and a hard stop. Later phases may refine earlier documents; they must not silently rewrite the case or the SRS without an explicit change log.

---

## Phase map

| Phase | Name | Status | What “done” means |
| ----- | ---- | ------ | ----------------- |
| 1 | Case scenario + SRS | **Complete** | Alex’s world is specified in enough detail to design against. SRS v1.0 is locked as the MVP contract. |
| 2 | Architecture & experience design | **Complete** | System design, data model, agent swim lanes, and demo UX can be implemented without inventing new product rules. |
| 3 | Foundation (auth, connectors, audit) | **Complete** | Gmail/Calendar can be connected via OAuth. Every agent action can be logged. No autonomous sending yet. |
| 4 | Inbox Gatekeeper (MVP core) | Not started | Inbound mail is categorized, drafted, scored, and held or escalated per FR-01–FR-03. |
| 5 | Calendar Traffic Controller | Not started | Booking, rescheduling, meeting-type classification, and “don’t book, reply in writing” all work per FR-04–FR-06. |
| 6 | Memory & retrieval | Not started | Replies are grounded in CRM/KB facts. Internal financials and private notes are redacted (FR-07, FR-08). |
| 7 | Safety net & founder controls | Not started | Human-only triggers, 5:00 PM digest, 5-minute undo, tone profiles, audit UI (FR-09, FR-10, NFR-04–NFR-06). |
| 8 | Portfolio demo & Upwork packaging | Not started | A seeded “Pinnacle Marketing” inbox can be walked end-to-end as a client demo. |

Post-MVP (Asana/Trello auto-delegation, weekly client risk reports, Meta spend pull) is **out of Phase 1–8**. It lives in SRS §6 and is not built until the MVP is demonstrated.

---

## Phase 1 — Case Scenario Expansion & SRS

**Goal.** Make Alex and Pinnacle Marketing real enough that every later feature can be traced to a specific pain, email, or calendar failure — and lock the MVP requirements so engineering does not invent scope.

**Why this phase exists.** Without a concrete agency, “AI personal assistant” becomes a chatbot. The founder’s bottleneck is not writing. It is being the switchboard: every email, every reschedule, every “quick question” that should have been a dashboard lookup.

**Work in this phase**

1. Expand the Agency Founder case into a full operating picture: company, team, clients, tools, a reconstructed workday, quantified cost, and the breaking point.
2. Turn the provided SRS into a build-ready specification with priorities, acceptance criteria, out-of-scope, and traceability from story beats to FR/NFR IDs.
3. Define MVP vs. post-MVP so Phase 4–7 cannot quietly absorb Phase 6 “future scope.”

**Deliverables**

- `docs/01-case-scenario-agency-founder.md` — narrative + evidence + email corpus
- `docs/02-srs-pinnacle-os.md` — SRS v1.0
- This phase plan

**Exit criteria (Phase 1 is done when)**

- A stranger can explain who Alex is, why the agency is stuck at a ceiling, and what “success” looks like in one minute.
- Every functional requirement in the SRS maps to at least one moment in the case.
- MVP in-scope vs. out-of-scope is explicit.
- No code is required to finish this phase.

**Hard stop.** Do not design APIs, pick a model, or scaffold the app in this phase.

**Status:** Complete. Deliverables on disk.

---

## Phase 2 — Architecture & Experience Design

**Goal.** Decide *how* PinnacleOS will run so Phase 3–7 implement a system, not a pile of scripts.

**Work**

- Component diagram: ingestion → classify → retrieve → decide → act → log
- Sequence diagrams for UC-01, UC-02, UC-03, and Smart Rescheduling
- Data model: emails, threads, classifications, drafts, calendar events, audit events, tone profiles, client records
- Trust UX: Drafts folder, confidence score, Slack ping, undo window, daily digest
- Tech-stack recommendation (cloud, email/calendar APIs, LLM, CRM, Slack) with a note on what the Upwork demo can fake vs. must be real
- Threat model for OAuth tokens, prompt injection via email, and accidental send

**Deliverables**

- `docs/03-architecture.md` — locked architecture, UX, stack, demo vs live, FR owners, Phase 3 contract

**Exit criteria**

- An engineer can implement Phase 3 without asking “where does this live?”
- Every FR has a stated owner component.
- Demo data strategy is written (seeded clients, fake Meta numbers, sandbox calendar).

**Hard stop.** No production integrations until Phase 3.

**Status:** Complete. Open points from SRS §10 are decided in architecture §1. No code, no OAuth.

---

## Phase 3 — Foundation

**Goal.** Connect the world Alex already lives in, with a kill switch, before any autonomous behavior.

**Work**

- OAuth 2.0 for Gmail (or Graph) and Google/Outlook Calendar
- Read-only inbox + calendar sync in a sandbox
- Audit log store and “who did what” record format
- Founder dashboard shell: connected accounts, last sync, kill switch (pause agent)
- Secret handling: tokens never stored as passwords; model never receives raw credentials

**Exit criteria**

- Founder can connect and disconnect accounts.
- A test email appears in the internal store with thread history.
- An audit row can be written for a fake action.
- Agent cannot send mail or mutate calendar yet.

**Deliverables**

- `apps/api` — FastAPI: OAuth, ingest, audit, kill switch
- `packages/google` — read-only Gmail/Calendar connector (send/write raise)
- `apps/web` — Founder Console desk / inbox / audit
- `docs/04-phase-3-run.md`

**Status:** Complete. Console at http://localhost:3001 (host port 3000 was already in use). API at http://localhost:8000. No send, no calendar writes.

---

## Phase 4 — Inbox Gatekeeper (MVP core)

**Goal.** Stop treating every email as equally urgent. This is the 18-hour drain.

**Work**

- FR-01 categorization into the five buckets
- FR-02 draft generation for General Client Question, with confidence score and 85% hold rule
- FR-03 sentiment gate: negative tone → no auto-send, Slack escalation
- Outbox (Pending Approval) vs. auto-send allow-list (per client, default off for MVP)
- Knowledge-base lookup stub (FAQ + weekly report attachments)

**Exit criteria**

- Golden-set of case emails (from Phase 1 corpus) classifies correctly at an agreed accuracy bar
- Angry creative-quality email never auto-replies
- FAQ-style spend/report questions produce a draft, not a meeting

**Hard stop.** Do not build calendar writes in this phase except as read-only context.

---

## Phase 5 — Calendar Traffic Controller

**Goal.** Make the calendar a triage system instead of a suggestion box.

**Work**

- FR-04: three contextual time offers (not a naked Calendly dump)
- FR-05: reschedule protocol — cancel, scan, propose, never double-book
- FR-06: meeting-type classifier (15-min stand-up / 45-min deep dive / refuse meeting and reply in text)
- Buffer rules and founder working hours (8 AM–6 PM founder-local, no Friday after 4 PM — to be confirmed in Phase 2)

**Exit criteria**

- “Move tomorrow 11 AM to Thursday” produces one valid Thursday slot and an invite update
- “How do I download the report?” never creates a 30-minute call
- Double-booking is impossible under concurrent requests (lock or transactional check)

---

## Phase 6 — Memory & Retrieval

**Goal.** Answers are factual and safe. Alex should not be the lookup table.

**Work**

- FR-07: pull current campaign performance + recent deliverables from HubSpot/Notion (or demo fixtures)
- Client Brief object generated from unstructured threads
- FR-08: redaction of internal finances, contractor rates, and private team notes
- Citation in the draft (“per the March retainer report attached 12 Mar”) so Alex can verify

**Exit criteria**

- UC-01 can be answered with a number from the knowledge source, not hallucinated
- A planted internal note (“we are raising rates in Q3”) never appears in a client-facing draft

---

## Phase 7 — Safety Net & Founder Controls

**Goal.** Trust-but-verify. Alex stays accountable without living in Gmail.

**Work**

- FR-09 human-only phrases and strategy-logic questions
- FR-10 5:00 PM Executive Summary
- NFR-05 undo/retract within 5 minutes
- NFR-06 tone profiles
- Audit log UI
- Slack ping for Urgent Escalation

**Exit criteria**

- Founder can retract a send or recover a meeting from one control
- Digest contains autonomous count, approval queue, and tomorrow’s top 3
- Tone change is visible on the next draft without a prompt rewrite by Alex

---

## Phase 8 — Portfolio Demo & Upwork Packaging

**Goal.** Prove the case, not the stack. A reviewer should feel Alex’s Tuesday and then see the agent break the loop.

**Work**

- Seeded Pinnacle Marketing workspace (clients, threads, calendar, KB)
- Scripted walkthrough: morning triage → angry client block → smart reschedule → EOD digest
- One-page case study for the Upwork profile: problem, approach, result (time saved in the demo)
- Known limitations list (what is fixture vs. live API)

**Exit criteria**

- A 5–8 minute demo can be run without explaining the SRS
- The happiness paradox is visible: communication stays fast, Alex’s calendar is no longer the delivery bottleneck

---

## How later chats should use this

When work continues:

1. State which phase is being executed.
2. Touch only that phase’s deliverables unless a defect in an earlier phase blocks progress.
3. If a new idea appears (e.g. auto-creating Trello cards), park it in SRS §6. Do not pull it into MVP because it is interesting.

**Next action after this chat:** Phase 3 is complete. Wait for approval before Phase 4 (Inbox Gatekeeper).
