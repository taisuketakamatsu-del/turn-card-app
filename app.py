import os
import io
import json
import datetime
import unicodedata
import urllib.request
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="TURN Training Card", layout="wide")

# フォントの確実な取得と配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "NotoSansJP-Bold.ttf")

if not os.path.exists(FONT_PATH) or os.path.getsize(FONT_PATH) < 500000:
    try:
        font_url = "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/static/NotoSansJP-Bold.ttf"
        urllib.request.urlretrieve(font_url, FONT_PATH)
    except Exception:
        pass

st.markdown("""
<style>
/* ヘッダー・フッター非表示 */
header[data-testid="stHeader"], 
[data-testid="stHeader"], 
[data-testid="stToolbar"], 
[data-testid="stDecoration"],
footer {
    display: none !important;
    height: 0 !important;
}

div[data-testid="stAppViewContainer"] > section,
.main,
.main .block-container,
[data-testid="stMainBlockContainer"],
.block-container {
    padding-top: 0.2rem !important;
    margin-top: 0rem !important;
    padding-bottom: 0.5rem !important;
}

html, body, [class*="css"] {
    font-family: 'Noto Sans JP', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: #0F172A !important;
}

.stApp {
    background-color: #F8FAFC !important;
}

.main .block-container {
    max-width: 1320px !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    margin: 0 auto !important;
}

.app-title {
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    margin-top: 0 !important;
    margin-bottom: 0.5rem !important;
}

.section-label {
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    color: #475569 !important;
    margin-bottom: 0.2rem !important;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* --- タブのホバー・非選択・選択中の文字色・背景色の固定 --- */
div[data-baseweb="tab-list"] {
    background-color: #E2E8F0 !important;
    border-radius: 8px !important;
    padding: 3px !important;
    gap: 4px !important;
    margin-bottom: 0.8rem !important;
    width: fit-content !important;
    display: inline-flex !important;
}

button[data-baseweb="tab"] {
    border-radius: 6px !important;
    border: none !important;
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    padding: 6px 16px !important;
    background-color: transparent !important;
}

button[data-baseweb="tab"] p,
button[data-baseweb="tab"] span,
button[data-baseweb="tab"] div {
    color: #475569 !important;
    font-weight: 700 !important;
}

button[data-baseweb="tab"]:hover {
    background-color: rgba(255, 255, 255, 0.5) !important;
}

button[data-baseweb="tab"]:hover p,
button[data-baseweb="tab"]:hover span,
button[data-baseweb="tab"]:hover div {
    color: #0F172A !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    background-color: #FFFFFF !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.12) !important;
}

button[data-baseweb="tab"][aria-selected="true"] p,
button[data-baseweb="tab"][aria-selected="true"] span,
button[data-baseweb="tab"][aria-selected="true"] div {
    color: #2563EB !important;
    font-weight: 700 !important;
}

/* --- アコーディオン（詳細設定）のホバー制御 --- */
div[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    margin-top: 0.4rem !important;
}

div[data-testid="stExpander"] summary {
    background-color: #FFFFFF !important;
    border-radius: 8px !important;
    color: #0F172A !important;
}

div[data-testid="stExpander"] summary:hover {
    background-color: #F1F5F9 !important;
    color: #0F172A !important;
}

div[data-testid="stExpander"] summary * {
    color: #0F172A !important;
    font-weight: 700 !important;
}

div[data-testid="stExpander"] label, .stTextInput label {
    color: #334155 !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
}

div[data-baseweb="select"] {
    background-color: #FFFFFF !important;
    border-radius: 8px !important;
    border: 1px solid #CBD5E1 !important;
}

div[data-baseweb="select"] * {
    color: #0F172A !important;
    background-color: #FFFFFF !important;
}

.stTextArea textarea, .stTextInput input {
    font-size: 0.88rem !important;
    line-height: 1.5 !important;
    border-radius: 8px !important;
    border: 1px solid #CBD5E1 !important;
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    caret-color: #2563EB !important;
}

div.stDownloadButton > button, div.stButton > button {
    height: 42px !important;
    background-color: #0F172A !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 0 1rem !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
    width: 100% !important;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08) !important;
}

div.stDownloadButton > button:hover, div.stButton > button:hover {
    background-color: #1E293B !important;
    color: #FFFFFF !important;
}

div[data-testid="stRadio"] > div {
    background-color: #E2E8F0 !important;
    padding: 3px !important;
    border-radius: 8px !important;
    display: inline-flex !important;
    gap: 4px !important;
    margin: 0 !important;
    width: 260px !important;
    height: 36px !important;
}

div[data-testid="stRadio"] label {
    flex: 1 !important;
    height: 30px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: transparent !important;
    border-radius: 6px !important;
    cursor: pointer !important;
}

div[data-testid="stRadio"] label > div:first-child {
    display: none !important;
}

div[data-testid="stRadio"] label p {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: #475569 !important;
    margin: 0 !important;
}

div[data-testid="stRadio"] label:has(input:checked) {
    background-color: #FFFFFF !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
}

div[data-testid="stRadio"] label:has(input:checked) p {
    color: #0F172A !important;
}

div[data-testid="stImage"] img {
    max-height: 82vh !important;
    width: auto !important;
    object-fit: contain !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
    background-color: #FFFFFF !important;
}

.history-card {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    padding: 0.8rem !important;
    margin-bottom: 0.6rem !important;
}
.history-card-title {
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    color: #0F172A !important;
}
.history-card-date {
    font-size: 0.75rem !important;
    color: #64748B !important;
    margin-top: 2px !important;
}
</style>
""", unsafe_allow_html=True)

