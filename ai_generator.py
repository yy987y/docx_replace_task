from __future__ import annotations

from collections import defaultdict
import json
import os
import random
import re
import subprocess
import tempfile
from pathlib import Path
from urllib import error, request as urllib_request

from codex_prompt import (
    BATCH_OUTPUT_SCHEMA,
    DOUBAO_SYSTEM_PROMPT,
    LOGICAL_FLOW_SYSTEM_PROMPT,
    build_batch_user_prompt,
    build_doubao_batch_user_prompt,
)


NAMES = [
    "糕糕",
    "阳阳",
    "叮当",
    "圆圆",
    "诞诞",
    "又又",
    "樾樾",
    "登登",
    "加加",
    "喜悦",
    "乐诚",
    "君严",
    "汤圆",
    "yoyo",
    "期期",
    "小天",
    "大宝",
    "小宝",
]

FORBIDDEN_CHILD_NAMES = [
    "莫莉",
    "星星",
    "圆子",
    "贝贝",
    "火龙果",
    "点点",
    "想想",
    "雅雅",
    "廖钰雅",
    "哥哥",
]

FORBIDDEN_WORDS = ["开心", "快乐", "认真", "培养", "促进", "提高", "有趣", "！", "!"]
RECENT_SCENES = defaultdict(list)
RECENT_NAME_GROUPS = []
TAG_CALL_COUNT = defaultdict(int)

ACTION_WORDS = [
    "拿",
    "放",
    "走",
    "看",
    "听",
    "说",
    "递",
    "蹲",
    "坐",
    "站",
    "推",
    "摆",
    "洗",
    "擦",
    "咬",
    "喝",
    "装",
    "倒",
    "排",
    "跟",
    "试",
    "指",
    "举",
    "转",
    "放回",
]

RECENT_LLM_SECONDARIES = defaultdict(list)
RECENT_LLM_BLUE_SNIPPETS = defaultdict(list)

TAG_ALIASES = {
    "香香进餐": "午餐",
}


