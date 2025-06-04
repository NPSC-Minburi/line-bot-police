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
    text = event.message.text.strip()
    reply = "❌ คำสั่งไม่ถูกต้อง"

    if text.startswith("@ "):
        try:
            parts = text.replace("@", "", 1).strip().split(",")
            if len(parts) != 4:
                reply = "❌ รูปแบบ: @ ชื่อ,เลขบัตร,เบอร์,ที่อยู่"
            else:
                name, id_card, phone, address = [p.strip() for p in parts]
                add_person(name, id_card, phone, address)
                reply = f"✅ เพิ่มข้อมูลของ {name} เรียบร้อย"
        except Exception as e:
            reply = f"❌ เกิดข้อผิดพลาด: {e}"

    elif text.startswith("@lat"):
        try:
            _, id_card, location = text.strip().split(" ", 2)
            ok = update_location(id_card, location)
            reply = "✅ เพิ่มโลเคชั่นแล้ว" if ok else "❌ ไม่พบเลขบัตรนี้"
        except:
            reply = "❌ ใช้รูปแบบ: @lat <เลขบัตร> <ละติจูด,ลองจิจูด>"

    elif text.startswith("@จับ"):
        try:
            parts = text.replace("@จับ", "", 1).strip().split(",")
            if len(parts) != 5:
                reply = "❌ รูปแบบ: @จับ เลขบัตร,ข้อหา,สถานที่จับกุม,วันที่,ของกลาง"
            else:
                id_card, charge, place, date, evidence = [p.strip() for p in parts]
                ok = update_case_info(id_card, charge, place, date, evidence)
                reply = "✅ บันทึกข้อมูลการจับกุมแล้ว" if ok else "❌ ไม่พบเลขบัตรนี้"
        except Exception as e:
            reply = f"❌ เกิดข้อผิดพลาด: {e}"

    elif text.startswith("#"):
        keyword = text.replace("#", "").strip()
        results = search_person(keyword)
        messages = []

        if results:
            for r in results:
                detail = f"""👤 {r['name']}
🆔 {r['id_card']}
📞 {r['phone']}
🏠 {r['address']}
📍 {r['location'] or 'ยังไม่มี'}
🚓 ข้อหา: {r['charge'] or '-'}
📍 สถานที่จับ: {r['arrest_place'] or '-'}
📅 วันที่จับ: {r['arrest_date'] or '-'}
🧾 ของกลาง: {r['evidence'] or '-'}"""
                messages.append(TextSendMessage(text=detail))

                if r.get("photo_url") and r["photo_url"].startswith("http"):
                    messages.append(ImageSendMessage(
                        original_content_url=r["photo_url"],
                        preview_image_url=r["photo_url"]
                    ))

                if r["location"]:
                    try:
                        lat, lng = map(float, r["location"].split(","))
                        messages.append(LocationSendMessage(
                            title=f"📍 ตำแหน่งของ {r['name']}",
                            address=r["address"],
                            latitude=lat,
                            longitude=lng
                        ))
                    except:
                        messages.append(TextSendMessage(text="⚠️ พิกัดไม่ถูกต้อง"))

            line_bot_api.reply_message(event.reply_token, messages)
            return
        else:
            reply = "ไม่พบข้อมูล"

    elif text in ["เมนู", "ช่วยเหลือ", "วิธีใช้"]:
        reply = """📌 คำสั่งใช้งานของบอท:
เพิ่มชื่อ
@ ชื่อ,เลขบัตร,เบอร์,ที่อยู่
เพิ่มตำแหน่ง Location
@lat เลขบัตร ละติจูด,ลองจิจูด
เพิ่มข้อหาและของกลาง
@จับ เลขบัตร,ข้อหา,สถานที่จับกุม,วันที่,ของกลาง
ค้นหา
# ชื่อ หรือ # เลขบัตร"""

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
