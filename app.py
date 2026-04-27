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
    {"key": "6 Mei 2026",  "label": "Selasa, 6 Mei 2026",  "day": "6",  "month": "MEI"},
    {"key": "13 Mei 2026", "label": "Selasa, 13 Mei 2026", "day": "13", "month": "MEI"},
    {"key": "20 Mei 2026", "label": "Selasa, 20 Mei 2026", "day": "20", "month": "MEI"},
    {"key": "27 Mei 2026", "label": "Selasa, 27 Mei 2026", "day": "27", "month": "MEI"},
    {"key": "2 Jun 2026",  "label": "Selasa, 2 Jun 2026",  "day": "2",  "month": "JUN"},
    {"key": "9 Jun 2026",  "label": "Selasa, 9 Jun 2026",  "day": "9",  "month": "JUN"},
    {"key": "23 Jun 2026", "label": "Selasa, 23 Jun 2026", "day": "23", "month": "JUN"},
    {"key": "30 Jun 2026", "label": "Selasa, 30 Jun 2026", "day": "30", "month": "JUN"},
    {"key": "7 Jul 2026",  "label": "Selasa, 7 Jul 2026",  "day": "7",  "month": "JUL"},
    {"key": "14 Jul 2026", "label": "Selasa, 14 Jul 2026", "day": "14", "month": "JUL"},
    {"key": "21 Jul 2026", "label": "Selasa, 21 Jul 2026", "day": "21", "month": "JUL"},
    {"key": "28 Jul 2026", "label": "Selasa, 28 Jul 2026", "day": "28", "month": "JUL"},
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

