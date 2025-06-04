import gspread
from oauth2client.service_account import ServiceAccountCredentials

# เชื่อมต่อกับ Google Sheet
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
client = gspread.authorize(creds)

# เปิด Sheet โดยใช้ Spreadsheet ID
sheet = client.open_by_key("1Dl_kjZd8zoVQBiA8C7e5o3oLglo_SLKojC9ONlo5Eyk").sheet1

# เพิ่มข้อมูลแถวใหม่
def add_person(name, id_card, phone, address):
    sheet.append_row([name, id_card, phone, address, ""])

# เพิ่มหรือแก้โลเคชั่น
def update_location(id_card, location):
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["id_card"] == id_card:
            sheet.update_cell(i, 5, location)
            return True
    return False

# ค้นหาตามชื่อหรือเลขบัตร
def search_person(keyword):
    records = sheet.get_all_records()
    results = []
    for row in records:
        name = str(row.get("name", "")).strip()
        id_card = str(row.get("id_card", "")).strip()
        if keyword in name or keyword in id_card:
            results.append({
                "name": name,
                "id_card": id_card,
                "phone": str(row.get("phone", "")).strip(),
                "address": str(row.get("address", "")).strip(),
                "location": str(row.get("location", "")).strip(),
                "photo_url": str(row.get("photo_url", "")).strip()
            })
    return results

