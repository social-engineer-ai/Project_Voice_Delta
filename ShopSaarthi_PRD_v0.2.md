# ShopSaarthi Product Requirements Document

**Version:** 0.2
**Date:** April 2026
**Owner:** Ashish Khandelwal
**Status:** Phase 1 build in progress

## Revision History

- **v0.1 (April 2026):** Initial draft covering product vision, five-phase plan, three-layer architecture, WhatsApp-primary messaging, Tier-2/3 focus, voice biometrics and noise suppression deferred to Phase 4.
- **v0.2 (April 2026):** Telegram as primary and only bot interface from Phase 1. Market scope expanded to small and medium businesses across all city tiers including showrooms. Voice biometrics promoted to Phase 1 as a trust feature with shop-configurable security threshold. Noise handling addressed through field testing protocol rather than preemptive noise reduction build. Phase 1 timeline revised to 3-4 weeks. Pricing tiers restructured based on verified April 2026 API costs. Unit economics section added with April 2026 Sarvam and Gemini pricing.

## 1. Product Vision

ShopSaarthi is a voice-native operational assistant for Indian small and medium businesses. It captures the hundreds of small tasks a shopkeeper or business owner generates daily — sales, credit, reminders, instructions to servants, communications with suppliers, inventory notes, customer balance queries — through natural Hindi speech in the business's real acoustic environment, and turns them into structured data the owner can retrieve, act on, and share.

The product is built on three principles. First, vernacular-native design: the system is built for Hindi, mixed Hindi-English, and eventually regional languages as they are spoken in Indian commercial contexts, not as a translation layer over English-first AI. Second, multi-party interaction awareness: Indian shopkeepers talk to multiple parties in parallel with frequent interrupts, and the system understands this structure rather than fighting it. Third, cost efficiency through bounded task universes: each business vertical has a bounded set of common tasks, which lets the core interaction run on small fast models, with larger models reserved for occasional high-value intelligence tasks.

The long-term ambition is a platform that serves multiple business verticals — kirana, building materials, hardware, commission agents (dalals), medical stores, stationery, sweet shops, tailors, small restaurants, showrooms (jewelry, furniture, electronics, clothing, automobile) — each with a specialized profile layered over a common task ontology, with individual shop-level customization emerging through use.

## 2. Target User

Primary: Indian small and medium business owners running single-location or small-chain operations, across all city tiers. Typical profile is an owner who runs the business personally or with a small team, whose operational bookkeeping is some combination of memory, scratch paper, WhatsApp voice messages, and a monthly accountant, and who loses real time and money to information friction every week.

The product is not restricted to Tier-2 or Tier-3 cities. A Delhi jewelry showroom owner has the same information management problem as a Siyaganj kirana shopkeeper, often at higher volume and higher revenue per customer. What they share is: vernacular operational culture, preference for voice over typing, multi-party interaction patterns, existing reliance on WhatsApp and UPI, and underservice by current English-first SaaS tools.

Phase 1 deployment concentrates in Indore because the founder has distribution advantage there (family network, former teaching relationships across 10+ local MBA colleges, credit-card-era selling experience in Siyaganj markets). This is a go-to-market choice, not a product limitation. Subsequent phases expand geographically and across business types.

Secondary users: accountants who serve these businesses, servants and helpers who execute tasks on the owner's behalf, family members involved in the business, and commission agents (dalals) whose work is almost entirely information management.

## 3. Core Value Proposition

For the business owner: "Stop losing time to reconstructing what you said, promised, and agreed to during the week. Speak it once, find it when you need it, never forget a task or a customer balance."

Concrete time savings: the Pravin case (commission agent who spends weekends making fair copies of scratch notes) points to 8-16 hours per week of clerical work that becomes unnecessary. For a kirana or building materials shopkeeper, the value is less about fair-copy time and more about reducing errors, forgotten promises, and credit lapses — typically worth several thousand rupees per month in avoided losses plus reduced cognitive load. For showroom owners, the value shifts toward customer relationship continuity — remembering what was discussed with a high-value customer across multiple visits.

## 4. Product Phases

The product is built in five phases, each one a working product that delivers value to users, with later phases extending rather than replacing earlier ones.

### Phase 1: Core Voice Assistant with Trust Layer (April - May 2026, 3-4 weeks)

The minimum viable product handles four core intents end-to-end, with Telegram as the sole interface and voice biometric verification as a trust feature from day one.

**Core intents:**

