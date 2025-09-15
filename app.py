import streamlit as st
import google.generativeai as genai
import json
import random
import pandas as pd
import re
import time
from prompts import *
import database
from components.interview_card import show_interview_card
from components.proctoring import ProctoringProcessor
from streamlit_webrtc import webrtc_streamer, WebRtcMode

# --- MAJOR SETTING: MOCK API MODE ---
MOCK_API_CALLS = False
# ------------------------------------

# --- Initialize Database ---
database.init_db()
# ---------------------------

st.set_page_config(layout="wide")


# Load custom CSS
def load_css():
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()


TRANSITION_PHRASES = [
    "Alright, next question for you.", "Okay, let's move on to the next one.",
    "Here is your next question.", "Let's try this one.", "Okay, moving on."
]

if not MOCK_API_CALLS:
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", system_instruction=INTERVIEWER_PERSONA
        )
    except (KeyError, ValueError):
        st.error("🚨 Error: GOOGLE_API_KEY not found. Please add it to your secrets.", icon="🚨")
        st.stop()

def initialize_session_state():
    if "page" not in st.session_state:
        st.session_state.page = "LOGIN"
    if "user_details" not in st.session_state:
        st.session_state.user_details = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "stage" not in st.session_state:
        st.session_state.stage = "AWAITING_START"
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "questions" not in st.session_state:
        st.session_state.questions = []
    if "question_index" not in st.session_state:
        st.session_state.question_index = 0
    if "evaluations" not in st.session_state:
        st.session_state.evaluations = []
    if "original_answer" not in st.session_state:
        st.session_state.original_answer = ""
    if "psych_question_count" not in st.session_state:
        st.session_state.psych_question_count = 0
    if "last_psych_question" not in st.session_state:
        st.session_state.last_psych_question = ""
    if "camera_active" not in st.session_state:
        st.session_state.camera_active = False
    if "last_warning" not in st.session_state:
        st.session_state.last_warning = "Status: OK"
    if "show_warning_dialog" not in st.session_state:
        st.session_state.show_warning_dialog = False
    if "warning_count" not in st.session_state:
        st.session_state.warning_count = 0    
    # -----------------------------------------------------------

def type_effect(text):
    for word in text.split():
        yield word + " "

def select_questions():
    all_questions = json.load(open("questions.json"))
    easy_q, mid_q, hard_q = [q for q in all_questions if q['level'] == 'easy'], [q for q in all_questions if q['level'] == 'mid'], [q for q in all_questions if q['level'] == 'hard']
    selected_questions = random.sample(hard_q, 2) + random.sample(easy_q + mid_q, 8)
    random.shuffle(selected_questions)
    return selected_questions

def generate_mock_content(prompt_type):
    time.sleep(0.5)
    class MockResponse:
        def __init__(self, text): self.text = text
    if prompt_type == "GREETING": return MockResponse("Hello, I am Alex, an AI interviewer. Please introduce yourself.")
    if prompt_type == "NAME_EXTRACTION": return MockResponse(st.session_state.user_details['name'])
    if prompt_type == "TRANSITION_TO_QUESTIONS": return MockResponse(f"Thank you, {st.session_state.user_details['name']}. Let's begin.")
    if prompt_type == "EVALUATION": return MockResponse('{"score": 3, "feedback": "This is mock feedback."}')
    if prompt_type == "PSYCH_RESPONSE_TRANSITION": return MockResponse("Okay, noted. Let's review.")
    if prompt_type == "FINAL_SUMMARY": return MockResponse("This is a mock summary.")
    return MockResponse("This is a generic mock response.")

def render_login_page():
    st.title("AI Excel Interviewer Login")
    st.write("Use one of the sample credentials: `priya_s` (pass123), `amit_k` (pass456), `sneha_p` (pass789)")
    with st.form("login_form"):
        userid = st.text_input("UserID")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", key="login_button")
        if submitted:
            user_details = database.verify_user(userid, password)
            if user_details:
                st.session_state.user_details = user_details
                st.session_state.page = "INTERVIEW"
                st.rerun()
            else:
                st.error("Invalid UserID or password")

