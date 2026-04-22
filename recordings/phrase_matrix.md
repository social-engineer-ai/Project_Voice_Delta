# Per-phrase capture matrix

For each of the 32 expected phrases from `RECORDING_BRIEF.md`, the table
below shows what each of the 7 Sarvam variants produced in each recording.

Matching is by keyword-span: a cell is populated if all keywords from
at least one set appear within ~180 characters of each other in the
variant's transcript. `—` means no keyword set matched (either the phrase
was not spoken, or the ASR rendering was too different for the keywords).

- **File 1** = `WhatsApp Audio 2026-04-19 at 12.08.32 PM.mp4` (~108s, all 32 phrases spoken)
- **File 2** = `WhatsApp Audio 2026-04-19 at 12.08.33 PM.mp4` (shorter, ~24 phrases spoken)

Phrase 20 ("The driver ko call karo") is intentionally excluded — it
transcribes identically to phrase 23, so keyword matching can't tell
them apart.

---

## Phrase 1: _Rajesh ko WhatsApp karo, bolo kal subah 10 baje aa jaaye_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | राजेश को बोलो WhatsApp करो। बोलो कल सुबह 10:00 बजे आएं। सप्लायर को ए | राजेश को WhatsApp करो, बोलो कल सुबह 10:00 बजे आ जाए। सप्लायर को |
| `saarika_v2.5_unknown` | राजेश को बोलो WhatsApp करो। बोलो कल सुबह 10:00 बजे आएं। सप्लायर को ए | राजेश को WhatsApp करो, बोलो कल सुबह 10:00 बजे आ जाए। सप्लायर को |
| `saaras_v3_transcribe` | राजेश को बोलो व्हाट्सएप करो। बोलो कल सुबह 10 बजे आएं। सप्लायर को एसएम | राजेश को व्हाट्सएप करो, बोलो कल सुबह 10 बजे आ जाए। सप्लायर को एस |
| `saaras_v3_verbatim` | राजेश को बोलो व्हाट्सएप करो बोलो कल सुबह दस बजे आए सप्लायर को एस एम | राजेश को व्हाट्सएप करो बोलो कल सुबह दस बजे आ जाए सप्लायर को एस |
| `saaras_v3_translit` | Rajesh ko bolo WhatsApp karo. Bolo kal subah 10:00 baje aaye. Supplier k | Rajesh ko WhatsApp karo bolo kal subah 10:00 baje aa jaaye. Suppli |
| `saaras_v3_codemix` | राजेश को बोलो WhatsApp करो। बोलो कल सुबह 10:00 बजे आए। सप्लायर को SM | राजेश को WhatsApp करो बोलो कल सुबह 10:00 बजे आ जाए। सप्लायर को |
| `saaras_v3_translate` | Tell Rajesh to WhatsApp. Tell him to come tomorrow morning at 10:00 AM. Send an SMS to the s | sApp Rajesh and tell him to come tomorrow morning at 10:00 AM. Send an SMS to the supp |

## Phrase 2: _Supplier ko SMS bhejo, cement ka rate kya hai confirm karo_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | आएं। सप्लायर को एसएमएस भेजो सीमेंट का रेट क्या है, कंफर्म करो। शर् | जाए। सप्लायर को एसएमएस भेजो, सीमेंट का रेट क्या है आज? शर्मा जी को |
| `saarika_v2.5_unknown` | आएं। सप्लायर को एसएमएस भेजो सीमेंट का रेट क्या है, कंफर्म करो। शर् | जाए। सप्लायर को एसएमएस भेजो, सीमेंट का रेट क्या है आज? शर्मा जी को |
| `saaras_v3_transcribe` | आएं। सप्लायर को एसएमएस भेजो सीमेंट का रेट क्या है कंफर्म करो। शर्म | जाए। सप्लायर को एसएमएस भेजो, सीमेंट का रेट क्या है आज? शर्मा जी को |
| `saaras_v3_verbatim` | े आए सप्लायर को एस एम एस भेजो सीमेंट का रेट क्या है कंफर्म करो शर्मा | जाए सप्लायर को एस एम एस भेजो सीमेंट का रेट क्या है आज शर्मा जी को म |
| `saaras_v3_translit` | aye. Supplier ko SMS bhejo cement ka rate kya hai confirm | aye. Supplier ko SMS bhejo, cement ka rate kya hai aaj? Sha |
| `saaras_v3_codemix` | आए। सप्लायर को SMS भेजो सीमेंट का रेट क्या है कंफर्म करो। शर्म | जाए। सप्लायर को SMS भेजो, सीमेंट का रेट क्या है आज? शर्मा जी को |
| `saaras_v3_translate` | the supplier, confirm what the rate of cement is. WhatsApp Sharma Saha | the supplier, what is the rate of cement today? Send a message to |

## Phrase 3: _Sharma sahab ko WhatsApp karo, kal milte hain shop par_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | करो। शर्मा साहब को WhatsApp करो, कल मिलने शॉप पर। नामू भैया, बोलो | — |
| `saarika_v2.5_unknown` | करो। शर्मा साहब को WhatsApp करो, कल मिलने शॉप पर। नामू भैया, बोलो | — |
| `saaras_v3_transcribe` | करो। शर्मा साहब को व्हाट्सएप करो कल मिलने शॉप पर। रामू भैया, बोलो | — |
| `saaras_v3_verbatim` | करो शर्मा साहब को व्हाट्सएप करो कल मिलने शॉप पर रामू भैया बोलो या | — |
| `saaras_v3_translit` | aro. Sharma sahab ko WhatsApp karo kal milne shop par. Ramu bhaiya, bolo y | — |
| `saaras_v3_codemix` | करो। शर्मा साहब को WhatsApp करो कल मिलने शॉप पर। रामू भैया, बोलो | — |
| `saaras_v3_translate` | sApp Sharma Sahab to meet at the shop tomorrow. Ramu Bhaiya, r | — |

