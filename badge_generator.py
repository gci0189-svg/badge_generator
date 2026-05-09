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

# ── 字型資料夾（repo 根目錄下的 fonts/） ────────────────────────
# 嘗試多種路徑找 fonts/，確保 Streamlit Cloud 也能正確讀到
def find_font_dir():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts"),
        os.path.join(os.getcwd(), "fonts"),
        "/app/fonts",          # Streamlit Cloud 部署路徑
        "/mount/src/fonts",    # 部分版本的 Streamlit Cloud
    ]
    # 找第一個存在且有字型檔的資料夾
    for path in candidates:
        if os.path.isdir(path):
            files = [f for f in os.listdir(path) if f.lower().endswith((".ttf",".otf",".ttc"))]
            if files:
                return path
    # 都找不到就回傳預設（讓後續邏輯靜默處理）
    return os.path.join(os.getcwd(), "fonts")

FONT_DIR = find_font_dir()

# Noto 備用字型（Streamlit Cloud 系統字型）
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
    """掃描 fonts/ 資料夾，回傳 {顯示名稱: 路徑}"""
    found = {}
    if os.path.isdir(FONT_DIR):
        for fname in sorted(os.listdir(FONT_DIR)):
            if fname.lower().endswith((".ttf", ".otf", ".ttc")):
                label = os.path.splitext(fname)[0]
                found[label] = os.path.join(FONT_DIR, fname)
    return found

REPO_FONTS  = scan_repo_fonts()
ALL_FONTS   = {**REPO_FONTS, **FALLBACK_FONTS}   # repo 字型優先
FONT_NAMES  = list(ALL_FONTS.keys())

def font_index(preferred, fallback_key=None):
    """
    先找 preferred 完全比對，再找部分比對，都找不到用 fallback_key 或 0。
    fonts/ 有字型時優先用；沒有時 fallback 到名稱相近的系統備用字型。
    """
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

