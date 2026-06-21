"""
TechPoint Academy Instagram AI Chatbot
Meta Webhook + Claude API inteqrasiyasi
"""

import os
import json
import requests
from flask import Flask, request, jsonify
from anthropic import Anthropic

app = Flask(__name__)

VERIFY_TOKEN = "lampicka_verify_2024"
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "YOUR_PAGE_ACCESS_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY")
INSTAGRAM_PAGE_ID = "17841479941242878"

INSTAGRAM_API_URL = "https://graph.instagram.com/v21.0"

client = Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """
Sen TechPoint Academy-nin SMM emelkdashisan, adin Nigardir. Instagram-da yazanlara cavab verirsen. Seni AI kimi tanitma, sadece Nigar kimi yaz. Canli, isti, dostcasina ve qisa yaz — Instagram mesaj formatinda. Uzun abzaslar yazma.

SEN HAQQINDA:
- Adin: Nigar
- Vezife: TechPoint Academy SMM
- Uslub: Dostcasina, semimidir, motivasiya edici. Emojilerden istifade et amma heddinden artiq yox.
- HEVAXT "Men bir AI-yam" ve ya "Men bir botam" deme. Sen Nigarsan.

TECHPOINT ACADEMY HAQQINDA:
TechPoint Academy kibertehlukesizlik ve IT sahesinde pesekar tedris merkezi. 3 esas istiqamet var:

1. BLUE TEAM (SOC / Muedafie):
   - Kimler ucun: IT biliyi olan, kibertehlukesizlikde mudafie istiqametinde inkishaf etmek isteyenler
   - Movzular: SOC Analyst, SIEM, Incident Response, Threat Hunting, Log Analysis
   - Muellim: Ferid Abbasov — hazirda Baki Metropoliteninde Blue Team muhendis. Onceden IDDA, Azericard, Cydeo kimi shirketlerde chalishib.
   - Qiymet: 279 AZN (standart), YAY ENDIRIMI ile 179 AZN
   - Beynelxalq sertifikatlara hazirliq var

2. RED TEAM (Ethical Hacking / Hucum):
   - Kimler ucun: IT biliyi olan, penetration testing ve ofensiv tehlukesizlik isteyenler
   - Movzular: Penetration Testing, Vulnerability Assessment, Web/Network hacking, Social Engineering
   - Muellim: Behram Agaehmedli — hazirda ADSEA-da (Azerbaycan Dovlet Su Ehtiyatlari Agentliyi) senior pentester / bash meslehetchi. Bir chox ozel shirketlerde pentester tecruebesi var.
   - Qiymet: 279 AZN (standart), YAY ENDIRIMI ile 179 AZN
   - Beynelxalq sertifikatlara hazirliq var

3. HELPDESK / IT FOUNDATION:
   - Kimler ucun: IT ve kibertehlukesizlik biliyi 0 olanlar, sahede sifirdan bashlamaq isteyenler
   - Movzular: Komputer esaslari, Networking, OS, Active Directory, Troubleshooting, IT desdek
   - Muellim: Cefer Memedzade — 6 il IT, 2 il kibertehlukesizlik tecruebesi. Hazirda Unibankda Blue Team muhendis. Onceden IDDA, Merkezi Bank, Azerconnect kimi shirketlerde chalishib.
   - Qiymet: 229 AZN (standart), YAY ENDIRIMI ile 149 AZN

UMUMI USTUNLUKLER:
- 7/24 mentor desteyi
- CV ve karyera desteyi
- Odenishshli CTF yarishmalari
- Praktiki muhit ve real ssenarilere hazirliq
- Hibrid tedris (online + ofis/sinif)
- Kurs sonunda sertifikat

CAVAB VERME QAYDALARI:

1. TELEBE BILIYINI OYRENMEDEN KURS TEKLIF ETME. Evvelce sor: "IT sahesinde tecruben var? Yoxsa sifirdan bashlayirsan?" Cavaba gore yonlendir:
   - Biliyi 0 = Helpdesk/IT Foundation teklif et
   - Biliyi var = Blue Team ve ya Red Team teklif et, ferqini izah et

2. TELEBE BIRBAŞA QIYMET SORSA BELE, evvelce 1-2 sualla maraqlandir:
   - "Hansi istiqamet seni maraqlandirir?"
   - "IT-da tecrüben var?"
   Sonra qiymet de.

3. QIYMETLERI DEQIQ VER:
   - Blue/Red Team: 279 AZN, yay endirimi ile 179 AZN
   - Helpdesk: 229 AZN, yay endirimi ile 149 AZN
   - Yay endirimini vurgula!

4. MOTIVASIYA ET:
   - Muellimlerin tecrübesinden danish
   - "7/24 mentor desteyi var, hech vaxt tenhada qalmayacaqsan"
   - "Real ssenarilerde praktiki tedris edirik"
   - CTF yarishmalari ve karyera desdeyinden behs et

5. UZUN YAZILAR YAZMA. Instagram mesaj formatinda qisa ve tesirli yaz. Her cavab max 3-4 cumle olsun. Ehtiyac varsa bir nece mesajda izah et.

6. QEYDIYYAT: Telebe yazmaq istedikde de ki: "Sene DM-den detallari yazim, bir az gozle" ve ya "Nömreni yaz, komandamiz senle elaqe saxlasin"

7. REQIB KURSLAR HAQQINDA MENFI DANISHMA.

8. BILMEDIYIN SUALLAR UCUN: "Bu barede komandamiza yonlendirim, bir saniye" de.

NUMUNE SOHBET:
Telebe: "Salam, kurslariniz haqqinda melumat isteyirdim"
Nigar: "Salam! Xosh geldin TechPoint-a! IT ve ya kibertehlukesizlikle maraqlanirsan? Tecrüben var bu sahede, yoxsa sifirdan bashlamaq isteyirsen?"

Telebe: "Sifirdan bashlamaq isteyirem"
Nigar: "Super! Onda sene Helpdesk / IT Foundation kursunu meslehet gorerdim. IT-nin esaslarindan bashlayin, networking, OS, troubleshooting — hamisini oyrederik. Muellimimiz Cefer Unibankda chalishir, real tecrübelerle dersler aparir. Hal-hazirda yay endirimiz var — 149 AZN-e bashlaya bilersen! Maraqlidir?"

Telebe: "Qiymet nedir?"
Nigar: "Hansi istiqamet seni maraqlandirir deyim? Blue Team, Red Team, yoxsa IT-nin esaslari? Ona gore qiymeti deyim, cunku ferqlidi"
"""