## Phrase 4: _Ramu bhaiya ko bolo yaad rakhe, kal delivery aayegi_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | नामू भैया, बोलो याद रखें, कल डिलीवरी आएगी। शर्मा जी को मैसेज | ामू भैया को बोलो, याद रखें कल डिलीवरी आएगी। राजेश को 5:00 बजे क |
| `saarika_v2.5_unknown` | नामू भैया, बोलो याद रखें, कल डिलीवरी आएगी। शर्मा जी को मैसेज | ामू भैया को बोलो, याद रखें कल डिलीवरी आएगी। राजेश को 5:00 बजे क |
| `saaras_v3_transcribe` | रामू भैया, बोलो याद रखें कल डिलीवरी आएगी। शर्मा जी को मैसेज | रामू भैया को बोलो याद रखें कल डिलीवरी आएगी, राजेश को 5 बजे का |
| `saaras_v3_verbatim` | रामू भैया बोलो याद रखें कल डिलीवरी आएगी शर्मा जी को मैसेज भ | रामू भैया को बोलो याद रखें कल डिलीवरी आएगी राजेश को पाँच बजे क |
| `saaras_v3_translit` | Ramu bhaiya, bolo yaad rakhen, kal delivery aayegi. Sharma ji ko mes | Ramu bhaiya ko bolo, yaad rakhen kal delivery aayegi. Rajesh ko 5:00 b |
| `saaras_v3_codemix` | रामू भैया, बोलो याद रखें, कल डिलीवरी आएगी। शर्मा जी को मैसेज | रामू भैया को बोलो याद रखें कल delivery आएगी राजेश को 5 बजे का बोलो य |
| `saaras_v3_translate` | Ramu Bhaiya, remember, the delivery will come tomorrow. Send | Ramu Bhaiya to remember, the delivery will come tomorrow. Tell |

## Phrase 5: _Send message to Sharma ji that payment will be done next week_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | एगी। शर्मा जी को मैसेज भेज के पेमेंट अलग अगले हफ्ते। की जाए। ड्राइवर को कॉल | आज? शर्मा जी को मैसेज भेजो, पेमेंट नेक्स्ट वीक देंगे। राजेश जी को फ़ोन ल |
| `saarika_v2.5_unknown` | एगी। शर्मा जी को मैसेज भेज के पेमेंट अलग अगले हफ्ते। की जाए। ड्राइवर को कॉल | आज? शर्मा जी को मैसेज भेजो, पेमेंट नेक्स्ट वीक देंगे। राजेश जी को फ़ोन ल |
| `saaras_v3_transcribe` | एगी। शर्मा जी को मैसेज भेज के पेमेंट अलग अगले हफ्ते। की जाए। ड्राइवर को कॉल | आज? शर्मा जी को मैसेज भेजो, पेमेंट नेक्स्ट वीक देंगे। राजेश जी को फ़ोन |
| `saaras_v3_verbatim` | आएगी शर्मा जी को मैसेज भेज के पेमेंट अलग अगले हफ्ते की जाए ड्राइवर को कॉल कर | ै आज शर्मा जी को मैसेज भेजो पेमेंट नेक्स्ट वीक देंगे राजेश जी को फ़ोन ल |
| `saaras_v3_translit` | egi. Sharma ji ko message bhej ke payment alag agle hafte. Ki jaaye. Driver ko cal | aaj? Sharma ji ko message bhejo, payment next week denge. Rajesh ji ko phon |
| `saaras_v3_codemix` | एगी। शर्मा जी को मैसेज भेज कि पेमेंट अलग अगले हफ्ते। की जाए। ड्राइवर को कॉल | आज? शर्मा जी को मैसेज भेजो, पेमेंट next week देंगे। राजेश जी को |
| `saaras_v3_translate` | e to Sharma Ji that the payment will be separate next week. It should be | e to Sharma Ji, we will give the payment next week. Call Rajesh ji. Call th |

## Phrase 6: _3 baje yaad dilana Rajesh ko call karna hai_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | ो। 3:00 बजे याद दिलाना राजेश को कॉल करने का। कल सुबह रि | मू। तीन बजे याद दिलाना राजेश को कॉल करना है कल सुबह रि |
| `saarika_v2.5_unknown` | ो। 3:00 बजे याद दिलाना राजेश को कॉल करने का। कल सुबह रि | मू। तीन बजे याद दिलाना राजेश को कॉल करना है कल सुबह रि |
| `saaras_v3_transcribe` | रो। 3 बजे याद दिलाना राजेश को कॉल करने का। कल सुबह र | ामू। 3 बजे याद दिलाना राजेश को कॉल करना है, कल सुबह |
| `saaras_v3_verbatim` | करो तीन बजे याद दिलाना राजेश को फ़ोन करने का कल सुबह | रामू तीन बजे याद दिलाना राजेश को कॉल करना है कल सुबह र |
| `saaras_v3_translit` | aro. 3:00 baje yaad dilana Rajesh ko call karne ka. Kal subah remi | amu. 3:00 baje yaad dilana Rajesh ko call karna hai. Kal subah rem |
| `saaras_v3_codemix` | करो। 3 बजे याद दिलाना राजेश को कॉल करने का। कल सुबह | रामू 3 बजे याद दिलाना राजेश को call करना है कल सुबह |
| `saaras_v3_translate` | mind Rajesh to call at 3:00. Set a reminder to go to | mind Rajesh at 3 o'clock to call. Set a reminder |

