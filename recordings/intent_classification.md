# Intent classification results — short clips

We ran each clip's transcript through `app.services.classify.classify_intent`
(Gemini 2.5 Flash-Lite, `classify.py` SYSTEM_PROMPT). Two inputs per clip:
the Hinglish translit output and the Devanagari output. If the classifier
is robust to script, both should produce the same intent.

`expected` is what a human would reasonably label the utterance — based on
the brief's phrase groupings. 'ambiguous' and 'unknown' are legitimate
outcomes for fragments and off-topic phrases.

## Intent accuracy (excluding clips the brief itself labels ambiguous)

- Translit input: **15/18** intent matches
- Devanagari input: **14/18** intent matches

## Per-clip detail

| Clip | Expected | ASR translit → intent | conf | ASR dev → intent | conf | Slots (translit) |
|---|---|---|---|---|---|---|
| `Yogesh/PM1`<br>_Hum theek hai_ | **unknown**<br>~31 (off-topic 'haan theek hai' variant) | ✓ unknown | 0.5 | ✓ unknown | 0.5 | (none) |
| `Yogesh/PM2`<br>_Bol do bol do das baje site par pahunche_ | **delegate**<br>~19 (Driver ko bolo site pahunche) — prefix dropped | ✗ unknown | 0.0 | ✗ unknown | 0.0 | (none) |
| `Yogesh/PM3`<br>_Aath baje yaad dilana_ | **reminder**<br>~9 variant (8 baje yaad dilana) | ✓ reminder | 0.0 | ✓ reminder | 0.0 | scheduled_time=20:00:00 |
| `Yogesh/PM4`<br>_Baje bolo_ | **ambiguous**<br>fragment 'baje bolo' | unknown | 0.5 | unknown | 0.5 | (none) |
| `Yogesh/PM5`<br>_Mountain G ko call karo abhi_ | **call**<br>26 (Accountant ji ko call karo abhi) — 'Mountain G' error | ✓ call | 0.0 | ✓ call | 0.0 | recipient_name=Mountain G<br>scheduled_time=now |
| `Yogesh/PM6`<br>_Ramu bhaiya ko bol do yaad rakhein kal delivery aayegi_ | **message**<br>4 (Ramu bhaiya ko bolo yaad rakhe...) | ✗ delegate | 0.0 | ✗ delegate | 0.0 | recipient_name=Ramu bhaiya<br>task_description=yaad rakhein kal delivery aayegi |
| `GS/PM11`<br>_Supplier ko SMS bhejo cement ka rate kya hai confirm karo_ | **message**<br>2 (Supplier ko SMS bhejo, cement rate) | ✓ message | 0.0 | ✓ message | 0.0 | recipient_name=Supplier<br>channel=sms |
| `GS/PM13`<br>_Rajesh ko WhatsApp karo aur bolo kal subah das baje aa jaye_ | **message**<br>1 (Rajesh ko WhatsApp karo) | ✓ message | 0.0 | ✓ message | 0.0 | recipient_name=Rajesh<br>channel=whatsapp |
| `GS/PM10`<br>_Thodi der mein yaad dilana._ | **reminder**<br>10 (Thodi der mein yaad dilana) | ✓ reminder | 0.0 | ✓ reminder | 0.0 | scheduled_time=in 30 minutes |
| `GS/PM7`<br>_Baje yaad dilana Rajesh ko call karna hai_ | **reminder**<br>6 (3 baje yaad dilana Rajesh ko call) — '3' dropped | ✓ reminder | 0.0 | ✓ reminder | 0.0 | recipient_name=Rajesh<br>reminder_text=Rajesh ko call karna hai |
| `GS/PM8`<br>_And message to Sharma ji, the payment will be done next week._ | **message**<br>5 (English: payment next week) | ✓ message | 0.9 | ✓ message | 0.9 | recipient_name=Sharma ji<br>message_body=the payment will be done next week. |
| `GS/PM9`<br>_Aamu ko bolo Praveen ko call karein aur delivery confirm karein_ | **delegate**<br>18 (Ramu → Praveen ko call & delivery confirm) — 'Ramu→Aamu' | ✓ delegate | 0.0 | ✗ unknown | 0.0 | recipient_name=Aamu<br>task_description=Praveen ko call karein aur delivery confirm karein |
| `GS/PM5`<br>_Bolo ghar ja ke khana le aaye_ | **delegate**<br>22 fragment (Chhotu ko bolo ghar jaake khana) | ✓ delegate | 0.0 | ✓ delegate | 0.0 | recipient_name=ghar<br>task_description=khana le aaye |
| `GS/PM6`<br>_Sharma sahab ko WhatsApp karo kal milte hain subah sahab par_ | **message**<br>3 (Sharma sahab ko WhatsApp) — 'shop par→subah sahab par' error | ✓ message | 0.0 | ✓ message | 0.0 | recipient_name=Sharma sahab<br>scheduled_time=tomorrow morning |
| `GS/PM`<br>_Message bhej do kal aana hai aur paanch baje yaad yaad bhi dilana_ | **message**<br>17 compound (Rajesh ko message + 5 baje yaad) — Rajesh dropped | ✓ message | 0.6 | ✓ message | 0.6 | message_body=kal aana hai<br>scheduled_time=17:00:00 |
| `GS/PM2-first`<br>_Hours remind me to call supplier_ | **reminder**<br>13 (2 hours remind me to call supplier) | ✓ reminder | 0.0 | ✓ reminder | 0.0 | recipient_name=supplier<br>reminder_text=call supplier<br>scheduled_time=in 1 hour |
| `GS/PM2-second`<br>_Mountain G ko call karo abhi_ | **call**<br>26 (same as Yogesh PM5) | ✓ call | 0.0 | ✓ call | 0.0 | recipient_name=Mountain G<br>scheduled_time=now |
| `GS/PM3`<br>_Baje bolo_ | **ambiguous**<br>fragment 'baje bolo' (same as Yogesh PM4) | unknown | 0.5 | unknown | 0.5 | (none) |
| `GS/PM4`<br>_Aath baje yaad dilana_ | **reminder**<br>9 variant (same as Yogesh PM3) | ✓ reminder | 0.0 | ✓ reminder | 0.0 | scheduled_time=20:00:00 |
| `GS/PM1`<br>_Ramu bhaiya ko bol do yaad rakhein kal delivery aayegi_ | **message**<br>4 (same as Yogesh PM6) | ✗ delegate | 0.0 | ✗ delegate | 0.0 | recipient_name=Ramu bhaiya<br>task_description=yaad rakhein kal delivery aayegi |