# --- UPDATED: This function is now completely replaced ---

def render_interview_page():
    # Create three equal-width columns
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    # --- USER DETAILS & TIMER (Left Column) ---
    with col1:
        st.subheader("Candidate Details")
        show_interview_card(
            name=st.session_state.user_details['name'],
            email=st.session_state.user_details['email'],
            start_time=st.session_state.start_time
        )

    # --- CHAT INTERFACE (Middle Column) ---
    with col2:
        st.title("🤖 AI Excel Interview")
        if MOCK_API_CALLS:
            st.warning("Running in MOCK mode. AI responses are placeholders.", icon="⚠️")

        # Create a container with a fixed height for the chat history
        chat_container = st.container(height=500, border=False)
        with chat_container:
            for i, message in enumerate(st.session_state.messages):
                with st.chat_message(message["role"]):
                    # If it's the last message from the assistant, apply the effect
                    if message["role"] == "assistant" and i == len(st.session_state.messages) - 1:
                        st.write_stream(type_effect(message["content"]))
                    else:
                        st.markdown(message["content"])

        # Start button and chat input are below the chat history
        if st.session_state.stage == "AWAITING_START":
            if st.button("Start Interview", use_container_width=True, key="start_button"):
                st.session_state.stage = "BOT_INTRODUCTION"
                st.session_state.questions = select_questions()
                st.session_state.start_time = time.time()
                if MOCK_API_CALLS:
                    response = generate_mock_content("GREETING")
                else:
                    response = model.generate_content(GREETING_PROMPT)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.rerun()

        if st.session_state.stage == "INTERVIEW_COMPLETE":
            if st.button("Submit and See Evaluation", use_container_width=True, key="submit_button"):
                database.save_interview_results(
                    userid=st.session_state.user_details['userid'],
                    evaluations=st.session_state.evaluations,
                    warning_count=st.session_state.warning_count
                )
                st.session_state.page = "EVALUATION"
                st.rerun()    

        is_interview_running = st.session_state.stage not in ["AWAITING_START", "INTERVIEW_COMPLETE"]
        chat_disabled = not st.session_state.camera_active and is_interview_running

        if chat_disabled and is_interview_running:
            st.info("Please enable your camera on the right to activate the answer box.")

        if prompt := st.chat_input("Your answer...", disabled=chat_disabled):
            st.session_state.messages.append({"role": "user", "content": prompt})
            handle_user_response(prompt)
            st.rerun()

    # --- CAMERA AND PROCTORING (Right Column) ---
    with col3:
        st.subheader("Camera & Proctoring")
        
        if st.session_state.stage not in ["AWAITING_START", "INTERVIEW_COMPLETE"]:
            st.warning("Camera must remain on. Turning it off will terminate the interview.", icon="❗")

        ctx = None
        if st.session_state.stage != "AWAITING_START":
            ctx = webrtc_streamer(
                key="proctoring",
                mode=WebRtcMode.SENDRECV,
                video_processor_factory=ProctoringProcessor,
                media_stream_constraints={"video": True, "audio": False},
                async_processing=True,
            )
            
            is_camera_playing = ctx is not None and ctx.state.playing
            interview_in_progress = st.session_state.stage not in ["AWAITING_START", "INTERVIEW_COMPLETE"]

            if interview_in_progress and st.session_state.camera_active and not is_camera_playing:
                st.session_state.page = "TERMINATED_CAMERA"
                st.rerun()

            if is_camera_playing != st.session_state.camera_active:
                st.session_state.camera_active = is_camera_playing
                st.rerun()

            if ctx and ctx.video_processor:
                current_warning = ctx.video_processor.warning_message
                
                # New Status Display Logic in a container
                with st.container(border=True):
                    if "Warning" in current_warning:
                        st.error(f"**Status:** {current_warning}", icon="🚨")
                    else:
                        st.success(f"**Status:** {current_warning}", icon="✅")
                    
                    # Use st.metric for a visually appealing warning counter
                    st.metric(label="Warnings", value=f"{st.session_state.warning_count} / 3")


                is_malpractice = "Warning:" in current_warning
                if is_malpractice and current_warning != st.session_state.last_warning:
                    st.toast(f"🚨 {current_warning} 🚨", icon="⚠️")
                    st.session_state.last_warning = current_warning
                    st.session_state.warning_count += 1

                    if st.session_state.warning_count >= 3:
                        st.session_state.page = "TERMINATED"
                        st.rerun()

                elif not is_malpractice and st.session_state.last_warning != "Status: OK":
                    st.session_state.last_warning = "Status: OK"
                    
    # Timer update logic should be outside the columns
    if st.session_state.stage not in ["AWAITING_START", "INTERVIEW_COMPLETE"]:
        # Rerun every second to update the timer
        time.sleep(1)
        st.rerun()

