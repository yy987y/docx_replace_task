from spire.doc import *
from spire.doc.common import *
import re

def is_level1_para(para) -> str:
    """返回一级标签文本（保留★），如果匹配则返回，否则返回 None"""
    text = para.Text.strip()
    known = ["室内自主游戏", "加点能量", "早操律动", "户外体育游戏", "户外自主游戏", 
             "生活活动", "餐前活动", "香香进餐", "餐后活动", "制作", "抱抱离园"]
    for lv in known:
        # 检查是否包含带★的标签
        if "★" + lv in text:
            return "★" + lv
        # 检查是否包含不带★的标签
        elif lv in text:
            return lv
    return None

def replace_in_paragraph(para, level1: str, new_secondary: str, new_blue: str):
    """保留一级标签，只替换二级标签和蓝色正文"""
    full_text = para.Text
    
    # 如果不包含一级标签，跳过
    if level1 not in full_text:
        return
    
    # 收集所有runs的信息
    runs_info = []
    for i in range(para.Items.Count):
        item = para.Items.get_Item(i)
        if hasattr(item, 'Text') and hasattr(item, 'CharacterFormat'):
            runs_info.append({
                'index': i,
                'text': item.Text,
                'color': item.CharacterFormat.TextColor.ToArgb(),
                'item': item
            })
    
    # 找到一级标签的结束位置
    level1_end_pos = full_text.index(level1) + len(level1)
    
    # 标记每个run的类型
    current_pos = 0
    level1_runs = []
    colon_run = None
    secondary_runs = []
    blue_runs = []
    
    in_level1 = True
    in_secondary = False
    
    for run in runs_info:
        run_start = current_pos
        run_end = current_pos + len(run['text'])
        
        # 判断是否为蓝色
        is_blue = run['color'] in [-16776961, -15072261]
        is_black = run['color'] in [0, -16777216]
        
        # 在一级标签范围内
        if run_end <= level1_end_pos:
            level1_runs.append(run['index'])
        # 一级标签刚结束，检查冒号
        elif in_level1 and run['text'].strip() in ["：", ":"]:
            colon_run = run['index']
            in_level1 = False
        # 二级标签（黑色）
        elif not in_secondary and is_black:
            in_secondary = True
            secondary_runs.append(run['index'])
            in_level1 = False
        elif in_secondary and is_black:
            secondary_runs.append(run['index'])
        # 蓝色正文
        elif is_blue:
            in_secondary = False
            in_level1 = False
            blue_runs.append(run['index'])
        
        current_pos = run_end
    
    # 检查二级标签末尾是否有句号
    has_period = False
    if secondary_runs:
        last_text = runs_info[secondary_runs[-1]]['text']
        if last_text.rstrip().endswith("。") or last_text.rstrip().endswith("."):
            has_period = True
    
    # 构建新的二级标签文本
    prefix = "" if colon_run is not None else "："
    suffix = "" if has_period else "。"
    new_secondary_text = prefix + new_secondary + suffix
    
    # 替换二级标签（从后往前删除，保留第一个）
    if secondary_runs:
        for idx in reversed(secondary_runs[1:]):
            para.Items.RemoveAt(idx)
        para.Items.get_Item(secondary_runs[0]).Text = new_secondary_text
    
    # 重新计算蓝色runs的索引（因为删除了二级标签的runs）
    deleted_count = len(secondary_runs) - 1
    adjusted_blue_runs = [idx - deleted_count for idx in blue_runs]
    
    # 替换蓝色正文（从后往前删除，保留第一个）
    if adjusted_blue_runs:
        for idx in reversed(adjusted_blue_runs[1:]):
            if idx < para.Items.Count:
                para.Items.RemoveAt(idx)
        if adjusted_blue_runs[0] < para.Items.Count:
            para.Items.get_Item(adjusted_blue_runs[0]).Text = new_blue

