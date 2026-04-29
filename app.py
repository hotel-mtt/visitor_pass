"""
Mitra Tours & Travel — Visitor Appointment System
Final Clean Version — Zero custom button tricks
Alur: Jadwal → Hotel → Kontak → Kirim
"""

import streamlit as st
import requests, random, string, re
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="Kunjungan Sales — Mitra Tours",
    page_icon="📅", layout="centered",
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
    {"key":"6 Mei 2026",  "label":"Selasa, 6 Mei 2026",  "month":"Mei"},
    {"key":"13 Mei 2026", "label":"Selasa, 13 Mei 2026", "month":"Mei"},
    {"key":"20 Mei 2026", "label":"Selasa, 20 Mei 2026", "month":"Mei"},
    {"key":"27 Mei 2026", "label":"Selasa, 27 Mei 2026", "month":"Mei"},
    {"key":"2 Jun 2026",  "label":"Selasa, 2 Jun 2026",  "month":"Jun"},
    {"key":"9 Jun 2026",  "label":"Selasa, 9 Jun 2026",  "month":"Jun"},
    {"key":"16 Jun 2026", "label":"Selasa, 16 Jun 2026", "month":"Jun"},
    {"key":"23 Jun 2026", "label":"Selasa, 23 Jun 2026", "month":"Jun"},
    {"key":"30 Jun 2026", "label":"Selasa, 30 Jun 2026", "month":"Jun"},
    {"key":"7 Jul 2026",  "label":"Selasa, 7 Jul 2026",  "month":"Jul"},
    {"key":"14 Jul 2026", "label":"Selasa, 14 Jul 2026", "month":"Jul"},
    {"key":"21 Jul 2026", "label":"Selasa, 21 Jul 2026", "month":"Jul"},
    {"key":"28 Jul 2026", "label":"Selasa, 28 Jul 2026", "month":"Jul"},
    {"key":"4 Agt 2026",  "label":"Selasa, 4 Agt 2026",  "month":"Agt"},
    {"key":"11 Agt 2026", "label":"Selasa, 11 Agt 2026", "month":"Agt"},
    {"key":"18 Agt 2026", "label":"Selasa, 18 Agt 2026", "month":"Agt"},
    {"key":"25 Agt 2026", "label":"Selasa, 25 Agt 2026", "month":"Agt"},
]

SESSIONS = [
    {"id":"P1","value":"09.00-10.00 WIB",  "icon":"-","label":"09.00–10.00 WIB"},
    {"id":"P2","value":"10.00-11.00 WIB",  "icon":"-","label":"10.00–11.00 WIB"},
    {"id":"S1","value":"13.30-14.30 WIB", "icon":"-","label":"13.30–14.30 WIB"},
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
    "Perkenalan Hotel","Presentasi Produk / Fasilitas",
    "Corporate Rate / Contract Rate","Promo / Special Offer",
    "Kerja Sama Partnership","Follow Up Existing Business",
]

# ── GOOGLE SHEETS ─────────────────────────────────────────────────
@st.cache_data(ttl=30)
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
                booked[f"{dk}|{sv}"] = booked.get(f"{dk}|{sv}", 0) + 1
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
                    "date_key":   d["key"],   "date_label": d["label"],
                    "sess_value": s["value"], "sess_label": s["label"],
                })
                if len(out) >= n:
                    return out
    return out

def gen_ref():
    return "SV-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=7))

# ── GAS WRITE ─────────────────────────────────────────────────────
def save_to_gas(payload):
    import json as _j
    payload["notifEmail"] = NOTIF_EMAIL
    sess = requests.Session()
    for url in [GAS_ENDPOINT, GAS_ENDPOINT + "?method=POST"]:
        try:
            resp = sess.post(url, data=_j.dumps(payload),
                             headers={"Content-Type": "application/json"},
                             allow_redirects=True, timeout=30)
            raw = resp.text.strip()
            if raw.startswith("{"):
                r = _j.loads(raw)
                if r.get("success"):
                    return True, r.get("ref", "")
                if r.get("error") == "Jadwal_TAKEN":
                    return False, "Jadwal_TAKEN"
                return False, r.get("message", r.get("error", "Unknown"))
        except requests.exceptions.Timeout:
            return False, "Timeout — coba lagi"
        except Exception:
            pass
    try:
        import urllib.parse as _up
        q = _up.urlencode({"payload": _j.dumps(payload), "action": "write"})
        r3 = sess.get(GAS_ENDPOINT + "?" + q, allow_redirects=True, timeout=30)
        raw3 = r3.text.strip()
        if raw3.startswith("{"):
            rr = _j.loads(raw3)
            if rr.get("success"):
                return True, rr.get("ref", "")
            if rr.get("error") == "Jadwal_TAKEN":
                return False, "Jadwal_TAKEN"
            return False, rr.get("message", rr.get("error", "Unknown"))
    except Exception as e:
        return False, str(e)
    return False, "Semua strategi gagal"

