# app.py
import streamlit as st
from grading_logic import grade_all
from rubric_data import RUBRIC

st.set_page_config(
    page_title="서논술형 자동 채점",
    page_icon="📝",
    layout="wide",
)

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
    .feedback-ok   { color: #1e8449; font-weight: 600; }
    .feedback-warn { color: #d68910; font-weight: 600; }
    .feedback-err  { color: #c0392b; font-weight: 600; }
    .model-box {
        background: #eafaf1; border-left: 4px solid #27ae60;
        border-radius: 6px; padding: 0.8rem 1rem;
        margin-top: 0.5rem; font-size: 0.92rem; color: #1a5c35;
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

SET_NAMES = {
    1: "세트 1 — 사회적 촉진과 억제",
    2: "세트 2 — 정전기",
    3: "세트 3 — AI 그림",
}

def feedback_html(msgs):
    lines = []
    for m in msgs:
        if m.startswith("✅"):
            cls = "feedback-ok"
        elif m.startswith("⚠️"):
            cls = "feedback-warn"
        else:
            cls = "feedback-err"
        lines.append(f'<p class="{cls}" style="margin:4px 0;">{m}</p>')
    return "".join(lines)

def render_model_answers_q2(model_answers):
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

def render_q1_detail(r1):
    cols = st.columns(3)
    for idx, (key, label_k) in enumerate([("gim","㉠"), ("gin","㉡"), ("gic","㉢")]):
        item = r1[key]
        with cols[idx]:
            st.markdown(f"**{item['label']}**")
            score_color = (
                "#27ae60" if item["score"] == item["max"]
                else ("#d68910" if item["score"] > 0 else "#c0392b")
            )
            st.markdown(
                f'<span style="background:{score_color};color:white;'
                f'border-radius:12px;padding:2px 12px;font-weight:700;">'
                f'{item["score"]} / {item["max"]}점 {item["status"]}</span>',
                unsafe_allow_html=True
            )
            st.markdown(feedback_html(item["feedback"]), unsafe_allow_html=True)
            with st.expander("📌 모범 답안 보기"):
                st.markdown(
                    f'<div class="model-box">{item["model"]}</div>',
                    unsafe_allow_html=True
                )

def render_q2_detail(q2):
    score_color = (
        "#27ae60" if q2["score"] == q2["max"]
        else ("#d68910" if q2["score"] > 0 else "#c0392b")
    )
    st.markdown(
        f'<span style="background:{score_color};color:white;'
        f'border-radius:12px;padding:2px 12px;font-weight:700;">'
        f'{q2["score"]} / {q2["max"]}점 {q2["status"]}</span>',
        unsafe_allow_html=True
    )
    st.markdown(feedback_html(q2["feedback"]), unsafe_allow_html=True)
    render_model_answers_q2(q2["model_answers"])

def render_q3_detail(q3):
    col_a, col_b = st.columns(2)
    for col, key in [(col_a, "A"), (col_b, "B")]:
        item = q3[key]
        with col:
            st.markdown(f"**{item['label']}**")
            score_color = (
                "#27ae60" if item["score"] == item["max"]
                else ("#d68910" if item["score"] > 0 else "#c0392b")
            )
            st.markdown(
                f'<span style="background:{score_color};color:white;'
                f'border-radius:12px;padding:2px 12px;font-weight:700;">'
                f'{item["score"]} / {item["max"]}점 {item["status"]}</span>',
                unsafe_allow_html=True
            )
            st.markdown(feedback_html(item["feedback"]), unsafe_allow_html=True)
            with st.expander("📌 모범 답안 보기"):
                st.markdown(
                    f'<div class="model-box">{item["model"]}</div>',
                    unsafe_allow_html=True
                )

def main():
    st.markdown('<div class="main-title">📝 서논술형 자동 채점 시스템</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="sub-title">2회 시험 대비 | 1~3번 문항 채점 연습</div>',
                unsafe_allow_html=True)

    set_num = st.selectbox(
        "📂 채점할 세트를 선택하세요",
        options=[1, 2, 3],
        format_func=lambda x: SET_NAMES[x],
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── 1번 입력 ───────────────────────────────────────────
    st.markdown('<div class="section-header">📌 서논술형 1번 — 표 완성 (㉠~㉢)</div>',
                unsafe_allow_html=True)
    rubric_q1 = RUBRIC[set_num]["q1"]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**{rubric_q1['gim']['label']}**")
        ans_gim = st.text_area(
            "㉠ 답안",
            key="gim",
            height=100,
            placeholder="여기에 답안을 입력하세요.",  # ← 힌트 없음
            value="",                                  # ← 초기값 비움
        )
    with col2:
        st.markdown(f"**{rubric_q1['gin']['label']}**")
        ans_gin = st.text_area(
            "㉡ 답안",
            key="gin",
            height=100,
            placeholder="여기에 답안을 입력하세요.",
            value="",
        )
    with col3:
        st.markdown(f"**{rubric_q1['gic']['label']}**")
        ans_gic = st.text_area(
            "㉢ 답안",
            key="gic",
            height=100,
            placeholder="여기에 답안을 입력하세요.",
            value="",
        )

    # ── 2번 입력 ───────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">✍️ 서논술형 2번 — 설명문 작성</div>',
                unsafe_allow_html=True)
    has_flow = RUBRIC[set_num]["q2"]["conditions"].get("logical_flow", False)
    flow_note = " *(논리적 흐름 조건 포함)*" if has_flow else ""
    st.caption(f"각 1문장 | 서로 다른 설명 방법 | 괄호 명칭 표기 | 지문 내용만 활용{flow_note}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**(1)번 문장**")
        ans_q2_1 = st.text_area(
            "(1) 답안",
            key="q2_1",
            height=150,
            placeholder="여기에 답안을 입력하세요.",  # ← 힌트 없음
            value="",
        )
    with col_b:
        st.markdown("**(2)번 문장**")
        ans_q2_2 = st.text_area(
            "(2) 답안",
            key="q2_2",
            height=150,
            placeholder="여기에 답안을 입력하세요.",
            value="",
        )

    # ── 3번 입력 ───────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">🎬 서논술형 3번 — 영상 기획안 (장면 2)</div>',
                unsafe_allow_html=True)
    ground_note = " *(지문 내용을 근거로 효과 서술)*" if set_num in [2, 3] else ""
    st.caption(f"Ⓐ 시각 요소 + Ⓑ 청각 요소 | 연출 효과 서술 | 장면 1과 대조{ground_note}")

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("**Ⓐ 시각 요소**")
        ans_q3_a = st.text_area(
            "Ⓐ 답안",
            key="q3_a",
            height=180,
            placeholder="여기에 답안을 입력하세요.",  # ← 힌트 없음
            value="",
        )
    with col_d:
        st.markdown("**Ⓑ 청각 요소**")
        ans_q3_b = st.text_area(
            "Ⓑ 답안",
            key="q3_b",
            height=180,
            placeholder="여기에 답안을 입력하세요.",
            value="",
        )

    # ── 채점 버튼 ──────────────────────────────────────────
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

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("## 📊 채점 결과")

        total_col, q1_col, q2_col, q3_col = st.columns(4)
        with total_col:
            st.markdown(
                f'<div class="score-box">총점<br>'
                f'{result["total"]} / {result["total_max"]}점</div>',
                unsafe_allow_html=True
            )
        with q1_col:
            st.markdown(
                f'<div class="score-box-sub">1번<br>'
                f'{result["q1_total"]} / {result["q1_max"]}점</div>',
                unsafe_allow_html=True
            )
        with q2_col:
            st.markdown(
                f'<div class="score-box-sub">2번<br>'
                f'{result["q2"]["score"]} / {result["q2"]["max"]}점</div>',
                unsafe_allow_html=True
            )
        with q3_col:
            st.markdown(
                f'<div class="score-box-sub">3번<br>'
                f'{result["q3_total"]} / {result["q3_max"]}점</div>',
                unsafe_allow_html=True
            )

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        st.markdown("### 📌 서논술형 1번 상세")
        render_q1_detail(result["q1"])

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        st.markdown("### ✍️ 서논술형 2번 상세")
        render_q2_detail(result["q2"])

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        st.markdown("### 🎬 서논술형 3번 상세")
        render_q3_detail(result["q3"])

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        st.markdown("### 💬 종합 피드백")
        pct = result["total"] / result["total_max"] * 100 if result["total_max"] else 0
        if pct == 100:
            st.success("🎉 모든 문항을 완벽하게 작성했습니다!")
        elif pct >= 75:
            st.info("👍 전반적으로 잘 작성했습니다. 부분 감점 항목을 확인하세요.")
        elif pct >= 50:
            st.warning("📖 핵심 개념을 다시 확인하고 모범 답안을 참고하세요.")
        else:
            st.error("❗ 모범 답안과 채점 기준을 꼼꼼히 검토한 후 다시 작성해 보세요.")

if __name__ == "__main__":
    main()