def process_document(doc_path: str, ai_generator):
    doc = Document()
    doc.LoadFromFile(doc_path)
    
    replaced_count = 0

    # 使用索引访问
    for sec_idx in range(doc.Sections.Count):
        sec = doc.Sections[sec_idx]
        
        for obj_idx in range(sec.Body.ChildObjects.Count):
            obj = sec.Body.ChildObjects[obj_idx]
            
            # 检查段落的子对象（文本框可能在这里）
            if hasattr(obj, 'ChildObjects'):
                for child_idx in range(obj.ChildObjects.Count):
                    child = obj.ChildObjects[child_idx]
                    
                    # 处理文本框
                    if hasattr(child, "Body") and child.Body:
                        for p_idx in range(child.Body.Paragraphs.Count):
                            p = child.Body.Paragraphs[p_idx]
                            level1 = is_level1_para(p)
                            if level1:
                                new_sec, new_blue = ai_generator(level1)
                                replace_in_paragraph(p, level1, new_sec, new_blue)
                                replaced_count += 1
                                print(f"替换: {level1}")

    output_path = "保教日志_替换后.docx"
    doc.SaveToFile(output_path, FileFormat.Docx2019)
    doc.Close()
    print(f"\n✅ 替换完成！共替换 {replaced_count} 个活动")
    print(f"输出文件: {output_path}")

# AI 生成函数（根据新prompt规则）
def demo_ai_generator(level1: str):
    """根据一级标签生成贴近幼儿生活的二级标签和蓝色正文
    
    二级标签格式：[10-20字纯白描一句话]（材料）
    蓝色正文长度规则：
    - 普通环节（不带★）：约40字
    - 带★环节：约90字
    """
    
    # 判断是否带★
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
        "加点能量": "小天走到点心桌前，拿起饼干咬了一口。yoyo说'我要牛奶'，老师帮她倒好。期期吃完后把杯子放回篮子里。乐诚拿着饼干走到窗边吃。君严吃得很快，又去拿了一块。莫莉慢慢地咬着饼干，看着窗外。",
        "早操律动": "老师拿着球说'我们一起碰一碰'。乐诚把球递给君严，两个球碰在一起。大宝在旁边笑着也拿起球加入。莫莉跟着老师的动作做。汤圆把球举得高高的。yoyo和期期一起碰球，发出咚咚的声音。小天跑来跑去追着球。",
        "户外自主游戏": "登登把野餐垫铺在地上，莫莉拿来小盘子放在上面。汤圆说'我们吃饭吧'，把玩具食物放进盘子。期期坐下来一起玩。小天拿来小勺子假装吃饭。yoyo说'我要喝水'，拿起小杯子。君严把食物分给大家。通过模仿野餐场景帮助婴幼儿建立生活经验。",
        "生活活动": "小天鼻子流鼻涕了，走到老师面前说'老师擦鼻涕'。老师拿纸巾帮他擦干净。乐诚看到后也走过来。莫莉自己拿纸巾擦嘴巴。汤圆上完厕所记得洗手。期期口渴了去饮水机喝水。君严帮小朋友拿毛巾。",
        "餐前活动": "老师说'我们一起做手指游戏'。君严伸出小手跟着老师做。莫莉在旁边也学着做，yoyo笑着拍手。期期认真地看着老师的手。小天做得很快。汤圆跟着节奏摇晃身体。大宝和乐诚一起做动作。",
        "香香进餐": "大宝吃饭时掉了一粒米在桌上，他用手捡起来放进嘴里。老师说'真棒，不浪费粮食'。期期也学着捡起掉的菜。莫莉用勺子舀起饭。小天吃得很香。汤圆把碗端起来喝汤。yoyo慢慢地嚼着菜。君严吃完后说'我吃饱了'。",
        "餐后活动": "汤圆吃完饭后走到玩具区，看到哥哥在搭积木。哥哥说'你也来玩'，汤圆坐下来一起搭。莫莉在旁边看着。期期拿起图书翻看。小天和yoyo一起玩拼图。君严帮老师收拾玩具。大宝照镜子擦嘴巴。乐诚搬小椅子。"
    }
    
    # 获取二级标签
    clean_level1 = level1.replace("★", "")
    secondary = secondary_map.get(clean_level1, "重点观察：常规生活技能")
    
    # 根据是否带★选择蓝色正文长度
    if has_star:
        blue = blue_long.get(clean_level1, "莫莉自己穿外套，拉好拉链。小天排队洗手，用肥皂搓出泡沫。汤圆擦干手后把毛巾挂回原位。乐诚把玩具放回篮子。君严帮老师整理桌子。yoyo和期期一起看图书。大宝坐在小椅子上休息。")
    else:
        blue = blue_short.get(clean_level1, "莫莉穿外套。小天洗手。汤圆擦手。")
    
    return secondary, blue

if __name__ == "__main__":
    process_document("保教日志.docx", demo_ai_generator)
