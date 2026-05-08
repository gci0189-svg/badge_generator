import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Image as RLImage, Table, TableStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
import tempfile, os

st.set_page_config(page_title="工作證產生器", layout="wide")
st.title("🎭 工作證產生器")
st.markdown("上傳底圖與 Excel 名單，自動產生 A4 排版 PDF（每頁 6 張）")

# ── 側欄：文字位置設定 ──────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 文字位置設定")
    st.caption("座標原點為底圖左上角，單位：像素")

    badge_w = st.number_input("工作證寬度（px）", value=900, step=10)
    badge_h = st.number_input("工作證高度（px）", value=600, step=10)

    st.divider()
    st.subheader("固定欄位（整批相同）")
    same_for_all = st.checkbox("節目名、單位、日期整批相同", value=True)

    if same_for_all:
        prog_name = st.text_input("節目名稱", "《阿窩咕的狗狗會說話 YA～》")
        unit_name = st.text_input("使用單位", "阿窩咕劇團")
        date_str  = st.text_input("使用日期", "114.11.11 ～ 114.11.16")

    st.divider()
    st.subheader("文字座標（x, y）")

    # 固定欄位座標
    px1, py1 = st.columns(2)
    prog_x = px1.number_input("節目名 X", value=30, key="pgx")
    prog_y = py1.number_input("節目名 Y", value=20, key="pgy")

    ux1, uy1 = st.columns(2)
    unit_x = ux1.number_input("單位 X", value=30, key="ux")
    unit_y = uy1.number_input("單位 Y", value=70, key="uy")

    dx1, dy1 = st.columns(2)
    date_x = dx1.number_input("日期 X", value=30, key="dx")
    date_y = dy1.number_input("日期 Y", value=120, key="dy")

    # 變動欄位座標
    st.divider()
    rx1, ry1 = st.columns(2)
    role_x = rx1.number_input("職務 X", value=30, key="rx")
    role_y = ry1.number_input("職務 Y", value=230, key="ry")

    nx1, ny1 = st.columns(2)
    name_x = nx1.number_input("姓名 X", value=250, key="nmx")
    name_y = ny1.number_input("姓名 Y", value=230, key="nmy")

    ex1, ey1 = st.columns(2)
    num_x = ex1.number_input("編號 X", value=480, key="ex")
    num_y = ey1.number_input("編號 Y", value=250, key="ey")

    st.divider()
    st.subheader("字型大小")
    font_sm  = st.slider("小字（節目/單位/日期）", 20, 60, 36)
    font_lg  = st.slider("大字（職務/姓名）", 40, 120, 72)
    font_num = st.slider("編號字體", 16, 50, 28)

    txt_color = st.color_picker("文字顏色", "#000000")

# ── 主區：上傳 ───────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    bg_file = st.file_uploader("📁 上傳底圖（JPG / PNG）", type=["jpg", "jpeg", "png"])

with col2:
    xl_file = st.file_uploader("📊 上傳 Excel 名單", type=["xlsx", "xls"])
    if xl_file:
        df = pd.read_excel(xl_file)
        st.dataframe(df, use_container_width=True)
        st.caption(f"共 {len(df)} 筆資料")

# ── 欄位對應 ─────────────────────────────────────────────────────
if xl_file:
    df = pd.read_excel(xl_file)
    cols = df.columns.tolist()
    st.divider()
    st.subheader("📋 Excel 欄位對應")
    c1, c2, c3 = st.columns(3)
    col_role = c1.selectbox("職務欄位", cols, index=min(0, len(cols)-1))
    col_name = c2.selectbox("姓名欄位", cols, index=min(1, len(cols)-1))
    col_num  = c3.selectbox("編號欄位", cols, index=min(2, len(cols)-1))

    if not same_for_all:
        c4, c5, c6 = st.columns(3)
        col_prog = c4.selectbox("節目名欄位", cols)
        col_unit = c5.selectbox("單位欄位", cols)
        col_date = c6.selectbox("日期欄位", cols)

