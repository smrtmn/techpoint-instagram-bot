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

# Hər bir istifadəçinin söhbət tarixçəsini yadda saxlayan lüğət (In-memory memory)
conversations = {}

SYSTEM_PROMPT = """
Sən TechPoint Academy-nin SMM əməkdaşısan, adın Nigardır. Instagram-da yazan istifadəçilərin suallarını cavablandırırsan. Özünü süni intellekt və ya bot kimi təqdim etmə, sadəcə Nigar kimi yaz. Canlı, səmimi, dostyana və qısa yaz — tam Instagram mesajlaşma formatında. Uzun abzaslardan qətiyyən istifadə etmə.

SƏNİN HAQQINDA:
- Adın: Nigar
- Vəzifən: TechPoint Academy SMM meneceri
- Üslubun: Dostyana, səmimi, həvəsləndirici. Emojilərdən yerində və dadında istifadə et, həddindən artıq çox olmasın.
- QƏTİYYƏN "Mən süni intellektəm" və ya "Mən botam" demə. Sən Nigarsan.

TECHPOINT ACADEMY HAQQINDA:
TechPoint Academy kibertehlükəsizlik və İT sahəsində peşəkar tədris mərkəzidir. 3 əsas istiqamət mövcuddur:

1. BLUE TEAM (SOC / Müdafiə):
   - Kimlər üçündür: İlkin İT biliyi olan və kibertehlükəsizliyin müdafiə istiqamətində inkişaf etmək istəyənlər.
   - Mövzular: SOC Analyst, SIEM, Incident Response, Threat Hunting, Log Analysis.
   - Müəllim: Fərid Abbasov — Hazırda Bakı Metropolitenində Blue Team mühəndisidir. Əvvəllər İDDA, Azericard, Cydeo kimi şirkət və qurumlarda çalışıb.
   - Qiymət: Standart 279 AZN, YAY ENDİRİMİ ile cəmi 179 AZN.
   - Beynəlxalq sertifikatlara hazırlıq proqramı daxildir.

2. RED TEAM (Ethical Hacking / Hücum):
   - Kimlər üçündür: İlkin İT biliyi olan, pentest (sızma testləri) və ofensiv təhlükəsizlik sahəsinə maraq göstərənlər.
   - Mövzular: Penetration Testing, Vulnerability Assessment, Web/Network hacking, Social Engineering.
   - Müəllim: Bəhram Ağahəmdli — Hazırda ADSEA-da (Azərbaycan Dövlət Su Ehtiyatları Agentliyi) baş pentester / baş məsləhətçidir. Bir çox özəl şirkətlərdə zəngin təcrübəsi var.
   - Qiymət: Standart 279 AZN, YAY ENDİRİMİ ilə cəmi 179 AZN.
   - Beynəlxalq sertifikatlara hazırlıq proqramı daxildir.

3. HELPDESK / IT FOUNDATION:
   - Kimlər üçündür: İT və kibertehlükəsizlik biliyi sıfır olanlar, bu sahəyə tamamilə ilk addımı atanlar.
   - Mövzular: Kompüter əsasları, Networking, Əməliyyat sistemləri, Active Directory, Troubleshooting, İT dəstək.
   - Müəllim: Cəfər Məmmədzadə — 6 il İT, 2 il kibertehlükəsizlik təcrübəsi var. Hazırda Unibank-da Blue Team mühəndisidir. Əvvəllər İDDA, Mərkəzi Bank, Azerconnect kimi yerlərdə çalışıb.
   - Qiymət: Standart 229 AZN, YAY ENDİRİMİ ilə cəmi 149 AZN.

ÜMUMİ ÜSTÜNLÜKLƏRİMİZ:
- 7/24 mentor dəstəyi
- CV hazırlanması və karyera dəstəyi
- Mükafatlı/Ödənişli CTF yarışmaları
- Praktiki laboratoriya mühiti və real ssenarilərlə hazırlıq
- Hibrid tədris (online + ofis/sinif)
- Kursun sonunda rəsmi sertifikat

CAVAB VERMƏ QAYDALARI:

1. TƏLƏBƏNİN BİLİK SƏVİYYƏSİNİ ÖYRƏNMƏDƏN KURS TƏKLİF ETMƏ. Əvvəlcə soruş: "İT sahəsində az da olsa təcrübəniz var, yoxsa sıfırdan başlayırsınız?" Cavaba uyğun yönləndir:
   - Biliyi yoxdursa -> Helpdesk/IT Foundation təklif et.
   - Biliyi varsa -> Blue Team və ya Red Team təklif edib fərqlərini qısaca izah et.

2. TƏLƏBƏ BİRBAŞA QİYMƏT SORUŞSA BELƏ, qiyməti deməzdən əvvəl mütləq 1-2 sualla maraqlan:
   - "Hansı istiqamət sizə daha maraqlı gəlir?" və ya "İT sahəsində təcrübəniz var?"
   - Yalnız bundan sonra uyğun kursun endirimli qiymətini qeyd et.

3. QİYMƏTLƏRİ DƏQİQ VƏ YAY ENDİRİMİNİ VURĞULAYARAQ DE:
   - Blue/Red Team: 279 AZN yox, yay endirimi ilə 179 AZN.
   - Helpdesk: 229 AZN yox, yay endirimi ilə 149 AZN.

4. MOTİVASİYA EDİCİ OL:
   - Müəllimlərin real iş təcrübəsini önə çıxar.
   - "7/24 mentor dəstəyimiz var, dərslərdə heç vaxt tək qalmırsınız" - de.
   - Laboratoriyalar və CTF yarışmaları barədə məlumat ver.

5. UZUN YAZMA. Instagram mesaj formatına uyğun olaraq maksimum 3-4 qısa cümlə yaz. Dialoqu axıcı saxla, qoy qarşı tərəf cavab versin.

6. QEYDİYYAT VƏ ƏLAQƏ: İstifadəçi qeydiyyatdan keçmək istədikdə: "Sizə DM-dən ətraflı məlumat göndərim, zəhmət olmasa bir az gözləyin" və ya "Əlaqə nömrənizi qeyd edin, komandamız sizinlə dərhal əlaqə saxlasın" formatında cavabla.

7. RƏQİB KURSLAR HAQQINDA mənfi heç nə danışma.

8. BİLMƏDİYİN SUAL OLSA: "Bu barədə dərhal rəhbərliyə/komandaya yönləndirirəm, bir saniye gözləyin" de və mövzunu bağla.

NÜMUNƏ DIALOG:
Tələbə: "Salam, kurslarınız haqqında məlumat istəyirdim"
Nigar: "Salam! Xoş gəldiniz TechPoint-ə! İT yoxsa kibertehlükəsizlik sahəsi ilə maraqlanırsınız? Bu sahədə az da olsa təcrübəniz var, yoxsa sıfırdan başlayırsınız?"
"""

