import asyncio
import io
import os
import re
import subprocess
import tempfile
import zipfile
import streamlit as st
import edge_tts
import google.generativeai as old_genai
from google import genai
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from youtube_transcript_api import YouTubeTranscriptApi
from moviepy.editor import VideoFileClip
from docx import Document
import pypdf

# ==========================================
# STREAMLIT PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="AI Creator & Video Tool Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Dark Modern Theme Styling
st.markdown(
    """
    <style>
    .stApp { background-color: #0d0f17; color: #ffffff; }
    .tool-card {
        background-color: #161b26;
        border: 1px solid #232a3b;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .tool-info { display: flex; align-items: center; gap: 16px; }
    .tool-icon {
        width: 44px; height: 44px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center; font-size: 20px;
    }
    .tool-title { font-size: 16px; font-weight: 600; color: #ffffff; margin: 0; }
    .tool-desc { font-size: 12px; color: #8b949e; margin: 2px 0 0 0; }
    .section-title { font-size: 14px; font-weight: 600; color: #6e7681; margin: 20px 0 10px 0; text-transform: uppercase; }
    .stButton>button { border-radius: 8px; height: 2.8em; font-weight: 600; }
    </style>
""",
    unsafe_allow_html=True,
)

# Session State for Page Navigation
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "🏠 Home Dashboard"

def navigate_to(page_name):
    st.session_state["current_page"] = page_name

# Sidebar Navigation Setup
st.sidebar.title("⚡ AI Creator Suite")
menu_options = [
    "🏠 Home Dashboard",
    "🎙️ Unlimited Voice & SRT Generator",
    "⚡ One Click Recap",
    "🎬 YouTube Video Recap",
    "🖼️ Thumbnail & Poster Maker",
    "⚡ Fast FFmpeg Video Splitter",
    "✂️ Text Splitter / Chunker",
    "🎥 Basic Video Editor",
    "🌐 Translate Content",
]

selected_tool = st.sidebar.radio(
    "Select Tool:",
    menu_options,
    index=menu_options.index(st.session_state["current_page"]) if st.session_state["current_page"] in menu_options else 0,
)

st.session_state["current_page"] = selected_tool
st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Mobile ဖုန်းတွင် ဘယ်ဘက်အပေါ်မှ ☰ ကိုနှိပ်၍ Menu ကို ဖွင့်/ပိတ် ပြုလုပ်နိုင်ပါသည်။")


# ==========================================
# 🏠 HOME DASHBOARD UI
# ==========================================
if st.session_state["current_page"] == "🏠 Home Dashboard":
    st.title("⚡ AI Creator & Video Tool Hub")
    st.caption("Select a tool below or use the sidebar menu to get started.")

    st.markdown('<div class="section-title">AI Content & Audio Tools</div>', unsafe_allow_html=True)

    tools_list = [
        ("🎙️ Unlimited Voice & SRT Generator", "Convert script to audio (.mp3) & .srt subtitles", "#064e3b", "#10b981", "🎙️"),
        ("⚡ One Click Recap", "Instantly recap any movie or script", "#2e1065", "#a855f7", "⚡"),
        ("🎬 YouTube Video Recap", "Generate recap script & voice from YouTube URL", "#1e1b4b", "#6366f1", "🎬"),
        ("🖼️ Thumbnail & Poster Maker", "Create multi-layer poster compositions", "#831843", "#f43f5e", "🖼️"),
        ("🌐 Translate Content", "Translate scripts to Burmese or English", "#312e81", "#818cf8", "🌐"),
    ]

    for title, desc, bg_color, text_color, icon in tools_list:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"""<div class="tool-card"><div class="tool-info">
                <div class="tool-icon" style="background-color: {bg_color}; color: {text_color};">{icon}</div>
                <div><p class="tool-title">{title}</p><p class="tool-desc">{desc}</p></div>
                </div></div>""",
                unsafe_allow_html=True,
            )
        with col2:
            if st.button("Launch", key=f"btn_{title}"):
                navigate_to(title)
                st.rerun()

    st.markdown('<div class="section-title">Video & Text Processing Tools</div>', unsafe_allow_html=True)

    video_tools = [
        ("⚡ Fast FFmpeg Video Splitter", "Split videos up to 1GB in seconds", "#451a03", "#f97316", "⚡"),
        ("✂️ Text Splitter / Chunker", "Split long scripts or docs by lines/characters", "#0f766e", "#14b8a6", "✂️"),
        ("🎥 Basic Video Editor", "Trim and crop video clips quickly", "#1e3a8a", "#3b82f6", "🎥"),
    ]

    for title, desc, bg_color, text_color, icon in video_tools:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"""<div class="tool-card"><div class="tool-info">
                <div class="tool-icon" style="background-color: {bg_color}; color: {text_color};">{icon}</div>
                <div><p class="tool-title">{title}</p><p class="tool-desc">{desc}</p></div>
                </div></div>""",
                unsafe_allow_html=True,
            )
        with col2:
            if st.button("Launch", key=f"btn_{title}"):
                navigate_to(title)
                st.rerun()


