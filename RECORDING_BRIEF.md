# ShopSaarthi Voice Recording Brief

**Purpose:** Collect voice recordings to test our ShopSaarthi bot's ability to understand Hindi voice commands from real shopkeepers in real shop environments.

---

## What this is

We are building a voice assistant for Papa's shop (and eventually other shops). The assistant listens to voice commands in Hindi and understands what to do. For it to work well, we need to test it against real voices of real people in real shops, not just clean studio recordings.

You are helping us build this test dataset.

---

## What you need

1. A smartphone (your own is fine) with a voice recorder app.
2. Three people willing to record: Papa (chachaji), Dadaji, and one or two other people (an employee at the shop, a family member, or a friend). More voice variety is better.
3. Access to the shop during both a quiet time and a busy time.
4. About 2-3 hours of your time across 2-3 sessions.
5. A quiet space for the clean recordings (shop back office, home, storeroom).

---

## The 32 phrases to record

Each person will speak each of these 32 phrases, twice: once in a quiet place, once in the busy shop. Read them naturally, as if you were actually telling a helper to do these things. Don't exaggerate clarity. Don't exaggerate noise.

### Message phrases (sending WhatsApp or SMS)

1. Rajesh ko WhatsApp karo, bolo kal subah 10 baje aa jaaye
2. Supplier ko SMS bhejo, cement ka rate kya hai confirm karo
3. Sharma sahab ko WhatsApp karo, kal milte hain shop par
4. Ramu bhaiya ko bolo yaad rakhe, kal delivery aayegi
5. Send message to Sharma ji that payment will be done next week

### Reminder phrases (setting reminders)

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

### Delegate phrases (telling someone to do something)

18. Ramu ko bolo Praveen ko call kare aur delivery confirm kare
19. Driver ko bolo 10 baje site par pahunche
20. The driver ko call karo
21. Naukar ko bolo dukaan band kare
22. Chhotu ko bolo ghar jaake khaana le aaye

### Call phrases (making phone calls)

23. Driver ko call karo
24. Rajesh ji ko phone lagao
25. Call Ramu
26. Accountant ji ko call karo abhi
27. Chacha ko phone karo

### Ambiguous or short phrases

28. Rajesh ko 5 baje bolo
29. Yaad dilana aaj
30. Kuch karo

### Off-topic phrases (not commands)

31. Haan theek hai
32. Namaste, kya haal hai

---

## How to record

### Setup

Use your smartphone's voice recorder. Any of these apps work:

- Easy Voice Recorder (Android, free)
- Samsung Voice Recorder (if on Samsung)
- iPhone Voice Memos (if iOS)

Record in MP3 or M4A format if given a choice. WAV is also fine but bigger files.

Hold the phone normally — about 15-20 cm from your mouth, not too close, not too far. Do not use earphones with microphones; use the phone's built-in mic. This matches how the actual shop bot will receive voice.

### Two recording conditions

For each person, for each of the 32 phrases, record twice:

**Clean recording (one session):**

- Location: shop back office, storeroom, home, or any quiet place. No TV, no music, no other conversations nearby.
- Time: whenever is convenient, doesn't matter what time of day.
- The goal is to capture what the voice sounds like when there is almost no background noise. This tells us the best-case accuracy our system can achieve with this person's voice.

**Noisy recording (one session, separate from clean):**

- Location: shop counter during busy hours. Papa's shop between 11am-1pm or 6pm-8pm works well.
- Time: when there are actually customers in the shop, vehicles passing outside, other conversations happening.
- Do not pause when a customer walks in or noise happens. Let the real shop environment be part of the recording.
- The goal is to capture what the voice sounds like in real shop conditions. This tells us what accuracy we should actually expect in deployment.

### Pacing

- Speak each phrase once. Do not repeat for a "better take" unless you completely stumbled.
- Wait 2-3 seconds between phrases so each one is a clearly separated chunk in the recording.
- Small hesitations, normal Hindi speech patterns, code-switching (Hindi and English mixed) — all of this is fine and realistic. Don't try to sound like a newsreader.
- If the speaker doesn't understand what a phrase means, don't explain it in detail. The point is to record the phrase as it would be spoken, not to teach the speaker what the bot does. A short "just read this naturally, like you were telling someone" is enough direction.

### File naming

Use this convention for each recording:

```
speaker-name_condition_YYYY-MM-DD.mp3
```

Examples:
- `papa_clean_2026-04-22.mp3`
- `papa_noisy_2026-04-22.mp3`
- `dadaji_clean_2026-04-23.mp3`
- `dadaji_noisy_2026-04-23.mp3`
- `mukesh_clean_2026-04-24.mp3` (if Mukesh is one of the other speakers)

Each file contains all 32 phrases spoken by one person in one condition. So for each speaker, two files total (one clean, one noisy). For three speakers, six files total.

### How long each session takes

Each session (one speaker, one condition) should be about 15-20 minutes of total recording, including the short pauses between phrases. Plan for 30 minutes to account for setup and re-dos if needed.

---

## Who should record

Ideally three different people:

1. **Papa (chachaji)** — this is the most important one because he is the actual first user of the bot. His voice, his speaking style, his vocabulary.
2. **Dadaji** — adds voice variety. Older voice, possibly different accent or pace.
3. **One other person** — an employee at the shop, a family member, or a friend who speaks Hindi. Preferably male since most shopkeepers are male, but female voice is also useful data if available.

If you can add a fourth or fifth speaker, even better, but three is the minimum.

---

## How to send the files

Once you have all the recordings:

1. Put them on Google Drive in a folder called "ShopSaarthi Recordings Garv"
2. Share the folder with me (I'll send you the email)
3. Message me once shared, so I know to download

Each recording file should be properly named using the convention above. If any file is missing phrases or has a technical issue, redo that one rather than sending a broken file.

---

## Important — consent

Before recording Papa, Dadaji, or any other person, tell them clearly:

- "Ashish chacha ji ke shop ke AI project ke liye aapki awaaz record kar raha hoon."
- "Yeh recording sirf unke hi system mein istemaal hogi, kisi ko nahi de jaayegi."
- "Aap kabhi bhi keh sakte hain ki delete kar do."

Get verbal yes from each person before starting. This is important for the way we are doing the research.

If any person you want to record does not want to, do not record them. Pick someone else.

---

## What I do with the recordings

The recordings go through our system to measure two things:

1. Can the system correctly understand what was said (transcription accuracy)?
2. Can the system correctly figure out what the speaker wants (intent accuracy)?

These measurements tell us where our system is strong and where it needs work before we let shopkeepers use it for real. Your recordings directly shape what we improve.

---

## Questions or problems

Any doubt, any issue, any phrase you don't understand how to say, message me on WhatsApp. Don't guess. Small clarifications upfront save redoing recordings later.

Good luck. Thanks for helping with this.
