"""
Mitra Tours & Travel — Visitor Appointment System
Redesign: Attractive Mobile-First UI
Warna: #1BA0E2 #1494C6 #0D7FCC #F0F0F0 #ff5e1f #DEDEDE
"""

import streamlit as st
import requests, random, string, re
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="Kunjungan Sales — Mitra Tours",
    page_icon="📅",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CONFIG ─────────────────────────────────────────────────────────────────────
GAS_ENDPOINT    = "https://script.google.com/macros/s/AKfycbz78iwrv1FiIHqpqbA4dX6sQVzcfO4UodJ3BhW4bLH_7zLA_c4wMmXpuhHSGC5yiE6Pww/exec"
SHEET_ID        = "1AQz-w3sLjGVdOsneDmdTFHFW6Nx7Z337Kjw2zzqFoXI"
API_KEY         = "AIzaSyA1Mau8yZxao0MD5Mx_Dt027EuMbrUN9oo"
SHEET_NAME      = "Sheet1"
NOTIF_EMAIL     = "d4t4m1tr4@gmail.com"
SHEETS_READ_URL = (
    f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}"
    f"/values/{SHEET_NAME}?key={API_KEY}"
)

DATES = [
    {"key":"6 Mei 2026",  "label":"Selasa, 6 Mei 2026",  "day":"6",  "mon":"Mei"},
    {"key":"13 Mei 2026", "label":"Selasa, 13 Mei 2026", "day":"13", "mon":"Mei"},
    {"key":"20 Mei 2026", "label":"Selasa, 20 Mei 2026", "day":"20", "mon":"Mei"},
    {"key":"27 Mei 2026", "label":"Selasa, 27 Mei 2026", "day":"27", "mon":"Mei"},
    {"key":"2 Jun 2026",  "label":"Selasa, 2 Jun 2026",  "day":"2",  "mon":"Jun"},
    {"key":"9 Jun 2026",  "label":"Selasa, 9 Jun 2026",  "day":"9",  "mon":"Jun"},
    {"key":"16 Jun 2026", "label":"Selasa, 16 Jun 2026", "day":"16", "mon":"Jun"},
    {"key":"23 Jun 2026", "label":"Selasa, 23 Jun 2026", "day":"23", "mon":"Jun"},
    {"key":"30 Jun 2026", "label":"Selasa, 30 Jun 2026", "day":"30", "mon":"Jun"},
    {"key":"7 Jul 2026",  "label":"Selasa, 7 Jul 2026",  "day":"7",  "mon":"Jul"},
    {"key":"14 Jul 2026", "label":"Selasa, 14 Jul 2026", "day":"14", "mon":"Jul"},
    {"key":"21 Jul 2026", "label":"Selasa, 21 Jul 2026", "day":"21", "mon":"Jul"},
    {"key":"28 Jul 2026", "label":"Selasa, 28 Jul 2026", "day":"28", "mon":"Jul"},
    {"key":"4 Agt 2026",  "label":"Selasa, 4 Agt 2026",  "day":"4",  "mon":"Agt"},
    {"key":"11 Agt 2026", "label":"Selasa, 11 Agt 2026", "day":"11", "mon":"Agt"},
    {"key":"18 Agt 2026", "label":"Selasa, 18 Agt 2026", "day":"18", "mon":"Agt"},
    {"key":"25 Agt 2026", "label":"Selasa, 25 Agt 2026", "day":"25", "mon":"Agt"},
]

SESSIONS = [
    {"id":"P1","value":"09.00-10.00 WIB","label":"09.00 – 10.00 WIB","period":"Pagi"},
    {"id":"P2","value":"10.00-11.00 WIB","label":"10.00 – 11.00 WIB","period":"Pagi"},
    {"id":"S1","value":"13.30-14.30 WIB","label":"13.30 – 14.30 WIB","period":"Siang"},
]

HOTEL_BRANDS = [
    "",
    "Accor","Aman Resorts","Archipelago International","ARTOTEL Group",
    "Aryaduta","Ascott Limited","Azana Hotels","Banyan Group Limited",
    "Best Western Hotels","Cross Hotels & Resorts","Dafam Hotel Management",
    "Dusit International","Four Seasons Hotels and Resorts","Hilton Worldwide",
    "Horison Hotels Group","Hotel Indonesia Group","Hyatt Hotels Corporation",
    "IHG Hotels & Resorts","Jambuluwuk Hotels & Resorts","Jumeirah","Kempinski",
    "Mandarin Oriental Hotel Group","Marriott International","Meliá Hotels International",
    "Minor Hotels","Oberoi Group","Pan Pacific Hotels and Resorts",
    "Parador Hotels & Resorts","Radisson Hotel Group",
    "Santika Indonesia Hotels & Resorts","Shangri-La Hotels and Resorts",
    "Swiss-Belhotel International","The Ascott Limited",
    "Waringin Hospitality Hotel Group","Wyndham Hotels & Resorts",
    "Independen / Tidak Berantai","Lainnya",
]

TUJUAN_OPTIONS = [
    "Perkenalan Hotel",
    "Presentasi Produk / Fasilitas",
    "Corporate Rate / Contract Rate",
    "Promo / Special Offer",
    "Kerja Sama Partnership",
    "Follow Up Existing Business",
]

# ── DATA LAYER ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=20)
def _fetch_cached():
    try:
        r = requests.get(SHEETS_READ_URL, timeout=10)
        r.raise_for_status()
        rows = r.json().get("values", [])[1:]
        booked = {}
        for row in rows:
            while len(row) < 16:
                row.append("")
            if row[15].lower().strip() in ("ditolak","dibatalkan"):
                continue
            dk = re.sub(r"\s*\(.*?\)", "", row[11].strip()).strip()
            sv = row[12].strip()
            if dk and sv:
                key = f"{dk}|{sv}"
                booked[key] = booked.get(key, 0) + 1
        return booked, ""
    except Exception as e:
        return {}, str(e)

def fetch_booked():
    b, err = _fetch_cached()
    if err:
        st.toast(f"Gagal memuat jadwal: {err}", icon="⚠️")
    return b

