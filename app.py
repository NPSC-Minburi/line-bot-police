from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    ImageSendMessage, LocationSendMessage
)
from sheet import (
    add_person, update_location, search_person,
    update_case_info
)

app = Flask(__name__)

line_bot_api = LineBotApi("XZQfnLfuJztTHpij7sX+4N89Hn/hO1AGLiXwieEFPf47YZcOMVEHyNgdfUC8sEF23opgt2LCtDKS7uNSMQukHQb4Zf7jpzUcjK13LyJAbyiw+h9UATVBQ0QQhySaQoDXW8+uESgYCr4b7pE5pStCjQdB04t89/1O/w1cDnyilFU=")
handler = WebhookHandler("8c6da693d7fe0139694d880b5a8a18bd")

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Error:", e)
        abort(400)
    return "OK"

@app.route("/ping")
def ping():
    return "pong"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()

    if text.startswith("@จับ"):
        parts = text[3:].split("|")
        if len(parts) != 9:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ รูปแบบคำสั่งผิด
โปรดใช้: @จับ ชื่อ|เลขบัตร|เบอร์โทร|ที่อยู่|โลเคชั่น|ข้อหา|สถานที่จับ|วันที่จับ|ของกลาง"))
            return
        name, id_card, phone, address, location, charge, arrest_place, arrest_date, evidence = [p.strip() for p in parts]
        sheet.append_person({
            "name": name,
            "id_card": id_card,
            "phone": phone,
            "address": address,
            "location": location,
            "charge": charge,
            "arrest_place": arrest_place,
            "arrest_date": arrest_date,
            "evidence": evidence
        })
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ เพิ่มข้อมูลเรียบร้อยแล้ว"))

    elif text.startswith("#"):
        keyword = text[1:].strip()
        results = sheet.search_person(keyword)
        if not results:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ ไม่พบข้อมูล"))
            return

        for r in results:
            reply = f"""👤 {r['name']}
🪪 เลขบัตร: {r['id_card']}
📞 เบอร์โทร: {r['phone']}
🏠 ที่อยู่: {r['address']}
📍 โลเคชั่น: {r['location']}
🧾 ข้อหา: {r['charge']}
📍 สถานที่จับกุม: {r['arrest_place']}
📅 วันที่จับ: {r['arrest_date']}
📦 ของกลาง: {r['evidence']}"""

            messages = [TextSendMessage(text=reply)]

            # ถ้ามีโลเคชั่น
            if r["location"].startswith("http"):
                loc_parts = r["location"].split("@")[-1].split(",")
                if len(loc_parts) >= 2:
                    lat = float(loc_parts[0])
                    lng = float(loc_parts[1])
                    messages.append(LocationSendMessage(
                        title="จุดที่ถูกจับ",
                        address=r["address"],
                        latitude=lat,
                        longitude=lng
                    ))

            line_bot_api.reply_message(event.reply_token, messages)

    else:
        menu = """📚 คำสั่งที่ใช้ได้:
🔹 เพิ่มข้อมูลจับกุม:
@จับ ชื่อ|เลขบัตร|เบอร์โทร|ที่อยู่|โลเคชั่น|ข้อหา|สถานที่จับ|วันที่จับ|ของกลาง

🔹 ค้นหาข้อมูล:
#คำค้นหา (เช่น #สมชาย)"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=menu))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