# ── GAS WRITE ────────────────────────────────────────────────────
def save_to_gas(payload: dict) -> tuple:
    try:
        payload["notifEmail"] = NOTIF_EMAIL
        import json as _json
        session = requests.Session()
        resp = session.post(
            GAS_ENDPOINT,
            data=_json.dumps(payload),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            allow_redirects=True, timeout=30,
        )
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
        resp2 = session.post(
            GAS_ENDPOINT + "?method=POST",
            data=_json.dumps(payload),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            allow_redirects=True, timeout=30,
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
        import urllib.parse as _up
        params = _up.urlencode({"payload": _json.dumps(payload), "action": "write"})
        resp3 = session.get(GAS_ENDPOINT + "?" + params, allow_redirects=True, timeout=30)
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
        "expanded_date": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── CSS ───────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

:root {
  --blue:    #0659a7;
  --blue-d:  #044d8f;
  --blue-l:  #e8f1fb;
  --blue-m:  #b3d0ef;
  --green:   #8dbc65;
  --green-d: #6fa048;
  --green-l: #eef6e6;
  --green-m: #c5e0a8;
  --red:     #ec1a23;
  --red-l:   #fdeaea;
  --red-m:   #f9b3b6;
  --text:    #2d3748;
  --text2:   #64748b;
  --text3:   #94a3b8;
  --bg:      #f5f8fc;
  --white:   #ffffff;
  --border:  #dce8f5;
  --border2: #edf2f9;
}

html,body,[class*="css"]{font-family:'DM Sans',sans-serif!important;background:var(--bg)!important;color:var(--text)!important}
#MainMenu,footer,header{visibility:hidden}
.stDeployButton,[data-testid="stToolbar"],[data-testid="collapsedControl"]{display:none}
.main .block-container{padding:0 0.75rem 3rem!important;max-width:580px!important}

/* HERO */
.hero{background:var(--blue);margin:0 -0.75rem;padding:30px 24px 66px;position:relative;overflow:hidden}
.hero::before{content:'';position:absolute;top:-60px;right:-60px;width:200px;height:200px;border-radius:50%;background:rgba(255,255,255,.05);pointer-events:none}
.hero::after{content:'';position:absolute;bottom:-40px;left:-30px;width:130px;height:130px;border-radius:50%;background:rgba(141,188,101,.08);pointer-events:none}
.hero-eyebrow{display:inline-flex;align-items:center;gap:7px;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.22);border-radius:100px;padding:5px 13px;font-size:10.5px;font-weight:600;letter-spacing:.7px;text-transform:uppercase;color:rgba(255,255,255,.92);margin-bottom:14px}
.pulse{width:7px;height:7px;background:#8dbc65;border-radius:50%;display:inline-block;animation:pls 2s ease-in-out infinite}
@keyframes pls{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.7)}}
.hero-title{font-size:26px!important;font-weight:700!important;color:#fff!important;letter-spacing:-.6px;line-height:1.2!important;margin-bottom:8px!important}
.hero-desc{font-size:13px;color:rgba(255,255,255,.7);line-height:1.65;margin-bottom:18px}
.hero-tags{display:flex;flex-wrap:wrap;gap:7px}
.hero-tag{background:rgba(255,255,255,.11);border:1px solid rgba(255,255,255,.18);border-radius:6px;padding:4px 10px;font-size:11px;font-weight:500;color:rgba(255,255,255,.85)}
.hero-tag.green{background:rgba(141,188,101,.18);border-color:rgba(141,188,101,.35);color:#c5e8a0}

/* STEPS */
.steps-wrap{padding:0 2px}
.steps-card{background:var(--white);border:1px solid var(--border);border-radius:16px;padding:15px 18px;margin-top:-32px;position:relative;z-index:10;box-shadow:0 8px 32px rgba(6,89,167,.1);display:flex;align-items:center}
.step-item{display:flex;align-items:center;gap:7px;flex:1}
.step-num{width:27px;height:27px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0}
.step-num.active{background:var(--blue);color:#fff}
.step-num.done{background:var(--green-l);color:var(--green-d);border:1.5px solid var(--green-m)}
.step-num.idle{background:var(--bg);color:var(--text3);border:1.5px solid var(--border)}
.step-txt{font-size:10.5px;font-weight:500;white-space:nowrap}
.step-txt.active{color:var(--blue);font-weight:700}
.step-txt.done{color:var(--text2)}
.step-txt.idle{color:var(--text3)}
.step-line{flex:1;height:1.5px;background:var(--border);margin:0 4px;max-width:28px}
.step-line.done{background:var(--blue-m)}

/* CARD */
.card{background:var(--white);border:1px solid var(--border);border-radius:18px;overflow:hidden;margin-bottom:12px;box-shadow:0 2px 16px rgba(6,89,167,.07)}
.card-header{background:var(--blue);padding:17px 20px 15px;display:flex;align-items:center;gap:13px}
.card-icon{width:40px;height:40px;background:rgba(255,255,255,.18);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:19px;flex-shrink:0}
.card-step{font-size:9.5px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:rgba(255,255,255,.6);margin-bottom:2px}
.card-title{font-size:15px!important;font-weight:700!important;color:#fff!important;letter-spacing:-.2px;margin:0!important}
.card-sub{font-size:11.5px;color:rgba(255,255,255,.6);margin-top:2px}
.card-body{padding:20px 18px}

/* INFO BOX */
.info-box{display:flex;gap:9px;background:var(--blue-l);border:1px solid var(--blue-m);border-left:3px solid var(--blue);border-radius:8px;padding:11px 13px;font-size:12px;color:var(--blue);line-height:1.55;margin-bottom:14px}

/* SECTION LABEL */
.sec-lbl{font-size:10px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;color:var(--text3);margin:16px 0 8px;display:flex;align-items:center;gap:8px}
.sec-lbl::after{content:'';flex:1;height:1px;background:var(--border2)}

/* ═══════════════════════════════════════
   DATE ACCORDION — mirip screenshot
═══════════════════════════════════════ */
.date-hint{font-size:12px;color:var(--text2);margin-bottom:10px;display:flex;align-items:center;gap:6px}

.date-row{
  display:flex;align-items:center;
  background:var(--white);
  border:1px solid var(--border2);
  border-radius:12px;
  padding:12px 14px;
  margin-bottom:8px;
  cursor:pointer;
  transition:border-color .15s,box-shadow .15s;
  gap:13px;
}
.date-row:hover{border-color:var(--blue-m);box-shadow:0 2px 10px rgba(6,89,167,.08)}
.date-row.expanded{border-color:var(--blue);box-shadow:0 2px 14px rgba(6,89,167,.12);border-radius:12px 12px 0 0;margin-bottom:0}
.date-row.selected{border-color:var(--green);background:var(--green-l)}
.date-row.full{background:#fafafa;opacity:.8}

/* Calendar mini */
.cal-box{width:46px;flex-shrink:0;text-align:center;background:var(--blue-l);border:1px solid var(--blue-m);border-radius:8px;padding:4px 2px;min-width:46px}
.date-row.selected .cal-box{background:var(--green-l);border-color:var(--green-m)}
.date-row.full .cal-box{background:#f1f5f9;border-color:#e2e8f0}
.cal-day{font-size:20px;font-weight:800;color:var(--blue);line-height:1}
.cal-month{font-size:9px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:var(--blue);margin-top:1px}
.date-row.selected .cal-day,.date-row.selected .cal-month{color:var(--green-d)}
.date-row.full .cal-day,.date-row.full .cal-month{color:var(--text3)}

/* Date info */
.date-info{flex:1}
.date-name-txt{font-size:14px;font-weight:600;color:var(--text)}
.date-row.full .date-name-txt{color:var(--text3)}
.date-dow{font-size:11px;color:var(--text3);margin-top:1px}

/* Availability pill */
.avail-pill{font-size:10.5px;font-weight:700;padding:4px 10px;border-radius:20px;white-space:nowrap}
.pill-ok{background:var(--green-l);color:var(--green-d);border:1px solid var(--green-m)}
.pill-part{background:#fffbeb;color:#92400e;border:1px solid #fde68a}
.pill-full{background:var(--red-l);color:var(--red);border:1px solid var(--red-m)}
.pill-sel{background:var(--green);color:#fff}

/* Arrow */
.date-arrow{font-size:14px;color:var(--text3);flex-shrink:0;transition:transform .2s;margin-left:4px}
.expanded .date-arrow,.date-row.expanded .date-arrow{transform:rotate(180deg)}

/* Slot panel (expanded) */
.slot-panel{
  border:1px solid var(--blue);
  border-top:none;
  border-radius:0 0 12px 12px;
  padding:10px 14px 12px;
  background:#fafcff;
  margin-bottom:8px;
}

.slot-item{
  display:flex;align-items:center;justify-content:space-between;
  border:1.5px solid var(--border);
  border-radius:9px;
  padding:10px 13px;
  margin-bottom:7px;
  background:var(--white);
  cursor:pointer;
}
.slot-item:last-child{margin-bottom:0}
.slot-item.av{border-color:var(--border2);background:#fafcff}
.slot-item.sel{border-color:var(--blue);background:var(--blue-l)}
.slot-item.full{border-color:var(--border2);background:#f8f9fa;opacity:.65;cursor:default}
.slot-time{font-size:13px;font-weight:600;color:var(--text)}
.slot-item.sel .slot-time{color:var(--blue)}
.slot-item.full .slot-time{text-decoration:line-through;color:var(--text3)}
.slot-badge{font-size:10px;font-weight:700;padding:3px 9px;border-radius:6px;text-transform:uppercase;letter-spacing:.2px}
.sbadge-av{background:var(--blue-l);color:var(--blue)}
.sbadge-sel{background:var(--blue);color:#fff}
.sbadge-full{background:var(--red-l);color:var(--red)}

/* SELECTED BAR */
.sel-bar{background:var(--blue);border-radius:12px;padding:13px 16px;margin:10px 0;display:flex;align-items:center;justify-content:space-between}
.sel-bar-lbl{font-size:9.5px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:rgba(255,255,255,.6);margin-bottom:2px}
.sel-bar-val{font-size:13.5px;font-weight:700;color:#fff}

/* ALERTS */
.alert-block{background:var(--red-l);border:1px solid var(--red-m);border-left:3px solid var(--red);border-radius:10px;padding:12px 14px;margin-bottom:12px;font-size:12.5px;color:#7f1d1d}
.alert-ok{background:var(--green-l);border:1px solid var(--green-m);border-left:3px solid var(--green);border-radius:10px;padding:12px 14px;margin-bottom:12px;font-size:12.5px;color:var(--green-d)}
.alert-title{font-weight:700;margin-bottom:3px;font-size:13px}

/* REVIEW */
.review-row{display:flex;border:1px solid var(--border2);border-radius:8px;overflow:hidden;margin-bottom:7px}
.review-lbl{width:100px;flex-shrink:0;background:var(--bg);padding:9px 12px;font-size:10px;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:.4px;border-right:1px solid var(--border2)}
.review-val{padding:9px 13px;font-size:13px;color:var(--text);font-weight:500;flex:1;word-break:break-word}

/* SUCCESS */
.success-box{text-align:center;padding:32px 16px}
.success-icon{width:70px;height:70px;margin:0 auto 18px;background:var(--green);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:28px}
.ref-badge{display:inline-block;background:var(--bg);border:1.5px solid var(--border);border-radius:8px;padding:7px 18px;font-size:13px;color:var(--text);font-family:'DM Mono',monospace;letter-spacing:2.5px;margin:10px 0 16px}
.succ-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;max-width:360px;margin:16px auto 0;text-align:left}
.succ-item{background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:11px 13px}
.succ-lbl{font-size:9.5px;text-transform:uppercase;letter-spacing:.6px;color:var(--text3);font-weight:700;margin-bottom:3px}
.succ-val{font-size:13px;font-weight:700;color:var(--text)}

.sec-div{border:none;border-top:1px solid var(--border2);margin:14px 0}
.footer{text-align:center;padding:20px 0 30px;font-size:11px;color:var(--text3)}

/* BUTTONS */
div[data-testid="stButton"]>button[kind="primary"]{background:var(--blue)!important;border:none!important;border-radius:10px!important;font-weight:600!important;font-size:14px!important;padding:11px 20px!important;width:100%!important}
div[data-testid="stButton"]>button[kind="primary"]:hover{background:var(--blue-d)!important}
div[data-testid="stButton"]>button[kind="secondary"]{border:1.5px solid var(--border)!important;border-radius:10px!important;color:var(--text2)!important;background:var(--white)!important;font-weight:600!important;font-size:14px!important;width:100%!important}

/* INPUTS */
div[data-testid="stTextInput"] input,div[data-testid="stTextArea"] textarea{border:1.5px solid var(--border)!important;border-radius:9px!important;font-size:14px!important;font-family:'DM Sans',sans-serif!important;background:#fafcfe!important;color:var(--text)!important}
div[data-testid="stTextInput"] input:focus,div[data-testid="stTextArea"] textarea:focus{border-color:var(--blue)!important;box-shadow:0 0 0 3px rgba(6,89,167,.1)!important;background:#fff!important}
label{color:var(--text2)!important;font-size:13px!important}
div[data-testid="stSelectbox"]>div>div{border:1.5px solid var(--border)!important;border-radius:9px!important;background:#fafcfe!important}
</style>""", unsafe_allow_html=True)


# ── UI HELPERS ────────────────────────────────────────────────────
def render_hero():
    st.markdown("""
<div class="hero">
  <div class="hero-eyebrow"><span class="pulse"></span>&nbsp;Sistem Aktif</div>
  <div class="hero-title">Ajukan Jadwal<br>Kunjungan Sales</div>
  <div class="hero-desc">Daftarkan kunjungan ke kantor kami. Slot real-time dari Google Sheets — anti double booking.</div>
  <div class="hero-tags">
    <span class="hero-tag green">&#10003; Cek slot real-time</span>
    <span class="hero-tag">&#128197; Hanya hari Selasa</span>
    <span class="hero-tag">&#128274; Anti double booking</span>
    <span class="hero-tag">&#128241; Konfirmasi WhatsApp</span>
  </div>
</div>""", unsafe_allow_html=True)


def render_steps(current: int):
    labels = ["Hotel", "Kontak", "Jadwal", "Kirim"]
    html = '<div class="steps-wrap"><div class="steps-card">'
    for i, lbl in enumerate(labels, 1):
        if i < current:
            cls = "done"; num = "&#10003;"
        elif i == current:
            cls = "active"; num = str(i)
        else:
            cls = "idle"; num = str(i)
        html += f'<div class="step-item"><div class="step-num {cls}">{num}</div><span class="step-txt {cls}">{lbl}</span></div>'
        if i < 4:
            lc = "done" if i < current else ""
            html += f'<div class="step-line {lc}"></div>'
    html += "</div></div>"
    st.markdown(html, unsafe_allow_html=True)
    st.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)


def card_open(icon, step_label, title, sub=""):
    sub_html = f'<div class="card-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
<div class="card">
  <div class="card-header">
    <div class="card-icon">{icon}</div>
    <div>
      <div class="card-step">{step_label}</div>
      <div class="card-title">{title}</div>
      {sub_html}
    </div>
  </div>
  <div class="card-body">""", unsafe_allow_html=True)

def card_close():
    st.markdown("</div></div>", unsafe_allow_html=True)

def sec_lbl(txt):
    st.markdown(f'<div class="sec-lbl">{txt}</div>', unsafe_allow_html=True)

def info_box(txt):
    st.markdown(f'<div class="info-box"><span>&#8505;&#65039;</span><div>{txt}</div></div>', unsafe_allow_html=True)


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
        st.session_state.conflict_type = "blocking"
        st.session_state.conflict_msg  = "Slot yang dipilih sudah terisi hotel lain."
        st.session_state.alternatives  = alts
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
    card_open("&#127968;", "Langkah 1 dari 3", "Informasi Hotel", "Data properti hotel Anda")
    st.session_state.nama_hotel = st.text_input("Nama Hotel / Property *", value=st.session_state.nama_hotel, placeholder="Contoh: Grand Hyatt Jakarta", key="inp_nama_hotel")
    st.session_state.alamat_hotel = st.text_area("Alamat Hotel *", value=st.session_state.alamat_hotel, placeholder="Alamat lengkap hotel...", height=80, key="inp_alamat")
    opts = HOTEL_BRANDS
    idx  = opts.index(st.session_state.brand_hotel) if st.session_state.brand_hotel in opts else 0
    st.session_state.brand_hotel = st.selectbox("Brand / Chain Hotel (opsional)", options=opts, index=idx, key="inp_brand", format_func=lambda x: "— Pilih Brand / Chain —" if x == "" else x)
    card_close()
    if st.button("Lanjut ke Kontak &#8594;", type="primary", key="btn1"):
        if validate_step1():
            st.session_state.step = 2; st.rerun()


# ── STEP 2 ────────────────────────────────────────────────────────
def render_step2():
    card_open("&#128100;", "Langkah 2 dari 3", "Data PIC & Kontak", "Penanggung jawab kunjungan")
    st.session_state.nama_pic = st.text_input("Nama PIC Utama *", value=st.session_state.nama_pic, placeholder="Nama lengkap", key="inp_nama_pic")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.jabatan = st.text_input("Jabatan *", value=st.session_state.jabatan, placeholder="Sales Manager, GM...", key="inp_jabatan")
    with col2:
        st.session_state.no_hp = st.text_input("WhatsApp *", value=st.session_state.no_hp, placeholder="08xx-xxxx-xxxx", key="inp_no_hp")
    st.session_state.email = st.text_input("Email *", value=st.session_state.email, placeholder="nama@hotel.com", key="inp_email")
    sec_lbl("Jumlah Peserta")
    p_opts = ["1 orang (PIC saja)", "2 orang", "3 orang", "4 orang", "5 orang"]
    cur_p  = p_opts.index(st.session_state.peserta) if st.session_state.peserta in p_opts else 0
    st.session_state.peserta = st.radio("Peserta", options=p_opts, index=cur_p, horizontal=True, label_visibility="collapsed", key="inp_peserta")
    card_close()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("&#8592; Kembali", key="btn2_back"):
            st.session_state.step = 1; st.rerun()
    with col2:
        if st.button("Lanjut ke Jadwal &#8594;", type="primary", key="btn2_next"):
            if validate_step2():
                _fetch_booked_cached.clear()
                st.session_state.step = 3; st.rerun()


# ── STEP 3 — DATE ACCORDION ───────────────────────────────────────
def render_step3():
    booked = fetch_booked_slots()

    card_open("&#128197;", "Langkah 3 dari 3", "Pilih Jadwal Kunjungan",
              "Klik tanggal untuk buka slot, klik lagi untuk tutup")

    info_box("Kunjungan hanya setiap <strong>Selasa</strong>. Setiap slot untuk <strong>1 hotel</strong>.")

    # Conflict alerts
    if st.session_state.conflict_type == "blocking":
        st.markdown(
            f'<div class="alert-block">'
            f'<div class="alert-title">&#9940; Slot tidak tersedia!</div>'
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
                    st.session_state.expanded_date  = alt["date_key"]
                    st.rerun()
    elif st.session_state.conflict_type == "ok":
        st.markdown(
            f'<div class="alert-ok">'
            f'<div class="alert-title">&#10003; Slot dipilih!</div>'
            f'{st.session_state.conflict_msg}</div>',
            unsafe_allow_html=True)

    # ── DATE ACCORDION ──
    for dt in DATES:
        dk = dt["key"]
        free_slots  = [s for s in SESSIONS if not is_booked(booked, dk, s["value"])]
        taken_slots = [s for s in SESSIONS if is_booked(booked, dk, s["value"])]
        all_full    = len(free_slots) == 0
        is_expanded = st.session_state.expanded_date == dk
        has_sel     = st.session_state.sel_date_key == dk

        # Availability pill
        if all_full:
            pill_cls = "pill-full"; pill_txt = "Penuh"
        elif has_sel:
            pill_cls = "pill-sel"; pill_txt = "&#10003; Dipilih"
        elif taken_slots:
            pill_cls = "pill-part"; pill_txt = f"{len(free_slots)} sisa"
        else:
            pill_cls = "pill-ok"; pill_txt = f"{len(free_slots)} tersedia"

        # Row classes
        row_cls = ""
        if all_full:
            row_cls = "full"
        elif has_sel:
            row_cls = "selected"
        elif is_expanded:
            row_cls = "expanded"

        arrow = "&#9650;" if is_expanded else "&#9660;"

        # Render date row as HTML
        st.markdown(f"""
<div class="date-row {row_cls}" id="dr_{dk}">
  <div class="cal-box">
    <div class="cal-day">{dt["day"]}</div>
    <div class="cal-month">{dt["month"]}</div>
  </div>
  <div class="date-info">
    <div class="date-name-txt">{dt["label"]}</div>
    <div class="date-dow">Selasa</div>
  </div>
  <span class="avail-pill {pill_cls}">{pill_txt}</span>
  <span class="date-arrow">{arrow}</span>
</div>""", unsafe_allow_html=True)

        # Toggle button (invisible, full-width overlay effect)
        if not all_full:
            toggle_lbl = "&#9650; Tutup" if is_expanded else "&#9660; Buka"
            if st.button(toggle_lbl, key=f"tog_{dk}", use_container_width=True):
                if is_expanded:
                    st.session_state.expanded_date = None
                else:
                    st.session_state.expanded_date = dk
                st.rerun()

        # Slot panel (expanded)
        if is_expanded and not all_full:
            st.markdown('<div class="slot-panel">', unsafe_allow_html=True)
            for sess in SESSIONS:
                is_taken  = is_booked(booked, dk, sess["value"])
                is_picked = (st.session_state.sel_date_key == dk and
                             st.session_state.sel_sess_value == sess["value"])
                s_lbl = sess["label"]

                if is_taken:
                    st.markdown(
                        f'<div class="slot-item full">'
                        f'<span class="slot-time">{s_lbl}</span>'
                        f'<span class="slot-badge sbadge-full">Penuh</span>'
                        f'</div>',
                        unsafe_allow_html=True)
                else:
                    item_cls   = "sel" if is_picked else "av"
                    badge_cls  = "sbadge-sel" if is_picked else "sbadge-av"
                    badge_txt  = "&#10003; Dipilih" if is_picked else "Pilih"
                    btn_label  = "&#10003; Dipilih" if is_picked else "Pilih slot ini"

                    st.markdown(
                        f'<div class="slot-item {item_cls}">'
                        f'<span class="slot-time">{s_lbl}</span>'
                        f'<span class="slot-badge {badge_cls}">{badge_txt}</span>'
                        f'</div>',
                        unsafe_allow_html=True)

                    if st.button(btn_label, key=f"slot_{dk}_{sess['id']}", use_container_width=True):
                        _fetch_booked_cached.clear()
                        fresh = fetch_booked_slots()
                        if is_booked(fresh, dk, sess["value"]):
                            alts = get_alternatives(fresh, dk, sess["value"])
                            st.session_state.conflict_type = "blocking"
                            st.session_state.conflict_msg  = f"Slot {s_lbl} pada {dt['label']} baru saja diisi hotel lain."
                            st.session_state.alternatives  = alts
                        else:
                            st.session_state.sel_date_key   = dk
                            st.session_state.sel_date_label = dt["label"]
                            st.session_state.sel_sess_value = sess["value"]
                            st.session_state.sel_sess_label = sess["label"]
                            st.session_state.conflict_type  = "ok"
                            st.session_state.conflict_msg   = f"{dt['label']} · {sess['label']} siap di-booking."
                            st.session_state.alternatives   = []
                            st.session_state.expanded_date  = None
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # Selected summary bar
    if st.session_state.sel_date_key and st.session_state.sel_sess_value:
        sel_dl = st.session_state.sel_date_label
        sel_sl = st.session_state.sel_sess_label
        st.markdown(
            f'<div class="sel-bar">'
            f'<div><div class="sel-bar-lbl">Jadwal Dipilih</div>'
            f'<div class="sel-bar-val">{sel_dl} &nbsp;&#183;&nbsp; {sel_sl}</div></div>'
            f'<div style="color:rgba(255,255,255,.5);font-size:20px">&#10003;</div>'
            f'</div>',
            unsafe_allow_html=True)
        if st.button("Batalkan pilihan", key="clear_slot"):
            st.session_state.sel_date_key = st.session_state.sel_date_label = None
            st.session_state.sel_sess_value = st.session_state.sel_sess_label = None
            st.session_state.conflict_type = None
            st.session_state.alternatives  = []
            st.session_state.expanded_date = None
            st.rerun()

    st.markdown('<hr class="sec-div">', unsafe_allow_html=True)

    # Tujuan
    sec_lbl("Tujuan Kunjungan")
    tujuan_selected = []
    col1, col2 = st.columns(2)
    for i, tuj in enumerate(TUJUAN_OPTIONS):
        with (col1 if i % 2 == 0 else col2):
            if st.checkbox(tuj, value=(tuj in st.session_state.tujuan), key=f"tuj_{i}"):
                tujuan_selected.append(tuj)
    st.session_state.tujuan = tujuan_selected

    # Durasi
    sec_lbl("Estimasi Durasi")
    d_opts = ["15 Menit", "30 Menit", "45 Menit"]
    cur_d  = d_opts.index(st.session_state.durasi) if st.session_state.durasi in d_opts else 0
    st.session_state.durasi = st.radio("Durasi", options=d_opts, index=cur_d, horizontal=True, label_visibility="collapsed", key="inp_durasi")

    # Catatan
    sec_lbl("Catatan Tambahan")
    st.session_state.catatan = st.text_area("Catatan", value=st.session_state.catatan, placeholder="Informasi tambahan (opsional)...", height=80, label_visibility="collapsed", key="inp_catatan")

    card_close()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("&#8592; Kembali", key="btn3_back"):
            st.session_state.step = 2; st.rerun()
    with col2:
        if st.button("Review & Kirim &#8594;", type="primary", key="btn3_next"):
            fresh_b = fetch_booked_slots()
            if validate_step3(fresh_b):
                st.session_state.step = 4; st.rerun()


# ── STEP 4 ────────────────────────────────────────────────────────
def render_step4():
    card_open("&#128203;", "Konfirmasi", "Review Permohonan", "Periksa semua data sebelum mengirim")
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
            f'</div>', unsafe_allow_html=True)
    info_box("Dengan mengirimkan formulir ini, Anda bersedia dihubungi via WhatsApp atau Email untuk konfirmasi jadwal.")
    card_close()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("&#8592; Edit Data", key="btn4_back"):
            st.session_state.step = 3; st.rerun()
    with col2:
        if st.button("Kirim Permohonan &#9993;", type="primary", key="btn4_submit"):
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


# ── STEP 5 ────────────────────────────────────────────────────────
def render_success():
    ref   = st.session_state.ref_number
    pic   = st.session_state.nama_pic
    hotel = st.session_state.nama_hotel
    tgl   = st.session_state.sel_date_label
    slot  = st.session_state.sel_sess_label
    st.markdown('<div class="card"><div class="card-body">', unsafe_allow_html=True)
    st.markdown(f"""
<div class="success-box">
  <div class="success-icon">&#10003;</div>
  <h2 style="font-size:21px;font-weight:700;color:#2d3748;margin-bottom:6px;letter-spacing:-.3px">Permohonan Terkirim!</h2>
  <p style="font-size:13px;color:#64748b;line-height:1.7;margin-bottom:6px">
    Terima kasih! Permohonan kunjungan Anda sudah kami terima.<br>
    Notifikasi dikirim ke <strong style="color:#0659a7">d4t4m1tr4@gmail.com</strong><br>
    Konfirmasi akan dikirimkan dalam 1–2 hari kerja.
  </p>
  <div class="ref-badge">{ref}</div>
  <p style="font-size:11.5px;color:#94a3b8;margin-bottom:0">Simpan nomor referensi untuk keperluan tindak lanjut.</p>
  <div class="succ-grid">
    <div class="succ-item"><div class="succ-lbl">Nama PIC</div><div class="succ-val">{pic}</div></div>
    <div class="succ-item"><div class="succ-lbl">Hotel</div><div class="succ-val">{hotel}</div></div>
    <div class="succ-item"><div class="succ-lbl">Tanggal</div><div class="succ-val">{tgl}</div></div>
    <div class="succ-item"><div class="succ-lbl">Slot</div><div class="succ-val">{slot}</div></div>
  </div>
</div>""", unsafe_allow_html=True)
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
        '<div class="footer">VisitorPass &nbsp;&#183;&nbsp; Mitra Tours &amp; Travel'
        '&nbsp;&#183;&nbsp; Data tersimpan di Google Sheets</div>',
        unsafe_allow_html=True)

if __name__ == "__main__":
    main()
