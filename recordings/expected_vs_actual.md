# Expected vs actual — what Sarvam transcribed

Two columns per file:
- **translit**: `saaras:v3` mode=translit — produces Hinglish Latin, lines up with the brief's format for easy visual comparison.
- **saarika (Hindi)**: `saarika:v2.5` — the current bot default. Rendered in Devanagari.

Each cell shows the extracted sentence containing the phrase keywords
(expanded to the nearest sentence boundary). `—` = no matching span
found, which means either the phrase wasn't spoken or the ASR output
deviated too far from any of the keyword variants we tried. Cross-check
against the full transcripts under `recordings/_variants/<variant>/` if
any `—` looks suspicious.

Phrase 20 ("The driver ko call karo") is excluded — transcribes
identically to phrase 23 so it can't be distinguished.

## File 1 (12.08.32 PM)

| # | Expected (from brief) | saaras:v3 translit | saarika:v2.5 (Hindi) |
|---|---|---|---|
| 1 | Rajesh ko WhatsApp karo, bolo kal subah 10 baje aa jaaye | Rajesh ko bolo WhatsApp karo. Bolo kal subah 10:00 baje aaye. | राजेश को बोलो WhatsApp करो। बोलो कल सुबह 10:00 बजे आएं। |
| 2 | Supplier ko SMS bhejo, cement ka rate kya hai confirm karo | Supplier ko SMS bhejo cement ka rate kya hai confirm karo. | सप्लायर को एसएमएस भेजो सीमेंट का रेट क्या है, कंफर्म करो। |
| 3 | Sharma sahab ko WhatsApp karo, kal milte hain shop par | Sharma sahab ko WhatsApp karo kal milne shop par. | शर्मा साहब को WhatsApp करो, कल मिलने शॉप पर। |
| 4 | Ramu bhaiya ko bolo yaad rakhe, kal delivery aayegi | Ramu bhaiya, bolo yaad rakhen, kal delivery aayegi. | नामू भैया, बोलो याद रखें, कल डिलीवरी आएगी। |
| 5 | Send message to Sharma ji that payment will be done next week | Sharma ji ko message bhej ke payment alag agle hafte. | शर्मा जी को मैसेज भेज के पेमेंट अलग अगले हफ्ते। |
| 6 | 3 baje yaad dilana Rajesh ko call karna hai | 3:00 baje yaad dilana Rajesh ko call karne ka. | 3:00 बजे याद दिलाना राजेश को कॉल करने का। |
| 7 | Kal subah reminder lagana bank jaana hai | Kal subah remind lagaakar bank jaana. | कल सुबह रिमाइंड लगाकर बैंक जाना। |
| 8 | 30 minute baad yaad dilana godown check karna hai | 20 minute baad yaad dilana, godown check karna hai. | 30 मिनट बाद याद दिलाना, गोडाउन चेक करना है। |
| 9 | Subah 8:30 baje yaad dilana | Subah 8:30 baje yaad dilana. | सुबह 8:30 बजे याद दिलाना। |
| 10 | Thodi der mein yaad dilana | Thodi der mein yaad dilana. | थोड़ी देर में याद दिलाना। |
| 11 | Abhi yaad dilana | Abhi yaad dilana. | अभी याद दिलाना। 30 मिनट में मुझे याद दिलाना। |
| 12 | In 30 minutes remind me | 30 minute mein mujhe yaad dilana. | 30 मिनट में मुझे याद दिलाना। |
| 13 | In two hours remind me to call supplier | 2 ghante mein mujhe supplier ko call karne ke liye yaad dilana. | 2 घंटे में मुझे सप्लायर को कॉल करने के लिए याद दिलाना। |
| 14 | Kal shaam yaad dilana | Kal shaam yaad dilana. | कल शाम याद दिलाना शाम को याद दिलाना गोडाउन बंद करना है रात को नौ बजे याद दिलाना राजेश को मैसेज भेजो कि कल आना है और पाँच बजे याद दिलाना रामू को बोलो प… |
| 15 | Shaam ko yaad dilana godown band karna | Shaam ko yaad dilana godown band karna hai. | कल शाम याद दिलाना शाम को याद दिलाना गोडाउन बंद करना है रात को नौ बजे याद दिलाना राजेश को मैसेज भेजो कि कल आना है और पाँच बजे याद दिलाना रामू को बोलो प… |
| 16 | Raat ko 9 baje yaad dilana | Raat ko 9:00 baje yaad dilana. | कल शाम याद दिलाना शाम को याद दिलाना गोडाउन बंद करना है रात को नौ बजे याद दिलाना राजेश को मैसेज भेजो कि कल आना है और पाँच बजे याद दिलाना रामू को बोलो प… |
| 17 | Rajesh ko message bhejo ki kal aana hai aur 5 baje yaad bhi dilana | Raat ko 9:00 baje yaad dilana. Rajesh ko message bhejo ki kal aana hai aur 5:00 baje yaad dilana. | …शाम को याद दिलाना गोडाउन बंद करना है रात को नौ बजे याद दिलाना राजेश को मैसेज भेजो कि कल आना है और पाँच बजे याद दिलाना रामू को बोलो परमानेंट को कॉल करे… |
| 18 | Ramu ko bolo Praveen ko call kare aur delivery confirm kare | Ramu ko bolo permanent ko call kare aur delivery confirm kare. | …बंद करना है रात को नौ बजे याद दिलाना राजेश को मैसेज भेजो कि कल आना है और पाँच बजे याद दिलाना रामू को बोलो परमानेंट को कॉल करे और डिलीवरी कन्फर्म करे। |
| 19 | Driver ko bolo 10 baje site par pahunche | Driver ko bolo 10:00 baje site par pahunche. | ड्राइवर को बोलो 10:00 बजे साइट पर पहुंचे। |
| 20 | The driver ko call karo | — | — |
| 21 | Naukar ko bolo dukaan band kare | Naukar ko bolo dukaan band kare. | नौकर को बोलो दुकान बंद करे। |
| 22 | Chhotu ko bolo ghar jaake khaana le aaye | Chhotu ko bolo ghar ja ke khana le aaye. | छोटू को बोलो घर जाके खाना ले आए। |
| 23 | Driver ko call karo | Driver ko call karo. | ड्राइवर को कॉल करो। |
| 24 | Rajesh ji ko phone lagao | Rajesh ji ko phone lagao. | राजेश जी को फ़ोन लगाओ। रामू को कॉल करे। |
| 25 | Call Ramu | Ramu ko call kare. | रामू को कॉल करे। |
| 26 | Accountant ji ko call karo abhi | Accountant ji se call karo abhi. | अकाउंटेंट जी से कॉल करो अभी। चाचा को फ़ोन करो। |
| 27 | Chacha ko phone karo | Chacha ko phone karo. | चाचा को फ़ोन करो। |
| 28 | Rajesh ko 5 baje bolo | Rajesh ko 5:00 baje bolo. | राजेश को 5:00 बजे बोलो। याद दिलाना आज कुछ करो हाँ ठीक है नमस्ते क्या हाल है |
| 29 | Yaad dilana aaj | Yaad dilana aaj. | याद दिलाना आज कुछ करो हाँ ठीक है नमस्ते क्या हाल है |
| 30 | Kuch karo | Kuch karo. | याद दिलाना आज कुछ करो हाँ ठीक है नमस्ते क्या हाल है |
| 31 | Haan theek hai | Haan theek hai. | याद दिलाना आज कुछ करो हाँ ठीक है नमस्ते क्या हाल है |
| 32 | Namaste, kya haal hai | Namaste kya haal hai. | याद दिलाना आज कुछ करो हाँ ठीक है नमस्ते क्या हाल है |