components.html("""
<script>
(function(){
  const parentDoc = window.parent.document;
  if(parentDoc.instantSubmitInjected) return;
  parentDoc.instantSubmitInjected = true;

  let timer = null;
  let isComposing = false;

  parentDoc.addEventListener('compositionstart', function(){
    isComposing = true;
  }, true);

  parentDoc.addEventListener('compositionend', function(e){
    isComposing = false;
    triggerInstantSubmit(e.target);
  }, true);

  function triggerInstantSubmit(target) {
    if(!target || target.tagName !== 'TEXTAREA') return;
    clearTimeout(timer);
    timer = setTimeout(function() {
      if(!isComposing) {
        const ev = new KeyboardEvent('keydown', {
          key: 'Enter', code: 'Enter', keyCode: 13, which: 13, ctrlKey: true, bubbles: true, cancelable: true
        });
        target.dispatchEvent(ev);
      }
    }, 200);
  }

  parentDoc.addEventListener('input', function(e) {
    if(!isComposing) {
      triggerInstantSubmit(e.target);
    }
  }, true);
})();
</script>
""", height=0, width=0)

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

def load_memory_callback(item):
    st.session_state["input_textarea_key"] = item["text"]
    st.session_state["input_tag_key"] = item["tag"]
    st.session_state["input_footer_key"] = item["footer"]

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

def auto_analyze_break_japanese(text):
    text = text.replace('<br>', '').strip()
    if '\n' in text or len(text) <= 10:
        return text

    patterns = [
        "返されると、", "済まされると、", "言われると、", "書かれると、", "確認されると", "話されると", "返事されると", "されると", "される", 
        "伝わらず", "見えず", "短文だと", "内容を", "電話で", "だけで", "まま", "見て", "前で", "以外のことを",
        "と、", "ば、", "たら、", "で、", "は、", "が、",
        "と", "が", "を", "に", "で", "は", "も", "から", "まで", "、"
    ]
    
    center = len(text) / 2.0
    best_pos = -1
    min_diff = 999

    for p in patterns:
        pos = 0
        while True:
            idx = text.find(p, pos)
            if idx == -1:
                break
            split_at = idx + len(p)
            if 3 <= split_at <= len(text) - 3:
                diff = abs(split_at - center)
                if diff < min_diff:
                    min_diff = diff
                    best_pos = split_at
            pos = idx + 1
        if best_pos != -1 and min_diff <= 3.5:
            break

    if best_pos != -1:
        return text[:best_pos] + "\n" + text[best_pos:]

    mid = len(text) // 2
    return text[:mid] + "\n" + text[mid:]

