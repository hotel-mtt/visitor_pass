"""
Mitra Tours & Travel — Visitor Appointment System
app.py  |  Redesigned with brand color palette
- Google Sheets read (slot check)
- Google Apps Script write
- Email notifikasi via GAS ke d4t4m1tr4@gmail.com
"""

import streamlit as st
import requests
import random
import string
import re
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="Kunjungan Sales — Mitra Tours",
    page_icon="🏢",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CONFIG ────────────────────────────────────────────────────────
GAS_ENDPOINT = "https://script.google.com/macros/s/AKfycbz78iwrv1FiIHqpqbA4dX6sQVzcfO4UodJ3BhW4bLH_7zLA_c4wMmXpuhHSGC5yiE6Pww/exec"
SHEET_ID     = "1AQz-w3sLjGVdOsneDmdTFHFW6Nx7Z337Kjw2zzqFoXI"
API_KEY      = "AIzaSyA1Mau8yZxao0MD5Mx_Dt027EuMbrUN9oo"
SHEET_NAME   = "Sheet1"
NOTIF_EMAIL  = "d4t4m1tr4@gmail.com"

SHEETS_READ_URL = (
    f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}"
    f"/values/{SHEET_NAME}?key={API_KEY}"
)

DATES = [
    {"key": "6 Mei 2026",  "label": "Selasa, 6 Mei 2026"},
    {"key": "13 Mei 2026", "label": "Selasa, 13 Mei 2026"},
    {"key": "20 Mei 2026", "label": "Selasa, 20 Mei 2026"},
    {"key": "27 Mei 2026", "label": "Selasa, 27 Mei 2026"},
    {"key": "2 Jun 2026", "label": "Selasa, 2 Jun 2026"},
    {"key": "9 Jun 2026", "label": "Selasa, 9 Jun 2026"},
    {"key": "23 Jun 2026", "label": "Selasa, 23 Jun 2026"},
    {"key": "30 Jun 2026", "label": "Selasa, 30 Jun 2026"},
    {"key": "7 Jul 2026", "label": "Selasa, 7 Jul 2026"},
    {"key": "14 Jul 2026", "label": "Selasa, 14 Jul 2026"},
    {"key": "21 Jul 2026", "label": "Selasa, 21 Jul 2026"},
    {"key": "28 Jul 2026", "label": "Selasa, 28 Jul 2026"},
]

SESSIONS = [
    {"id": "P1", "value": "Pagi 09.00-10.00 WIB",  "label": "Pagi  09.00 - 10.00 WIB"},
    {"id": "P2", "value": "Pagi 10.00-11.00 WIB",  "label": "Pagi  10.00 - 11.00 WIB"},
    {"id": "S1", "value": "Siang 13.30-14.30 WIB", "label": "Siang 13.30 - 14.30 WIB"},
]

HOTEL_BRANDS = [
    "",
    "Accor", "Aman Resorts", "Archipelago International", "ARTOTEL Group",
    "Aryaduta", "Ascott Limited", "Azana Hotels", "Banyan Group Limited",
    "Best Western Hotels", "Cross Hotels & Resorts", "Dafam Hotel Management",
    "Dusit International", "Four Seasons Hotels and Resorts", "Hilton Worldwide",
    "Horison Hotels Group", "Hotel Indonesia Group", "Hyatt Hotels Corporation",
    "IHG Hotels & Resorts", "Jambuluwuk Hotels & Resorts", "Jumeirah", "Kempinski",
    "Mandarin Oriental Hotel Group", "Marriott International", "Meliá Hotels International",
    "Minor Hotels", "Oberoi Group", "Pan Pacific Hotels and Resorts",
    "Parador Hotels & Resorts", "Radisson Hotel Group",
    "Santika Indonesia Hotels & Resorts", "Shangri-La Hotels and Resorts",
    "Swiss-Belhotel International", "The Ascott Limited",
    "Waringin Hospitality Hotel Group", "Wyndham Hotels & Resorts",
    "Independen / Tidak Berantai", "Lainnya",
]

TUJUAN_OPTIONS = [
    "Perkenalan Hotel",
    "Presentasi Produk / Fasilitas",
    "Corporate Rate / Contract Rate",
    "Promo / Special Offer",
    "Kerja Sama Partnership",
    "Follow Up Existing Business",
]

# ── GOOGLE SHEETS READ ────────────────────────────────────────────
@st.cache_data(ttl=30)
def _fetch_booked_cached() -> tuple:
    try:
        resp = requests.get(SHEETS_READ_URL, timeout=10)
        resp.raise_for_status()
        rows = resp.json().get("values", [])[1:]
        booked = {}
        for row in rows:
            while len(row) < 16:
                row.append("")
            status = row[15].lower().strip()
            if status in ("ditolak", "dibatalkan"):
                continue
            date_raw = row[11].strip()
            slot_val = row[12].strip()
            if not date_raw or not slot_val:
                continue
            dk  = re.sub(r"\s*\(.*?\)", "", date_raw).strip()
            key = f"{dk}|{slot_val}"
            booked[key] = booked.get(key, 0) + 1
        return booked, ""
    except Exception as e:
        return {}, str(e)

def fetch_booked_slots() -> dict:
    booked, err = _fetch_booked_cached()
    if err:
        st.toast(f"Gagal memuat jadwal: {err}", icon="⚠️")
    return booked

def is_booked(booked: dict, date_key: str, sess_val: str) -> bool:
    return booked.get(f"{date_key}|{sess_val}", 0) >= 1

