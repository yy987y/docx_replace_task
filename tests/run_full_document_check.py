import argparse
from collections import defaultdict
import io
import os
import re
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_generator import MATERIAL_CONFIG, TAG_ALIASES, ai_generator
from replace_word import KNOWN_LEVEL1_TAGS, is_level1_para, process_document
from spire.doc import Document


KNOWN_TAGS = KNOWN_LEVEL1_TAGS[:]
KNOWN_ITEMS = sorted(
    {
        item
        for tag_config in MATERIAL_CONFIG.values()
        for material in tag_config["materials"]
        for item in material["items"]
    },
    key=len,
    reverse=True,
)


def collect_activity_texts(doc_path: Path):
    doc = Document()
    doc.LoadFromFile(str(doc_path))
    texts = []

    try:
        for sec_idx in range(doc.Sections.Count):
            sec = doc.Sections[sec_idx]
            for obj_idx in range(sec.Body.ChildObjects.Count):
                obj = sec.Body.ChildObjects[obj_idx]
                if not hasattr(obj, "ChildObjects"):
                    continue
                for child_idx in range(obj.ChildObjects.Count):
                    child = obj.ChildObjects[child_idx]
                    if not hasattr(child, "Body") or not child.Body:
                        continue
                    for p_idx in range(child.Body.Paragraphs.Count):
                        paragraph = child.Body.Paragraphs[p_idx]
                        level1 = is_level1_para(paragraph)
                        if level1:
                            texts.append(paragraph.Text.strip())
    finally:
        doc.Close()

    return texts


def count_labels(texts):
    counts = {TAG_ALIASES.get(tag, tag): 0 for tag in KNOWN_TAGS}
    for text in texts:
        for tag in KNOWN_TAGS:
            if f"★{tag}" in text or tag in text:
                counts[TAG_ALIASES.get(tag, tag)] += 1
                break
    return counts


def normalized_text(text):
    text = re.sub(r"（[^）]*）", "", text)
    return re.sub(r"[\W_]+", "", text)


def secondary_skeleton(text):
    text = re.sub(r"（[^）]*）", "", text)
    for item in KNOWN_ITEMS:
        text = text.replace(item, "<ITEM>")
    text = re.sub(r"\s+", "", text)
    return text


def has_significant_overlap(secondary, blue):
    sec_core = secondary.split("：", 1)[-1]
    sec_norm = normalized_text(sec_core)
    blue_norm = normalized_text(blue)
    if not sec_norm or not blue_norm:
        return False
    if sec_norm in blue_norm:
        return True
    max_size = min(len(sec_norm), 12)
    for size in range(max_size, 7, -1):
        for start in range(0, len(sec_norm) - size + 1):
            if sec_norm[start : start + size] in blue_norm:
                return True
    return False


def find_over_limit_examples(counter_map, limit):
    return {
        key: values
        for key, values in counter_map.items()
        if len(values) > limit
    }