# ==========================================
# 🎙️ UNLIMITED VOICE & SRT GENERATOR
# ==========================================
elif st.session_state["current_page"] == "🎙️ Unlimited Voice & SRT Generator":
    st.title("🎙️ Unlimited Voice & SRT Generator")
    st.write("Movie Recap Script များကို စာလုံးရေ အကန့်အသတ်မရှိ Audio (.mp3) နှင့် Subtitle (.srt) သို့ ပြောင်းလဲပေးသည့် Tool")

    script_text = st.text_area("Recap Script စာသားများကို ဒီမှာ Paste လုပ်ပါ:", height=250)

    voice_option = st.selectbox(
        "အသံအမျိုးအစား ရွေးပါ:",
        [
            ("မြန်မာ - Nilar (Female)", "my-MM-NilarNeural"),
            ("မြန်မာ - Thiha (Male)", "my-MM-ThihaNeural"),
            ("English - Christopher (Male)", "en-US-ChristopherNeural"),
            ("English - Ava (Female)", "en-US-AvaNeural")
        ],
        format_func=lambda x: x[0]
    )

    def text_to_srt(text):
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        srt_content = ""
        start_time = 0
        
        for i, line in enumerate(lines, 1):
            duration = max(2, len(line) * 0.25)
            end_time = start_time + duration
            
            def format_time(seconds):
                hrs = int(seconds // 3600)
                mins = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                msecs = int((seconds - int(seconds)) * 1000)
                return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"
            
            srt_content += f"{i}\n"
            srt_content += f"{format_time(start_time)} --> {format_time(end_time)}\n"
            srt_content += f"{line}\n\n"
            start_time = end_time
            
        return srt_content

    async def generate_audio_file(text, voice_code):
        communicate = edge_tts.Communicate(text, voice_code)
        await communicate.save("output_voice.mp3")

    if st.button("🚀 Audio နှင့် SRT ထုတ်ယူမည်", type="primary"):
        if script_text.strip():
            with st.spinner("Audio နှင့် Subtitle များ ဖန်တီးနေပါသည်။ ခဏစောင့်ပါ..."):
                voice_code = voice_option[1]
                asyncio.run(generate_audio_file(script_text, voice_code))
                srt_data = text_to_srt(script_text)
                
                st.success("✨ ဖန်တီးမှု အောင်မြင်ပါသည်။")
                
                with open("output_voice.mp3", "rb") as f:
                    audio_bytes = f.read()
                st.audio(audio_bytes, format="audio/mp3")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download Audio (.mp3)",
                        data=audio_bytes,
                        file_name="recap_voice.mp3",
                        mime="audio/mp3"
                    )
                with col2:
                    st.download_button(
                        label="📥 Download Subtitle (.srt)",
                        data=srt_data,
                        file_name="recap_subtitles.srt",
                        mime="text/plain"
                    )
        else:
            st.error("ကျေးဇူးပြု၍ Script စာသား ထည့်သွင်းပါ။")