def get_alternatives(booked: dict, exc_dk: str, exc_sv: str, max_n: int = 3) -> list:
    alts = []
    for d in DATES:
        for s in SESSIONS:
            if d["key"] == exc_dk and s["value"] == exc_sv:
                continue
            if not is_booked(booked, d["key"], s["value"]):
                alts.append({"date_key": d["key"], "date_label": d["label"],
                              "sess_value": s["value"], "sess_label": s["label"]})
                if len(alts) >= max_n:
                    return alts
    return alts

def generate_ref() -> str:
    return "SV-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=7))

# ── GAS WRITE + EMAIL NOTIF ───────────────────────────────────────
def save_to_gas(payload: dict) -> tuple:
    """
    GAS Web App selalu melakukan redirect 302 saat menerima POST.
    requests.post() tidak mengikuti redirect untuk POST — akibatnya
    Google mengembalikan halaman HTML error.
    Solusi: kirim sebagai POST dengan allow_redirects=True dan
    fallback ke GET dengan payload di query string jika masih gagal.
    """
    try:
        payload["notifEmail"] = NOTIF_EMAIL
        import json as _json

        # ── Strategi 1: POST dengan follow redirect ──
        session = requests.Session()
        resp = session.post(
            GAS_ENDPOINT,
            data=_json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            allow_redirects=True,
            timeout=30,
        )

        # Cek apakah response adalah JSON
        content_type = resp.headers.get("Content-Type", "")
        raw = resp.text.strip()

        if "application/json" in content_type or (raw.startswith("{") and raw.endswith("}")):
            try:
                result = _json.loads(raw)
                if result.get("success"):
                    return True, result.get("ref", "")
                elif result.get("error") == "SLOT_TAKEN":
                    return False, "SLOT_TAKEN"
                else:
                    return False, result.get("message", result.get("error", "Unknown error"))
            except Exception:
                pass

        # ── Strategi 2: POST ke URL dengan ?method=POST ──
        # GAS kadang butuh parameter tambahan untuk bypass redirect
        resp2 = session.post(
            GAS_ENDPOINT + "?method=POST",
            data=_json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            allow_redirects=True,
            timeout=30,
        )
        raw2 = resp2.text.strip()
        if raw2.startswith("{"):
            try:
                result2 = _json.loads(raw2)
                if result2.get("success"):
                    return True, result2.get("ref", "")
                elif result2.get("error") == "SLOT_TAKEN":
                    return False, "SLOT_TAKEN"
                else:
                    return False, result2.get("message", result2.get("error", "Unknown error"))
            except Exception:
                pass

        # ── Strategi 3: GET dengan payload di query string ──
        # Sebagai fallback terakhir — GAS doGet bisa menerima ini
        import urllib.parse as _up
        params = _up.urlencode({"payload": _json.dumps(payload), "action": "write"})
        resp3 = session.get(
            GAS_ENDPOINT + "?" + params,
            allow_redirects=True,
            timeout=30,
        )
        raw3 = resp3.text.strip()
        if raw3.startswith("{"):
            try:
                result3 = _json.loads(raw3)
                if result3.get("success"):
                    return True, result3.get("ref", "")
                elif result3.get("error") == "SLOT_TAKEN":
                    return False, "SLOT_TAKEN"
                else:
                    return False, result3.get("message", result3.get("error", "Unknown error"))
            except Exception:
                pass

        return False, f"Semua strategi gagal. Response: {raw[:200]}"

    except requests.exceptions.Timeout:
        return False, "Timeout — coba lagi"
    except Exception as e:
        return False, str(e)