def render_evaluation_page():
    st.title("📈 Interview Performance Evaluation")
    if MOCK_API_CALLS: st.warning("Displaying MOCK evaluation data.", icon="⚠️")
    if not st.session_state.evaluations:
        st.warning("No evaluations recorded.")
        return
    total_score = sum(item.get('score', 0) for item in st.session_state.evaluations)
    max_score = len(st.session_state.evaluations) * 5
    final_percentage = (total_score / max_score) * 100 if max_score > 0 else 0

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Final Score", f"{total_score}/{max_score}", f"{final_percentage:.1f}%")
    with m2:
        st.metric("Total Questions", len(st.session_state.evaluations))
    with m3:
        # Use warning_count from session state
        st.metric("Proctoring Warnings", st.session_state.warning_count)
    st.divider() 
    
    with st.spinner("Generating final summary..."):
        if MOCK_API_CALLS: summary_response = generate_mock_content("FINAL_SUMMARY")
        else:
            eval_json_str = json.dumps(st.session_state.evaluations)
            summary_prompt = FINAL_REPORT_PROMPT_TEMPLATE.format(evaluations=eval_json_str)
            summary_response = model.generate_content(summary_prompt)
        st.subheader("Overall Summary")
        st.markdown(summary_response.text)
    st.subheader("Detailed Breakdown")
    df_data = []
    for i, eval_item in enumerate(st.session_state.evaluations):
        df_data.append({"Question #": i + 1, "Topic": eval_item["topic"], "Your Score (out of 5)": eval_item["score"], "Feedback": eval_item["feedback"]})
    df = pd.DataFrame(df_data)

    def style_scores(score):
        """Applies color to the score cell based on its value."""
        color = 'white' # default text color
        if score < 3:
            background_color = '#992222' # Red
        elif score == 3:
            background_color = '#886600' # Yellow
        else:
            background_color = '#227722' # Green
        return f'background-color: {background_color}; color: {color}'

    # Apply the styling function to the 'Your Score' column
    st.dataframe(
        df.style.apply(lambda x: x.map(style_scores), subset=['Your Score (out of 5)']),
        hide_index=True,
        use_container_width=True
    )

# In app.py (can be placed after render_evaluation_page)

def render_terminated_page():
    st.title("❌ Interview Terminated")
    st.error(
        "Your interview has been terminated due to receiving 3 warnings regarding the interview policy. "
        "This session has now concluded. Please contact the hiring administrator for further information."
    )
    st.warning(f"Total Warnings Received: {st.session_state.warning_count}")
    st.stop()


def render_terminated_camera_page():
    st.title("❌ Interview Terminated")
    st.error(
        "Your interview has been terminated because the camera was deactivated during the session. "
        "Maintaining a constant video feed is mandatory for this assessment."
    )
    st.stop()


def handle_user_response(prompt):
    current_stage = st.session_state.stage
    if current_stage == "BOT_INTRODUCTION": handle_introduction_and_transition(prompt)
    elif current_stage == "AWAITING_ANSWER": handle_main_answer(prompt)
    elif current_stage == "AWAITING_PSYCH_RESPONSE": handle_psych_response(prompt)

