import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Table, TableStyle, PageBreak
from reportlab.lib.units import mm
from reportlab.lib import colors
import tempfile, os

# ── 固定內容（不可改） ───────────────────────────────────────────
UNIT_NAME = "阿甯咕劇團"

# ── 字型資料夾 ───────────────────────────────────────────────────
def find_font_dir():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"),
        os.path.join(os.getcwd(), "fonts"),
        "/app/fonts",
        "/mount/src/fonts",
    ]
    for path in candidates:
        if os.path.isdir(path):
            files = [f for f in os.listdir(path) if f.lower().endswith((".ttf",".otf",".ttc"))]
            if files:
                return path
    return os.path.join(os.getcwd(), "fonts")

FONT_DIR = find_font_dir()

FALLBACK_FONTS = {
    "Sans Regular（黑體標準）":  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "Sans Medium（黑體中粗）":   "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
    "Sans Bold（黑體粗）":       "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "Sans Black（黑體超粗）":    "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",
    "Serif Regular（明體標準）": "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "Serif Bold（明體粗）":      "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
    "Serif Black（明體超粗）":   "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc",
}

def scan_repo_fonts():
    found = {}
    if os.path.isdir(FONT_DIR):
        for fname in sorted(os.listdir(FONT_DIR)):
            if fname.lower().endswith((".ttf", ".otf", ".ttc")):
                label = os.path.splitext(fname)[0]
                found[label] = os.path.join(FONT_DIR, fname)
    return found

REPO_FONTS = scan_repo_fonts()
ALL_FONTS  = {**REPO_FONTS, **FALLBACK_FONTS}
FONT_NAMES = list(ALL_FONTS.keys())

def font_index(preferred, fallback_key=None):
    if preferred in FONT_NAMES:
        return FONT_NAMES.index(preferred)
    for i, n in enumerate(FONT_NAMES):
        if preferred.lower() in n.lower():
            return i
    if fallback_key:
        for i, n in enumerate(FONT_NAMES):
            if fallback_key.lower() in n.lower():
                return i
    return 0

DEF_PROG = font_index("jf open 粉圓",       "Sans Regular")
DEF_UNIT = font_index("jf open 粉圓",       "Sans Regular")
DEF_DATE = font_index("jf open 粉圓",       "Sans Regular")
DEF_ROLE = font_index("思源黑體 Medium",    "Sans Medium")
DEF_NAME = font_index("思源黑體 Heavy",     "Sans Bold")
DEF_NUM  = font_index("JetBrainsMono-Thin", "Sans Regular")

# ── 頁面設定 ────────────────────────────────────────────────────
st.set_page_config(page_title="工作證產生器 ｜ 阿甯咕劇團", layout="wide", page_icon="🎭")