# ── SESSION STATE ──────────────────────────────────────────────────
def init_state():
    defaults = {
        "step": 1,
        "sel_date_key": None, "sel_date_label": None,
        "sel_sess_value": None, "sel_sess_label": None,
        "nama_hotel": "", "alamat_hotel": "", "brand_hotel": "",
        "nama_pic": "", "jabatan": "", "no_hp": "", "email": "",
        "peserta": "1 orang (PIC saja)",
        "tujuan": [], "durasi": "15 Menit", "catatan": "",
        "ref_number": "", "conflict_type": None,
        "conflict_msg": "", "alternatives": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── CSS ───────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Plus Jakarta Sans',sans-serif!important}
#MainMenu,footer,header{visibility:hidden}
.stDeployButton,[data-testid="stToolbar"],[data-testid="collapsedControl"]{display:none}
.main .block-container{padding:0 .75rem 3rem!important;max-width:600px!important}

/* ── HEADER ── */
.hdr{background:#0659a7;margin:0 -.75rem;padding:22px 22px 54px;
  border-radius:0 0 22px 22px;position:relative;overflow:hidden}
.hdr::after{content:'';position:absolute;right:-28px;bottom:-28px;
  width:120px;height:120px;border-radius:50%;background:rgba(255,255,255,.04)}
.hdr-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:13px}
.hdr-brand{font-size:11px;font-weight:500;color:rgba(255,255,255,.6);
  letter-spacing:.6px;text-transform:uppercase}
.hdr-live{display:flex;align-items:center;gap:5px;
  background:rgba(141,188,101,.18);border:1px solid rgba(141,188,101,.32);
  border-radius:20px;padding:3px 10px;font-size:10px;font-weight:500;color:#b8e098}
.ldot{width:5px;height:5px;background:#8dbc65;border-radius:50%;
  display:inline-block;animation:blink 2s ease-in-out infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.25}}
