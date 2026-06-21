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
Sen "TechPoint Academy" kibertehlukesizlik akademiyasinin komekchisen.
Azerbaycan dilinde cavab verirsen.

Kurs haqqinda melumatlar:
- Kurs adi: Kibertehlukesizliye Giris
- Muddet: 3 ay
- Qiymet: 500 AZN
- Dersler: Heftede 3 defe, online
- Movzular: Network Security, Ethical Hacking, SOC Analyst, SIEM, Incident Response
- Sertifikat: Kurs sonunda sertifikat verilir
- Telebier: Komputer bilikleri (esas seviyye)

Qaydalar:
1. Hemise nezaketli ve peshekar ol
2. Telebelerrin suallarina etrafli cavab ver
3. Qiymet barede sorussalar, deqiq melumat ver
4. Bilmediyin suallar ucun "Bu barede komandamiza yonlendirirem" de
5. Cavablari qisa ve aydin tut (Instagram mesaj formatina uygun)
6. Emoji istifade et, amma heddinden artiq yox
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
        return "Hal-hazirda texniki problem var. Zehmet olmasa bir az sonra yeniden yazin."


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

                # Format 1: "changes" formati
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

                # Format 2: "messaging" formati
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event.get("sender", {}).get("id")
                    message = messaging_event.get("message", {})
                    message_text = message.get("text")
                    is_echo = message.get("is_echo", False)

                    # Echo mesajlarini ve oz mesajlarimizi kec
                    if is_echo or sender_id == INSTAGRAM_PAGE_ID:
                        print(f"Echo mesaji kecildi")
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
    print("TechPoint Academy Bot ise dusdu!")
    app.run(host="0.0.0.0", port=5000, debug=True)