def is_booked(b, dk, sv):
    return b.get(f"{dk}|{sv}", 0) >= 1

def get_alts(b, edk, esv, n=3):
    out = []
    for d in DATES:
        for s in SESSIONS:
            if d["key"] == edk and s["value"] == esv:
                continue
            if not is_booked(b, d["key"], s["value"]):
                out.append({
                    "date_key":   d["key"],
                    "date_label": d["label"],
                    "sess_value": s["value"],
                    "sess_label": s["label"],
                })
                if len(out) >= n:
                    return out
    return out

def gen_ref():
    return "SV-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=7))

def save_to_gas(payload):
    import json as _j
    payload["notifEmail"] = NOTIF_EMAIL
    headers = {"Content-Type": "application/json"}
    body    = _j.dumps(payload)
    ref     = payload.get("ref", "")
    try:
        resp = requests.post(GAS_ENDPOINT, data=body, headers=headers,
                             allow_redirects=True, timeout=30)
        raw = resp.text.strip()
        if raw.startswith("{"):
            r = _j.loads(raw)
            if r.get("success"):
                return True, r.get("ref", ref)
            if r.get("error") in ("Jadwal_TAKEN", "SLOT_TAKEN"):
                return False, "Jadwal_TAKEN"
            if "duplicate" in r.get("message","").lower():
                return True, ref
            return False, r.get("message", r.get("error", "Unknown"))
        if resp.status_code in (200, 201, 302):
            return True, ref
        return False, f"HTTP {resp.status_code}"
    except requests.exceptions.Timeout:
        return False, "Timeout — coba lagi"
    except Exception as e:
        return False, str(e)

def valid_email(e):
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", e.strip()))

def valid_phone(p):
    digits = re.sub(r"[\s\-\(\)]", "", p)
    return bool(re.match(r"^(\+62|62|0)\d{8,13}$", digits))

# ── SESSION STATE ──────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "step": 1,
        "sel_date_key": None, "sel_date_label": None,
        "sel_date_day": None, "sel_date_mon": None,
        "sel_sess_value": None, "sel_sess_label": None,
        "nama_hotel": "", "alamat_hotel": "", "brand_hotel": "",
        "nama_pic": "", "jabatan": "", "no_hp": "", "email": "",
        "peserta": "1 orang", "tujuan": [],
        "durasi": "30 Menit", "catatan": "",
        "ref_number": "", "submitted_ref": "",
        "conflict_type": None, "conflict_msg": "", "alternatives": [],
        "_prev_date_key": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── MASTER CSS ─────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Nunito+Sans:wght@400;500;600;700&display=swap');

/* ── VARIABLES ── */
:root {
  --c1: #1BA0E2;
  --c2: #1494C6;
  --c3: #0D7FCC;
  --bg: #F0F0F0;
  --border: #DEDEDE;
  --accent: #ff5e1f;
  --accent-dk: #e04c10;
  --white: #ffffff;
  --text: #1a1f2e;
  --muted: #6b7280;
  --light: #F7F9FC;
  --danger: #ef4444;
  --success: #10b981;
  --r: 14px;
  --r-sm: 10px;
  --r-xs: 7px;
  --shadow: 0 2px 12px rgba(13,127,204,0.10);
  --shadow-md: 0 6px 24px rgba(13,127,204,0.16);
}

/* ── RESET ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
  font-family: 'Nunito Sans', sans-serif !important;
  -webkit-font-smoothing: antialiased;
  background: var(--bg) !important;
}
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton,[data-testid="stToolbar"],[data-testid="collapsedControl"]{ display:none!important; }
.main { background: var(--bg) !important; }
.main .block-container {
  padding: 0 0 100px !important;
  max-width: 460px !important;
  margin: 0 auto !important;
}

/* ── TOPBAR ── */
.topbar {
  background: var(--white);
  border-bottom: 2px solid var(--border);
  padding: 0 18px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 200;
}
.topbar-logo {
  display: flex;
  align-items: center;
  gap: 9px;
}
.topbar-icon {
  width: 32px; height: 32px;
  background: linear-gradient(135deg, var(--c1), var(--c3));
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(13,127,204,0.3);
}
.topbar-name {
  font-family: 'Nunito', sans-serif;
  font-size: 14px;
  font-weight: 800;
  color: var(--text);
  letter-spacing: -0.4px;
}
.topbar-name span { color: var(--c1); }
.topbar-live {
  display: flex; align-items: center; gap: 5px;
  background: #ecfdf5;
  border: 1px solid #6ee7b7;
  border-radius: 20px;
  padding: 4px 10px;
  font-size: 10px;
  font-weight: 700;
  color: #059669;
  letter-spacing: 0.2px;
}
.pulse-dot {
  width: 6px; height: 6px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%,100% { opacity:1; transform:scale(1); }
  50%      { opacity:.4; transform:scale(.8); }
}

/* ── HERO HEADER ── */
.hero {
  background: linear-gradient(145deg, var(--c1) 0%, var(--c3) 100%);
  padding: 24px 20px 40px;
  position: relative;
  overflow: hidden;
}
.hero::before {
  content: '';
  position: absolute; top: -30px; right: -30px;
  width: 130px; height: 130px;
  border-radius: 50%;
  background: rgba(255,255,255,0.07);
}
.hero::after {
  content: '';
  position: absolute; bottom: -20px; left: 50%;
  width: 80px; height: 80px;
  border-radius: 50%;
  background: rgba(255,255,255,0.05);
}
.hero-step-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255,255,255,0.18);
  border: 1px solid rgba(255,255,255,0.28);
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 10px;
  font-weight: 700;
  color: rgba(255,255,255,0.9);
  text-transform: uppercase;
  letter-spacing: 0.6px;
  margin-bottom: 12px;
}
.hero-title {
  font-family: 'Nunito', sans-serif;
  font-size: 22px;
  font-weight: 900;
  color: #fff;
  line-height: 1.18;
  margin-bottom: 5px;
  letter-spacing: -0.5px;
}
.hero-sub {
  font-size: 12.5px;
  color: rgba(255,255,255,0.72);
  line-height: 1.55;
}

