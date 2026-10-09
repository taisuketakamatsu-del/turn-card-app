import os
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
# Streamlit Cloud 上ではPCのフォルダに保存できない
IS_CLOUD = os.path.exists("/mount/src")


def base_opts(cookie_path):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
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


def download_mp3(url, out_dir, bitrate, embed_thumb, cookie_path):
    """1曲をダウンロードしてMP3に変換し、ファイルパスを返す"""
    work_dir = tempfile.mkdtemp(dir=out_dir)
    postprocessors = [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": str(bitrate)},
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
    mp3s = glob.glob(os.path.join(work_dir, "*.mp3"))
    if not mp3s:
        raise RuntimeError("MP3ファイルが生成されませんでした")
    return mp3s[0]


def unique_name(name, used):
    stem, ext = os.path.splitext(name)
    candidate, n = name, 2
    while candidate in used:
        candidate = f"{stem} ({n}){ext}"
        n += 1
    used.add(candidate)
    return candidate


# ---------------- UI ----------------
st.title("🎵 YouTube 再生リスト → MP3")
st.caption("自分の動画（限定公開を含む）や、ダウンロードが許可されているコンテンツにのみ使用してください。")

urls_text = st.text_area(
    "再生リスト / 動画のURL（1行に1つ、いくつでも追加できます）",
    height=120,
    placeholder="https://youtube.com/playlist?list=...\nhttps://youtube.com/playlist?list=...",
)

col1, col2, col3 = st.columns(3)
with col1:
    bitrate = st.selectbox("音質 (kbps)", [128, 192, 256, 320], index=1)
with col2:
    limit = st.number_input("1リストの最大曲数", min_value=1, max_value=MAX_TRACKS, value=50)
with col3:
    embed_thumb = st.checkbox("サムネをジャケットに", value=True)

save_dir = ""
if not IS_CLOUD:
    save_dir = st.text_input("保存先フォルダ（空欄ならZIPダウンロードのみ）", value=os.path.join(os.path.expanduser("~"), "Music", "YouTube"))

with st.expander("詳細設定（ボット確認エラーが出る場合）"):
    st.caption("「Sign in to confirm you're not a bot」と出る場合、ブラウザから書き出した cookies.txt をアップロードすると通ることがあります。ファイルは処理後すぐ削除されます。")
    cookie_file = st.file_uploader("cookies.txt", type=["txt"])

if st.button("MP3に変換", type="primary", use_container_width=True):
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
                failed.append((url, str(e)))
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
            path = download_mp3(track["url"], out_dir, bitrate, embed_thumb, cookie_path)
            files.append(path)
            if save_dir:
                shutil.copy2(path, os.path.join(save_dir, os.path.basename(path)))
                saved += 1
        except Exception as e:
            failed.append((track["title"], str(e)))
    progress.progress(1.0, text="完了")

    if cookie_path and os.path.exists(cookie_path):
        os.remove(cookie_path)

    zip_path = None
    if files:
        zip_path = os.path.join(out_dir, "mp3.zip")
        used = set()
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as zf:
            for path in files:
                zf.write(path, unique_name(os.path.basename(path), used))

    st.session_state["result"] = {"dir": out_dir, "zip": zip_path, "files": files, "failed": failed, "saved": saved, "save_dir": save_dir}

# ---------------- 結果 ----------------
result = st.session_state.get("result")
if result:
    if result["files"]:
        st.success(f"{len(result['files'])}曲をMP3に変換しました")
        if result["saved"]:
            st.info(f"📁 {result['saved']}曲を保存しました：{result['save_dir']}")
        zip_path = result["zip"]
        st.download_button(
            "📦 まとめてダウンロード (ZIP)",
            data=lambda: open(zip_path, "rb").read(),
            file_name="mp3.zip",
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
                    mime="audio/mpeg",
                    key=f"dl_{i}",
                )
    if result["failed"]:
        with st.expander(f"⚠️ 失敗 {len(result['failed'])}件"):
            for name, err in result["failed"]:
                st.write(f"**{name}**")
                st.code(err[:500])