1. *Send message* — "Rajesh ko WhatsApp karo, kal delivery aayegi." Bot composes the message, identifies the recipient from the contacts database, provides a tap-to-send link that opens the shopkeeper's own WhatsApp or SMS with content pre-filled. Zero messaging cost to the product because the shopkeeper's carrier handles delivery.

2. *Set reminder* — "3 baje yaad dilana Sharma ji ko call karna hai." Bot parses the time expression (absolute or relative, Hindi or English), schedules a Telegram ping for that time, notifies the shopkeeper when it fires.

3. *Delegate task* — "Ramu ko bolo Praveen ko call kare aur delivery confirm kare." Bot generates a WhatsApp tap-to-send link for the instruction, schedules a follow-up reminder to the shopkeeper to verify completion.

4. *Make call* — "Driver ko call karo." Bot resolves the contact, provides a tap-to-dial link that uses the shopkeeper's own carrier (Jio/Airtel/Vi), which is free on current prepaid plans. No bridged calling, no per-call cost.

**Voice biometric trust layer:**

During onboarding, the shopkeeper enrolls their voice by speaking 5-7 short phrases. The system extracts voice embeddings using Resemblyzer and stores them per user. Each subsequent voice command is checked against the enrolled embedding before being processed.

This is a *trust feature*, not a security feature. Its primary purpose is to demonstrate to customers standing at the counter that the bot is specifically tied to the shopkeeper. When the shopkeeper asks the bot for a customer's balance in front of that customer, the customer can see that the bot responds only to the shopkeeper's voice — building confidence in the information.

The security threshold is configurable per shop, because different shops have different needs:
- **Strict** — accepts only clearly-matching voices; minimizes false acceptance at the cost of occasional false rejection of the owner.
- **Medium** (default) — balanced setting suitable for normal single-user operation.
- **Loose** — accepts voices that are plausibly the enrolled user; useful when family members share the account or when the owner's voice varies significantly.

The shopkeeper sets this through a `/security` command. When a voice fails verification, the bot responds visibly so the rejection is observable: "Yeh awaaz match nahi hui. Agar yeh aap hi hain, /security loose karke try kariye."

The shopkeeper can also run `/reenroll` at any time to augment their voice profile with fresh samples, which reduces false rejections as the profile becomes more robust to vocal variation.

**Contact management:**

Shopkeepers add contacts through `/addcontact <name> <phone> [role]`. The contact database supports role-based references ("the driver"), honorific stripping ("Rajesh ji" → "Rajesh"), aliases, and fuzzy name matching. This is the foundation for correctly resolving "Rajesh," "Ramu," "driver," "the supplier" to actual phone numbers in voice commands.

**Stack:**

Python 3.11, python-telegram-bot 21.6, FastAPI (for future dashboard), PostgreSQL (SQLite for local dev), Sarvam Saarika v2.5 for Hindi/multilingual ASR, Google Gemini 2.5 Flash-Lite for intent classification and entity extraction, Resemblyzer for speaker embeddings, APScheduler with SQLAlchemy job store for reminders. Deployed on AWS (using Activate credits) in ap-south-1 for low latency to Indian users.

**Phase 1 success criteria:**

The author's brother uses the system for real daily tasks in his building materials shop for 14 consecutive days without abandoning. Self-reported value: at least one real task prevented from being forgotten or lost per day. Voice biometric accuracy: fewer than 5% false rejections on the author's brother's voice across normal shop conditions. Technical: 85%+ ASR accuracy on vocabulary that appears in his shop, 90%+ intent classification accuracy, end-to-end latency under 5 seconds including speaker verification.

### Phase 1b: Bill Generation and Tally Export (May - June 2026, 2 weeks)

Extension of Phase 1 adding commercial document generation, targeted at the accountant user's needs and at demonstrating product range during the India trip demos.

Shopkeeper speaks a bill creation command: "Rajesh ji ka bill banao, 20 bori ACC cement 380 rupee ka, 10 bori Ultratech 410 ka, aur 5 kilo binding wire 75 rupee ka." System parses line items, pulls customer details from contacts, applies hardcoded GST rates and HSN codes for the 15-20 items the author's brother commonly sells, generates a sequential bill number, produces a PDF bill and a Tally-compatible XML export.

The accountant can download Tally XML from a simple web dashboard and import into their existing Tally installation. This is the bridge feature that makes the product valuable to accountants directly and creates natural distribution into their other client shops.

### Phase 2: India Field Deployment and Paid Beta (June - August 2026, 10-12 weeks)