/* ── STEP TRACKER ── */
.step-track {
  display: flex;
  align-items: center;
  background: var(--white);
  margin: -20px 14px 0;
  border-radius: var(--r);
  padding: 14px 12px;
  box-shadow: var(--shadow-md);
  position: relative;
  z-index: 10;
}
.st-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  position: relative;
}
.st-item:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 13px;
  left: 60%;
  width: 80%;
  height: 2px;
  background: var(--border);
}
.st-item.done:not(:last-child)::after,
.st-item.active:not(:last-child)::after {
  background: linear-gradient(90deg, var(--c1), var(--border));
}
.st-dot {
  width: 26px; height: 26px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px;
  font-weight: 800;
  border: 2px solid var(--border);
  color: var(--muted);
  background: var(--white);
  transition: all 0.25s;
  z-index: 1;
}
.st-item.done .st-dot {
  background: var(--c1);
  border-color: var(--c1);
  color: white;
  font-size: 12px;
}
.st-item.active .st-dot {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
  box-shadow: 0 0 0 4px rgba(255,94,31,0.18);
}
.st-label {
  font-size: 9px;
  font-weight: 700;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}
.st-item.done .st-label  { color: var(--c2); }
.st-item.active .st-label { color: var(--accent); }

/* ── CONTENT WRAP ── */
.content { padding: 16px 14px 0; }

/* ── SECTION HEADING ── */
.sec-head {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--muted);
  margin: 18px 0 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.sec-head::after {
  content: '';
  flex: 1;
  height: 1.5px;
  background: var(--border);
  border-radius: 1px;
}

/* ── INFO BOX ── */
.ibox {
  background: rgba(27,160,226,0.07);
  border: 1.5px solid rgba(27,160,226,0.22);
  border-radius: var(--r-sm);
  padding: 11px 14px;
  font-size: 12px;
  color: var(--c3);
  line-height: 1.6;
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin-bottom: 14px;
}
.ibox-icon { font-size: 13px; flex-shrink: 0; margin-top: 1px; }