# ==========================================
# ⚡ ONE CLICK RECAP FUNCTION
# ==========================================
elif st.session_state["current_page"] == "⚡ One Click Recap":
    st.subheader("⚡ One Click Movie/Anime Recap Generator")

    api_key = st.text_input("Gemini API Key ထည့်ပါ:", type="password")
    raw_story = st.text_area("ဇာတ်လမ်း အကျဉ်း သို့မဟုတ် Plot Detail များ ထည့်ပါ:", height=200)

    if st.button("🚀 Generate Recap Script", type="primary"):
        if api_key and raw_story:
            try:
                old_genai.configure(api_key=api_key)
                model = old_genai.GenerativeModel("gemini-1.5-flash")
                prompt = (
                    "You are a professional movie recap creator. Write an engaging"
                    " movie recap script in Burmese language based on the following"
                    f" text:\n{raw_story}"
                )

                with st.spinner("AI Script ရေးသားနေပါသည်..."):
                    response = model.generate_content(prompt)
                    st.success("✨ Script ရရှိပါပြီ!")
                    st.text_area("Generated Recap Script:", response.text, height=250)
            except Exception as e:
                st.error(f"Error occurred: {e}")
        else:
            st.warning("API Key နှင့် Plot စာသား ဖြည့်သွင်းပေးပါ။")


# ==========================================
# 🎬 YOUTUBE VIDEO RECAP GENERATOR
# ==========================================
elif st.session_state["current_page"] == "🎬 YouTube Video Recap":
    st.title("🎬 YouTube to MM Voice Recap Generator")
    st.write("YouTube Link ထည့်လိုက်ရုံဖြင့် မြန်မာ Recap Script နှင့် AI Voiceover ဖိုင်ကို ထုတ်ပေးမည်ဖြစ်ပါသည်။")

    api_key = st.text_input("Google Gemini API Key ထည့်ပါ:", type="password")

    def get_video_id(url):
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
        return match.group(1) if match else None

    def get_youtube_transcript(video_id):
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "my", "ja"])
            return " ".join([item["text"] for item in transcript_list])
        except Exception as e:
            return f"Error: Transcript ဆွဲထုတ်၍ မရပါ ({str(e)})"

    def generate_recap_script(client, transcript):
        prompt = f"""
        Below is a transcript of a video. Please write an engaging, exciting Movie/Anime Recap script in Burmese language based on this transcript.
        Keep the tone entertaining, clear, and ready for a video recap voiceover.
        
        Transcript:
        {transcript}
        """
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text

    async def text_to_speech_myanmar(text, output_filename="recap_voice.mp3"):
        voice = "my-MM-NilarNeural"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_filename)

    youtube_url = st.text_input("YouTube Video Link ကို ဒီမှာ Paste လုပ်ပါ:")

    if st.button("Generate Recap & Voice", type="primary"):
        if not api_key:
            st.warning("ကျေးဇူးပြု၍ Gemini API Key ကို အရင်ထည့်သွင်းပေးပါ။")
        elif not youtube_url:
            st.warning("YouTube Link ထည့်သွင်းပေးပါ။")
        else:
            video_id = get_video_id(youtube_url)
            if video_id:
                try:
                    client = genai.Client(api_key=api_key)

                    st.info("၁။ YouTube မှ Transcript ဆွဲထုတ်နေပါသည်...")
                    raw_transcript = get_youtube_transcript(video_id)

                    if not raw_transcript.startswith("Error"):
                        st.info("၂။ Gemini AI ဖြင့် မြန်မာ Recap Script ရေးသားနေပါသည်...")
                        burmese_script = generate_recap_script(client, raw_transcript)

                        st.subheader("📝 ထွက်ရှိလာသော မြန်မာ Recap Script:")
                        st.text_area("Script", burmese_script, height=250)

                        st.info("၃။ AI မြန်မာ Voiceover (MP3) ပြောင်းလဲနေပါသည်...")
                        asyncio.run(text_to_speech_myanmar(burmese_script, "recap_voice.mp3"))

                        st.success("✅ အားလုံး ပြီးစီးပါပြီ!")
                        st.audio("recap_voice.mp3", format="audio/mp3")

                        with open("recap_voice.mp3", "rb") as file:
                            st.download_button(
                                label="⬇️ Audio (.mp3) ဒေါင်းလုဒ်ဆွဲရန်",
                                data=file,
                                file_name="recap_voice.mp3",
                                mime="audio/mp3",
                            )
                    else:
                        st.error(raw_transcript)
                except Exception as e:
                    st.error(f"အမှားအယွင်းရှိပါသည်: {str(e)}")
            else:
                st.error("မှန်ကန်သော YouTube URL မဟုတ်ပါ။")