MATERIAL_CONFIG = {
    "室内自主游戏": {
        "materials": [
            {"label": "积木、小车", "items": ["积木", "小车"]},
            {"label": "黏土、扭扭棒", "items": ["黏土", "扭扭棒"]},
            {"label": "串珠、绳子", "items": ["串珠", "绳子"]},
            {"label": "纸杯、木夹", "items": ["纸杯", "木夹"]},
            {"label": "拼图、托盘", "items": ["拼图", "托盘"]},
        ],
    },
    "加点能量": {
        "materials": [
            {"label": "饼干、牛奶", "items": ["饼干", "牛奶"]},
            {"label": "奶酪棒、小杯子", "items": ["奶酪棒", "小杯子"]},
            {"label": "苹果块、小叉子", "items": ["苹果块", "小叉子"]},
            {"label": "蔬菜干、小碗", "items": ["蔬菜干", "小碗"]},
            {"label": "坚果、小盘子", "items": ["坚果", "小盘子"]},
        ],
    },
    "早操律动": {
        "materials": [
            {"label": "球", "items": ["球", "球"]},
            {"label": "纱巾", "items": ["纱巾", "纱巾"]},
            {"label": "响环", "items": ["响环", "响环"]},
            {"label": "小鼓、鼓槌", "items": ["小鼓", "鼓槌"]},
        ],
    },
    "制作": {
        "materials": [
            {"label": "彩纸、胶棒", "items": ["彩纸", "胶棒"]},
            {"label": "海绵印章、颜料", "items": ["海绵印章", "颜料"]},
            {"label": "贴纸、白纸", "items": ["贴纸", "白纸"]},
            {"label": "蜡笔、画纸", "items": ["蜡笔", "画纸"]},
        ],
    },
    "主题活动": {
        "materials": [
            {"label": "图片卡", "items": ["图片卡", "图片"]},
            {"label": "绘本、图片", "items": ["绘本", "图片"]},
            {"label": "水果卡片、小篮子", "items": ["水果卡片", "小篮子"]},
            {"label": "小动物图片、托盘", "items": ["小动物图片", "托盘"]},
        ],
    },
    "户外体育游戏": {
        "materials": [
            {"label": "球、轮滑桩", "items": ["球", "轮滑桩"]},
            {"label": "呼啦圈、地垫", "items": ["呼啦圈", "地垫"]},
            {"label": "隧道筒、垫子", "items": ["隧道筒", "垫子"]},
            {"label": "平衡木、小旗", "items": ["平衡木", "小旗"]},
        ],
    },
    "户外自主游戏": {
        "materials": [
            {"label": "小铲子、小桶", "items": ["小铲子", "小桶"]},
            {"label": "树叶、小篮子", "items": ["树叶", "小篮子"]},
            {"label": "野餐垫、小盘子", "items": ["野餐垫", "小盘子"]},
            {"label": "小车、塑料杯", "items": ["小车", "塑料杯"]},
            {"label": "水盆、小勺子", "items": ["水盆", "小勺子"]},
        ],
    },
    "起床": {
        "materials": [
            {"label": "小被子、鞋子", "items": ["小被子", "鞋子"]},
            {"label": "被子、小袜子", "items": ["被子", "小袜子"]},
            {"label": "枕头、外套", "items": ["枕头", "外套"]},
        ],
    },
    "生活活动": {
        "materials": [
            {"label": "纸巾", "items": ["纸巾", "纸巾"]},
            {"label": "毛巾、水杯", "items": ["毛巾", "水杯"]},
            {"label": "洗手液、毛巾", "items": ["洗手液", "毛巾"]},
            {"label": "小杯子、纸巾", "items": ["小杯子", "纸巾"]},
        ],
    },
    "抱抱离园": {
        "materials": [
            {"label": "外套、书包", "items": ["外套", "书包"]},
            {"label": "水杯、书包", "items": ["水杯", "书包"]},
            {"label": "室外鞋、小书包", "items": ["室外鞋", "小书包"]},
        ],
    },
    "餐前活动": {
        "materials": [
            {"label": "小手、音乐", "items": ["小手", "音乐"]},
            {"label": "图书、地垫", "items": ["图书", "地垫"]},
            {"label": "手指玩偶", "items": ["手指玩偶", "手指玩偶"]},
        ],
    },
    "午餐": {
        "materials": [
            {"label": "勺子、餐盘", "items": ["勺子", "餐盘"]},
            {"label": "米饭、小碗", "items": ["米饭", "小碗"]},
            {"label": "青菜、勺子", "items": ["青菜", "勺子"]},
        ],
    },
    "餐后活动": {
        "materials": [
            {"label": "积木", "items": ["积木", "积木"]},
            {"label": "图书、地垫", "items": ["图书", "地垫"]},
            {"label": "拼图、托盘", "items": ["拼图", "托盘"]},
        ],
    },
}


def _clean_tag(level1: str) -> str:
    return TAG_ALIASES.get(level1.replace("★", ""), level1.replace("★", ""))


def _rng_for(level1: str) -> random.Random:
    clean_level1 = _clean_tag(level1)
    call_index = TAG_CALL_COUNT[level1]
    TAG_CALL_COUNT[level1] += 1
    return random.Random(f"{clean_level1}-{call_index}")


def _pick_names(rng: random.Random, count: int) -> list[str]:
    available = NAMES[:]
    rng.shuffle(available)
    group = tuple(sorted(available[:count]))
    if group in RECENT_NAME_GROUPS and len(available) > count:
        available = available[count:] + available[:count]
        group = tuple(sorted(available[:count]))
    RECENT_NAME_GROUPS.append(group)
    del RECENT_NAME_GROUPS[:-6]
    return list(group)


