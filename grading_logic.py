# grading_logic.py
import re
from rubric_data import RUBRIC


def normalize(text):
    return re.sub(r"\s+", " ", text.strip().lower())


def contains_any(text, keywords):
    t = normalize(text)
    return any(kw in t for kw in keywords)


def contains_all(text, keywords):
    t = normalize(text)
    return all(kw in t for kw in keywords)


def match_required_any(text, groups):
    return any(contains_all(text, g) for g in groups)


def match_required_groups(text, groups):
    return all(any(kw in normalize(text) for kw in g) for g in groups)


def check_wrong_keywords(text, wrong_list):
    t = normalize(text)
    return [w for w in wrong_list if w in t]


def extract_method_labels(text, valid_methods):
    found = re.findall(r"[（(]([^）)]+)[）)]", text)
    return [f.strip() for f in found if f.strip() in valid_methods]


def count_sentences(text):
    sentences = re.split(r"[.。!?]\s*", text.strip())
    return len([s for s in sentences if s.strip()])


def check_logical_flow(s1, s2):
    connectors = [
        "그러나", "반면", "하지만", "이에 반해", "반대로",
        "또한", "따라서", "그러므로", "이처럼", "즉", "예를 들어",
        "더불어", "이와 달리", "그런데", "이에 비해"
    ]
    has_connector = any(c in s2 for c in connectors)
    overlap = len(set(normalize(s1).split()) & set(normalize(s2).split()))
    total = len(set(normalize(s1).split()) | set(normalize(s2).split()))
    similarity = overlap / total if total > 0 else 0
    if similarity > 0.7:
        return False, "⚠️ 두 문장이 거의 동일한 내용입니다. 논리적 심화가 필요합니다."
    if not has_connector:
        return False, "⚠️ 접속어가 없어 논리적 흐름 연결이 불명확합니다."
    return True, "✅ 논리적 흐름 충족"


def grade_q1(set_num, answers):
    rubric = RUBRIC[set_num]["q1"]
    results = {}

    for key in ["gim", "gin", "gic"]:
        r = rubric[key]
        ans = answers.get(key, "").strip()
        max_score = r["score"]
        feedback = []
        score = 0

        if not ans:
            results[key] = {
                "label": r["label"], "score": 0, "max": max_score,
                "status": "❌ 미작성", "feedback": ["답안을 작성해 주세요."],
                "model": r["model_answer"]
            }
            continue

        wrong_hits = check_wrong_keywords(ans, r.get("wrong_keywords", []))
        if wrong_hits:
            results[key] = {
                "label": r["label"], "score": 0, "max": max_score,
                "status": "❌ 오답",
                "feedback": [f"오개념 키워드 감지: '{', '.join(wrong_hits)}'"],
                "model": r["model_answer"]
            }
            continue

        if "required_any" in r:
            if match_required_any(ans, r["required_any"]):
                score = max_score
                feedback.append("✅ 핵심 요소 충족")
            elif "partial_only" in r and contains_any(ans, r["partial_only"]):
                score = max_score // 2
                feedback.append("⚠️ 부분 인정: 핵심 요소 일부 누락")
            else:
                score = 0
                feedback.append("❌ 핵심 요소 미포함")

        elif "required_groups" in r:
            matched = [
                any(kw in normalize(ans) for kw in g)
                for g in r["required_groups"]
            ]
            if all(matched):
                score = max_score
                feedback.append("✅ 모든 핵심 요소 충족")
            elif any(matched):
                score = max_score // 2
                missing = [
                    f"그룹{i+1}({'/'.join(r['required_groups'][i])})"
                    for i, m in enumerate(matched) if not m
                ]
                feedback.append(f"⚠️ 부분 인정: {', '.join(missing)} 누락")
            else:
                score = 0
                feedback.append("❌ 핵심 요소 미포함")

        status = "✅ 정답" if score == max_score else ("⚠️ 부분 인정" if score > 0 else "❌ 오답")
        results[key] = {
            "label": r["label"], "score": score, "max": max_score,
            "status": status, "feedback": feedback,
            "model": r["model_answer"]
        }

    return results


