import os
import io
import json
import base64
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

FONT_PATH = "NotoSansJP-Bold.ttf"

st.markdown("""
<style>
/* ヘッダー・フッター・不要な余白の完全削除 */
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
    padding-top: 0.8rem !important;
    padding-bottom: 0.8rem !important;
}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", "Noto Sans JP", sans-serif !important;
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

/* タイトル・ラベル */
.app-title {
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    letter-spacing: -0.01em;
    margin-bottom: 0.6rem !important;
}

.section-label {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    color: #64748B !important;
    margin-bottom: 0.3rem !important;
    letter-spacing: 0.03em;
    text-transform: uppercase;
}

/* タブのデザイン整理 */
button[data-baseweb="tab"] *, 
div[data-baseweb="tab-list"] button *,
[data-testid="stTab"] * {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
}

button[data-baseweb="tab"][aria-selected="true"] *, 
div[data-baseweb="tab-list"] button[aria-selected="true"] *,
[data-testid="stTab"][aria-selected="true"] * {
    color: #2563EB !important;
    -webkit-text-fill-color: #2563EB !important;
    font-weight: 700 !important;
}

div[data-baseweb="tab-list"] {
    background-color: #E2E8F0 !important;
    border-radius: 6px !important;
    padding: 2px !important;
    gap: 2px !important;
    margin-bottom: 0.8rem !important;
    width: fit-content !important;
    display: inline-flex !important;
}

div[data-baseweb="tab-list"] button {
    padding: 4px 12px !important;
    border-radius: 4px !important;
}

/* 詳細設定（stExpander） */
div[data-testid="stExpander"] {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 6px !important;
    margin-top: 0.5rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03) !important;
    overflow: hidden !important;
}

div[data-testid="stExpander"] summary {
    background-color: #FFFFFF !important;
    padding: 0.5rem 0.8rem !important;
    border-radius: 6px !important;
}

div[data-testid="stExpander"] summary:hover {
    background-color: #F1F5F9 !important;
}

div[data-testid="stExpander"] summary * {
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
}

div[data-testid="stExpander"] label, .stTextInput label, div[data-testid="stSlider"] label, div[data-testid="stCheckbox"] label * {
    color: #334155 !important;
    font-weight: 600 !important;
    font-size: 0.75rem !important;
}

div[data-baseweb="select"] {
    background-color: #FFFFFF !important;
    border-radius: 6px !important;
    border: 1px solid #CBD5E1 !important;
}

div[data-baseweb="select"] * {
    font-size: 0.82rem !important;
    color: #0F172A !important;
}

.stTextArea textarea, .stTextInput input {
    font-size: 0.82rem !important;
    line-height: 1.5 !important;
    border-radius: 6px !important;
    border: 1px solid #CBD5E1 !important;
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    padding: 0.5rem !important;
}

div.stDownloadButton > button, div.stButton > button {
    height: 36px !important;
    background-color: #0F172A !important;
    color: #FFFFFF !important;
    border-radius: 6px !important;
    border: none !important;
    padding: 0 0.8rem !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08) !important;
}

div[data-testid="stRadio"] > div {
    background-color: #E2E8F0 !important;
    padding: 2px !important;
    border-radius: 6px !important;
    display: inline-flex !important;
    gap: 2px !important;
    margin: 0 !important;
    width: 220px !important;
    height: 32px !important;
}

div[data-testid="stRadio"] label {
    flex: 1 !important;
    height: 28px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: transparent !important;
    border-radius: 4px !important;
}

div[data-testid="stRadio"] label p {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: #64748B !important;
}

div[data-testid="stRadio"] label:has(input:checked) {
    background-color: #FFFFFF !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.06) !important;
}

div[data-testid="stRadio"] label:has(input:checked) p {
    color: #0F172A !important;
}

/* 右カラム追従固定 (Sticky) 設定 */
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(2) {
    position: sticky !important;
    top: 0.8rem !important;
    align-self: flex-start !important;
}

/* プレビュー画像表示 */
div[data-testid="stImage"] img {
    max-height: 82vh !important;
    width: auto !important;
    object-fit: contain !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06) !important;
    background-color: #FFFFFF !important;
}

.history-card {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 6px !important;
    padding: 0.6rem !important;
    margin-bottom: 0.5rem !important;
}
.history-card-title {
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    color: #0F172A !important;
}
.history-card-date {
    font-size: 0.7rem !important;
    color: #64748B !important;
}
</style>
""", unsafe_allow_html=True)

