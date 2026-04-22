# Phrase alignment — Garv's recordings (2026-04-19)

Matches each segment of the Sarvam transcript against the 32 numbered phrases
in `RECORDING_BRIEF.md`. The speaker did not read phrases in the brief's order;
matches are by content, not position.

Status legend:
- `OK` — phrase captured accurately
- `OK*` — captured but with a meaningful ASR word error (flagged in Note)
- `PARTIAL` — phrase partially captured (word dropped or altered)
- `MISSING` — phrase not found in transcript

---

## File 1 — `WhatsApp Audio 2026-04-19 at 12.08.32 PM.mp4` (~108s)

31 of 32 phrases captured. Phrase 20 indistinguishable from phrase 23 (speaker
may have said it but ASR produced an identical string).

| #  | Expected (Hinglish)                                                  | Sarvam output                                                              | Status  | Note |
|----|----------------------------------------------------------------------|----------------------------------------------------------------------------|---------|------|
| 1  | Rajesh ko WhatsApp karo, bolo kal subah 10 baje aa jaaye             | राजेश को बोलो WhatsApp करो। बोलो कल सुबह 10:00 बजे आएं।                  | OK      | "bolo" inserted twice |
| 2  | Supplier ko SMS bhejo, cement ka rate kya hai confirm karo           | सप्लायर को एसएमएस भेजो सीमेंट का रेट क्या है, कंफर्म करो।                | OK      |      |
| 3  | Sharma sahab ko WhatsApp karo, kal milte hain shop par               | शर्मा साहब को WhatsApp करो, कल मिलने शॉप पर।                              | PARTIAL | "milte hain" → "milne" |
| 4  | Ramu bhaiya ko bolo yaad rakhe, kal delivery aayegi                  | नामू भैया, बोलो याद रखें, कल डिलीवरी आएगी।                                 | OK*     | **Ramu → "नामू" (Naamu)** — name misheard |
| 5  | Send message to Sharma ji that payment will be done next week        | शर्मा जी को मैसेज भेज के पेमेंट अलग अगले हफ्ते। की जाए।                   | PARTIAL | "will be done" garbled to "अलग … की जाए" |
| 6  | 3 baje yaad dilana Rajesh ko call karna hai                          | 3:00 बजे याद दिलाना राजेश को कॉल करने का।                                 | OK      |      |
| 7  | Kal subah reminder lagana bank jaana hai                             | कल सुबह रिमाइंड लगाकर बैंक जाना।                                          | PARTIAL | "reminder" → "रिमाइंड", "hai" dropped |
| 8  | 30 minute baad yaad dilana godown check karna hai                    | 30 मिनट बाद याद दिलाना, गोडाउन चेक करना है।                               | OK      |      |
| 9  | Subah 8:30 baje yaad dilana                                          | सुबह 8:30 बजे याद दिलाना।                                                 | OK      |      |
| 10 | Thodi der mein yaad dilana                                           | थोड़ी देर में याद दिलाना।                                                 | OK      |      |
| 11 | Abhi yaad dilana                                                     | अभी याद दिलाना।                                                          | OK      |      |
| 12 | In 30 minutes remind me                                              | 30 मिनट में मुझे याद दिलाना।                                              | OK      | Sarvam translated English to Hindi |
| 13 | In two hours remind me to call supplier                              | 2 घंटे में मुझे सप्लायर को कॉल करने के लिए याद दिलाना।                   | OK      | Translated to Hindi |
| 14 | Kal shaam yaad dilana                                                | कल शाम याद दिलाना                                                         | OK      |      |
| 15 | Shaam ko yaad dilana godown band karna                               | शाम को याद दिलाना गोडाउन बंद करना है                                      | OK      |      |
| 16 | Raat ko 9 baje yaad dilana                                           | रात को नौ बजे याद दिलाना                                                  | OK      |      |
| 17 | Rajesh ko message bhejo ki kal aana hai aur 5 baje yaad bhi dilana   | राजेश को मैसेज भेजो कि कल आना है और पाँच बजे याद दिलाना                   | OK      | "bhi" dropped |
| 18 | Ramu ko bolo Praveen ko call kare aur delivery confirm kare          | रामू को बोलो परमानेंट को कॉल करे और डिलीवरी कन्फर्म करे।                  | OK*     | **Praveen → "परमानेंट" (Permanent)** — proper-noun miss |
| 19 | Driver ko bolo 10 baje site par pahunche                             | ड्राइवर को बोलो 10:00 बजे साइट पर पहुंचे।                                 | OK      |      |
| 20 | The driver ko call karo                                              | (not distinguishable from #23 — see below)                                | MISSING | Either spoken identically to #23 and deduped, or skipped |
| 21 | Naukar ko bolo dukaan band kare                                      | नौकर को बोलो दुकान बंद करे।                                              | OK      |      |
| 22 | Chhotu ko bolo ghar jaake khaana le aaye                             | छोटू को बोलो घर जाके खाना ले आए।                                         | OK      |      |
| 23 | Driver ko call karo                                                  | ड्राइवर को कॉल करो।                                                      | OK      |      |
| 24 | Rajesh ji ko phone lagao                                             | राजेश जी को फ़ोन लगाओ।                                                   | OK      |      |
| 25 | Call Ramu                                                            | रामू को कॉल करे।                                                         | OK      | Speaker spoke in Hindi instead of English |
| 26 | Accountant ji ko call karo abhi                                      | अकाउंटेंट जी से कॉल करो अभी।                                             | PARTIAL | "ko" → "से" |
| 27 | Chacha ko phone karo                                                 | चाचा को फ़ोन करो।                                                        | OK      |      |
| 28 | Rajesh ko 5 baje bolo                                                | राजेश को 5:00 बजे बोलो।                                                  | OK      |      |
| 29 | Yaad dilana aaj                                                      | याद दिलाना आज                                                            | OK      |      |
| 30 | Kuch karo                                                            | कुछ करो                                                                  | OK      |      |
| 31 | Haan theek hai                                                       | हाँ ठीक है                                                               | OK      |      |
| 32 | Namaste, kya haal hai                                                | नमस्ते क्या हाल है                                                        | OK      |      |

---

## File 2 — `WhatsApp Audio 2026-04-19 at 12.08.33 PM.mp4`

24 of 32 phrases captured. 8 phrases not found in the transcript. This looks
like a shorter / partial second take.

| #  | Expected (Hinglish)                                                  | Sarvam output                                                              | Status  | Note |
|----|----------------------------------------------------------------------|----------------------------------------------------------------------------|---------|------|
| 1  | Rajesh ko WhatsApp karo, bolo kal subah 10 baje aa jaaye             | राजेश को WhatsApp करो, बोलो कल सुबह 10:00 बजे आ जाए।                      | OK      |      |
| 2  | Supplier ko SMS bhejo, cement ka rate kya hai confirm karo           | सप्लायर को एसएमएस भेजो, सीमेंट का रेट क्या है आज?                         | PARTIAL | "confirm karo" → "आज" (misheard) |
| 3  | Sharma sahab ko WhatsApp karo, kal milte hain shop par               | —                                                                          | MISSING |      |
| 4  | Ramu bhaiya ko bolo yaad rakhe, kal delivery aayegi                  | रामू भैया को बोलो, याद रखें कल डिलीवरी आएगी।                              | OK      | Ramu correct this time |
| 5  | Send message to Sharma ji that payment will be done next week        | शर्मा जी को मैसेज भेजो, पेमेंट नेक्स्ट वीक देंगे।                        | OK      | Spoken in Hinglish; cleaner than file 1 |
| 6  | 3 baje yaad dilana Rajesh ko call karna hai                          | तीन बजे याद दिलाना राजेश को कॉल करना है                                    | OK      |      |
| 7  | Kal subah reminder lagana bank jaana hai                             | कल सुबह रिमाइंडर लगाना बैंक जाना है                                        | OK      |      |
| 8  | 30 minute baad yaad dilana godown check karna hai                    | 30 मिनट बाद याद दिलाना, गोडाउन चेक करना है।                               | OK      |      |
| 9  | Subah 8:30 baje yaad dilana                                          | —                                                                          | MISSING |      |
| 10 | Thodi der mein yaad dilana                                           | थोड़ी देर में याद दिलाना                                                  | OK      |      |
| 11 | Abhi yaad dilana                                                     | अभी याद दिलाना                                                            | OK      |      |
| 12 | In 30 minutes remind me                                              | —                                                                          | MISSING |      |
| 13 | In two hours remind me to call supplier                              | इन टू आवर्स रिमाइंड मी टू कॉल द सप्लायर।                                  | OK      | English preserved well (transliterated to Devanagari) |
| 14 | Kal shaam yaad dilana                                                | —                                                                          | MISSING |      |
| 15 | Shaam ko yaad dilana godown band karna                               | शाम को याद दिलाना, गोडाउन बंद करना है।                                    | OK      |      |
| 16 | Raat ko 9 baje yaad dilana                                           | रात को 9:00 बजे याद दिलाना।                                               | OK      |      |
| 17 | Rajesh ko message bhejo ki kal aana hai aur 5 baje yaad bhi dilana   | —                                                                          | MISSING |      |
| 18 | Ramu ko bolo Praveen ko call kare aur delivery confirm kare          | रामू को बोलो प्रवीण को कॉल करके डिलीवरी कन्फर्म करें                      | OK      | Praveen correct this time |
| 19 | Driver ko bolo 10 baje site par pahunche                             | ड्राइवर को बोलो दस बजे साइट पर पहुंचे                                     | OK      |      |
| 20 | The driver ko call karo                                              | —                                                                          | MISSING |      |
| 21 | Naukar ko bolo dukaan band kare                                      | नौकर को बोलो दुकान बंद करे।                                              | OK      |      |
| 22 | Chhotu ko bolo ghar jaake khaana le aaye                             | छोटू को बोलो घर जाके खाना खा खाना ले आए।                                 | OK      | Speaker stutter preserved |
| 23 | Driver ko call karo                                                  | —                                                                          | MISSING |      |
| 24 | Rajesh ji ko phone lagao                                             | राजेश जी को फ़ोन लगाओ।                                                   | OK      |      |
| 25 | Call Ramu                                                            | कॉल रामू।                                                                | OK      | English preserved |
| 26 | Accountant ji ko call karo abhi                                      | अकाउंटेंट को कॉल करो अभी।                                                | OK      | "ji" dropped |
| 27 | Chacha ko phone karo                                                 | —                                                                          | MISSING |      |
| 28 | Rajesh ko 5 baje bolo                                                | राजेश को 5:00 बजे का बोलो।                                                | PARTIAL | Extra "का" inserted |
| 29 | Yaad dilana aaj                                                      | याद दिलाना आज।                                                           | OK      |      |
| 30 | Kuch karo                                                            | कुछ करो।                                                                 | OK      |      |
| 31 | Haan theek hai                                                       | हाँ ठीक है                                                               | OK      |      |
| 32 | Namaste, kya haal hai                                                | नमस्ते क्या हाल है                                                        | OK      |      |

---

## Summary

| Metric                          | File 1 | File 2 |
|---------------------------------|--------|--------|
| Phrases captured                | 31/32  | 24/32  |
| Clean OK                        | 25     | 22     |
| OK with ASR word error (OK*)    | 2      | 0      |
| PARTIAL                         | 4      | 2      |
| MISSING                         | 1      | 8      |

### Notable ASR failures (to test classifier against)
- File 1, phrase 4: **Ramu → Naamu** (नामू). Contact-name miss on a common Hindi name.
- File 1, phrase 18: **Praveen → Permanent** (परमानेंट). Proper-noun miss — serious because the classifier cannot recover this via contact resolution.
- File 2 does **not** reproduce either error — "Ramu" and "Praveen" both decoded correctly. Suggests these are context/pronunciation-dependent misses, not systematic.
- File 1 phrase 5 and file 2 phrase 2 show minor English-word drops ("confirm karo" → "आज", "done" → "अलग … की जाए").

### Behavioural observation
Speaker read groups out of order in both files: messages → calls → reminders → delegate → (short/ambiguous/off-topic), rather than the brief's 1-32 order. Not a problem for evaluation since we match by content, but worth noting when writing the field-test harness.

### Suggested next step
Use file 1 as the primary clean-condition baseline for Papa (31/32 captured) and treat file 2 as a partial/noisy take. Before judging Sarvam accuracy overall, ask Garv to re-record the missing 8 phrases in file 2, or confirm whether this was a deliberate shorter session.