# 各欄位預設字型
DEF_PROG  = font_index("jf open 粉圓",       "Sans Regular")   # 節目名稱
DEF_UNIT  = font_index("jf open 粉圓",       "Sans Regular")   # 使用單位
DEF_DATE  = font_index("jf open 粉圓",       "Sans Regular")   # 使用日期
DEF_ROLE  = font_index("思源黑體 Medium",    "Sans Medium")    # 職稱
DEF_NAME  = font_index("思源黑體 Heavy",     "Sans Bold")      # 姓名
DEF_NUM   = font_index("JetBrainsMono-Thin", "Sans Regular")   # 編號

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

    # ── 字型狀態提示 ─────────────────────────────────────────
    if REPO_FONTS:
        st.markdown(f'<div class="font-hint">✅ 已載入 {len(REPO_FONTS)} 個 repo 字型<br>📂 路徑：{FONT_DIR}</div>',
                    unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ fonts/ 資料夾無字型，使用系統備用字型\n📂 找尋路徑：{FONT_DIR}")

    st.divider()

    # ── 固定欄位內容 ─────────────────────────────────────────
    st.subheader("📝 活動資訊")
    prog_name = st.text_input("節目名稱", value="《阿甯咕的爸鼻不見了？》")
    date_str  = st.text_input("使用日期", value="115.05.23～115.05.24")
    st.caption(f"使用單位：{UNIT_NAME}（固定）")

    st.divider()

    # ── 尺寸 ─────────────────────────────────────────────────
    st.subheader("📐 工作證尺寸")
    st.caption("預設：9.5cm × 9cm @ 150dpi")
    badge_w = st.number_input("寬度（px）", value=561, step=10)
    badge_h = st.number_input("高度（px）", value=531, step=10)

    st.divider()

    # ── 字型選擇（各欄位獨立） ────────────────────────────────
    st.subheader("🔡 各欄位字型")
    f_prog = st.selectbox("節目名稱", FONT_NAMES, index=DEF_PROG, key="f_prog")
    f_unit = st.selectbox("使用單位", FONT_NAMES, index=DEF_UNIT, key="f_unit")
    f_date = st.selectbox("使用日期", FONT_NAMES, index=DEF_DATE, key="f_date")
    f_role = st.selectbox("職稱",     FONT_NAMES, index=DEF_ROLE, key="f_role")
    f_name = st.selectbox("姓名",     FONT_NAMES, index=DEF_NAME, key="f_name")
    f_num  = st.selectbox("編號",     FONT_NAMES, index=DEF_NUM,  key="f_num")

    st.divider()

    # ── 字型大小 ─────────────────────────────────────────────
    st.subheader("🔤 字型大小")
    font_prog = st.slider("節目名稱", 10, 50, 30)
    font_unit = st.slider("使用單位", 10, 50, 30)
    font_date = st.slider("使用日期", 10, 50, 30)
    font_role = st.slider("職稱",     20, 100, 46)
    font_name = st.slider("姓名",     20, 100, 50)
    font_num  = st.slider("編號",     10,  50, 30)

    txt_color = st.color_picker("文字顏色", "#1a1a1a")

    st.divider()

    # ── 座標設定 ─────────────────────────────────────────────
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
    sep_h   = st.slider("分隔線高度（px）", 10, 120, 50)
    sep_w   = st.slider("分隔線粗細（px）",  1,  10,  3)
    sep_gap = st.slider("分隔線左右留白（px）", 4, 40, 14)
    num_gap = st.slider("編號與姓名間距（px）", 4, 40, 12)
    sep_color = st.color_picker("分隔線顏色", "#1a1a1a")

    st.divider()
    st.subheader("📄 PDF 設定")
    per_row  = st.radio("每列幾張", [2, 3], index=0, horizontal=True)
    per_page = st.radio("每頁幾張", [4, 6], index=1, horizontal=True)

# ── 頁面頂部活動資訊 ────────────────────────────────────────────
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
@st.cache_resource
def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def get_font(font_key, size):
    path = ALL_FONTS.get(font_key, list(FALLBACK_FONTS.values())[0])
    return load_font(path, size)

# ── 產生單張工作證 ───────────────────────────────────────────────
def make_badge(bg_img, role, name, num, cfg):
    img  = bg_img.copy().resize((cfg["w"], cfg["h"]), Image.LANCZOS)
    draw = ImageDraw.Draw(img)
    c    = cfg["color"]
    sc   = cfg["sep_color"]
    W    = cfg["w"]

    # 固定三行
    draw.text((cfg["prog_x"], cfg["prog_y"]),
              f"節目名稱：{prog_name}",
              font=get_font(cfg["f_prog"], cfg["fs_prog"]), fill=c)
    draw.text((cfg["unit_x"], cfg["unit_y"]),
              f"使用單位：{UNIT_NAME}",
              font=get_font(cfg["f_unit"], cfg["fs_unit"]), fill=c)
    draw.text((cfg["date_x"], cfg["date_y"]),
              f"使用日期：{date_str}",
              font=get_font(cfg["f_date"], cfg["fs_date"]), fill=c)

    # 職稱｜姓名 編號 三者整體置中（方案B）
    f_role = get_font(cfg["f_role"], cfg["fs_role"])
    f_name = get_font(cfg["f_name"], cfg["fs_name"])
    f_num  = get_font(cfg["f_num"],  cfg["fs_num"])

    def text_width(draw_obj, text, font):
        try:
            w = draw_obj.textlength(str(text), font=font)
            if w > 0:
                return w
        except Exception:
            pass
        try:
            bb = font.getbbox(str(text))
            return bb[2] - bb[0]
        except Exception:
            return len(str(text)) * font.size

    role_w = text_width(draw, str(role), f_role)
    name_w = text_width(draw, str(name), f_name)
    num_w  = text_width(draw, str(num),  f_num)

    sep_gap       = cfg["sep_gap"]    # 分隔線左右留白
    sep_thickness = cfg["sep_w"]
    num_gap       = cfg["num_gap"]    # 編號與姓名間距

    total_w = role_w + sep_gap + sep_thickness + sep_gap + name_w + num_gap + num_w
    start_x = (W - total_w) / 2

    row_y   = cfg["row_y"]
    sep_h   = cfg["sep_h"]

    # 職稱
    draw.text((start_x, row_y), str(role), font=f_role, fill=c)

    # 分隔線
    sep_x = start_x + role_w + sep_gap
    draw.line([(sep_x, row_y + 4), (sep_x, row_y + sep_h)], fill=sc, width=sep_thickness)

    # 姓名
    name_x = sep_x + sep_thickness + sep_gap
    draw.text((name_x, row_y - 2), str(name), font=f_name, fill=c)

    # 編號（自動貼齊姓名右側）
    num_x = name_x + name_w + num_gap
    num_y = row_y + (cfg["fs_name"] - cfg["fs_num"]) // 2
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
        row_y=row_y,
        sep_h=sep_h, sep_w=sep_w,
        sep_gap=sep_gap, num_gap=num_gap,
    )