# ── SESSION STATE ─────────────────────────────────────────────────
def init_state():
    defaults = {
        "step": 1,
        "nama_hotel": "", "alamat_hotel": "", "brand_hotel": "",
        "nama_pic": "", "jabatan": "", "no_hp": "", "email": "",
        "peserta": "1 orang (PIC saja)",
        "sel_date_key": None, "sel_date_label": None,
        "sel_sess_value": None, "sel_sess_label": None,
        "tujuan": [], "durasi": None, "catatan": "",
        "ref_number": "", "submitted": False,
        "conflict_type": None, "conflict_msg": "", "alternatives": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── CSS — Brand Colors from Reference ────────────────────────────
# Image 1 (light): typeface #FFFFFF, bird body #FFFFFF, bird wing #F0F0F0, wing shade #DEDEDE
# Image 2 (color): typeface #434343, bird body #1BA0E2, bird wing #1494C6, wing shade #0D7FCC
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Brand Color Variables ── */
:root {
  --bird-body:    #1BA0E2;
  --bird-wing:    #1494C6;
  --wing-shade:   #0D7FCC;
  --typeface:     #434343;
  --white:        #FFFFFF;
  --light-wing:   #F0F0F0;
  --light-shade:  #DEDEDE;

  --bg:           #F4F8FC;
  --surface:      #FFFFFF;
  --border:       #DCE8F5;
  --border-light: #EBF3FA;
  --text-primary: #434343;
  --text-secondary: #6B8299;
  --text-muted:   #9DB3C5;
}

html, body, [class*="css"] {
  font-family: 'DM Sans', sans-serif !important;
  background: var(--bg) !important;
  color: var(--text-primary) !important;
}

#MainMenu, footer, header { visibility: hidden }
.stDeployButton,
[data-testid="stToolbar"],
[data-testid="collapsedControl"] { display: none }

.main .block-container {
  padding: 0 0.75rem 3rem !important;
  max-width: 560px !important;
}

/* ── HERO ── */
.hero {
  background: var(--bird-body);
  margin: 0 -0.75rem;
  padding: 32px 24px 70px;
  position: relative;
  overflow: hidden;
}
.hero::before {
  content: '';
  position: absolute;
  top: -60px; right: -60px;
  width: 220px; height: 220px;
  border-radius: 50%;
  background: rgba(255,255,255,0.06);
  pointer-events: none;
}
.hero::after {
  content: '';
  position: absolute;
  bottom: -40px; left: -30px;
  width: 140px; height: 140px;
  border-radius: 50%;
  background: rgba(255,255,255,0.04);
  pointer-events: none;
}

.hero-eyebrow {
  display: inline-flex; align-items: center; gap: 7px;
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 100px;
  padding: 5px 13px;
  font-size: 10.5px; font-weight: 600; letter-spacing: 0.7px;
  text-transform: uppercase;
  color: rgba(255,255,255,0.92);
  margin-bottom: 14px;
}
.pulse {
  width: 7px; height: 7px;
  background: #FFFFFF;
  border-radius: 50%;
  display: inline-block;
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%,100% { opacity:1; transform:scale(1) }
  50%      { opacity:.4; transform:scale(.7) }
}

.hero-logo {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 10px;
}
.hero-logo-icon {
  width: 44px; height: 44px;
  background: rgba(255,255,255,0.2);
  border: 1.5px solid rgba(255,255,255,0.3);
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
}
.hero-logo-text {
  font-size: 13px; font-weight: 600;
  color: rgba(255,255,255,0.8);
  letter-spacing: 0.2px;
  line-height: 1.3;
}
.hero-logo-sub {
  font-size: 10.5px;
  color: rgba(255,255,255,0.55);
  font-weight: 400;
}

.hero-title {
  font-size: 26px !important; font-weight: 700 !important;
  color: #FFFFFF !important;
  letter-spacing: -0.6px; line-height: 1.2 !important;
  margin-bottom: 8px !important;
}
.hero-desc {
  font-size: 13px; color: rgba(255,255,255,0.72);
  line-height: 1.65; max-width: 400px;
  margin-bottom: 18px;
}

.hero-tags { display: flex; flex-wrap: wrap; gap: 7px; }
.hero-tag {
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 11px; font-weight: 500;
  color: rgba(255,255,255,0.85);
}

/* ── STEPS BAR ── */
.steps-wrap { padding: 0 2px; }
.steps-card {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 16px 18px;
  margin-top: -32px;
  position: relative; z-index: 10;
  box-shadow: 0 8px 32px rgba(20,148,198,0.12);
  display: flex; align-items: center;
}
.step-item { display: flex; align-items: center; gap: 7px; flex: 1; }
.step-num {
  width: 28px; height: 28px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; flex-shrink: 0;
}
.step-num.active { background: var(--bird-body); color: #fff; }
.step-num.done   { background: #E6F5FC; color: var(--bird-wing); border: 1.5px solid #B3DFF5; }
.step-num.idle   { background: var(--light-wing); color: var(--text-muted); border: 1.5px solid var(--light-shade); }
.step-txt { font-size: 10.5px; font-weight: 500; white-space: nowrap; }
.step-txt.active { color: var(--bird-body); font-weight: 700; }
.step-txt.done   { color: var(--text-secondary); }
.step-txt.idle   { color: var(--text-muted); }
.step-line { flex: 1; height: 1.5px; background: var(--light-shade); margin: 0 5px; max-width: 28px; }
.step-line.done { background: var(--bird-body); opacity: 0.35; }

/* ── CARD ── */
.card {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 0;
  margin-bottom: 12px;
  box-shadow: 0 2px 16px rgba(20,148,198,0.07);
  overflow: hidden;
}
.card-header {
  background: var(--bird-body);
  padding: 18px 20px 16px;
  display: flex; align-items: center; gap: 13px;
}
.card-header-icon {
  width: 42px; height: 42px;
  background: rgba(255,255,255,0.2);
  border-radius: 11px;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; flex-shrink: 0;
}
.card-header-step {
  font-size: 9.5px; font-weight: 700; letter-spacing: 0.8px;
  text-transform: uppercase;
  color: rgba(255,255,255,0.65);
  margin-bottom: 3px;
}
.card-header-title {
  font-size: 15px !important; font-weight: 700 !important;
  color: #fff !important; letter-spacing: -0.2px;
  margin: 0 !important;
}
.card-header-sub {
  font-size: 11.5px; color: rgba(255,255,255,0.65);
  margin-top: 2px;
}
.card-body { padding: 20px 18px; }

/* ── INFO BOX ── */
.info-box {
  display: flex; gap: 9px;
  background: #EBF6FD;
  border: 1px solid #B3DFF5;
  border-left: 3px solid var(--bird-body);
  border-radius: 8px;
  padding: 11px 13px;
  font-size: 12px; color: var(--wing-shade);
  line-height: 1.55; margin-bottom: 14px;
}

/* ── SECTION LABEL ── */
.sec-lbl {
  font-size: 10px; font-weight: 700; letter-spacing: 0.8px;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 16px 0 8px;
  display: flex; align-items: center; gap: 8px;
}
.sec-lbl::after { content: ''; flex: 1; height: 1px; background: var(--border-light); }

/* ── DATE HEADER ── */
.date-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px; margin-top: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-light);
}
.date-name { font-size: 13px; font-weight: 700; color: var(--typeface); }
.avail-pill {
  font-size: 10px; font-weight: 700;
  padding: 3px 10px; border-radius: 100px;
  letter-spacing: 0.2px;
}
.avail-ok   { background: #E6F5FC; color: var(--wing-shade); border: 1px solid #B3DFF5; }
.avail-part { background: #FEF9C3; color: #854D0E; border: 1px solid #FDE047; }
.avail-full { background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }

/* ── SLOT CARDS ── */
.slot-card {
  border-radius: 10px;
  padding: 11px 14px;
  margin-bottom: 7px;
  display: flex; align-items: center; justify-content: space-between;
  transition: all 0.15s ease;
}
.slot-available {
  border: 1.5px solid var(--border);
  background: #FAFCFE;
}
.slot-selected {
  border: 2px solid var(--bird-body);
  background: #EBF6FD;
}
.slot-taken {
  border: 1.5px solid var(--light-shade);
  background: var(--light-wing);
  opacity: 0.65;
  cursor: default;
}
.slot-label {
  font-size: 13px; font-weight: 600;
  color: var(--typeface);
}
.slot-taken .slot-label { color: var(--text-muted); text-decoration: line-through; }
.slot-selected .slot-label { color: var(--wing-shade); }
.slot-badge {
  font-size: 10px; font-weight: 700;
  padding: 3px 9px; border-radius: 6px;
  text-transform: uppercase; letter-spacing: 0.2px;
}
.badge-avail { background: #E6F5FC; color: var(--bird-wing); }
.badge-sel   { background: var(--bird-body); color: #fff; }
.badge-taken { background: var(--light-wing); color: var(--text-muted); }

/* ── SELECTED BAR ── */
.sel-bar {
  background: var(--bird-body);
  border-radius: 12px;
  padding: 13px 16px;
  margin: 12px 0;
  display: flex; align-items: center; justify-content: space-between;
}
.sel-bar-lbl {
  font-size: 9.5px; font-weight: 700; letter-spacing: 0.5px;
  text-transform: uppercase; color: rgba(255,255,255,0.6);
  margin-bottom: 3px;
}
.sel-bar-val { font-size: 13.5px; font-weight: 700; color: #fff; }

/* ── ALERTS ── */
.alert-block {
  background: #FEF2F2;
  border: 1px solid #FECACA;
  border-left: 3px solid #EF4444;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 12px;
  font-size: 12.5px; color: #7F1D1D;
}
.alert-ok {
  background: #EBF6FD;
  border: 1px solid #B3DFF5;
  border-left: 3px solid var(--bird-body);
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 12px;
  font-size: 12.5px; color: var(--wing-shade);
}
.alert-title { font-weight: 700; margin-bottom: 3px; font-size: 13px; }

/* ── REVIEW ROWS ── */
.review-row {
  display: flex;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 7px;
}
.review-lbl {
  width: 100px; flex-shrink: 0;
  background: #F4F8FC;
  padding: 9px 12px;
  font-size: 10px; font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase; letter-spacing: 0.4px;
  border-right: 1px solid var(--border-light);
}
.review-val {
  padding: 9px 13px;
  font-size: 13px; color: var(--typeface);
  font-weight: 500; flex: 1; word-break: break-word;
}

/* ── SUCCESS ── */
.success-box { text-align: center; padding: 32px 16px; }
.success-icon {
  width: 72px; height: 72px;
  margin: 0 auto 20px;
  background: var(--bird-body);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 30px;
}
.ref-badge {
  display: inline-block;
  background: var(--bg);
  border: 1.5px solid var(--border);
  border-radius: 8px;
  padding: 7px 18px;
  font-size: 13px; color: var(--typeface);
  font-family: 'DM Mono', monospace;
  letter-spacing: 2.5px;
  margin: 10px 0 16px;
}
.succ-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 8px; max-width: 360px;
  margin: 16px auto 0;
  text-align: left;
}
.succ-item {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 11px 13px;
}
.succ-lbl {
  font-size: 9.5px; text-transform: uppercase;
  letter-spacing: 0.6px; color: var(--text-muted);
  font-weight: 700; margin-bottom: 3px;
}
.succ-val { font-size: 13px; font-weight: 700; color: var(--typeface); }

/* ── DIVIDER ── */
.sec-div { border: none; border-top: 1px solid var(--border-light); margin: 14px 0; }

/* ── FOOTER ── */
.footer {
  text-align: center;
  padding: 20px 0 30px;
  font-size: 11px; color: var(--text-muted);
}

/* ── BUTTONS ── */
div[data-testid="stButton"] > button[kind="primary"] {
  background: var(--bird-body) !important;
  border: none !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  padding: 11px 20px !important;
  width: 100% !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
  background: var(--bird-wing) !important;
}
div[data-testid="stButton"] > button[kind="secondary"] {
  border: 1.5px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--text-secondary) !important;
  background: var(--white) !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  width: 100% !important;
}

/* ── INPUTS ── */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
  border: 1.5px solid var(--border) !important;
  border-radius: 9px !important;
  font-size: 14px !important;
  font-family: 'DM Sans', sans-serif !important;
  background: #FAFCFE !important;
  color: var(--typeface) !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
  border-color: var(--bird-body) !important;
  box-shadow: 0 0 0 3px rgba(27,160,226,0.12) !important;
  background: #fff !important;
}
label { color: var(--text-secondary) !important; font-size: 13px !important; }

/* selectbox */
div[data-testid="stSelectbox"] > div > div {
  border: 1.5px solid var(--border) !important;
  border-radius: 9px !important;
  background: #FAFCFE !important;
}
</style>""", unsafe_allow_html=True)


# ── UI HELPERS ────────────────────────────────────────────────────
def render_hero():
    st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">
    <span class="pulse"></span>&nbsp;Sistem Aktif
  </div>
  <div class="hero-logo">
    <div class="hero-logo-icon"><img src="data:image/png;base64,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" style="width:40px;height:40px;object-fit:contain;border-radius:6px;"></div>
    <div>
      <div class="hero-logo-text">Mitra Tours &amp; Travel</div>
      <div class="hero-logo-sub">Visitor Appointment System</div>
    </div>
  </div>
  <div class="hero-title">Ajukan Jadwal<br>Kunjungan Sales</div>
  <div class="hero-desc">
    Daftarkan kunjungan ke kantor kami dengan mudah.
    Slot real-time dari Google Sheets — anti double booking.
  </div>
  <div class="hero-tags">
    <span class="hero-tag">✓ Cek slot real-time</span>
    <span class="hero-tag">📅 Hanya hari Selasa</span>
    <span class="hero-tag">🔒 Anti double booking</span>
    <span class="hero-tag">📱 Konfirmasi WhatsApp</span>
  </div>
</div>""", unsafe_allow_html=True)


def render_steps(current: int):
    labels = ["Hotel", "Kontak", "Jadwal", "Kirim"]
    html = '<div class="steps-wrap"><div class="steps-card">'
    for i, lbl in enumerate(labels, 1):
        if i < current:
            cls = "done"; num_html = "✓"
        elif i == current:
            cls = "active"; num_html = str(i)
        else:
            cls = "idle"; num_html = str(i)
        html += (
            f'<div class="step-item">'
            f'<div class="step-num {cls}">{num_html}</div>'
            f'<span class="step-txt {cls}">{lbl}</span>'
            f'</div>'
        )
        if i < 4:
            line_cls = "done" if i < current else ""
            html += f'<div class="step-line {line_cls}"></div>'
    html += "</div></div>"
    st.markdown(html, unsafe_allow_html=True)
    st.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)


def card_open(icon, step_label, title, sub=""):
    sub_html = f'<div class="card-header-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
<div class="card">
  <div class="card-header">
    <div class="card-header-icon">{icon}</div>
    <div>
      <div class="card-header-step">{step_label}</div>
      <div class="card-header-title">{title}</div>
      {sub_html}
    </div>
  </div>
  <div class="card-body">""", unsafe_allow_html=True)

def card_close():
    st.markdown("</div></div>", unsafe_allow_html=True)

def sec_lbl(txt):
    st.markdown(f'<div class="sec-lbl">{txt}</div>', unsafe_allow_html=True)

def info_box(txt):
    st.markdown(
        f'<div class="info-box"><span>ℹ️</span><div>{txt}</div></div>',
        unsafe_allow_html=True)


# ── VALIDATION ────────────────────────────────────────────────────
def valid_email(e):
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", e.strip()))

def validate_step1():
    ok = True
    if not st.session_state.nama_hotel.strip():
        st.error("Nama hotel wajib diisi"); ok = False
    if not st.session_state.alamat_hotel.strip():
        st.error("Alamat hotel wajib diisi"); ok = False
    return ok

def validate_step2():
    ok = True
    if not st.session_state.nama_pic.strip():
        st.error("Nama PIC wajib diisi"); ok = False
    if not st.session_state.jabatan.strip():
        st.error("Jabatan wajib diisi"); ok = False
    if not st.session_state.no_hp.strip():
        st.error("Nomor WhatsApp wajib diisi"); ok = False
    if not st.session_state.email.strip():
        st.error("Email wajib diisi"); ok = False
    elif not valid_email(st.session_state.email):
        st.error("Format email tidak valid"); ok = False
    return ok

def validate_step3(booked):
    ok = True
    if not st.session_state.sel_date_key or not st.session_state.sel_sess_value:
        st.error("Pilih tanggal dan slot waktu kunjungan"); ok = False
    elif is_booked(booked, st.session_state.sel_date_key, st.session_state.sel_sess_value):
        alts = get_alternatives(booked, st.session_state.sel_date_key, st.session_state.sel_sess_value)
        st.session_state.conflict_type  = "blocking"
        st.session_state.conflict_msg   = "Slot yang dipilih sudah terisi hotel lain."
        st.session_state.alternatives   = alts
        for k in ("sel_date_key","sel_date_label","sel_sess_value","sel_sess_label"):
            st.session_state[k] = None
        ok = False
    if not st.session_state.tujuan:
        st.error("Pilih minimal satu tujuan kunjungan"); ok = False
    if not st.session_state.durasi:
        st.error("Estimasi durasi wajib dipilih"); ok = False
    return ok


# ── STEP 1 ────────────────────────────────────────────────────────
def render_step1():
    card_open("🏨", "Langkah 1 dari 3", "Informasi Hotel", "Data properti hotel Anda")

    st.session_state.nama_hotel = st.text_input(
        "Nama Hotel / Property *",
        value=st.session_state.nama_hotel,
        placeholder="Contoh: Grand Hyatt Jakarta",
        key="inp_nama_hotel")

    st.session_state.alamat_hotel = st.text_area(
        "Alamat Hotel *",
        value=st.session_state.alamat_hotel,
        placeholder="Alamat lengkap hotel...",
        height=80, key="inp_alamat")

    opts = HOTEL_BRANDS
    idx  = opts.index(st.session_state.brand_hotel) if st.session_state.brand_hotel in opts else 0
    st.session_state.brand_hotel = st.selectbox(
        "Brand / Chain Hotel (opsional)", options=opts, index=idx, key="inp_brand",
        format_func=lambda x: "— Pilih Brand / Chain —" if x == "" else x)

    card_close()

    if st.button("Lanjut ke Kontak →", type="primary", key="btn1"):
        if validate_step1():
            st.session_state.step = 2
            st.rerun()


# ── STEP 2 ────────────────────────────────────────────────────────
def render_step2():
    card_open("👤", "Langkah 2 dari 3", "Data PIC & Kontak", "Penanggung jawab kunjungan")

    st.session_state.nama_pic = st.text_input(
        "Nama PIC Utama *", value=st.session_state.nama_pic,
        placeholder="Nama lengkap", key="inp_nama_pic")

    col1, col2 = st.columns(2)
    with col1:
        st.session_state.jabatan = st.text_input(
            "Jabatan *", value=st.session_state.jabatan,
            placeholder="Sales Manager, GM...", key="inp_jabatan")
    with col2:
        st.session_state.no_hp = st.text_input(
            "WhatsApp *", value=st.session_state.no_hp,
            placeholder="08xx-xxxx-xxxx", key="inp_no_hp")

    st.session_state.email = st.text_input(
        "Email *", value=st.session_state.email,
        placeholder="nama@hotel.com", key="inp_email")

    sec_lbl("Jumlah Peserta")
    p_opts = ["1 orang (PIC saja)", "2 orang", "3 orang", "4 orang", "5 orang"]
    cur_p  = p_opts.index(st.session_state.peserta) if st.session_state.peserta in p_opts else 0
    st.session_state.peserta = st.radio(
        "Peserta", options=p_opts, index=cur_p, horizontal=True,
        label_visibility="collapsed", key="inp_peserta")

    card_close()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Kembali", key="btn2_back"):
            st.session_state.step = 1; st.rerun()
    with col2:
        if st.button("Lanjut ke Jadwal →", type="primary", key="btn2_next"):
            if validate_step2():
                _fetch_booked_cached.clear()
                st.session_state.step = 3; st.rerun()


# ── STEP 3 ────────────────────────────────────────────────────────
def render_step3():
    booked = fetch_booked_slots()

    card_open("📅", "Langkah 3 dari 3", "Pilih Jadwal Kunjungan",
              "Slot tersedia real-time dari Google Sheets")

    info_box("Kunjungan hanya setiap <strong>Selasa</strong>. Setiap slot untuk <strong>1 hotel</strong>.")

    # Conflict alerts
    if st.session_state.conflict_type == "blocking":
        st.markdown(
            f'<div class="alert-block">'
            f'<div class="alert-title">⛔ Slot tidak tersedia!</div>'
            f'{st.session_state.conflict_msg}</div>',
            unsafe_allow_html=True)
        if st.session_state.alternatives:
            st.markdown("**Slot alternatif:**")
            for alt in st.session_state.alternatives:
                btn_lbl = f"{alt['date_label']}  ·  {alt['sess_label']}"
                if st.button(btn_lbl, key=f"alt_{alt['date_key']}_{alt['sess_value']}"):
                    st.session_state.sel_date_key   = alt["date_key"]
                    st.session_state.sel_date_label = alt["date_label"]
                    st.session_state.sel_sess_value = alt["sess_value"]
                    st.session_state.sel_sess_label = alt["sess_label"]
                    st.session_state.conflict_type  = "ok"
                    st.session_state.conflict_msg   = f"Slot dipilih: {alt['date_label']} - {alt['sess_label']}"
                    st.session_state.alternatives   = []
                    st.rerun()

    elif st.session_state.conflict_type == "ok":
        st.markdown(
            f'<div class="alert-ok">'
            f'<div class="alert-title">✓ Slot tersedia!</div>'
            f'{st.session_state.conflict_msg}</div>',
            unsafe_allow_html=True)

    # Slot picker
    for dt in DATES:
        free  = [s for s in SESSIONS if not is_booked(booked, dt["key"], s["value"])]
        taken = [s for s in SESSIONS if is_booked(booked, dt["key"], s["value"])]
        all_full = len(free) == 0

        if all_full:
            pill_cls = "avail-full"; pill_txt = "Penuh"
        elif taken:
            pill_cls = "avail-part"; pill_txt = f"{len(free)} slot tersisa"
        else:
            pill_cls = "avail-ok";  pill_txt = f"{len(free)} slot tersedia"

        st.markdown(
            f'<div class="date-header">'
            f'<span class="date-name">{dt["label"]}</span>'
            f'<span class="avail-pill {pill_cls}">{pill_txt}</span>'
            f'</div>',
            unsafe_allow_html=True)

        if all_full:
            st.caption("Semua slot penuh untuk tanggal ini.")
            continue

        for sess in SESSIONS:
            is_taken  = is_booked(booked, dt["key"], sess["value"])
            is_picked = (st.session_state.sel_date_key == dt["key"] and
                         st.session_state.sel_sess_value == sess["value"])
            s_lbl = sess["label"]

            if is_taken:
                st.markdown(
                    f'<div class="slot-card slot-taken">'
                    f'<span class="slot-label">{s_lbl}</span>'
                    f'<span class="slot-badge badge-taken">Penuh</span>'
                    f'</div>',
                    unsafe_allow_html=True)
            else:
                card_cls   = "slot-selected" if is_picked else "slot-available"
                badge_cls2 = "badge-sel" if is_picked else "badge-avail"
                badge_txt2 = "Dipilih ✓" if is_picked else "Tersedia"
                btn_label  = "Dipilih ✓" if is_picked else "Pilih"

                st.markdown(
                    f'<div class="slot-card {card_cls}">'
                    f'<span class="slot-label">{s_lbl}</span>'
                    f'<span class="slot-badge {badge_cls2}">{badge_txt2}</span>'
                    f'</div>',
                    unsafe_allow_html=True)

                btn_key = f"slot_{dt['key']}_{sess['id']}"
                if st.button(btn_label, key=btn_key, use_container_width=True):
                    _fetch_booked_cached.clear()
                    fresh = fetch_booked_slots()
                    if is_booked(fresh, dt["key"], sess["value"]):
                        alts = get_alternatives(fresh, dt["key"], sess["value"])
                        st.session_state.conflict_type = "blocking"
                        st.session_state.conflict_msg  = f"Slot {s_lbl} pada {dt['label']} baru saja diisi hotel lain."
                        st.session_state.alternatives  = alts
                    else:
                        st.session_state.sel_date_key   = dt["key"]
                        st.session_state.sel_date_label = dt["label"]
                        st.session_state.sel_sess_value = sess["value"]
                        st.session_state.sel_sess_label = sess["label"]
                        st.session_state.conflict_type  = "ok"
                        st.session_state.conflict_msg   = f"{dt['label']} - {sess['label']} siap di-booking."
                        st.session_state.alternatives   = []
                    st.rerun()

    # Selected summary bar
    if st.session_state.sel_date_key and st.session_state.sel_sess_value:
        sel_dl = st.session_state.sel_date_label
        sel_sl = st.session_state.sel_sess_label
        st.markdown(
            f'<div class="sel-bar">'
            f'<div><div class="sel-bar-lbl">Jadwal Dipilih</div>'
            f'<div class="sel-bar-val">{sel_dl} &nbsp;·&nbsp; {sel_sl}</div></div>'
            f'<div style="color:rgba(255,255,255,.5);font-size:18px">✓</div>'
            f'</div>',
            unsafe_allow_html=True)
        if st.button("Batalkan pilihan", key="clear_slot"):
            st.session_state.sel_date_key = st.session_state.sel_date_label = None
            st.session_state.sel_sess_value = st.session_state.sel_sess_label = None
            st.session_state.conflict_type = None; st.session_state.alternatives = []
            st.rerun()

    st.markdown('<hr class="sec-div">', unsafe_allow_html=True)

    sec_lbl("Tujuan Kunjungan")
    tujuan_selected = []
    col1, col2 = st.columns(2)
    for i, tuj in enumerate(TUJUAN_OPTIONS):
        with (col1 if i % 2 == 0 else col2):
            if st.checkbox(tuj, value=(tuj in st.session_state.tujuan), key=f"tuj_{i}"):
                tujuan_selected.append(tuj)
    st.session_state.tujuan = tujuan_selected

    sec_lbl("Estimasi Durasi")
    d_opts = ["15 Menit", "30 Menit", "45 Menit"]
    cur_d  = d_opts.index(st.session_state.durasi) if st.session_state.durasi in d_opts else 0
    st.session_state.durasi = st.radio(
        "Durasi", options=d_opts, index=cur_d, horizontal=True,
        label_visibility="collapsed", key="inp_durasi")

    sec_lbl("Catatan Tambahan")
    st.session_state.catatan = st.text_area(
        "Catatan", value=st.session_state.catatan,
        placeholder="Informasi tambahan (opsional)...", height=80,
        label_visibility="collapsed", key="inp_catatan")

    card_close()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Kembali", key="btn3_back"):
            st.session_state.step = 2; st.rerun()
    with col2:
        if st.button("Review & Kirim →", type="primary", key="btn3_next"):
            fresh_b = fetch_booked_slots()
            if validate_step3(fresh_b):
                st.session_state.step = 4; st.rerun()


# ── STEP 4 — REVIEW & SUBMIT ──────────────────────────────────────
def render_step4():
    card_open("📋", "Konfirmasi", "Review Permohonan", "Periksa semua data sebelum mengirim")

    rows = [
        ("Hotel",    st.session_state.nama_hotel),
        ("Alamat",   st.session_state.alamat_hotel),
        ("Brand",    st.session_state.brand_hotel or "—"),
        ("Nama PIC", st.session_state.nama_pic),
        ("Jabatan",  st.session_state.jabatan),
        ("WhatsApp", st.session_state.no_hp),
        ("Email",    st.session_state.email),
        ("Peserta",  st.session_state.peserta),
        ("Tanggal",  st.session_state.sel_date_label or "—"),
        ("Slot",     st.session_state.sel_sess_label or "—"),
        ("Durasi",   st.session_state.durasi or "—"),
        ("Tujuan",   ", ".join(st.session_state.tujuan) or "—"),
    ]
    if st.session_state.catatan:
        rows.append(("Catatan", st.session_state.catatan))

    for lbl, val in rows:
        st.markdown(
            f'<div class="review-row">'
            f'<div class="review-lbl">{lbl}</div>'
            f'<div class="review-val">{val}</div>'
            f'</div>',
            unsafe_allow_html=True)

    info_box("Dengan mengirimkan formulir ini, Anda bersedia dihubungi via WhatsApp atau Email untuk konfirmasi jadwal.")

    card_close()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Edit Data", key="btn4_back"):
            st.session_state.step = 3; st.rerun()
    with col2:
        if st.button("Kirim Permohonan ✉️", type="primary", key="btn4_submit"):
            do_submit()


def do_submit():
    _fetch_booked_cached.clear()
    fresh = fetch_booked_slots()
    dk = st.session_state.sel_date_key
    sv = st.session_state.sel_sess_value

    if is_booked(fresh, dk, sv):
        alts = get_alternatives(fresh, dk, sv)
        st.session_state.conflict_type = "blocking"
        st.session_state.conflict_msg  = f"Slot {st.session_state.sel_sess_label} pada {st.session_state.sel_date_label} baru saja dipesan hotel lain."
        st.session_state.alternatives  = alts
        for k in ("sel_date_key","sel_date_label","sel_sess_value","sel_sess_label"):
            st.session_state[k] = None
        st.session_state.step = 3; st.rerun(); return

    wib = datetime.now(ZoneInfo("Asia/Jakarta"))
    ref = generate_ref()

    payload = {
        "ref":         ref,
        "timestamp":   wib.strftime("%d/%m/%Y %H:%M:%S"),
        "namaHotel":   st.session_state.nama_hotel,
        "alamatHotel": st.session_state.alamat_hotel,
        "brand":       st.session_state.brand_hotel or "—",
        "namaPIC":     st.session_state.nama_pic,
        "jabatan":     st.session_state.jabatan,
        "noHP":        st.session_state.no_hp,
        "email":       st.session_state.email,
        "peserta":     st.session_state.peserta,
        "tujuan":      ", ".join(st.session_state.tujuan),
        "tanggal":     dk + " (Selasa)",
        "slot":        sv,
        "durasi":      st.session_state.durasi or "",
        "catatan":     st.session_state.catatan or "",
        "notifEmail":  NOTIF_EMAIL,
    }

    with st.spinner("Menyimpan & mengirim notifikasi..."):
        ok, result = save_to_gas(payload)

    if ok:
        st.session_state.ref_number = result or ref
        st.session_state.submitted  = True
        st.session_state.step       = 5
        _fetch_booked_cached.clear()
        st.rerun()
    elif result == "SLOT_TAKEN":
        _fetch_booked_cached.clear()
        fresh2 = fetch_booked_slots()
        alts   = get_alternatives(fresh2, dk, sv)
        st.session_state.conflict_type = "blocking"
        st.session_state.conflict_msg  = f"Slot {st.session_state.sel_sess_label} pada {st.session_state.sel_date_label} baru saja dipesan saat Anda submit."
        st.session_state.alternatives  = alts
        for k in ("sel_date_key","sel_date_label","sel_sess_value","sel_sess_label"):
            st.session_state[k] = None
        st.session_state.step = 3; st.rerun()
    else:
        st.error(f"Gagal menyimpan: {result}")


# ── STEP 5 — SUCCESS ──────────────────────────────────────────────
def render_success():
    ref   = st.session_state.ref_number
    pic   = st.session_state.nama_pic
    hotel = st.session_state.nama_hotel
    tgl   = st.session_state.sel_date_label
    slot  = st.session_state.sel_sess_label

    st.markdown('<div class="card"><div class="card-body">', unsafe_allow_html=True)
    st.markdown(f"""
<div class="success-box">
  <div class="success-icon">✓</div>
  <h2 style="font-size:21px;font-weight:700;color:#434343;margin-bottom:6px;letter-spacing:-.3px">
    Permohonan Terkirim!
  </h2>
  <p style="font-size:13px;color:#6B8299;line-height:1.7;margin-bottom:6px">
    Terima kasih! Permohonan kunjungan Anda sudah kami terima.<br>
    Notifikasi dikirim ke <strong style="color:#1494C6">d4t4m1tr4@gmail.com</strong><br>
    Konfirmasi akan dikirimkan dalam 1–2 hari kerja.
  </p>
  <div class="ref-badge">{ref}</div>
  <p style="font-size:11.5px;color:#9DB3C5;margin-bottom:0">
    Simpan nomor referensi untuk keperluan tindak lanjut.
  </p>
  <div class="succ-grid">
    <div class="succ-item"><div class="succ-lbl">Nama PIC</div><div class="succ-val">{pic}</div></div>
    <div class="succ-item"><div class="succ-lbl">Hotel</div><div class="succ-val">{hotel}</div></div>
    <div class="succ-item"><div class="succ-lbl">Tanggal</div><div class="succ-val">{tgl}</div></div>
    <div class="succ-item"><div class="succ-lbl">Slot</div><div class="succ-val">{slot}</div></div>
  </div>
</div>
""", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("+ Ajukan Kunjungan Baru", key="btn_reset"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ── MAIN ──────────────────────────────────────────────────────────
def main():
    init_state()
    inject_css()
    render_hero()

    s = st.session_state.step
    if s < 5:
        render_steps(s)

    if   s == 1: render_step1()
    elif s == 2: render_step2()
    elif s == 3: render_step3()
    elif s == 4: render_step4()
    elif s == 5: render_success()

    st.markdown(
        '<div class="footer">'
        'VisitorPass &nbsp;·&nbsp; Mitra Tours &amp; Travel'
        '&nbsp;·&nbsp; Data tersimpan di Google Sheets'
        '</div>',
        unsafe_allow_html=True)

if __name__ == "__main__":
    main()
