import os
import sys
import subprocess
from dotenv import load_dotenv

# Nạp biến môi trường từ .env
load_dotenv()

# Kỹ thuật khởi động an toàn trên Windows: Khóa vòng lặp bằng biến môi trường
if os.environ.get("STREAMLIT_RUNNING") != "true":
    os.environ["STREAMLIT_RUNNING"] = "true"
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__], check=True)
    except Exception as e:
        print(f"Lỗi khởi động hệ thống DSS: {e}")
        input("Nhấn Enter để thoát...")
    sys.exit(0)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import json
import re
import logging

from ahp_engine import AHPEngine
from gemini_services import GeminiService

# Cấu hình trang
st.set_page_config(
    page_title="DSS - Chuyên gia Tu van IT",
    page_icon="https://cdn-icons-png.flaticon.com/512/3203/3203491.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# DESIGN SYSTEM: The Executive DSS — Ported from React prototype
st.markdown("""
<style>
    /* ═══ SYSTEM RESET ═══ */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* ═══ TYPOGRAPHY ═══ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #2e364b;
    }
    
    /* ═══ SURFACES ═══ */
    .stApp { background-color: #f7f9fb; }
    
    /* ═══ HERO BANNER ═══ */
    .hero-banner {
        background: linear-gradient(135deg, #1a2035 0%, #2e364b 55%, #1e3a38 100%);
        padding: 40px 48px 36px;
        border-radius: 20px;
        position: relative;
        overflow: hidden;
        margin-bottom: 32px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.22), 0 8px 24px rgba(0,62,56,0.15), inset 0 1px 0 rgba(255,255,255,0.05);
        border: 1px solid rgba(137,245,231,0.08);
        text-align: center;
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: -80px; right: -80px;
        width: 260px; height: 260px;
        background: radial-gradient(circle, rgba(137,245,231,0.07) 0%, transparent 65%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero-banner::after {
        content: '';
        position: absolute;
        bottom: -50px; left: -30px;
        width: 160px; height: 160px;
        background: radial-gradient(circle, rgba(0,62,56,0.12) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .hero-banner .hero-badge {
        display: inline-block;
        padding: 4px 16px;
        background: rgba(137,245,231,0.12);
        color: #89f5e7;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        border-radius: 20px;
        border: 1px solid rgba(137,245,231,0.15);
        margin-bottom: 16px;
    }
    .hero-banner .hero-title {
        font-size: 30px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin: 0 0 8px 0;
        position: relative;
        z-index: 1;
    }
    .hero-banner .hero-accent {
        display: inline-block;
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, #89f5e7, rgba(137,245,231,0.2));
        border-radius: 2px;
        margin: 12px auto 16px;
    }
    .hero-banner .hero-subtitle {
        font-size: 14px;
        font-weight: 400;
        color: rgba(221,226,239,0.85);
        letter-spacing: 0.02em;
        margin: 0;
        position: relative;
        z-index: 1;
    }
    .hero-banner .hero-subtitle strong {
        font-weight: 600;
        color: #89f5e7;
    }
    
    /* ═══ SECTION TITLE ═══ */
    .section-title {
        font-size: 20px;
        font-weight: 800;
        color: #1a2035;
        padding-bottom: 12px;
        margin-bottom: 24px;
        margin-top: 32px;
        letter-spacing: -0.02em;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .section-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, #3b82f6, transparent);
        opacity: 0.3;
    }
    
    /* ═══ MICRO LABEL (uppercase) ═══ */
    .micro-label {
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: #737784;
        margin-bottom: 4px;
    }
    
    /* ═══ KPI CARD (from KPICard.tsx) ═══ */
    .exec-kpi {
        background: #ffffff;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid rgba(195,198,213,0.08);
        box-shadow: 0px 4px 20px rgba(0,0,0,0.02);
        margin-bottom: 8px;
    }
    .exec-kpi .kpi-label {
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: #737784;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .exec-kpi .kpi-value {
        font-size: 28px;
        font-weight: 900;
        color: #2e364b;
        line-height: 1.1;
    }
    .exec-kpi .kpi-unit {
        font-size: 14px;
        font-weight: 500;
        color: #c3c6d5;
        margin-left: 2px;
    }
    .exec-kpi .kpi-trend {
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #003e38;
        margin-top: 8px;
    }
    
    /* ═══ AI SYNTHESIS CARD — nâng cấp bóng đổ Luxury ═══ */
    .exec-synthesis {
        background: linear-gradient(135deg, #1a2035 0%, #2e364b 60%, #1e3a38 100%);
        color: #ffffff;
        padding: 36px;
        border-radius: 20px;
        position: relative;
        overflow: hidden;
        margin-bottom: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.25), 0 8px 20px rgba(0,62,56,0.2), inset 0 1px 0 rgba(255,255,255,0.06);
        border: 1px solid rgba(137,245,231,0.1);
    }
    .exec-synthesis::before {
        content: '';
        position: absolute;
        top: -60px; right: -60px;
        width: 180px; height: 180px;
        background: radial-gradient(circle, rgba(137,245,231,0.06) 0%, transparent 70%);
        border-radius: 50%;
    }
    .exec-synthesis::after {
        content: '';
        position: absolute;
        bottom: -40px; left: -20px;
        width: 120px; height: 120px;
        background: radial-gradient(circle, rgba(0,62,56,0.15) 0%, transparent 70%);
        border-radius: 50%;
    }
    .exec-synthesis .synth-label {
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.25em;
        color: #89f5e7;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .exec-synthesis .synth-body {
        font-size: 15px;
        font-weight: 300;
        line-height: 1.8;
        color: #dde2ef;
    }
    .exec-synthesis .synth-body strong {
        font-weight: 700;
        color: #89f5e7;
    }

    /* ═══ COURSE CARD — viền xanh lá pastel ═══ */
    .course-enroll-card {
        background: #ffffff;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 12px;
        border-left: 4px solid rgba(34,197,94,0.5);
        border-top: 1px solid rgba(34,197,94,0.12);
        border-right: 1px solid rgba(34,197,94,0.08);
        border-bottom: 1px solid rgba(34,197,94,0.08);
        box-shadow: 0 2px 12px rgba(34,197,94,0.06);
        transition: all 0.2s ease;
    }
    .course-enroll-card:hover {
        box-shadow: 0 4px 20px rgba(34,197,94,0.12);
        border-left-color: rgba(34,197,94,0.8);
    }
    .course-enroll-card .c-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }
    .course-enroll-card .c-name { font-size: 14px; font-weight: 700; color: #2e364b; }
    .course-enroll-card .c-badge {
        font-size: 10px; font-weight: 700; padding: 3px 10px;
        background: rgba(34,197,94,0.1); color: #15803d;
        border-radius: 20px; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap;
    }
    .course-enroll-card .c-action { font-size: 11px; font-weight: 600; color: #15803d; margin-bottom: 6px; }
    .course-enroll-card .c-reason { font-size: 13px; color: #515f74; font-weight: 500; }
    .course-enroll-card .c-detail { font-size: 12px; color: #737784; line-height: 1.6; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(34,197,94,0.1); }

    /* ═══ SKILL CARD — viền vàng amber pastel ═══ */
    .skill-self-study-card {
        background: #ffffff;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 12px;
        border-left: 4px solid rgba(245,158,11,0.5);
        border-top: 1px solid rgba(245,158,11,0.12);
        border-right: 1px solid rgba(245,158,11,0.08);
        border-bottom: 1px solid rgba(245,158,11,0.08);
        box-shadow: 0 2px 12px rgba(245,158,11,0.06);
        transition: all 0.2s ease;
    }
    .skill-self-study-card:hover {
        box-shadow: 0 4px 20px rgba(245,158,11,0.12);
        border-left-color: rgba(245,158,11,0.8);
    }
    .skill-self-study-card .s-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }
    .skill-self-study-card .s-name { font-size: 14px; font-weight: 700; color: #2e364b; }
    .skill-self-study-card .s-platform {
        font-size: 10px; font-weight: 700; padding: 3px 10px;
        background: rgba(245,158,11,0.1); color: #b45309;
        border-radius: 20px; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap;
    }
    .skill-self-study-card .s-reason { font-size: 13px; color: #515f74; font-weight: 500; margin-bottom: 0; }
    .skill-self-study-card .s-detail { font-size: 12px; color: #737784; line-height: 1.6; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(245,158,11,0.1); }
    
    /* ═══ INTERACTIVE DETAILS (ACCORDION) ═══ */
    details {
        width: 100%;
        transition: all 0.3s ease;
    }
    summary {
        list-style: none; /* Ẩn mũi tên mặc định */
        cursor: pointer;
        outline: none;
    }
    summary::-webkit-details-marker {
        display: none;
    }
    summary .click-hint {
        display: block;
        font-size: 10px;
        font-weight: 700;
        color: #737784;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 10px;
        transition: color 0.2s;
    }
    details[open] summary .click-hint {
        color: #2e364b;
    }
    details[open] .c-detail, details[open] .s-detail {
        animation: fadeIn 0.4s ease-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* ═══ COURSE ROW (legacy — giữ cho tương thích) ═══ */
    .exec-course-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px;
        background: #f7f9fb;
        border-radius: 8px;
        margin-bottom: 8px;
        border: 1px solid transparent;
        transition: all 0.15s ease;
    }
    .exec-course-row:hover {
        background: #f2f4f6;
        border-color: rgba(195,198,213,0.2);
    }
    .exec-course-row .course-info .course-name {
        font-size: 14px;
        font-weight: 700;
        color: #2e364b;
    }
    .exec-course-row .course-info .course-detail {
        font-size: 12px;
        color: #515f74;
        font-weight: 500;
        margin-top: 2px;
    }
    .exec-course-row .course-badge {
        font-size: 10px;
        font-weight: 700;
        padding: 4px 10px;
        background: rgba(46,54,75,0.08);
        color: #2e364b;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        white-space: nowrap;
    }
    
    /* ═══ ROADMAP CARD (from RoadmapSection.tsx) ═══ */
    .exec-roadmap-card {
        background: #ffffff;
        padding: 24px;
        border-radius: 8px;
        border: 1px solid rgba(195,198,213,0.1);
        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
        transition: all 0.2s ease;
        margin-bottom: 12px;
    }
    .exec-roadmap-card:hover {
        box-shadow: 0 0 0 2px #2e364b;
    }
    .exec-roadmap-card .rm-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .exec-roadmap-card .rm-priority {
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #003e38;
    }
    .exec-roadmap-card .rm-title {
        font-size: 15px;
        font-weight: 700;
        color: #2e364b;
        margin-bottom: 4px;
    }
    .exec-roadmap-card .rm-desc {
        font-size: 12px;
        color: #515f74;
        font-weight: 500;
        line-height: 1.5;
    }
    
    /* ═══ RANKING LIST ═══ */
    .exec-rank-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0;
    }
    .exec-rank-item .rank-medal {
        font-size: 20px;
    }
    .exec-rank-item .rank-name {
        font-size: 14px;
        font-weight: 700;
        color: #2e364b;
    }
    .exec-rank-item .rank-score {
        font-size: 12px;
        font-weight: 500;
        color: #737784;
        margin-left: auto;
    }
    
    /* ═══ CARD CONTAINER ═══ */
    .exec-card {
        background: #ffffff;
        border: 1px solid rgba(195,198,213,0.08);
        border-radius: 12px;
        padding: 28px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.02);
        margin-bottom: 16px;
    }
    .exec-card-title {
        font-size: 14px;
        font-weight: 700;
        color: #2e364b;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 16px;
    }
    
    /* ═══ BUTTONS ═══ */
    .stButton > button[kind="primary"] {
        background-color: #2e364b;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.02em;
        transition: all 0.2s ease;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #003e38;
        box-shadow: 0 4px 16px rgba(0,62,56,0.25);
    }
    .stDownloadButton > button {
        background-color: #2e364b;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
    }
    .stDownloadButton > button:hover {
        background-color: #003e38;
    }
    
    /* ═══ EXECUTIVE EXPANDER (CUSTOM) ═══ */
    .executive-expander {
        margin-bottom: 24px;
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(0,0,0,0.05);
        background: #ffffff;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .executive-expander:hover {
        transform: translateY(-2px);
    }
    
    .executive-summary {
        padding: 20px 28px;
        font-weight: 800;
        font-size: 14px;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        cursor: pointer;
        list-style: none;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    /* Differentiated Variants */
    .summary-competency {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
    }
    .summary-courses {
        background: linear-gradient(135deg, #064e3b 0%, #10b981 100%);
        color: white;
    }
    .summary-skills {
        background: linear-gradient(135deg, #78350f 0%, #f59e0b 100%);
        color: white;
    }

    .executive-summary::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(rgba(255,255,255,0.15), transparent);
        opacity: 0;
        transition: opacity 0.3s;
    }
    .executive-summary:hover::before {
        opacity: 1;
    }

    .summary-title-wrapper {
        display: flex;
        align-items: center;
        gap: 12px;
        z-index: 1;
    }

    .summary-icon {
        font-size: 20px;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
    }

    .executive-summary .click-hint {
        font-size: 0;  /* Ẩn text thật, hiển thị qua ::before */
        font-weight: 600;
        color: rgba(255,255,255,0.85);
        letter-spacing: 0.1em;
        text-transform: uppercase;
        white-space: nowrap;
        margin-left: 16px;
        z-index: 1;
        background: rgba(0,0,0,0.15);
        padding: 4px 12px;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        transition: all 0.3s;
    }
    .executive-summary .click-hint::before {
        content: 'ẤN VÀO ĐỂ XEM PHÂN TÍCH';
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.08em;
    }

    .executive-expander[open] .executive-summary {
        border-bottom-left-radius: 0;
        border-bottom-right-radius: 0;
    }
    
    .executive-expander[open] .executive-summary .click-hint {
        background: rgba(255,255,255,0.25);
        color: white;
    }
    .executive-expander[open] .executive-summary .click-hint::before {
        content: 'THU GỌN';
    }

    .executive-content {
        padding: 32px;
        background: #fdfdfd;
        border-top: 1px solid rgba(0,0,0,0.05);
        animation: slideDown 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }

    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .exec-rank-item .rank-number {
        font-weight: 800;
        color: #3b82f6;
        margin-right: 12px;
        font-size: 14px;
    }
    
    hr { border-color: #f2f4f6; }
    .stAlert { border-radius: 12px; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }

    /* ═══ STRENGTH / WEAKNESS CARD ═══ */
    .sw-card {
        background: #ffffff;
        padding: 20px 24px;
        border-radius: 12px;
        margin-bottom: 12px;
        transition: all 0.2s ease;
    }
    .sw-card.strength {
        border-left: 4px solid rgba(0,180,160,0.5);
        border-top: 1px solid rgba(0,180,160,0.12);
        border-right: 1px solid rgba(0,180,160,0.08);
        border-bottom: 1px solid rgba(0,180,160,0.08);
        box-shadow: 0 2px 12px rgba(0,180,160,0.06);
    }
    .sw-card.strength:hover {
        box-shadow: 0 4px 20px rgba(0,180,160,0.12);
        border-left-color: rgba(0,180,160,0.8);
    }
    .sw-card.weakness {
        border-left: 4px solid rgba(225,29,72,0.45);
        border-top: 1px solid rgba(225,29,72,0.1);
        border-right: 1px solid rgba(225,29,72,0.06);
        border-bottom: 1px solid rgba(225,29,72,0.06);
        box-shadow: 0 2px 12px rgba(225,29,72,0.05);
    }
    .sw-card.weakness:hover {
        box-shadow: 0 4px 20px rgba(225,29,72,0.1);
        border-left-color: rgba(225,29,72,0.7);
    }
    .sw-card .sw-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
    .sw-card .sw-area { font-size: 14px; font-weight: 700; color: #2e364b; }
    .sw-card .sw-badge {
        font-size: 10px; font-weight: 700; padding: 3px 10px;
        border-radius: 20px; text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap;
    }
    .sw-card.strength .sw-badge { background: rgba(0,180,160,0.1); color: #047857; }
    .sw-card.weakness .sw-badge { background: rgba(225,29,72,0.08); color: #be123c; }
    .sw-card .sw-score { font-size: 22px; font-weight: 800; margin-bottom: 6px; }
    .sw-card.strength .sw-score { color: #047857; }
    .sw-card.weakness .sw-score { color: #be123c; }
    .sw-card .sw-insight { font-size: 13px; color: #515f74; font-weight: 500; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# Khởi tạo Session State
if "ocr_scores" not in st.session_state:
    st.session_state.ocr_scores = None
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "final_ranking" not in st.session_state:
    st.session_state.final_ranking = None
if "advisory_report" not in st.session_state:
    st.session_state.advisory_report = None
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False

@st.cache_resource
def load_engines():
    """Khởi tạo các Engine 1 lần duy nhất để tối ưu hiệu năng (v.2024.04.01)"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "Nhóm 2_Tính toán tiêu chí AHP môn HHTRQĐ.xlsx")
        ahp = AHPEngine(config_path)
        ahp.load_expert_knowledge()
        gemini = GeminiService()
        return ahp, gemini
    except Exception as e:
        st.error(f"Lỗi khởi tạo hệ thống lõi: {e}")
        st.stop()

@st.cache_data
def load_course_knowledge():
    """
    Nạp Cơ sở Tri thức Môn học từ course_database.xlsx vào RAM.
    -------------------------------------------------------
    Cache Strategy: @st.cache_data đảm bảo file chỉ được đọc từ ổ cứng
    DUY NHẤT 1 LẦN khi khởi động app. Mọi lần truy cập tiếp theo đều 
    đọc từ RAM cache với độ phức tạp O(1), triệt tiêu nghẽn I/O.
    -------------------------------------------------------
    Returns:
        str: Chuỗi văn bản tri thức gom nhóm C1->C5, sẵn sàng inject vào Prompt AI.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "course_database.xlsx")
    
    if not os.path.exists(db_path):
        return "(Chưa có Ngân hàng Môn học. Hãy chạy data_prep.py trước.)"
    
    import pandas as pd
    df = pd.read_excel(db_path, engine='openpyxl')
    
    # Nhóm tên mô tả cho từng criteria
    group_labels = {
        'C1': 'Kỹ năng Lập trình cốt lõi',
        'C2': 'Tư duy Toán học và Xử lý Dữ liệu',
        'C3': 'Tư duy Thiết kế Hệ thống',
        'C4': 'Kỹ năng Quản lý Quy trình & Chất lượng',
        'C5': 'Kiến thức Nghiệp vụ Chuyên ngành',
    }
    
    lines = []
    for group_key in ['C1', 'C2', 'C3', 'C4', 'C5']:
        group_name = group_labels.get(group_key, group_key)
        group_df = df[df['Nhóm năng lực'] == group_key]
        
        lines.append(f"\n--- Nhóm {group_key}: {group_name} ({len(group_df)} môn) ---")
        for _, row in group_df.iterrows():
            ma = str(row['Mã học phần']).strip()
            ten = str(row['Tên học phần mới']).strip()
            loai = str(row['Loại môn']).strip()
            hk = str(row.get('Học kỳ', '')).strip()
            hk_info = f", HK{hk}" if hk else ""
            lines.append(f"  {ma} - {ten} ({loai}{hk_info})")
    
    return "\n".join(lines)

def parse_ai_response(raw_text: str):
    """
    Bóc tách JSON từ phản hồi của AI. Thử tìm trong tag <final_output> trước,
    nếu không thấy thì tìm khối JSON thô đầu tiên trong văn bản.
    """
    try:
        if not raw_text or not isinstance(raw_text, str):
            return None
        
        # 1. Thử tìm trong tag <final_output>
        match = re.search(r'<final_output>\s*(.*?)\s*</final_output>', raw_text, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
        else:
            # 2. Nếu không có tag, thử tìm khối { ... } đầu tiên và cuối cùng
            # Đây là cách "lì lợm" để lấy JSON nấp trong văn bản
            match_json = re.search(r'(\{.*\})', raw_text, re.DOTALL)
            if match_json:
                json_str = match_json.group(1).strip()
            else:
                logging.warning("⚠️ Không tìm thấy cấu trúc JSON trong phản hồi AI.")
                return None
        
        # Làm sạch chuỗi JSON (loại bỏ markdown code fences)
        json_str = re.sub(r'^```(?:json)?\s*', '', json_str)
        json_str = re.sub(r'\s*```$', '', json_str)
        
        # Parse JSON
        data = json.loads(json_str)
        return data
    except Exception as e:
        logging.error(f"❌ Lỗi bóc tách JSON: {e}")
        return None

def draw_radar_chart(student_scores, job_profile, job_name, criteria_keys, dream_job_profile=None, dream_job_name=None):
    categories = criteria_keys
    
    student_values = [float(student_scores.get(k, 0)) for k in categories]
    
    # Min-Max Scaling job_values (AHP Profile) lên hệ quy chiếu [5, 10]
    raw_job_values = list(job_profile)
    min_job = min(raw_job_values)
    max_job = max(raw_job_values)
    if max_job == min_job:
        job_values = [10.0 for _ in raw_job_values]
    else:
        job_values = [((val - min_job) / (max_job - min_job)) * 5.0 + 5.0 for val in raw_job_values]
    
    # Close the polygon by appending the first value to the end
    categories = [*categories, categories[0]]
    student_values = [*student_values, student_values[0]]
    job_values = [*job_values, job_values[0]]

    fig = go.Figure()

    # Mảng 1: Thực tế (Xanh lam nhạt)
    fig.add_trace(go.Scatterpolar(
        r=student_values,
        theta=categories,
        fill='toself',
        name='Năng lực của Bạn',
        line_color='rgba(59, 130, 246, 0.8)',
        fillcolor='rgba(59, 130, 246, 0.4)'
    ))
    
    # Mảng 2: Job Đề xuất (Xanh lục)
    fig.add_trace(go.Scatterpolar(
        r=job_values,
        theta=categories,
        fill='toself',
        name=f'Top 1: {job_name}',
        line_color='rgba(34, 197, 94, 0.8)',
        fillcolor='rgba(34, 197, 94, 0.2)'
    ))

    # Mảng 3: Dream Job (Đỏ nét đứt)
    if dream_job_profile is not None and dream_job_name is not None:
        raw_dream_values = list(dream_job_profile)
        min_dream = min(raw_dream_values)
        max_dream = max(raw_dream_values)
        if max_dream == min_dream:
            dream_job_values = [10.0 for _ in raw_dream_values]
        else:
            dream_job_values = [((val - min_dream) / (max_dream - min_dream)) * 5.0 + 5.0 for val in raw_dream_values]
        
        dream_job_values = [*dream_job_values, dream_job_values[0]]
        fig.add_trace(go.Scatterpolar(
            r=dream_job_values,
            theta=categories,
            fill='none',
            name=f'Đam Mê: {dream_job_name}',
            line=dict(color='rgba(239, 68, 68, 0.8)', width=3, dash='dash')
        ))

    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickangle=0,
                gridcolor='lightgray',
                linecolor='lightgray',
                tickfont=dict(color='#1E293B')
            ),
            angularaxis=dict(
                gridcolor='lightgray',
                linecolor='lightgray',
                tickfont=dict(color='#1E293B', size=11)
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(color='#1E293B')
        ),
        title=dict(
            text="Phân tích Gap: Thực tế vs AHP vs Đam mê",
            font=dict(color='#1B2A4A', size=16)
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=40, b=40),
        font=dict(family="Inter, sans-serif", color='#1E293B')
    )
    return fig

def generate_pdf_report(report_md, radar_fig):
    import io
    import os
    import markdown
    from bs4 import BeautifulSoup
    from fpdf import FPDF

    # Render ảnh radar vào RAM (triệt tiêu WinError 32)
    img_bytes = io.BytesIO()
    radar_fig.write_image(img_bytes, format="png", engine="kaleido")
    img_bytes.seek(0)
    
    pdf = FPDF()
    pdf.add_page()
    
    font_path_regular = r"C:\Windows\Fonts\arial.ttf"
    font_path_bold = r"C:\Windows\Fonts\arialbd.ttf"
    font_path_italic = r"C:\Windows\Fonts\ariali.ttf"
    
    if os.path.exists(font_path_regular):
        pdf.add_font("ArialFallback", "", font_path_regular, uni=True)
        if os.path.exists(font_path_bold):
            pdf.add_font("ArialFallback", "B", font_path_bold, uni=True)
        if os.path.exists(font_path_italic):
            pdf.add_font("ArialFallback", "I", font_path_italic, uni=True)
        pdf.set_font("ArialFallback", size=12)
    else:
        pdf.set_font("Helvetica", size=12)
        
    pdf.set_font("ArialFallback", 'B', 18)
    pdf.cell(0, 10, txt="BÁO CÁO TƯ VẤN HƯỚNG NGHIỆP CNTT", ln=1, align='C')
    pdf.set_font("ArialFallback", 'I', 12)
    pdf.cell(0, 8, txt="Hệ thống Hỗ trợ Ra Quyết định (DSS)", ln=1, align='C')
    pdf.ln(5)
    
    # Phần 1 & 2: Biểu đồ (Căn giữa bằng cách chèn x)
    # Lấy độ rộng trang (width of A4 is 210mm) -> center image w=150 -> x=(210-150)/2 = 30
    pdf.image(img_bytes, x=30, w=150)
    pdf.ln(5)
    
    # Phần 3: Lời khuyên chi tiết từ AI
    pdf.set_font("ArialFallback", 'B', 14)
    pdf.cell(0, 10, txt="LỜI KHUYÊN CHI TIẾT TỪ AI:", ln=1, align='L')
    pdf.ln(2)
    pdf.set_font("ArialFallback", '', 12)
    
    # Biến HTML markup sang raw text đẹp để in multi-cell không bị lỗi FPDF HTML Parser
    # Tinh chỉnh lại text để loại bỏ khoảng trắng dư thừa
    html_content = markdown.markdown(report_md)
    text_content = BeautifulSoup(html_content, "html.parser").get_text("\n")
    
    # Đặt auto page break để multi-cell trôi chảy
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.multi_cell(0, 7, txt=text_content)
    
    pdf_bytes_data = pdf.output(dest='S')
    if isinstance(pdf_bytes_data, str):
        pdf_bytes_data = pdf_bytes_data.encode('latin1')
    return bytes(pdf_bytes_data)


# Bắt đầu giao diện
st.markdown("""
<div class="hero-banner">
    <span class="hero-badge">Decision Support System</span>
    <h1 class="hero-title">HỆ THỐNG HỖ TRỢ RA QUYẾT ĐỊNH</h1>
    <div class="hero-accent"></div>
    <p class="hero-subtitle">Tư vấn Lộ trình Nghề nghiệp CNTT &mdash; Phương pháp <strong>AHP</strong> kết hợp <strong>Trí tuệ Nhân tạo</strong></p>
</div>
""", unsafe_allow_html=True)

# Sidebar: Dev tools
with st.sidebar:
    st.markdown("### Cấu hình hệ thống")
    st.caption("Công cụ quản trị")
    if st.button("Xóa Cache và Tải lại Engine", help="Khởi tạo lại dịch vụ phân tích"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.success("Cache đã được xóa! Đang tải lại...")
        st.rerun()

ahp_engine, gemini_service = load_engines()


# BƯỚC 1: KHU VỰC TIÊU ĐỀ & CẢNH BÁO
st.markdown("<div class='section-title'>Chính sách Bảo mật</div>", unsafe_allow_html=True)
privacy_agreed = st.checkbox("Tôi đồng ý hệ thống ẩn danh dữ liệu cá nhân (Không lưu Tên, MSSV, Ảnh gốc) để bảo vệ quyền riêng tư.")

if privacy_agreed:
    st.divider()
    
    # BƯỚC 2: TIẾP NHẬN UPLOAD
    st.markdown("<div class='section-title'>Bước 1: Trích xuất Bảng điểm & Định hướng Nghề nghiệp</div>", unsafe_allow_html=True)
    
    # TÍCH HỢP ĐAM MÊ (DREAM JOB) GIAO DIỆN NỔI BẬT
    st.markdown("<div class='card'><p class='card-title'>Tiến độ Học tập & Định hướng</p></div>", unsafe_allow_html=True)
    st.caption("Việc chia sẻ định hướng giúp hệ thống phân tích lộ trình học bù (Gap Analysis) dành riêng cho bạn.")
    
    col_progress, col_job = st.columns(2)
    with col_progress:
        semester_options = [
            "Năm 1 - Học kỳ 1", "Năm 1 - Học kỳ 2", 
            "Năm 2 - Học kỳ 1", "Năm 2 - Học kỳ 2", 
            "Năm 3 - Học kỳ 1", "Năm 3 - Học kỳ 2", 
            "Năm 4 - Học kỳ 1", "Năm 4 - Học kỳ 2"
        ]
        semester_input = st.selectbox("Tiến độ học tập hiện tại của bạn:", options=semester_options)
        st.session_state.current_semester = semester_options.index(semester_input) + 1
        
    with col_job:
        dream_job_options = ["(Chưa xác định)"] + ahp_engine.job_roles
        dream_job_input = st.selectbox("Chọn định hướng nghề nghiệp:", options=dream_job_options)
        st.session_state.dream_job = dream_job_input if dream_job_input != "(Chưa xác định)" else "Chưa có định hướng rõ ràng"
    

    uploaded_file = st.file_uploader("Tải lên ảnh bảng điểm (.PNG, .JPG, .PDF) để hệ thống số hóa:", type=["png", "jpg", "jpeg", "pdf"])
    

    if uploaded_file is not None:
        # 🛡️ CHỐT CHẶN 1: KIỂM SOÁT DUNG LƯỢNG (Max 5MB)
        MAX_FILE_SIZE = 5 * 1024 * 1024 # 5MB
        if uploaded_file.size > MAX_FILE_SIZE:
            st.error("Dung lượng file quá lớn. Vui lòng nén file dưới 5MB.")
            st.stop()
            
        # 🛡️ CHỐT CHẶN 2 & 3: KIỂM SOÁT ĐỊNH DẠNG VÀ SỐ TRANG
        file_extension = uploaded_file.name.split('.')[-1].lower()
        try:
            if file_extension == 'pdf':
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                num_pages = len(pdf_reader.pages)
                if num_pages > 3:
                    st.error("Hệ thống chỉ chấp nhận bảng điểm tối đa 3 trang.")
                    st.stop()
                # Sau khi đọc xong, reset con trỏ file về 0
                uploaded_file.seek(0)
            else:
                from PIL import Image
                img_test = Image.open(uploaded_file)
                img_test.verify() # Nhận dạng file rách/lỗi
                uploaded_file.seek(0)
        except Exception as e:
            st.error("File của bạn bị lỗi hoặc không đúng định dạng chuẩn. Vui lòng xuất lại bảng điểm.")
            st.stop()
            
        col1, col2 = st.columns([1, 2])
        if file_extension != 'pdf':
            col1.image(uploaded_file, caption="Bảng điểm đã tải lên", use_container_width=True)
        else:
            col1.info(f"File PDF hợp lệ ({num_pages} trang). Nhấn Quét OCR để tiếp tục.")
        
        with col2:
            if st.button("Quét OCR bằng AI", use_container_width=True, type="primary"):
                with st.spinner("Đang đọc ảnh và ánh xạ môn học..."):
                    try:
                        # Gọi API Gemini OCR
                        # (Trong trường hợp demo thực tế ko có API key thật, ta sẽ giả lập dữ liệu)
                        if os.environ.get("GEMINI_API_KEY") == "MOCK_API_KEY_FOR_TESTING" or not os.environ.get("GEMINI_API_KEY"):
                            st.info("Đang chạy ở chế độ MOCK (Không cấu hình API Key). Tự sinh dữ liệu điểm...")
                            time.sleep(1.5)
                            st.session_state.ocr_scores = {
                                "C1": {"score": 8.5, "subjects": ["Lập trình C++: 8.5", "Cấu trúc dữ liệu: 8.5"]}, 
                                "C2": {"score": 9.0, "subjects": ["Toán rời rạc: 9.0"]}, 
                                "C3": {"score": 6.0, "subjects": ["Mạng máy tính: 6.0"]}, 
                                "C4": {"score": 7.0, "subjects": ["Quản lý dự án: 7.0"]}, 
                                "C5": {"score": 0.0, "subjects": []}
                            }
                        else:
                            import mimetypes
                            mime_type = mimetypes.guess_type(uploaded_file.name)[0] or "image/jpeg"
                            scores = gemini_service.extract_and_map_scores(uploaded_file.getvalue(), mime_type=mime_type)
                            if "error" in scores:
                                st.error("Hình ảnh không hợp lệ. Vui lòng tải lên đúng bảng điểm.")
                                st.stop()
                            st.session_state.ocr_scores = scores
                            
                        st.success("Trích xuất hoàn tất! Vui lòng kiểm tra lại điểm số bên dưới.")
                    except Exception as e:
                        st.error(f"Lỗi hệ thống: {str(e)}")
            
        # BƯỚC 3: HUMAN-IN-THE-LOOP (Kiểm duyệt điểm số)
        if st.session_state.ocr_scores is not None:
            st.divider()
            st.markdown("<div class='section-title'>Bước 2: Hiệu chỉnh Điểm số (Human-in-the-loop)</div>", unsafe_allow_html=True)
            st.warning("AI có thể nhận diện sai một vài môn học. Vui lòng rà soát và sửa dữ liệu bên dưới.")
            
            # Cột giải thích Tiêu chí
            criteria_desc = {
                "C1": "Khả năng Lập trình (Coding)",
                "C2": "Toán học & Dữ liệu (Math/Data)",
                "C3": "Hệ thống (System)",
                "C4": "Quy trình & Kỹ năng (Process)",
                "C5": "Nghiệp vụ Domain (Domain)"
            }
            
            edited_scores = {}
            for key, desc in criteria_desc.items():
                data = st.session_state.ocr_scores.get(key, {"score": 0.0, "subjects": []})
                # Đảm bảo tương thích nếu API trả về số thực (fallback)
                if isinstance(data, dict):
                    score = data.get("score", 0.0)
                    subjects = data.get("subjects", [])
                else:
                    score = float(data)
                    subjects = []
                    
                with st.expander(f"Tiêu chí {key} — {desc} (Điểm: {score:.1f})"):
                    if subjects:
                        st.markdown("**Các môn học thành phần:**")
                        for sub in subjects:
                            st.markdown(f"- {sub}")
                    else:
                        st.markdown("*Không có môn học nào thuộc nhóm này.*")
                        
                    # Sửa lại điểm nếu cần
                    new_score = st.number_input(f"Nhập điểm chốt cho {key}:", min_value=0.0, max_value=10.0, value=float(score), step=0.1, key=f"edit_score_{key}")
                    edited_scores[key] = new_score
            
            # BƯỚC 4: ANTI-SPAM VÀ RUN THUẬT TOÁN
            st.markdown("<br>", unsafe_allow_html=True)
            
            gemini_to_ahp_map = {
                "C1": "[C1] Coding",
                "C2": "[C2] Math/Data",
                "C3": "[C3] System",
                "C4": "[C4] Process",
                "C5": "[C5] Domain"
            }
            
            def process_engine():
                st.session_state.is_processing = True
                
            run_btn = st.button(
                "Chạy Thuật toán AHP & Khởi động Cố vấn AI", 
                type="primary", 
                use_container_width=True,
                disabled=st.session_state.is_processing,
                on_click=process_engine
            )
            
            if st.session_state.is_processing and not st.session_state.analysis_done:
                with st.spinner("Đang tính toán ma trận AHP và sinh báo cáo. Vui lòng không làm mới trang..."):
                    try:
                        # 1. Trích xuất dict sửa lại từ expander & Map sang AHP keys chuẩn xác
                        final_scores = {gemini_to_ahp_map.get(k, k): v for k, v in edited_scores.items()}
                        
                        # 2. Chạy thuật toán AHP
                        ranking = ahp_engine.calculate_personalized_ranking(final_scores)
                        st.session_state.final_ranking = ranking
                        
                        # 3. Nạp Ngân hàng Môn học (O(1) từ RAM cache)
                        course_knowledge = load_course_knowledge()
                        
                        # 4. Chạy Gemini sinh báo cáo (có inject Tri thức Môn học)
                        use_mock = st.session_state.get("demo_mode", False) or os.environ.get("GEMINI_API_KEY") == "MOCK_API_KEY_FOR_TESTING" or not os.environ.get("GEMINI_API_KEY")
                        if use_mock:
                            time.sleep(2)
                            mock_json = json.dumps({
                                "overview": f"Dựa trên phân tích AHP, năng lực Toán học và Lập trình của bạn rất nổi trội. Vị trí {ranking[0]['Job_Role']} phù hợp cao. Tuy nhiên, điểm Hệ thống (C3) đang là điểm yếu cần khắc phục.",
                                "strengths_weaknesses": [
                                    {"area": "Tư duy Toán học và Xử lý Dữ liệu", "type": "strength", "score": 9.0, "insight": "Năng lực xuất sắc. Đây là lợi thế cạnh tranh rất lớn cho các vị trí liên quan đến AI, Data Science. Hãy phát huy tối đa nền tảng này."},
                                    {"area": "Kỹ năng Lập trình cốt lõi", "type": "strength", "score": 8.5, "insight": "Nền tảng vững chắc, đủ điều kiện cho việc triển khai các dự án thực tế. Cần nâng cao thêm khả năng viết mã sạch và tối ưu hoá."},
                                    {"area": "Tư duy Thiết kế Hệ thống", "type": "weakness", "score": 6.0, "insight": "Lỗ hổng nghiêm trọng nhất trong hồ sơ. 100% doanh nghiệp lớn yêu cầu kiến thức về Cloud, Docker và CI/CD. Cần ưu tiên bổ sung gấp."},
                                    {"area": "Kiến thức Nghiệp vụ Chuyên ngành", "type": "weakness", "score": 5.0, "insight": "Điểm thấp nhất, tuy nhiên không ảnh hưởng quá lớn nếu bạn nhắm vị trí kỹ thuật thuần túy. Xem xét bổ sung nếu chuyển hướng BA/PM."}
                                ],
                                "recommended_courses": [
                                    {"course_id": "IT301", "course_name": "Mạng máy tính nâng cao", "semester": "HK5", "action": "Đăng ký mới", "reason": "Lấp khoảng trống C3 - System, nền tảng bắt buộc cho mọi vị trí IT"},
                                    {"course_id": "IT205", "course_name": "Kiến trúc phần mềm", "semester": "HK4", "action": "Đăng ký mới", "reason": "Tư duy thiết kế hệ thống là yêu cầu then chốt của doanh nghiệp"},
                                    {"course_id": "IT102", "course_name": "Cấu trúc dữ liệu và Giải thuật", "semester": "HK2", "action": "Học cải thiện", "reason": "Nền tảng giải thuật cần vững chắc hơn cho vị trí AI Engineer"}
                                ],
                                "external_skills": [
                                    {"skill": "Docker & Kubernetes", "platform": "Udemy / KodeKloud", "reason": "95% doanh nghiệp yêu cầu container hóa ứng dụng"},
                                    {"skill": "AWS Cloud Practitioner", "platform": "AWS Skill Builder", "reason": "Cloud là hạ tầng tiêu chuẩn, chứng chỉ tăng lợi thế cạnh tranh"}
                                ]
                            }, ensure_ascii=False)
                            report = f"<thought_process>\nĐây là dữ liệu MOCK để kiểm thử giao diện.\n</thought_process>\n\n<final_output>\n{mock_json}\n</final_output>"
                        else:
                            report = gemini_service.generate_advisory_report(
                                final_scores, 
                                ranking, 
                                st.session_state.dream_job,
                                course_knowledge_text=course_knowledge,
                                current_semester=st.session_state.current_semester
                            )
                            
                        st.session_state.advisory_report = report
                        st.session_state.analysis_done = True
                        st.session_state.is_processing = False
                        st.rerun() # Refresh màn hình để update UI
                        
                    except Exception as e:
                        st.error(f"Lỗi xử lý: {str(e)}")
                        st.session_state.is_processing = False
                        
            # BƯỚC 5: TRÌNH BÀY KẾT QUẢ — THE EXECUTIVE DASHBOARD
            if st.session_state.analysis_done:
                st.divider()
                
                # Parse AI response
                parsed_data = parse_ai_response(st.session_state.advisory_report)
                
                # ── HEADER SECTION (from App.tsx header) ──
                top1_role = st.session_state.final_ranking[0]["Job_Role"]
                top1_score = st.session_state.final_ranking[0]["Matching_Score"]
                dream = st.session_state.dream_job
                semester = st.session_state.current_semester
                
                header_html = (
                    '<div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:28px;">'
                    '<div>'
                    '<h2 style="font-size:26px;font-weight:800;color:#2e364b;margin:0;letter-spacing:-0.5px;">CHIẾN LƯỢC NGHỀ NGHIỆP</h2>'
                    f'<p style="color:#515f74;font-weight:500;margin-top:4px;">Định hướng: <span style="color:#2e364b;font-weight:700;">{dream}</span></p>'
                    '</div>'
                    '<div style="text-align:right;">'
                    '<span style="display:inline-block;padding:4px 14px;background:#003e38;color:white;font-size:10px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;border-radius:20px;margin-bottom:6px;">TÌNH TRẠNG HỌC VỤ</span>'
                    f'<p style="font-size:13px;font-weight:500;color:#515f74;margin:0;">Học kỳ {semester} / 8</p>'
                    '</div>'
                    '</div>'
                )
                st.markdown(header_html, unsafe_allow_html=True)
                
                # ── KPI GRID (from KPICard.tsx) ──
                status_text = "Phân tích thành công" if parsed_data else "Fallback Mode"
                status_color = "#003e38" if parsed_data else "#737784"
                
                k1, k2, k3, k4 = st.columns(4)
                with k1:
                    kpi1 = '<div class="exec-kpi"><p class="kpi-label">Độ tương thích</p>' + f'<p class="kpi-value">{top1_score}<span class="kpi-unit">%</span></p><p class="kpi-trend">Vị trí số 1: {top1_role}</p></div>'
                    st.markdown(kpi1, unsafe_allow_html=True)
                with k2:
                    num_courses = len(parsed_data.get('recommended_courses', [])) if parsed_data else 0
                    kpi2 = '<div class="exec-kpi"><p class="kpi-label">Học phần đề xuất</p>' + f'<p class="kpi-value">{num_courses}<span class="kpi-unit"> môn</span></p></div>'
                    st.markdown(kpi2, unsafe_allow_html=True)
                with k3:
                    num_skills = len(parsed_data.get('external_skills', [])) if parsed_data else 0
                    kpi3 = '<div class="exec-kpi"><p class="kpi-label">Kỹ năng tự học</p>' + f'<p class="kpi-value">{num_skills}<span class="kpi-unit"> kỹ năng</span></p></div>'
                    st.markdown(kpi3, unsafe_allow_html=True)
                with k4:
                    kpi4 = f'<div class="exec-kpi"><p class="kpi-label">Trạng thái phân tích</p><p class="kpi-value" style="font-size:16px;color:{status_color};">{status_text}</p></div>'
                    st.markdown(kpi4, unsafe_allow_html=True)
                
                st.markdown("")
                
                # ── MAIN CONTENT GRID ──
                col1, col2 = st.columns([5, 7])
                
                # ════ CỘT TRÁI: Competency Matrix + Ranking ════
                with col1:
                    st.markdown('<div class="exec-card"><p class="exec-card-title">MA TRẬN NĂNG LỰC & SO SÁNH GAP</p><p style="font-size:12px;color:#515f74;font-weight:500;margin-top:-12px;margin-bottom:16px;">Phân tích AHP — So sánh năng lực hiện tại với yêu cầu vị trí</p></div>', unsafe_allow_html=True)
                    
                    fig = None
                    try:
                        role_index = ahp_engine.job_roles.index(top1_role)
                        top1_profile = ahp_engine.job_profile_matrix[role_index]
                        
                        dream_job_profile = None
                        dream_job_name = None
                        try:
                            dj = st.session_state.dream_job
                            if dj and dj != "Chưa có định hướng rõ ràng":
                                dj_index = ahp_engine.job_roles.index(dj)
                                dream_job_profile = ahp_engine.job_profile_matrix[dj_index]
                                dream_job_name = dj
                        except ValueError:
                            pass

                        mapped_scores_chart = {gemini_to_ahp_map.get(k, k): v for k, v in edited_scores.items()}
                        
                        fig = draw_radar_chart(
                            mapped_scores_chart, 
                            top1_profile, 
                            top1_role, 
                            ahp_engine.criteria_keys,
                            dream_job_profile=dream_job_profile,
                            dream_job_name=dream_job_name
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except ValueError:
                        st.caption("Không tìm thấy ma trận Profile để vẽ biểu đồ.")
                    
                    # Ranking list — build full HTML string first, pass directly
                    ranking_html = '<div class="exec-card"><p class="exec-card-title">Xếp hạng mức độ phù hợp</p>'
                    for i, res in enumerate(st.session_state.final_ranking[:3]):
                        rank_num = i + 1
                        ranking_html += (
                            '<div class="exec-rank-item">'
                            f'<span class="rank-number">TOP {rank_num}</span>'
                            f'<span class="rank-name">{res["Job_Role"]}</span>'
                            f'<span class="rank-score">{res["Matching_Score"]}%</span>'
                            '</div>'
                        )
                    ranking_html += '</div>'
                    st.markdown(ranking_html, unsafe_allow_html=True)
                
                # ════ CỘT PHẢI: AI Synthesis + Courses + Roadmap ════
                with col2:
                    if parsed_data:
                        # ── AI Synthesis Card — Tư vấn Chiến lược ──
                        overview = parsed_data.get('overview', 'Không có dữ liệu.')
                        synth_html = (
                            '<div class="exec-synthesis">'
                            '<p class="synth-label">PHÂN TÍCH CHIẾN LƯỢC TỪ CHUYÊN GIA AI</p>'
                            f'<p class="synth-body">{overview}</p>'
                            '</div>'
                        )
                        st.markdown(synth_html, unsafe_allow_html=True)
                        
                        # ── PHÂN TÍCH NĂNG LỰC CHI TIẾT (ĐIỂM MẠNH / ĐIỂM YẾU) ──
                        # Ưu tiên dữ liệu từ AI, nếu không có thì tự tính từ điểm số
                        sw_items = parsed_data.get("strengths_weaknesses", [])
                        
                        if not sw_items:
                            # Fallback: Tự sinh từ điểm số sinh viên
                            area_labels = {
                                "C1": "Kỹ năng Lập trình cốt lõi",
                                "C2": "Tư duy Toán học và Xử lý Dữ liệu",
                                "C3": "Tư duy Thiết kế Hệ thống",
                                "C4": "Kỹ năng Quản lý Quy trình & Chất lượng",
                                "C5": "Kiến thức Nghiệp vụ Chuyên ngành"
                            }
                            for ck, label in area_labels.items():
                                sc = edited_scores.get(ck, 0)
                                sw_type = "strength" if sc >= 7.0 else "weakness"
                                if sw_type == "strength":
                                    insight = f"Điểm {sc}/10 cho thấy nền tảng vững chắc. Đây là lợi thế cạnh tranh giúp tiếp cận tốt các vị trí đòi hỏi năng lực này."
                                else:
                                    insight = f"Điểm {sc}/10 đang dưới ngưỡng cạnh tranh. Cần ưu tiên bổ sung kiến thức để thu hẹp khoảng cách với yêu cầu thị trường."
                                sw_items.append({"area": label, "type": sw_type, "score": sc, "insight": insight})
                        
                        if sw_items:
                            # Sắp xếp: điểm mạnh lên trước, điểm yếu xuống sau
                            sw_items.sort(key=lambda x: (0 if x.get('type') == 'strength' else 1, -x.get('score', 0)))
                            num_str = len([x for x in sw_items if x.get('type') == 'strength'])
                            num_wk = len([x for x in sw_items if x.get('type') == 'weakness'])
                            sw_html = (
                                '<details class="executive-expander">'
                                '<summary class="executive-summary summary-competency">'
                                '<div class="summary-title-wrapper">'
                                f'<span>PHÂN TÍCH NĂNG LỰC: {num_str} ĐIỂM MẠNH — {num_wk} ĐIỂM YẾU</span>'
                                '</div>'
                                '<span class="click-hint"></span>'
                                '</summary>'
                                '<div class="executive-content">'
                            )
                            for item in sw_items:
                                sw_type = item.get('type', 'strength')
                                area = item.get('area', 'N/A')
                                score = item.get('score', 0)
                                insight = item.get('insight', '')
                                badge_text = 'Điểm mạnh' if sw_type == 'strength' else 'Điểm yếu'
                                score_display = f'{score}/10'
                                
                                sw_html += (
                                    f'<div class="sw-card {sw_type}">'
                                    '<div class="sw-header">'
                                    f'<span class="sw-area">{area}</span>'
                                    f'<span class="sw-badge">{badge_text}</span>'
                                    '</div>'
                                    f'<p class="sw-score">{score_display}</p>'
                                    f'<p class="sw-insight">{insight}</p>'
                                    '</div>'
                                )
                            sw_html += '</div></details>'
                            st.markdown(sw_html, unsafe_allow_html=True)
                        
                        # ── HỌC PHẦN ĐỀ XUẤT ĐĂNG KÝ (TRONG TRƯỜNG) ──
                        courses = parsed_data.get("recommended_courses", [])
                        if courses:
                            courses_html = (
                                '<details class="executive-expander">'
                                '<summary class="executive-summary summary-courses">'
                                '<div class="summary-title-wrapper">'
                                f'<span>DANH SÁCH {len(courses)} HỌC PHẦN KHUYẾN NGHỊ</span>'
                                '</div>'
                                '<span class="click-hint"></span>'
                                '</summary>'
                                '<div class="executive-content">'
                            )
                            for course in courses:
                                cname   = course.get('course_name', 'N/A')
                                cid     = course.get('course_id', '')
                                sem     = course.get('semester', '')
                                action  = course.get('action', '')
                                reason  = course.get('reason', '')
                                detail  = course.get('detailed_reason', '')
                                detail_block = f'<div class="c-detail">{detail}</div>' if detail else ''
                                
                                courses_html += (
                                    '<div class="course-enroll-card">'
                                    '<div class="c-header">'
                                    f'<span class="c-name">{cid}: {cname}</span>'
                                    f'<span class="c-badge">{sem}</span>'
                                    '</div>'
                                    f'<p class="c-action">PHƯƠNG ÁN: {action}</p>'
                                    f'<p class="c-reason">{reason}</p>'
                                    + detail_block +
                                    '</div>'
                                )
                            courses_html += '</div></details>'
                            st.markdown(courses_html, unsafe_allow_html=True)
                        
                        # ── LỘ TRÌNH TỰ HỌC NGOÀI TRƯỜNG (KIẾN NGHỊ) ──
                        skills = parsed_data.get("external_skills", [])
                        if skills:
                            skills_html = (
                                '<details class="executive-expander">'
                                '<summary class="executive-summary summary-skills">'
                                '<div class="summary-title-wrapper">'
                                f'<span>LỘ TRÌNH {len(skills)} KỸ NĂNG TỰ HỌC NGOÀI TRƯỜNG</span>'
                                '</div>'
                                '<span class="click-hint"></span>'
                                '</summary>'
                                '<div class="executive-content">'
                            )
                            for skill_item in skills:
                                sname    = skill_item.get('skill', 'N/A')
                                platform = skill_item.get('platform', '')
                                reason   = skill_item.get('reason', '')
                                detail   = skill_item.get('detailed_reason', '')
                                detail_block = f'<div class="s-detail">{detail}</div>' if detail else ''
                                
                                skills_html += (
                                    '<div class="skill-self-study-card">'
                                    '<div class="s-header">'
                                    f'<span class="s-name">{sname}</span>'
                                    f'<span class="s-platform">{platform}</span>'
                                    '</div>'
                                    f'<p class="s-reason">{reason}</p>'
                                    + detail_block +
                                    '</div>'
                                )
                            skills_html += '</div></details>'
                            st.markdown(skills_html, unsafe_allow_html=True)
                    else:
                        # Fallback
                        with st.container(border=True):
                            st.markdown("##### CANH BAO: Khong the phan tich cau truc dữ liệu")
                            raw = st.session_state.advisory_report
                            if raw:
                                st.markdown(raw, unsafe_allow_html=True)
                            else:
                                st.caption("Khong co du lieu bao cao. Vui long chay lai phan tich.")
                        
                st.markdown("---")
                st.markdown("<div class='section-title'>KẾT XUẤT BÁO CÁO CHI TIẾT</div>", unsafe_allow_html=True)
                
                # TÍNH NĂNG XUẤT PDF
                # TÍNH NĂNG XUẤT PDF - Nâng cấp nội dung chuyên sâu
                if fig is not None:
                    try:
                        if parsed_data:
                            pdf_report_text = f"NHẬN ĐỊNH CHIẾN LƯỢC TỪ CHUYÊN GIA AI:\n{parsed_data.get('overview', '')}\n\n"
                            
                            pdf_report_text += "HỌC PHẦN ĐỀ XUẤT ĐĂNG KÝ (TRONG TRƯỜNG):\n"
                            for c in parsed_data.get('recommended_courses', []):
                                pdf_report_text += f"- {c.get('course_id', '')} {c.get('course_name', '')} ({c.get('action', '')})\n"
                                pdf_report_text += f"  Lý do chiến lược: {c.get('reason', '')}\n"
                                if c.get('detailed_reason'):
                                    pdf_report_text += f"  Phân tích chuyên sâu: {c.get('detailed_reason')}\n"
                                pdf_report_text += "\n"
                                
                            pdf_report_text += "LỘ TRÌNH TÍCH LŨY KỸ NĂNG (NGOÀI TRƯỜNG):\n"
                            for s in parsed_data.get('external_skills', []):
                                pdf_report_text += f"- {s.get('skill', '')} (Nền tảng: {s.get('platform', '')})\n"
                                pdf_report_text += f"  Lý do cần thiết: {s.get('reason', '')}\n"
                                if s.get('detailed_reason'):
                                    pdf_report_text += f"  Phân tích thực tế: {s.get('detailed_reason')}\n"
                                pdf_report_text += "\n"
                        else:
                            pdf_report_text = st.session_state.advisory_report or "(Không có nội dung báo cáo)"
                        
                        with st.spinner("Đang khởi tạo bản in PDF chuyên sâu..."):
                            pdf_bytes = generate_pdf_report(pdf_report_text, fig)
                        st.download_button(
                            label="📥 Tải Báo cáo Chiến lược Nghề nghiệp (PDF)",
                            data=pdf_bytes,
                            file_name=f"Bao_Cao_Chien_Luoc_IT_{st.session_state.dream_job.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"⚠️ Không thể tạo bản in PDF. Lỗi hệ thống: {e}")
                else:
                    st.caption("Không thể tạo PDF do biểu đồ radar chưa được khởi tạo.")
                        
                # Nút Reset
                if st.button("Bắt đầu Phân tích Mới"):
                    for key in ["ocr_scores", "is_processing", "analysis_done", "final_ranking", "advisory_report"]:
                        del st.session_state[key]
                    st.rerun()
else:
    st.caption("Vui lòng xác nhận sự đồng ý ở trên để bắt đầu sử dụng Hệ thống.")
