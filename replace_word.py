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

def process_document(doc_path: str, ai_generator, max_count=None):
    doc = Document()
    doc.LoadFromFile(doc_path)
    
    skip_tags = set()
    
    replaced_count = 0
    skipped_count = 0

    for sec_idx in range(doc.Sections.Count):
        sec = doc.Sections[sec_idx]

        for p_idx in range(sec.Body.Paragraphs.Count):
            p = sec.Body.Paragraphs[p_idx]
            level1 = is_level1_para(p)
            if level1:
                clean_tag = TAG_ALIASES.get(level1.replace('★', ''), level1.replace('★', ''))
                if clean_tag in skip_tags:
                    skipped_count += 1
                    print(f"跳过 {skipped_count}: {level1}")
                    continue

                new_sec, new_blue = ai_generator(level1)
                replace_in_paragraph(p, level1, new_sec, new_blue)
                replaced_count += 1
                print(f"替换 {replaced_count}: {level1}")
                if max_count and replaced_count >= max_count:
                    break
        if max_count and replaced_count >= max_count:
            break
        
        for obj_idx in range(sec.Body.ChildObjects.Count):
            obj = sec.Body.ChildObjects[obj_idx]
            
            if hasattr(obj, 'ChildObjects'):
                for child_idx in range(obj.ChildObjects.Count):
                    child = obj.ChildObjects[child_idx]
                    
                    if hasattr(child, "Body") and child.Body:
                        for p_idx in range(child.Body.Paragraphs.Count):
                            p = child.Body.Paragraphs[p_idx]
                            level1 = is_level1_para(p)
                            if level1:
                                clean_tag = TAG_ALIASES.get(level1.replace('★', ''), level1.replace('★', ''))
                                if clean_tag in skip_tags:
                                    skipped_count += 1
                                    print(f"跳过 {skipped_count}: {level1}")
                                    continue
                                
                                new_sec, new_blue = ai_generator(level1)
                                replace_in_paragraph(p, level1, new_sec, new_blue)
                                replaced_count += 1
                                print(f"替换 {replaced_count}: {level1}")
                                
                                # 如果达到最大数量，停止
                                if max_count and replaced_count >= max_count:
                                    break
                        if max_count and replaced_count >= max_count:
                            break
                if max_count and replaced_count >= max_count:
                    break
        if max_count and replaced_count >= max_count:
            break

    output_path = "保教日志_替换后.docx"
    doc.SaveToFile(output_path, FileFormat.Docx2019)
    doc.Close()
    print(f"\n✅ 替换完成！")
    print(f"替换: {replaced_count} 个活动")
    print(f"跳过: {skipped_count} 个活动")
    print(f"输出文件: {output_path}")

# AI 生成函数（根据新prompt规则）
def demo_ai_generator(level1: str):
    """根据一级标签生成贴近幼儿生活的二级标签和蓝色正文"""
    
    has_star = "★" in level1
    
    # 二级标签：10-20字白描 + 材料（无前缀）
    secondary_map = {
        "室内自主游戏": "幼儿拿起黏土搓成圆球，插上扭扭棒递给旁边小朋友（黏土、扭扭棒）",
        "加点能量": "幼儿走到点心桌前拿起饼干咬一口（饼干、牛奶）",
        "早操律动": "幼儿拿着球和同伴碰一碰发出声音（球）",
        "制作": "幼儿选红色彩纸撕成小块用胶棒贴上（彩纸、胶棒）",
        "主题活动": "老师拿出马桶图片幼儿说出名字（图片）",
        "户外体育游戏": "幼儿推着球绕过轮滑桩走到终点（球、轮滑桩）",
        "户外自主游戏": "幼儿把野餐垫铺地上拿小盘子放玩具食物（野餐垫、小盘子）",
        "生活活动": "幼儿走到老师面前说擦鼻涕老师帮忙擦（纸巾）",
        "餐前活动": "幼儿伸出小手跟着老师做手指游戏（无）",
        "香香进餐": "幼儿用勺子舀饭捡起掉的米放进嘴里（勺子）",
        "餐后活动": "幼儿走到玩具区和哥哥一起搭积木（积木）",
        "抱抱离园": "幼儿穿好外套拉拉链和老师说再见（外套）"
    }
    
    # 蓝色正文：普通环节（约40字）
    blue_short = {
        "室内自主游戏": "登登拿起黏土搓成圆球，把扭扭棒插进去。莫莉说'我也要'。",
        "加点能量": "小天拿起饼干咬了一口。yoyo说'我要牛奶'。",
        "早操律动": "乐诚把球递给君严，两个球碰在一起。大宝也拿起球。",
        "制作": "莫莉选了红色彩纸撕成小块。小天用胶棒贴上去。",
        "主题活动": "老师拿出马桶图片。期期说'马桶'。老师说'对'。",
        "户外体育游戏": "君严推着球往前走。yoyo在后面跟着。大宝推到终点。",
        "户外自主游戏": "登登把野餐垫铺在地上。莫莉拿来小盘子。汤圆说'吃饭'。",
        "生活活动": "小天走到老师面前说'擦鼻涕'。老师拿纸巾帮他擦。",
        "餐前活动": "老师说'做手指游戏'。君严伸出小手跟着做。",
        "香香进餐": "大宝捡起掉的米放进嘴里。老师说'真棒'。",
        "餐后活动": "汤圆走到玩具区。哥哥说'你也来玩'。"
    }
    
    # 蓝色正文：带★环节（约90字）
    blue_long = {
        "室内自主游戏": "登登拿起黏土搓成圆球，把扭扭棒插进去。莫莉在旁边说'我也要做'，登登把黏土分给她一半。汤圆做好后举起来给老师看，老师说'真棒'。期期也想做，拿起黏土学着登登的样子搓。小天把做好的棒棒糖放在盘子里。",
        "户外自主游戏": "登登把野餐垫铺在地上，莫莉拿来小盘子放在上面。汤圆说'我们吃饭吧'，把玩具食物放进盘子。期期坐下来一起玩。小天拿来小勺子假装吃饭。yoyo说'我要喝水'，拿起小杯子。君严把食物分给大家。通过模仿野餐场景帮助婴幼儿建立生活经验。"
    }
    
    clean_level1 = level1.replace("★", "")
    secondary = secondary_map.get(clean_level1, "幼儿进行常规生活活动（无）")
    
    if has_star:
        blue = blue_long.get(clean_level1, "莫莉自己穿外套，拉好拉链。小天排队洗手。")
    else:
        blue = blue_short.get(clean_level1, "莫莉穿外套。小天洗手。")
    
    return secondary, blue

if __name__ == "__main__":
    # 处理全部文档
    process_document("原文档.docx", ai_generator, max_count=None)