# テキストリアルタイム同期JS
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
          key: 'Enter', code: 'Enter', keyCode: 13, which: 13, ctrlKey: true, metaKey: true, bubbles: true, cancelable: true
        });
        target.dispatchEvent(ev);
      }
    }, 300);
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

DEFAULT_FONT_SIZE = 60

if "input_textarea_key" not in st.session_state:
    st.session_state["input_textarea_key"] = PRESETS["不快スイッチ"]["text"]
if "input_tag_key" not in st.session_state:
    st.session_state["input_tag_key"] = PRESETS["不快スイッチ"]["tag"]
if "input_footer_key" not in st.session_state:
    st.session_state["input_footer_key"] = PRESETS["不快スイッチ"]["footer"]
if "input_font_size_key" not in st.session_state:
    st.session_state["input_font_size_key"] = DEFAULT_FONT_SIZE
if "input_show_number_key" not in st.session_state:
    st.session_state["input_show_number_key"] = False
if "input_auto_break_key" not in st.session_state:
    st.session_state["input_auto_break_key"] = True
if "input_use_custom_sizes" not in st.session_state:
    st.session_state["input_use_custom_sizes"] = False

for idx in range(10):
    key_name = f"custom_font_size_{idx}"
    if key_name not in st.session_state:
        st.session_state[key_name] = DEFAULT_FONT_SIZE

def load_memory_callback(item):
    st.session_state["input_textarea_key"] = item["text"]
    st.session_state["input_tag_key"] = item["tag"]
    st.session_state["input_footer_key"] = item["footer"]
    st.session_state["input_font_size_key"] = item.get("font_size", DEFAULT_FONT_SIZE)
    st.session_state["input_show_number_key"] = item.get("show_number", False)
    st.session_state["input_auto_break_key"] = item.get("auto_break", True)
    
    if "custom_sizes" in item and isinstance(item["custom_sizes"], list):
        st.session_state["input_use_custom_sizes"] = True
        for idx, s in enumerate(item["custom_sizes"][:10]):
            st.session_state[f"custom_font_size_{idx}"] = s
    else:
        st.session_state["input_use_custom_sizes"] = False

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
    st.session_state["input_font_size_key"] = DEFAULT_FONT_SIZE
    st.session_state["input_show_number_key"] = False
    st.session_state["input_auto_break_key"] = True
    st.session_state["input_use_custom_sizes"] = False
    for idx in range(10):
        st.session_state[f"custom_font_size_{idx}"] = DEFAULT_FONT_SIZE

def auto_analyze_break_japanese(text):
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

def process_card_text(text, enable_auto_break):
    text = text.replace("<改行>", "\n").replace("(改行)", "\n").replace("<br>", "\n").replace("<BR>", "\n").strip()
    if enable_auto_break and "\n" not in text:
        return auto_analyze_break_japanese(text)
    return text

def get_japanese_font(size):
    candidates = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/System/Library/Fonts/Supplemental/ヒラギノ角ゴ ProN W6.ttc'
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    try:
        url = "https://github.com/google/fonts/raw/main/ofl/notosansjp/static/NotoSansJP-Bold.ttf"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return ImageFont.truetype(io.BytesIO(response.read()), size)
    except Exception:
        pass

    return ImageFont.load_default()

# ★文字位置の調整座標
X_COORDS = [112, 1187, 2262]
Y_COORDS = [67, 716, 1365, 2014, 2663, 3312]

def create_fallback_frame():
    canvas_w, canvas_h = 2373, 3379
    img = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    dash_color = (200, 210, 220, 255)
    for x in X_COORDS:
        for y in range(Y_COORDS[0], Y_COORDS[-1], 20):
            draw.line([(x, y), (x, min(y + 10, Y_COORDS[-1]))], fill=dash_color, width=3)
    for y in Y_COORDS:
        for x in range(X_COORDS[0], X_COORDS[-1], 20):
            draw.line([(x, y), (min(x + 10, X_COORDS[-1]), y)], fill=dash_color, width=3)
    return img

