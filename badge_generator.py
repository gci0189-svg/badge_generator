import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Table, TableStyle, PageBreak
from reportlab.lib.units import mm
from reportlab.lib import colors
import tempfile, os

# ── 固定內容 ────────────────────────────────────────────────────
PROG_NAME = "《阿甯咕的爸鼻不見了？》"
UNIT_NAME = "阿甯咕劇團"
DATE_STR  = "115.05.23 ～ 115.05.24"

st.set_page_config(page_title="工作證產生器 ｜ 阿甯咕劇團", layout="wide", page_icon="🎭")

# ── CSS 美化 ────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background: #fafafa; }
    .stButton > button {
        background: linear-gradient(135deg, #e8831a, #f5a623);
        color: white;
        font-weight: 700;
        font-size: 1.1rem;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(232,131,26,0.4);
    }
    .info-box {
        background: linear-gradient(135deg, #fff7ed, #fef3c7);
        border-left: 4px solid #e8831a;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0 1rem 0;
    }
    .info-box p { margin: 0.2rem 0; font-size: 0.95rem; color: #444; }
    .info-box strong { color: #c05621; }
</style>
""", unsafe_allow_html=True)

st.title("🎭 工作證產生器")
st.markdown(f"""
<div class="info-box">
    <p>📌 <strong>節目名稱</strong>：{PROG_NAME}</p>
    <p>🏢 <strong>使用單位</strong>：{UNIT_NAME}</p>
    <p>📅 <strong>使用日期</strong>：{DATE_STR}</p>
</div>
""", unsafe_allow_html=True)
st.caption("上傳底圖與 Excel 名單，自動產生 A4 排版 PDF（每頁 6 張，2 欄 × 3 列）")

# ── 側欄：文字位置設定 ──────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 版面設定")
    st.caption("座標原點為底圖左上角，單位：像素")

    badge_w = st.number_input("工作證寬度（px）", value=1353, step=10)
    badge_h = st.number_input("工作證高度（px）", value=1210, step=10)

    st.divider()
    st.subheader("📍 文字座標（x, y）")
    st.caption("固定欄位")

    px1, py1 = st.columns(2)
    prog_x = px1.number_input("節目名 X", value=60,  key="pgx")
    prog_y = py1.number_input("節目名 Y", value=30,  key="pgy")

    ux1, uy1 = st.columns(2)
    unit_x = ux1.number_input("單位 X", value=60,  key="ux")
    unit_y = uy1.number_input("單位 Y", value=110, key="uy")

    dx1, dy1 = st.columns(2)
    date_x = dx1.number_input("日期 X", value=60,  key="dx")
    date_y = dy1.number_input("日期 Y", value=190, key="dy")

    st.caption("變動欄位")
    rx1, ry1 = st.columns(2)
    role_x = rx1.number_input("職務 X", value=60,  key="rx")
    role_y = ry1.number_input("職務 Y", value=390, key="ry")

    nx1, ny1 = st.columns(2)
    name_x = nx1.number_input("姓名 X", value=510, key="nmx")
    name_y = ny1.number_input("姓名 Y", value=390, key="nmy")

    ex1, ey1 = st.columns(2)
    num_x = ex1.number_input("編號 X", value=970, key="ex")
    num_y = ey1.number_input("編號 Y", value=415, key="ey")

    st.divider()
    st.subheader("🔤 字型大小")
    font_sm  = st.slider("小字（節目/單位/日期）", 20, 80,  48)
    font_lg  = st.slider("大字（職務/姓名）",      50, 160, 110)
    font_num = st.slider("編號字體",               16,  60,  40)

    txt_color = st.color_picker("文字顏色", "#1a1a1a")

    st.divider()
    st.subheader("📄 PDF 設定")
    per_row = st.radio("每列幾張", [2, 3], index=0, horizontal=True)
    per_page = st.radio("每頁幾張", [4, 6], index=1, horizontal=True)

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
if xl_file:
    df = pd.read_excel(xl_file)
    cols = df.columns.tolist()
    st.divider()
    st.subheader("📋 Excel 欄位對應")
    c1, c2, c3 = st.columns(3)

    # 嘗試智慧預設
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
def get_font(size):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJKtc-Regular.otf",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "C:/Windows/Fonts/msjh.ttc",
        "C:/Windows/Fonts/mingliu.ttc",
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

# ── 產生單張工作證 ───────────────────────────────────────────────
def make_badge(bg_img, role, name, num, cfg):
    img = bg_img.copy().resize((cfg["w"], cfg["h"]), Image.LANCZOS)
    draw = ImageDraw.Draw(img)

    c  = cfg["color"]
    sm  = get_font(cfg["fsm"])
    lg  = get_font(cfg["flg"])
    nm  = get_font(cfg["fnum"])

    draw.text((cfg["prog_x"], cfg["prog_y"]), f"節目名稱：{PROG_NAME}", font=sm, fill=c)
    draw.text((cfg["unit_x"], cfg["unit_y"]), f"使用單位：{UNIT_NAME}", font=sm, fill=c)
    draw.text((cfg["date_x"], cfg["date_y"]), f"使用日期：{DATE_STR}",  font=sm, fill=c)
    draw.text((cfg["role_x"], cfg["role_y"]), str(role), font=lg, fill=c)
    draw.text((cfg["name_x"], cfg["name_y"]), str(name), font=lg, fill=c)
    draw.text((cfg["num_x"],  cfg["num_y"]),  str(num),  font=nm, fill=c)

    return img

# ── 組 cfg ─────────────────────────────────────────────────────
def build_cfg():
    return dict(
        w=int(badge_w), h=int(badge_h), color=txt_color,
        fsm=font_sm, flg=font_lg, fnum=font_num,
        prog_x=prog_x, prog_y=prog_y,
        unit_x=unit_x, unit_y=unit_y,
        date_x=date_x, date_y=date_y,
        role_x=role_x, role_y=role_y,
        name_x=name_x, name_y=name_y,
        num_x=num_x,   num_y=num_y,
    )

# ── 預覽 ─────────────────────────────────────────────────────────
if bg_file and xl_file:
    st.divider()
    st.subheader("👁️ 預覽第一張")

    bg = Image.open(bg_file).convert("RGBA")
    df = pd.read_excel(xl_file)
    first = df.iloc[0]
    cfg = build_cfg()

    preview = make_badge(bg,
                         role=str(first[col_role]),
                         name=str(first[col_name]),
                         num=str(first[col_num]),
                         cfg=cfg)
    st.image(preview, width=640)

    # ── 產生 PDF ─────────────────────────────────────────────────
    st.divider()
    if st.button("🖨️ 產生 PDF（A4，每頁 6 張）", type="primary", use_container_width=True):

        bg = Image.open(bg_file).convert("RGBA")
        df = pd.read_excel(xl_file)
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

        # 存暫存 PNG
        tmp_dir = tempfile.mkdtemp()
        paths = []
        for i, img in enumerate(badge_imgs):
            p = os.path.join(tmp_dir, f"badge_{i:03d}.png")
            img.convert("RGB").save(p, dpi=(150, 150))
            paths.append(p)

        # PDF 排版：A4 每頁 6 張（2 欄 × 3 列）
        pdf_buf = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buf, pagesize=A4,
            leftMargin=8*mm, rightMargin=8*mm,
            topMargin=8*mm, bottomMargin=8*mm
        )

        usable_w = 210*mm - 16*mm   # ≈ 194mm
        usable_h = 297*mm - 16*mm   # ≈ 281mm

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
                    p = page_paths[idx]
                    if p:
                        row_cells.append(RLImage(p, width=cell_w, height=cell_h))
                    else:
                        row_cells.append("")
                rows.append(row_cells)

            tbl = Table(rows,
                        colWidths=[cell_w] * cols_n,
                        rowHeights=[cell_h] * rows_n)
            tbl.setStyle(TableStyle([
                ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID",   (0, 0), (-1, -1), 0.3, colors.lightgrey),
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
