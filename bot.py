import os
import time
import sqlite3
import requests
import threading
from datetime import datetime, timezone, timedelta
import anthropic
from requests.exceptions import ConnectionError, Timeout

# ================= 1. SOZLAMALAR =================
GREEN_ID_INSTANCE = "710722747557"
GREEN_API_TOKEN = "324a0b855b7e4d57889d907054e0bf1a830b756817ab4e7fac"
CLAUDE_API_KEY = "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"

MY_ALERT_PHONE = "998917890666@c.us"
GREEN_BASE_URL = f"https://api.green-api.com/waInstance{GREEN_ID_INSTANCE}"

claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
ISRAEL_TZ = timezone(timedelta(hours=3))

WORK_HOURS = {
    6: (9, 18),  # Yakshanba
    0: (9, 18),  # Dushanba
    1: (9, 18),  # Seshanba
    2: (9, 18),  # Chorshanba
    3: (9, 18),  # Payshanba
    4: None,     # Juma
    5: None      # Shanba
}

PHONE_NUMBERS = [
    "972526401194", "972552970707", "972508899151", "972504300423", "97235059998",
    "972522914610", "972523222219", "972529284421", "972747888555", "972505340092",
    "97235505502", "972505288727", "972553005050", "972525277776", "972523176689",
    "972587333330", "972523278069", "972525681068", "97286750915", "972529462243",
    "97237616111", "97239235540", "972505212016", "972529599950", "97288671889",
    "97288671890", "972733986770", "972505498423", "97239675955", "972543334403",
    "972544360033", "972545449542", "972765399500", "972522444315", "972525244400",
    "97236377388", "972505338080", "972529248354", "972747491901", "972546565295",
    "972542699763", "972524279226", "972509560915", "972522443130", "97286988095",
    "972522429336", "972545970870", "972552222280", "972542887733", "972547645067",
    "972503915171", "972548021887", "97288699177", "972522298298", "972527723614",
    "972506698285", "972504420119", "972508864685", "972528862668", "97289257979",
    "972523414760", "972527977138", "972544548399", "972509011696", "972523444985",
    "972524558844", "972722223378", "972546623233", "972528870282", "972772054762",
    "972526919292", "972544726855", "972546929122", "972525381466", "97237549592",
    "972546477110", "972504555636", "972529462212", "972777441155", "97289224848",
    "97286767892", "97235138201", "97235138203", "972536233153", "972507368366",
    "972505389107", "972505410812", "972507509334", "972774060485", "972532311106",
    "972733987700", "972505225838", "972528903311", "972524410222", "972528226555",
    "97286680818", "972546511644", "972508675077", "972546455455", "97286201777",
    "972548167160", "97299549888", "972523000666", "972546114729", "97239422260",
    "972525451018", "972545501400", "972524428429", "972526009505", "972542507704",
    "972502744439", "97235383667", "972525551275", "972509910241", "972544890145",
    "97236365777", "972525524048", "972549133451", "97286277766", "972525582258",
    "972547703666", "972525887608", "972733246048", "972508885888", "972505275384",
    "972544733746", "972548800600", "972505999331", "97249999978", "972522380674",
    "972529214043", "972523642996", "972505111812", "97246282080", "972547000992",
    "972523354400", "97229977260", "972547045843", "97246217025", "97246203633",
    "972539319799", "972544550383", "972733266892", "972522969057", "972547755897",
    "972507924168", "972503200591", "972546729300", "972505980506", "972529274890",
    "972542333111", "972526588860", "972505267080", "97299543765", "972522352793",
    "972508533694", "97237776044", "972543323332", "97236525821", "972542373159",
    "972502799260", "972509019015", "972535923444", "97236301089", "972539229394",
    "97286654663", "97286639656", "972528662935", "972524294000", "972722222322",
    "972765300333", "972584314441", "97239513667", "97297611022", "972525287531",
    "972502507414", "972546732608", "972526195558", "97236965404", "972545606037",
    "97288580881", "972543978763", "97237708177", "97237401780", "972549405805",
    "972528400637", "972547461239", "972545355455", "972506532300", "97286162030",
    "972546874362", "972526911370", "972536350005", "972528383941", "972522866666",
    "97286426288", "972547684103", "972549847774", "97239508286", "972547777014",
    "97252222238", "9725258335020", "972549922361", "972522939761", "972523552420",
    "972502166615", "97236879130", "972505696059", "972504300043", "972543975261",
    "972528150005", "972526070622", "972544861786", "972545608622", "972547202222",
    "97236500999", "972527261177", "972547836789", "972505331383", "97289516994",
    "972527433632", "97237974283", "972542529601", "97286138888", "972547381298",
    "972529415770", "972526711233", "972507435618", "972527022846"
]