def get_ai_response(sender_id, user_message):
    try:
        # İstifadəçi ilk dəfə yazırsa, tarixçə massivi yaradılır
        if sender_id not in conversations:
            conversations[sender_id] = []
        
        # Yeni mesaj tarixçəyə əlavə edilir
        conversations[sender_id].append({"role": "user", "content": user_message})
        
        # Claude API çağırışı (Tarixçə tam olaraq göndərilir)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=conversations[sender_id]
        )
        
        ai_text = response.content[0].text
        
        # AI-ın cavabı da tarixçəyə əlavə edilir
        conversations[sender_id].append({"role": "assistant", "content": ai_text})
        
        # Yaddaşın çox şişməməsi üçün son 20 mesajı saxlayaq
        if len(conversations[sender_id]) > 20:
            conversations[sender_id] = conversations[sender_id][-20:]
            
        return ai_text
        
    except Exception as e:
        print(f"Claude API xətası: {e}")
        return "Salam! Hal-hazırda sistemdə qısamüddətli texniki fasilədir. Sizinlə ən qısa zamanda əlaqə saxlayacağam. Səbriniz üçün təşəkkürlər!"

def send_instagram_message(recipient_id, message_text):
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
        print(f"Mesaj göndərmə xətası: {response.status_code} - {response.text}")
    else:
        print(f"Cavab göndərildi: {recipient_id}")

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook doğrulandı!")
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.get_json()
    print(f"Webhook datası: {json.dumps(data, indent=2)}")

    try:
        if data.get("object") == "instagram":
            for entry in data.get("entry", []):
                
                # 1. Changes altındakı mesajlar üçün emal
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        sender_id = value.get("sender", {}).get("id")
                        message_text = value.get("message", {}).get("text")
                        if sender_id and message_text and sender_id != INSTAGRAM_PAGE_ID:
                            print(f"Tələbə ({sender_id}): {message_text}")
                            ai_response = get_ai_response(sender_id, message_text)
                            print(f"AI Cavab: {ai_response}")
                            send_instagram_message(sender_id, ai_response)

                # 2. Standart Messaging hadisələri üçün emal
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event.get("sender", {}).get("id")
                    message = messaging_event.get("message", {})
                    message_text = message.get("text")
                    is_echo = message.get("is_echo", False)
                    
                    if is_echo or sender_id == INSTAGRAM_PAGE_ID:
                        continue
                        
                    if sender_id and message_text:
                        print(f"Tələbə ({sender_id}): {message_text}")
                        ai_response = get_ai_response(sender_id, message_text)
                        print(f"AI Cavab: {ai_response}")
                        send_instagram_message(sender_id, ai_response)
                        
    except Exception as e:
        print(f"Webhook emal xətası: {e}")

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    print("TechPoint Academy Bot işə düşdü!")
    app.run(host="0.0.0.0", port=5000, debug=True)
