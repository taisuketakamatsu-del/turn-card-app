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
    私は言語モデルですので、そちらに対応できるようには設計されていません。
