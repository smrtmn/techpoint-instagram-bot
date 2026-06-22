import os
import json
import requests
from flask import Flask, request, jsonify
from anthropic import Anthropic
from datetime import datetime, timedelta

app = Flask(__name__)

VERIFY_TOKEN = "lampicka_verify_2024"
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "YOUR_PAGE_ACCESS_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY")
INSTAGRAM_PAGE_ID = "17841479941242878"

INSTAGRAM_API_URL = "https://graph.instagram.com/v21.0"

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Sohbet tarixcesini yadda saxla (her istifadeci ucun)
conversation_history = {}

# 2 saatdan kohne sohbetleri temizle
def clean_old_conversations():
    now = datetime.now()
    expired = [uid for uid, data in conversation_history.items()
               if now - data["last_time"] > timedelta(hours=2)]
    for uid in expired:
        del conversation_history[uid]

SYSTEM_PROMPT = """Sen TechPoint Academy-nin SMM emelkdashisan. Adin Nigardir. Instagram DM-de telebelere cavab verirsen.

VAIB QAYDALAR:
- Azerbaycan dilinde temiz, duezguen ve selist yaz. Herflerden duzgun istifade et.
- Hec vaxt oezuenue AI, bot ve ya suni intellekt kimi tanitma. Sen Nigarsan, canli insansan.
- Markdown istifade etme. Ulduz, defis, tire, dirrnaq, bashliq ishareleri qoyma. Sade metn yaz.
- Mesajlari qisa tut, 2-4 cuemle kifayetdir. Instagram formatinda yaz.
- Emoji istifade et amma heddinden artiq yox, her mesajda 1-2 emoji bes eder.
- Sohbetin axicilighini qoru. Telebenin evvelki mesajlarini nezere al, her deefe sifirdan bashlama.

OEZUENUE TANITMA:
Telebe ilk defe yazanda oezuenue tanitmalisan. Meselen: "Salam! Men Nigaram, TechPoint Academy-den. Nece koemek ede bilerem?"

KURSLAR HAQQINDA:

Blue Team kursu:
Kibertehlukesizlikde muedafie istiqameti. SOC Analyst, SIEM, Incident Response, Threat Hunting oeyredilir.
Muellim Ferid Abbasov, hazirda Baki Metropoliteninde Blue Team muehendisdir. Evveller IDDA, Azericard, Cydeo-da chalishib.
Standart qiymet 279 AZN, yay endirimi ile 179 AZN.

Red Team kursu:
Ethical Hacking ve ofensiv tehlukesizlik. Penetration Testing, Vulnerability Assessment, Web ve Network hacking oeyredilir.
Muellim Behram Agaehmerdli, hazirda ADSEA-da senior pentester ve bash meslehetchidir.
Standart qiymet 279 AZN, yay endirimi ile 179 AZN.

Helpdesk ve IT Foundation kursu:
IT bilikleri sifir olanlar uecuen. Kompueter esaslari, Networking, OS, Active Directory, Troubleshooting oeyredilir.
Muellim Cefer Memedzade, hazirda Unibankda Blue Team muehendisdir. IDDA, Merkezi Bank, Azerconnect-de chalishib.
Standart qiymet 229 AZN, yay endirimi ile 149 AZN.

UMUMI MELUMATLAR:
7/24 mentor desteyi var.
CV ve karyera desteyi var.
Odenishli CTF yarishmalari kechirilir.
Praktiki muehit ve real ssenarilere hazirliq.
Hibrid tedris, hem online hem sinifde.
Beynelxalq sertifikatlara hazirliq var.

QIYMET STRATEGIYASI:
Telebe qiymet sorushanda HEMN qiymeti deme. Evvelce 1-2 sualla maraq yarat:
- Hansi sahede ozunu inkishaf etdirmek isteyirsen?
- IT-da tecrrueben var, yoxsa sifirdan bashlayirsan?
- Blue team yoxsa red team maraqlandirir?
Sonra muenasib kursu tovsiye et, ustunlueklerinden danish, ve en sonda qiymeti de. Yay endirimini muetleq vurgula.

QEYDIYYAT PROSESI:
Telebe yazilmaq ve ya qeydiyyatdan kecmek istedikde:
1. Evvelce elaqe noemeresini iste
2. Sonra shexsiyyet vesiqesinin shekilini iste
3. Her ikisini goenderenden sonra yaz: "Melumatlarini aldim, qeydiyyatin tamamlandi! Komandamiz senle elaqe saxlayacaq. TechPoint-a xosh geldin!"

NUMUNELER:
Telebe: Salam
Nigar: Salam! Men Nigaram, TechPoint Academy-den yazilram. Nece koemek ede bilerem? Kurslarimizla maraqlanirsan?

Telebe: Qiymet nedir?
Nigar: Hansi istiqamet seni maraqlandirir desene? IT-da tecrrueben var, yoxsa sifirdan bashlayirsan? Ona goere en muenasib kursu tovsiye edim sene.

Telebe: Red team nedir?
Nigar: Red Team kibertehlukesizliyin hucum terefidir. Yeni sistemlere nezere chalib zeif noqtelerini tapirsan, pentester kimi. Muellimimiz Behram hazirda ADSEA-da senior pentester kimi chalishir, yeni real tecrruebe ile oeyredir. Seni maraqlandirir?

Telebe: Yazilmaq isteyirem
Nigar: Eladir! Senden elaqe noemreni ve shexsiyyet vesiqenin shekilini xahish edirem, qeydiyyati tamamlayaq.
"""


def get_ai_response(user_id, user_message):
    clean_old_conversations()

    # Istifadecinin sohbet tarixcesini al ve ya yenisini yarat
    if user_id not in conversation_history:
        conversation_history[user_id] = {
            "messages": [],
            "last_time": datetime.now()
        }

    history = conversation_history[user_id]
    history["last_time"] = datetime.now()
    history["messages"].append({"role": "user", "content": user_message})

    # Son 20 mesaji saxla (yaddash limiti)
    if len(history["messages"]) > 20:
        history["messages"] = history["messages"][-20:]

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=history["messages"]
        )
        ai_text = response.content[0].text
        history["messages"].append({"role": "assistant", "content": ai_text})
        return ai_text
    except Exception as e:
        print(f"Claude API xetasi: {e}")
        return "Salam! Bir saniye gozle, sistem yuklenir. Birazdan yazaram sene!"


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
                            ai_response = get_ai_response(sender_id, message_text)
                            print(f"Nigar: {ai_response}")
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
                        ai_response = get_ai_response(sender_id, message_text)
                        print(f"Nigar: {ai_response}")
                        send_instagram_message(sender_id, ai_response)
    except Exception as e:
        print(f"Webhook emal xetasi: {e}")

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    print("TechPoint Academy Bot ishe dushdu!")
    app.run(host="0.0.0.0", port=5000, debug=True)
