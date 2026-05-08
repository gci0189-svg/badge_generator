# 🎭 工作證產生器 ｜ 阿甯咕劇團

自動批次產生工作證 PDF，A4 每頁排 6 張（2 欄 × 3 列）。

## 本次活動固定內容

| 欄位 | 內容 |
|------|------|
| 節目名稱 | 《阿甯咕的爸鼻不見了？》 |
| 使用單位 | 阿甯咕劇團 |
| 使用日期 | 115.05.23 ～ 115.05.24 |

---

## 快速開始（本機）

```bash
# 1. 安裝 CJK 字型（Linux）
sudo apt-get install -y fonts-noto-cjk

# 2. 安裝 Python 套件
pip install -r requirements.txt

# 3. 啟動
streamlit run app.py
```

---

## 部署到 Streamlit Cloud（免費）

### Step 1 — 上傳到 GitHub

1. 到 [github.com](https://github.com) 登入
2. 點右上角 **+** → **New repository**
3. 命名（例如 `badge-generator`），設為 Public
4. 將本資料夾所有檔案上傳：
   - `app.py`
   - `requirements.txt`
   - `packages.txt`
   - `README.md`

> 💡 可直接拖曳整個資料夾到 GitHub 網頁上傳

### Step 2 — 部署到 Streamlit Cloud

1. 到 [share.streamlit.io](https://share.streamlit.io) 用 GitHub 帳號登入
2. 點 **New app**
3. 選擇你的 repository、branch（main）、主程式（`app.py`）
4. 點 **Deploy!**，等 2～3 分鐘即完成 🎉

部署完成後你會得到一個公開連結，例如：  
`https://你的帳號-badge-generator-app-xxxxxx.streamlit.app`

---

## Excel 名單格式

| 職務 | 姓名 | 編號 |
|------|------|------|
| 行政統籌 | 劉桂伶 | 1 |
| 導演 | 陳大文 | 2 |
| ... | ... | ... |

- 欄位名稱可自訂，上傳後在網頁上指定對應欄位即可
- 支援 `.xlsx` / `.xls`

---

## 使用流程

1. 上傳**底圖**（JPG/PNG）
2. 上傳 **Excel 名單**
3. 左側欄調整文字座標與大小（對照預覽圖微調）
4. 確認預覽第一張正確後，點「產生 PDF」
5. 下載 PDF 送印 ✅

---

## 文字座標參考（以 1353×1210px 底圖為基準）

| 欄位 | 建議 X | 建議 Y |
|------|--------|--------|
| 節目名稱 | 60 | 30 |
| 使用單位 | 60 | 110 |
| 使用日期 | 60 | 190 |
| 職務 | 60 | 390 |
| 姓名 | 510 | 390 |
| 編號 | 970 | 415 |

可在左側欄即時調整，預覽視窗會同步更新。