def _pick_material(cfg: dict, rng: random.Random, tag: str) -> dict:
    recent = RECENT_SCENES[tag]
    candidates = cfg["materials"][:]
    rng.shuffle(candidates)
    for material in candidates:
        if material["label"] not in recent[-3:]:
            recent.append(material["label"])
            del recent[:-6]
            return material
    material = candidates[0]
    recent.append(material["label"])
    del recent[:-6]
    return material


def _normalized_text(text: str) -> str:
    text = re.sub(r"（[^）]*）", "", text)
    return re.sub(r"[\W_]+", "", text)


def _has_significant_overlap(secondary_tag: str, blue_text: str) -> bool:
    sec_core = secondary_tag.split("：", 1)[-1]
    sec_norm = _normalized_text(sec_core)
    blue_norm = _normalized_text(blue_text)
    if not sec_norm or not blue_norm:
        return False
    if sec_norm in blue_norm:
        return True
    max_size = min(len(sec_norm), 12)
    for size in range(max_size, 7, -1):
        for start in range(0, len(sec_norm) - size + 1):
            chunk = sec_norm[start : start + size]
            if chunk and chunk in blue_norm:
                return True
    return False


def _sanitize_secondary(text: str) -> str:
    text = re.sub(r"\s+", "", text)
    text = text.lstrip("：:")
    text = text.rstrip("。.")
    for word in FORBIDDEN_WORDS:
        text = text.replace(word, "")
    return text


def _sanitize_blue(text: str, star: bool) -> str:
    text = text.replace("\n", "").replace("\r", "").strip()
    for word in FORBIDDEN_WORDS:
        text = text.replace(word, "")
    text = re.sub(r"[。]{2,}", "。", text)
    if not text.endswith("。"):
        text += "。"
    max_len = 140 if star else 68
    if len(text) > max_len:
        text = text[:max_len]
        last_period = text.rfind("。")
        if last_period >= max_len * 0.75:
            text = text[: last_period + 1]
    return text


def _extract_source_hint(source_text: str | None, level1: str) -> str:
    if not source_text:
        return ""

    hint = source_text.strip()
    for marker in (level1, level1.replace("★", ""), _clean_tag(level1)):
        if marker and marker in hint:
            hint = hint.split(marker, 1)[1]
            break

    hint = hint.lstrip("：:").strip()
    hint = re.sub(r"\s+", " ", hint)
    if hint in {"", "幼儿进行活动（材料）。幼儿在活动。", "幼儿在活动。"}:
        return ""
    return hint[:120]


def _mentioned_names(text: str) -> list[str]:
    return [name for name in NAMES if name in text]


def _mentioned_forbidden_child_names(text: str) -> list[str]:
    normalized = text.replace("点点头", "点头")
    return [name for name in FORBIDDEN_CHILD_NAMES if name in normalized]


