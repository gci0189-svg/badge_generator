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

def get_font(size):
    candidates = [
        os.path.join(os.path.dirname(__file__), "fonts", "NotoSansCJK-Regular.ttc"),
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "C:/Windows/Fonts/msjh.ttc",
        "C:/Windows/Fonts/mingliu.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

with st.sidebar:
    st.header("⚙️ 設定")

    st.subheader("工作證尺寸（px）")
    c1, c2 = st.columns(2)
    badge_w = c1.number_input("寬", value=900, step=10)
    badge_h = c2.number_input("高", value=600, step=10)

    st.divider()
    st.subheader("固定欄位")
    same_for_all = st.checkbox("節目名、單位、日期整批相同", value=True)
    if same_for_all:
        prog_name = st.text_input("節目名稱", "《阿甯咕的爸鼻不見了？》")
        unit_name = st.text_input("使用單位", "阿甯咕劇團")
        date_str  = st.text_input("使用日期", "115.05.23～115.05.24")

    st.divider()
    st.subheader("文字座標（x, y）")

    px1, py1 = st.columns(2)
    prog_x = px1.number_input("節目名 X", value=25)
    prog_y = py1.number_input("節目名 Y", value=14)

    ux1, uy1 = st.columns(2)
    unit_x = ux1.number_input("單位 X", value=25)
    unit_y = uy1.number_input("單位 Y", value=46)

    dx1, dy1 = st.columns(2)
    date_x = dx1.number_input("日期 X", value=25)
    date_y = dy1.number_input("日期 Y", value=78)

    st.caption("職稱｜姓名 編號 — 整列設定")
    row_y  = st.number_input("整列 Y 座標", value=220, step=5)
    role_x = st.number_input("職務起始 X", value=25)

    st.divider()
    st.subheader("字型大小")
    font_sm  = st.slider("小字（節目/單位/日期）", 20, 80, 36)
    font_lg  = st.slider("大字（職務/姓名）", 40, 150, 72)
    font_num = st.slider("編號字體", 16, 60, 28)

    st.divider()
    st.subheader("分隔線樣式")
    div_h   = st.slider("分隔線高度（px）", 10, 150, 72)
    div_w   = st.slider("分隔線粗細（px）", 1, 8, 3)
    div_pad = st.slider("分隔線左右留白（px）", 4, 40, 14)
    num_gap = st.slider("編號與姓名間距（px）", 4, 40, 12)

    txt_color = st.color_picker("文字顏色", "#000000")

col1, col2 = st.columns(2)
with col1:
    bg_file = st.file_uploader("📁 上傳底圖（JPG / PNG）", type=["jpg","jpeg","png"])
with col2:
    xl_file = st.file_uploader("📊 上傳 Excel 名單", type=["xlsx","xls"])
    if xl_file:
        df_preview = pd.read_excel(xl_file)
        st.dataframe(df_preview, use_container_width=True)
        st.caption(f"共 {len(df_preview)} 筆資料")

col_role = col_name = col_num = None
col_prog = col_unit = col_date = None

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

def make_badge(bg_img, row, cfg):
    img  = bg_img.copy().convert("RGBA").resize((cfg["w"], cfg["h"]))
    draw = ImageDraw.Draw(img)

    sm    = get_font(cfg["fsm"])
    lg    = get_font(cfg["flg"])
    num_f = get_font(cfg["fnum"])
    c     = cfg["color"]

    draw.text((cfg["prog_x"], cfg["prog_y"]), f"節目名稱：{row['prog']}", font=sm, fill=c)
    draw.text((cfg["unit_x"], cfg["unit_y"]), f"使用單位：{row['unit']}", font=sm, fill=c)
    draw.text((cfg["date_x"], cfg["date_y"]), f"使用日期：{row['date']}", font=sm, fill=c)

    role_str = str(row["role"])
    name_str = str(row["name"])
    num_str  = str(row["num"])

    y  = int(cfg["row_y"])
    rx = int(cfg["role_x"])

    try:
        role_w = int(lg.getlength(role_str))
        name_w = int(lg.getlength(name_str))
    except Exception:
        bb = draw.textbbox((0, 0), role_str, font=lg)
        role_w = bb[2] - bb[0]
        bb = draw.textbbox((0, 0), name_str, font=lg)
        name_w = bb[2] - bb[0]

    div_x = rx + role_w + cfg["div_pad"]
    nx    = div_x + cfg["div_w"] + cfg["div_pad"]
    ex    = nx + name_w + cfg["num_gap"]

    draw.text((rx, y), role_str, font=lg, fill=c)
    draw.line([(div_x, y), (div_x, y + cfg["div_h"])], fill=c, width=cfg["div_w"])
    draw.text((nx, y), name_str, font=lg, fill=c)

    num_y = y + (cfg["flg"] - cfg["fnum"]) // 2
    draw.text((ex, num_y), num_str, font=num_f, fill=c)

    return img

if bg_file and xl_file and col_role:
    st.divider()
    st.subheader("👁️ 預覽第一張")

    bg    = Image.open(bg_file)
    df    = pd.read_excel(xl_file)
    first = df.iloc[0]

    cfg = dict(
        w=int(badge_w), h=int(badge_h), color=txt_color,
        fsm=font_sm, flg=font_lg, fnum=font_num,
        prog_x=prog_x, prog_y=prog_y,
        unit_x=unit_x, unit_y=unit_y,
        date_x=date_x, date_y=date_y,
        row_y=row_y,   role_x=role_x,
        div_h=div_h,   div_w=div_w,
        div_pad=div_pad, num_gap=num_gap,
    )
    row = {
        "prog": prog_name if same_for_all else str(first[col_prog]),
        "unit": unit_name if same_for_all else str(first[col_unit]),
        "date": date_str  if same_for_all else str(first[col_date]),
        "role": str(first[col_role]),
        "name": str(first[col_name]),
        "num":  str(first[col_num]),
    }

    with st.expander("🔍 除錯資訊"):
        f = get_font(font_lg)
        st.write(f"字型：{f}")
        try:
            st.write(f"職務寬度：{int(f.getlength(str(first[col_role])))} px")
        except Exception as e:
            st.write(f"getlength 失敗：{e}")

    preview = make_badge(bg, row, cfg)
    st.image(preview, width=700)

    st.divider()
    if st.button("🖨️ 產生 PDF（A4，每頁 6 張）", type="primary", use_container_width=True):
        bg  = Image.open(bg_file)
        df  = pd.read_excel(xl_file)
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

        cell_w = 90 * mm
        cell_h = 90 * mm
        story  = []

        for page_start in range(0, len(paths), 6):
            page_paths = paths[page_start:page_start+6]
            while len(page_paths) < 6:
                page_paths.append(None)

            rows = []
            for ri in range(3):
                r_cells = []
                for ci in range(2):
                    p = page_paths[ri * 2 + ci]
                    r_cells.append(RLImage(p, width=cell_w, height=cell_h) if p else "")
                rows.append(r_cells)

            tbl = Table(rows, colWidths=[cell_w, cell_w], rowHeights=[cell_h]*3)
            tbl.setStyle(TableStyle([
                ("ALIGN",  (0,0), (-1,-1), "CENTER"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("GRID",   (0,0), (-1,-1), 0.5, colors.lightgrey),
            ]))
            story.append(tbl)

        doc.build(story)
        pdf_buf.seek(0)

        pages = -(-len(badge_imgs) // 6)
        st.success(f"✅ 共產生 {len(badge_imgs)} 張工作證，{pages} 頁 PDF")
        st.download_button(
            label="⬇️ 下載 PDF",
            data=pdf_buf,
            file_name="工作證.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
