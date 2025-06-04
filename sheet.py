import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("key.json", scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1Dl_kjZd8zoVQBiA8C7e5o3oLglo_SLKojC9ONlo5Eyk").sheet1

def add_person(name, id_card, phone, address):
    sheet.append_row([name, id_card, phone, address, "", "", "", "", "", ""])

def update_location(id_card, location):
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        row_id = str(row.get("id_card", "")).strip()
        if str(id_card).strip() == row_id:
            sheet.update_cell(i, 5, location)
            return True
    return False

def update_case_info(id_card, charge, arrest_place, arrest_date, evidence):
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        row_id = str(row.get("id_card", "")).strip()
        if str(id_card).strip() == row_id:
            sheet.update_cell(i, 7, charge)
            sheet.update_cell(i, 8, arrest_place)
            sheet.update_cell(i, 9, arrest_date)
            sheet.update_cell(i, 10, evidence)
            return True
    return False

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
                "charge": str(row.get("charge", "")).strip(),
                "arrest_place": str(row.get("arrest_place", "")).strip(),
                "arrest_date": str(row.get("arrest_date", "")).strip(),
                "evidence": str(row.get("evidence", "")).strip(),
                "photo_url": str(row.get("photo_url", "")).strip()
            })
    return results