# ==========================================
# 🖼️ THUMBNAIL & POSTER MAKER
# ==========================================
elif st.session_state["current_page"] == "🖼️ Thumbnail & Poster Maker":
    st.subheader("🖼️ Multi-layer Poster & Concept Art Compositor")

    col_inputs, col_preview = st.columns([1, 2])

    with col_inputs:
        bg_img = st.file_uploader("1. Background Image", type=["jpg", "png"])
        hero_img = st.file_uploader("2. Hero Person PNG (Transparent)", type=["png"])

        p_title = st.text_input("Title Text", "MAGIC POSTER")
        h_x = st.slider("Hero Position X", 0, 1000, 350)
        h_y = st.slider("Hero Position Y", 0, 1000, 100)
        h_scale = st.slider("Hero Scale (%)", 20, 200, 100)

    def draw_poster():
        cw, ch = 1280, 720
        canvas = (
            Image.open(bg_img).convert("RGBA").resize((cw, ch))
            if bg_img
            else Image.new("RGBA", (cw, ch), (20, 10, 35, 255))
        )

        if hero_img:
            h_pic = Image.open(hero_img).convert("RGBA")
            ow, oh = h_pic.size
            nw, nh = int(ow * (h_scale / 100.0)), int(oh * (h_scale / 100.0))
            canvas.paste(
                h_pic.resize((nw, nh)), (h_x, h_y), h_pic.resize((nw, nh))
            )

        draw = ImageDraw.Draw(canvas)
        draw.rectangle(
            [(50, 40), (500, 120)],
            fill=(15, 10, 25, 220),
            outline=(212, 175, 55),
            width=3,
        )
        draw.text((70, 60), p_title, fill=(255, 215, 0))
        return canvas

    with col_preview:
        poster = draw_poster()
        buf = io.BytesIO()
        poster.convert("RGB").save(buf, format="JPEG", quality=95)
        st.image(buf.getvalue(), use_container_width=True)
        st.download_button("📥 Download Poster", buf.getvalue(), "poster.jpg", "image/jpeg")


