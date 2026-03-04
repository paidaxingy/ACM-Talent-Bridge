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
    standard_answer: str | None = None


@dataclass(frozen=True)
class AnswerEvaluation:
    score: int
    strengths: str
    weaknesses: str
    suggestions: str
    raw: str | None = None


@dataclass(frozen=True)
class ChatQuestion:
    question: str
    difficulty: str | None = None


@dataclass(frozen=True)
class ChatTurnEvaluation:
    score: int
    standard_answer: str
    strengths: str
    weaknesses: str
    suggestions: str
    next_question: str | None = None
    next_difficulty: str | None = None
    raw: str | None = None


@dataclass(frozen=True)
class MemberAIProfileResult:
    competitive_strength: int
    consistency: int
    communication: int
    problem_solving: int
    recommended_directions: list[dict]
    improvement_plan: list[str]
    persona_summary: str
    raw: str | None = None


class AIProvider:
    def generate_questions(
        self,
        profile: dict,
        *,
        num_questions: int,
        target_role: str | None,
        resume_text: str | None,
    ) -> list[InterviewQuestionItem]:
        raise NotImplementedError

    def evaluate_answer(self, profile: dict, *, question: str, answer: str) -> AnswerEvaluation:
        raise NotImplementedError

    def start_chat_interview(
        self,
        profile: dict,
        *,
        target_role: str | None,
        resume_text: str,
    ) -> ChatQuestion:
        raise NotImplementedError

    def evaluate_and_followup(
        self,
        profile: dict,
        *,
        target_role: str | None,
        resume_text: str,
        history: list[dict],
        current_question: str,
        candidate_answer: str,
        is_last_round: bool,
    ) -> ChatTurnEvaluation:
        raise NotImplementedError

    def generate_member_ai_profile(self, profile: dict, *, resume_text: str | None) -> MemberAIProfileResult:
        raise NotImplementedError