## Phrase 7: _Kal subah reminder lagana bank jaana hai_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | बह रिमाइंड लगाकर बैंक जाना। 30 मिनट बाद याद दिला | ुबह रिमाइंडर लगाना बैंक जाना है 30 मिनट बाद याद द |
| `saarika_v2.5_unknown` | बह रिमाइंड लगाकर बैंक जाना। 30 मिनट बाद याद दिला | ुबह रिमाइंडर लगाना बैंक जाना है 30 मिनट बाद याद द |
| `saaras_v3_transcribe` | ुबह रिमाइंडर लगाकर बैंक जाना। 30 मिनट बाद याद दिल | सुबह रिमाइंडर लगाना बैंक जाना है। 30 मिनट बाद याद |
| `saaras_v3_verbatim` | सुबह रिमाइंडर लगाकर बैंक जाना बीस मिनट बाद याद दि | सुबह रिमाइंडर लगाना बैंक जाना है तीस मिनट बाद याद |
| `saaras_v3_translit` | ubah remind lagaakar bank jaana. 20 minute baad ya | ubah reminder lagana bank jaana hai. 30 minute baa |
| `saaras_v3_codemix` | सुबह रिमाइंडर लगाकर बैंक जाना। 30 मिनट बाद याद दि | सुबह reminder लगाना bank जाना है 30 मिनट बाद याद |
| `saaras_v3_translate` | et a reminder to go to the bank tomorrow morning. Remind | the bank. Remind me after 30 minutes to c |

## Phrase 8: _30 minute baad yaad dilana godown check karna hai_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | ा, गोडाउन चेक करना है। सुबह 8:30 बजे याद | ना, गोडाउन चेक करना है। शाम को याद दिलान |
| `saarika_v2.5_unknown` | ा, गोडाउन चेक करना है। सुबह 8:30 बजे याद | ना, गोडाउन चेक करना है। शाम को याद दिलान |
| `saaras_v3_transcribe` | ना, गोडाउन चेक करना है। सुबह 8:30 बजे या | लाना गोडाउन चेक करना है। शाम को याद दिला |
| `saaras_v3_verbatim` | लाना गोडाउन चेक करना है सुबह साढ़े आठ बज | लाना गोडाउन चेक करना है शाम को याद दिलान |
| `saaras_v3_translit` | ana, godown check karna hai. Subah 8:30 ba | lana godown check karna hai. Shaam ko yaad |
| `saaras_v3_codemix` | ाना, गोडाउन चेक करना है। सुबह 8:30 बजे य | लाना गोडाउन चेक करना है। शाम को याद दिला |
| `saaras_v3_translate` | d to check the godown. Remind me at 8:30 AM. R | s to check the warehouse. Remind me in the evenin |

## Phrase 9: _Subah 8:30 baje yaad dilana_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | ै। सुबह 8:30 बजे याद दिलाना। थोड़ी देर म | — |
| `saarika_v2.5_unknown` | ै। सुबह 8:30 बजे याद दिलाना। थोड़ी देर म | — |
| `saaras_v3_transcribe` | है। सुबह 8:30 बजे याद दिलाना। थोड़ी देर | — |
| `saaras_v3_verbatim` | सुबह साढ़े आठ बजे याद दिलाना थोड़ी देर | — |
| `saaras_v3_translit` | hai. Subah 8:30 baje yaad dilana. Thodi | — |
| `saaras_v3_codemix` | है। सुबह 8:30 बजे याद दिलाना। थोड़ी दे | — |
| `saaras_v3_translate` | e at 8:30 AM. Remind me in a little w | — |

## Phrase 10: _Thodi der mein yaad dilana_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | ा। थोड़ी देर में याद दिलाना। अभी याद दिल | ाना थोड़ी देर में याद दिलाना हाँ ठीक है |
| `saarika_v2.5_unknown` | ा। थोड़ी देर में याद दिलाना। अभी याद दिल | ाना थोड़ी देर में याद दिलाना हाँ ठीक है |
| `saaras_v3_transcribe` | ना। थोड़ी देर में याद दिलाना। अभी याद द | ाना, थोड़ी देर में याद दिलाना। हाँ, ठीक |
| `saaras_v3_verbatim` | लाना थोड़ी देर में याद दिलाना अभी याद द | लाना थोड़ी देर में याद दिलाना हाँ ठीक ह |
| `saaras_v3_translit` | ana. Thodi der mein yaad dilana. Abhi y | lana thodi der mein yaad dilana Haan th |
| `saaras_v3_codemix` | ाना। थोड़ी देर में याद दिलाना। अभी याद | लाना थोड़ी देर में याद दिलाना हाँ ठीक ह |
| `saaras_v3_translate` | in a little while. Remind me now. Remind m | in a little while. Yes, okay. Hello, how a |

## Phrase 11: _Abhi yaad dilana_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | । अभी याद दिलाना। 30 मिनट में मुझे याद दिलान | रो। अभी याद दिलाना थोड़ी देर में याद दिलाना |
| `saarika_v2.5_unknown` | । अभी याद दिलाना। 30 मिनट में मुझे याद दिलान | रो। अभी याद दिलाना थोड़ी देर में याद दिलाना |
| `saaras_v3_transcribe` | ना। अभी याद दिलाना। 30 मिनट में मुझे याद दिल | करो। अभी याद दिलाना, थोड़ी देर में याद दिलान |
| `saaras_v3_verbatim` | में याद दिलाना अभी याद दिलाना तीस मिनट में | करो अभी याद दिलाना थोड़ी देर में याद दिलाना |
| `saaras_v3_translit` | ana. Abhi yaad dilana. 30 minute mein mujhe ya | aro. Abhi yaad dilana thodi der mein yaad dila |
| `saaras_v3_codemix` | ाना। अभी याद दिलाना। 30 मिनट में मुझे याद दि | करो अभी याद दिलाना थोड़ी देर में याद दिलाना |
| `saaras_v3_translate` | ile. Remind me now. Remind me in 30 minutes | ing. Remind me now, remind me in a little w |

## Phrase 12: _In 30 minutes remind me_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | । 30 मिनट में मुझे याद दिलाना। 2 घंटे में मुझे | — |
| `saarika_v2.5_unknown` | । 30 मिनट में मुझे याद दिलाना। 2 घंटे में मुझे | — |
| `saaras_v3_transcribe` | ना। 30 मिनट में मुझे याद दिलाना। 2 घंटे में मु | — |
| `saaras_v3_verbatim` | लाना तीस मिनट में मुझे याद दिलाना दो घंटे में म | — |
| `saaras_v3_translit` | ana. 30 minute mein mujhe yaad dilana. 2 ghante me | — |
| `saaras_v3_codemix` | ाना। 30 मिनट में मुझे याद दिलाना। 2 घंटे में म | — |
| `saaras_v3_translate` | d me in 30 minutes. Remind me to call the s | — |