st.markdown("""
<style>
    .stButton > button {
        background: linear-gradient(135deg, #e8831a, #f5a623);
        color: white; font-weight: 700; font-size: 1.1rem;
        border: none; border-radius: 12px;
        padding: 0.6rem 1.2rem; transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(232,131,26,0.4);
    }
    .info-box {
        background: linear-gradient(135deg, #fff7ed, #fef3c7);
        border-left: 4px solid #e8831a; border-radius: 8px;
        padding: 1rem 1.2rem; margin: 0.5rem 0 1rem 0;
    }
    .info-box p { margin: 0.2rem 0; font-size: 0.95rem; color: #444; }
    .info-box strong { color: #c05621; }
    .font-hint {
        background: #f0fdf4; border-left: 3px solid #22c55e;
        border-radius: 6px; padding: 0.5rem 0.8rem;
        font-size: 0.82rem; color: #166534; margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎭 工作證產生器")

# ── 側欄 ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 版面設定")

    if REPO_FONTS:
        st.markdown(f'<div class="font-hint">✅ 已載入 {len(REPO_FONTS)} 個 repo 字型</div>',
                    unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ fonts/ 資料夾無字型，使用系統備用字型\n📂 找尋路徑：{FONT_DIR}")

    st.divider()

    st.subheader("📝 活動資訊")
    prog_name = st.text_input("節目名稱", value="《阿甯咕的爸鼻不見了？》")
    date_str  = st.text_input("使用日期", value="115.05.18～115.05.24")
    st.caption(f"使用單位：{UNIT_NAME}（固定）")

    st.divider()

    st.subheader("📐 工作證尺寸")
    st.caption("預設：9.5cm × 9cm @ 150dpi")
    badge_w = st.number_input("寬度（px）", value=561, step=10)
    badge_h = st.number_input("高度（px）", value=531, step=10)

    st.divider()

    st.subheader("🔡 各欄位字型")
    f_prog = st.selectbox("節目名稱", FONT_NAMES, index=DEF_PROG, key="f_prog")
    f_unit = st.selectbox("使用單位", FONT_NAMES, index=DEF_UNIT, key="f_unit")
    f_date = st.selectbox("使用日期", FONT_NAMES, index=DEF_DATE, key="f_date")
    f_role = st.selectbox("職稱",     FONT_NAMES, index=DEF_ROLE, key="f_role")
    f_name = st.selectbox("姓名",     FONT_NAMES, index=DEF_NAME, key="f_name")
    f_num  = st.selectbox("編號",     FONT_NAMES, index=DEF_NUM,  key="f_num")

    st.divider()

    st.subheader("🔤 字型大小")
    font_prog = st.slider("節目名稱", 10, 50, 30)
    font_unit = st.slider("使用單位", 10, 50, 30)
    font_date = st.slider("使用日期", 10, 50, 30)
    font_role = st.slider("職稱",     20, 100, 46)
    font_name = st.slider("姓名",     20, 100, 50)
    font_num  = st.slider("編號",     10,  50, 30)

    txt_color = st.color_picker("文字顏色", "#1a1a1a")

    st.divider()

    st.subheader("📍 文字座標（x, y）")
    st.caption("固定欄位")
    px1, py1 = st.columns(2)
    prog_x = px1.number_input("節目名 X", value=25, key="pgx")
    prog_y = py1.number_input("節目名 Y", value=14, key="pgy")
    ux1, uy1 = st.columns(2)
    unit_x = ux1.number_input("單位 X", value=25, key="ux")
    unit_y = uy1.number_input("單位 Y", value=46, key="uy")
    dx1, dy1 = st.columns(2)
    date_x = dx1.number_input("日期 X", value=25, key="dx")
    date_y = dy1.number_input("日期 Y", value=78, key="dy")

    st.caption("職稱｜姓名 編號 整體置中設定")
    row_y   = st.number_input("整列 Y 座標", value=168, step=2, key="row_y")
    sep_w   = st.slider("分隔線粗細（px）",      1,  10,  3)
    sep_gap = st.slider("分隔線左右留白（px）",   4,  40, 14)
    num_gap = st.slider("編號與姓名間距（px）",   4,  40, 12)
    sep_color = st.color_picker("分隔線顏色", "#1a1a1a")

    st.divider()

    # ── PDF 設定（含邊界） ────────────────────────────────────
    st.subheader("📄 PDF 設定")
    per_row  = st.radio("每列幾張", [2, 3], index=0, horizontal=True)
    per_page = st.radio("每頁幾張", [4, 6], index=1, horizontal=True)

    st.caption("列印邊界（mm）")
    mg1, mg2 = st.columns(2)
    margin_top    = mg1.number_input("上", value=8, min_value=0, max_value=30, key="mt")
    margin_bottom = mg2.number_input("下", value=8, min_value=0, max_value=30, key="mb")
    mg3, mg4 = st.columns(2)
    margin_left   = mg3.number_input("左", value=8, min_value=0, max_value=30, key="ml")
    margin_right  = mg4.number_input("右", value=8, min_value=0, max_value=30, key="mr")

# ── 活動資訊顯示 ────────────────────────────────────────────────
st.markdown(f"""
<div class="info-box">
    <p>📌 <strong>節目名稱</strong>：{prog_name}</p>
    <p>🏢 <strong>使用單位</strong>：{UNIT_NAME}</p>
    <p>📅 <strong>使用日期</strong>：{date_str}</p>
</div>
""", unsafe_allow_html=True)
st.caption("上傳底圖與 Excel 名單，自動產生 A4 排版 PDF（每頁 6 張，2 欄 × 3 列）")

# ── 主區：上傳 ───────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.subheader("📁 底圖")
    bg_file = st.file_uploader("上傳底圖（JPG / PNG）", type=["jpg", "jpeg", "png"])
    if bg_file:
        st.image(bg_file, caption="目前底圖", use_container_width=True)
with col2:
    st.subheader("📊 人員名單")
    xl_file = st.file_uploader("上傳 Excel 名單", type=["xlsx", "xls"])
    st.caption("Excel 需包含：職務、姓名、編號 等欄位")
    if xl_file:
        df_preview = pd.read_excel(xl_file)
        st.dataframe(df_preview, use_container_width=True)
        st.caption(f"共 {len(df_preview)} 筆資料")

# ── 欄位對應 ─────────────────────────────────────────────────────
col_role = col_name = col_num = None
if xl_file:
    df = pd.read_excel(xl_file)
    cols = df.columns.tolist()
    st.divider()
    st.subheader("📋 Excel 欄位對應")
    c1, c2, c3 = st.columns(3)

    def guess_col(keywords, cols):
        for kw in keywords:
            for c in cols:
                if kw in str(c):
                    return cols.index(c)
        return 0

    ri = guess_col(["職務", "職稱", "role", "title"], cols)
    ni = guess_col(["姓名", "名字", "name"], cols)
    ei = guess_col(["編號", "號碼", "num", "no", "id"], cols)
    col_role = c1.selectbox("職務欄位", cols, index=ri)
    col_name = c2.selectbox("姓名欄位", cols, index=ni)
    col_num  = c3.selectbox("編號欄位", cols, index=ei)

# ── 字型載入 ────────────────────────────────────────────────────
def get_font(font_key, size):
    path = ALL_FONTS.get(font_key, list(FALLBACK_FONTS.values())[0])
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.truetype(list(FALLBACK_FONTS.values())[0], size)
        except Exception:
            return ImageFont.load_default()

# ── 產生單張工作證 ───────────────────────────────────────────────
def make_badge(bg_img, role, name, num, cfg):
    img  = bg_img.copy().resize((cfg["w"], cfg["h"]), Image.LANCZOS)
    draw = ImageDraw.Draw(img)
    c    = cfg["color"]
    sc   = cfg["sep_color"]
    W    = cfg["w"]

    # ── 固定三行 ──────────────────────────────────────────────
    draw.text((cfg["prog_x"], cfg["prog_y"]),
              f"節目名稱：{prog_name}",
              font=get_font(cfg["f_prog"], cfg["fs_prog"]), fill=c)
    draw.text((cfg["unit_x"], cfg["unit_y"]),
              f"使用單位：{UNIT_NAME}",
              font=get_font(cfg["f_unit"], cfg["fs_unit"]), fill=c)
    draw.text((cfg["date_x"], cfg["date_y"]),
              f"使用日期：{date_str}",
              font=get_font(cfg["f_date"], cfg["fs_date"]), fill=c)

    f_role = get_font(cfg["f_role"], cfg["fs_role"])
    f_name = get_font(cfg["f_name"], cfg["fs_name"])
    f_num  = get_font(cfg["f_num"],  cfg["fs_num"])

    sep_gap       = cfg["sep_gap"]
    sep_thickness = cfg["sep_w"]
    num_gap       = cfg["num_gap"]
    row_y         = cfg["row_y"]

    def text_width(text, font):
        try:
            bb = font.getbbox(str(text))
            w  = bb[2] - bb[0]
            if w > 0:
                return float(w)
        except Exception:
            pass
        try:
            w = draw.textlength(str(text), font=font)
            if w > 0:
                return w
        except Exception:
            pass
        try:
            single = font.getbbox("國")[2] - font.getbbox("國")[0]
            return single * len(str(text))
        except Exception:
            return cfg["fs_role"] * len(str(text))

    def text_height(text, font):
        try:
            bb = font.getbbox(str(text))
            return bb[3] - bb[1]
        except Exception:
            return cfg["fs_role"]

    # ── 職稱：尊重 Excel 換行（\n） ─────────────────────────
    role_str   = str(role)
    role_lines = role_str.splitlines() if role_str else [role_str]
    line_h     = text_height(role_lines[0] if role_lines else "國", f_role)
    line_gap   = int(line_h * 0.15)
    role_w     = max(text_width(l, f_role) for l in role_lines)
    role_total_h = len(role_lines) * line_h + (len(role_lines) - 1) * line_gap

    # ── 判斷姓名是否有效 ─────────────────────────────────────
    name_str  = str(name).strip()
    has_name  = name_str and name_str.lower() not in ("nan", "none", "")

    num_w    = text_width(str(num), f_num)
    num_h_bb = text_height(str(num), f_num)

    if has_name:
        name_w    = text_width(name_str, f_name)
        name_h_bb = text_height(name_str, f_name)
        total_w   = role_w + sep_gap + sep_thickness + sep_gap + name_w + num_gap + num_w
    else:
        name_w  = 0
        total_w = role_w + num_gap + num_w

    start_x = (W - total_w) / 2

    # ── 畫職稱（多行，垂直置中在 row_y） ─────────────────────
    role_start_y = row_y - role_total_h // 2
    for li, line in enumerate(role_lines):
        ly = role_start_y + li * (line_h + line_gap)
        draw.text((start_x, ly), line, font=f_role, fill=c)

    if has_name:
        # 分隔線：拉滿職稱總高度
        sep_x      = start_x + role_w + sep_gap
        sep_top    = role_start_y
        sep_bottom = role_start_y + role_total_h
        draw.line([(sep_x, sep_top), (sep_x, sep_bottom)], fill=sc, width=sep_thickness)

        # 姓名：垂直置中對齊整列
        name_x = sep_x + sep_thickness + sep_gap
        name_y = row_y - name_h_bb // 2
        draw.text((name_x, name_y), name_str, font=f_name, fill=c)

        # 編號：底部對齊姓名底部往上 10px
        num_x = name_x + name_w + num_gap
        num_y = name_y + name_h_bb - num_h_bb - 10
        draw.text((num_x, num_y), str(num), font=f_num, fill=c)
    else:
        # 無姓名：職稱＋編號整體置中，編號貼右側
        num_x = start_x + role_w + num_gap
        num_y = row_y - num_h_bb // 2
        draw.text((num_x, num_y), str(num), font=f_num, fill=c)

    return img


def build_cfg():
    return dict(
        w=int(badge_w), h=int(badge_h),
        color=txt_color, sep_color=sep_color,
        f_prog=f_prog, fs_prog=font_prog,
        f_unit=f_unit, fs_unit=font_unit,
        f_date=f_date, fs_date=font_date,
        f_role=f_role, fs_role=font_role,
        f_name=f_name, fs_name=font_name,
        f_num=f_num,   fs_num=font_num,
        prog_x=prog_x, prog_y=prog_y,
        unit_x=unit_x, unit_y=unit_y,
        date_x=date_x, date_y=date_y,
        row_y=int(row_y),
        sep_w=sep_w, sep_gap=sep_gap, num_gap=num_gap,
    )

# ── A4 預覽圖產生 ────────────────────────────────────────────────
def make_a4_preview(badge_imgs, page_idx, cols_n, rows_n, mg_t, mg_b, mg_l, mg_r):
    """
    把第 page_idx 頁的工作證排成 A4 比例預覽圖（白底）
    A4: 210 x 297mm → 比例 1:1.414，預覽圖寬固定 800px
    """
    PW, PH = 800, int(800 * 297 / 210)
    preview = Image.new("RGB", (PW, PH), "white")

    # 邊界轉換（mm → px，以 PW=800px=210mm 為基準）
    scale = PW / 210
    pad_t = int(mg_t * scale)
    pad_b = int(mg_b * scale)
    pad_l = int(mg_l * scale)
    pad_r = int(mg_r * scale)

    usable_w = PW - pad_l - pad_r
    usable_h = PH - pad_t - pad_b - int(4 * scale)  # 安全邊距

    cell_w = usable_w // cols_n
    cell_h = usable_h // rows_n

    per_page = cols_n * rows_n
    start    = page_idx * per_page
    page_imgs = badge_imgs[start : start + per_page]

    for idx, bimg in enumerate(page_imgs):
        ri = idx // cols_n
        ci = idx % cols_n
        x  = pad_l + ci * cell_w
        y  = pad_t + ri * cell_h
        # 等比縮放填入格子（保留比例）
        bimg_rgb = bimg.convert("RGB")
        bw, bh   = bimg_rgb.size
        ratio    = min(cell_w / bw, cell_h / bh)
        nw, nh   = int(bw * ratio), int(bh * ratio)
        resized  = bimg_rgb.resize((nw, nh), Image.LANCZOS)
        # 置中放入格子
        ox = x + (cell_w - nw) // 2
        oy = y + (cell_h - nh) // 2
        preview.paste(resized, (ox, oy))

    # 畫格線
    draw = ImageDraw.Draw(preview)
    for ci in range(cols_n + 1):
        x = pad_l + ci * cell_w
        draw.line([(x, pad_t), (x, pad_t + rows_n * cell_h)], fill="#cccccc", width=1)
    for ri in range(rows_n + 1):
        y = pad_t + ri * cell_h
        draw.line([(pad_l, y), (pad_l + cols_n * cell_w, y)], fill="#cccccc", width=1)
    # 頁面外框
    draw.rectangle([(0, 0), (PW-1, PH-1)], outline="#aaaaaa", width=2)

    return preview

# ── 主邏輯 ───────────────────────────────────────────────────────
if bg_file and xl_file and col_role:
    st.divider()
    bg  = Image.open(bg_file).convert("RGBA")
    df  = pd.read_excel(xl_file)
    cfg = build_cfg()

    # 產生所有工作證圖（供預覽與 PDF 共用）
    all_badges = []
    for _, r in df.iterrows():
        all_badges.append(make_badge(bg,
                                     role=str(r[col_role]),
                                     name=str(r[col_name]),
                                     num=str(r[col_num]),
                                     cfg=cfg))

    cols_n   = int(per_row)
    rows_n   = per_page // cols_n
    total_pages = -(-len(all_badges) // per_page)

    # ── 單張預覽 ─────────────────────────────────────────────
    st.subheader("👁️ 單張預覽")
    st.image(all_badges[0].convert("RGB"), width=500)

    # ── A4 整頁預覽（可翻頁） ────────────────────────────────
    st.divider()
    st.subheader("📄 A4 整頁預覽")

    if "preview_page" not in st.session_state:
        st.session_state.preview_page = 0
    if st.session_state.preview_page >= total_pages:
        st.session_state.preview_page = 0

    nav1, nav2, nav3 = st.columns([1, 3, 1])
    with nav1:
        if st.button("◀ 上一頁", use_container_width=True,
                     disabled=st.session_state.preview_page == 0):
            st.session_state.preview_page -= 1
            st.rerun()
    with nav2:
        st.markdown(
            f"<div style='text-align:center;padding-top:8px;font-weight:600;'>"
            f"第 {st.session_state.preview_page + 1} 頁 / 共 {total_pages} 頁</div>",
            unsafe_allow_html=True
        )
    with nav3:
        if st.button("下一頁 ▶", use_container_width=True,
                     disabled=st.session_state.preview_page >= total_pages - 1):
            st.session_state.preview_page += 1
            st.rerun()

    a4_img = make_a4_preview(
        all_badges,
        page_idx = st.session_state.preview_page,
        cols_n   = cols_n,
        rows_n   = rows_n,
        mg_t     = margin_top,
        mg_b     = margin_bottom,
        mg_l     = margin_left,
        mg_r     = margin_right,
    )
    st.image(a4_img, use_container_width=True)

    # ── 產生 PDF ─────────────────────────────────────────────
    st.divider()
    if st.button("🖨️ 產生 PDF（A4，每頁 6 張）", type="primary", use_container_width=True):
        progress = st.progress(0, text="存檔中…")
        tmp_dir = tempfile.mkdtemp()
        paths   = []
        for i, img in enumerate(all_badges):
            p = os.path.join(tmp_dir, f"badge_{i:03d}.png")
            img.convert("RGB").save(p, dpi=(150, 150))
            paths.append(p)
            progress.progress((i + 1) / len(all_badges), text=f"存檔 {i+1}/{len(all_badges)}…")

        progress.progress(1.0, text="排版 PDF…")

        pdf_buf = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buf, pagesize=A4,
            leftMargin   = margin_left   * mm,
            rightMargin  = margin_right  * mm,
            topMargin    = margin_top    * mm,
            bottomMargin = margin_bottom * mm,
        )

        # 自動計算 cell 大小，扣除安全邊距確保三列塞得進去
        usable_w = (210 - margin_left - margin_right) * mm
        usable_h = (297 - margin_top  - margin_bottom) * mm - 4  # 4pt 安全邊距
        cell_w   = usable_w / cols_n
        cell_h   = usable_h / rows_n

        story = []
        for page_start in range(0, len(paths), per_page):
            page_paths = paths[page_start : page_start + per_page]
            while len(page_paths) < per_page:
                page_paths.append(None)

            tbl_rows = []
            for ri in range(rows_n):
                row_cells = []
                for ci in range(cols_n):
                    idx = ri * cols_n + ci
                    p   = page_paths[idx]
                    row_cells.append(RLImage(p, width=cell_w, height=cell_h) if p else "")
                tbl_rows.append(row_cells)

            tbl = Table(tbl_rows, colWidths=[cell_w]*cols_n, rowHeights=[cell_h]*rows_n)
            tbl.setStyle(TableStyle([
                ("ALIGN",  (0,0), (-1,-1), "CENTER"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("GRID",   (0,0), (-1,-1), 0.3, colors.lightgrey),
            ]))
            story.append(tbl)
            if page_start + per_page < len(paths):
                story.append(PageBreak())

        doc.build(story)
        pdf_buf.seek(0)

        st.success(f"✅ 共產生 {len(all_badges)} 張工作證，{total_pages} 頁 PDF")
        st.download_button(
            label="⬇️ 下載 PDF",
            data=pdf_buf,
            file_name="工作證_阿甯咕爸鼻不見了.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

elif not bg_file and not xl_file:
    st.info("👆 請上傳底圖與 Excel 名單後開始使用")
elif not bg_file:
    st.warning("⚠️ 請上傳底圖")
elif not xl_file:
    st.warning("⚠️ 請上傳 Excel 名單")
