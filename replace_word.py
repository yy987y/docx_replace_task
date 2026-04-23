from spire.doc import *
from spire.doc.common import *

from ai_generator import TAG_ALIASES, ai_generator


KNOWN_LEVEL1_TAGS = [
    "户外自主游戏回应性照护",
    "室内自主游戏",
    "户外自主游戏",
    "户外体育游戏",
    "生活活动",
    "抱抱离园",
    "餐前活动",
    "餐后活动",
    "加点能量",
    "早操律动",
    "主题活动",
    "制作",
    "香香进餐",
    "午餐",
    "起床",
]

def is_level1_para(para) -> str:
    """返回一级标签文本（保留★），如果匹配则返回，否则返回 None"""
    text = para.Text.strip()
    for lv in sorted(KNOWN_LEVEL1_TAGS, key=len, reverse=True):
        if text.startswith("★" + lv):
            return "★" + lv
        if text.startswith(lv):
            return lv
    return None

def replace_in_paragraph(para, level1: str, new_secondary: str, new_blue: str):
    """保留一级标签和冒号，删除其后旧内容，再追加新的二级标签和蓝色正文。"""
    full_text = para.Text
    
    if level1 not in full_text:
        return
    
    label_end_pos = full_text.index(level1) + len(level1)
    keep_end_pos = label_end_pos
    while keep_end_pos < len(full_text) and full_text[keep_end_pos].isspace():
        keep_end_pos += 1
    if keep_end_pos < len(full_text) and full_text[keep_end_pos] in ["：", ":"]:
        keep_end_pos += 1

    delete_from = para.Items.Count
    has_colon = keep_end_pos > label_end_pos and full_text[keep_end_pos - 1] in ["：", ":"]
    current_pos = 0

    for i in range(para.Items.Count):
        item = para.Items.get_Item(i)
        if not hasattr(item, 'Text'):
            continue
        
        text = item.Text
        run_start = current_pos
        run_end = current_pos + len(text)

        if run_end <= keep_end_pos:
            current_pos = run_end
            continue

        if run_start < keep_end_pos < run_end:
            item.Text = text[: keep_end_pos - run_start]
            delete_from = i + 1
            break

        if run_start >= keep_end_pos:
            delete_from = i
            break

        current_pos = run_end

    while para.Items.Count > delete_from:
        para.Items.RemoveAt(delete_from)

    new_secondary = new_secondary.strip().lstrip("：:").rstrip("。.")
    new_blue = new_blue.strip().lstrip("。.")

    if not has_colon:
        text_range = para.AppendText("：")
        text_range.CharacterFormat.FontName = "宋体"
        text_range.CharacterFormat.FontSize = 10.5
        text_range.CharacterFormat.TextColor = Color.get_Black()

    text_range = para.AppendText(new_secondary + "。")
    text_range.CharacterFormat.FontName = "宋体"
    text_range.CharacterFormat.FontSize = 10.5
    text_range.CharacterFormat.TextColor = Color.get_Black()

    text_range = para.AppendText(new_blue)
    text_range.CharacterFormat.FontName = "宋体"
    text_range.CharacterFormat.FontSize = 10.5
    text_range.CharacterFormat.TextColor = Color.get_Blue()


def _collect_targets(doc, max_count=None):
    targets = []
    skip_tags = set()
    skipped_count = 0

    def try_append(paragraph):
        nonlocal skipped_count
        level1 = is_level1_para(paragraph)
        if not level1:
            return False

        clean_tag = TAG_ALIASES.get(level1.replace("★", ""), level1.replace("★", ""))
        if clean_tag in skip_tags:
            skipped_count += 1
            print(f"跳过 {skipped_count}: {level1}")
            return False

        targets.append(
            {
                "paragraph": paragraph,
                "level1": level1,
                "source_text": paragraph.Text.strip(),
            }
        )
        return max_count is not None and len(targets) >= max_count

    for sec_idx in range(doc.Sections.Count):
        sec = doc.Sections[sec_idx]

        for p_idx in range(sec.Body.Paragraphs.Count):
            if try_append(sec.Body.Paragraphs[p_idx]):
                return targets, skipped_count

        for obj_idx in range(sec.Body.ChildObjects.Count):
            obj = sec.Body.ChildObjects[obj_idx]
            if not hasattr(obj, "ChildObjects"):
                continue
            for child_idx in range(obj.ChildObjects.Count):
                child = obj.ChildObjects[child_idx]
                if not hasattr(child, "Body") or not child.Body:
                    continue
                for p_idx in range(child.Body.Paragraphs.Count):
                    if try_append(child.Body.Paragraphs[p_idx]):
                        return targets, skipped_count

    return targets, skipped_count


def process_document(doc_path: str, ai_generator, max_count=None):
    doc = Document()
    doc.LoadFromFile(doc_path)

    targets, skipped_count = _collect_targets(doc, max_count=max_count)
    replaced_count = 0

    if hasattr(ai_generator, "batch_generate"):
        generated_pairs = ai_generator.batch_generate(
            [
                {
                    "level1": target["level1"],
                    "source_text": target["source_text"],
                }
                for target in targets
            ]
        )
    else:
        generated_pairs = [
            ai_generator(target["level1"], target["source_text"])
            for target in targets
        ]

    for target, (new_sec, new_blue) in zip(targets, generated_pairs):
        replace_in_paragraph(target["paragraph"], target["level1"], new_sec, new_blue)
        replaced_count += 1
        print(f"替换 {replaced_count}: {target['level1']}")

    output_path = "保教日志_替换后.docx"
    doc.SaveToFile(output_path, FileFormat.Docx2019)
    doc.Close()
    print(f"\n✅ 替换完成！")
    print(f"替换: {replaced_count} 个活动")
    print(f"跳过: {skipped_count} 个活动")
    print(f"输出文件: {output_path}")

if __name__ == "__main__":
    # 处理全部文档
    process_document("原文档.docx", ai_generator, max_count=None)