# ==========================================
# ⚡ FAST FFMPEG VIDEO SPLITTER
# ==========================================
elif st.session_state["current_page"] == "⚡ Fast FFmpeg Video Splitter":
    st.title("⚡ Ultra-Fast Video Splitter (Up to 1GB)")
    st.write("Video Upload တင်ပြီး Re-encode မလုပ်ဘဲ FFmpeg ဖြင့် စက္ကန့်ပိုင်းအတွင်း ခွဲထုတ်ပေးပါမည်။")

    def get_video_duration(input_path):
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return float(result.stdout.strip())

    def fast_ffmpeg_split(input_path, start_time, duration, output_path):
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", input_path,
            "-t", str(duration),
            "-c", "copy",
            "-avoid_negative_ts", "1",
            output_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if "zip_bytes" not in st.session_state:
        st.session_state.zip_bytes = None
    if "split_done" not in st.session_state:
        st.session_state.split_done = False
    if "num_parts_done" not in st.session_state:
        st.session_state.num_parts_done = 0

    uploaded_file = st.file_uploader("Video ဖိုင် ရွေးချယ်ပါ (Max 1GB)", type=["mp4", "mov", "avi", "mkv"])

    if uploaded_file is not None:
        if "last_filename" not in st.session_state or st.session_state.last_filename != uploaded_file.name:
            st.session_state.zip_bytes = None
            st.session_state.split_done = False
            st.session_state.last_filename = uploaded_file.name

        temp_dir = tempfile.mkdtemp()
        tfile_path = os.path.join(temp_dir, "uploaded_video.mp4")

        if not os.path.exists(tfile_path):
            with st.spinner("Video ဖိုင်ကို Upload တင်နေပါသည်..."):
                with open(tfile_path, "wb") as f:
                    while True:
                        chunk = uploaded_file.read(5 * 1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)

        try:
            total_duration = get_video_duration(tfile_path)

            st.subheader("📹 မူရင်း Video အချက်အလက်")
            mins, secs = divmod(int(total_duration), 60)
            st.info(f"⏱️ စုစုပေါင်း ကြာချိန်: **{mins} မိနစ် {secs} စက္ကန့်** ({total_duration:.2f} စက္ကန့်)")

            st.markdown("---")
            st.subheader("⚙️ အပိုင်း ခွဲခြားမှု သတ်မှတ်ရန်")

            split_mode = st.radio(
                "ဘယ်လို အပိုင်းခွဲချင်ပါသလဲ?",
                ["၁၀ ပိုင်း ခွဲမည်", "အပိုင်း ၂၀ ခွဲမည်", "စိတ်ကြိုက် အပိုင်း အရေအတွက် သတ်မှတ်မည်"],
                horizontal=True
            )

            if split_mode == "၁၀ ပိုင်း ခွဲမည်":
                num_parts = 10
            elif split_mode == "အပိုင်း ၂၀ ခွဲမည်":
                num_parts = 20
            else:
                num_parts = st.number_input("ခွဲချင်သည့် အပိုင်း အရေအတွက် ရိုက်ထည့်ပါ:", min_value=2, max_value=100, value=5, step=1)

            part_duration = total_duration / num_parts
            p_mins, p_secs = divmod(int(part_duration), 60)

            st.success(f"💡 အပိုင်း **{num_parts}** ပိုင်း ခွဲပါမည်။ (တစ်ပိုင်းလျှင် **{p_mins} မိနစ် {p_secs} စက္ကန့် / {part_duration:.2f} စက္ကန့်** ကျရောက်ပါမည်)")

            if st.button("🚀 FFmpeg ဖြင့် အမြန်ဆုံး ဖြတ်မည်", type="primary"):
                output_files = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i in range(num_parts):
                    start_time = i * part_duration
                    dur = part_duration if i < num_parts - 1 else (total_duration - start_time)

                    status_text.text(f"⚡ Fast Splitting Part {i+1} of {num_parts}...")

                    out_filename = os.path.join(temp_dir, f"part_{i+1}.mp4")
                    fast_ffmpeg_split(tfile_path, start_time, dur, out_filename)
                    
                    output_files.append(out_filename)
                    progress_bar.progress((i + 1) / num_parts)

                status_text.text("✨ Cutting အောင်မြင်ပါပြီ! ZIP ဖိုင် ပြင်ဆင်နေပါသည်...")

                zip_path = os.path.join(temp_dir, "fast_split_videos.zip")
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for file in output_files:
                        zipf.write(file, os.path.basename(file))

                with open(zip_path, "rb") as f:
                    st.session_state.zip_bytes = f.read()
                
                st.session_state.split_done = True
                st.session_state.num_parts_done = num_parts

            if st.session_state.split_done and st.session_state.zip_bytes is not None:
                st.success(f"🎉 အပိုင်း **{st.session_state.num_parts_done}** ပိုင်းစလုံး အသင့်ဖြစ်ပါပြီ!")
                st.download_button(
                    label="📦 Cut ထားသော Video အားလုံးကို ZIP ဖိုင်ဖြင့် ဒေါင်းလုဒ်ဆွဲမည်",
                    data=st.session_state.zip_bytes,
                    file_name=f"fast_split_{st.session_state.num_parts_done}_parts.zip",
                    mime="application/zip"
                )

        except Exception as e:
            st.error(f"အမှားအယွင်း ဖြစ်ပေါ်ခဲ့သည်: {str(e)}")