def grade_q2(set_num, ans1, ans2):
    r = RUBRIC[set_num]["q2"]
    cond = r["conditions"]
    valid_methods = r["valid_methods"]
    max_score = r["score"]
    feedback = []
    score = max_score
    deductions = []

    full_text = ans1 + " " + ans2

    if not ans1.strip() and not ans2.strip():
        return {
            "score": 0, "max": max_score, "status": "❌ 미작성",
            "feedback": ["답안을 작성해 주세요."],
            "model_answers": r["model_answers"]
        }

    sc1 = count_sentences(ans1)
    sc2 = count_sentences(ans2)
    if sc1 > 1:
        deductions.append(f"⚠️ (1)번이 {sc1}문장입니다. 1문장 조건 위반 (-1점)")
        score -= 1
    if sc2 > 1:
        deductions.append(f"⚠️ (2)번이 {sc2}문장입니다. 1문장 조건 위반 (-1점)")
        score -= 1

    methods1 = extract_method_labels(ans1, valid_methods)
    methods2 = extract_method_labels(ans2, valid_methods)

    if not methods1:
        deductions.append("⚠️ (1)번 설명 방법 명칭 미표기 (-1점)")
        score -= 1
    if not methods2:
        deductions.append("⚠️ (2)번 설명 방법 명칭 미표기 (-1점)")
        score -= 1

    if methods1 and methods2:
        def normalize_method(m):
            return "대조" if m == "비교" else m
        nm1 = [normalize_method(m) for m in methods1]
        nm2 = [normalize_method(m) for m in methods2]
        if set(nm1) & set(nm2):
            deductions.append("⚠️ (1)(2)에 동일한 설명 방법 사용 (-1점)")
            score -= 1
        else:
            feedback.append("✅ 서로 다른 설명 방법 사용 확인")

    for pattern in r.get("wrong_patterns", []):
        if re.search(pattern, normalize(full_text)):
            deductions.append(f"❌ 오개념 감지: 개념 혼동 (-2점)")
            score -= 2

    concept_ok_1 = any(
        contains_all(ans1, group)
        for group in r["required_concepts"]["(1)"]
    )
    concept_ok_2 = any(
        contains_all(ans2, group)
        for group in r["required_concepts"]["(2)"]
    )

    if not concept_ok_1:
        deductions.append("⚠️ (1)번에 필수 개념 미포함 (-1점)")
        score -= 1
    else:
        feedback.append("✅ (1)번 필수 개념 포함")

    if not concept_ok_2:
        deductions.append("⚠️ (2)번에 필수 개념 미포함 (-1점)")
        score -= 1
    else:
        feedback.append("✅ (2)번 필수 개념 포함")

    if cond.get("logical_flow"):
        flow_ok, flow_msg = check_logical_flow(ans1, ans2)
        if not flow_ok:
            deductions.append(f"{flow_msg} (-1점)")
            score -= 1
        else:
            feedback.append(flow_msg)

    conclusion_keywords = {
        1: ["향상", "효과적", "촉진", "억제", "저하"],
        2: ["위험하지 않", "안전", "전류량", "머물"],
        3: ["예술", "범주", "확장", "변화", "가치"],
    }
    ck = conclusion_keywords.get(set_num, [])
    if ck and not contains_any(full_text, ck):
        deductions.append("⚠️ 결론 방향 불명확 — 핵심 결론어 미포함 (-1점)")
        score -= 1
    else:
        feedback.append("✅ 결론 방향 명확")

    score = max(0, score)
    all_feedback = feedback + deductions
    status = "✅ 정답" if score == max_score else ("⚠️ 부분 인정" if score > 0 else "❌ 오답")

    return {
        "score": score, "max": max_score, "status": status,
        "feedback": all_feedback,
        "model_answers": r["model_answers"]
    }