## File 2 (12.08.33 PM)

| # | Expected (from brief) | saaras:v3 translit | saarika:v2.5 (Hindi) |
|---|---|---|---|
| 1 | Rajesh ko WhatsApp karo, bolo kal subah 10 baje aa jaaye | Rajesh ko WhatsApp karo bolo kal subah 10:00 baje aa jaaye. | राजेश को WhatsApp करो, बोलो कल सुबह 10:00 बजे आ जाए। |
| 2 | Supplier ko SMS bhejo, cement ka rate kya hai confirm karo | Supplier ko SMS bhejo, cement ka rate kya hai aaj? | सप्लायर को एसएमएस भेजो, सीमेंट का रेट क्या है आज? |
| 3 | Sharma sahab ko WhatsApp karo, kal milte hain shop par | — | — |
| 4 | Ramu bhaiya ko bolo yaad rakhe, kal delivery aayegi | Ramu bhaiya ko bolo, yaad rakhen kal delivery aayegi. | रामू भैया को बोलो, याद रखें कल डिलीवरी आएगी। |
| 5 | Send message to Sharma ji that payment will be done next week | Sharma ji ko message bhejo, payment next week denge. | शर्मा जी को मैसेज भेजो, पेमेंट नेक्स्ट वीक देंगे। |
| 6 | 3 baje yaad dilana Rajesh ko call karna hai | 3:00 baje yaad dilana Rajesh ko call karna hai. | तीन बजे याद दिलाना राजेश को कॉल करना है कल सुबह रिमाइंडर लगाना बैंक जाना है 30 मिनट बाद याद दिलाना, गोडाउन चेक करना है। |
| 7 | Kal subah reminder lagana bank jaana hai | Kal subah reminder lagana bank jaana hai. | तीन बजे याद दिलाना राजेश को कॉल करना है कल सुबह रिमाइंडर लगाना बैंक जाना है 30 मिनट बाद याद दिलाना, गोडाउन चेक करना है। |
| 8 | 30 minute baad yaad dilana godown check karna hai | 30 minute baad yaad dilana godown check karna hai. | तीन बजे याद दिलाना राजेश को कॉल करना है कल सुबह रिमाइंडर लगाना बैंक जाना है 30 मिनट बाद याद दिलाना, गोडाउन चेक करना है। |
| 9 | Subah 8:30 baje yaad dilana | — | — |
| 10 | Thodi der mein yaad dilana | Abhi yaad dilana thodi der mein yaad dilana Haan theek hai Namaste kya haal hain | अभी याद दिलाना थोड़ी देर में याद दिलाना हाँ ठीक है नमस्ते क्या हाल है |
| 11 | Abhi yaad dilana | Abhi yaad dilana thodi der mein yaad dilana Haan theek hai Namaste kya haal hain | अभी याद दिलाना थोड़ी देर में याद दिलाना हाँ ठीक है नमस्ते क्या हाल है |
| 12 | In 30 minutes remind me | — | — |
| 13 | In two hours remind me to call supplier | In two hours remind me to call the supplier. | इन टू आवर्स रिमाइंड मी टू कॉल द सप्लायर। रात को 9:00 बजे याद दिलाना। |
| 14 | Kal shaam yaad dilana | — | — |
| 15 | Shaam ko yaad dilana godown band karna | Shaam ko yaad dilana godown band karna hai. | शाम को याद दिलाना, गोडाउन बंद करना है। |
| 16 | Raat ko 9 baje yaad dilana | Raat ko 9:00 baje yaad dilana. | रात को 9:00 बजे याद दिलाना। |
| 17 | Rajesh ko message bhejo ki kal aana hai aur 5 baje yaad bhi dilana | — | — |
| 18 | Ramu ko bolo Praveen ko call kare aur delivery confirm kare | Ramu ko bolo Praveen ko call karke delivery confirm kare. | रामू को बोलो प्रवीण को कॉल करके डिलीवरी कन्फर्म करें ड्राइवर को बोलो दस बजे साइट पर पहुंचे नौकर को बोलो दुकान बंद करे। |
| 19 | Driver ko bolo 10 baje site par pahunche | Driver ko bolo 10:00 baje site par pahunche. | रामू को बोलो प्रवीण को कॉल करके डिलीवरी कन्फर्म करें ड्राइवर को बोलो दस बजे साइट पर पहुंचे नौकर को बोलो दुकान बंद करे। |
| 20 | The driver ko call karo | — | — |
| 21 | Naukar ko bolo dukaan band kare | Naukar ko bolo dukaan band kare. | रामू को बोलो प्रवीण को कॉल करके डिलीवरी कन्फर्म करें ड्राइवर को बोलो दस बजे साइट पर पहुंचे नौकर को बोलो दुकान बंद करे। |
| 22 | Chhotu ko bolo ghar jaake khaana le aaye | Chhotu ko bolo ghar ja ke khana khana le aaye. | छोटू को बोलो घर जाके खाना खा खाना ले आए। |
| 23 | Driver ko call karo | — | — |
| 24 | Rajesh ji ko phone lagao | Rajesh ji ko phone lagao. | राजेश जी को फ़ोन लगाओ। अकाउंटेंट को कॉल करो अभी। |
| 25 | Call Ramu | Call Ramu. | कॉल रामू। तीन बजे याद दिलाना राजेश को कॉल करना है कल सुबह रिमाइंडर लगाना बैंक जाना है 30 मिनट बाद याद दिलाना, गोडाउन चेक करना है। |
| 26 | Accountant ji ko call karo abhi | Accountant ko call karo abhi. | अकाउंटेंट को कॉल करो अभी। कॉल रामू। |
| 27 | Chacha ko phone karo | — | — |
| 28 | Rajesh ko 5 baje bolo | Rajesh ko 5:00 baje ka bolo. | राजेश को 5:00 बजे का बोलो। याद दिलाना आज। |
| 29 | Yaad dilana aaj | Yaad dilana aaj. | याद दिलाना आज। कुछ करो। |
| 30 | Kuch karo | Kuch karo. | कुछ करो। अभी याद दिलाना थोड़ी देर में याद दिलाना हाँ ठीक है नमस्ते क्या हाल है |
| 31 | Haan theek hai | Abhi yaad dilana thodi der mein yaad dilana Haan theek hai Namaste kya haal hain | अभी याद दिलाना थोड़ी देर में याद दिलाना हाँ ठीक है नमस्ते क्या हाल है |
| 32 | Namaste, kya haal hai | Abhi yaad dilana thodi der mein yaad dilana Haan theek hai Namaste kya haal hain | अभी याद दिलाना थोड़ी देर में याद दिलाना हाँ ठीक है नमस्ते क्या हाल है |
