"""
Lampicka Instagram AI Chatbot
Meta Webhook + Claude API inteqrasiyası
"""

import os
import json
import requests
from flask import Flask, request, jsonify
from anthropic import Anthropic

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════
#  KONFİQURASİYA — bu dəyərləri öz məlumatlarınızla əvəz edin
# ═══════════════════════════════════════════════════════════
VERIFY_TOKEN = "lampicka_verify_2024"           # Webhook üçün özünüz təyin edin
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN", "YOUR_PAGE_ACCESS_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY")

INSTAGRAM_API_URL = "https://graph.instagram.com/v21.0"

# Claude API client
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ═══════════════════════════════════════════════════════════
#  SİSTEM PROMPTU — Kursunuz haqqında məlumatlar buraya yazılır
#  Bu hissəni öz kursunuza uyğun dəyişdirin!
# ═══════════════════════════════════════════════════════════
SYSTEM_PROMPT = """
Sən "Lampicka" kibertəhlükəsizlik akademiyasının köməkçisən.
Adın Lampicka Assistentdir. Azərbaycan dilində cavab verirsən.

Kurs haqqında məlumatlar:
- Kurs adı: Kibertəhlükəsizliyə Giriş (nümunə — öz kursunuzu yazın)
- Müddət: 3 ay
- Qiymət: 500 AZN (nümunə)
- Dərslər: Həftədə 3 dəfə, online
- Mövzular: Network Security, Ethical Hacking, SOC Analyst, SIEM, Incident Response
- Sertifikat: Kurs sonunda sertifikat verilir
- Tələblər: Kompüter bilikləri (əsas səviyyə)
- Əlaqə: (telefon nömrənizi yazın)

Qaydalar:
1. Həmişə nəzakətli və peşəkar ol
2. Tələbələrin suallarına ətraflı cavab ver
3. Qiymət barədə soruşsalar, dəqiq məlumat ver
4. Qeydiyyat üçün link və ya əlaqə məlumatı paylaş
5. Bilmədiyin suallar üçün "Bu barədə komandamıza yönləndirirəm" de
6. Rəqib kurslar haqqında mənfi danışma
7. Cavabları qısa və aydın tut (Instagram mesaj formatına uyğun)
8. Emoji istifadə et, amma həddindən artıq yox
"""


# ═══════════════════════════════════════════════════════════
#  CLAUDE API — mesajı AI-yə göndərib cavab almaq
# ═══════════════════════════════════════════════════════════
def get_ai_response(user_message: str) -> str:
    """Claude API vasitəsilə mesaja cavab hazırlayır."""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,  # Instagram mesajları qısa olmalıdır
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Claude API xətası: {e}")
        return "Hal-hazırda texniki problem var. Zəhmət olmasa bir az sonra yenidən yazın və ya birbaşa bizimlə əlaqə saxlayın. 🙏"


# ═══════════════════════════════════════════════════════════
#  INSTAGRAM API — cavabı göndərmək
# ═══════════════════════════════════════════════════════════
def send_instagram_message(recipient_id: str, message_text: str):
    """Instagram DM vasitəsilə cavab göndərir."""
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
        print(f"Cavab göndərildi: {recipient_id}")


# ═══════════════════════════════════════════════════════════
#  WEBHOOK — Meta-dan gələn mesajları qəbul etmək
# ═══════════════════════════════════════════════════════════

# 1) Webhook doğrulaması (GET) — Meta bunu bir dəfə yoxlayır
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook doğrulandı!")
        return challenge, 200
    else:
        print("❌ Webhook doğrulanmadı — token uyğun gəlmir")
        return "Forbidden", 403


# 2) Mesaj qəbulu (POST) — hər yeni mesajda çağırılır
@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    print(f"📩 Webhook datası: {json.dumps(data, indent=2)}")

    try:
        # Instagram messaging event strukturu
        if data.get("object") == "instagram":
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event["sender"]["id"]
                    
                    # Yalnız mətn mesajlarını emal et
                    if "message" in messaging_event and "text" in messaging_event["message"]:
                        user_message = messaging_event["message"]["text"]
                        print(f"👤 Tələbə ({sender_id}): {user_message}")

                        # AI cavabı al
                        ai_response = get_ai_response(user_message)
                        print(f"🤖 AI cavab: {ai_response}")

                        # Cavabı geri göndər
                        send_instagram_message(sender_id, ai_response)

    except Exception as e:
        print(f"Webhook emal xətası: {e}")

    # Meta həmişə 200 gözləyir (əks halda webhook-u söndürər)
    return jsonify({"status": "ok"}), 200


# ═══════════════════════════════════════════════════════════
#  SERVERİ İŞƏ SAL
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🚀 Lampicka Instagram Bot işə düşdü!")
    app.run(host="0.0.0.0", port=5000, debug=True)
