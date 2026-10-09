import os
import re
import time
import subprocess
import sys
import glob
import shutil
import zipfile
import tempfile
import streamlit as st
import imageio_ffmpeg
from yt_dlp import YoutubeDL

try:
    import deno
    DENO_PATH = deno.find_deno_bin()
except Exception:
    DENO_PATH = None

st.set_page_config(page_title="YouTube → MP3", layout="centered")

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
MAX_TRACKS = 200
URLS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "urls.txt")
# Streamlit Cloud 上ではPCのフォルダに保存できない
IS_CLOUD = os.path.exists("/mount/src")


def base_opts(cookie_path):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "retries": 5,
        "fragment_retries": 5,
        "extractor_retries": 3,
        "ffmpeg_location": FFMPEG_PATH,
        "windowsfilenames": True,
    }
    if DENO_PATH:
        opts["js_runtimes"] = {"deno": {"path": DENO_PATH}}
    if cookie_path:
        opts["cookiefile"] = cookie_path
    return opts


def fetch_tracks(url, limit, cookie_path):
    """再生リスト（または単体動画）から曲のURLとタイトル一覧を取得"""
    opts = base_opts(cookie_path) | {"extract_flat": "in_playlist", "playlistend": limit}
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = info.get("entries")
    if entries is None:
        return info.get("title", url), [{"url": info.get("webpage_url", url), "title": info.get("title", url)}]
    tracks = []
    for e in entries:
        if not e:
            continue
        tracks.append({"url": e.get("url") or e.get("webpage_url"), "title": e.get("title") or e.get("id")})
    return info.get("title", url), tracks


def download_audio(url, out_dir, fmt, bitrate, embed_thumb, cookie_path):
    """1曲をダウンロードしてMP3/WAVに変換し、ファイルパスを返す"""
    embed_thumb = embed_thumb and fmt == "mp3"  # WAVはジャケット非対応
    work_dir = tempfile.mkdtemp(dir=out_dir)
    postprocessors = [
        {"key": "FFmpegExtractAudio", "preferredcodec": fmt, "preferredquality": str(bitrate)},
        {"key": "FFmpegMetadata", "add_metadata": True},
    ]
    if embed_thumb:
        postprocessors.append({"key": "EmbedThumbnail"})
    opts = base_opts(cookie_path) | {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(work_dir, "%(title)s.%(ext)s"),
        "noplaylist": True,
        "writethumbnail": embed_thumb,
        "postprocessors": postprocessors,
    }
    with YoutubeDL(opts) as ydl:
        ydl.download([url])
    outs = glob.glob(os.path.join(work_dir, f"*.{fmt}"))
    if not outs:
        raise RuntimeError(f"{fmt.upper()}ファイルが生成されませんでした")
    return outs[0]


def download_with_retry(url, out_dir, fmt, bitrate, embed_thumb, cookie_path, attempts=3):
    """一時的なエラー（403など）に備えて、間をあけて再試行する"""
    for n in range(attempts):
        try:
            return download_audio(url, out_dir, fmt, bitrate, embed_thumb, cookie_path)
        except Exception:
            if n == attempts - 1:
                raise
            time.sleep(5 * (n + 1))


def explain_error(err):
    err = re.sub(r"\x1b\[[0-9;]*m|\[[0-9;]*m", "", str(err))
    if "403" in err:
        err += "\n→ YouTubeに拒否されました。時間をおいて再試行するか、詳細設定から cookies.txt を使うと通ることがあります。"
    elif "Sign in to confirm" in err:
        err += "\n→ ボット確認です。詳細設定から cookies.txt をアップロードしてください。"
    return err


def notify(message):
    """Macの通知センターに完了を知らせる（Mac以外では何もしない）"""
    if sys.platform != "darwin":
        return
    script = f'display notification "{message}" with title "YouTube → MP3" sound name "Glass"'
    try:
        subprocess.run(["osascript", "-e", script], timeout=10)
    except Exception:
        pass


def unique_name(name, used):
    stem, ext = os.path.splitext(name)
    candidate, n = name, 2
    while candidate in used:
        candidate = f"{stem} ({n}){ext}"
        n += 1
    used.add(candidate)
    return candidate