## Phrase 13: _In two hours remind me to call supplier_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | । 2 घंटे में मुझे सप्लायर को कॉल करने के लिए याद दिला | इन टू आवर्स रिमाइंड मी टू कॉल द सप्लायर। रात को 9:00 बजे याद दिला |
| `saarika_v2.5_unknown` | । 2 घंटे में मुझे सप्लायर को कॉल करने के लिए याद दिला | इन टू आवर्स रिमाइंड मी टू कॉल द सप्लायर। रात को 9:00 बजे याद दिला |
| `saaras_v3_transcribe` | ना। 2 घंटे में मुझे सप्लायर को कॉल करने के लिए याद दि | । इन टू आवर्स रिमाइंड मी टू कॉल द सप्लायर। रात को 9:00 बजे याद दिल |
| `saaras_v3_verbatim` | लाना दो घंटे में मुझे सप्लायर को कॉल करने के लिए याद द | ै इन टू आवर्स रिमाइंड मी टू कॉल द सप्लायर, रात को नौ बजे याद दिलान |
| `saaras_v3_translit` | ana. 2 ghante mein mujhe supplier ko call karne ke liye ya | . In two hours remind me to call the supplier. Raat ko 9:00 baje yaad |
| `saaras_v3_codemix` | ाना। 2 घंटे में मुझे सप्लायर को कॉल करने के लिए याद द | । इन 2 hours remind me to call the supplier. रात को 9:00 बजे याद दिल |
| `saaras_v3_translate` | the supplier in 2 hours. Remind me tomorrow even | . In 2 hours, remind me to call the supplier. Remind me at 9:00 PM. T |

## Phrase 14: _Kal shaam yaad dilana_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | । कल शाम याद दिलाना शाम को याद दिलाना गो | — |
| `saarika_v2.5_unknown` | । कल शाम याद दिलाना शाम को याद दिलाना गो | — |
| `saaras_v3_transcribe` | ना। कल शाम याद दिलाना। शाम को याद दिलाना | — |
| `saaras_v3_verbatim` | लाना कल शाम याद दिलाना शाम को याद दिलाना | — |
| `saaras_v3_translit` | ana. Kal shaam yaad dilana. Shaam ko yaad di | — |
| `saaras_v3_codemix` | ाना। कल शाम याद दिलाना। शाम को याद दिलान | — |
| `saaras_v3_translate` | d me tomorrow evening. Remind me in the evening to clo | — |

## Phrase 15: _Shaam ko yaad dilana godown band karna_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | ा शाम को याद दिलाना गोडाउन बंद करना है रात को नौ बजे याद द | है। शाम को याद दिलाना, गोडाउन बंद करना है। इन टू आवर्स रिमा |
| `saarika_v2.5_unknown` | ा शाम को याद दिलाना गोडाउन बंद करना है रात को नौ बजे याद द | है। शाम को याद दिलाना, गोडाउन बंद करना है। इन टू आवर्स रिमा |
| `saaras_v3_transcribe` | ना। शाम को याद दिलाना गोडाउन बंद करना है। रात को 9:00 बजे | है। शाम को याद दिलाना गोडाउन बंद करना है। इन टू आवर्स रिम |
| `saaras_v3_verbatim` | लाना शाम को याद दिलाना गोडाउन बंद करना है रात को नौ बजे या | ा है शाम को याद दिलाना गोडाउन बंद करना है इन टू आवर्स रिमा |
| `saaras_v3_translit` | ana. Shaam ko yaad dilana godown band karna hai. Raat ko 9:00 | hai. Shaam ko yaad dilana godown band karna hai. In two hours |
| `saaras_v3_codemix` | ाना। शाम को याद दिलाना गोडाउन बंद करना है। रात को 9:00 बजे | है। शाम को याद दिलाना गोडाउन बंद करना है। इन 2 hours remi |
| `saaras_v3_translate` | the evening to close the godown. Remind me at 9:00 PM. S | the evening to close the warehouse. In 2 hours, remind me t |

## Phrase 16: _Raat ko 9 baje yaad dilana_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | ै रात को नौ बजे याद दिलाना राजेश को मैसेज भेजो | यर। रात को 9:00 बजे याद दिलाना। रामू को बोलो प्रव |
| `saarika_v2.5_unknown` | ै रात को नौ बजे याद दिलाना राजेश को मैसेज भेजो | यर। रात को 9:00 बजे याद दिलाना। रामू को बोलो प्रव |
| `saaras_v3_transcribe` | है। रात को 9:00 बजे याद दिलाना। राजेश को मैसेज भे | ायर। रात को 9:00 बजे याद दिलाना। रामू को बोलो प्र |
| `saaras_v3_verbatim` | ा है रात को नौ बजे याद दिलाना राजेश को मैसेज भे | ायर, रात को नौ बजे याद दिलाना रामू को बोलो प्रव |
| `saaras_v3_translit` | hai. Raat ko 9:00 baje yaad dilana. Rajesh ko messag | ier. Raat ko 9:00 baje yaad dilana. Ramu ko bolo Pra |
| `saaras_v3_codemix` | है। रात को 9:00 बजे याद दिलाना। राजेश को मैसेज भ | ier. रात को 9:00 बजे याद दिलाना। रामू को बोलो प्र |
| `saaras_v3_translate` | own. Remind me at 9:00 PM. Send a message to Rajes | ier. Remind me at 9:00 PM. Tell Ramu to call Prave |

