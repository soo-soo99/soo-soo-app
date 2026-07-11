# app.py
import streamlit as st
from grading_logic import grade_all
from rubric_data import RUBRIC

# ── 페이지 설정 ───────────────────────────────────────────
st.set_page_config(
    page_title="서논술형 자동 채점",
    page_icon="📝",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2rem; font-weight: 800;
        color: #1a1a2e; text-align: center;
        padding: 1rem 0 0.5rem;
    }
    .sub-title {
        font-size: 1rem; color: #555;
        text-align: center; margin-bottom: 2rem;
    }
    .score-box {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white; border-radius: 12px;
        padding: 1.2rem; text-align: center;
        font-size: 1.5rem; font-weight: 700;
        margin: 0.5rem 0;
    }
    .score-box-sub {
        background: #f0f4ff; border-radius: 10px;
        padding: 1rem; text-align: center;
        font-size: 1.1rem; font-weight: 600;
        color: #3a3a5c; margin: 0.3rem 0;
    }
    .feedback-ok  { color: #1e8449; font-weight: 600; }
    .feedback-warn{ color: #d68910; font-weight: 600; }
    .feedback-err { color: #c0392b; font-weight: 600; }
    .model-box {
        background: #eafaf1; border-left: 4px solid #27ae60;
        border-radius: 6px; padding: 0.8rem 1rem;
        margin-top: 0.5rem; font-size: 0.92rem;
        color: #1a5c35;
    }
    .section-header {
        background: #1a1a2e; color: white;
        padding: 0.5rem 1rem; border-radius: 8px;
        font-size: 1.1rem; font-weight: 700;
        margin: 1.5rem 0 1rem;
    }
    .divider { border-top: 2px solid #e0e0e0; margin: 1.5rem 0; }
</style>
""", unsafe_allow_html=True)


# ── 헬퍼 함수 ─────────────────────────────────────────────
SET_NAMES = {
    1: "세트 1 — 사회적 촉진과 억제",
    2: "세트 2 — 정전기",
    3: "세트 3 — AI 그림",
}

def feedback_html(msgs: list) -> str:
    lines = []
    for m in msgs:
        if m.startswith("✅"):
            cls = "feedback-ok"
        elif m.startswith("⚠️"):
            cls = "feedback-warn"
        else:
            cls = "feedback-err"
        lines.append(f'<p class="{cls}">{m}</p>')
    return "".join(lines)

def render_score_badge(score, max_score):
    pct = int(score / max_score * 100) if max_score else 0
    color = "#27ae60" if pct == 100 else ("#d68910" if pct >= 50 else "#c0392b")
    st.markdown(
        f'<div style="display:inline-block; background:{color}; color:white; '
        f'border-radius:20px; padding:2px 14px; font-weight:700; font-size:1rem;">'
        f'{score} / {max_score}점</div>',
        unsafe_allow_html=True
    )

def render_model_answers_q2(model_answers: list):
    with st.expander("📚 설명 방법 조합별 모범 답안 보기"):
        for ma in model_answers:
            st.markdown(f"**🔷 {ma['combo']}**")
            st.markdown(
                f'<div class="model-box">'
                f'<b>(1)</b> {ma["(1)"]}<br><br>'
                f'<b>(2)</b> {ma["(2)"]}'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown("")


# ── 메인 앱 ───────────────────────────────────────────────
def main():
    st.markdown('<div class="main-title">📝 서논술형 자동 채점 시스템</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">2회 시험 대비 | 1~3번 문항 채점 연습</div>', unsafe_allow_html=True)

    # ── 세트 선택
    set_num = st.selectbox(
        "📂 채점할 세트를 선택하세요",
        options=[1, 2, 3],
        format_func=lambda x: SET_NAMES[x],
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # 서논술형 1번
    # ══════════════════════════════════════════
    st.markdown('<div class="section-header">📌 서논술형 1번 — 표 완성 (㉠~㉢)</div>',
                unsafe_allow_html=True)

    rubric_q1 = RUBRIC[set_num]["q1"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**{rubric_q1['gim']['label']}**")
        ans_gim = st.text_area("㉠ 답안 입력", key="gim", height=100,
                               placeholder="㉠에 해당하는 내용을 입력하세요.")
    with col2:
        st.markdown(f"**{rubric_q1['gin']['label']}**")
        ans_gin = st.text_area("㉡ 답안 입력", key="gin", height=100,
                               placeholder="㉡에 해당하는 내용을 입력하세요.")
    with col3:
        st.markdown(f"**{rubric_q1['gic']['label']}**")
        ans_gic = st.text_area("㉢ 답안 입력", key="gic", height=100,
                               placeholder="㉢에 해당하는 내용을 입력하세요.")

    # ══════════════════════════════════════════
    # 서논술형 2번
    # ══════════════════════════════════════════
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">✍️ 서논술형 2번 — 설명문 작성</div>',
                unsafe_allow_html=True)

    has_flow = RUBRIC[set_num]["q2"]["conditions"].get("logical_flow", False)
    flow_note = " *(논리적 흐름 조건 포함)*" if has_flow else ""
    st.caption(f"각 1문장 | 서로 다른 설명 방법 | 괄호 명칭 표기 | 지문 내용만 활용{flow_note}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**(1)번 문장**")
        ans_q2_1 = st.text_area("(1) 답안 입력", key="q2_1", height=140,
                                placeholder="예) ...이다. (대조)")
    with col_b:
        st.markdown("**(2)번 문장**")
        ans_q2_2 = st.text_area("(2) 답안 입력", key="q2_2", height=140,
                                placeholder="예) ...이다. (예시)")

    # ══════════════════════════════════════════
    # 서논술형 3번
    # ══════════════════════════════════════════
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">🎬 서논술형 3번 — 영상 기획안 (장면 2)</div>',
                unsafe_allow_html=True)

    ground_note = " *(지문 내용을 근거로 효과 서술)*" if set_num in [2, 3] else ""
    st.caption(f"Ⓐ 시각 요소 + Ⓑ 청각 요소 | 연출 효과 서술 포함 | 장면 1과 대조{ground_note}")

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("**Ⓐ 시각 요소**")
        ans_q3_a = st.text_area("Ⓐ 답안 입력", key="q3_a", height=180,
                                placeholder="시각 요소 설정 + 연출 효과 서술")
    with col_d:
        st.markdown("**Ⓑ 청각 요소**")
        ans_q3_b = st.text_area("Ⓑ 답안 입력", key="q3_b", height=180,
                                placeholder="청각 요소 설정 + 연출 효과 서술")

    # ══════════════════════════════════════════
    # 채점 버튼
    # ══════════════════════════════════════════
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    btn = st.button("🔍 채점하기", type="primary", use_container_width=True)

    if btn:
        with st.spinner("채점 중..."):
            result = grade_all(
                set_num=set_num,
                q1_answers={"gim": ans_gim, "gin": ans_gin, "gic": ans_gic},
                q2_ans1=ans_q2_1,
                q2_ans2=ans_q2_2,
                q3_ans_a=ans_q3_a,
                q3_ans_b=ans_q3_b,
            )

        # ── 총점 표시
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("## 📊 채점 결과")

        total_col, q1_col, q2_col, q3_col = st.columns(4)
        with total_col:
            st.markdown(
                f'<div class="score-box">총점<br>{result["total"]} / {result["total_max"]}점</div>',
                unsafe_allow_html=True
            )
        with q1_col:
            st.markdown(
                f'<div class="score-box-sub">1번<br>{result["q1_total"]} / {result["q1_max"]}점</div>',
                unsafe_allow_html=True
            )
        with q2_col:
            st.markdown(
                f'<div class="score-box-sub">2번<br>{result["q2"]["score"]} / {result["q2"]["max"]}점</div>',
                unsafe_allow_html=True
            )
        with q3_col:
            st.markdown(
                f'<div class="score-box-sub">3번<br>{result["q3_total"]} / {result["q3_max"]}점</div>',
                unsafe_allow_html=True
            )

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ── 1번 상세
        st.markdown("### 📌 서논술형 1번 상세")
        r1 = result["q1"]
        for key, label_k in [("gim", "㉠"), ("gin", "㉡"), ("gic", "㉢")]:
            item = r1[
