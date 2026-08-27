import os
import io
import json
import datetime
import unicodedata
import urllib.request
import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="TURN Training Card", layout="wide")

FONT_PATH = "NotoSansJP-Bold.ttf"

st.markdown("""
<style>
header[data-testid="stHeader"], [data-testid="stHeader"], [data-testid="stToolbar"], footer {
    display: none !important;
}
.main .block-container {
    max-width: 1320px !important;
    padding-top: 0.5rem !important;
}
html, body, [class*="css"] {
    font-family: 'Noto Sans JP', sans-serif !important;
}
button[data-baseweb="tab"] * {
    color: #475569 !important;
    font-weight: 700 !important;
}
button[data-baseweb="tab"][aria-selected="true"] * {
    color: #2563EB !important;
}
div.stDownloadButton > button, div.stButton > button {
    height: 42px !important;
    background-color: #0F172A !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

STORAGE_FILE = "saved_memories.json"

def load_memories():
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_memories(memories):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)

PRESETS = {
    "不快スイッチ": {
        "tag": "不快スイッチ",
        "footer": "TURN Training",
        "text": """「今ちょっといい？」と用件を書かずにチャットされると不安になる
リアクションがないと届いているのか不安になる
定時直前に「今日中で」と仕事を振られると焦る
結論を言わずに前置きをダラダラ話されるとイライラする
「で、要点は？」と話を途中で遮られると固まってしまう
「自由にやって」と丸投げされると放置された気がして困る
質問したときに「自分で考えて」と返されると次から聞きづらくなる
大勢の前で大げさに褒められると目立ってしまいやりづらい
成果を出しても完全にスルーされるとやる気がなくなる
周りで大きいため息や激しい打鍵音が聞こえると怯えてしまう"""
    },
    "Thinkカード": {
        "tag": "Thinkカード",
        "footer": "TURN Training",
        "text": """「なる早」でお願いします
「ちゃんと」確認しておいて
「いい感じに」まとめておいて
「適当に」対応しといて
「例の件」どうなった？
「ざっくり」でいいから教えて
「近いうちに」打ち合わせしよう
「手が空いたとき」にやっておいて
「ちょっと」話あるんだけど
「常識的に考えて」やってみて"""
    },
    "Navigateカード": {
        "tag": "Navigateカード",
        "footer": "TURN Training",
        "text": """「何か手伝えることある？」
「ここまでで気になる点はある？」
「◯日◯時までに終われば大丈夫です」
「相談してくれてありがとう」
「どこで困っているか教えて？」
「いま5分だけ時間大丈夫？」
「念のため前提を確認させて」
「いつもサポート助かっているよ」
「無理そうなら早めに教えてね」
「まずは一度ここで手を止めよう」"""
    }
}

if "input_textarea_key" not in st.session_state:
    st.session_state["input_textarea_key"] = PRESETS["不快スイッチ"]["text"]
if "input_tag_key" not in st.session_state:
    st.session_state["input_tag_key"] = PRESETS["不快スイッチ"]["tag"]
if "input_footer_key" not in st.session_state:
    st.session_state["input_footer_key"] = PRESETS["不快スイッチ"]["footer"]
if "input_font_size_key" not in st.session_state:
    st.session_state["input_font_size_key"] = 52
if "input_show_number_key" not in st.session_state:
    st.session_state["input_show_number_key"] = False

def load_memory_callback(item):
    st.session_state["input_textarea_key"] = item["text"]
    st.session_state["input_tag_key"] = item["tag"]
    st.session_state["input_footer_key"] = item["footer"]
    st.session_state["input_font_size_key"] = item.get("font_size", 52)
    st.session_state["input_show_number_key"] = item.get("show_number", False)

def delete_memory_callback(idx):
    memories = load_memories()
    if 0 <= idx < len(memories):
        memories.pop(idx)
        save_memories(memories)

def on_preset_change():
    selected = st.session_state["preset_select_key"]
    st.session_state["input_textarea_key"] = PRESETS[selected]["text"]
    st.session_state["input_tag_key"] = PRESETS[selected]["tag"]
    st.session_state["input_footer_key"] = PRESETS[selected]["footer"]
    st.session_state["input_font_size_key"] = 52
    st.session_state["input_show_number_key"] = False

def auto_analyze_break_japanese(text):
    text = text.replace('<br>', '').strip()
    if '\n' in text or len(text) <= 10:
        return text

    patterns = ["返されると、", "言われると、", "話されると、", "されると", "と、", "で、", "は、", "が、"]
    for p in patterns:
        if p in text:
            idx = text.find(p) + len(p)
            return text[:idx] + "\n" + text[idx:]

    mid = len(text) // 2
    return text[:mid] + "\n" + text[mid:]

def get_japanese_font(size):
    candidates = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc'
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def get_frame_image(uploaded_file):
    if uploaded_file is not None:
        try:
            return Image.open(uploaded_file).convert('RGBA')
        except Exception:
            pass
    for filename in os.listdir('.'):
        normalized = unicodedata.normalize('NFC', filename)
        if filename.endswith(('.png', '.jpg', '.jpeg')) and not filename.startswith('.'):
            if any(k in normalized for k in ["カード", "本家", "0テレ", "HR"]):
                try:
                    return Image.open(filename).convert('RGBA')
                except Exception:
                    pass
    return None

def generate_card_layers(card_lines, tag_title, footer_title, frame_img, font_size, show_number):
    canvas_w, canvas_h = 2373, 3379
    x_coords = [158, 1233, 2307]
    y_coords = [128, 777, 1426, 2075, 2725, 3376]

    text_layer = Image.new('RGBA', (canvas_w, canvas_h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(text_layer)

    font_tag = get_japanese_font(42)
    font_text = get_japanese_font(font_size)
    font_footer = get_japanese_font(30)
    font_number = get_japanese_font(28)

    for i, text in enumerate(card_lines[:10]):
        col, row = i % 2, i // 2
        box_x0, box_x1 = x_coords[col], x_coords[col + 1]
        box_y0, box_y1 = y_coords[row], y_coords[row + 1]
        cx, cy = (box_x0 + box_x1) / 2.0, (box_y0 + box_y1) / 2.0
        
        tag_w, tag_h = 320, 70
        tag_x0, tag_y0 = cx - tag_w / 2.0, box_y0 + 70
        draw.rounded_rectangle([tag_x0, tag_y0, tag_x0 + tag_w, tag_y0 + tag_h], radius=18, fill=(45, 55, 72))
        draw.text((cx, tag_y0 + tag_h/2.0), tag_title, fill=(255, 255, 255), font=font_tag, anchor='mm')
        
        analyzed_text = auto_analyze_break_japanese(text)
        draw.text((cx, cy + 20), analyzed_text, fill=(26, 32, 44), font=font_text, anchor='mm', align='center', spacing=25)
        draw.text((box_x1 - 40, box_y1 - 40), footer_title, fill=(160, 174, 192), font=font_footer, anchor='rb')

        if show_number:
            draw.text((box_x0 + 40, box_y0 + 40), f"No.{i+1:02d}", fill=(160, 174, 192), font=font_number, anchor='lt')

    composite_layer = text_layer.copy()
    if frame_img is not None:
        try:
            f_img = frame_img.convert('RGBA')
            if f_img.size != (canvas_w, canvas_h):
                f_img = f_img.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
            composite_layer = Image.alpha_composite(text_layer, f_img)
        except Exception:
            pass

    return composite_layer

def convert_to_pdf_bytes(pil_img):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    rgb_img = pil_img.convert('RGB')
    img_buffer = io.BytesIO()
    rgb_img.save(img_buffer, format="JPEG", quality=80)
    img_buffer.seek(0)
    c.drawImage(ImageReader(img_buffer), 0, 0, width=A4[0], height=A4[1])
    c.save()
    return pdf_buffer.getvalue()

left_col, right_col = st.columns([1, 1.25], gap="large")
uploaded_frame = None

with left_col:
    st.markdown('### TURN Training Card')
    tab_edit, tab_memory = st.tabs(["✏️ カード編集", "📁 保存した記憶"])

    with tab_edit:
        st.selectbox("パターン選択", list(PRESETS.keys()), key="preset_select_key", on_change=on_preset_change)
        st.text_area("テキスト編集", key="input_textarea_key", height=200)

        with st.expander("詳細設定", expanded=False):
            c1, c2 = st.columns(2)
            with c1: st.text_input("タグ名", key="input_tag_key")
            with c2: st.text_input("フッター表記", key="input_footer_key")
            st.slider("文字サイズ", min_value=30, max_value=80, key="input_font_size_key")
            st.checkbox("通し番号を表示する", key="input_show_number_key")
            uploaded_frame = st.file_uploader("枠画像の変更", type=["png", "jpg", "jpeg"])

        save_c1, save_c2 = st.columns([2, 1])
        with save_c1:
            save_title = st.text_input("記憶の題名", placeholder="題名を入力...", label_visibility="collapsed")
        with save_c2:
            if st.button("💾 記憶する"):
                if save_title.strip():
                    memories = load_memories()
                    memories.insert(0, {
                        "id": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                        "title": save_title.strip(),
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "tag": st.session_state["input_tag_key"],
                        "footer": st.session_state["input_footer_key"],
                        "text": st.session_state["input_textarea_key"],
                        "font_size": st.session_state["input_font_size_key"],
                        "show_number": st.session_state["input_show_number_key"]
                    })
                    save_memories(memories)
                    st.success("保存しました！")

    with tab_memory:
        memories = load_memories()
        if not memories:
            st.info("保存された記憶はありません。")
        else:
            for idx, item in enumerate(memories):
                st.write(f"**{item['title']}** ({item['date']})")
                m1, m2 = st.columns(2)
                with m1: st.button("↩️ 読み込む", key=f"load_{item['id']}", on_click=load_memory_callback, args=(item,))
                with m2: st.button("🗑 削除", key=f"del_{item['id']}", on_click=delete_memory_callback, args=(idx,))

card_lines = [l.strip() for l in st.session_state["input_textarea_key"].split("\n") if l.strip()]
frame_img_data = get_frame_image(uploaded_frame)

display_img = generate_card_layers(
    card_lines, 
    st.session_state["input_tag_key"], 
    st.session_state["input_footer_key"], 
    frame_img_data,
    st.session_state["input_font_size_key"],
    st.session_state["input_show_number_key"]
)

with right_col:
    st.image(display_img)

with left_col:
    pdf_data = convert_to_pdf_bytes(display_img)
    st.download_button("💾 PDFをダウンロード・印刷する", data=pdf_data, file_name="card_print.pdf", mime="application/pdf")