## Phrase 17: _Rajesh ko message bhejo ki kal aana hai aur 5 baje yaad bhi dilana_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | े याद दिलाना राजेश को मैसेज भेजो कि कल आना है और पाँच बजे याद दिलाना रामू | — |
| `saarika_v2.5_unknown` | े याद दिलाना राजेश को मैसेज भेजो कि कल आना है और पाँच बजे याद दिलाना रामू | — |
| `saaras_v3_transcribe` | बजे याद दिलाना। राजेश को मैसेज भेजो कि कल आना है और 5:00 बजे याद दिलाना। र | — |
| `saaras_v3_verbatim` | बजे याद दिलाना राजेश को मैसेज भेजो कि कल आना है और पाँच बजे याद दिलाना र | — |
| `saaras_v3_translit` | 9:00 baje yaad dilana. Rajesh ko message bhejo ki kal aana hai aur 5:00 baje yaad d | — |
| `saaras_v3_codemix` | बजे याद दिलाना। राजेश को मैसेज भेजो कि कल आना है और 5:00 बजे याद दिलाना। | — |
| `saaras_v3_translate` | e to Rajesh that he has to come tomorrow and remind me at 5:00 PM. Tell Ramu to call Pa | — |

## Phrase 18: _Ramu ko bolo Praveen ko call kare aur delivery confirm kare_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | ा रामू को बोलो परमानेंट को कॉल करे और डिलीवरी कन्फर्म करे। ड्राइवर को बोल | ना। रामू को बोलो प्रवीण को कॉल करके डिलीवरी कन्फर्म करें ड्राइवर को ब |
| `saarika_v2.5_unknown` | ा रामू को बोलो परमानेंट को कॉल करे और डिलीवरी कन्फर्म करे। ड्राइवर को बोल | ना। रामू को बोलो प्रवीण को कॉल करके डिलीवरी कन्फर्म करें ड्राइवर को ब |
| `saaras_v3_transcribe` | ना। रामू को बोलो परमिट को कॉल करें और डिलीवरी कंफर्म करें। ड्राइवर को ब | ाना। रामू को बोलो प्रवीण को कॉल करके डिलीवरी कन्फर्म करें। ड्राइवर को |
| `saaras_v3_verbatim` | लाना रामू को बोलो परमिण को कॉल करें और डिलीवरी कंफर्म करें ड्राइवर को ब | लाना रामू को बोलो प्रवीण को कॉल करके डिलीवरी कन्फर्म करें ड्राइवर को |
| `saaras_v3_translit` | ana. Ramu ko bolo permanent ko call kare aur delivery confirm kare. Driver ko | ana. Ramu ko bolo Praveen ko call karke delivery confirm kare. Driver ko |
| `saaras_v3_codemix` | ाना। रामू को बोलो परमण को कॉल करे और डिलीवरी कंफर्म करे। ड्राइवर को ब | ाना। रामू को बोलो प्रवीण को call करके delivery confirm करे। driver को ब |
| `saaras_v3_translate` | Tell Ramu to call Parman and confirm the delivery. Tell the driver to reac | Tell Ramu to call Praveen and confirm the delivery. Tell the driver to reac |

## Phrase 19: _Driver ko bolo 10 baje site par pahunche_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | । ड्राइवर को बोलो 10:00 बजे साइट पर पहुंचे। नौकर को बोलो दुक | रें ड्राइवर को बोलो दस बजे साइट पर पहुंचे नौकर को बोलो दु |
| `saarika_v2.5_unknown` | । ड्राइवर को बोलो 10:00 बजे साइट पर पहुंचे। नौकर को बोलो दुक | रें ड्राइवर को बोलो दस बजे साइट पर पहुंचे नौकर को बोलो दु |
| `saaras_v3_transcribe` | ें। ड्राइवर को बोलो 10 बजे साइट पर पहुंचे। नौकर को बोलो द | रें। ड्राइवर को बोलो 10 बजे साइट पर पहुंचे। नौकर को बोलो |
| `saaras_v3_verbatim` | करें ड्राइवर को बोलो दस बजे साइट पर पहुंचे नौकर को बोलो द | करें ड्राइवर को बोलो दस बजे साइट पर पहुंचे नौकर को बोलो द |
| `saaras_v3_translit` | are. Driver ko bolo 10:00 baje site par pahunche. Naukar ko | are. Driver ko bolo 10:00 baje site par pahunche. Naukar ko |
| `saaras_v3_codemix` | करे। ड्राइवर को बोलो 10:00 बजे साइट पर पहुंचे। नौकर को बोलो | करे। driver को बोलो 10:00 बजे site पर पहुंचे। नौकर को बोलो |
| `saaras_v3_translate` | the driver to reach the site by 10:00 AM. Tell the se | the driver to reach the site by 10:00 AM. Tell the se |

## Phrase 20: _The driver ko call karo_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | — | — |
| `saarika_v2.5_unknown` | — | — |
| `saaras_v3_transcribe` | — | — |
| `saaras_v3_verbatim` | — | — |
| `saaras_v3_translit` | — | — |
| `saaras_v3_codemix` | — | — |
| `saaras_v3_translate` | — | — |

## Phrase 21: _Naukar ko bolo dukaan band kare_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | । नौकर को बोलो दुकान बंद करे। छोटू को बोलो घर जा | ंचे नौकर को बोलो दुकान बंद करे। छोटू को बोलो घर |
| `saarika_v2.5_unknown` | । नौकर को बोलो दुकान बंद करे। छोटू को बोलो घर जा | ंचे नौकर को बोलो दुकान बंद करे। छोटू को बोलो घर |
| `saaras_v3_transcribe` | चे। नौकर को बोलो दुकान बंद करें। छोटू को बोलो घर | ंचे। नौकर को बोलो दुकान बंद करें। छोटू को बोलो घ |
| `saaras_v3_verbatim` | ुंचे नौकर को बोलो दुकान बंद करें छोटू को बोलो घर | ुंचे नौकर को बोलो दुकान बंद करें छोटू को बोलो घर |
| `saaras_v3_translit` | che. Naukar ko bolo dukaan band kare. Chhotu ko bol | che. Naukar ko bolo dukaan band kare. Chhotu ko bol |
| `saaras_v3_codemix` | ंचे। नौकर को बोलो दुकान बंद करे। छोटू को बोलो घर | ंचे। नौकर को बोलो दुकान बंद करे। छोटू को बोलो घर |
| `saaras_v3_translate` | the servant to close the shop. Tell Chhotu to | the servant to close the shop. Tell Chhotu to |