# ==========================================
# ✂️ TEXT SPLITTER / CHUNKER
# ==========================================
elif st.session_state["current_page"] == "✂️ Text Splitter / Chunker":
    st.title("✂️ စာသားနှင့် File များကို အပိုင်းလိုက် ခွဲပေးသည့် Tool")

    if "stored_text" not in st.session_state:
        st.session_state.stored_text = ""
    if "chunks" not in st.session_state:
        st.session_state.chunks = []

    input_type = st.radio("စာသားထည့်သွင်းမည့် နည်းလမ်း ရွေးပါ -", ["Direct Text", "File Upload (.txt, .docx, .pdf)"], horizontal=True)

    if input_type == "Direct Text":
        user_input = st.text_area("ခွဲချင်သည့် စာသားများကို အောက်တွင် ထည့်ပါ -", value=st.session_state.stored_text, height=200)
        st.session_state.stored_text = user_input
    else:
        uploaded_file = st.file_uploader("File တင်ပါ", type=["txt", "docx", "pdf"])
        if uploaded_file is not None:
            if uploaded_file.name.endswith(".txt"):
                st.session_state.stored_text = uploaded_file.read().decode("utf-8")
            elif uploaded_file.name.endswith(".docx"):
                doc = Document(uploaded_file)
                st.session_state.stored_text = "\n".join([p.text for p in doc.paragraphs])
            elif uploaded_file.name.endswith(".pdf"):
                pdf_reader = pypdf.PdfReader(uploaded_file)
                pdf_text = ""
                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        pdf_text += extracted + "\n"
                st.session_state.stored_text = pdf_text

    if st.session_state.stored_text:
        st.info(f"📊 လက်ရှိထည့်သွင်းထားသော စာလုံးရေစုစုပေါင်း: **{len(st.session_state.stored_text)}** characters")

    st.subheader("⚙️ စာသား ခွဲမည့် နည်းလမ်း သတ်မှတ်ပါ")
    col1, col2 = st.columns(2)

    with col1:
        split_method = st.selectbox("ခွဲမည့် ပုံစံ:", ["စာလုံးရေ အလိုက် (By Characters)", "စာကြောင်းရေ အလိုက် (By Lines)"])

    with col2:
        if split_method == "စာလုံးရေ အလိုက် (By Characters)":
            chunk_size = st.number_input("Part တစ်ခုလျှင် ရှိရမည့် စာလုံးရေ:", min_value=100, max_value=50000, value=3000, step=500)
        else:
            chunk_size = st.number_input("Part တစ်ခုလျှင် ရှိရမည့် စာကြောင်းရေ:", min_value=1, max_value=5000, value=50, step=10)

    def split_by_chars(text, size):
        return [text[i:i+size] for i in range(0, len(text), size)]

    def split_by_lines(text, size):
        lines = text.split("\n")
        return ["\n".join(lines[i:i+size]) for i in range(0, len(lines), size)]

    if st.button("Split Text Now (စာသား အပိုင်းခွဲမည်)", type="primary"):
        current_text = st.session_state.stored_text.strip()
        if not current_text:
            st.warning("ကျေးဇူးပြု၍ စာသား သို့မဟုတ် File အရင်ထည့်ပါ။")
            st.session_state.chunks = []
        else:
            if split_method == "စာလုံးရေ အလိုက် (By Characters)":
                st.session_state.chunks = split_by_chars(current_text, chunk_size)
            else:
                st.session_state.chunks = split_by_lines(current_text, chunk_size)

    if st.session_state.chunks:
        st.success(f"စာသားများကို စုစုပေါင်း **{len(st.session_state.chunks)} အပိုင်း** ခွဲပေးလိုက်ပါပြီ။")
        st.markdown("---")
        
        for index, chunk in enumerate(st.session_state.chunks):
            with st.expander(f"📌 Part {index + 1} (စာလုံးရေ: {len(chunk)} characters)", expanded=True):
                st.text_area(f"Part {index + 1} Content:", value=chunk, height=150, key=f"chunk_{index}")
                st.download_button(
                    label=f"⬇️ Download Part {index + 1} (.txt)",
                    data=chunk,
                    file_name=f"part_{index + 1}.txt",
                    mime="text/plain",
                    key=f"dl_{index}"
                )