# ── 預覽 ─────────────────────────────────────────────────────────
if bg_file and xl_file and col_role:
    st.divider()
    st.subheader("👁️ 預覽第一張")
    bg    = Image.open(bg_file).convert("RGBA")
    df    = pd.read_excel(xl_file)
    cfg   = build_cfg()
    first = df.iloc[0]
    preview = make_badge(bg,
                         role=str(first[col_role]),
                         name=str(first[col_name]),
                         num=str(first[col_num]),
                         cfg=cfg)
    st.image(preview, width=640)

    # 除錯資訊（確認字型載入）
    with st.expander("🔍 除錯資訊（確認字型是否正確載入）"):
        f_role_key = cfg["f_role"]
        f_name_key = cfg["f_name"]
        f_num_key  = cfg["f_num"]
        path_role = ALL_FONTS.get(f_role_key, "找不到")
        path_name = ALL_FONTS.get(f_name_key, "找不到")
        path_num  = ALL_FONTS.get(f_num_key,  "找不到")
        st.write(f"職稱字型：`{f_role_key}` → `{path_role}`")
        st.write(f"姓名字型：`{f_name_key}` → `{path_name}`")
        st.write(f"編號字型：`{f_num_key}` → `{path_num}`")
        st.write(f"路徑存在：職稱={os.path.exists(path_role)}, 姓名={os.path.exists(path_name)}, 編號={os.path.exists(path_num)}")
        st.write(f"FONT_DIR={FONT_DIR}")
        st.write(f"REPO_FONTS keys={list(REPO_FONTS.keys())}")

    # ── 產生 PDF ─────────────────────────────────────────────────
    st.divider()
    if st.button("🖨️ 產生 PDF（A4，每頁 6 張）", type="primary", use_container_width=True):
        bg  = Image.open(bg_file).convert("RGBA")
        df  = pd.read_excel(xl_file)
        cfg = build_cfg()

        progress = st.progress(0, text="產生工作證中…")
        badge_imgs = []
        for i, (_, r) in enumerate(df.iterrows()):
            badge_imgs.append(make_badge(bg,
                                         role=str(r[col_role]),
                                         name=str(r[col_name]),
                                         num=str(r[col_num]),
                                         cfg=cfg))
            progress.progress((i + 1) / len(df), text=f"產生中 {i+1}/{len(df)}…")

        progress.progress(1.0, text="排版 PDF…")

        tmp_dir = tempfile.mkdtemp()
        paths   = []
        for i, img in enumerate(badge_imgs):
            p = os.path.join(tmp_dir, f"badge_{i:03d}.png")
            img.convert("RGB").save(p, dpi=(150, 150))
            paths.append(p)

        pdf_buf = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buf, pagesize=A4,
            leftMargin=8*mm, rightMargin=8*mm,
            topMargin=8*mm, bottomMargin=8*mm
        )

        usable_w = 210*mm - 16*mm
        usable_h = 297*mm - 16*mm
        cols_n   = int(per_row)
        rows_n   = per_page // cols_n
        cell_w   = usable_w / cols_n
        cell_h   = usable_h / rows_n

        story = []
        for page_start in range(0, len(paths), per_page):
            page_paths = paths[page_start : page_start + per_page]
            while len(page_paths) < per_page:
                page_paths.append(None)

            rows = []
            for ri in range(rows_n):
                row_cells = []
                for ci in range(cols_n):
                    idx = ri * cols_n + ci
                    p   = page_paths[idx]
                    row_cells.append(RLImage(p, width=cell_w, height=cell_h) if p else "")
                rows.append(row_cells)

            tbl = Table(rows, colWidths=[cell_w]*cols_n, rowHeights=[cell_h]*rows_n)
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

        total_pages = -(-len(badge_imgs) // per_page)
        st.success(f"✅ 共產生 {len(badge_imgs)} 張工作證，{total_pages} 頁 PDF")
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