/* ── ALERT ── */
.alert {
  border-radius: var(--r-sm);
  padding: 11px 14px;
  font-size: 12.5px;
  line-height: 1.55;
  margin-bottom: 12px;
  display: flex; gap: 9px; align-items: flex-start;
  font-weight: 500;
}
.alert-error   { background:#fef2f2; border:1.5px solid #fca5a5; color:#991b1b; }
.alert-success { background:#ecfdf5; border:1.5px solid #6ee7b7; color:#065f46; }
.alert-warn    { background:#fff7ed; border:1.5px solid #fed7aa; color:#92400e; }

/* ── DATE GRID ── */
.date-scroll {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 7px;
  margin-bottom: 4px;
}
.date-chip {
  background: var(--white);
  border: 2px solid var(--border);
  border-radius: var(--r-sm);
  padding: 9px 4px 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.18s ease;
  -webkit-tap-highlight-color: transparent;
  user-select: none;
}
.date-chip:active { transform: scale(0.95); }
.date-chip:hover:not(.dc-full)  {
  border-color: var(--c1);
  background: rgba(27,160,226,0.05);
  box-shadow: 0 2px 8px rgba(27,160,226,0.15);
}
.date-chip.dc-selected {
  border-color: var(--c1);
  background: linear-gradient(145deg, rgba(27,160,226,0.12), rgba(13,127,204,0.08));
  box-shadow: 0 2px 10px rgba(27,160,226,0.2);
}
.date-chip.dc-full {
  opacity: 0.38;
  cursor: not-allowed;
  background: var(--bg);
}
.dc-day  { font-family:'Nunito',sans-serif; font-size:18px; font-weight:900; color:var(--text); line-height:1; }
.dc-mon  { font-size:9px; font-weight:700; color:var(--muted); margin-top:2px; text-transform:uppercase; }
.dc-ind  { margin:5px auto 0; width:5px; height:5px; border-radius:50%; background:var(--border); }
.dc-selected .dc-day { color:var(--c3); }
.dc-selected .dc-ind { background:var(--c1); }
.dc-full .dc-ind     { background:var(--danger); }

/* ── SESSION CARDS ── */
.sess-list { display:flex; flex-direction:column; gap:8px; }
.sess-card {
  background: var(--white);
  border: 2px solid var(--border);
  border-radius: var(--r-sm);
  padding: 0;
  overflow: hidden;
  transition: all 0.18s;
}
.sess-card.sc-available { cursor: pointer; }
.sess-card.sc-available:hover {
  border-color: var(--c1);
  box-shadow: 0 3px 12px rgba(27,160,226,0.15);
  transform: translateY(-1px);
}
.sess-card.sc-selected {
  border-color: var(--c1);
  background: linear-gradient(135deg, rgba(27,160,226,0.07), rgba(20,148,198,0.04));
  box-shadow: 0 4px 16px rgba(27,160,226,0.2);
}
.sess-card.sc-taken { opacity:0.42; cursor:not-allowed; background:var(--bg); }
.sess-inner {
  display: flex;
  align-items: center;
  padding: 13px 15px;
  gap: 13px;
}
.sess-radio-ring {
  width: 20px; height: 20px;
  border-radius: 50%;
  border: 2px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}
.sc-selected .sess-radio-ring {
  border-color: var(--c1);
  background: var(--c1);
}
.sess-radio-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: white;
  opacity: 0;
  transition: opacity 0.15s;
}
.sc-selected .sess-radio-dot { opacity: 1; }
.sess-period-tag {
  font-size: 9px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 4px;
  background: rgba(27,160,226,0.1);
  color: var(--c2);
  text-transform: uppercase;
  letter-spacing: 0.3px;
  flex-shrink: 0;
}
.sc-taken .sess-period-tag { background:#fee2e2; color:var(--danger); }
.sess-time { font-size:14px; font-weight:700; color:var(--text); flex:1; font-family:'Nunito',sans-serif; }
.sc-taken .sess-time { text-decoration:line-through; color:var(--muted); }
.sess-status { font-size:10px; font-weight:700; }
.sess-status.avail { color:var(--c1); }
.sess-status.taken { color:var(--danger); }
/* Streamlit button overlay on sess card */
.sess-btn-wrap { position:relative; }
.sess-btn-wrap div[data-testid="stButton"] > button {
  position: absolute !important;
  top: 0 !important; left: 0 !important;
  width: 100% !important; height: 100% !important;
  opacity: 0 !important;
  cursor: pointer !important;
  border: none !important;
  background: transparent !important;
  padding: 0 !important;
  border-radius: 0 !important;
  min-height: unset !important;
}

/* ── SELECTED JADWAL BANNER ── */
.sel-banner {
  background: linear-gradient(135deg, var(--c1), var(--c3));
  border-radius: var(--r-sm);
  padding: 12px 16px;
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
  box-shadow: 0 4px 16px rgba(13,127,204,0.25);
}
.sb-info { flex:1; }
.sb-tag { font-size:9px; font-weight:700; color:rgba(255,255,255,0.65); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:3px; }
.sb-val { font-size:13px; font-weight:700; color:white; }
.sb-check {
  width:28px; height:28px; border-radius:50%;
  background:rgba(255,255,255,0.22);
  display:flex; align-items:center; justify-content:center;
  font-size:13px; color:white;
}

/* ── ALT SLOT BUTTONS ── */
.alt-slot-wrap { display:flex; flex-direction:column; gap:6px; margin-top:8px; }

/* ── FORM FIELDS ── */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
  border: 2px solid var(--border) !important;
  border-radius: var(--r-xs) !important;
  font-family: 'Nunito Sans', sans-serif !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  background: var(--white) !important;
  color: var(--text) !important;
  padding: 11px 13px !important;
  transition: border-color 0.18s, box-shadow 0.18s !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
  border-color: var(--c1) !important;
  box-shadow: 0 0 0 3px rgba(27,160,226,0.14) !important;
  background: var(--white) !important;
  outline: none !important;
}
div[data-testid="stSelectbox"] > div > div {
  border: 2px solid var(--border) !important;
  border-radius: var(--r-xs) !important;
  font-family: 'Nunito Sans', sans-serif !important;
  font-size: 14px !important;
  background: var(--white) !important;
}
[data-testid="stWidgetLabel"] p,
label {
  font-size: 12.5px !important;
  font-weight: 700 !important;
  color: var(--text) !important;
  margin-bottom: 4px !important;
}

/* ── PESERTA RADIO ── */
div[data-testid="stRadio"] > div {
  gap: 6px !important;
  flex-wrap: wrap !important;
}
div[data-testid="stRadio"] > div > label {
  border: 2px solid var(--border) !important;
  border-radius: var(--r-xs) !important;
  padding: 8px 14px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  background: var(--white) !important;
  cursor: pointer !important;
  transition: all 0.15s !important;
  color: var(--text) !important;
}
div[data-testid="stRadio"] > div > label:has(input:checked) {
  border-color: var(--c1) !important;
  background: rgba(27,160,226,0.10) !important;
  color: var(--c3) !important;
}
div[data-testid="stRadio"] > div > label > div:first-child { display:none !important; }
div[data-testid="stRadio"] > div > label > div:last-child p {
  font-size: 13px !important;
  font-weight: 600 !important;
  color: inherit !important;
  margin: 0 !important;
}

/* ── CHECKBOXES (TUJUAN) ── */
div[data-testid="stCheckbox"] {
  border: 2px solid var(--border);
  border-radius: var(--r-xs);
  padding: 10px 12px;
  background: var(--white);
  margin-bottom: 5px;
  transition: all 0.15s;
  cursor: pointer;
}
div[data-testid="stCheckbox"]:has(input:checked) {
  border-color: var(--c1);
  background: rgba(27,160,226,0.07);
}
div[data-testid="stCheckbox"] p {
  font-size: 12.5px !important;
  font-weight: 600 !important;
  color: var(--text) !important;
}
div[data-testid="stCheckbox"]:has(input:checked) p { color: var(--c3) !important; }

/* ── GLOBAL BUTTONS ── */
div[data-testid="stButton"] > button {
  font-family: 'Nunito', sans-serif !important;
  font-weight: 800 !important;
  font-size: 14px !important;
  border-radius: var(--r-xs) !important;
  padding: 12px 18px !important;
  width: 100% !important;
  transition: all 0.18s !important;
  letter-spacing: -0.2px !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, var(--c1), var(--c3)) !important;
  border: none !important;
  color: white !important;
  box-shadow: 0 4px 14px rgba(13,127,204,0.3) !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 20px rgba(13,127,204,0.4) !important;
}
div[data-testid="stButton"] > button[kind="primary"]:active {
  transform: translateY(0) !important;
}
div[data-testid="stButton"] > button[kind="secondary"] {
  background: var(--white) !important;
  border: 2px solid var(--border) !important;
  color: var(--muted) !important;
}
div[data-testid="stButton"] > button[kind="secondary"]:hover {
  border-color: var(--c1) !important;
  color: var(--c1) !important;
}

/* ── ACCENT / SUBMIT BUTTON ── */
.btn-accent div[data-testid="stButton"] > button {
  background: linear-gradient(135deg, var(--accent), var(--accent-dk)) !important;
  border: none !important;
  color: white !important;
  box-shadow: 0 4px 14px rgba(255,94,31,0.35) !important;
  font-size: 15px !important;
  padding: 13px !important;
}
.btn-accent div[data-testid="stButton"] > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 22px rgba(255,94,31,0.45) !important;
}

/* ── REVIEW TABLE ── */
.rev-card {
  background: var(--white);
  border: 2px solid var(--border);
  border-radius: var(--r);
  overflow: hidden;
  margin-bottom: 14px;
}
.rev-group-head {
  background: linear-gradient(90deg, rgba(27,160,226,0.08), transparent);
  border-bottom: 1.5px solid var(--border);
  padding: 8px 14px;
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  color: var(--c2);
  display: flex;
  align-items: center;
  gap: 6px;
}
.rev-row { display:flex; border-bottom:1px solid var(--bg); }
.rev-row:last-child { border-bottom:none; }
.rev-lbl {
  width: 82px; flex-shrink:0;
  padding: 9px 12px;
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  border-right: 1px solid var(--bg);
}
.rev-val {
  padding: 9px 13px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  flex: 1;
  word-break: break-word;
  line-height: 1.45;
}
.rev-val.hl { color: var(--c3); font-weight: 800; }

