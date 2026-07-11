
📄 grading_logic.py — GitHub에 붙여넣을 전체 코드
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
    total  = len(set(normalize(s1).split()) | set(normalize(s2).split()))
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
        r   = rubric[key]
        ans = answers.get(key, "").strip()
        max_score = r["score"]
        feedback  = []
        score     = 0
        if not ans:
            results[key] = {"label": r["label"], "score": 0, "max": max_score,
                            "status": "❌ 미작성", "feedback": ["답안을 작성해 주세요."],
                            "model": r["model_answer"]}
            continue
        wrong_hits = check_wrong_keywords(ans, r.get("wrong_keywords", []))
        if wrong_hits:
            results[key] = {"label": r["label"], "score": 0, "max": max_score,
                            "status": "❌ 오답",
                            "feedback": [f"오개념 키워드 감지: '{', '.join(wrong_hits)}'"],
                            "model": r["model_answer"]}
            continue
        if "required_any" in r:
            if match_required_any(ans, r["required_any"]):
                score = max_score
                feedback.append("✅ 핵심 요소 충족")
            elif "partial_only" in r and contains_any(ans, r["partial_only"]):
                score = max_score // 2
                feedback.append("⚠️ 부분 인정: 핵심 요소 일부 누락")
            else:
                feedback.append("❌ 핵심 요소 미포함")
        elif "required_groups" in r:
            matched = [any(kw in normalize(ans) for kw in g) for g in r["required_groups"]]
            if all(matched):
                score = max_score
                feedback.append("✅ 모든 핵심 요소 충족")
            elif any(matched):
                score = max_score // 2
                missing = [f"그룹{i+1}({'/'.join(r['required_groups'][i])})"
                           for i, m in enumerate(matched) if not m]
