import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1Dl_kjZd8zoVQBiA8C7e5o3oLglo_SLKojC9ONlo5Eyk").sheet1

def check_duplicate_id(id_card):
    records = sheet.get_all_records()
    for row in records:
        if str(row.get("id_card", "")).strip() == str(id_card).strip():
            return True
    return False

def add_person(name, id_card, phone, address):
    sheet.append_row([name, id_card, phone, address, "", "", "", "", "", "", "", ""])

def update_location(id_card, location):
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if str(id_card).strip() == str(row.get("id_card", "")).strip():
            sheet.update_cell(i, 5, location)
            return True
    return False

def update_case_info(id_card, charge, arrest_place, arrest_date, evidence):
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if str(id_card).strip() == str(row.get("id_card", "")).strip():
            sheet.update_cell(i, 7, charge)
            sheet.update_cell(i, 8, arrest_place)
            sheet.update_cell(i, 9, arrest_date)
            sheet.update_cell(i, 10, evidence)
            return True
    return False

def update_note_type(id_card, note, data_type):
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if str(id_card).strip() == str(row.get("id_card", "")).strip():
            sheet.update_cell(i, 11, note)
            sheet.update_cell(i, 12, data_type)
            return True
    return False

def update_photo_url(id_card, photo_url):
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if str(id_card).strip() == str(row.get("id_card", "")).strip():
            sheet.update_cell(i, 6, photo_url)
            return True
    return False

def search_person(keyword):
    records = sheet.get_all_records()
    results = []
    for row in records:
        name = str(row.get("name", "")).strip()
        id_card = str(row.get("id_card", "")).strip()
        address = str(row.get("address", "")).strip()
        if keyword in name or keyword in id_card or keyword in address:
            results.append({
                "name": name,
                "id_card": id_card,
                "phone": str(row.get("phone", "")).strip(),
                "address": address,
                "location": str(row.get("location", "")).strip(),
                "charge": str(row.get("charge", "")).strip(),
                "arrest_place": str(row.get("arrest_place", "")).strip(),
                "arrest_date": str(row.get("arrest_date", "")).strip(),
                "evidence": str(row.get("evidence", "")).strip(),
                "photo_url": str(row.get("photo_url", "")).strip(),
                "note": str(row.get("note", "")).strip(),
                "data_type": str(row.get("data_type", "")).strip(),
            })
    return results
