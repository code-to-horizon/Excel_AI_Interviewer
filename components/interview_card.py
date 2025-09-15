# components/interview_card.py
import streamlit as st
import time

def show_interview_card(name, email, start_time):
    """Displays a card in the top-left with user details and a running timer (DARK THEME)."""
    
    # Calculate elapsed time
    if start_time:
        elapsed_seconds = int(time.time() - start_time)
        minutes = elapsed_seconds // 60
        seconds = elapsed_seconds % 60
        timer_text = f"{minutes:02d}:{seconds:02d}"
    else:
        timer_text = "00:00"

    # Use st.markdown with a custom div for positioning and styling (Dark Theme CSS)
    card_html = f"""
    <div style="
        background-color: #262730;
        color: #FAFAFA;
        border: 1px solid #444;
        border-radius: 10px;
        padding: 15px;
        width: 100%;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
        <h4 style="margin-bottom: 10px; color: #FFFFFF;">{name}</h4>
        <p style="font-size: 14px; color: #A0A0A0; margin-bottom: 15px;">{email}</p>
        <div style="font-size: 20px; font-weight: bold; text-align: center; background-color: #1A1A1A; border-radius: 5px; padding: 5px; color: #FAFAFA;">
            <span style="font-size:14px; font-weight:normal; color:#A0A0A0;">Time Elapsed:</span><br>
            {timer_text}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)  