def get_japanese_font(size):
    if os.path.exists(FONT_PATH) and os.path.getsize(FONT_PATH) > 500000:
        try:
            return ImageFont.truetype(FONT_PATH, size)
        except Exception:
            pass

    candidates = [
        '/System/Library/Fonts/Supplemental/ヒラギノ角ゴ ProN W6.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc'
    ]
    for path in candidates:
        if os.path.exists(path) and os.path.getsize(path) > 10000:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def create_fallback_frame():
    canvas_w, canvas_h = 2373, 3379
    img = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    dash_color = (200, 210, 220, 255)
    x_coords = [158, 1233, 2307]
    y_coords = [128, 777, 1426, 2075, 2725, 3376]
    for x in x_coords:
        for y in range(y_coords[0], y_coords[-1], 20):
            draw.line([(x, y), (x, min(y + 10, y_coords[-1]))], fill=dash_color, width=3)
    for y in y_coords:
        for x in range(x_coords[0], x_coords[-1], 20):
            draw.line([(x, y), (min(x + 10, x_coords[-1]), y)], fill=dash_color, width=3)
    return img

def get_frame_image(uploaded_file):
    if uploaded_file is not None:
        try:
            return Image.open(uploaded_file).convert('RGBA')
        except Exception:
            pass

    for filename in os.listdir('.'):
        normalized = unicodedata.normalize('NFC', filename)
        if ("カード" in normalized or "本家" in normalized or "input_file" in normalized) and normalized.endswith(('.png', '.jpg', '.jpeg')):
            try:
                return Image.open(filename).convert('RGBA')
            except Exception:
                pass

    return create_fallback_frame()

