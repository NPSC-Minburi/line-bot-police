from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    ImageSendMessage, LocationSendMessage
)
from sheet import add_person, update_location, search_person

app = Flask(__name__)

line_bot_api = LineBotApi("XZQfnLfuJztTHpij7sX+4N89Hn/hO1AGLiXwieEFPf47YZcOMVEHyNgdfUC8sEF23opgt2LCtDKS7uNSMQukHQb4Zf7jpzUcjK13LyJAbyiw+h9UATVBQ0QQhySaQoDXW8+uESgYCr4b7pE5pStCjQdB04t89/1O/w1cDnyilFU=")
handler = WebhookHandler("8c6da693d7fe0139694d880b5a8a18bd")

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

    # ➕ เพิ่มข้อมูล
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

    # 🗺️ เพิ่มโลเคชั่น
    elif text.startswith("@lat"):
        try:
            _, id_card, location = text.strip().split(" ", 2)
            ok = update_location(id_card, location)
            reply = "✅ เพิ่มโลเคชั่นแล้ว" if ok else "❌ ไม่พบเลขบัตรนี้"
        except:
            reply = "❌ ใช้รูปแบบ: @lat <เลขบัตร> <ละติจูด,ลองจิจูด>"

    # 🔍 ค้นหา
    elif text.startswith("#"):
        keyword = text.replace("#", "").strip()
        results = search_person(keyword)
        messages = []

        if results:
            for r in results:
                detail = (
                    f"👤 {r['name']}\n"
                    f"🆔 {r['id_card']}\n"
                    f"📞 {r['phone']}\n"
                    f"🏠 {r['address']}\n"
                    f"📍 {r['location'] or 'ยังไม่มี'}"
                )
                messages.append(TextSendMessage(text=detail))

                # 📷 รูปภาพบ้าน
                if r.get("photo_url") and r["photo_url"].startswith("http"):
                    messages.append(ImageSendMessage(
                        original_content_url=r["photo_url"],
                        preview_image_url=r["photo_url"]
                    ))

                # 🗺️ ส่งพิกัดแผนที่
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

    # 📜 แสดงเมนู
    elif text in ["เมนู", "ช่วยเหลือ", "วิธีใช้"]:
        reply = (
            "📌 คำสั่งใช้งานของบอท:\n\n"
            "➕ เพิ่มข้อมูล:\n"
            "@ ชื่อ,เลขบัตร,เบอร์โทร,ที่อยู่\n\n"
            "🗺️ เพิ่มโลเคชั่น:\n"
            "@lat เลขบัตร ละติจูด,ลองจิจูด\n\n"
            "🔍 ค้นหาข้อมูล:\n"
            "# ชื่อ หรือ # เลขบัตร\n\n"
            "📞 ตัวอย่าง:\n"
            "@ ไอบูม,4455,0886663333,บ้านริมคลอง\n"
            "@lat 4455 13.00000,100.6666\n"
            "# ไอบูม"
        )

    # 🔚 ส่งข้อความกลับ (สำหรับกรณีปกติ)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