# ── 產生單張工作證 ───────────────────────────────────────────────
def make_badge(bg_img, row, cfg):
    img = bg_img.copy().resize((cfg["w"], cfg["h"]))
    draw = ImageDraw.Draw(img)

    # 嘗試載入字型（Streamlit Cloud 上用預設字型）
    def get_font(size):
        for path in [
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "C:/Windows/Fonts/msjh.ttc",
        ]:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        return ImageFont.load_default()

    c = cfg["color"]
    sm, lg, nm = get_font(cfg["fsm"]), get_font(cfg["flg"]), get_font(cfg["fnum"])

    draw.text((cfg["prog_x"], cfg["prog_y"]), f"節目名稱：{row['prog']}", font=sm, fill=c)
    draw.text((cfg["unit_x"], cfg["unit_y"]), f"使用單位：{row['unit']}", font=sm, fill=c)
    draw.text((cfg["date_x"], cfg["date_y"]), f"使用日期：{row['date']}", font=sm, fill=c)
    draw.text((cfg["role_x"], cfg["role_y"]), str(row["role"]), font=lg, fill=c)
    draw.text((cfg["name_x"], cfg["name_y"]), str(row["name"]), font=lg, fill=c)
    draw.text((cfg["num_x"],  cfg["num_y"]),  str(row["num"]),  font=nm, fill=c)

    return img

# ── 預覽 ─────────────────────────────────────────────────────────
if bg_file and xl_file:
    st.divider()
    st.subheader("👁️ 預覽第一張")

    bg = Image.open(bg_file).convert("RGBA")
    df = pd.read_excel(xl_file)
    first = df.iloc[0]

    cfg = dict(
        w=int(badge_w), h=int(badge_h), color=txt_color,
        fsm=font_sm, flg=font_lg, fnum=font_num,
        prog_x=prog_x, prog_y=prog_y,
        unit_x=unit_x, unit_y=unit_y,
        date_x=date_x, date_y=date_y,
        role_x=role_x, role_y=role_y,
        name_x=name_x, name_y=name_y,
        num_x=num_x,   num_y=num_y,
    )

    row = {
        "prog": prog_name if same_for_all else str(first[col_prog]),
        "unit": unit_name if same_for_all else str(first[col_unit]),
        "date": date_str  if same_for_all else str(first[col_date]),
        "role": str(first[col_role]),
        "name": str(first[col_name]),
        "num":  str(first[col_num]),
    }

    preview = make_badge(bg, row, cfg)
    st.image(preview, width=600)

# ── 產生 PDF ─────────────────────────────────────────────────────
    st.divider()
    if st.button("🖨️ 產生 PDF（A4，每頁 6 張）", type="primary", use_container_width=True):
        bg = Image.open(bg_file).convert("RGBA")
        df = pd.read_excel(xl_file)

        badge_imgs = []
        for _, r in df.iterrows():
            row = {
                "prog": prog_name if same_for_all else str(r[col_prog]),
                "unit": unit_name if same_for_all else str(r[col_unit]),
                "date": date_str  if same_for_all else str(r[col_date]),
                "role": str(r[col_role]),
                "name": str(r[col_name]),
                "num":  str(r[col_num]),
            }
            badge_imgs.append(make_badge(bg, row, cfg))

        # 存成暫存 PNG，再排進 ReportLab
        tmp_dir = tempfile.mkdtemp()
        paths = []
        for i, img in enumerate(badge_imgs):
            p = os.path.join(tmp_dir, f"badge_{i:03d}.png")
            img.convert("RGB").save(p)
            paths.append(p)

        pdf_buf = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buf, pagesize=A4,
                                leftMargin=10*mm, rightMargin=10*mm,
                                topMargin=10*mm, bottomMargin=10*mm)

        # A4 可用區：190mm × 277mm，每頁 3 列 × 2 欄
        cell_w = 90 * mm
        cell_h = 90 * mm

        story = []
        for page_start in range(0, len(paths), 6):
            page_paths = paths[page_start:page_start+6]
            # 補空格到 6 個
            while len(page_paths) < 6:
                page_paths.append(None)

            rows = []
            for ri in range(3):
                r_cells = []
                for ci in range(2):
                    idx = ri * 2 + ci
                    p = page_paths[idx]
                    if p:
                        r_cells.append(RLImage(p, width=cell_w, height=cell_h))
                    else:
                        r_cells.append("")
                rows.append(r_cells)

            tbl = Table(rows, colWidths=[cell_w, cell_w], rowHeights=[cell_h]*3)
            tbl.setStyle(TableStyle([
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
            ]))
            story.append(tbl)

        doc.build(story)
        pdf_buf.seek(0)

        st.success(f"✅ 共產生 {len(badge_imgs)} 張工作證，{-(-len(badge_imgs)//6)} 頁 PDF")
        st.download_button(
            label="⬇️ 下載 PDF",
            data=pdf_buf,
            file_name="工作證.pdf",
            mime="application/pdf",
            use_container_width=True,
        )