def generate_card_layers(card_lines, tag_title, footer_title, frame_img):
    canvas_w, canvas_h = 2373, 3379
    x_coords = [158, 1233, 2307]
    y_coords = [128, 777, 1426, 2075, 2725, 3376]

    text_layer = Image.new('RGBA', (canvas_w, canvas_h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(text_layer)

    font_tag = get_japanese_font(42)
    font_text = get_japanese_font(52)
    font_footer = get_japanese_font(30)

    for i, text in enumerate(card_lines[:10]):
        col = i % 2
        row = i // 2
        
        box_x0 = x_coords[col]
        box_x1 = x_coords[col + 1]
        box_y0 = y_coords[row]
        box_y1 = y_coords[row + 1]
        
        cx = (box_x0 + box_x1) / 2.0
        cy = (box_y0 + box_y1) / 2.0
        
        tag_w, tag_h = 320, 70
        tag_x0 = cx - tag_w / 2.0
        tag_y0 = box_y0 + 70
        draw.rounded_rectangle([tag_x0, tag_y0, tag_x0 + tag_w, tag_y0 + tag_h], radius=18, fill=(45, 55, 72))
        draw.text((cx, tag_y0 + tag_h/2.0), tag_title, fill=(255, 255, 255), font=font_tag, anchor='mm')
        
        analyzed_text = auto_analyze_break_japanese(text)
        draw.text((cx, cy + 20), analyzed_text, fill=(26, 32, 44), font=font_text, anchor='mm', align='center', spacing=25)
        
        draw.text((box_x1 - 40, box_y1 - 40), footer_title, fill=(160, 174, 192), font=font_footer, anchor='rb')

    composite_layer = text_layer.copy()
    if frame_img is not None:
        try:
            f_img = frame_img.convert('RGBA')
            if f_img.size != (canvas_w, canvas_h):
                f_img = f_img.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)

            arr_frame = np.array(f_img)
            if len(arr_frame.shape) == 3 and arr_frame.shape[2] == 4:
                rgb_part = arr_frame[:, :, :3]
                is_white = np.all(rgb_part >= 240, axis=2)
                arr_frame[is_white, 3] = 0
                processed_frame = Image.fromarray(arr_frame)
                composite_layer = Image.alpha_composite(text_layer, processed_frame)
            else:
                composite_layer = Image.alpha_composite(text_layer, f_img)
        except Exception:
            pass

    return text_layer, composite_layer

def convert_to_pdf_bytes(pil_img):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    page_w, page_h = A4
    rgb_img = pil_img.convert('RGB')
    c.drawImage(ImageReader(rgb_img), 0, 0, width=page_w, height=page_h)
    c.save()
    return pdf_buffer.getvalue()

left_col, right_col = st.columns([1, 1.25], gap="large")

uploaded_frame = None

with left_col:
    st.markdown('<div class="app-title">TURN Training Card</div>', unsafe_allow_html=True)
    
    tab_edit, tab_memory = st.tabs(["✏️ カード編集", "📁 保存した記憶"])

    with tab_edit:
        st.markdown('<div class="section-label">カード選択</div>', unsafe_allow_html=True)
        st.selectbox(
            "パターン選択", 
            list(PRESETS.keys()), 
            key="preset_select_key", 
            on_change=on_preset_change, 
            label_visibility="collapsed"
        )

        st.markdown('<div class="section-label">テキスト編集（10行）</div>', unsafe_allow_html=True)
        st.text_area(
            "テキスト編集", 
            key="input_textarea_key", 
            height=210, 
            label_visibility="collapsed"
        )

        with st.expander("詳細設定（タグ・フッター・枠画像）", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("タグ名", key="input_tag_key")
            with c2:
                st.text_input("フッター表記", key="input_footer_key")
            
            uploaded_frame = st.file_uploader("枠画像の変更", type=["png", "jpg", "jpeg"])

        st.markdown('<div class="section-label" style="margin-top: 0.6rem;">この10枚を記憶・保存する</div>', unsafe_allow_html=True)
        save_c1, save_c2 = st.columns([1.8, 1])
        with save_c1:
            save_title = st.text_input("記憶の題名（例: 8月チーム用）", value="", placeholder="題名を入力...", label_visibility="collapsed")
        with save_c2:
            if st.button("💾 記憶する"):
                if save_title.strip():
                    memories = load_memories()
                    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    new_item = {
                        "id": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                        "title": save_title.strip(),
                        "date": now_str,
                        "tag": st.session_state["input_tag_key"],
                        "footer": st.session_state["input_footer_key"],
                        "text": st.session_state["input_textarea_key"]
                    }
                    memories.insert(0, new_item)
                    save_memories(memories)
                    st.success(f"『{save_title}』を記憶しました！")
                else:
                    st.warning("題名を入力してください")

    with tab_memory:
        memories = load_memories()
        st.markdown('<div class="section-label">保存された記憶一覧</div>', unsafe_allow_html=True)
        
        if not memories:
            st.info("保存された記憶はまだありません。編集タブから保存してください。")
        else:
            for idx, item in enumerate(memories):
                st.markdown(f"""
                <div class="history-card">
                    <div class="history-card-title">{item['title']}</div>
                    <div class="history-card-date">📅 保存日時: {item['date']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                m_btn1, m_btn2 = st.columns([1, 1])
                with m_btn1:
                    st.button(
                        "↩️ 読み込む", 
                        key=f"load_{item['id']}", 
                        on_click=load_memory_callback, 
                        args=(item,)
                    )
                with m_btn2:
                    st.button(
                        "🗑 削除", 
                        key=f"del_{item['id']}", 
                        on_click=delete_memory_callback, 
                        args=(idx,)
                    )

card_lines = [line.strip() for line in st.session_state["input_textarea_key"].strip().split("\n") if line.strip()]
frame_img_data = get_frame_image(uploaded_frame)
text_only_img, frame_overlaid_img = generate_card_layers(
    card_lines, 
    st.session_state["input_tag_key"], 
    st.session_state["input_footer_key"], 
    frame_img_data
)

with right_col:
    view_mode = st.radio(
        "表示切替",
        ["枠あり表示", "テキストのみ"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    display_img = frame_overlaid_img if view_mode == "枠あり表示" else text_only_img
    st.image(display_img)

with left_col:
    pdf_data = convert_to_pdf_bytes(display_img)
    st.download_button(
        label="PDFを保存する",
        data=pdf_data,
        file_name="card_print_final.pdf",
        mime="application/pdf"
    )
