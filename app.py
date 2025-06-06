from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage,
    TextSendMessage, ImageSendMessage, LocationSendMessage
)
from sheet import (
    add_person, update_location, search_person,
    update_case_info, update_note_type, check_duplicate_id, update_photo_url
)
import firebase_admin
from firebase_admin import credentials, storage
import os

# Initialize Firebase
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'linebot-storage.appspot.com'
})

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

# === Upload Image to Firebase ===
def upload_to_firebase(image_bytes, filename):
    bucket = storage.bucket()
    blob = bucket.blob(f"line_images/{filename}")
    blob.upload_from_string(image_bytes, content_type='image/jpeg')
    blob.make_public()
    return blob.public_url

# === Handle Image Upload ===
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    try:
        with open("photo_mapping.txt", "r") as f:
            mapping = f.read().strip().split(",")
        user_id, id_card = mapping
        if user_id != event.source.user_id:
            raise Exception("User ID mismatch")
    except:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ กรุณาส่งคำสั่ง @รูป เลขบัตร ก่อนส่งภาพ")
        )
        return

    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = b"".join([chunk for chunk in message_content.iter_content(None)])
    filename = f"{id_card}_{event.message.id}.jpg"
    image_url = upload_to_firebase(image_data, filename)

    update_photo_url(id_card, image_url)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"🖼️ อัปโหลดรูปภาพเรียบร้อยแล้ว: {image_url}")
    )

# === Handle Text Message ===
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    reply = "❌ คำสั่งไม่ถูกต้อง กรุณาพิมพ์ 'เมนู' เพื่อดูคำสั่งทั้งหมด"

    if text.startswith("@ "):
        try:
            parts = text.replace("@", "", 1).strip().split(",")
            if len(parts) != 4:
                reply = "📥 รูปแบบ: @ ชื่อ,เลขบัตร,เบอร์,ที่อยู่"
            else:
                name, id_card, phone, address = [p.strip() for p in parts]
                if check_duplicate_id(id_card):
                    reply = f"⚠️ มีข้อมูลของเลขบัตร {id_card} อยู่ในระบบแล้ว"
                else:
                    add_person(name, id_card, phone, address)
                    reply = f"✅ เพิ่มข้อมูลของ {name} เรียบร้อยแล้ว"
        except Exception as e:
            reply = f"⚠️ เกิดข้อผิดพลาด: {e}"

    elif text.startswith("@lat"):
        try:
            _, id_card, location = text.strip().split(" ", 2)
            ok = update_location(id_card, location)
            reply = "📍 เพิ่มโลเคชั่นสำเร็จ" if ok else "❌ ไม่พบเลขบัตรนี้"
        except:
            reply = "📍 รูปแบบ: @lat เลขบัตร ละติจูด,ลองจิจูด"

    elif text.startswith("@จับ"):
        try:
            parts = text.replace("@จับ", "", 1).strip().split(",")
            if len(parts) != 5:
                reply = "🚓 รูปแบบ: @จับ เลขบัตร,ข้อหา,สถานที่จับ,วันที่,ของกลาง"
            else:
                id_card, charge, place, date, evidence = [p.strip() for p in parts]
                ok = update_case_info(id_card, charge, place, date, evidence)
                reply = "✅ บันทึกข้อมูลการจับกุมแล้ว" if ok else "❌ ไม่พบเลขบัตรนี้"
        except Exception as e:
            reply = f"⚠️ เกิดข้อผิดพลาด: {e}"

    elif text.startswith("@โน้ต"):
        try:
            parts = text.replace("@โน้ต", "", 1).strip().split(",")
            if len(parts) != 3:
                reply = "🗒️ รูปแบบ: @โน้ต เลขบัตร,หมายเหตุ,ประเภท"
            else:
                id_card, note, data_type = [p.strip() for p in parts]
                ok = update_note_type(id_card, note, data_type)
                reply = "✅ บันทึกหมายเหตุสำเร็จ" if ok else "❌ ไม่พบเลขบัตรนี้"
        except Exception as e:
            reply = f"⚠️ เกิดข้อผิดพลาด: {e}"

    elif text.startswith("@รูป"):
        try:
            _, id_card = text.strip().split(" ", 1)
            with open("photo_mapping.txt", "w") as f:
                f.write(f"{event.source.user_id},{id_card.strip()}")
            reply = f"📸 ส่งภาพเข้ามาได้เลยสำหรับเลขบัตร {id_card.strip()}"
        except:
            reply = "📸 รูปแบบ: @รูป เลขบัตร"

    elif text.strip() == "#รายชื่อ":
        results = search_person("")
        if not results:
            reply = "📋 ยังไม่มีข้อมูลในระบบ"
        else:
            chunks = []
            chunk = ""
            for r in results:
                entry = f"👤 {r['name']}\n🏠 {r['address'] or '-'}\n\n"
                if len(chunk + entry) > 1500:
                    chunks.append(chunk)
                    chunk = entry
                else:
                    chunk += entry
            chunks.append(chunk)
            messages = [TextSendMessage(text=msg.strip()) for msg in chunks[:5]]
            line_bot_api.reply_message(event.reply_token, messages)
            return

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
📍 พิกัด: {r['location'] or 'ยังไม่มี'}
⚖️ ข้อหา: {r['charge'] or '-'}
🚔 สถานที่จับ: {r['arrest_place'] or '-'}
📆 วันที่จับ: {r['arrest_date'] or '-'}
🧾 ของกลาง: {r['evidence'] or '-'}
🗒️ หมายเหตุ: {r.get('note', '-') or '-'}
📂 ประเภท: {r.get('data_type', '-') or '-'}"""
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

            line_bot_api.reply_message(event.reply_token, messages[:5])
            return
        else:
            reply = "❌ ไม่พบข้อมูลที่ค้นหา"

    elif text in ["เมนู", "menu", "help"]:
        reply = (
            "📌 คำสั่งใช้งานของบอท:\n\n"
            "➕ เพิ่มข้อมูล:\n@ ชื่อ,เลขบัตร,เบอร์,ที่อยู่\n\n"
            "📍 เพิ่มโลเคชั่น:\n@lat เลขบัตร ละติจูด,ลองจิจูด\n\n"
            "🚓 เพิ่มข้อมูลจับกุม:\n@จับ เลขบัตร,ข้อหา,สถานที่จับ,วันที่จับ,ของกลาง\n\n"
            "🗒️ เพิ่มหมายเหตุ/ประเภท:\n@โน้ต เลขบัตร,หมายเหตุ,ประเภท\n\n"
            "🖼️ ส่งรูปภาพ:\n@รูป เลขบัตร แล้วตามด้วยภาพ\n\n"
            "🔍 ค้นหาข้อมูล:\n#ชื่อ หรือ #เลขบัตร หรือ #ที่อยู่\n\n"
            "📋 แสดงรายชื่อทั้งหมด:\n#รายชื่อ"
        )

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