/* ── SUCCESS SCREEN ── */
.succ-wrap { padding: 20px 14px; }
.succ-hero {
  background: linear-gradient(145deg, var(--c1), var(--c3));
  border-radius: var(--r);
  padding: 28px 20px;
  text-align: center;
  position: relative;
  overflow: hidden;
  margin-bottom: 14px;
  box-shadow: var(--shadow-md);
}
.succ-hero::before {
  content:''; position:absolute; top:-20px; right:-20px;
  width:100px; height:100px; border-radius:50%;
  background:rgba(255,255,255,0.07);
}
.succ-ring {
  width: 64px; height: 64px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  border: 3px solid rgba(255,255,255,0.5);
  margin: 0 auto 14px;
  display: flex; align-items: center; justify-content: center;
  font-size: 26px; color: white;
  animation: pop 0.5s cubic-bezier(0.175,0.885,0.32,1.275);
}
@keyframes pop {
  0%   { transform:scale(0); opacity:0; }
  100% { transform:scale(1); opacity:1; }
}
.succ-title {
  font-family: 'Nunito', sans-serif;
  font-size: 20px; font-weight: 900;
  color: white; margin-bottom: 5px;
  letter-spacing: -0.4px;
}
.succ-sub { font-size: 12px; color: rgba(255,255,255,0.78); line-height: 1.65; }
.ref-tag {
  display: inline-block;
  font-family: 'Nunito', sans-serif;
  font-size: 17px; font-weight: 900;
  color: white;
  background: rgba(255,255,255,0.18);
  border: 1.5px solid rgba(255,255,255,0.35);
  border-radius: var(--r-xs);
  padding: 7px 18px;
  letter-spacing: 2.5px;
  margin: 12px 0 6px;
}
.ref-hint { font-size:10px; color:rgba(255,255,255,0.55); }
.succ-grid {
  display: grid; grid-template-columns:1fr 1fr;
  gap: 8px; margin-bottom: 14px;
}
.succ-item {
  background: var(--white);
  border: 2px solid var(--border);
  border-radius: var(--r-xs);
  padding: 11px 13px;
}
.succ-lbl { font-size:9px; font-weight:800; text-transform:uppercase; letter-spacing:0.5px; color:var(--muted); margin-bottom:3px; }
.succ-val { font-size:13px; font-weight:700; color:var(--text); }