# ==========================================
# 🎥 BASIC VIDEO EDITOR
# ==========================================
elif st.session_state["current_page"] == "🎥 Basic Video Editor":
    st.title("🎥 Basic Video Editor (MoviePy)")
    st.write("ဖုန်းထဲမှ ဗီဒီယိုများကို ဖြတ်တောက် ရွေးချယ်နိုင်ပါသည်။")

    uploaded_video = st.file_uploader("ဗီဒီယိုဖိုင် တင်ပါ (MP4, MOV)", type=["mp4", "mov"])

    if uploaded_video is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_video.read())
        
        clip = VideoFileClip(tfile.name)
        duration = int(clip.duration)
        
        st.subheader("မူရင်း ဗီဒီယို")
        st.video(tfile.name)
        st.write(f"ဗီဒီယို ကြာမြင့်ချိန်: **{duration} စက္ကန့်**")

        st.divider()
        st.subheader("✂️ ဗီဒီယို ဖြတ်တောက်ရန် (Trimming)")
        
        start_time, end_time = st.slider(
            "စတင်မည့်ချိန် နှင့် ပြီးဆုံးမည့်ချိန် (စက္ကန့်) ကို ရွေးပါ",
            0, duration, (0, min(10, duration))
        )

        if st.button("🎬 ဗီဒီယို ဖြတ်မည်", type="primary"):
            with st.spinner("ဗီဒီယို Processing လုပ်နေပါသည်... ခဏစောင့်ပါ..."):
                edited_clip = clip.subclip(start_time, end_time)
                output_path = "output_edited.mp4"
                edited_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
                
                st.success("ဗီဒီယို ပြင်ဆင်ပြီးပါပြီ!")
                st.video(output_path)
                
                with open(output_path, "rb") as file:
                    st.download_button(
                        label="⬇️ ပြင်ဆင်ထားသော ဗီဒီယို ဒေါင်းလုဒ်ဆွဲရန်",
                        data=file,
                        file_name="edited_video.mp4",
                        mime="video/mp4"
                    )
                
                clip.close()
                edited_clip.close()


# ==========================================
# 🌐 TRANSLATE CONTENT FUNCTION
# ==========================================
elif st.session_state["current_page"] == "🌐 Translate Content":
    st.subheader("🌐 Translate Content")

    api_key_t = st.text_input("Gemini API Key:", type="password")
    src_text = st.text_area("ဘာသာပြန်လိုသော စာသားများ ရေးထည့်ပါ:", height=180)
    target_lang = st.selectbox("ပြန်ဆိုချင်သည့် ဘာသာစကား:", ["Burmese (မြန်မာ)", "English"])

    if st.button("🚀 Translate Text", type="primary"):
        if api_key_t and src_text:
            try:
                old_genai.configure(api_key=api_key_t)
                model = old_genai.GenerativeModel("gemini-1.5-flash")
                prompt = f"Translate the following content into {target_lang}:\n\n{src_text}"

                with st.spinner("Translating..."):
                    res = model.generate_content(prompt)
                    st.success("Translated Output:")
                    st.text_area("Result:", res.text, height=200)
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("API Key နှင့် စာသား ရေးပေးပါ။")