## Phrase 22: _Chhotu ko bolo ghar jaake khaana le aaye_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | । छोटू को बोलो घर जाके खाना ले आए। राजेश को 5:00 बजे बो | रे। छोटू को बोलो घर जाके खाना खा खाना ले आए। रामू भैया |
| `saarika_v2.5_unknown` | । छोटू को बोलो घर जाके खाना ले आए। राजेश को 5:00 बजे बो | रे। छोटू को बोलो घर जाके खाना खा खाना ले आए। रामू भैया |
| `saaras_v3_transcribe` | ें। छोटू को बोलो घर जाके खाना ले आएं। राजेश को 5 बजे बो | रें। छोटू को बोलो घर जाके खाना ले आएं। रामू भैया को बोल |
| `saaras_v3_verbatim` | करें छोटू को बोलो घर जाके खाना ले आए राजेश को पाँच बजे | करें छोटू को बोलो घर जाके खाना खा खाना ले आए रामू भैया |
| `saaras_v3_translit` | are. Chhotu ko bolo ghar ja ke khana le aaye. Rajesh ko 5:00 | are. Chhotu ko bolo ghar ja ke khana khana le aaye. Ramu bhai |
| `saaras_v3_codemix` | करे। छोटू को बोलो घर जाके खाना ले आए। राजेश को 5:00 बजे | करे। छोटू को बोलो घर जाके खाना खा खाना ले आए। रामू भैया |
| `saaras_v3_translate` | Tell Chhotu to go home and bring food. Tell Rajesh to come by | Tell Chhotu to go home and bring food. Tell Ramu Bhaiya to rem |

## Phrase 23: _Driver ko call karo_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | जाए। ड्राइवर को कॉल करो। राजेश जी को फ़ोन लगाओ। र | — |
| `saarika_v2.5_unknown` | जाए। ड्राइवर को कॉल करो। राजेश जी को फ़ोन लगाओ। र | — |
| `saaras_v3_transcribe` | जाए। ड्राइवर को कॉल करो। राजेश जी को फोन लगाओ। र | — |
| `saaras_v3_verbatim` | जाए ड्राइवर को कॉल करो राजेश जी को फोन लगाओ राम | — |
| `saaras_v3_translit` | aye. Driver ko call karo. Rajesh ji ko phone laga | — |
| `saaras_v3_codemix` | जाए। ड्राइवर को कॉल करो। राजेश जी को फोन लगाओ। र | — |
| `saaras_v3_translate` | one. Call the driver. Call Rajesh Ji. Call Ra | — |

## Phrase 24: _Rajesh ji ko phone lagao_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | करो। राजेश जी को फ़ोन लगाओ। रामू को कॉल करे। अकाउंटे | ंगे। राजेश जी को फ़ोन लगाओ। अकाउंटेंट को कॉल करो अभी |
| `saarika_v2.5_unknown` | करो। राजेश जी को फ़ोन लगाओ। रामू को कॉल करे। अकाउंटे | ंगे। राजेश जी को फ़ोन लगाओ। अकाउंटेंट को कॉल करो अभी |
| `saaras_v3_transcribe` | करो। राजेश जी को फोन लगाओ। रामू को कॉल करें। अकाउं | ंगे। राजेश जी को फ़ोन लगाओ, अकाउंटेंट को कॉल करो अभ |
| `saaras_v3_verbatim` | करो राजेश जी को फोन लगाओ रामू को कॉल करें अकाउंटे | ेंगे राजेश जी को फ़ोन लगाओ अकाउंटेंट को कॉल करो अभी |
| `saaras_v3_translit` | aro. Rajesh ji ko phone lagao. Ramu ko call kare. Acco | nge. Rajesh ji ko phone lagao. Accountant ko call karo |
| `saaras_v3_codemix` | करो। राजेश जी को फोन लगाओ। रामू को कॉल करें। अकाउं | ंगे। राजेश जी को phone लगाओ accountant को call करो अ |
| `saaras_v3_translate` | ver. Call Rajesh Ji. Call Ramu. Call the | eek. Call Rajesh ji. Call the accountant |

## Phrase 25: _Call Ramu_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | ाओ। रामू को कॉल करे। अकाउंटेंट जी से कॉल | भी। कॉल रामू। तीन बजे याद दिलाना राजेश |
| `saarika_v2.5_unknown` | ाओ। रामू को कॉल करे। अकाउंटेंट जी से कॉल | भी। कॉल रामू। तीन बजे याद दिलाना राजेश |
| `saaras_v3_transcribe` | गाओ। रामू को कॉल करें। अकाउंटेंट जी से कॉ | अभी, कॉल रामू। 3 बजे याद दिलाना राजेश |
| `saaras_v3_verbatim` | लगाओ रामू को कॉल करें अकाउंटेंट जी से कॉल | अभी कॉल रामू तीन बजे याद दिलाना राजेश |
| `saaras_v3_translit` | gao. Ramu ko call kare. Accountant ji se c | bhi. Call Ramu. 3:00 baje yaad dilana R |
| `saaras_v3_codemix` | गाओ। रामू को कॉल करें। अकाउंटेंट जी से कॉ | अभी call रामू 3 बजे याद दिलाना राजेश क |
| `saaras_v3_translate` | Ji. Call Ramu. Call the accountant now | now. Call Ramu. Remind Rajesh at 3 o'cl |

