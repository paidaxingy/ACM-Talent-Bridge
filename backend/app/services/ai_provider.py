from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass(frozen=True)
class InterviewQuestionItem:
    question: str
    topic: str | None = None
    difficulty: str | None = None


@dataclass(frozen=True)
class AnswerEvaluation:
    score: int
    strengths: str
    weaknesses: str
    suggestions: str
    raw: str | None = None


class AIProvider:
    def generate_questions(self, profile: dict, *, num_questions: int, target_role: str | None) -> list[InterviewQuestionItem]:
        raise NotImplementedError

    def evaluate_answer(self, profile: dict, *, question: str, answer: str) -> AnswerEvaluation:
        raise NotImplementedError


class MockProvider(AIProvider):
    def generate_questions(self, profile: dict, *, num_questions: int, target_role: str | None) -> list[InterviewQuestionItem]:
        rating = int(profile.get("rating") or 1500)
        level = "easy" if rating < 1400 else "medium" if rating < 1800 else "hard"
        role = target_role or "软件开发/算法工程"

        base = [
            ("请解释时间复杂度与空间复杂度，并举例说明如何分析一个算法。", "complexity"),
            ("给定一个数组，如何在 O(n) 时间内找到最大子数组和？请说明思路。", "dp"),
            ("解释哈希表的冲突处理方式，并分析不同方式的优缺点。", "data-structures"),
            ("描述 BFS 与 DFS 的差异及典型应用场景。", "graph"),
            ("你在竞赛中遇到过最困难的问题是什么？你是如何拆解并解决的？", "experience"),
        ]

        qs: list[InterviewQuestionItem] = []
        for i in range(num_questions):
            q, topic = base[i % len(base)]
            qs.append(InterviewQuestionItem(question=f"[{role}] {q}", topic=topic, difficulty=level))
        return qs

    def evaluate_answer(self, profile: dict, *, question: str, answer: str) -> AnswerEvaluation:
        text = answer.strip()
        length = len(text)
        if length < 30:
            score = 45
        elif length < 80:
            score = 60
        elif length < 200:
            score = 75
        else:
            score = 85

        strengths = "回答结构清晰" if length >= 80 else "回答简洁"
        weaknesses = "细节不足（建议补充例子/复杂度/边界情况）" if length < 120 else "可进一步给出更严谨的证明或复杂度分析"
        suggestions = "建议按：定义 → 思路 → 复杂度 → 边界情况 → 示例 的顺序作答。"
        raw = json.dumps({"mock": True, "length": length, "rating": profile.get("rating")}, ensure_ascii=False)

        return AnswerEvaluation(
            score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            raw=raw,
        )


class OpenAICompatibleProvider(AIProvider):
    """
    OpenAI-compatible Chat Completions provider.

    Requires:
    - AI_BASE_URL (e.g. https://api.openai.com) or a compatible gateway
    - AI_API_KEY
    - AI_MODEL (optional; defaults to gpt-4o-mini)
    """

    def __init__(self, base_url: str, api_key: str, model: str = "gpt-4o-mini"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def _post_chat(self, messages: list[dict], *, temperature: float = 0.2) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": self.model, "messages": messages, "temperature": temperature}
        with httpx.Client(timeout=30) as client:
            r = client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        return data["choices"][0]["message"]["content"]

    def generate_questions(self, profile: dict, *, num_questions: int, target_role: str | None) -> list[InterviewQuestionItem]:
        role = target_role or "软件开发/算法工程"
        prompt = (
            "你是资深技术面试官。根据候选人的竞赛画像，为其生成个性化算法/工程面试题。\n"
            f"目标岗位：{role}\n"
            f"候选人画像（JSON）：{json.dumps(profile, ensure_ascii=False)}\n\n"
            "请输出严格 JSON 数组，每个元素包含：question, topic, difficulty(easy|medium|hard)。\n"
            f"题目数量：{num_questions}\n"
        )
        content = self._post_chat([{"role": "user", "content": prompt}], temperature=0.4)
        try:
            arr = json.loads(content)
            out: list[InterviewQuestionItem] = []
            for it in arr[:num_questions]:
                out.append(
                    InterviewQuestionItem(
                        question=str(it.get("question", "")).strip(),
                        topic=(str(it.get("topic")).strip() if it.get("topic") else None),
                        difficulty=(str(it.get("difficulty")).strip() if it.get("difficulty") else None),
                    )
                )
            return [q for q in out if q.question]
        except Exception:  # noqa: BLE001 (LLM output may be imperfect)
            # fallback: wrap raw content as a single question list
            return [InterviewQuestionItem(question=content.strip(), topic="mixed", difficulty="medium")]

    def evaluate_answer(self, profile: dict, *, question: str, answer: str) -> AnswerEvaluation:
        prompt = (
            "你是技术面试官，请对候选人的回答做结构化评价。\n"
            f"候选人画像（JSON）：{json.dumps(profile, ensure_ascii=False)}\n"
            f"面试题：{question}\n"
            f"回答：{answer}\n\n"
            "请输出严格 JSON，字段：score(0-100), strengths, weaknesses, suggestions。\n"
        )
        content = self._post_chat([{"role": "user", "content": prompt}], temperature=0.2)
        try:
            obj = json.loads(content)
            return AnswerEvaluation(
                score=int(obj.get("score", 0)),
                strengths=str(obj.get("strengths", "")),
                weaknesses=str(obj.get("weaknesses", "")),
                suggestions=str(obj.get("suggestions", "")),
                raw=content,
            )
        except Exception:  # noqa: BLE001
            return AnswerEvaluation(
                score=0,
                strengths="",
                weaknesses="",
                suggestions="",
                raw=content,
            )


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    if settings.ai_provider.lower() == "mock":
        return MockProvider()

    base_url = (settings.ai_base_url or "").strip()
    api_key = (settings.ai_api_key or "").strip()
    model = (getattr(settings, "ai_model", None) or "gpt-4o-mini").strip()
    if not base_url or not api_key:
        return MockProvider()
    return OpenAICompatibleProvider(base_url=base_url, api_key=api_key, model=model)