def handle_introduction_and_transition(introduction_text):
    with st.spinner("..."):
        if MOCK_API_CALLS:
            name_response = generate_mock_content("NAME_EXTRACTION")
            transition_response = generate_mock_content("TRANSITION_TO_QUESTIONS")
        else:
            name_prompt = NAME_EXTRACTION_PROMPT_TEMPLATE.format(introduction=introduction_text)
            name_response = model.generate_content(name_prompt)
            transition_prompt = TRANSITION_TO_QUESTIONS_PROMPT_TEMPLATE.format(name=name_response.text.strip())
            transition_response = model.generate_content(transition_prompt)
        st.session_state.messages.append({"role": "assistant", "content": transition_response.text})
    ask_next_question()

def ask_next_question():
    idx = st.session_state.question_index
    if idx < len(st.session_state.questions):
        question = st.session_state.questions[idx]['question']
        transition = random.choice(TRANSITION_PHRASES)
        st.session_state.messages.append({"role": "assistant", "content": f"{transition}\n\n{question}"})
        st.session_state.stage = "AWAITING_ANSWER"
    else:
        st.session_state.stage = "INTERVIEW_COMPLETE"
        st.session_state.messages.append({"role": "assistant", "content": "That was the final question. Please click the 'Submit' button."})

def handle_main_answer(answer):
    question_data = st.session_state.questions[st.session_state.question_index]
    if (question_data['level'] in ['mid', 'hard'] and st.session_state.psych_question_count < 4):
        st.session_state.original_answer, st.session_state.stage = answer, "AWAITING_PSYCH_RESPONSE"
        psych_question = random.choice(PSYCHOLOGICAL_QUESTIONS)
        st.session_state.last_psych_question = psych_question
        st.session_state.psych_question_count += 1
        st.session_state.messages.append({"role": "assistant", "content": psych_question})
    else:
        perform_evaluation(answer)

def handle_psych_response(psych_response):
    with st.spinner("..."):
        if MOCK_API_CALLS:
            transition_response = generate_mock_content("PSYCH_RESPONSE_TRANSITION")
        else:
            prompt = PSYCH_RESPONSE_TRANSITION_PROMPT_TEMPLATE.format(psych_question=st.session_state.last_psych_question, psych_response=psych_response)
            transition_response = model.generate_content(prompt)
        st.session_state.messages.append({"role": "assistant", "content": transition_response.text})
    perform_evaluation(st.session_state.original_answer)

def perform_evaluation(answer):
    idx = st.session_state.question_index
    question_data = st.session_state.questions[idx]
    with st.spinner("..."):
        try:
            if MOCK_API_CALLS: response = generate_mock_content("EVALUATION")
            else:
                prompt = EVALUATION_PROMPT_TEMPLATE.format(question=question_data['question'], answer=answer)
                response = model.generate_content(prompt)
            text_response = response.text
            match = re.search(r"```json\s*(\{.*?\})\s*```", text_response, re.DOTALL)
            json_str = match.group(1) if match else text_response.strip()
            evaluation = json.loads(json_str)
            eval_data = {**question_data, **evaluation}
            st.session_state.evaluations.append(eval_data)
            conversational_feedback = evaluation.get("feedback", "Okay, noted.")
            st.session_state.messages.append({"role": "assistant", "content": conversational_feedback})
        except (json.JSONDecodeError, AttributeError, KeyError) as e:
            st.warning("Sorry, there was an issue processing that response. Let's move on.")
        finally:
            st.session_state.question_index += 1
            ask_next_question()

initialize_session_state()
if st.session_state.page == "LOGIN":
    render_login_page()
elif 'user_details' in st.session_state and st.session_state.user_details:
    if st.session_state.page == "INTERVIEW":
        render_interview_page()
    elif st.session_state.page == "EVALUATION":
        render_evaluation_page()
    elif st.session_state.page == "TERMINATED":
        render_terminated_page()
    elif st.session_state.page == "TERMINATED_CAMERA":
        render_terminated_camera_page()
else:
    render_login_page()