## Phrase 26: _Accountant ji ko call karo abhi_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | रे। अकाउंटेंट जी से कॉल करो अभी। चाचा को फ़ोन करो। 3:00 बज | ाओ। अकाउंटेंट को कॉल करो अभी। कॉल रामू। तीन बजे याद दि |
| `saarika_v2.5_unknown` | रे। अकाउंटेंट जी से कॉल करो अभी। चाचा को फ़ोन करो। 3:00 बज | ाओ। अकाउंटेंट को कॉल करो अभी। कॉल रामू। तीन बजे याद दि |
| `saaras_v3_transcribe` | रें। अकाउंटेंट जी से कॉल करो अभी। चाचा को फ़ोन करो। 3 बजे | गाओ, अकाउंटेंट को कॉल करो अभी, कॉल रामू। 3 बजे याद दिल |
| `saaras_v3_verbatim` | करें अकाउंटेंट जी से कॉल करो अभी चाचा को फ़ोन करो तीन बजे | लगाओ अकाउंटेंट को कॉल करो अभी कॉल रामू तीन बजे याद दिल |
| `saaras_v3_translit` | are. Accountant ji se call karo abhi. Chacha ko phone karo. 3 | gao. Accountant ko call karo abhi. Call Ramu. 3:00 baje ya |
| `saaras_v3_codemix` | रें। अकाउंटेंट जी से कॉल करो अभी। चाचा को फ़ोन करो। 3 बजे | लगाओ accountant को call करो अभी call रामू 3 बजे याद दिला |
| `saaras_v3_translate` | the accountant now. Call uncle. Remind Raje | the accountant now. Call Ramu. Remind Rajes |

## Phrase 27: _Chacha ko phone karo_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | भी। चाचा को फ़ोन करो। 3:00 बजे याद दिलाना र | — |
| `saarika_v2.5_unknown` | भी। चाचा को फ़ोन करो। 3:00 बजे याद दिलाना र | — |
| `saaras_v3_transcribe` | अभी। चाचा को फ़ोन करो। 3 बजे याद दिलाना राज | — |
| `saaras_v3_verbatim` | अभी चाचा को फ़ोन करो तीन बजे याद दिलाना र | — |
| `saaras_v3_translit` | bhi. Chacha ko phone karo. 3:00 baje yaad dil | — |
| `saaras_v3_codemix` | अभी। चाचा को फ़ोन करो। 3 बजे याद दिलाना रा | — |
| `saaras_v3_translate` | now. Call uncle. Remind Rajesh to call a | — |

## Phrase 28: _Rajesh ko 5 baje bolo_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | । राजेश को 5:00 बजे बोलो। याद दिलाना आज कुछ करो हाँ | गी। राजेश को 5:00 बजे का बोलो। याद दिलाना आज। कुछ करो। |
| `saarika_v2.5_unknown` | । राजेश को 5:00 बजे बोलो। याद दिलाना आज कुछ करो हाँ | गी। राजेश को 5:00 बजे का बोलो। याद दिलाना आज। कुछ करो। |
| `saaras_v3_transcribe` | एं। राजेश को 5 बजे बोलो। याद दिलाना आज, कुछ करो। | एगी, राजेश को 5 बजे का बोलो याद दिलाना आज कुछ करो। अ |
| `saaras_v3_verbatim` | े आए राजेश को पाँच बजे बोलो याद दिलाना आज। कुछ करो। | आएगी राजेश को पाँच बजे का बोलो याद दिलाना आज कुछ करो अभ |
| `saaras_v3_translit` | aye. Rajesh ko 5:00 baje bolo. Yaad dilana aaj. Kuch k | egi. Rajesh ko 5:00 baje ka bolo. Yaad dilana aaj. Kuch k |
| `saaras_v3_codemix` | आए। राजेश को 5:00 बजे बोलो। याद दिलाना आज। कुछ करो। | आएगी राजेश को 5 बजे का बोलो याद दिलाना आज कुछ करो अभ |
| `saaras_v3_translate` | Tell Rajesh to come by 5:00 PM. Remind me today. | row. Tell Rajesh to remember to call at 5 o'clock today. Do someth |

## Phrase 29: _Yaad dilana aaj_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | । याद दिलाना आज कुछ करो हाँ ठीक है नमस्ते क | लो। याद दिलाना आज। कुछ करो। अभी याद दिलाना |
| `saarika_v2.5_unknown` | । याद दिलाना आज कुछ करो हाँ ठीक है नमस्ते क | लो। याद दिलाना आज। कुछ करो। अभी याद दिलाना |
| `saaras_v3_transcribe` | लो। याद दिलाना आज, कुछ करो। हाँ ठीक है। नमस | बोलो याद दिलाना आज कुछ करो। अभी याद दिलाना, |
| `saaras_v3_verbatim` | बोलो याद दिलाना आज। कुछ करो। हां ठीक है। नम | बोलो याद दिलाना आज कुछ करो अभी याद दिलाना थ |
| `saaras_v3_translit` | olo. Yaad dilana aaj. Kuch karo. Haan theek h | olo. Yaad dilana aaj. Kuch karo. Abhi yaad di |
| `saaras_v3_codemix` | ोलो। याद दिलाना आज। कुछ करो। हां ठीक है। नम | बोलो याद दिलाना आज कुछ करो अभी याद दिलाना थ |
| `saaras_v3_translate` | PM. Remind me today. Do something. Yes, okay | — |

## Phrase 30: _Kuch karo_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | ज कुछ करो हाँ ठीक है नमस्ते क्या हाल | आज। कुछ करो। अभी याद दिलाना थोड़ी देर |
| `saarika_v2.5_unknown` | ज कुछ करो हाँ ठीक है नमस्ते क्या हाल | आज। कुछ करो। अभी याद दिलाना थोड़ी देर |
| `saaras_v3_transcribe` | आज, कुछ करो। हाँ ठीक है। नमस्ते, क्या | ा आज कुछ करो। अभी याद दिलाना, थोड़ी द |
| `saaras_v3_verbatim` | आज। कुछ करो। हां ठीक है। नमस्ते क्या | ा आज कुछ करो अभी याद दिलाना थोड़ी देर |
| `saaras_v3_translit` | aaj. Kuch karo. Haan theek hai. Namaste | aaj. Kuch karo. Abhi yaad dilana thodi |
| `saaras_v3_codemix` | आज। कुछ करो। हां ठीक है। नमस्ते क्या | ा आज कुछ करो अभी याद दिलाना थोड़ी देर |
| `saaras_v3_translate` | day. Do something. Yes, okay. Hello, how a | day. Do something. Remind me now, remind m |

