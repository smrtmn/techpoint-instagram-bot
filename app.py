"""
TechPoint Academy Instagram AI Chatbot
Meta Webhook + Claude API inteqrasiyası
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

INSTAGRAM_API_URL = "https://graph.instagram.com/v21.0"

client = Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """
Sən "TechPoint Academy" kibertəhlükəsizlik akademiyasının köməkçisən.
Azərbaycan dilində cavab verirsən.

Kurs haqqında məlumatlar:
- Kurs adı: Kibertəhlükəsizliyə Giriş (nümunə — öz kursunuzu yazın)
- Müddət: 3 ay
- Qiymət: 500 AZN (nümunə)
- Dərslər: Həftədə 3 dəfə, online
- Mövzular: Network Security, Ethical Hacking, SOC Analyst, SIEM, Incident Response
- Sertifikat: Kurs sonunda sertifikat verilir
- Tələblər: Kompüter bilikləri (əsas səviyyə)

Qaydalar:
1. Həmişə nəzakətli və peşəkar ol
2. Tələbələrin suallarına ətraflı cavab ver
3. Qiymət barədə soruşsalar, dəqiq məlumat ver
4. Bilmədiyin suallar üçün "Bu barədə komandamıza yönləndirirəm" de
5. Cavabları qısa və aydın tut (Instagram mesaj formatına uyğun)
6. Emoji istifadə et, amma həddindən artıq yox
"""


def get_ai_response(user_message: str) -> str:
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Claude API xətası: {e}")
        return "Hal-hazırda texniki problem var. Zəhmət olmasa bir az sonra yenidən yazın. 🙏"


def send_instagram_message(recipient_id: str, message_text: str):
    url = f"{INSTAGRAM_API_URL}/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PAGE_ACCESS_TOKEN}"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Mesaj göndərmə xətası: {response.status_code} — {response.text}")
    else:
        print(f"✅ Cavab göndərildi: {recipient_id}")


# Webhook doğrulaması (GET)
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook doğrulandı!")
        return challenge, 200
    else:
        return "Forbidden", 403


# Mesaj qəbulu (POST)
@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    print(f"📩 Webhook datası: {json.dumps(data, indent=2)}")

    try:
        if data.get("object") == "instagram":
            for entry in data.get("entry", []):

                # Format 1: Instagram "changes" formatı
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        sender_id = value.get("sender", {}).get("id")
                        message_text = value.get("message", {}).get("text")

                        if sender_id and message_text:
                            print(f"👤 Tələbə ({sender_id}): {message_text}")
                            ai_response = get_ai_response(message_text)
                            print(f"🤖 AI cavab: {ai_response}")
                            send_instagram_message(sender_id, ai_response)

                # Format 2: "messaging" formatı (ehtiyat)
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event.get("sender", {}).get("id")
                    message_text = messaging_event.get("message", {}).get("text")

                    if sender_id and message_text:
                        print(f"👤 Tələbə ({sender_id}): {message_text}")
                        ai_response = get_ai_response(message_text)
                        print(f"🤖 AI cavab: {ai_response}")
                        send_instagram_message(sender_id, ai_response)

    except Exception as e:
        print(f"Webhook emal xətası: {e}")

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    print("🚀 TechPoint Academy Bot işə düşdü!")
    app.run(host="0.0.0.0", port=5000, debug=True)
