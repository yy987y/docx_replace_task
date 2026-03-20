import requests
import json
from collections import defaultdict

API_URL = "http://154.193.243.154:8080/v1/chat/completions"
API_KEY = "sk-772849b4d84f64a252c8abe09aeb9755d4f0e7b5ccf48e0789b7c218a203780a"

# 记录最近生成的场景，避免重复
recent_scenes = defaultdict(list)

def call_llm(prompt, max_tokens=100, temperature=0.9):
    """调用LLM API"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-5.4",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,  # 提高随机性
        "max_tokens": max_tokens
    }
    
    response = requests.post(API_URL, headers=headers, json=data)
    result = response.json()
    
    if "choices" in result and len(result["choices"]) > 0:
        return result["choices"][0]["message"]["content"].strip()
    else:
        raise Exception(f"API调用失败: {result}")

def generate_secondary_tag(level1):
    """生成二级标签"""
    clean_level1 = level1.replace("★", "")
    
    # 为不同活动类型提供多样化场景提示
    scene_hints = {
        "室内自主游戏": "建构类（积木、纸箱）、艺术类（涂鸦、撕贴）、角色类（娃娃家、小厨房）、操作类（串珠、拼图）",
        "加点能量": "不同点心（饼干、牛奶、水果、坚果、奶酪）和不同吃法",
        "早操律动": "不同音乐游戏（拍手、踏步、转圈、蹲起、模仿动物）",
        "制作": "不同手工（撕贴、涂色、印画、捏泥、粘贴）",
        "主题活动": "认知类（颜色、形状、大小）、探索类（水、沙、声音）",
        "户外体育游戏": "不同运动（跑跳、爬钻、投掷、平衡、推拉）",
        "户外自主游戏": "自然探索（捡叶子、玩沙、玩水）、大型玩具（滑梯、秋千、攀爬）"
    }
    
    hint = scene_hints.get(clean_level1, "")
    hint_text = f"\n**场景提示（从中选一种，每次不同）：** {hint}" if hint else ""
    
    # 获取最近生成的场景，避免重复
    recent = recent_scenes.get(clean_level1, [])
    avoid_text = ""
    if recent:
        avoid_text = f"\n**严禁重复以下场景：** {', '.join(recent[-3:])}"  # 只避免最近3个
    
    prompt = f"""你是一位专业的幼儿园一线教师。

**核心要求（必须100%遵守，不能跑偏）：**
1. 用户会单独提供一个活动类别（如"室内自主游戏"），你为2-3岁幼儿设计1个贴合生活的小活动（含简单材料）。
2. 输出必须严格只有一行：[10-20字纯白描一句话]（材料）
   - 白描只写具体动作、行为顺序、幼儿自己/同伴/教师的小互动。
   - 严禁任何形容词、情感词、比喻、感叹号、教育意义。
   - 整句正好10-20字，一句话写完。
3. 只输出这一行内容，不要任何额外文字、解释、编号、前言、总结。{hint_text}{avoid_text}

**参考示例：**
- 幼儿拿起黏土搓成圆球，插上扭扭棒递给旁边小朋友（黏土、扭扭棒）
- 幼儿把积木叠高，推倒后和同伴一起笑（积木）
- 幼儿用蜡笔在纸上画圈，递给老师看（蜡笔、纸）

现在开始，用户提供类别：{clean_level1}"""
    
    result = call_llm(prompt, max_tokens=100, temperature=1.0)
    
    # 记录生成的场景（提取关键动作）
    if result:
        # 提取括号前的内容作为场景描述
        scene_desc = result.split('（')[0] if '（' in result else result[:15]
        recent_scenes[clean_level1].append(scene_desc)
        # 只保留最近5个
        if len(recent_scenes[clean_level1]) > 5:
            recent_scenes[clean_level1] = recent_scenes[clean_level1][-5:]
    
    return result

def generate_blue_text(level1, secondary_tag):
    """生成蓝色正文"""
    has_star = "★" in level1
    clean_level1 = level1.replace("★", "")
    
    # 确定字数要求
    if has_star:
        length_req = "90个字左右"
        max_length = 100
        if clean_level1 == "户外自主游戏":
            extra_req = "\n\n**重要：** 在正文末尾增加一个回应性照护（30字），格式：通过...帮助婴幼儿..."
            max_length = 130
        else:
            extra_req = ""
    else:
        length_req = "40个字左右"
        max_length = 50
        extra_req = ""
    
    # 特殊说明
    special_note = ""
    if clean_level1 == "加点能量":
        special_note = "\n**注意：** 加点能量是吃点心的环节，点心包括：牛奶、饼干、奶酪棒、坚果、蔬菜干等。"
    
    prompt = f"""以下是幼儿园托班（2岁—3岁幼儿）的"{clean_level1}"环节。

**预设小目标：** {secondary_tag}

**任务：** 根据这个小目标，写出幼儿自己、幼儿和幼儿、或者幼儿和教师之间可能发生的事情。

**要求：**
1. 贴近幼儿生活
2. 多一些事情的白描，不要有过多形容词
3. 长度：{length_req}（严格控制字数，不要超出）
4. 幼儿名字从以下选择（每次随机选择不同的名字组合）：
   - 男孩：大宝、小宝、诞诞、登登、小天、乐诚、又又、小叮当、糕糕、君言、加加、阳阳、樾樾
   - 女孩：圆圆、yoyo、小汤圆、喜悦{special_note}{extra_req}
5. **重要：每次生成都要有创意和变化，避免重复相似的情节、动作和对话。尝试不同的场景和互动方式。**

**只输出正文内容，不要任何标题、前言、总结、换行。必须是连续的一段话。**

现在开始生成："""
    
    max_tokens = 250 if has_star else 120
    result = call_llm(prompt, max_tokens=max_tokens)
    
    # 清理换行符和多余空格
    result = result.replace('\n', '').replace('\r', '').strip()
    
    # 严格控制字数
    target_length = 90 if has_star else 40
    if len(result) > target_length:
        # 截取到最近的句号或逗号
        result = result[:target_length]
        # 找最后一个标点
        for punct in ['。', '，', '、']:
            last_idx = result.rfind(punct)
            if last_idx > target_length * 0.8:  # 至少保留80%
                result = result[:last_idx + 1]
                break
    
    return result

def ai_generator(level1):
    """主生成函数"""
    try:
        # 生成二级标签
        secondary = generate_secondary_tag(level1)
        
        # 生成蓝色正文
        blue = generate_blue_text(level1, secondary)
        
        return secondary, blue
    except Exception as e:
        print(f"AI生成失败: {e}")
        # 返回默认值
        return "幼儿进行活动（材料）", "幼儿在活动。"
