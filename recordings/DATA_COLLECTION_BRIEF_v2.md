# ShopSaarthi Voice Data Collection — Round 2

**Goal:** Build a test corpus spanning multiple real shops so we can measure
where our voice assistant succeeds, where it fails, and how those patterns
shift across shop types, speakers, and noise conditions. Round 1 (Garv's
home recordings) told us the raw transcription is strong; this round tests
whether that holds up in live market environments and pushes on specific
known failure modes.

---

## What we learned from Round 1 (why this list looks the way it does)

Transcription of 32 phrases in quiet conditions captured nearly everything.
The real errors clustered into predictable buckets, and this round is
designed to probe each of them deliberately:

1. **Proper-noun drift.** "Ramu" was heard as "Naamu" / "Aamu"; "Praveen"
   became "Permanent" / "Parman" / "Permit"; "Accountant ji" became
   "Mountain G". Same audio, different ASR calls — which means we need
   many more names to stress this.
2. **Common English word → Hindi phonetic neighbor.** "Shop par" was heard
   as "subah sahab par" (morning-sir). This is not about noise, it is about
   the ASR's language model preferring common Hindi collocations.
3. **Dropped leading tokens in short utterances.** "3 baje" lost the "3";
   "2 hours remind me" lost the "2". Short fragments are more brittle than
   full sentences.
