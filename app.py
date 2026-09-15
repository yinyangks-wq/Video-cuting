import streamlit as st
import ffmpeg
import yt_dlp
import tempfile
import os
import whisper
from datetime import timedelta

st.set_page_config(page_title="Video Cutter & Auto Subtitle", layout="centered")

st.title("🎬 Video Cutter & Auto Subtitle")
st.caption("Video ကို Fast Cut ပြုလုပ်ပြီး အသံမှ စာတမ်းထိုး (Transcript / SRT) ကို အလိုအလျောက် ထုတ်ပေးသည့် Tool")

# Whisper Model ကို Streamlit Cache ဖြင့် ခေါ်ယူခြင်း (RAM သက်သာစေရန် 'tiny' model ကို သုံးထားသည်)
@st.cache_resource
def load_whisper():
    return whisper.load_model("tiny")

with st.spinner("Whisper AI Model ကို စတင်ပြင်ဆင်နေပါသည်..."):
    model = load_whisper()

# Helper function: Whisper result မှ .srt ဖိုင် format သို့ ပြောင်းလဲပေးခြင်း
def create_srt(segments):
    srt_content = ""
    for i, seg in enumerate(segments, start=1):
        start_time = str(timedelta(seconds=int(seg['start']))) + f",{int((seg['start'] % 1) * 1000):03d}"
        end_time = str(timedelta(seconds=int(seg['end']))) + f",{int((seg['end'] % 1) * 1000):03d}"
        text = seg['text'].strip()
        
        srt_content += f"{i}\n0{start_time} --> 0{end_time}\n{text}\n\n"
    return srt_content

# Source ရွေးချယ်မှု
source_type = st.radio("Video ရယူမည့် နည်းလမ်း:", ("Video Link (YouTube/Web)", "Direct File Upload"))

video_path = None

if source_type == "Video Link (YouTube/Web)":
    url = st.text_input("Video URL Link ထည့်ပါ:")
    if url and st.button("Link မှ Video ရယူမည်"):
        with st.spinner("Video လင့်ခ်ကို ဒေါင်းလုဒ်ဆွဲနေပါသည်..."):
            try:
                # Format Error မတက်စေရန် Flexible အဖြစ်ဆုံး Option များကို သုံးထားပါသည်
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': tempfile.mktemp(suffix='.mp4'),
                    'quiet': True,
                    'no_warnings': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    st.session_state['downloaded_file'] = ydl.prepare_filename(info)
                st.success("Video ရရှိပါပြီ!")
            except Exception as e:
                st.error(f"Error: {e}")

    if 'downloaded_file' in st.session_state:
        video_path = st.session_state['downloaded_file']

else:
    uploaded_file = st.file_uploader("Video File Upload တင်ပါ", type=["mp4", "mov", "avi", "mkv"])
    if uploaded_file is not None:
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        video_path = tfile.name

# Video Process ပြုလုပ်သည့် အပိုင်း
if video_path and os.path.exists(video_path):
    st.markdown("---")
    st.subheader("✂️ ဖြတ်ထုတ်မည့် အချိန်သတ်မှတ်ပါ (HH:MM:SS)")

    col1, col2 = st.columns(2)
    with col1:
        st.write("**စတင်မည့်အချိန် (Start)**")
        h_s = st.number_input("Hour", 0, 24, 0, key="hs")
        m_s = st.number_input("Min", 0, 59, 0, key="ms")
        s_s = st.number_input("Sec", 0, 59, 0, key="ss")
    with col2:
        st.write("**ပြီးဆုံးမည့်အချိန် (End)**")
        h_e = st.number_input("Hour", 0, 24, 0, key="he")
        m_e = st.number_input("Min", 0, 59, 0, key="me")
        s_e = st.number_input("Sec", 0, 59, 10, key="se")

    start_sec = (h_s * 3600) + (m_s * 60) + s_s
    end_sec = (h_e * 3600) + (m_e * 60) + s_e

    st.markdown("---")
    generate_sub = st.checkbox("စာတမ်းထိုး (Auto Subtitle / Transcript) ထုတ်ယူမည်", value=True)

    if st.button("🚀 Process (Cut & Subtitle) လုပ်မည်", type="primary"):
        if start_sec >= end_sec:
            st.error("စတင်ချိန်သည် ပြီးဆုံးချိန်ထက် ငယ်ရပါမည်။")
        else:
            output_path = "cut_output.mp4"
            
            # 1. FFmpeg Fast Cut
            with st.spinner("Video ကို Cut နေပါသည်..."):
                try:
                    (
                        ffmpeg
                        .input(video_path, ss=start_sec, t=end_sec - start_sec)
                        .output(output_path, c='copy')
                        .overwrite_output()
                        .run(capture_stdout=True, capture_stderr=True)
                    )
                    st.success("Video Cut လို့ ပြီးပါပြီ!")
                    st.video(output_path)
                except Exception as e:
                    st.error(f"FFmpeg Error: {e}")

            # 2. Whisper AI Subtitle Generation
            if generate_sub and os.path.exists(output_path):
                with st.spinner("Whisper AI ဖြင့် အသံမှ စာသားပြောင်းလဲနေပါသည်..."):
                    try:
                        result = model.transcribe(output_path)
                        transcript_text = result["text"]
                        srt_data = create_srt(result["segments"])

                        st.subheader("📜 ထွက်ရှိလာသော စာတမ်းထိုးများ")
                        st.text_area("Transcript စာသား:", transcript_text, height=150)

                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            st.download_button(
                                label="📝 Subtitle (.srt) ဒေါင်းလုဒ်ဆွဲမည်",
                                data=srt_data,
                                file_name="subtitle.srt",
                                mime="text/plain"
                            )
                        with col_d2:
                            st.download_button(
                                label="📄 Plain Text (.txt) ဒေါင်းလုဒ်ဆွဲမည်",
                                data=transcript_text,
                                file_name="transcript.txt",
                                mime="text/plain"
                            )
                    except Exception as e:
                        st.error(f"Subtitle Generation Error: {e}")

            # 3. Video Download Button
            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Cut လုပ်ထားသော Video (.mp4) ဒေါင်းလုဒ်ဆွဲမည်",
                        data=f,
                        file_name="cut_video.mp4",
                        mime="video/mp4"
                    )