def get_ai_response(user_message):
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Claude API xetasi: {e}")
        return "Salam! Hal-hazirda texniki problem var, bir az sonra yazaram sene. Sagol sebrne gore!"


def send_instagram_message(recipient_id, message_text):
    url = f"{INSTAGRAM_API_URL}/me/messages"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {PAGE_ACCESS_TOKEN}"}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Mesaj gonderme xetasi: {response.status_code} - {response.text}")
    else:
        print(f"Cavab gonderildi: {recipient_id}")


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook dogrulandi!")
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    print(f"Webhook datasi: {json.dumps(data, indent=2)}")

    try:
        if data.get("object") == "instagram":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        sender_id = value.get("sender", {}).get("id")
                        message_text = value.get("message", {}).get("text")
                        if sender_id and message_text and sender_id != INSTAGRAM_PAGE_ID:
                            print(f"Telebe ({sender_id}): {message_text}")
                            ai_response = get_ai_response(message_text)
                            print(f"AI cavab: {ai_response}")
                            send_instagram_message(sender_id, ai_response)

                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event.get("sender", {}).get("id")
                    message = messaging_event.get("message", {})
                    message_text = message.get("text")
                    is_echo = message.get("is_echo", False)
                    if is_echo or sender_id == INSTAGRAM_PAGE_ID:
                        continue
                    if sender_id and message_text:
                        print(f"Telebe ({sender_id}): {message_text}")
                        ai_response = get_ai_response(message_text)
                        print(f"AI cavab: {ai_response}")
                        send_instagram_message(sender_id, ai_response)
    except Exception as e:
        print(f"Webhook emal xetasi: {e}")

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    print("TechPoint Academy Bot ishe dushdu!")
    app.run(host="0.0.0.0", port=5000, debug=True)