4. **Ambiguous times.** "Aath baje" (8 o'clock) silently resolved to 8 PM
   in the classifier, with no disambiguation prompt.
5. **Missing prefixes.** Speakers dropped "Driver ko" or "Chhotu ko" and
   left a command without a subject; the classifier then guessed "ghar"
   (home) was a person.
6. **Compound commands.** "Rajesh ko message bhejo aur 5 baje yaad bhi
   dilana" — the classifier picked one intent and under-filled slots.

Round 2 probes all six buckets in realistic shop settings, across
multiple speakers at multiple shops.

---

## How to run this in the market — three tiers

Not every shopkeeper has 90 minutes. Match the tier to the opportunity:

### Tier 1 — Quick visit (5-10 min at the counter)
**Goal:** Grab a minimum-viable regression baseline. Use when a shopkeeper
is willing but busy.
- Record **Section A only** (25 phrases).
- One condition: whatever the ambient shop environment is *right now*.
- One speaker: the shopkeeper.

### Tier 2 — Extended visit (30-45 min)
**Goal:** Proper failure-mode coverage.
- Record **Sections A, B, C, D** (~70 phrases).
- Two conditions: (1) shop-ambient (at the counter during normal
  business), (2) quiet-corner (back office, storeroom, or sending the
  shopkeeper home briefly).
- One or two speakers.

### Tier 3 — Full session (90 min, by appointment)
**Goal:** Complete corpus for this shop.
- All sections A through L (~135 phrases).
- Three conditions: quiet, shop-ambient, extra-noisy (near traffic /
  near a loudspeaker / during a rush).
- Two or three speakers (owner + employee + optionally a family member
  or customer who consents).

---

## Target shop mix

Aim for 6-10 shops total, sampling variety. Each of these has different
ambient noise profiles and different vocabulary:

| Shop type           | Why it matters |
|---------------------|----------------|
| Kirana / grocery    | Highest-volume use case; heavy customer conversations |
| Building materials  | Papa's domain — truck noise, cement/rate vocabulary |
| Medical / pharmacy  | Precise names (medicines), quiet ambient, busy phone |
| Stationery / books  | Usually quieter; names of publishers |
| Hardware            | Generator/fan noise, technical part names |
| Sweets / dairy      | Peak-hour crowd, billing vocabulary |
| Cloth / kapda       | Piece/meter/bundle vocabulary |
| Mobile / electronics| English-heavy; prices and model numbers |
| Tea stall / dhaba   | Very noisy; short commands only |
| Auto parts          | Mixed Hindi-English with part-name jargon |

Mark the shop type in the filename (see **File naming** below) so we can
analyze performance per vertical.

---

## Voice-biometric enrollment — one small addition

Before the phrase-by-phrase session, record a short enrollment sample
for each speaker:

- Ask the speaker to read Section A's first 5 phrases back-to-back as
  one continuous recording (approximately 30 seconds).
- Save this file as `<shopID>_<speakerID>_enrollment_<date>.m4a`.

This is all we need. The 2026-04-22 biometric evaluation with
SpeechBrain ECAPA-TDNN achieved clean same-vs-different-speaker
separation on 30-60 seconds of enrollment audio — no dedicated
paragraph recording is required. If a speaker only does Tier 1
(quick visit), skip enrollment for that speaker; we can build the
profile from their phrase recordings later.

## Speakers to target at each shop

Priority order — record the ones available, skip the rest:

1. **Shop owner** — the primary voice we're optimizing for.
2. **Employee / helper** — often younger, different accent.
3. **Woman family member / cashier** — different pitch range; we have
   almost zero female voice data.
4. **Older relative on premises (parents, uncle)** — dialect + age.
5. **A customer who consents** — different prosody, not trained on the
   phrase list.

Minimum per shop: 1 speaker. Ideal: 2-3.

---

## The phrases — 12 sections, ~135 phrases

Each phrase is tagged with its *expected intent* so we can auto-grade
classifier output against ground truth later.

### Section A: Baseline regression (Round 1's original 32)
*Keep the brief's original phrases verbatim so we can compare new-shop
results directly to Round 1 home recordings.*

#### A1. Message (5) — expected intent: `message`
1. Rajesh ko WhatsApp karo, bolo kal subah 10 baje aa jaaye
2. Supplier ko SMS bhejo, cement ka rate kya hai confirm karo
3. Sharma sahab ko WhatsApp karo, kal milte hain shop par
4. Ramu bhaiya ko bolo yaad rakhe, kal delivery aayegi
5. Send message to Sharma ji that payment will be done next week

#### A2. Reminder (12) — expected intent: `reminder`
6. 3 baje yaad dilana Rajesh ko call karna hai
7. Kal subah reminder lagana bank jaana hai
8. 30 minute baad yaad dilana godown check karna hai
9. Subah 8:30 baje yaad dilana
10. Thodi der mein yaad dilana
11. Abhi yaad dilana
12. In 30 minutes remind me
13. In two hours remind me to call supplier
14. Kal shaam yaad dilana
15. Shaam ko yaad dilana godown band karna
16. Raat ko 9 baje yaad dilana
17. Rajesh ko message bhejo ki kal aana hai aur 5 baje yaad bhi dilana

#### A3. Delegate (5) — expected intent: `delegate`
18. Ramu ko bolo Praveen ko call kare aur delivery confirm kare
19. Driver ko bolo 10 baje site par pahunche
20. The driver ko call karo
21. Naukar ko bolo dukaan band kare
22. Chhotu ko bolo ghar jaake khaana le aaye

#### A4. Call (5) — expected intent: `call`
23. Driver ko call karo
24. Rajesh ji ko phone lagao
25. Call Ramu
26. Accountant ji ko call karo abhi
27. Chacha ko phone karo

#### A5. Ambiguous / off-topic (5)
28. Rajesh ko 5 baje bolo — *ambiguous (message/reminder/call)*
29. Yaad dilana aaj — *ambiguous (reminder, no what)*
30. Kuch karo — *ambiguous*
31. Haan theek hai — *off-topic / `unknown`*
32. Namaste, kya haal hai — *off-topic / `unknown`*

---

### Section B: Proper-noun stress (20) — expected: `call` or `message`
*Target the adversarial-name failure mode directly. Use common Indian
names with consonant clusters and English-homophone neighbors.*

33. Praveen ko phone karo — *ASR confused this one 3 ways in Round 1*
34. Mahendra bhaiya ko WhatsApp karo
35. Mukesh ji ko call lagao
36. Naresh ko message bhejo kal milte hain
37. Suresh ko bolo dukaan par aa jaaye
38. Dinesh bhaiya ko call karo abhi
39. Kamlesh ji ko SMS karo, payment ready hai
40. Manoj ko phone lagao
41. Jitendra sahab ko yaad dila dena 3 baje
42. Dhanraj ji ko call karo
43. Babulal ji ko WhatsApp kar do
44. Rajendra ko bolo 10 baje pahunche
45. Jagdish Prasad ji ko call karo
46. Ram Bahadur ko message bhejo
47. Pappu ko call karo
48. Chotu ko bolo — *vs Round 1's Chhotu; test spelling variant*
49. Ashok ji ko phone lagao
50. Vinod bhaiya ko call karo
51. Shyam ji ko SMS bhejo
52. Mohan ji ko bolo kal aaye

---

### Section C: Titles and roles (10)
*Accountant ji became "Mountain G". Test other titles for similar
failure.*

53. Munim ji ko call karo — *expected: `call`*
54. Accountant ji ko message bhejo — *message; known: "Mountain G"*
55. Agent ji ko phone lagao — *call*
56. Distributor ko SMS bhejo — *message*
57. Transporter ji ko bolo gaadi bhej de — *delegate*
58. Electrician ko bolo pankha theek kar de — *delegate*
59. Plumber ko call karo — *call*
60. Tailor master ko bolo kapda ready hai — *delegate*
61. Halwaai ji ko order bhej do — *message*
62. Karigar ko bolo kal aaye — *delegate*

---

### Section D: Time and number edge cases (15)
*Ambiguous times, numbers at the start of utterances, Indian number
formats.*

63. Aath baje yaad dilana — *8 AM or 8 PM? classifier must ask*
64. Subah aath baje yaad dilana — *8 AM, clearer*
65. Shaam ke aath baje Sharma ji ko call karo — *8 PM*
66. Dopahar ke 2 baje delivery aayegi, yaad dilana
67. Raat ke 10 baje dukaan band karna yaad dilana
68. Saade teen baje yaad dilana — *3:30 in colloquial form*
69. Paune paanch baje yaad dilana — *4:45*
70. Sava 12 baje yaad dilana — *12:15*
71. 15 minute mein reminder lagao
72. Ek ghante mein yaad dila dena
73. Aaj se teen din baad yaad dilana
74. Agle Mangalvar subah 10 baje
75. Is hafte ke andar supplier ko payment clear karo
76. Mahine ke 5 tareekh ko bill yaad dilana
77. Sunday ko band rahega, Rajesh ko bata do

---

### Section E: Real shop vocabulary (15)
*Test real-life shopkeeper language: udhaar, bakaya, stock, godown,
rate, invoice.*

78. Rajesh ka bakaya kitna hai, yaad dilana — *reminder / unusual*
79. Ramu ko bolo 5000 ki udhaari hai, yaad rakhe
80. Supplier ko bolo 50 bori cement bheje kal subah tak
81. Ashok bhaiya ki udhaar list nikalo
82. Aaj ka rate check kar lo, supplier ko SMS karo
83. Stock kam ho raha hai, order bhej do distributor ko
84. Par-bill banvana hai, accountant ji ko bolo
85. GST ki file bharani hai, 20 tareekh tak yaad dilana
86. Godown se 10 bori nikalna hai kal, yaad dila dena
87. Invoice bhejo Sharma ji ko, payment clear karna hai
88. Paanch kilo bhari bhej do dukaan par
89. Ek dozen packets bhejo
90. Bundle khol ke dikhana hai, karigar ko bolo
91. Retail rate confirm karo supplier se
92. Purana bill nikaalo, accountant ji se baat karni hai

---

### Section F: Prefix / suffix drop (10)
*Mimic real-world speaker-drops. These SHOULD fail gracefully by
asking who the recipient is.*

93. Site par 10 baje pahunchna — *no recipient; expect clarification*
94. 5 baje milna — *no recipient*
95. Kal subah aana hai — *no recipient*
96. Bolo yaad rakhe — *no recipient*
97. Ghar jaake khana le aaye — *no recipient*
98. Bolo kal aayenge — *no recipient*
99. Delivery confirm kar de — *no recipient*
100. Dukaan band karna hai — *no agent, implied self*
101. Payment ready hai — *no action*
102. Message bhej do — *no recipient, no content*

---

### Section G: Compound / multi-intent (10)
*Two or more intents in one utterance.*

103. Rajesh ko call karo aur bolo kal delivery hai — *call → message on pickup*
104. Ramu ko bolo Praveen ko call kare aur mujhe yaad dila dena — *delegate + reminder*
105. Supplier ko SMS karo aur 2 ghante baad yaad dilana confirm karna — *message + reminder*
106. Call karo aur phir message bhejo bank detail ke saath — *call + message*
107. Kal subah bank jaana yaad dilana aur 10 baje Mahesh ko message bhejo — *reminder + message*
108. Driver ko bolo site par pahunche aur mujhe yaad dila dena check karna — *delegate + reminder*
109. Accountant ji ko bolo bill banaye aur Sharma ji ko WhatsApp karo — *delegate + message*
110. Aaj shaam ko godown band karna yaad dila aur Chhotu ko bolo chaabi lock kare — *reminder + delegate*
111. Paanch minute baad reminder lagao aur supplier ko confirm karo — *reminder + delegate*
112. Agar Ramu na uthaaye to Suresh ko phone karo — *conditional call*

---

### Section H: Pronouns and deictic references (8)
*"Him", "that guy", "the new customer" — requires context resolution.*

113. Usko call karo — *who is "him"?*
114. Wahan wale ko message bhejo — *which person?*
115. Naye wale customer ko WhatsApp karo
116. Kal wale supplier ko SMS karo — *"the one from yesterday"*
117. Jo abhi aaya tha usko phone karo
118. Woh wala distributor ko bolo delivery bhej de
119. Upar wale godown wale ko bolo
120. Sharma ji wale agent ko message bhejo — *genitive chain*

---

### Section I: Prosody variants (6)
*Same phrase, different speed / emotion. Pick one phrase from Section A
and say it 6 different ways.*

Base phrase: **"Rajesh ko WhatsApp karo, kal 10 baje aa jaaye"**

121. (Normal pace, neutral tone)
122. (Rapid, almost one word: "Rajeshkowhatsappkarokal10bajeaajaye")
123. (Slow, with pauses: "Rajesh ... ko ... WhatsApp ... karo ...")
124. (Urgent / raised voice: "Jaldi! Rajesh ko WhatsApp karo abhi!")
125. (Tired / low energy)
126. (Speaking while walking — footsteps / breathing audible)

---

### Section J: Off-topic / unknown intent (6)
*Should cleanly resolve to `unknown`.*

127. Aaj ka mausam kaisa hai
128. Bhaisahab, chai lagao
129. Ruk, main abhi aata hoon
130. Yeh wala record mat karna
131. Are rehne de
132. Haan bhai kya chal raha hai

---

### Section K: Corrections and retries (5)
*Multi-turn flows. Should mostly resolve to `unknown` at the single-utterance
level — the full handling needs a conversation layer we haven't built yet.*

133. Nahin nahin, Rajesh nahin, Mahendra ko call karo
134. Haan wahi, usko phone lagao
135. Ek minute ruko, phir se bolta hoon
136. Cancel karo, last wala
137. Wait, phir se — Supplier ko SMS bhejo

---

### Section L: Future-phase intents (7)
*These now have their own classifier categories as of 2026-04-22 — the
bot recognises them and logs them to `FuturePhaseLog`, but does not
yet fulfil them. Expected intents listed alongside so the field
recorder can verify the classifier routed correctly.*

138. Aaj ka total sale kitna hua — *expected: `summary`*
139. Stock check karo cement ka — *expected: `inventory`*
140. Kitne ki udhaari hai Ashok bhaiya ki — *expected: `collection`*
141. Bill print karo — *expected: `unknown` (not covered by any future-phase category)*
142. Purana order repeat karo — *expected: `order`*
143. Kal ki sale ki report dikhao — *expected: `summary`*
144. Shop band karne ka time bata — *expected: `summary` or `unknown`*

---

## Recording protocol

### Equipment
- Smartphone's built-in mic. Any of: iPhone Voice Memos, Samsung Voice
  Recorder, Easy Voice Recorder (Android).
- Format: M4A or MP3. WAV is fine but larger.
- Sample rate: whatever the app defaults to (typically 44.1 or 48 kHz).
- **Do not** use earphones with an attached mic. The phone mic is what
  the bot will actually receive.

### Distance
- Phone held 15-20 cm from the speaker's mouth. Normal holding distance.
- Do not rest the phone on a hard surface right next to the speaker —
  that changes the acoustics.

### Pacing
- Read each phrase once, at a natural pace. Do not re-do for a "better
  take" unless the speaker stumbled mid-word.
- Pause 2-3 seconds between phrases. Clear gaps let us cut the file
  into per-phrase clips later.
- **Do not** explain the phrase's meaning to the speaker in detail.
  A brief "bas aise bolna jaise kisi ko command de rahe ho" is enough.
- Skip any phrase the speaker can't say comfortably. Note which number
  they skipped.

### Conditions to record
Record each speaker in as many of these conditions as the shop allows:

1. **Quiet**: back office, storeroom, or outside shop hours. Goal: zero
   background conversation.
2. **Shop-ambient**: at the counter during normal business. Goal: the
   real acoustic environment the bot will face.
3. **Extra-noisy** *(optional)*: near the road, near a neighbor's
   loudspeaker, or during a clear rush. Goal: worst-case audio.

The same speaker should say the same phrase in each condition so we can
isolate the effect of noise from the effect of speaker/phrase.

---

## File naming

```
shopID_speakerID_condition_section_YYYY-MM-DD_take.m4a
```

- **shopID**: short code like `kirana01`, `buildmat02`, `medical03`.
  Use the same ID for all recordings at one shop.
- **speakerID**: role + index: `owner`, `emp1`, `emp2`, `family`,
  `customer`.
- **condition**: `quiet`, `ambient`, or `noisy`.
- **section**: section letter from the phrase list, e.g. `A`, `B-C`,
  `full`. If one file contains multiple sections, use `A-D`.
- **YYYY-MM-DD**: recording date.
- **take**: `1`, `2`, ... for multiple sessions on the same day.

Examples:
- `kirana01_owner_ambient_A_2026-05-01_1.m4a`
- `buildmat02_emp1_quiet_A-D_2026-05-03_1.m4a`
- `medical03_family_noisy_full_2026-05-05_2.m4a`

One file per `(shop, speaker, condition, section-range, take)`. A single
file can contain all 135 phrases in sequence if the speaker reads them
continuously — that is fine, we will cut them apart later.

---

## Metadata to capture per shop visit

Alongside the audio, create a simple text file `shopID_metadata.txt`
with:

```
shop_id: kirana01
shop_type: kirana
location: Indira Market, Nagpur (approximate, no exact address)
date: 2026-05-01
visit_duration_min: 45
tier: 2

speakers:
  - id: owner
    age_range: 45-55
    gender: M
    native_language: Marathi + Hindi
    notes: soft voice, some dental issues affect /s/
  - id: emp1
    age_range: 18-22
    gender: M
    native_language: Hindi
    notes: faster pace, occasional stammer

conditions_recorded:
  - quiet: back office (counter was closed 15 min)
  - ambient: 11 AM, moderate foot traffic, neighbor playing radio
  - noisy: not captured — no noisy moment available

phrases_skipped: 48, 97
  # 48: Chotu — speaker said "Chhotu" same as #22
  # 97: Ghar jaake khana le aaye — felt repetitive, skipped

consent:
  - owner: yes (verbal, recorded at start of session)
  - emp1:  yes (verbal)

observations:
  - Owner used "dhyaan rakhna" interchangeably with "yaad rakhna" — this
    would be an interesting alternative phrasing to test.
  - Generator kicked in mid-session; one minute of noise spike around
    11:07 AM (trimmed from clean-section file).
```

---

## Consent — what to say to each speaker

Before recording, in the speaker's comfortable language:

> "Main Ashish ji ke voice assistant project ke liye kuch phrases record
> kar raha hoon. Ye sirf unke testing mein istemaal hogi, kisi ko aur
> nahin dee jaayegi. Aap 5-10 minute ke liye kuch commands bol kar
> record karwa sakte hain? Agar aap bolna nahin chaahte, koi baat nahin."

Record their **verbal yes at the start of the file itself** (first few
seconds). If they say no, do not record that person — pick someone else.

---

## Priorities if you only have limited time

If the team member can only do 5 shops instead of 10, prioritize:

1. Two kirana/grocery shops (the highest-volume target segment).
2. One building-materials shop (Papa's vertical).
3. One tea stall / dhaba (worst-case noise; short commands only from
   Section A needed).
4. One more — pick by availability.

If forced to cut phrases, Sections A, B, C, and F are the highest-value
subsets:
- **A**: regression baseline (compare directly to Garv's home session)
- **B**: the known-bad names
- **C**: the known-bad titles
- **F**: the prefix-drop failures that the classifier most visibly
  mishandles

Leave Sections E, G, H, K, L for the shops that have time.

---

## Delivery

Upload all files into a shared Google Drive folder named
`ShopSaarthi Data Round 2 - <your name>`. Keep the per-shop structure:

```
ShopSaarthi Data Round 2 - <name>/
  kirana01/
    kirana01_owner_ambient_A_2026-05-01_1.m4a
    kirana01_owner_quiet_A_2026-05-01_1.m4a
    kirana01_emp1_ambient_full_2026-05-01_1.m4a
    kirana01_metadata.txt
  buildmat02/
    ...
```

Share the folder with AV (email to be provided) once at least one shop
is complete. Do not wait until everything is done to share — early
uploads let us sanity-check audio quality and flag issues before more
shops are recorded.

---

## Summary in one sentence

Hit 6-10 shops across verticals, record the owner (plus anyone else
willing), read the 25 baseline + the failure-mode probes that fit in
the time available, capture real ambient noise as-is, name files with
shop/speaker/condition/section/date, and log per-shop metadata. The
point is to stress the bot against realistic market variety — not to
produce clean studio audio.