.hdr-h1{font-size:22px;font-weight:600;color:#fff;line-height:1.22;margin-bottom:4px}
.hdr-sub{font-size:12px;color:rgba(255,255,255,.58);line-height:1.6}

/* ── STEP PILLS ── */
.spills{display:flex;gap:2px;background:#fff;border-radius:13px;padding:5px;
  margin-top:-28px;position:relative;z-index:10;
  box-shadow:0 4px 18px rgba(6,89,167,.11)}
.sp{flex:1;text-align:center;padding:7px 2px;border-radius:9px}
.sp-n{font-size:9px;font-weight:500;display:block;margin-bottom:1px;
  text-transform:uppercase;letter-spacing:.5px}
.sp-l{font-size:11px;font-weight:600;display:block;white-space:nowrap}
.sp.act{background:#0659a7}
.sp.act .sp-n{color:rgba(255,255,255,.55)}
.sp.act .sp-l{color:#fff}
.sp.done{background:#eef7e2}
.sp.done .sp-n,.sp.done .sp-l{color:#3b6d11}
.sp.idle .sp-n,.sp.idle .sp-l{color:#a0aec0}

/* ── SELECTED BAR ── */
.sel-bar{background:#0659a7;border-radius:10px;padding:11px 15px;
  margin-bottom:14px;display:flex;align-items:center;justify-content:space-between}
.sb-lbl{font-size:9px;font-weight:500;color:rgba(255,255,255,.55);
  text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px}
.sb-val{font-size:13px;font-weight:600;color:#fff}
.sb-ico{width:22px;height:22px;border-radius:50%;background:rgba(255,255,255,.2);
  display:flex;align-items:center;justify-content:center;font-size:11px;
  color:#fff;flex-shrink:0}

/* ── INFO / ALERT ── */
.ibox{display:flex;gap:7px;background:#e8f1fb;border-left:2px solid #0659a7;
  border-radius:0 8px 8px 0;padding:10px 13px;font-size:12px;color:#044d8f;
  line-height:1.55;margin-bottom:14px}
.alert-red{background:#fdeaea;border-left:2px solid #ec1a23;
  border-radius:0 8px 8px 0;padding:10px 13px;font-size:12px;
  color:#7f1d1d;margin-bottom:12px}
.alert-green{background:#eef7e2;border-left:2px solid #8dbc65;
  border-radius:0 8px 8px 0;padding:10px 13px;font-size:12px;
  color:#27500a;margin-bottom:12px}

/* ── FIELD LABEL ── */
.flbl{font-size:10.5px;font-weight:600;color:#64748b;text-transform:uppercase;
  letter-spacing:.5px;margin:14px 0 7px;display:flex;align-items:center;gap:6px}
.flbl-num{width:18px;height:18px;border-radius:50%;background:#0659a7;color:#fff;
  font-size:9px;font-weight:700;display:flex;align-items:center;
  justify-content:center;flex-shrink:0}

/* ── Jadwal RADIO — styled as card list ── */
/* Container */
div[data-testid="stRadio"][data-Jadwal-radio] > div {
  border: 1.5px solid #e2eaf4 !important;
  border-radius: 10px !important;
  overflow: hidden !important;
  gap: 0 !important;
  padding: 0 !important;
}
/* Each radio option */
div[data-testid="stRadio"][data-Jadwal-radio] > div > label {
  display: flex !important;
  align-items: center !important;
  padding: 14px 16px !important;
  margin: 0 !important;
  border-bottom: 1px solid #f0f5fb !important;
  border-radius: 0 !important;
  cursor: pointer !important;
  width: 100% !important;
  gap: 0 !important;
  background: #fff !important;
  transition: background .12s !important;
}
div[data-testid="stRadio"][data-Jadwal-radio] > div > label:last-child {
  border-bottom: none !important;
}
div[data-testid="stRadio"][data-Jadwal-radio] > div > label:hover {
  background: #f4f8fd !important;
}
/* Hide default radio circle */
div[data-testid="stRadio"][data-Jadwal-radio] > div > label > div:first-child {
  display: none !important;
}
/* The label text */
div[data-testid="stRadio"][data-Jadwal-radio] > div > label p {
  font-size: 13.5px !important;
  font-weight: 600 !important;
  color: #1a2332 !important;
  margin: 0 !important;
}

/* ── SECTION LABEL ── */
.slbl{font-size:10px;font-weight:600;letter-spacing:.6px;text-transform:uppercase;
  color:#a0aec0;margin:16px 0 9px;display:flex;align-items:center;gap:8px}
.slbl::after{content:'';flex:1;height:1px;background:#edf2f9}

/* ── REVIEW TABLE ── */
.rev-wrap{background:#fff;border:1px solid #e2eaf4;border-radius:10px;
  overflow:hidden;margin-bottom:12px}
.rev-sec{background:#f7f9fc;padding:7px 12px;font-size:9.5px;font-weight:600;
  color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;
  border-bottom:1px solid #e2eaf4}
.rev-row{display:flex;border-bottom:1px solid #f0f5fb}
.rev-row:last-child{border-bottom:none}
.rev-lbl{width:90px;flex-shrink:0;padding:9px 12px;font-size:11.5px;
  color:#64748b;border-right:1px solid #f0f5fb}
.rev-val{padding:9px 13px;font-size:13px;color:#1a2332;font-weight:500;
  flex:1;word-break:break-word}
.rev-val.blue{color:#0659a7;font-weight:600}

/* ── SUCCESS ── */
.succ{text-align:center;padding:28px 16px}
.succ-ring{width:62px;height:62px;border-radius:50%;background:#8dbc65;
  margin:0 auto 14px;display:flex;align-items:center;
  justify-content:center;font-size:24px;color:#fff}
.succ-ref{background:#f7f9fc;border:1.5px solid #e2eaf4;border-radius:7px;
  padding:6px 16px;font-size:13px;font-family:monospace;letter-spacing:2px;
  color:#1a2332;display:inline-block;margin:8px 0 12px}
.succ-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;
  max-width:320px;margin:12px auto 0;text-align:left}
.succ-item{background:#f7f9fc;border:1px solid #e2eaf4;border-radius:8px;padding:9px 11px}
.succ-lbl{font-size:9px;text-transform:uppercase;letter-spacing:.5px;
  color:#94a3b8;font-weight:600;margin-bottom:2px}
.succ-val{font-size:12.5px;font-weight:500;color:#1a2332}

/* ── GLOBAL BUTTONS ── */
div[data-testid="stButton"]>button[kind="primary"]{
  background:#0659a7!important;border:none!important;border-radius:9px!important;
  font-weight:600!important;font-size:14px!important;width:100%!important;padding:11px!important}
div[data-testid="stButton"]>button[kind="primary"]:hover{background:#044d8f!important}
div[data-testid="stButton"]>button[kind="secondary"]{
  border:1px solid #e2eaf4!important;border-radius:9px!important;color:#64748b!important;
  background:#fff!important;font-weight:500!important;font-size:14px!important;
  width:100%!important;padding:11px!important}
.btn-green div[data-testid="stButton"]>button{
  background:#8dbc65!important;border:none!important;border-radius:9px!important;
  font-weight:600!important;font-size:14px!important;color:#fff!important;
  width:100%!important;padding:11px!important}
.btn-green div[data-testid="stButton"]>button:hover{background:#6fa048!important}

/* ── INPUTS ── */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea{
  border:1px solid #e2eaf4!important;border-radius:8px!important;
  font-size:13.5px!important;background:#fafcfe!important}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus{
  border-color:#0659a7!important;
  box-shadow:0 0 0 3px rgba(6,89,167,.07)!important}
div[data-testid="stSelectbox"]>div>div{
  border:1px solid #e2eaf4!important;border-radius:8px!important;font-size:14px!important}
label{color:#64748b!important;font-size:13px!important}

.footer{text-align:center;padding:18px 0 26px;font-size:11px;color:#a0aec0}
</style>""", unsafe_allow_html=True)

# ── UI HELPERS ─────────────────────────────────────────────────────
def render_header():
    st.markdown("""
<div class="hdr">
  <div class="hdr-top">
    <span class="hdr-brand">Mitra Tours &amp; Travel</span>
    <div class="hdr-live"><span class="ldot"></span>Sistem Aktif</div>
  </div>
  <div class="hdr-h1">Form Registrasi Kunjungan</div>
  <div class="hdr-sub">Pilih jadwal terlebih dahulu, lalu lengkapi data &amp; kontak.</div>
</div>""", unsafe_allow_html=True)

def render_steps(cur):
    labels = ["Jadwal","Hotel","Kontak","Kirim"]
    html = '<div class="spills">'
    for i, lbl in enumerate(labels, 1):
        cls = "done" if i < cur else ("act" if i == cur else "idle")
        html += (f'<div class="sp {cls}">'
                 f'<span class="sp-n">0{i}</span>'
                 f'<span class="sp-l">{lbl}</span></div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

def sel_bar():
    if st.session_state.sel_date_key and st.session_state.sel_sess_value:
        st.markdown(
            f'<div class="sel-bar">'
            f'<div><div class="sb-lbl">Jadwal Dipilih</div>'
            f'<div class="sb-val">{st.session_state.sel_date_label}'
            f' &nbsp;·&nbsp; {st.session_state.sel_sess_label}</div></div>'
            f'<div class="sb-ico">&#10003;</div></div>',
            unsafe_allow_html=True)

def slbl(txt):
    st.markdown(f'<div class="slbl">{txt}</div>', unsafe_allow_html=True)

def ibox(txt):
    st.markdown(
        f'<div class="ibox"><span>&#8505;</span><div>{txt}</div></div>',
        unsafe_allow_html=True)

def valid_email(e):
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", e.strip()))

# ── STEP 1 — JADWAL ───────────────────────────────────────────────
def render_step1():
    booked = fetch_booked()

    ibox("Kunjungan setiap <strong>Selasa</strong> · 1 hotel per Jadwal · "
         "Pilih tanggal lalu pilih jam yang tersedia")

    # Conflict alerts
    if st.session_state.conflict_type == "blocking":
        st.markdown(
            f'<div class="alert-red"><strong>Jadwal tidak tersedia</strong><br>'
            f'{st.session_state.conflict_msg}</div>', unsafe_allow_html=True)
        if st.session_state.alternatives:
            st.caption("Pilih Jadwal alternatif:")
            for alt in st.session_state.alternatives:
                if st.button(
                    f"→ {alt['date_label']} · {alt['sess_label']}",
                    key=f"alt_{alt['date_key']}_{alt['sess_value']}"
                ):
                    st.session_state.sel_date_key   = alt["date_key"]
                    st.session_state.sel_date_label = alt["date_label"]
                    st.session_state.sel_sess_value = alt["sess_value"]
                    st.session_state.sel_sess_label = alt["sess_label"]
                    st.session_state.conflict_type  = None
                    st.rerun()

    elif st.session_state.conflict_type == "ok":
        st.markdown(
            f'<div class="alert-green"><strong>&#10003; Jadwal dipilih</strong><br>'
            f'{st.session_state.conflict_msg}</div>', unsafe_allow_html=True)

    # ── Dropdown tanggal ──────────────────────────────────────────
    st.markdown(
        '<div class="flbl">'
        '<span class="flbl-num">1</span>Pilih Tanggal Kunjungan</div>',
        unsafe_allow_html=True)

    date_opts   = ["— Pilih tanggal —"]
    date_map    = {}
    for dt in DATES:
        free = sum(1 for s in SESSIONS
                   if not is_booked(booked, dt["key"], s["value"]))
        if free == 0:
            suf = " — Penuh"
        elif free < len(SESSIONS):
            suf = f" — {free} Jadwal tersisa"
        else:
            suf = f" — {free} Jadwal tersedia"
        opt = dt["label"] + suf
        date_opts.append(opt)
        date_map[opt] = dt

    # Determine current index
    cur_opt = None
    if st.session_state.sel_date_key:
        for lbl, dt in date_map.items():
            if dt["key"] == st.session_state.sel_date_key:
                cur_opt = lbl
                break
    cur_idx = date_opts.index(cur_opt) if cur_opt else 0

    chosen_label = st.selectbox(
        "Tanggal", options=date_opts, index=cur_idx,
        label_visibility="collapsed", key="dd_tanggal")
    chosen_dt = date_map.get(chosen_label)

    # Reset Jadwal when date changes
    if chosen_dt and chosen_dt["key"] != st.session_state.sel_date_key:
        st.session_state.sel_date_key   = chosen_dt["key"]
        st.session_state.sel_date_label = chosen_dt["label"]
        st.session_state.sel_sess_value = None
        st.session_state.sel_sess_label = None
        st.session_state.conflict_type  = None
        st.rerun()

    # ── Radio Jadwal jam ────────────────────────────────────────────
    if chosen_dt:
        dk = chosen_dt["key"]
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        st.markdown(
            '<div class="flbl">'
            '<span class="flbl-num">2</span>Pilih Jadwal</div>',
            unsafe_allow_html=True)

        # Build options: available sessions only, taken shown as disabled text
        Jadwal_options  = []   # values for radio
        Jadwal_labels   = []   # display labels for radio
        Jadwal_taken_set = set()

        for sess in SESSIONS:
            taken = is_booked(booked, dk, sess["value"])
            if taken:
                # Show as disabled label — radio won't include this
                Jadwal_taken_set.add(sess["value"])
            else:
                Jadwal_options.append(sess["value"])
                Jadwal_labels.append(f"{sess['icon']}  {sess['label']}")

        # Show taken Jadwals as greyed HTML above radio
        taken_html = ""
        for sess in SESSIONS:
            if sess["value"] in Jadwal_taken_set:
                taken_html += (
                    f'<div style="display:flex;align-items:center;gap:12px;'
                    f'padding:14px 16px;border:1.5px solid #e2eaf4;border-radius:10px;'
                    f'margin-bottom:6px;background:#fafafa;opacity:.55;">'
                    f'<div style="width:20px;height:20px;border-radius:50%;'
                    f'border:2px solid #dce8f5;flex-shrink:0"></div>'
                    f'<span style="font-size:20px">{sess["icon"]}</span>'
                    f'<div style="flex:1">'
                    f'<div style="font-size:13.5px;font-weight:600;color:#94a3b8;'
                    f'text-decoration:line-through">{sess["label"]}</div>'
                    f'<div style="font-size:11.5px;color:#94a3b8;margin-top:2px">'
                    f'Jadwal ini sudah terisi hotel lain</div></div>'
                    f'<span style="font-size:10px;font-weight:600;padding:4px 10px;'
                    f'border-radius:8px;background:#fdeaea;color:#ec1a23;white-space:nowrap">'
                    f'Penuh</span></div>')

        if not Jadwal_options:
            # All Jadwals full for this date
            st.markdown(
                f'<div style="border:1.5px solid #e2eaf4;border-radius:10px;'
                f'overflow:hidden;margin-bottom:6px">{taken_html}</div>',
                unsafe_allow_html=True)
            st.warning("Semua Jadwal pada tanggal ini sudah penuh. Pilih tanggal lain.")
        else:
            # Determine current radio selection
            cur_sess = (st.session_state.sel_sess_value
                        if st.session_state.sel_date_key == dk else None)
            cur_radio_idx = (Jadwal_options.index(cur_sess)
                             if cur_sess in Jadwal_options else 0)

            # Show taken Jadwals first (greyed HTML)
            taken_above = ""
            for sess in SESSIONS:
                if sess["value"] in Jadwal_taken_set:
                    taken_above += (
                        f'<div style="display:flex;align-items:center;gap:12px;'
                        f'padding:14px 16px;border-bottom:1px solid #f0f5fb;'
                        f'background:#fafafa;opacity:.55;">'
                        f'<div style="width:20px;height:20px;border-radius:50%;'
                        f'border:2px solid #dce8f5;flex-shrink:0"></div>'
                        f'<span style="font-size:20px">{sess["icon"]}</span>'
                        f'<div style="flex:1">'
                        f'<div style="font-size:13.5px;font-weight:600;color:#94a3b8;'
                        f'text-decoration:line-through">{sess["label"]}</div>'
                        f'<div style="font-size:11.5px;color:#94a3b8;margin-top:2px">'
                        f'Jadwal ini sudah terisi hotel lain</div></div>'
                        f'<span style="font-size:10px;font-weight:600;padding:4px 10px;'
                        f'border-radius:8px;background:#fdeaea;color:#ec1a23">'
                        f'Penuh</span></div>')

            # Wrap: taken HTML + radio for available
            if taken_above:
                st.markdown(
                    f'<div style="border:1.5px solid #e2eaf4;border-radius:10px;'
                    f'overflow:hidden;margin-bottom:6px">{taken_above}</div>',
                    unsafe_allow_html=True)

            # Native st.radio for available Jadwals
            chosen_val = st.radio(
                "Pilih jam",
                options=Jadwal_options,
                format_func=lambda v: next(
                    f"{s['icon']}  {s['label']}" for s in SESSIONS if s["value"] == v
                ),
                index=cur_radio_idx,
                label_visibility="collapsed",
                key=f"radio_Jadwal_{dk}",
            )

            # If selection changed, update and re-verify
            if chosen_val != st.session_state.sel_sess_value or dk != st.session_state.sel_date_key:
                _fetch_cached.clear()
                fresh = fetch_booked()
                if is_booked(fresh, dk, chosen_val):
                    alts = get_alts(fresh, dk, chosen_val)
                    st.session_state.conflict_type = "blocking"
                    st.session_state.conflict_msg  = (
                        f"Jadwal ini baru saja diisi hotel lain.")
                    st.session_state.alternatives  = alts
                else:
                    sess_obj = next(s for s in SESSIONS if s["value"] == chosen_val)
                    st.session_state.sel_date_key   = dk
                    st.session_state.sel_date_label = chosen_dt["label"]
                    st.session_state.sel_sess_value = chosen_val
                    st.session_state.sel_sess_label = sess_obj["label"]
                    st.session_state.conflict_type  = "ok"
                    st.session_state.conflict_msg   = (
                        f"{chosen_dt['label']} · {sess_obj['label']} siap di-booking.")
                    st.session_state.alternatives   = []
                st.rerun()

    # ── Bottom CTA ────────────────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if st.session_state.sel_date_key and st.session_state.sel_sess_value:
        sel_bar()
        c1, c2 = st.columns([1, 2])
        with c1:
            if st.button("✕ Batal", key="clear_Jadwal"):
                for k in ("sel_date_key","sel_date_label",
                          "sel_sess_value","sel_sess_label"):
                    st.session_state[k] = None
                st.session_state.conflict_type = None
                st.rerun()
        with c2:
            if st.button("Lanjut →",
                         type="primary", key="btn1_next"):
                st.session_state.step = 2
                st.rerun()
    elif chosen_dt:
        st.caption("Pilih jam kunjungan di atas untuk melanjutkan.")

# ── STEP 2 — HOTEL ────────────────────────────────────────────────
def render_step2():
    sel_bar()
    st.session_state.nama_hotel = st.text_input(
        "Nama Hotel / Property *", value=st.session_state.nama_hotel,
        placeholder="Contoh: Grand Hyatt Jakarta", key="inp_nama_hotel")
    st.session_state.alamat_hotel = st.text_area(
        "Alamat Hotel *", value=st.session_state.alamat_hotel,
        placeholder="Alamat lengkap hotel...", height=80, key="inp_alamat")
    opts = HOTEL_BRANDS
    idx  = opts.index(st.session_state.brand_hotel) if st.session_state.brand_hotel in opts else 0
    st.session_state.brand_hotel = st.selectbox(
        "Brand / Chain Hotel (opsional)", options=opts, index=idx, key="inp_brand",
        format_func=lambda x: "— Pilih Brand / Chain —" if x == "" else x)
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("← Jadwal", key="btn2_back"):
            st.session_state.step = 1; st.rerun()
    with c2:
        if st.button("Lanjut ke Kontak →", type="primary", key="btn2_next"):
            ok = True
            if not st.session_state.nama_hotel.strip():
                st.error("Nama hotel wajib diisi"); ok = False
            if not st.session_state.alamat_hotel.strip():
                st.error("Alamat hotel wajib diisi"); ok = False
            if ok:
                st.session_state.step = 3; st.rerun()

# ── STEP 3 — KONTAK ───────────────────────────────────────────────
def render_step3():
    sel_bar()
    st.session_state.nama_pic = st.text_input(
        "Nama PIC Utama *", value=st.session_state.nama_pic,
        placeholder="Nama lengkap", key="inp_nama_pic")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.jabatan = st.text_input(
            "Jabatan *", value=st.session_state.jabatan,
            placeholder="Sales Manager, GM...", key="inp_jabatan")
    with c2:
        st.session_state.no_hp = st.text_input(
            "WhatsApp *", value=st.session_state.no_hp,
            placeholder="08xx-xxxx-xxxx", key="inp_no_hp")
    st.session_state.email = st.text_input(
        "Email *", value=st.session_state.email,
        placeholder="nama@hotel.com", key="inp_email")
    slbl("Jumlah Peserta")
    p_opts = ["1 orang (PIC saja)","2 orang","3 orang","4 orang","5 orang"]
    cur_p  = p_opts.index(st.session_state.peserta) if st.session_state.peserta in p_opts else 0
    st.session_state.peserta = st.radio(
        "Peserta", options=p_opts, index=cur_p,
        horizontal=True, label_visibility="collapsed", key="inp_peserta")
    slbl("Tujuan Kunjungan")
    tujuan_sel = []
    ca, cb = st.columns(2)
    for i, tuj in enumerate(TUJUAN_OPTIONS):
        with (ca if i % 2 == 0 else cb):
            if st.checkbox(tuj, value=(tuj in st.session_state.tujuan),
                           key=f"tuj_{i}"):
                tujuan_sel.append(tuj)
    st.session_state.tujuan = tujuan_sel
    slbl("Estimasi Durasi")
    d_opts = ["15 Menit","30 Menit","45 Menit"]
    cur_d  = d_opts.index(st.session_state.durasi) if st.session_state.durasi in d_opts else 0
    st.session_state.durasi = st.radio(
        "Durasi", options=d_opts, index=cur_d,
        horizontal=True, label_visibility="collapsed", key="inp_durasi")
    slbl("Catatan Tambahan")
    st.session_state.catatan = st.text_area(
        "Catatan", value=st.session_state.catatan,
        placeholder="Informasi tambahan (opsional)...",
        height=70, label_visibility="collapsed", key="inp_catatan")
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("← Hotel", key="btn3_back"):
            st.session_state.step = 2; st.rerun()
    with c2:
        if st.button("Review & Kirim →", type="primary", key="btn3_next"):
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
            if not st.session_state.tujuan:
                st.error("Pilih minimal satu tujuan kunjungan"); ok = False
            if ok:
                st.session_state.step = 4; st.rerun()

# ── STEP 4 — REVIEW & KIRIM ───────────────────────────────────────
def render_step4():
    def row(lbl, val, blue=False):
        vcls = "rev-val blue" if blue else "rev-val"
        return (f'<div class="rev-row">'
                f'<div class="rev-lbl">{lbl}</div>'
                f'<div class="{vcls}">{val}</div></div>')

    html = (
        '<div class="rev-wrap"><div class="rev-sec">Jadwal</div>'
        + row("Tanggal", st.session_state.sel_date_label or "—", True)
        + row("Jadwal",    st.session_state.sel_sess_label  or "—", True)
        + '<div class="rev-sec">Hotel</div>'
        + row("Hotel",   st.session_state.nama_hotel)
        + row("Alamat",  st.session_state.alamat_hotel)
        + row("Brand",   st.session_state.brand_hotel or "—")
        + '<div class="rev-sec">Kontak</div>'
        + row("Nama PIC", st.session_state.nama_pic)
        + row("Jabatan",  st.session_state.jabatan)
        + row("WhatsApp", st.session_state.no_hp)
        + row("Email",    st.session_state.email)
        + row("Peserta",  st.session_state.peserta)
        + row("Durasi",   st.session_state.durasi or "—")
        + row("Tujuan",   ", ".join(st.session_state.tujuan) or "—")
        + (row("Catatan", st.session_state.catatan) if st.session_state.catatan else "")
        + '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
    ibox("Dengan mengirimkan formulir ini, Anda bersedia dihubungi via "
         "WhatsApp atau Email untuk konfirmasi jadwal kunjungan.")
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("← Edit", key="btn4_back"):
            st.session_state.step = 3; st.rerun()
    with c2:
        st.markdown('<div class="btn-green">', unsafe_allow_html=True)
        if st.button("Kirim Permohonan ✓", key="btn4_submit"):
            do_submit()
        st.markdown('</div>', unsafe_allow_html=True)

def do_submit():
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
        
# ── STEP 5 — SUCCESS ──────────────────────────────────────────────
def render_success():
    st.markdown(f"""
<div class="succ">
  <div class="succ-ring">&#10003;</div>
  <div style="font-size:19px;font-weight:600;color:#1a2332;margin-bottom:6px">
    Permohonan Terkirim!
  </div>
  <div style="font-size:12px;color:#64748b;line-height:1.75">
    Notifikasi dikirim ke
    <strong style="color:#0659a7">{NOTIF_EMAIL}</strong><br>
    Konfirmasi dalam <strong>1–2 hari kerja</strong>.
  </div>
  <div class="succ-ref">{st.session_state.ref_number}</div>
  <p style="font-size:11px;color:#a0aec0;margin-bottom:0">
    Simpan nomor referensi untuk tindak lanjut.
  </p>
  <div class="succ-grid">
    <div class="succ-item">
      <div class="succ-lbl">Hotel</div>
      <div class="succ-val">{st.session_state.nama_hotel}</div>
    </div>
    <div class="succ-item">
      <div class="succ-lbl">Nama PIC</div>
      <div class="succ-val">{st.session_state.nama_pic}</div>
    </div>
    <div class="succ-item">
      <div class="succ-lbl">Tanggal</div>
      <div class="succ-val">{st.session_state.sel_date_label}</div>
    </div>
    <div class="succ-item">
      <div class="succ-lbl">Jadwal</div>
      <div class="succ-val">{st.session_state.sel_sess_label}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("+ Ajukan Kunjungan Baru", key="btn_reset"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

# ── MAIN ──────────────────────────────────────────────────────────
def main():
    init_state()
    inject_css()
    render_header()
    s = st.session_state.step
    if s < 5:
        render_steps(s)
    if   s == 1: render_step1()
    elif s == 2: render_step2()
    elif s == 3: render_step3()
    elif s == 4: render_step4()
    elif s == 5: render_success()
    st.markdown(
        '<div class="footer">Meetly &nbsp;·&nbsp; Powered by'
        ' &nbsp;·&nbsp; Mitra Tours and Travel  • Version 1.0</div>',
        unsafe_allow_html=True)

if __name__ == "__main__":
    main()