def _chunked(items: list[dict], size: int) -> list[list[dict]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def _ensure_response_care_text(text: str) -> str:
    if re.search(r"通过.*(支持|帮助|引导)(婴幼儿|幼儿)", text):
        return text

    addition = "通过示范轮流递接，帮助婴幼儿继续和同伴一起操作。"
    if not text.endswith("。"):
        text += "。"
    return text + addition


def _load_local_env_files() -> None:
    for filename in (".env.local", ".env"):
        path = Path(filename)
        if not path.exists():
            continue

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_local_env_files()


class BaseActivityGenerator:
    def __init__(self) -> None:
        self.batch_size = max(1, int(os.getenv("DOCX_LLM_BATCH_SIZE", "4")))
        self.timeout = max(30, int(os.getenv("DOCX_LLM_TIMEOUT", "360")))
        self.include_source_hint = os.getenv("DOCX_INCLUDE_SOURCE_HINT", "1") == "1"

    def _rng_suffix(self) -> str:
        return "llm"

    def __call__(self, level1: str, source_text: str | None = None) -> tuple[str, str]:
        return self.batch_generate([{"level1": level1, "source_text": source_text}])[0]

    def batch_generate(self, requests: list[dict]) -> list[tuple[str, str]]:
        prepared = [
            self._prepare_request(index, item["level1"], item.get("source_text"))
            for index, item in enumerate(requests)
        ]
        outputs: list[tuple[str, str]] = []

        for chunk in _chunked(prepared, self.batch_size):
            try:
                outputs.extend(self._generate_chunk(chunk))
            except Exception as chunk_error:
                for request in chunk:
                    try:
                        outputs.extend(self._generate_chunk([request]))
                    except Exception as single_error:
                        raise RuntimeError(
                            f"{request['level1']} 生成失败：{single_error}；批次错误：{chunk_error}"
                        ) from single_error

        return outputs

    def _prepare_request(self, index: int, level1: str, source_text: str | None) -> dict:
        clean_level1 = _clean_tag(level1)
        if clean_level1 not in MATERIAL_CONFIG:
            raise ValueError(f"不支持的一级标签: {level1}")

        suffix = self._rng_suffix()
        rng = _rng_for(f"{level1}-{suffix}")
        cfg = MATERIAL_CONFIG[clean_level1]
        material = _pick_material(cfg, rng, f"{clean_level1}-{suffix}")
        allowed_names = _pick_names(rng, 2)

        needs_response_care = "★" in level1 and clean_level1 == "户外自主游戏"
        blue_range = "90-120字" if "★" in level1 else "30-45字"
        if needs_response_care:
            blue_range = "100-140字"

        return {
            "index": index,
            "level1": level1,
            "clean_level1": clean_level1,
            "age_range": "2岁-3岁",
            "starred": "★" in level1,
            "secondary_char_range": "8-14字优先，最多18字，不要过短",
            "blue_char_range": blue_range,
            "allowed_names": allowed_names,
            "material": material,
            "needs_response_care": needs_response_care,
            "source_hint": _extract_source_hint(source_text, level1)
            if self.include_source_hint
            else "",
            "avoid_recent_secondary": RECENT_LLM_SECONDARIES[clean_level1][-3:],
            "avoid_recent_blue": RECENT_LLM_BLUE_SNIPPETS[clean_level1][-2:],
        }

    def _normalize_payload(self, chunk: list[dict], payload: dict, provider_name: str) -> list[tuple[str, str]]:
        items = payload.get("items")
        if not isinstance(items, list):
            raise ValueError(f"{provider_name} 输出缺少 items: {json.dumps(payload, ensure_ascii=False)[:200]}")
        if len(items) != len(chunk):
            raise ValueError(f"{provider_name} 输出数量不匹配：期望 {len(chunk)}，实际 {len(items)}")

        normalized = []
        items_by_index = {item["index"]: item for item in items}
        for request in chunk:
            item = items_by_index.get(request["index"])
            if item is None:
                raise ValueError(f"{provider_name} 输出缺少 index={request['index']} 的结果")
            secondary, blue = self._normalize_result(request, item)
            normalized.append((secondary, blue))
            RECENT_LLM_SECONDARIES[request["clean_level1"]].append(secondary)
            RECENT_LLM_SECONDARIES[request["clean_level1"]] = RECENT_LLM_SECONDARIES[
                request["clean_level1"]
            ][-6:]
            RECENT_LLM_BLUE_SNIPPETS[request["clean_level1"]].append(blue[:40])
            RECENT_LLM_BLUE_SNIPPETS[request["clean_level1"]] = RECENT_LLM_BLUE_SNIPPETS[
                request["clean_level1"]
            ][-4:]
        return normalized

    def _normalize_result(self, request: dict, item: dict) -> tuple[str, str]:
        secondary = self._sanitize_secondary_text(str(item.get("secondary", "")), request)
        blue = self._sanitize_blue_text(str(item.get("blue", "")), request)

        secondary = re.sub(rf"^{re.escape(request['clean_level1'])}[:：]", "", secondary)
        secondary = secondary.strip("“”\"' ")
        blue = blue.strip("“”\"' ")
        if request["needs_response_care"]:
            blue = _ensure_response_care_text(blue)
        if not blue.endswith("。"):
            blue += "。"

        self._validate_result(request, secondary, blue)
        return secondary, blue

    def _sanitize_secondary_text(self, text: str, request: dict) -> str:
        return _sanitize_secondary(text)

    def _sanitize_blue_text(self, text: str, request: dict) -> str:
        return _sanitize_blue(text, request["starred"])

    def _secondary_length_bounds(self, request: dict) -> tuple[int, int]:
        return 7, 18

    def _blue_length_bounds(self, request: dict) -> tuple[int, int]:
        min_blue_len = 24 if not request["starred"] else 72
        max_blue_len = 70 if not request["starred"] else 145
        if request["needs_response_care"]:
            min_blue_len = 96
            max_blue_len = 190
        return min_blue_len, max_blue_len

    def _validate_result(self, request: dict, secondary: str, blue: str) -> None:
        min_secondary_len, max_secondary_len = self._secondary_length_bounds(request)
        if not secondary or len(secondary) < min_secondary_len or len(secondary) > max_secondary_len:
            raise ValueError(f"小目标长度异常: {secondary}")
        if "。" in secondary or "\n" in secondary:
            raise ValueError(f"小目标格式异常: {secondary}")
        if not blue or "\n" in blue:
            raise ValueError("正文为空或包含换行")
        if not any(word in blue for word in ACTION_WORDS):
            raise ValueError(f"正文缺少动作感: {blue}")
        if _has_significant_overlap(secondary, blue):
            raise ValueError(f"小目标和正文重复度过高: {secondary} / {blue}")

        forbidden_names = _mentioned_forbidden_child_names(f"{secondary}。{blue}")
        if forbidden_names:
            raise ValueError(f"输出包含旧名字池名字: {forbidden_names}")

        mentioned = _mentioned_names(blue)
        mentioned_unique = list(dict.fromkeys(mentioned))
        if not mentioned_unique:
            raise ValueError(f"正文缺少幼儿名字: {blue}")
        if len(mentioned_unique) > 2:
            raise ValueError(f"正文出现超过 2 个名字: {blue}")
        if any(name not in request["allowed_names"] for name in mentioned_unique):
            raise ValueError(
                f"正文使用了未授权名字: {mentioned_unique}，允许={request['allowed_names']}"
            )

        min_blue_len, max_blue_len = self._blue_length_bounds(request)
        if len(blue) < min_blue_len or len(blue) > max_blue_len:
            raise ValueError(f"正文长度异常({len(blue)}): {blue}")

        if request["needs_response_care"] and not re.search(r"通过.*(支持|帮助|引导)(婴幼儿|幼儿)", blue):
            raise ValueError(f"户外自主游戏缺少回应性照护: {blue}")

    def _generate_chunk(self, chunk: list[dict]) -> list[tuple[str, str]]:
        raise NotImplementedError


class CodexActivityGenerator(BaseActivityGenerator):
    def __init__(self) -> None:
        super().__init__()
        self.codex_bin = os.getenv("DOCX_CODEX_BIN", "codex")
        self.codex_model = os.getenv("DOCX_CODEX_MODEL", "").strip()
        self.batch_size = max(1, int(os.getenv("DOCX_CODEX_BATCH_SIZE", str(self.batch_size))))
        self.timeout = max(30, int(os.getenv("DOCX_CODEX_TIMEOUT", str(self.timeout))))
        self.sandbox = os.getenv("DOCX_CODEX_SANDBOX", "read-only")
        self.workdir = os.getenv("DOCX_CODEX_WORKDIR", "/tmp")
        self.reasoning_effort = os.getenv("DOCX_CODEX_REASONING_EFFORT", "high").strip()
        self._schema_path: str | None = None

    def _rng_suffix(self) -> str:
        return "codex"

    def _schema_path_for_batch(self) -> str:
        if self._schema_path:
            return self._schema_path

        fd, path = tempfile.mkstemp(prefix="docx_replace_schema_", suffix=".json")
        os.close(fd)
        Path(path).write_text(
            json.dumps(BATCH_OUTPUT_SCHEMA, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._schema_path = path
        return path

    def _generate_chunk(self, chunk: list[dict]) -> list[tuple[str, str]]:
        prompt = f"{LOGICAL_FLOW_SYSTEM_PROMPT}\n\n{build_batch_user_prompt(chunk)}"
        schema_path = self._schema_path_for_batch()

        fd, output_path = tempfile.mkstemp(prefix="docx_replace_output_", suffix=".json")
        os.close(fd)

        cmd = [
            self.codex_bin,
            "exec",
            "--color",
            "never",
            "--skip-git-repo-check",
            "--ephemeral",
            "--sandbox",
            self.sandbox,
            "-C",
            self.workdir,
            "--output-schema",
            schema_path,
            "-o",
            output_path,
        ]
        if self.reasoning_effort:
            cmd.extend(["-c", f'model_reasoning_effort="{self.reasoning_effort}"'])
        if self.codex_model:
            cmd.extend(["-m", self.codex_model])
        cmd.append("-")

        completed = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=self.timeout,
            check=False,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            stdout = completed.stdout.strip()
            raise RuntimeError(
                f"codex exec 失败，exit={completed.returncode}，stderr={stderr[-400:]}，stdout={stdout[-400:]}"
            )

        raw_output = Path(output_path).read_text(encoding="utf-8").strip()
        payload = json.loads(raw_output)
        return self._normalize_payload(chunk, payload, "Codex")


class ArkActivityGenerator(BaseActivityGenerator):
    BAD_SECONDARY_PHRASES = ("重点观察", "观察记录", "生活观察", "教学")
    BAD_BLUE_PHRASES = (
        "再按顺序做下一步",
        "再继续完成接下来的动作",
        "再听提示做后面的动作",
        "把东西放好后",
        "转过身后",
    )

    def __init__(self) -> None:
        super().__init__()
        self.api_key = os.getenv("DOCX_ARK_API_KEY") or os.getenv("ARK_API_KEY", "")
        self.base_url = os.getenv("DOCX_ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
        self.model = os.getenv("DOCX_ARK_MODEL", "doubao-seed-2-0-lite-260215").strip()
        self.reasoning_effort = os.getenv("DOCX_ARK_REASONING_EFFORT", "medium").strip()
        self.batch_size = max(1, int(os.getenv("DOCX_ARK_BATCH_SIZE", str(self.batch_size))))
        self.timeout = max(30, int(os.getenv("DOCX_ARK_TIMEOUT", str(self.timeout))))

    def _rng_suffix(self) -> str:
        return "ark"

    def _sanitize_secondary_text(self, text: str, request: dict) -> str:
        text = re.sub(r"\s+", "", text)
        text = text.lstrip("：:").rstrip("。.")
        text = re.sub(rf"^{re.escape(request['clean_level1'])}[:：]", "", text)
        if "：" in text or ":" in text:
            text = re.split(r"[:：]", text, 1)[0]
        return text.strip("“”\"' ")

    def _sanitize_blue_text(self, text: str, request: dict) -> str:
        text = text.replace("\n", "").replace("\r", "").strip()
        text = re.sub(r"[。]{2,}", "。", text)
        if not text.endswith("。"):
            text += "。"
        return text

    def _secondary_length_bounds(self, request: dict) -> tuple[int, int]:
        return 4, 30

    def _blue_length_bounds(self, request: dict) -> tuple[int, int]:
        if request["needs_response_care"]:
            return 55, 300
        if request["starred"]:
            return 45, 260
        return 18, 180

    def _validate_result(self, request: dict, secondary: str, blue: str) -> None:
        if any(phrase in secondary for phrase in self.BAD_SECONDARY_PHRASES):
            raise ValueError(f"豆包小目标过于模板化: {secondary}")
        if any(phrase in blue for phrase in self.BAD_BLUE_PHRASES):
            raise ValueError(f"豆包正文出现模板动作链: {blue}")
        super()._validate_result(request, secondary, blue)

    def _generate_chunk(self, chunk: list[dict]) -> list[tuple[str, str]]:
        if not self.api_key:
            raise RuntimeError("未配置豆包 API Key，请设置 DOCX_ARK_API_KEY 或 ARK_API_KEY")

        prompt = build_doubao_batch_user_prompt(chunk)
        payload = self._request_completion(prompt)
        return self._normalize_payload(chunk, payload, "豆包")

    def _request_completion(self, prompt: str) -> dict:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": DOUBAO_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        }
        if self.reasoning_effort:
            body["reasoning_effort"] = self.reasoning_effort

        request_body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib_request.Request(
            f"{self.base_url}/chat/completions",
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib_request.urlopen(req, timeout=self.timeout) as response:
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"豆包请求失败，status={exc.code}，body={detail[-400:]}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"豆包请求失败：{exc.reason}") from exc

        try:
            response_payload = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"豆包返回非 JSON：{raw_body[:200]}") from exc

        content = self._extract_message_content(response_payload)
        return self._parse_model_json(content)

    def _extract_message_content(self, response_payload: dict) -> str:
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError(f"豆包返回缺少 choices: {json.dumps(response_payload, ensure_ascii=False)[:200]}")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(str(item.get("text", "")))
            text = "".join(parts).strip()
            if text:
                return text

        raise ValueError(f"豆包返回缺少文本 content: {json.dumps(message, ensure_ascii=False)[:200]}")

    def _parse_model_json(self, content: str) -> dict:
        stripped = content.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```json\s*", "", stripped)
            stripped = re.sub(r"^```\s*", "", stripped)
            stripped = re.sub(r"\s*```$", "", stripped)
            stripped = stripped.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError as exc:
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start != -1 and end != -1 and start < end:
                try:
                    return json.loads(stripped[start : end + 1])
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"豆包输出不是合法 JSON：{content[:200]}") from exc


class FallbackActivityGenerator:
    def __init__(self, primary, fallback, primary_name: str, fallback_name: str) -> None:
        self.primary = primary
        self.fallback = fallback
        self.primary_name = primary_name
        self.fallback_name = fallback_name

    def __call__(self, level1: str, source_text: str | None = None) -> tuple[str, str]:
        return self.batch_generate([{"level1": level1, "source_text": source_text}])[0]

    def batch_generate(self, requests: list[dict]) -> list[tuple[str, str]]:
        try:
            return self.primary.batch_generate(requests)
        except Exception as primary_error:
            print(
                f"{self.primary_name} 调用失败，自动回退到 {self.fallback_name}：{primary_error}"
            )
            return self.fallback.batch_generate(requests)


def _create_generator(provider: str):
    if provider == "codex":
        return CodexActivityGenerator()
    if provider == "ark":
        return ArkActivityGenerator()
    raise ValueError(f"不支持的 LLM provider: {provider}")


def build_ai_generator():
    provider = os.getenv("DOCX_LLM_PROVIDER", "ark").strip().lower()
    fallback_provider = os.getenv("DOCX_LLM_FALLBACK_PROVIDER", "").strip().lower()
    generator = _create_generator(provider)
    if fallback_provider and fallback_provider != provider:
        fallback_generator = _create_generator(fallback_provider)
        return FallbackActivityGenerator(generator, fallback_generator, provider, fallback_provider)
    return generator


ai_generator = build_ai_generator()