The author relocates to Indore for 2-3 months. Deployment expands from family-network testing to a structured paid beta with 15-40 shops across 2-4 verticals in Indore, plus a light-touch deployment of 10-20 shops in Surat through a single relationship to establish geographic signal.

Shops join as founding collaborators rather than passive beta testers — the product is co-built with domain partners (building materials via author's brother, medical via friend's daughter who is based at her father's shop, dalal via Pravin, accountant as a separate interface collaborator) who each contribute operational knowledge, test the system in their real work, and surface edge cases that inform product evolution.

Operational support is established through a hired or appointed operations lead in Indore who handles shop onboarding, ongoing support, and feedback collection after the author returns to the US in August. Compensation for this role: ₹40,000-60,000 per month full-time or equivalent part-time arrangement.

DAV Indore and other local MBA college connections are activated for structured student engagement during the summer. The author has prior teaching relationships at 10+ Indore MBA colleges; 3-5 student interns are recruited for observation, annotation, and support work at ₹5,000-10,000/month stipends.

**Phase 2 success criteria:**

40-80 shops actively using the product with 3+ weeks of retention by end of summer. At least 60% of shops indicate willingness to continue at paid pricing after the beta period. Operations lead is functioning independently for day-to-day support by the time the author returns. Initial data on product-market fit, pricing willingness, and vertical-specific usage patterns.

### Phase 3: Multi-Vertical Expansion and Ontology Building (September 2026 - February 2027, 6 months)

The product extends from 2-4 verticals to 6-8, and the three-layer schema architecture is fully implemented.

**Three-layer architecture:**

Layer 1 (general): approximately 40-50 universal task types spanning transactional, inventory, people, time, information, communication, and financial oversight categories. Stable across verticals.

Layer 2 (vertical): 60-100 specialized task patterns per vertical layered over the general ontology, with vertical-specific vocabulary and entity types. New verticals added include hardware, medical (OTC only for Phase 3), stationery, sweet shops, and one initial showroom vertical (likely small electronics or furniture based on Phase 2 learnings).

Layer 3 (shop-specific): individual parties, items, patterns, voice profiles, and preferences learned through use.

**Student research program:**

Annotation tool built as a progressive web app for structured observation by student researchers. Students from DAV, IIM Indore, and other local institutions conduct paid short-term observation projects in shops through their family/relationship networks across multiple Indian cities. Dual-level tagging (vertical and shop) feeds the ontology directly. Target: 15-25 students across 2 semesters producing 60-100 documented shop observations.

**Operations:**

Scale from 80 shops to 150-250 shops across Indore, Surat, and 1-2 additional cities. Operations team grows to 2-3 people in Indore.

**Phase 3 success criteria:**

6-8 active verticals, 150-250 paying shops, ontology extension mechanism demonstrated (new verticals added in under 6 weeks from first observation to deployment), one working paper or conference submission describing the methodology, investor conversations initiated with Abhishek Sanghvi or equivalent ecosystem partners based on concrete traction data.

### Phase 4: Scale, Intelligence Features, and Multi-User Support (March - December 2027)

Scaling phase. Product grows from 250 shops in 3 cities to 800-1500 shops across 5-10 cities, with a functional operations team in India handling deployment, support, and customer success.

**Intelligence features** (using larger models occasionally, not on every interaction):

Weekly business summaries, GST-ready transaction exports for accountants, pattern detection (regular customer hasn't visited, supplier prices drifting, credit exposure growing), cross-shop benchmarking in anonymized aggregate. These run once per week per shop and use Gemini 2.5 Flash or Claude Haiku 4.5 depending on complexity.

**Multi-user support:**

Additional family members and authorized employees can be enrolled with their own voice profiles, with permission tiers. Shopkeeper can authorize large transactions; servant can log tasks but not authorize credit; accountant has read-only access for specific exports. The voice biometric infrastructure from Phase 1 is extended to handle multiple users per shop.

**Showroom vertical expansion:**

Showroom-specific features added including multi-visit customer tracking, long sales cycle coordination, high-ticket transaction handling, and visual product reference (where the shopkeeper can say "the customer liked the piece I showed yesterday" and the system retrieves the conversation context).

**Phase 4 success criteria:**

800-1500 shops, monthly recurring revenue ₹8-20 lakh, operations team of 4-6 people in India, multi-user deployed for 30%+ of active shops, intelligence features consumed by 50%+ of active shops.

### Phase 5: Platform, Ecosystem, and Commercial Structure (2028 and beyond)

Platform capabilities (accountant API, Tally/Vyapar/Khatabook integrations, third-party vertical extensions). Commercial structure matures based on evidence. If traction supports it, formal India entity, operator co-founder arrangements, and potential investor rounds of scale. If path is clearer to continued bootstrapping or small funding, that path is taken.

## 5. Technical Architecture

### 5.1 Stack (April 2026)

- **Python 3.11** with type hints throughout
- **python-telegram-bot 21.6** for Telegram integration
- **FastAPI** for web dashboard (Phase 1b onwards)
- **PostgreSQL** production, SQLite for local dev
- **SQLAlchemy 2.0** ORM
- **Sarvam Saarika v2.5** for ASR (₹30/hour ≈ ₹0.50/minute; free tier ₹1000 credits)
- **Google Gemini 2.5 Flash-Lite** for intent classification ($0.10/$0.40 per 1M tokens)
- **Resemblyzer** for speaker verification embeddings (open-source, runs locally)
- **APScheduler 3.10** with SQLAlchemy job store for persistent scheduled reminders
- **RapidFuzz** for fuzzy contact name matching
- **AWS** infrastructure in ap-south-1 (Mumbai) using Activate credits

### 5.2 Model Strategy

The strategy prioritizes small, fast, cheap models for high-frequency core interactions, with larger models reserved for occasional high-value intelligence tasks.

**Speech-to-text:** Sarvam Saarika v2.5 as primary. Handles Hindi, code-mixed Hindi-English, 9 other Indian languages, with auto-language-detection via `language_code="unknown"`. Pricing is per-minute, which scales directly with usage.

*Open-source evaluation:* Fine-tuned Whisper Small on Indic-specific data could reduce ASR cost to near-zero once self-hosted on AWS Activate credits. Phase 3 evaluation: if a fine-tuned Whisper Small beats Sarvam accuracy within 5% on our test set, migrate. Until then, Sarvam is the right choice for cost and quality.

**Intent classification and entity extraction:** Gemini 2.5 Flash-Lite as primary. Selected because at $0.10/$0.40 per million tokens it is the cheapest production-quality LLM available from a major provider in April 2026, and the bounded task universe (4 intents) doesn't require a more capable model.

*Fallback options if accuracy insufficient:* Gemini 2.5 Flash at $0.30/$2.50, or Claude Haiku 4.5 at $1.00/$5.00. *Long-term open-source migration:* Fine-tuned Gemma 2B or Llama 3.2 3B on accumulated task corpus once 50+ shops' data is available (Phase 3+).

**Speaker verification:** Resemblyzer open-source library. Produces 256-dimensional voice embeddings. Cosine similarity comparison against enrolled embedding. Configurable threshold per shop. No per-call cost since it runs on our infrastructure.

**Text-to-speech (Phase 4+ for intelligence summaries):** Sarvam Bulbul at ₹15 per 10,000 characters.

**Intelligence features (Phase 4+):** Gemini 2.5 Flash or Claude Haiku 4.5 depending on complexity. Runs weekly per shop, not per interaction, so cost is negligible.

### 5.3 Three-Layer Schema (Phase 3+)

Detailed architecture deferred to Phase 3 implementation. Phase 1 uses a simpler flat schema with intent-specific JSON payload, designed to be refactorable into the three-layer architecture without data migration.

### 5.4 Infrastructure

Backend: FastAPI application, Postgres, S3-compatible object storage for voice recordings (temporary — deleted after embedding extraction and transcription), Redis for caching. AWS ap-south-1.

Client: Telegram bot only in Phase 1. No mobile app. No web app initially. Web dashboard for accountant Tally export begins in Phase 1b.

### 5.5 Noise Handling: Field-Tested Rather Than Preemptively Built

Rather than building generic noise reduction as a Phase 1 feature, the product is tested in real shop acoustic environments using a structured field-testing protocol.

**Field testing protocol:**

A 12th-grade research assistant in Indore visits 15-20 shops across diverse acoustic environments (busy tea shop, quiet kirana, building materials shop with vehicle noise, medical store with foot traffic, small restaurant during lunch rush, hardware store with drilling, sweet shop during festival season). For each shop, he records 15-20 minutes of realistic utterances using a prepared set of 30-40 Hindi prompts spanning the four intents. Each recording has metadata: shop type, dominant noise signature, ground-truth transcription, speaker role.

Total engagement: approximately ₹15,000-20,000 for the initial dataset over 3-4 weeks.

**Evaluation:** Sarvam Saarika is run against the field dataset. Word error rate is measured across environments. If accuracy is 85%+ across all environments, no additional noise preprocessing is added. If accuracy drops below 85% in specific noise types, targeted preprocessing is added using open-source libraries (RNNoise, Facebook Denoiser) for those specific environments only.

This approach is better than building generic noise reduction because it's calibrated to actual deployment conditions. It also produces a reusable test dataset for future model evaluation.

## 6. Data Collection and Training

### 6.1 Phase 1 Bootstrap

The first classifier uses Gemini's general capabilities with careful system prompting and few-shot examples. No fine-tuning in Phase 1. Training data is accumulated through Phase 2 beta usage with shop consent as part of participation terms.

### 6.2 Paid Beta Corpus (Phase 2)

15-40 paid beta shops contribute voice data as a term of participation. Consent is explicit: shops sign a one-page agreement in Hindi covering recording scope (voice commands and shop-environment audio during commands), retention (12 months, then destroyed), anonymization (personally identifying information removed within 30 days), and withdrawal rights (data destroyed within 30 days of request).

Compensation: ₹1,500-2,500 per month per shop for 8 weeks of paid beta. Shops keep benefit of any value the tool provides during this period. After the beta, shops continue at regular subscription pricing if they choose.

Customer privacy: signage in each shop notifies customers that recording is in progress for product improvement. Customer voices are excluded from training data through voice-separation preprocessing.

### 6.3 Student Research Corpus (Phase 3)

The annotation tool and student program generate structured observation data (not audio training data) feeding the vertical ontologies. Audio training data continues to come from paid beta shops under the same protocols.

### 6.4 Commercial Usage Data (Phase 3 onward)

Paying subscriber usage data flows into the training corpus under standard commercial terms of service, legally distinct from research data.

## 7. Ethical Protocols (Lab Protocols)

The project operates under internal lab protocols rather than through UIUC IRB in Phase 1-2, given the international fieldwork complexity and tight timeline. Protocols match what would be required under IRB in substance.

**Documented protocols:**

- Informed consent from every participating shop owner in Hindi
- Transparent customer notice (signage) in every participating shop
- Encrypted data storage with restricted access
- Confidentiality agreements for anyone with access to raw recordings
- Systematic anonymization within 30 days of recording
- Raw audio retention limited to 12 months, then destroyed
- Exclusion from corpus of any content involving minors, sensitive personal information, or illegal activity
- Withdrawal rights exercisable at any time with 30-day compliance
- Annual protocol review

Lab protocol document is signed by the author and any research assistants, stored with project records, and revisited annually. If Phase 3 outputs are targeted for academic publication, retroactive IRB review is pursued at that time.

## 8. Pricing (Revised)

Based on April 2026 API costs with Telegram as the messaging primary and AWS Activate credits covering initial infrastructure.

**Per-shop monthly cost estimates:**

*Phase 1-2* (commercial APIs, AWS credits covering infrastructure):
- Sarvam ASR at 60 interactions/day × 10 seconds: ~₹150/month
- Gemini Flash-Lite for classification: ~₹10-20/month
- Speaker verification: effectively zero (runs locally)
- Telegram: zero
- SMS for non-Telegram contacts: ~₹10-30/month
- Infrastructure: zero during credits, ~₹30-50/month at scale
- **Total: ₹170-250/month per shop**

*Phase 3-4* (mix of commercial and self-hosted):
- Self-hosted Whisper for ASR: ~₹30-60/month
- Self-hosted small LLM for classification: ~₹10-20/month
- **Total: ₹60-130/month per shop**

**Subscription tiers:**

*Basic — ₹199/month or ₹1,999/year (17% annual discount):*
- Up to 30 interactions per day
- Four core intents (message, reminder, delegate, call)
- Single user, voice-verified
- Daily WhatsApp summary of tasks
- Basic retrieval

*Standard — ₹399/month or ₹3,999/year:*
- Up to 80 interactions per day
- All Basic features plus bill generation with Tally export
- Expanded retrieval and search
- Multi-user voice support (up to 3 enrolled voices)
- Phase 4 intelligence features included as they launch

*Power — ₹799/month or ₹7,999/year:*
- Unlimited interactions
- All Standard features plus accountant dashboard access
- Priority support
- Advanced reporting and GST-ready exports
- Suitable for dalals, high-volume shops, and small showrooms

*Free first month for all tiers, no credit card required, easy cancellation.*

**Margin at scale (Phase 3-4):**
- Basic: ₹199 revenue, ~₹80 cost = ~60% gross margin
- Standard: ₹399 revenue, ~₹130 cost = ~67% gross margin
- Power: ₹799 revenue, ~₹200 cost = ~75% gross margin

These margins support a real SaaS business at a few thousand active shops.

## 9. Success Metrics Across Phases

### Phase 1: 3-4 weeks
Author's brother uses system for 14 consecutive days without abandoning. Self-reported value: ≥1 real task saved or prevented from loss per day. Voice verification false-rejection rate <5% for the enrolled user across normal shop conditions. Technical: 85%+ ASR accuracy, 90%+ classification accuracy, <5s end-to-end latency.

### Phase 1b: Additional 2 weeks
Bill generation demonstrated to accountant. Tally XML export successfully imported to the accountant's Tally installation for at least 10 test bills. Accountant signals willingness to adopt for his other clients if product continues to work.

### Phase 2: 10-12 weeks India deployment
40-80 shops active with 3+ weeks retention. 60%+ willingness-to-pay signal at tier pricing. Operations lead functioning independently. 1-2 domain collaborators (brother, accountant, Pravin, friend's daughter) actively contributing to product evolution.

### Phase 3: 6 months (Sep 2026 - Feb 2027)
6-8 active verticals, 150-250 paying shops, one academic working paper, student research program producing 60+ documented observations, investor conversations initiated.

### Phase 4: 2027 full year
800-1500 shops, ₹8-20 lakh monthly recurring revenue, operations team of 4-6, multi-user deployed for 30%+ of shops.

### Phase 5: 2028+
Platform capabilities live, commercial structure finalized based on evidence, potential investor round or continued bootstrapping path decided.

## 10. Open Questions and Decisions Pending

**Model migration timing:** When does accumulated fine-tuning data justify migrating from Gemini Flash-Lite to self-hosted Gemma 2B or similar? Decision criterion: when gross margin on Basic tier drops below 50% at scale, or when Gemini pricing changes adversely, or when classification accuracy on fine-tuned model exceeds Flash-Lite by 2%+ on our test set.

**Edge device vs phone-only:** Telegram bot on Android phone is the Phase 1 interface. Evaluate in Phase 3 whether a dedicated device (Raspberry Pi on the shop counter with always-on microphone) adds enough value to justify its cost and complexity.

**Commercial structure in India:** Deferred until Phase 3 when traction data supports an investor conversation. Current operating mode is founder-owned with contractor arrangements for Indian staff. Structure formalizes when funding is raised or revenue justifies it.

**Offline architecture:** Currently online-dependent for ASR and LLM. Revisit at end of Phase 2 based on empirical data about shop connectivity reliability. If offline becomes a retention issue, add queued capture in Phase 3.

**IRB path for research outputs:** Phase 1-2 operates under lab protocols. If Phase 3 outputs are targeted for academic publication at venues requiring IRB, pursue retroactive IRB review at that time. If outputs stay as working papers or industry venues, lab protocols are sufficient.

**Surat deployment depth:** Phase 2 includes light-touch Surat deployment (10-20 shops through one relationship). Decide at end of Phase 2 whether to invest in a proper Surat operation or consolidate in Indore and MP before geographic expansion.

## 11. Note for Claude Code Implementation

When a Claude Code session picks up this PRD to implement Phase 1 features, it should pause before coding and discuss with the author which Claude Code capabilities would add value for this specific build. Possibilities to consider:

- **Custom skills** for Telegram bot patterns, Sarvam integration, Resemblyzer integration
- **Hooks** for running the test_classify.py suite before committing prompt changes
- **Subagents** for parallel work on backend handlers vs. client testing
- **MCP servers** for Telegram API, AWS deployment, database management
- **CLAUDE.md** additions specifying the architecture conventions, language style (Hindi strings, Hinglish variable names where appropriate), and the lab protocol requirements
- **Plan mode** for multi-step features like voice enrollment flow that touch several files

The author prefers grounded, restrained implementation without grandiosity. No em-dashes in code comments. Plain professional language. Understated tone. Code should be readable by a mid-level engineer maintaining the project after the author has moved to other work.


Future aspects

Model migration to Gemma 4 (26B MoE). Apache 2.0 licensed, better economics at scale, fine-tunable on accumulated corpus. Evaluation trigger: when monthly classifier call volume exceeds 50,000 calls (roughly 80+ active shops), or when Flash-Lite pricing changes adversely, or when accumulated fine-tuning data from 50+ shops is available. Also evaluate E2B/E4B sizes for potential on-device deployment in markets with unreliable connectivity.