def assert_output_quality(input_texts, output_texts, output_doc, log_text):
    if len(input_texts) != len(output_texts):
        raise AssertionError(
            f"活动段落数量不一致：输入 {len(input_texts)}，输出 {len(output_texts)}。"
        )

    input_counts = count_labels(input_texts)
    output_counts = count_labels(output_texts)
    if input_counts != output_counts:
        raise AssertionError(
            f"一级标签计数不一致：输入 {input_counts}，输出 {output_counts}。"
        )

    if not output_doc.exists():
        raise AssertionError(f"未生成输出文档：{output_doc}")

    if output_doc.stat().st_size <= 0:
        raise AssertionError(f"输出文档为空：{output_doc}")

    response_care_matches = 0
    missing_colon = []
    too_short = []
    placeholders = []
    repeated_pairs = []
    secondary_occurrences = defaultdict(list)
    skeleton_occurrences = defaultdict(list)
    awkward_secondaries = []

    for text in output_texts:
        label = next((tag for tag in KNOWN_TAGS if f"★{tag}" in text or tag in text), None)
        if not label:
            continue

        marker = f"★{label}" if f"★{label}" in text else label
        suffix = text.split(marker, 1)[1]
        if not suffix.startswith("：") and not suffix.startswith(":"):
            missing_colon.append(text[:80])

        normalized = re.sub(r"\s+", "", suffix)
        if len(normalized) < 8:
            too_short.append(text[:80])

        if "幼儿进行活动（材料）" in text or "幼儿在活动。" in text:
            placeholders.append(text[:80])

        if "。" in suffix:
            secondary_part, blue_part = suffix.lstrip("：:").split("。", 1)
            secondary_stem = re.sub(r"（[^）]*）", "", secondary_part).strip()
            secondary_occurrences[secondary_stem].append(text[:100])
            skeleton = secondary_skeleton(secondary_part)
            skeleton_occurrences[skeleton].append(text[:100])
            if has_significant_overlap(secondary_part, blue_part):
                repeated_pairs.append(text[:100])
            if re.search(r"(时时|后后|以后以后|时以后|后以后|，，)", secondary_part):
                awkward_secondaries.append(text[:100])

        if "★户外自主游戏" in text and "通过" in text and "帮助婴幼儿" in text:
            response_care_matches += 1

    if missing_colon:
        raise AssertionError(f"发现一级标签后缺少冒号的段落：{missing_colon[:3]}")

    if too_short:
        raise AssertionError(f"发现替换后内容过短的段落：{too_short[:3]}")

    if placeholders:
        raise AssertionError(f"发现占位兜底文案未被替换：{placeholders[:3]}")

    if repeated_pairs:
        raise AssertionError(f"发现二级标签与蓝色正文重复：{repeated_pairs[:3]}")

    duplicate_secondaries = find_over_limit_examples(secondary_occurrences, 2)
    if duplicate_secondaries:
        sample_key = next(iter(duplicate_secondaries))
        raise AssertionError(
            f"发现二级标签超出 2 次复用：{sample_key} -> {duplicate_secondaries[sample_key][:3]}"
        )

    duplicate_skeletons = find_over_limit_examples(skeleton_occurrences, 2)
    if duplicate_skeletons:
        sample_key = next(iter(duplicate_skeletons))
        raise AssertionError(
            f"发现二级标签骨架超出 2 次复用：{sample_key} -> {duplicate_skeletons[sample_key][:3]}"
        )

    if awkward_secondaries:
        raise AssertionError(f"发现二级标签存在不自然拼接：{awkward_secondaries[:3]}")

    if response_care_matches == 0:
        raise AssertionError("未在任何 ★户外自主游戏 段落中检测到回应性照护文本。")


def main():
    parser = argparse.ArgumentParser(description="完整文档本地生成 + Word 替换自动化验证")
    parser.add_argument(
        "--input",
        default="原文档.docx",
        help="待处理的输入文档路径，默认原文档.docx",
    )
    parser.add_argument(
        "--output",
        default="保教日志_替换后.docx",
        help="输出文档路径，默认保教日志_替换后.docx",
    )
    parser.add_argument(
        "--log",
        default="artifacts/full_document_test.log",
        help="测试运行日志输出路径",
    )
    args = parser.parse_args()

    input_doc = Path(args.input).resolve()
    output_doc = Path(args.output).resolve()
    log_path = Path(args.log).resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_doc.exists():
        raise FileNotFoundError(f"输入文档不存在：{input_doc}")

    input_texts = collect_activity_texts(input_doc)
    if not input_texts:
        raise AssertionError("输入文档中未识别到任何活动段落。")

    if output_doc.exists():
        output_doc.unlink()

    buffer = io.StringIO()
    start = time.time()
    with redirect_stdout(buffer):
        process_document(str(input_doc), ai_generator, max_count=None)
    elapsed = time.time() - start

    log_text = buffer.getvalue()
    log_path.write_text(
        log_text + f"\n[tester] elapsed_seconds={elapsed:.2f}\n",
        encoding="utf-8",
    )

    output_texts = collect_activity_texts(output_doc)
    assert_output_quality(input_texts, output_texts, output_doc, log_text)

    print("完整文档测试通过")
    print(f"输入活动数: {len(input_texts)}")
    print(f"输出活动数: {len(output_texts)}")
    print(f"耗时(秒): {elapsed:.2f}")
    print(f"日志文件: {log_path}")
    print(f"输出文档: {output_doc}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"完整文档测试失败: {exc}", file=sys.stderr)
        raise
