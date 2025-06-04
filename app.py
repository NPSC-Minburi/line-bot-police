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

@app.route("/ping")
def ping():
    return "pong"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text.strip()
    user_id = event.source.user_id

    if msg.startswith("@"):
        try:
            _, name, id_card, phone, address, location = msg.split("|")
            sheet.add_person(name, id_card, phone, address, location)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ เพิ่มข้อมูลเรียบร้อยแล้ว"))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ รูปแบบไม่ถูกต้อง กรุณาใช้ @ชื่อ|เลขบัตร|เบอร์|ที่อยู่|โลเคชั่น"))
    elif msg.startswith("@lat"):
        try:
            _, id_card, lat, lng = msg.split("|")
            sheet.update_location(id_card, f"{lat},{lng}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="📍 เพิ่ม location สำเร็จ"))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ รูปแบบไม่ถูกต้อง ใช้ @lat|เลขบัตร|lat|lng"))
    elif msg.startswith("@จับ"):
        try:
            _, id_card, charge, arrest_place, arrest_date, evidence = msg.split("|")
            sheet.update_case_info(id_card, charge, arrest_place, arrest_date, evidence)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ เพิ่มข้อมูลการจับกุมเรียบร้อยแล้ว"))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ รูปแบบไม่ถูกต้อง ใช้ @จับ|เลขบัตร|ข้อหา|สถานที่จับ|วันที่|ของกลาง"))
    elif msg.startswith("#"):
        keyword = msg[1:]
        results = sheet.search_person(keyword)
        if results:
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
                msgs = [TextSendMessage(text=reply)]
                if r["location"]:
                    lat, lng = r["location"].split(",")
                    msgs.append(LocationSendMessage(
                        title="📍 ตำแหน่งที่อยู่",
                        address=r["address"],
                        latitude=float(lat),
                        longitude=float(lng)
                    ))
                line_bot_api.reply_message(event.reply_token, msgs)
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ไม่พบข้อมูลในระบบ"))
    else:
        help_text = """📌 คำสั่งใช้งาน:
@ชื่อ|เลขบัตร|เบอร์|ที่อยู่|โลเคชั่น ➕ เพิ่มข้อมูล
@lat|เลขบัตร|lat|lng ➕ เพิ่มพิกัด
@จับ|เลขบัตร|ข้อหา|สถานที่จับ|วันที่|ของกลาง ➕ เพิ่มข้อมูลการจับกุม
#คำค้นหา 🔍 ค้นหาข้อมูล
"""
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=help_text))

if __name__ == "__main__":


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
