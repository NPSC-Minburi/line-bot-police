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
    reply = "Invalid command format."

    if text.startswith("@ "):
        try:
            parts = text.replace("@", "", 1).strip().split(",")
            if len(parts) != 4:
                reply = "Format: @ Name,ID,Phone,Address"
            else:
                name, id_card, phone, address = [p.strip() for p in parts]
                add_person(name, id_card, phone, address)
                reply = f"Added {name} successfully"
        except Exception as e:
            reply = f"Error: {e}"

    elif text.startswith("@lat"):
        try:
            _, id_card, location = text.strip().split(" ", 2)
            ok = update_location(id_card, location)
            reply = "Location updated" if ok else "ID not found"
        except:
            reply = "Use format: @lat ID latitude,longitude"

    elif text.startswith("@จับ"):
        try:
            parts = text.replace("@จับ", "", 1).strip().split(",")
            if len(parts) != 5:
                reply = "Format: @จับ ID,Charge,Place,Date,Evidence"
            else:
                id_card, charge, place, date, evidence = [p.strip() for p in parts]
                ok = update_case_info(id_card, charge, place, date, evidence)
                reply = "Arrest record updated" if ok else "ID not found"
        except Exception as e:
            reply = f"Error: {e}"

    elif text.strip() == "#รายชื่อ":
        results = search_person("")
        if not results:
            reply = "No data available."
        else:
            chunks = []
            chunk = ""
            for r in results:
               entry = (
    f"Name: {r['name']}\n"
    f"Address: {r['address'] or '-'}\n\n"
)

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
                detail = f"""Name: {r['name']}
ID: {r['id_card']}
Phone: {r['phone']}
Address: {r['address']}
Location: {r['location'] or 'None'}
Charge: {r['charge'] or '-'}
Place: {r['arrest_place'] or '-'}
Date: {r['arrest_date'] or '-'}
Evidence: {r['evidence'] or '-'}"""
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
                            title=f"Location of {r['name']}",
                            address=r["address"],
                            latitude=lat,
                            longitude=lng
                        ))
                    except:
                        messages.append(TextSendMessage(text="Invalid coordinates."))

            line_bot_api.reply_message(event.reply_token, messages[:5])
            return
        else:
            reply = "No matching records found."

    elif text in ["เมนู", "menu", "help"]:
        reply = ("Bot Command Menu:

"
                 "@ ชื่อ,เลขบัตร,เบอร์,ที่อยู่
"
                 "@lat เลขบัตร latitude,longitude
"
                 "@จับ เลขบัตร,ข้อหา,สถานที่จับกุม,วันที่จับกุม,ของกลาง
"
                 "#keyword or #ID
"
                 "#รายชื่อ")

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