def get_frame_image(uploaded_file):
    if uploaded_file is not None:
        try:
            return Image.open(uploaded_file).convert('RGBA')
        except Exception:
            pass

    for filename in os.listdir('.'):
        normalized = unicodedata.normalize('NFC', filename)
        if (filename.endswith(('.png', '.jpg', '.jpeg'))) and not filename.startswith('.'):
            if any(k in normalized for k in ["カード", "本家", "0テレ", "HR", "frame", "input"]):
                try:
                    return Image.open(filename).convert('RGBA')
                except Exception:
                    pass

    for filename in os.listdir('.'):
        if filename.endswith(('.png', '.jpg', '.jpeg')) and not filename.startswith('.'):
            try:
                return Image.open(filename).convert('RGBA')
            except Exception:
                pass

    return create_fallback_frame()

def generate_card_layers(card_lines, tag_title, footer_title, frame_img, default_font_size, font_sizes_list, show_number, enable_auto_break):
    canvas_w, canvas_h = 2373, 3379

    text_layer = Image.new('RGBA', (canvas_w, canvas_h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(text_layer)

    font_tag = get_japanese_font(42)
    font_footer = get_japanese_font(30)
    font_number = get_japanese_font(28)

    for i, text in enumerate(card_lines[:10]):
        col = i % 2
        row = i // 2
        
        box_x0 = X_COORDS[col]
        box_x1 = X_COORDS[col + 1]
        box_y0 = Y_COORDS[row]
        box_y1 = Y_COORDS[row + 1]
        
        cx = (box_x0 + box_x1) / 2.0
        cy = (box_y0 + box_y1) / 2.0
        
        tag_w, tag_h = 320, 70
        tag_x0 = cx - tag_w / 2.0
        tag_y0 = box_y0 + 70
        draw.rounded_rectangle([tag_x0, tag_y0, tag_x0 + tag_w, tag_y0 + tag_h], radius=18, fill=(45, 55, 72))
        draw.text((cx, tag_y0 + tag_h/2.0), tag_title, fill=(255, 255, 255), font=font_tag, anchor='mm')
        
        current_font_size = font_sizes_list[i] if font_sizes_list and i < len(font_sizes_list) else default_font_size
        font_text = get_japanese_font(current_font_size)

        processed_text = process_card_text(text, enable_auto_break)
        draw.text((cx, cy + 20), processed_text, fill=(26, 32, 44), font=font_text, anchor='mm', align='center', spacing=25)
        
        draw.text((box_x1 - 55, box_y1 - 55), footer_title, fill=(160, 174, 192), font=font_footer, anchor='rb')

        if show_number:
            draw.text((box_x0 + 45, box_y0 + 45), f"No.{i+1:02d}", fill=(160, 174, 192), font=font_number, anchor='lt')

    composite_layer = text_layer.copy()
    if frame_img is not None:
        try:
            f_img = frame_img.convert('RGBA')
            if f_img.size != (canvas_w, canvas_h):
                f_img = f_img.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)

            # 1. 枠線画像全体をシフト
            dx, dy = -46, -61
            shifted_frame = Image.new('RGBA', (canvas_w, canvas_h), (0, 0, 0, 0))
            shifted_frame.paste(f_img, (dx, dy))

            # 2. 上部余白領域の旧ロゴエリアをクリア
            draw_sf = ImageDraw.Draw(shifted_frame)
            draw_sf.rectangle([0, 0, 600, 66], fill=(0, 0, 0, 0))

            # 3. 元画像からロゴ領域（0テレHR）をピンポイント抽出
            raw_logo_area = f_img.crop((0, 0, 650, 128))
            bbox = raw_logo_area.getbbox()
            
            if bbox:
                exact_logo = raw_logo_area.crop(bbox)
                target_h = 44
                target_w = int(exact_logo.width * (target_h / float(exact_logo.height)))
                logo_resized = exact_logo.resize((target_w, target_h), Image.Resampling.LANCZOS)
                
                # ★左へ寄せて点線枠（x=112）の左端ラインにピッタリ合わせる (x: 75, y: 12)
                shifted_frame.paste(logo_resized, (75, 12), logo_resized)

            arr_frame = np.array(shifted_frame)
            if len(arr_frame.shape) == 3 and arr_frame.shape[2] == 4:
                rgb_part = arr_frame[:, :, :3]
                is_white = np.all(rgb_part >= 240, axis=2)
                arr_frame[is_white, 3] = 0
                processed_frame = Image.fromarray(arr_frame)
                composite_layer = Image.alpha_composite(text_layer, processed_frame)
            else:
                composite_layer = Image.alpha_composite(text_layer, shifted_frame)
        except Exception:
            pass

    return text_layer, composite_layer

def convert_to_pdf_bytes(pil_img):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    page_w, page_h = A4
    
    rgb_img = pil_img.convert('RGB')
    img_buffer = io.BytesIO()
    rgb_img.save(img_buffer, format="JPEG", quality=85)
    img_buffer.seek(0)
    
    c.drawImage(ImageReader(img_buffer), 0, 0, width=page_w, height=page_h)
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

        components.html("""
        <style>
        .br-btn {
            width: 100%;
            height: 32px;
            background-color: #334155;
            color: #FFFFFF;
            border-radius: 5px;
            border: none;
            font-size: 0.78rem;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 4px;
            transition: all 0.15s ease;
        }
        .br-btn:hover {
            background-color: #1E293B;
        }
        </style>
        <button class="br-btn" onclick="insertBrAtCursor()">↵ カーソル位置に &lt;改行&gt; を挿入</button>
        <script>
        function insertBrAtCursor() {
            const parentDoc = window.parent.document;
            const textarea = parentDoc.querySelector('div[data-testid="stTextArea"] textarea');
            if(!textarea) return;

            textarea.focus();
            if (parentDoc.queryCommandSupported && parentDoc.queryCommandSupported('insertText')) {
                parentDoc.execCommand('insertText', false, '<改行>');
            } else {
                const startPos = textarea.selectionStart;
                const endPos = textarea.selectionEnd;
                const val = textarea.value;
                textarea.value = val.substring(0, startPos) + "<改行>" + val.substring(endPos);
                textarea.selectionStart = textarea.selectionEnd = startPos + 4;
            }
            
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            textarea.dispatchEvent(new KeyboardEvent('keydown', {
                key: 'Enter', code: 'Enter', keyCode: 13, which: 13, ctrlKey: true, metaKey: true, bubbles: true, cancelable: true
            }));
        }
        </script>
        """, height=36)

        st.text_area(
            "テキスト編集", 
            key="input_textarea_key", 
            height=260, 
            label_visibility="collapsed"
        )

        with st.expander("詳細設定（タグ・改行・個別文字サイズ・枠画像）", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.text_input("タグ名", key="input_tag_key")
            with c2:
                st.text_input("フッター表記", key="input_footer_key")
            
            st.checkbox("自動改行（読みやすく2行に自動分割）を有効にする", key="input_auto_break_key")
            st.checkbox("通し番号（No.01, No.02...）をカード左上に表示する", key="input_show_number_key")
            
            st.markdown("<hr style='margin:0.6rem 0;'>", unsafe_allow_html=True)
            st.checkbox("カードごとに個別に文字サイズを調整する", key="input_use_custom_sizes")
            
            if st.session_state["input_use_custom_sizes"]:
                st.markdown("<p style='font-size:0.75rem; font-weight:600; color:#475569; margin-bottom:0.3rem;'>各枠の文字サイズ設定 (No.01〜No.10)</p>", unsafe_allow_html=True)
                size_cols1 = st.columns(2)
                size_cols2 = st.columns(2)
                size_cols3 = st.columns(2)
                size_cols4 = st.columns(2)
                size_cols5 = st.columns(2)
                all_cols = [
                    size_cols1[0], size_cols1[1],
                    size_cols2[0], size_cols2[1],
                    size_cols3[0], size_cols3[1],
                    size_cols4[0], size_cols4[1],
                    size_cols5[0], size_cols5[1]
                ]
                for idx in range(10):
                    with all_cols[idx]:
                        st.slider(f"No.{idx+1:02d} サイズ", min_value=30, max_value=80, value=DEFAULT_FONT_SIZE, step=2, key=f"custom_font_size_{idx}")
            else:
                st.slider("全体の文字サイズ", min_value=30, max_value=80, value=DEFAULT_FONT_SIZE, step=2, key="input_font_size_key")
            
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
                    
                    custom_sizes_data = None
                    if st.session_state["input_use_custom_sizes"]:
                        custom_sizes_data = [st.session_state[f"custom_font_size_{i}"] for i in range(10)]

                    new_item = {
                        "id": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                        "title": save_title.strip(),
                        "date": now_str,
                        "tag": st.session_state["input_tag_key"],
                        "footer": st.session_state["input_footer_key"],
                        "text": st.session_state["input_textarea_key"],
                        "font_size": st.session_state["input_font_size_key"],
                        "show_number": st.session_state["input_show_number_key"],
                        "auto_break": st.session_state["input_auto_break_key"],
                        "custom_sizes": custom_sizes_data
                    }
                    memories.insert(0, new_item)
                    save_memories(memories)
                    st.success(f"『{save_title}』を記憶しました！")
                else:
                    st.warning("題名を入力してください")

    with tab_memory:
        memories = load_memories()
        
        with st.expander("⚙️ 記憶データのバックアップと復元", expanded=False):
            st.markdown("<p style='font-size:0.75rem; color:#64748B;'>※定期的なバックアップを推奨します。</p>", unsafe_allow_html=True)
            b1, b2 = st.columns(2)
            with b1:
                json_string = json.dumps(memories, ensure_ascii=False, indent=2)
                st.download_button(
                    label="📥 バックアップを保存",
                    data=json_string,
                    file_name="turn_card_backup.json",
                    mime="application/json"
                )
            with b2:
                uploaded_backup = st.file_uploader("復元ファイルを選択", type=["json"], label_visibility="collapsed")
                if uploaded_backup is not None:
                    try:
                        restored_memories = json.load(uploaded_backup)
                        if isinstance(restored_memories, list):
                            save_memories(restored_memories)
                            st.success("記憶データを復元しました！画面を更新してください。")
                    except Exception:
                        st.error("正しいバックアップファイルではありません。")

        st.markdown('<div class="section-label" style="margin-top: 0.8rem;">保存された記憶一覧</div>', unsafe_allow_html=True)
        
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

active_custom_sizes = None
if st.session_state["input_use_custom_sizes"]:
    active_custom_sizes = [st.session_state[f"custom_font_size_{i}"] for i in range(10)]

text_only_img, frame_overlaid_img = generate_card_layers(
    card_lines, 
    st.session_state["input_tag_key"], 
    st.session_state["input_footer_key"], 
    frame_img_data,
    st.session_state["input_font_size_key"],
    active_custom_sizes,
    st.session_state["input_show_number_key"],
    st.session_state["input_auto_break_key"]
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
    st.markdown("<br>", unsafe_allow_html=True)
    pdf_data = convert_to_pdf_bytes(display_img)
    b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
    
    btn_col1, btn_col2 = st.columns([1, 1])
    
    with btn_col1:
        st.download_button(
            label="💾 PDFを保存する",
            data=pdf_data,
            file_name="card_print_final.pdf",
            mime="application/pdf"
        )
        
    with btn_col2:
        print_html = f"""
        <style>
        .print-btn {{
            width: 100%;
            height: 36px;
            background-color: #2563EB;
            color: #FFFFFF;
            border-radius: 6px;
            border: none;
            font-size: 0.82rem;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 1px 3px rgba(37, 99, 235, 0.15);
            transition: all 0.15s ease;
        }}
        .print-btn:hover {{
            background-color: #1D4ED8;
        }}
        </style>
        <button class="print-btn" onclick="openAndPrintPDF()">🖨️ そのまま印刷する</button>
        <script>
        function openAndPrintPDF() {{
            const pdfDataUrl = "data:application/pdf;base64,{b64_pdf}";
            const newWindow = window.open();
            newWindow.document.write(`
                <html>
                <head>
                    <title>カード印刷プレビュー</title>
                    <style>
                        body {{ margin: 0; padding: 0; background-color: #525659; display: flex; justify-content: center; align-items: center; height: 100vh; }}
                        embed {{ width: 100%; height: 100%; }}
                    </style>
                </head>
                <body>
                    <embed src="${{pdfDataUrl}}" type="application/pdf">
                </body>
                </html>
            `);
            newWindow.document.close();
            setTimeout(() => {{
                newWindow.print();
            }}, 1000);
        }}
        </script>
        """
        components.html(print_html, height=40)
                            