# ================= 2. BAZA (SQLite) =================
def init_db():
    conn = sqlite3.connect("israel_outreach.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            phone TEXT PRIMARY KEY,
            first_sent_at TIMESTAMP,
            followup_sent_at TIMESTAMP,
            replied INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ================= 3. CLAUDE AI =================
def generate_initial_msg() -> str:
    prompt = """
    Write a short, highly professional cold outreach message in English for WhatsApp to an Israeli employer or HR manager.
    KEY DETAILS:
    - From: "Youth Globe" Private Employment Agency (Licensed Agency №818851).
    - We have extensive experience deploying qualified workforce FROM UZBEKISTAN to Israel and Europe.
    - Inquire politely if they have open workforce requirements.
    - Signature: Sherzod Eshmuradov, Director | WhatsApp: +972 55 507 3003 | youthglobe.uz
    Output ONLY the message text.
    """
    response = claude_client.messages.create(
        model="claude-sonnet-5",
        max_tokens=250,
        messages=[{"role": "user", "content": prompt}]
    )
    for block in response.content:
        if hasattr(block, 'text'):
            return block.text.strip()
    return str(response.content[0]).strip()

def generate_followup_msg() -> str:
    prompt = """
    Write a polite, 2-sentence follow-up WhatsApp message in English for an Israeli employer from Youth Globe Agency (License №818851) regarding workforce deployment from Uzbekistan. Ask for a brief introductory call.
    Signature: Sherzod Eshmuradov (+972 55 507 3003).
    Output ONLY the message text.
    """
    response = claude_client.messages.create(
        model="claude-sonnet-5",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    for block in response.content:
        if hasattr(block, 'text'):
            return block.text.strip()
    return str(response.content[0]).strip()

# ================= 4. WHATSAPP (90s TIMEOUT VA 4 URINISH) =================
def send_wa(chat_id: str, text: str, max_retries=4):
    url = f"{GREEN_BASE_URL}/sendMessage/{GREEN_API_TOKEN}"
    payload = {"chatId": chat_id, "message": text}
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(max_retries):
        try:
            # Timeout 90 soniyaga uzaytirildi (Render uchun xavfsiz)
            r = requests.post(url, json=payload, headers=headers, timeout=90)
            return r.json()
        except (ConnectionError, Timeout) as e:
            print(f"Ulanish vaqti tugadi ({chat_id}), qayta urinish ({attempt + 1}/{max_retries})...")
            if attempt < max_retries - 1:
                time.sleep(20)
            else:
                print(f"Serverga ulanib bo'lmadi ({chat_id}), bu raqam tashlab yuborildi.")
                return None
        except Exception as e:
            print(f"Kutilmagan xatolik ({chat_id}): {e}")
            return None

def is_working_time():
    now = datetime.now(ISRAEL_TZ)
    rule = WORK_HOURS.get(now.weekday())
    if rule is None:
        return False, "Dam olish kuni"
    start, end = rule
    if start <= now.hour < end:
        return True, "Ish vaqti"
    return False, "Ish vaqti emas"

def wait_for_working_time():
    while True:
        ok, status = is_working_time()
        if ok:
            break
        print(f"[Kutish] {status}. 10 daqiqadan so'ng tekshiriladi...")
        time.sleep(600)

# ================= 5. YUBORISH =================
def broadcast_worker():
    print("[Kampaniya] Xat yuborish boshlandi...")
    while True:
        try:
            wait_for_working_time()
            conn = sqlite3.connect("israel_outreach.db")
            c = conn.cursor()

            three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""
                SELECT phone FROM contacts 
                WHERE first_sent_at <= ? AND followup_sent_at IS NULL AND replied = 0 
                LIMIT 1
            """, (three_days_ago,))
            followup_candidate = c.fetchone()

            if followup_candidate:
                phone = followup_candidate[0]
                chat_id = f"{phone}@c.us"
                msg = generate_followup_msg()
                print(f"\n[Follow-up 3 kun]: {chat_id}")
                send_wa(chat_id, msg)
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("UPDATE contacts SET followup_sent_at = ? WHERE phone = ?", (now_str, phone))
                conn.commit()
                conn.close()
                time.sleep(900)
                continue

            c.execute("SELECT phone FROM contacts WHERE first_sent_at IS NOT NULL")
            already_sent = {row[0] for row in c.fetchall()}

            next_number = None
            for num in PHONE_NUMBERS:
                clean_num = num.replace("+", "").strip()
                if clean_num not in already_sent:
                    next_number = clean_num
                    break

            if next_number:
                chat_id = f"{next_number}@c.us"
                msg = generate_initial_msg()
                print(f"\n[Yuborilmoqda]: {chat_id}")
                send_wa(chat_id, msg)
                
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("INSERT OR REPLACE INTO contacts (phone, first_sent_at, replied) VALUES (?, ?, 0)", (next_number, now_str))
                conn.commit()
                conn.close()
                
                print("Muvaffaqiyatli yuborildi. 15 daqiqa kutilmoqda...")
                time.sleep(900)
            else:
                conn.close()
                print("[Tugadi] Barcha raqamlarga yuborildi.")
                time.sleep(600)

        except Exception as e:
            print(f"[Xatolik]: {e}")
            time.sleep(60)

# ================= 6. TINGLOVCHI =================
def listener_worker():
    receive_url = f"{GREEN_BASE_URL}/receiveNotification/{GREEN_API_TOKEN}"
    delete_url = f"{GREEN_BASE_URL}/deleteNotification/{GREEN_API_TOKEN}/"
    print("[Tinglovchi] Ishga tushdi...")

    while True:
        try:
            res = requests.get(receive_url, timeout=30)
            data = res.json()
            if data and "receiptId" in data:
                receipt_id = data["receiptId"]
                body = data.get("body", {})

                if body.get("typeWebhook") == "incomingMessageReceived":
                    sender_chat = body.get("senderData", {}).get("chatId", "")
                    sender_phone = sender_chat.replace("@c.us", "")
                    msg_data = body.get("messageData", {})

                    if msg_data.get("typeMessage") == "textMessage":
                        user_text = msg_data.get("textMessageData", {}).get("textMessage", "")
                        print(f"\n[JAVOB KELDI] {sender_chat}: {user_text}")

                        conn = sqlite3.connect("israel_outreach.db")
                        c = conn.cursor()
                        c.execute("UPDATE contacts SET replied = 1 WHERE phone = ?", (sender_phone,))
                        conn.commit()
                        conn.close()

                        analysis_prompt = f"""
                        Analyze this message from an Israeli employer: "{user_text}".
                        Does the user show interest in recruiting workers, request a meeting, call, details, or express interest?
                        Reply ONLY 'YES' or 'NO'.
                        """
                        analysis_res = claude_client.messages.create(
                            model="claude-sonnet-5",
                            max_tokens=10,
                            messages=[{"role": "user", "content": analysis_prompt}]
                        )
                        analysis = ""
                        for block in analysis_res.content:
                            if hasattr(block, 'text'):
                                analysis = block.text.strip()
                                break

                        if "YES" in analysis.upper():
                            alert_msg = (f"🔥 DIQQAT! ISROIL ISH BERUVCHISI UCHRASHUV / HAMKORLIK SO'RADI!\n\n"
                                         f"Raqam: +{sender_phone}\n"
                                         f"Xabar: {user_text}\n"
                                         f"Darhol bog'laning!")
                            send_wa(MY_ALERT_PHONE, alert_msg)

                        reply_prompt = f"""
                        You are the senior representative of 'Youth Globe' Licensed Employment Agency.
                        An Israeli employer replied: "{user_text}".
                        Detect the language of their message and respond FLUENTLY in that EXACT SAME language.
                        If they asked for a meeting, confirm that Director Sherzod Eshmuradov will connect via Google Meet / Zoom.
                        Output ONLY the reply message text.
                        """
                        reply_res = claude_client.messages.create(
                            model="claude-sonnet-5",
                            max_tokens=300,
                            messages=[{"role": "user", "content": reply_prompt}]
                        )
                        ai_reply = ""
                        for block in reply_res.content:
                            if hasattr(block, 'text'):
                                ai_reply = block.text.strip()
                                break

                        send_wa(sender_chat, ai_reply)

                requests.delete(f"{delete_url}{receipt_id}")
            time.sleep(1)
        except Exception:
            time.sleep(3)

# ================= 7. MAIN =================
if __name__ == "__main__":
    t1 = threading.Thread(target=broadcast_worker, daemon=True)
    t2 = threading.Thread(target=listener_worker, daemon=True)

    t1.start()
    t2.start()

    print("\n✅ Bot muvaffaqiyatli ishga tushdi!")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nTo'xtatildi.")