def load_urls():
    try:
        with open(URLS_FILE, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def on_urls_change():
    # URLを保存して、自動で変換を開始する
    try:
        with open(URLS_FILE, "w", encoding="utf-8") as f:
            f.write(st.session_state["urls"])
    except OSError:
        pass
    st.session_state["auto_run"] = True


# ---------------- UI ----------------
st.title("🎵 YouTube 再生リスト → MP3 / WAV")
st.caption("自分の動画（限定公開を含む）や、ダウンロードが許可されているコンテンツにのみ使用してください。")

if "urls" not in st.session_state:
    st.session_state["urls"] = load_urls()
urls_text = st.text_area(
    "再生リスト / 動画のURL（1行に1つ。入力すると自動で保存・変換が始まります）",
    key="urls",
    on_change=on_urls_change,
    height=120,
    placeholder="https://youtube.com/playlist?list=...\nhttps://youtube.com/playlist?list=...",
)

col0, col1, col2, col3 = st.columns(4)
with col0:
    fmt = st.selectbox("形式", ["mp3", "wav"], format_func=str.upper)
with col1:
    bitrate = st.selectbox("音質 (kbps)", [128, 192, 256, 320], index=1, disabled=fmt == "wav")
with col2:
    limit = st.number_input("1リストの最大曲数", min_value=1, max_value=MAX_TRACKS, value=50)
with col3:
    embed_thumb = st.checkbox("サムネをジャケットに", value=True, disabled=fmt == "wav")

save_dir = ""
if not IS_CLOUD:
    save_dir = st.text_input("保存先フォルダ（空欄ならZIPダウンロードのみ）", value=os.path.join(os.path.expanduser("~"), "Music", "YouTube"))

with st.expander("詳細設定（ボット確認エラーが出る場合）"):
    st.caption("「Sign in to confirm you're not a bot」と出る場合、ブラウザから書き出した cookies.txt をアップロードすると通ることがあります。ファイルは処理後すぐ削除されます。")
    cookie_file = st.file_uploader("cookies.txt", type=["txt"])

clicked = st.button("もう一度変換する", use_container_width=True)
if clicked or st.session_state.pop("auto_run", False):
    urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
    if not urls:
        st.warning("URLを入力してください")
        st.stop()

    # 前回の結果を削除
    old = st.session_state.pop("result", None)
    if old:
        shutil.rmtree(old["dir"], ignore_errors=True)

    out_dir = tempfile.mkdtemp(prefix="ytmp3_")
    cookie_path = None
    if cookie_file:
        cookie_path = os.path.join(out_dir, "cookies.txt")
        with open(cookie_path, "wb") as f:
            f.write(cookie_file.getvalue())

    # 曲リスト取得
    all_tracks, failed = [], []
    with st.status("曲リストを取得中...") as status:
        for url in urls:
            try:
                title, tracks = fetch_tracks(url, int(limit), cookie_path)
                st.write(f"📃 {title}：{len(tracks)}曲")
                all_tracks.extend(tracks)
            except Exception as e:
                failed.append((url, explain_error(e)))
                st.write(f"❌ {url}")
        status.update(label=f"{len(all_tracks)}曲見つかりました", state="complete")

    # ダウンロード＆変換
    files = []
    saved = 0
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
    progress = st.progress(0.0)
    for i, track in enumerate(all_tracks):
        progress.progress(i / max(len(all_tracks), 1), text=f"({i + 1}/{len(all_tracks)}) {track['title']}")
        try:
            path = download_with_retry(track["url"], out_dir, fmt, bitrate, embed_thumb, cookie_path)
            files.append(path)
            if save_dir:
                shutil.copy2(path, os.path.join(save_dir, os.path.basename(path)))
                saved += 1
        except Exception as e:
            failed.append((track["title"], explain_error(e)))
    progress.progress(1.0, text="完了")
    msg = f"{len(files)}曲のダウンロード準備ができました"
    if failed:
        msg += f"（失敗 {len(failed)}件）"
    notify(msg)

    if cookie_path and os.path.exists(cookie_path):
        os.remove(cookie_path)

    zip_path = None
    if files:
        zip_path = os.path.join(out_dir, f"{fmt}.zip")
        used = set()
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            for path in files:
                zf.write(path, unique_name(os.path.basename(path), used))

    st.session_state["result"] = {"dir": out_dir, "zip": zip_path, "files": files, "failed": failed, "fmt": fmt, "saved": saved, "save_dir": save_dir}

# ---------------- 結果 ----------------
result = st.session_state.get("result")
if result:
    if result["files"]:
        st.success(f"{len(result['files'])}曲を{result['fmt'].upper()}に変換しました")
        if result["saved"]:
            st.info(f"📁 {result['saved']}曲を保存しました：{result['save_dir']}")
        zip_path = result["zip"]
        st.download_button(
            "📦 まとめてダウンロード (ZIP)",
            data=lambda: open(zip_path, "rb").read(),
            file_name=f"{result['fmt']}.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True,
        )
        with st.expander("1曲ずつダウンロード"):
            for i, path in enumerate(result["files"]):
                st.download_button(
                    os.path.basename(path),
                    data=lambda p=path: open(p, "rb").read(),
                    file_name=os.path.basename(path),
                    mime="audio/mpeg" if result["fmt"] == "mp3" else "audio/wav",
                    key=f"dl_{i}",
                )
    if result["failed"]:
        with st.expander(f"⚠️ 失敗 {len(result['failed'])}件"):
            for name, err in result["failed"]:
                st.write(f"**{name}**")
                st.code(err[:500])