/* ── FOOTER ── */
.footer { text-align:center; padding:20px 0 32px; font-size:11px; color:#bbb; letter-spacing:0.3px; }
.footer span { color:var(--c1); font-weight:700; }

/* ── SPACING OVERRIDES ── */
div[data-testid="stVerticalBlock"] { gap: 6px !important; }
</style>
""", unsafe_allow_html=True)

# ── COMPONENT HELPERS ──────────────────────────────────────────────────────────
def render_topbar():
    st.markdown("""
<div class="topbar">
  <div class="topbar-logo">
    <img src="https://mitratour.com/wp-content/uploads/2019/09/LOGO-MITRA-Converted-Copy-min.png"
         alt="Mitra Tours & Travel"
         style="height:36px;width:auto;object-fit:contain;display:block;" />
  </div>
  <div class="topbar-live">
    <div class="pulse-dot"></div>
    Sistem Aktif
  </div>
</div>""", unsafe_allow_html=True)

STEP_META = {
    1: ("📅", "Pilih Jadwal",  "Tentukan tanggal & sesi kunjungan"),
    2: ("🏨", "Data Hotel",    "Informasi properti yang dikunjungi"),
    3: ("👤", "Data Kontak",   "PIC & tujuan kunjungan"),
    4: ("✅", "Review & Kirim","Periksa & konfirmasi permohonan"),
    5: ("🎉", "Selesai",       "Permohonan berhasil terkirim"),
}

def render_hero(step):
    icon, title, sub = STEP_META.get(step, ("📅","Kunjungan",""))
    step_labels = ["Jadwal","Hotel","Kontak","Kirim"]
    tag_label   = step_labels[step-1] if step <= 4 else "Selesai"
    st.markdown(f"""
<div class="hero">
  <div class="hero-step-tag">
    <span>{icon}</span>
    Langkah {min(step,4)} dari 4 · {tag_label}
  </div>
  <div class="hero-title">{title}</div>
  <div class="hero-sub">{sub}</div>
</div>""", unsafe_allow_html=True)

def render_step_tracker(cur):
    labels = ["Jadwal","Hotel","Kontak","Kirim"]
    items  = ""
    for i, lbl in enumerate(labels, 1):
        if   i < cur:  cls = "done";   dot_content = "✓"
        elif i == cur: cls = "active";  dot_content = str(i)
        else:          cls = "";        dot_content = str(i)
        items += f"""
<div class="st-item {cls}">
  <div class="st-dot">{dot_content}</div>
  <div class="st-label">{lbl}</div>
</div>"""
    st.markdown(f'<div class="step-track">{items}</div>', unsafe_allow_html=True)

def sel_banner():
    if st.session_state.sel_date_key and st.session_state.sel_sess_value:
        st.markdown(f"""
<div class="sel-banner">
  <div class="sb-info">
    <div class="sb-tag">📅 Jadwal Dipilih</div>
    <div class="sb-val">{st.session_state.sel_date_label} &nbsp;·&nbsp; {st.session_state.sel_sess_label}</div>
  </div>
  <div class="sb-check">✓</div>
</div>""", unsafe_allow_html=True)

def ibox(txt):
    st.markdown(f"""
<div class="ibox">
  <span class="ibox-icon">ℹ️</span>
  <div>{txt}</div>
</div>""", unsafe_allow_html=True)

def alert(msg, kind="warn", icon="⚠️"):
    st.markdown(f"""
<div class="alert alert-{kind}">
  <span style="font-size:14px;flex-shrink:0">{icon}</span>
  <div>{msg}</div>
</div>""", unsafe_allow_html=True)

def sec(txt):
    st.markdown(f'<div class="sec-head">{txt}</div>', unsafe_allow_html=True)

# ── STEP 1 ─────────────────────────────────────────────────────────────────────
def render_step1():
    booked = fetch_booked()

    st.markdown('<div class="content">', unsafe_allow_html=True)
    ibox("Kunjungan dilakukan setiap <strong>Selasa</strong> · 1 hotel per sesi · Pilih tanggal lalu pilih jam")

    # ── Conflict alerts
    if st.session_state.conflict_type == "blocking":
        alert(f"<strong>Jadwal penuh!</strong> {st.session_state.conflict_msg}", kind="error", icon="❌")
        if st.session_state.alternatives:
            st.caption("Jadwal alternatif tersedia:")
            for alt in st.session_state.alternatives:
                if st.button(
                    f"→ {alt['date_label']} · {alt['sess_label']}",
                    key=f"alt_{alt['date_key']}_{alt['sess_value']}",
                ):
                    st.session_state.sel_date_key   = alt["date_key"]
                    st.session_state.sel_date_label = alt["date_label"]
                    st.session_state.sel_sess_value = alt["sess_value"]
                    st.session_state.sel_sess_label = alt["sess_label"]
                    st.session_state.conflict_type  = "ok"
                    st.session_state.conflict_msg   = f"{alt['date_label']} · {alt['sess_label']} tersedia."
                    st.rerun()

    elif st.session_state.conflict_type == "ok":
        alert(st.session_state.conflict_msg, kind="success", icon="✅")

    # ── Date selector ──
    sec("Pilih Tanggal Kunjungan")

    date_opts = ["— Pilih tanggal —"]
    date_map  = {}
    for dt in DATES:
        free = sum(1 for s in SESSIONS if not is_booked(booked, dt["key"], s["value"]))
        suf  = " ✕ Penuh" if free == 0 else (f" · {free} sesi" if free < len(SESSIONS) else "")
        opt  = dt["label"] + suf
        date_opts.append(opt)
        date_map[opt] = dt

    cur_opt = None
    if st.session_state.sel_date_key:
        for lbl, dt in date_map.items():
            if dt["key"] == st.session_state.sel_date_key:
                cur_opt = lbl; break
    cur_idx = date_opts.index(cur_opt) if cur_opt in date_opts else 0

    chosen_label = st.selectbox("Tanggal", options=date_opts, index=cur_idx,
                                 label_visibility="collapsed", key="dd_tanggal")
    chosen_dt = date_map.get(chosen_label)

    # Reset when date changes — use _prev_date_key to avoid rerun loop
    if chosen_dt and chosen_dt["key"] != st.session_state._prev_date_key:
        if chosen_dt["key"] != st.session_state.sel_date_key:
            st.session_state.sel_date_key   = chosen_dt["key"]
            st.session_state.sel_date_label = chosen_dt["label"]
            st.session_state.sel_sess_value = None
            st.session_state.sel_sess_label = None
            st.session_state.conflict_type  = None
        st.session_state._prev_date_key = chosen_dt["key"]
        st.rerun()

    # ── Session slots ──
    if chosen_dt:
        dk = chosen_dt["key"]
        sec("Pilih Sesi Waktu")

        st.markdown('<div class="sess-list">', unsafe_allow_html=True)
        for sess in SESSIONS:
            taken    = is_booked(booked, dk, sess["value"])
            selected = (st.session_state.sel_sess_value == sess["value"]
                        and st.session_state.sel_date_key == dk)
            sc_cls   = "sc-taken" if taken else ("sc-selected" if selected else "sc-available")
            st_cls   = "taken"    if taken else ("avail"       if not selected else "avail")
            st_txt   = "Penuh"    if taken else "Tersedia"

            st.markdown(f"""
<div class="sess-card {sc_cls}" style="position:relative;">
  <div class="sess-inner">
    <div class="sess-radio-ring">
      <div class="sess-radio-dot"></div>
    </div>
    <span class="sess-period-tag">{"Penuh" if taken else sess["period"]}</span>
    <div class="sess-time">{sess["label"]}</div>
    <span class="sess-status {st_cls}">{st_txt}</span>
  </div>
</div>""", unsafe_allow_html=True)

            if not taken:
                if st.button(sess["label"], key=f"sb_{dk}_{sess['id']}"):
                    _fetch_cached.clear()
                    fresh = fetch_booked()
                    if is_booked(fresh, dk, sess["value"]):
                        alts = get_alts(fresh, dk, sess["value"])
                        st.session_state.conflict_type = "blocking"
                        st.session_state.conflict_msg  = "Jadwal ini baru saja terisi hotel lain."
                        st.session_state.alternatives  = alts
                    else:
                        st.session_state.sel_date_key   = dk
                        st.session_state.sel_date_label = chosen_dt["label"]
                        st.session_state.sel_sess_value = sess["value"]
                        st.session_state.sel_sess_label = sess["label"]
                        st.session_state.conflict_type  = "ok"
                        st.session_state.conflict_msg   = f"{chosen_dt['label']} · {sess['label']} siap di-booking."
                        st.session_state.alternatives   = []
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ── CTA ──
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if st.session_state.sel_date_key and st.session_state.sel_sess_value:
        sel_banner()
        c1, c2 = st.columns([1, 2])
        with c1:
            if st.button("Batal", key="clear_jadwal"):
                for k in ("sel_date_key","sel_date_label","sel_sess_value","sel_sess_label"):
                    st.session_state[k] = None
                st.session_state.conflict_type  = None
                st.session_state._prev_date_key = None
                st.rerun()
        with c2:
            if st.button("Lanjut →", type="primary", key="btn1_next"):
                st.session_state.step = 2
                st.rerun()
    else:
        if chosen_dt:
            alert("Pilih sesi waktu di atas untuk melanjutkan.", kind="warn", icon="👆")
        else:
            alert("Pilih tanggal kunjungan terlebih dahulu.", kind="warn", icon="📅")

    st.markdown('</div>', unsafe_allow_html=True)

# ── STEP 2 ─────────────────────────────────────────────────────────────────────
def render_step2():
    st.markdown('<div class="content">', unsafe_allow_html=True)
    sel_banner()

    st.session_state.nama_hotel = st.text_input(
        "Nama Hotel / Property *",
        value=st.session_state.nama_hotel,
        placeholder="Contoh: Grand Hyatt Jakarta",
        key="inp_nama_hotel",
    )
    st.session_state.alamat_hotel = st.text_area(
        "Alamat Lengkap *",
        value=st.session_state.alamat_hotel,
        placeholder="Jl. ..., Kelurahan, Kecamatan, Kota",
        height=90, key="inp_alamat",
    )
    opts = HOTEL_BRANDS
    idx  = opts.index(st.session_state.brand_hotel) if st.session_state.brand_hotel in opts else 0
    st.session_state.brand_hotel = st.selectbox(
        "Brand / Chain Hotel (opsional)", options=opts, index=idx, key="inp_brand",
        format_func=lambda x: "— Pilih brand / chain —" if x == "" else x,
    )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("← Kembali", key="btn2_back"):
            st.session_state.step = 1; st.rerun()
    with c2:
        if st.button("Lanjut →", type="primary", key="btn2_next"):
            errs = []
            if not st.session_state.nama_hotel.strip():  errs.append("Nama hotel wajib diisi.")
            if not st.session_state.alamat_hotel.strip(): errs.append("Alamat hotel wajib diisi.")
            if errs:
                [st.error(e) for e in errs]
            else:
                st.session_state.step = 3; st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ── STEP 3 ─────────────────────────────────────────────────────────────────────
def render_step3():
    st.markdown('<div class="content">', unsafe_allow_html=True)
    sel_banner()

    sec("Identitas PIC")
    st.session_state.nama_pic = st.text_input("Nama PIC Utama *",
        value=st.session_state.nama_pic, placeholder="Nama lengkap", key="inp_nama_pic")

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.jabatan = st.text_input("Jabatan *",
            value=st.session_state.jabatan, placeholder="Sales Manager, GM...", key="inp_jabatan")
    with c2:
        st.session_state.no_hp = st.text_input("WhatsApp *",
            value=st.session_state.no_hp, placeholder="08xx-xxxx-xxxx", key="inp_no_hp")

    st.session_state.email = st.text_input("Email *",
        value=st.session_state.email, placeholder="nama@hotel.com", key="inp_email")

    sec("Jumlah Peserta")
    p_opts = ["1 orang","2 orang","3 orang","4 orang","5 orang"]
    cur_p  = p_opts.index(st.session_state.peserta) if st.session_state.peserta in p_opts else 0
    st.session_state.peserta = st.radio("Peserta", options=p_opts, index=cur_p,
        horizontal=True, label_visibility="collapsed", key="inp_peserta")

    sec("Tujuan Kunjungan")
    tujuan_sel = []
    ca, cb = st.columns(2)
    for i, tuj in enumerate(TUJUAN_OPTIONS):
        with (ca if i % 2 == 0 else cb):
            if st.checkbox(tuj, value=(tuj in st.session_state.tujuan), key=f"tuj_{i}"):
                tujuan_sel.append(tuj)
    st.session_state.tujuan = tujuan_sel

    sec("Estimasi Durasi")
    d_opts = ["15 Menit","30 Menit","45 Menit"]
    cur_d  = d_opts.index(st.session_state.durasi) if st.session_state.durasi in d_opts else 1
    st.session_state.durasi = st.radio("Durasi", options=d_opts, index=cur_d,
        horizontal=True, label_visibility="collapsed", key="inp_durasi")

    sec("Catatan Tambahan (Opsional)")
    st.session_state.catatan = st.text_area("Catatan", value=st.session_state.catatan,
        placeholder="Informasi tambahan...", height=75,
        label_visibility="collapsed", key="inp_catatan")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("← Kembali", key="btn3_back"):
            st.session_state.step = 2; st.rerun()
    with c2:
        if st.button("Review →", type="primary", key="btn3_next"):
            errs = []
            if not st.session_state.nama_pic.strip():  errs.append("Nama PIC wajib diisi.")
            if not st.session_state.jabatan.strip():   errs.append("Jabatan wajib diisi.")
            if not st.session_state.no_hp.strip():     errs.append("Nomor WhatsApp wajib diisi.")
            elif not valid_phone(st.session_state.no_hp): errs.append("Format nomor WA tidak valid.")
            if not st.session_state.email.strip():     errs.append("Email wajib diisi.")
            elif not valid_email(st.session_state.email): errs.append("Format email tidak valid.")
            if not st.session_state.tujuan:            errs.append("Pilih minimal satu tujuan kunjungan.")
            if errs:
                [st.error(e) for e in errs]
            else:
                st.session_state.step = 4; st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ── STEP 4 ─────────────────────────────────────────────────────────────────────
def render_step4():
    st.markdown('<div class="content">', unsafe_allow_html=True)

    def row(lbl, val, hl=False):
        vcls = "rev-val hl" if hl else "rev-val"
        return f'<div class="rev-row"><div class="rev-lbl">{lbl}</div><div class="{vcls}">{val}</div></div>'

    html = (
        '<div class="rev-card">'
        '<div class="rev-group-head">📅 Jadwal</div>'
        + row("Tanggal", st.session_state.sel_date_label or "—", hl=True)
        + row("Sesi",    st.session_state.sel_sess_label  or "—", hl=True)
        + '<div class="rev-group-head">🏨 Hotel</div>'
        + row("Hotel",   st.session_state.nama_hotel)
        + row("Alamat",  st.session_state.alamat_hotel)
        + row("Brand",   st.session_state.brand_hotel or "—")
        + '<div class="rev-group-head">👤 Kontak</div>'
        + row("Nama PIC", st.session_state.nama_pic)
        + row("Jabatan",  st.session_state.jabatan)
        + row("WA",       st.session_state.no_hp)
        + row("Email",    st.session_state.email)
        + row("Peserta",  st.session_state.peserta)
        + row("Durasi",   st.session_state.durasi)
        + row("Tujuan",   ", ".join(st.session_state.tujuan) or "—")
        + (row("Catatan", st.session_state.catatan) if st.session_state.catatan.strip() else "")
        + '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    ibox("Dengan mengirim, Anda bersedia dihubungi via WhatsApp atau Email untuk konfirmasi jadwal.")

    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("← Edit", key="btn4_back"):
            st.session_state.step = 3; st.rerun()
    with c2:
        st.markdown('<div class="btn-accent">', unsafe_allow_html=True)
        if st.button("Kirim Permohonan ✓", key="btn4_submit"):
            _do_submit()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def _do_submit():
    _fetch_cached.clear()
    fresh = fetch_booked()

    dk = st.session_state.sel_date_key
    sv = st.session_state.sel_sess_value

    # ─────────────────────────────────────────────
    # DOUBLE CHECK SLOT MASIH TERSEDIA
    # ─────────────────────────────────────────────
    if is_booked(fresh, dk, sv):
        alts = get_alts(fresh, dk, sv)

        st.session_state.conflict_type = "blocking"
        st.session_state.conflict_msg = (
            f"Jadwal {st.session_state.sel_sess_label} pada "
            f"{st.session_state.sel_date_label} baru saja dipesan hotel lain."
        )
        st.session_state.alternatives = alts

        for k in (
            "sel_date_key",
            "sel_date_label",
            "sel_sess_value",
            "sel_sess_label",
        ):
            st.session_state[k] = None

        st.session_state.step = 1
        st.rerun()
        return

    # ─────────────────────────────────────────────
    # GENERATE REF & WIB TIME
    # ─────────────────────────────────────────────
    wib = datetime.now(ZoneInfo("Asia/Jakarta"))
    ref = gen_ref()

    # ─────────────────────────────────────────────
    # PAYLOAD SESUAI GOOGLE APPS SCRIPT
    # ─────────────────────────────────────────────
    payload = {
        "ref": ref,
        "timestamp": wib.strftime("%d/%m/%Y %H:%M:%S"),

        "namaHotel": st.session_state.nama_hotel.strip(),
        "alamatHotel": st.session_state.alamat_hotel.strip(),
        "brand": st.session_state.brand_hotel or "—",

        "namaPIC": st.session_state.nama_pic.strip(),
        "jabatan": st.session_state.jabatan.strip(),
        "noHP": st.session_state.no_hp.strip(),
        "email": st.session_state.email.strip(),

        "peserta": st.session_state.peserta,
        "tujuan": ", ".join(st.session_state.tujuan),

        "tanggal": dk,
        "slot": sv,

        "durasi": st.session_state.durasi,
        "catatan": st.session_state.catatan or "",

        "notifEmail": NOTIF_EMAIL,
    }

    # ─────────────────────────────────────────────
    # SUBMIT TO GAS
    # ─────────────────────────────────────────────
    with st.spinner("Menyimpan & mengirim notifikasi..."):
        ok, result = save_to_gas(payload)

    # ─────────────────────────────────────────────
    # SUCCESS
    # ─────────────────────────────────────────────
    if ok:
        st.session_state.ref_number = result or ref
        st.session_state.step = 5
        _fetch_cached.clear()
        st.rerun()

    # ─────────────────────────────────────────────
    # SLOT SUDAH DIAMBIL ORANG LAIN
    # ─────────────────────────────────────────────
    elif result == "SLOT_TAKEN":
        _fetch_cached.clear()
        fresh2 = fetch_booked()

        alts = get_alts(fresh2, dk, sv)

        st.session_state.conflict_type = "blocking"
        st.session_state.conflict_msg = (
            f"Jadwal {st.session_state.sel_sess_label} "
            f"baru saja dipesan saat Anda submit."
        )
        st.session_state.alternatives = alts

        for k in (
            "sel_date_key",
            "sel_date_label",
            "sel_sess_value",
            "sel_sess_label",
        ):
            st.session_state[k] = None

        st.session_state.step = 1
        st.rerun()

    # ─────────────────────────────────────────────
    # ERROR LAIN
    # ─────────────────────────────────────────────
    else:
        st.error(f"Gagal menyimpan: {result}")

# ── STEP 5 ─────────────────────────────────────────────────────────────────────
def render_success():
    st.markdown(f"""
<div class="succ-wrap">
  <div class="succ-hero">
    <div class="succ-ring">✓</div>
    <div class="succ-title">Permohonan Terkirim!</div>
    <div class="succ-sub">
      Notifikasi dikirim ke <strong>{NOTIF_EMAIL}</strong><br>
      Konfirmasi dalam <strong>1–2 hari kerja</strong>.
    </div>
    <div class="ref-tag">{st.session_state.ref_number}</div>
    <div class="ref-hint">Simpan nomor referensi ini</div>
  </div>

  <div class="succ-grid">
    <div class="succ-item">
      <div class="succ-lbl">Hotel</div>
      <div class="succ-val">{st.session_state.nama_hotel}</div>
    </div>
    <div class="succ-item">
      <div class="succ-lbl">PIC</div>
      <div class="succ-val">{st.session_state.nama_pic}</div>
    </div>
    <div class="succ-item">
      <div class="succ-lbl">Tanggal</div>
      <div class="succ-val">{st.session_state.sel_date_label}</div>
    </div>
    <div class="succ-item">
      <div class="succ-lbl">Sesi</div>
      <div class="succ-val">{st.session_state.sel_sess_label}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div style="padding:0 14px;">', unsafe_allow_html=True)
    if st.button("+ Ajukan Kunjungan Baru", type="primary", key="btn_reset"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    init_state()
    inject_css()
    render_topbar()

    s = st.session_state.step
    if s <= 4:
        render_hero(s)
        render_step_tracker(s)

    if   s == 1: render_step1()
    elif s == 2: render_step2()
    elif s == 3: render_step3()
    elif s == 4: render_step4()
    elif s == 5: render_success()

    st.markdown(
        '<div class="footer">Mitra Tours and Travel &nbsp;·&nbsp; '
        '<span>Booking System</span> &nbsp;·&nbsp; v2.0</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