## Phrase 31: _Haan theek hai_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | ो हाँ ठीक है नमस्ते क्या हाल है | ाना हाँ ठीक है नमस्ते क्या हाल है |
| `saarika_v2.5_unknown` | ो हाँ ठीक है नमस्ते क्या हाल है | ाना हाँ ठीक है नमस्ते क्या हाल है |
| `saaras_v3_transcribe` | रो। हाँ ठीक है। नमस्ते, क्या हाल है? | ाना। हाँ, ठीक है। नमस्ते, क्या हाल है? |
| `saaras_v3_verbatim` | करो। हां ठीक है। नमस्ते क्या हाल है? | लाना हाँ ठीक है नमस्ते क्या हाल है |
| `saaras_v3_translit` | aro. Haan theek hai. Namaste kya haal hai. | lana Haan theek hai Namaste kya haal hain |
| `saaras_v3_codemix` | करो। हां ठीक है। नमस्ते क्या हाल है? | लाना हाँ ठीक है नमस्ते क्या हाल है |
| `saaras_v3_translate` | ing. Yes, okay. Hello, how are you? | ile. Yes, okay. Hello, how are you? |

## Phrase 32: _Namaste, kya haal hai_

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | ै नमस्ते क्या हाल है | है नमस्ते क्या हाल है |
| `saarika_v2.5_unknown` | ै नमस्ते क्या हाल है | है नमस्ते क्या हाल है |
| `saaras_v3_transcribe` | है। नमस्ते, क्या हाल है? | है। नमस्ते, क्या हाल है? |
| `saaras_v3_verbatim` | है। नमस्ते क्या हाल है? | क है नमस्ते क्या हाल है |
| `saaras_v3_translit` | hai. Namaste kya haal hai. | hai Namaste kya haal hain |
| `saaras_v3_codemix` | है। नमस्ते क्या हाल है? | क है नमस्ते क्या हाल है |
| `saaras_v3_translate` | kay. Hello, how are you? | kay. Hello, how are you? |

---

## Capture summary per variant

Number of phrases captured (out of 31; phrase 20 excluded).

| Variant | File 1 | File 2 |
|---|---|---|
| `saarika_v2.5_hi` | 31/31 | 24/31 |
| `saarika_v2.5_unknown` | 31/31 | 24/31 |
| `saaras_v3_transcribe` | 31/31 | 24/31 |
| `saaras_v3_verbatim` | 31/31 | 24/31 |
| `saaras_v3_translit` | 31/31 | 24/31 |
| `saaras_v3_codemix` | 31/31 | 24/31 |
| `saaras_v3_translate` | 31/31 | 23/31 |

## Per-phrase capture count

Number of variants (out of 7) that captured each phrase.

| # | Phrase | File 1 | File 2 |
|---|---|---|---|
| 1 | Rajesh ko WhatsApp karo, bolo kal subah 10 baje aa jaaye | 7/7 | 7/7 |
| 2 | Supplier ko SMS bhejo, cement ka rate kya hai confirm karo | 7/7 | 7/7 |
| 3 | Sharma sahab ko WhatsApp karo, kal milte hain shop par | 7/7 | 0/7 |
| 4 | Ramu bhaiya ko bolo yaad rakhe, kal delivery aayegi | 7/7 | 7/7 |
| 5 | Send message to Sharma ji that payment will be done next week | 7/7 | 7/7 |
| 6 | 3 baje yaad dilana Rajesh ko call karna hai | 7/7 | 7/7 |
| 7 | Kal subah reminder lagana bank jaana hai | 7/7 | 7/7 |
| 8 | 30 minute baad yaad dilana godown check karna hai | 7/7 | 7/7 |
| 9 | Subah 8:30 baje yaad dilana | 7/7 | 0/7 |
| 10 | Thodi der mein yaad dilana | 7/7 | 7/7 |
| 11 | Abhi yaad dilana | 7/7 | 7/7 |
| 12 | In 30 minutes remind me | 7/7 | 0/7 |
| 13 | In two hours remind me to call supplier | 7/7 | 7/7 |
| 14 | Kal shaam yaad dilana | 7/7 | 0/7 |
| 15 | Shaam ko yaad dilana godown band karna | 7/7 | 7/7 |
| 16 | Raat ko 9 baje yaad dilana | 7/7 | 7/7 |
| 17 | Rajesh ko message bhejo ki kal aana hai aur 5 baje yaad bhi dilana | 7/7 | 0/7 |
| 18 | Ramu ko bolo Praveen ko call kare aur delivery confirm kare | 7/7 | 7/7 |
| 19 | Driver ko bolo 10 baje site par pahunche | 7/7 | 7/7 |
| 20 | The driver ko call karo | n/a | n/a |
| 21 | Naukar ko bolo dukaan band kare | 7/7 | 7/7 |
| 22 | Chhotu ko bolo ghar jaake khaana le aaye | 7/7 | 7/7 |
| 23 | Driver ko call karo | 7/7 | 0/7 |
| 24 | Rajesh ji ko phone lagao | 7/7 | 7/7 |
| 25 | Call Ramu | 7/7 | 7/7 |
| 26 | Accountant ji ko call karo abhi | 7/7 | 7/7 |
| 27 | Chacha ko phone karo | 7/7 | 0/7 |
| 28 | Rajesh ko 5 baje bolo | 7/7 | 7/7 |
| 29 | Yaad dilana aaj | 7/7 | 6/7 |
| 30 | Kuch karo | 7/7 | 7/7 |
| 31 | Haan theek hai | 7/7 | 7/7 |
| 32 | Namaste, kya haal hai | 7/7 | 7/7 |