def grade_q3(set_num, ans_a, ans_b):
    r = RUBRIC[set_num]["q3"]["scene2"]
    results = {}

    for key, ans in [("A", ans_a), ("B", ans_b)]:
        rb = r[key]
        max_score = rb["score"]
        feedback = []
        score = 0
        deductions = []

        if not ans.strip():
            results[key] = {
                "label": rb["label"], "score": 0, "max": max_score,
                "status": "❌ 미작성", "feedback": ["답안을 작성해 주세요."],
                "model": rb["model_answer"]
            }
            continue

        wrong_hits = check_wrong_keywords(ans, rb.get("wrong_keywords", []))
        if wrong_hits:
            deductions.append(
                f"❌ 장면 1과 동일한 요소 감지: '{', '.join(wrong_hits)}' — 대조 조건 위반 (-2점)"
            )
            score -= 2

        concept_groups = rb.get("required_concepts", [])
        matched = [
            any(kw in normalize(ans) for kw in g)
            for g in concept_groups
        ]

        if all(matched):
            score += 2
            feedback.append("✅ 요소 설정 충족")
        elif any(matched):
            score += 1
            missing = [
                f"그룹{i+1}({'/'.join(concept_groups[i])})"
                for i, m in enumerate(matched) if not m
            ]
            deductions.append(f"⚠️ 요소 설정 부분 충족: {', '.join(missing)} 누락")
        else:
            deductions.append("❌ 요소 설정 미충족")

        effect_keywords = [
            "이를 통해", "효과", "전달", "표현", "강조",
            "부각", "나타낸다", "보여준다", "느낄 수 있"
        ]
        if contains_any(ans, effect_keywords):
            score += 1
            feedback.append("✅ 효과 서술 포함")
        else:
            deductions.append("⚠️ 효과 서술 누락 (-1점)")

        if set_num in [2, 3]:
            ground_keywords = {
                2: {
                    "A": ["전하", "이동", "머물", "정전기"],
                    "B": ["전류량", "정전기", "위험하지 않", "안전"],
                },
                3: {
                    "A": ["감정", "경험", "창작", "인간"],
                    "B": ["감동", "감정", "따뜻", "인간"],
                },
            }
            gk = ground_keywords.get(set_num, {}).get(key, [])
            if gk and not contains_any(ans, gk):
                deductions.append("⚠️ 지문 근거 미명시 (-1점)")
                score -= 1
            else:
                feedback.append("✅ 지문 근거 포함")

        contrast_keywords = ["장면 1", "대조", "대비", "반면", "달리", "비해", "반대로"]
        if contains_any(ans, contrast_keywords):
            score += 1
            feedback.append("✅ 장면 1과의 대조 언급")
        else:
            deductions.append("⚠️ 장면 1과의 대조 언급 없음 (-1점)")
            score -= 1

        score = max(0, min(score, max_score))
        status = "✅ 정답" if score == max_score else ("⚠️ 부분 인정" if score > 0 else "❌ 오답")

        results[key] = {
            "label": rb["label"], "score": score, "max": max_score,
            "status": status, "feedback": feedback + deductions,
            "model": rb["model_answer"]
        }

    return results


def grade_all(set_num, q1_answers, q2_ans1, q2_ans2, q3_ans_a, q3_ans_b):
    q1 = grade_q1(set_num, q1_answers)
    q2 = grade_q2(set_num, q2_ans1, q2_ans2)
    q3 = grade_q3(set_num, q3_ans_a, q3_ans_b)

    q1_total = sum(v["score"] for v in q1.values())
    q1_max   = sum(v["max"]   for v in q1.values())
    q3_total = q3["A"]["score"] + q3["B"]["score"]
    q3_max   = q3["A"]["max"]   + q3["B"]["max"]
    total     = q1_total + q2["score"] + q3_total
    total_max = q1_max   + q2["max"]   + q3_max

    return {
        "set_num": set_num,
        "q1": q1, "q1_total": q1_total, "q1_max": q1_max,
        "q2": q2,
        "q3": q3, "q3_total": q3_total, "q3_max": q3_max,
        "total": total, "total_max": total_max,
    }