class MockProvider(AIProvider):
    def generate_questions(
        self,
        profile: dict,
        *,
        num_questions: int,
        target_role: str | None,
        resume_text: str | None,
    ) -> list[InterviewQuestionItem]:
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
            qs.append(
                InterviewQuestionItem(
                    question=f"[{role}] {q}",
                    topic=topic,
                    difficulty=level,
                    standard_answer="建议从定义、核心思路、复杂度、边界条件和示例五个层次回答，并给出可落地实现。",
                )
            )
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

    def start_chat_interview(
        self,
        profile: dict,
        *,
        target_role: str | None,
        resume_text: str,
    ) -> ChatQuestion:
        role = target_role or "软件开发/算法工程师"
        question = f"请你先做一个 1 分钟自我介绍，重点说明与你申请的 {role} 相关的项目经历。"
        return ChatQuestion(question=question, difficulty="easy")

    def evaluate_and_followup(
        self,
        profile: dict,
        *,
        target_role: str | None,
        resume_text: str,
        history: list[dict],
        current_question: str,
        candidate_answer: str,
        is_last_round: bool,
    ) -> ChatTurnEvaluation:
        text = candidate_answer.strip()
        length = len(text)
        score = 50 if length < 40 else 68 if length < 100 else 80 if length < 220 else 88
        strengths = "表达清晰，结构较完整" if length >= 100 else "回答简洁，有核心信息"
        weaknesses = "建议补充量化结果与技术细节" if length < 180 else "可进一步补充边界与权衡"
        suggestions = "建议按：背景-目标-行动-结果（STAR）方式作答。"
        standard_answer = "优秀回答应包含：场景背景、你的职责、关键技术决策、结果指标、复盘改进。"
        next_question = None if is_last_round else "请详细说明你在该项目中最难的一次技术问题，以及你如何定位并解决。"
        next_difficulty = None if is_last_round else "medium"
        return ChatTurnEvaluation(
            score=score,
            standard_answer=standard_answer,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            next_question=next_question,
            next_difficulty=next_difficulty,
            raw=json.dumps({"mock": True, "length": length}, ensure_ascii=False),
        )

    def generate_member_ai_profile(self, profile: dict, *, resume_text: str | None) -> MemberAIProfileResult:
        def _clamp(v: int) -> int:
            return max(0, min(100, int(v)))

        base_comp = _clamp(profile.get("competitive_strength", 60))
        base_cons = _clamp(profile.get("consistency", 55))
        base_comm = _clamp(profile.get("communication", 60))
        base_prob = _clamp(profile.get("problem_solving", 58))

        recommended = profile.get("recommended_directions") or [
            {"direction": "后端开发", "reason": "建议先夯实数据结构、系统设计与工程实践。"}
        ]
        plan = profile.get("improvement_plan") or ["每周完成阶段复盘，并沉淀可复用的解题与工程模板。"]
        summary = "你具备一定训练基础，建议继续强化项目表达与工程细节，逐步提升稳定输出能力。"
        if resume_text:
            summary = "你的简历体现了真实项目与竞赛经历，后续重点在于量化成果表达和关键技术取舍说明。"

        return MemberAIProfileResult(
            competitive_strength=base_comp,
            consistency=base_cons,
            communication=base_comm,
            problem_solving=base_prob,
            recommended_directions=recommended[:3],
            improvement_plan=[str(x) for x in plan][:6],
            persona_summary=summary,
            raw=json.dumps({"mock": True}, ensure_ascii=False),
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
        try:
            with httpx.Client(timeout=90) as client:
                r = client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
        except httpx.ReadTimeout as e:
            raise RuntimeError("AI 服务响应超时，请稍后重试") from e
        except httpx.HTTPStatusError as e:
            body = e.response.text[:300] if e.response is not None else ""
            raise RuntimeError(f"AI 服务返回异常状态：{e.response.status_code if e.response else 'unknown'} {body}") from e
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"调用 AI 服务失败：{e}") from e
        return data["choices"][0]["message"]["content"]

    def _extract_question_from_text(self, content: str) -> str | None:
        text = (content or "").strip()
        if not text:
            return None

        def _question_from_json(raw: str) -> str | None:
            try:
                obj = json.loads(raw)
            except Exception:  # noqa: BLE001
                return None
            if isinstance(obj, dict):
                q = obj.get("question")
                if isinstance(q, str) and q.strip():
                    return q.strip()
            if isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        q = item.get("question")
                        if isinstance(q, str) and q.strip():
                            return q.strip()
            return None

        # 1) strict json content
        q = _question_from_json(text)
        if q:
            return q

        # 2) markdown code fence with json
        if "```" in text:
            start = text.find("```")
            end = text.find("```", start + 3)
            if end != -1:
                fenced = text[start + 3 : end].strip()
                if fenced.lower().startswith("json"):
                    fenced = fenced[4:].strip()
                q = _question_from_json(fenced)
                if q:
                    return q

        # 3) loose fallback by key extraction
        marker = '"question"'
        idx = text.find(marker)
        if idx != -1:
            tail = text[idx + len(marker) :]
            colon = tail.find(":")
            if colon != -1:
                raw_val = tail[colon + 1 :].strip().lstrip('"')
                end_quote = raw_val.find('"')
                if end_quote > 0:
                    candidate = raw_val[:end_quote].strip()
                    if candidate:
                        return candidate

        return None

    def _extract_json_object(self, content: str) -> dict | None:
        text = (content or "").strip()
        if not text:
            return None

        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                return obj
        except Exception:  # noqa: BLE001
            pass

        fence_match = None
        if "```" in text:
            import re

            fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
        if fence_match:
            fenced = (fence_match.group(1) or "").strip()
            try:
                obj = json.loads(fenced)
                if isinstance(obj, dict):
                    return obj
            except Exception:  # noqa: BLE001
                pass

        # try to parse the first {...} block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            maybe = text[start : end + 1]
            try:
                obj = json.loads(maybe)
                if isinstance(obj, dict):
                    return obj
            except Exception:  # noqa: BLE001
                return None
        return None

    def generate_questions(
        self,
        profile: dict,
        *,
        num_questions: int,
        target_role: str | None,
        resume_text: str | None,
    ) -> list[InterviewQuestionItem]:
        role = target_role or "软件开发/算法工程"
        prompt = (
            "你是资深技术面试官。根据候选人的竞赛画像，为其生成个性化算法/工程面试题。\n"
            f"目标岗位：{role}\n"
            f"候选人画像（JSON）：{json.dumps(profile, ensure_ascii=False)}\n\n"
            f"候选人简历文本（可能为空）：{resume_text or '（未提供简历）'}\n\n"
            "请输出严格 JSON 数组，每个元素包含：question, topic, difficulty(easy|medium|hard), standard_answer。\n"
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
                        standard_answer=(str(it.get("standard_answer")).strip() if it.get("standard_answer") else None),
                    )
                )
            return [q for q in out if q.question]
        except Exception:  # noqa: BLE001 (LLM output may be imperfect)
            # fallback: wrap raw content as a single question list
            return [
                InterviewQuestionItem(
                    question=content.strip(),
                    topic="mixed",
                    difficulty="medium",
                    standard_answer="请按概念、实现、复杂度、边界和示例结构化作答。",
                )
            ]

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

    def start_chat_interview(
        self,
        profile: dict,
        *,
        target_role: str | None,
        resume_text: str,
    ) -> ChatQuestion:
        role = target_role or "软件开发/算法工程师"
        prompt = (
            "你是一位严谨但友好的技术面试官。请基于候选人简历发起第一轮问题。\n"
            f"目标岗位：{role}\n"
            f"候选人画像（JSON）：{json.dumps(profile, ensure_ascii=False)}\n"
            f"候选人简历文本：{resume_text}\n\n"
            "请严格输出 JSON 对象，字段：question, difficulty(easy|medium|hard)。\n"
            "要求：优先基于简历中的项目经历/技术栈/职责发问，不要把 AC 率或提交统计作为首轮主问题；"
            "同时允许围绕简历技能做相关基础知识追问（八股），例如简历提到 C++，可问内存模型、RAII、智能指针、虚函数、并发基础；"
            "问题要短而聚焦，避免一次性抛多个问题。"
        )
        content = self._post_chat([{"role": "user", "content": prompt}], temperature=0.4)
        try:
            obj = json.loads(content)
            question = str(obj.get("question", "")).strip()
            if not question:
                question = self._extract_question_from_text(content) or "请做一个简短自我介绍。"
            return ChatQuestion(
                question=question,
                difficulty=(str(obj.get("difficulty")).strip() if obj.get("difficulty") else "medium"),
            )
        except Exception:  # noqa: BLE001
            question = self._extract_question_from_text(content) or content.strip() or "请做一个简短自我介绍。"
            return ChatQuestion(question=question, difficulty="medium")

    def evaluate_and_followup(
        self,
        profile: dict,
        *,
        target_role: str | None,
        resume_text: str,
        history: list[dict],
        current_question: str,
        candidate_answer: str,
        is_last_round: bool,
    ) -> ChatTurnEvaluation:
        role = target_role or "软件开发/算法工程师"
        prompt = (
            "你是一位技术面试官，请对本轮回答评分并决定下一轮提问。\n"
            f"目标岗位：{role}\n"
            f"候选人画像（JSON）：{json.dumps(profile, ensure_ascii=False)}\n"
            f"候选人简历文本：{resume_text}\n"
            f"历史对话（JSON）：{json.dumps(history, ensure_ascii=False)}\n"
            f"当前问题：{current_question}\n"
            f"候选人回答：{candidate_answer}\n"
            f"是否最后一轮：{is_last_round}\n\n"
            "请严格输出 JSON 对象，字段：score(0-100), standard_answer, strengths, weaknesses, suggestions, "
            "next_question, next_difficulty(easy|medium|hard)。\n"
            "若为最后一轮，next_question 置为空字符串。"
            "下一问必须紧贴简历项目细节或候选人上一轮回答中的技术点，也可以延展到该技术栈的基础知识追问（八股）；"
            "不要重复问 AC 率/提交统计。"
        )
        content = self._post_chat([{"role": "user", "content": prompt}], temperature=0.2)
        try:
            obj = self._extract_json_object(content) or {}
            next_question = str(obj.get("next_question", "")).strip() or None
            if is_last_round:
                next_question = None
            return ChatTurnEvaluation(
                score=int(obj.get("score", 0)),
                standard_answer=str(obj.get("standard_answer", "")),
                strengths=str(obj.get("strengths", "")),
                weaknesses=str(obj.get("weaknesses", "")),
                suggestions=str(obj.get("suggestions", "")),
                next_question=next_question,
                next_difficulty=(str(obj.get("next_difficulty")).strip() if obj.get("next_difficulty") else None),
                raw=content,
            )
        except Exception:  # noqa: BLE001
            answer_len = len(candidate_answer.strip())
            fallback_score = 45 if answer_len < 30 else 60 if answer_len < 100 else 75
            if is_last_round:
                next_question = None
            elif answer_len < 60:
                next_question = "你的回答有些概括，请补充一个具体场景：你的目标、做法、结果指标分别是什么？"
            else:
                next_question = "请给出一个你亲自排查并解决问题的完整案例，按背景-问题-定位-修复-结果来说明。"
            return ChatTurnEvaluation(
                score=fallback_score,
                standard_answer="建议给出具体案例，并包含目标、方案选择、关键细节和量化结果。",
                strengths="回答覆盖了部分关键点",
                weaknesses="细节与量化结果不足，缺少完整的问题定位过程",
                suggestions="按 STAR 或 背景-问题-行动-结果 结构回答，并补充指标/日志/对比数据。",
                next_question=next_question,
                next_difficulty="medium",
                raw=content,
            )

    def generate_member_ai_profile(self, profile: dict, *, resume_text: str | None) -> MemberAIProfileResult:
        prompt = (
            "你是高校 ACM 成员培养与求职辅导专家，请生成该成员的能力画像结论。\n"
            f"成员画像基础数据（JSON）：{json.dumps(profile, ensure_ascii=False)}\n"
            f"简历文本（可能为空）：{resume_text or '（未提供）'}\n\n"
            "输出要求：严格 JSON 对象，字段如下：\n"
            "- competitive_strength: 0-100 整数\n"
            "- consistency: 0-100 整数\n"
            "- communication: 0-100 整数\n"
            "- problem_solving: 0-100 整数\n"
            "- recommended_directions: 数组，每项包含 direction, reason\n"
            "- improvement_plan: 数组，每项是一条可执行建议\n"
            "- persona_summary: 80-180字中文总结\n"
            "规则：\n"
            "1) 结论要与输入数据一致，不要凭空编造经历；\n"
            "2) 推荐方向不超过3条，提升计划不超过6条；\n"
            "3) 若简历中有技术栈/项目，结论应体现对应方向。"
        )
        content = self._post_chat([{"role": "user", "content": prompt}], temperature=0.2)
        try:
            obj = self._extract_json_object(content) or {}

            def _clamp(v: int) -> int:
                return max(0, min(100, int(v)))

            recommended = obj.get("recommended_directions") or []
            if not isinstance(recommended, list):
                recommended = []
            normalized_recommended: list[dict] = []
            for item in recommended[:3]:
                if not isinstance(item, dict):
                    continue
                direction = str(item.get("direction", "")).strip()
                reason = str(item.get("reason", "")).strip()
                if direction and reason:
                    normalized_recommended.append({"direction": direction, "reason": reason})

            improvement = obj.get("improvement_plan") or []
            if not isinstance(improvement, list):
                improvement = []
            normalized_plan = [str(x).strip() for x in improvement if str(x).strip()][:6]

            summary = str(obj.get("persona_summary", "")).strip()
            if not summary:
                summary = "当前画像生成成功，但总结文本较短，建议结合近期训练和项目经历继续补充。"

            return MemberAIProfileResult(
                competitive_strength=_clamp(obj.get("competitive_strength", profile.get("competitive_strength", 60))),
                consistency=_clamp(obj.get("consistency", profile.get("consistency", 55))),
                communication=_clamp(obj.get("communication", profile.get("communication", 60))),
                problem_solving=_clamp(obj.get("problem_solving", profile.get("problem_solving", 58))),
                recommended_directions=normalized_recommended
                or (profile.get("recommended_directions") if isinstance(profile.get("recommended_directions"), list) else []),
                improvement_plan=normalized_plan
                or ([str(x) for x in profile.get("improvement_plan", []) if str(x).strip()][:6]),
                persona_summary=summary,
                raw=content,
            )
        except Exception:  # noqa: BLE001
            return MemberAIProfileResult(
                competitive_strength=max(0, min(100, int(profile.get("competitive_strength", 60)))),
                consistency=max(0, min(100, int(profile.get("consistency", 55)))),
                communication=max(0, min(100, int(profile.get("communication", 60)))),
                problem_solving=max(0, min(100, int(profile.get("problem_solving", 58)))),
                recommended_directions=(
                    profile.get("recommended_directions")
                    if isinstance(profile.get("recommended_directions"), list)
                    else [{"direction": "后端开发", "reason": "建议补齐工程实践并强化系统设计能力。"}]
                ),
                improvement_plan=[
                    str(x) for x in (profile.get("improvement_plan") or ["保持周训练节奏并强化复盘质量。"]) if str(x).strip()
                ][:6],
                persona_summary="已保留基础画像，AI 输出解析失败，建议稍后重试生成更细粒度结论。",
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
        raise RuntimeError("AI provider is enabled but AI_BASE_URL or AI_API_KEY is missing")
    return OpenAICompatibleProvider(base_url=base_url, api_key=api_key, model=model)

