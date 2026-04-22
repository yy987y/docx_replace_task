from __future__ import annotations

from collections import defaultdict
import random
import re


NAMES = [
    "乐诚",
    "君严",
    "汤圆",
    "yoyo",
    "期期",
    "小天",
    "大宝",
    "莫莉",
    "登登",
    "喜悦",
    "糕糕",
    "小宝",
]

FORBIDDEN_WORDS = ["开心", "快乐", "认真", "培养", "促进", "提高", "有趣", "！", "!"]
RECENT_SCENES = defaultdict(list)
RECENT_NAME_GROUPS = []
TAG_CALL_COUNT = defaultdict(int)
USED_SECONDARY_BY_TAG = defaultdict(set)
USED_SECONDARY_STEMS = defaultdict(int)
USED_SECONDARY_SIGNATURES = defaultdict(set)
USED_SECONDARY_SKELETONS = defaultdict(int)
USED_SECONDARY_LEADS = defaultdict(int)
SECONDARY_STYLE_COUNTS = defaultdict(lambda: defaultdict(int))

MAX_SECONDARY_STEM_REPEAT = 2
MAX_SECONDARY_SKELETON_REPEAT = 2
MAX_SECONDARY_LEAD_REPEAT = 2

SECONDARY_EXTENSIONS = [
    "",
    "，再看看同伴的做法",
    "，再按顺序做下一步",
    "，再换一种方式试试",
    "，再听提示做后面的动作",
    "，再继续完成接下来的动作",
]

SECONDARY_INTROS = [
    "",
    "听到老师提醒后，",
    "轮到自己时，",
    "走到前面后，",
    "看着材料时，",
    "坐稳以后，",
    "伸手过去时，",
    "低头看看后，",
    "把东西放好后，",
    "跟着老师提示时，",
    "自己试一试时，",
    "转过身后，",
    "看见同伴后，",
    "把小手放好后，",
    "慢慢走近时，",
    "回到位置上后，",
]

SECONDARY_STYLE_TEMPLATES = [
    ("standard", "{prefix}：{intro}{action}{extension}"),
    ("around_material", "{prefix}：围绕{material}，{intro}{action}{extension}"),
    ("with_material", "{prefix}：结合{material}时，{intro}{action}{extension}"),
    ("process_material", "{prefix}：在接触{material}的过程中，{intro}{action}{extension}"),
    ("continue_try", "{prefix}：借助{material}继续尝试，{intro}{action}{extension}"),
]


TAG_ALIASES = {
    "香香进餐": "午餐",
}


GENERATOR_CONFIG = {
    "室内自主游戏": {
        "materials": [
            {"label": "积木、小车", "items": ["积木", "小车"]},
            {"label": "黏土、扭扭棒", "items": ["黏土", "扭扭棒"]},
            {"label": "串珠、绳子", "items": ["串珠", "绳子"]},
            {"label": "纸杯、木夹", "items": ["纸杯", "木夹"]},
            {"label": "拼图、托盘", "items": ["拼图", "托盘"]},
        ],
        "secondary_prefixes": ["重点观察", "观察记录"],
        "secondary_actions": [
            "把{item1}排成一排，再让{item2}从旁边经过",
            "拿起{item1}装进{item2}里，再倒出来",
            "把{item1}一个个连起来，递给旁边的小朋友",
            "把{item1}摆开后，伸手去拿{item2}",
            "把{item1}按颜色分开，再放进小盘里",
        ],
        "short_sentences": [
            "{n1}把{item1}摆在地垫上。",
            "{n1}拿起{item2}碰了碰{item1}。",
            "{n2}走过来说“我也要”。",
            "{n1}把{item1}递给{n2}。",
            "老师说“慢慢放进去”。",
            "{n3}蹲下来继续摆{item1}。",
        ],
        "long_sentences": [
            "{n1}把{item1}一个个摆开。",
            "{n2}拿着{item2}走过来说“给我一个”。",
            "{n1}分出一份放到{n2}手边。",
            "{n3}蹲下来跟着一起摆。",
            "老师说“你们可以一起放”。",
            "{n4}把做好的一份放进盘里。",
            "{n2}又把{item2}轻轻挪到旁边。",
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
        "secondary_prefixes": ["能够自己取点心", "愿意坐下来吃点心", "自己拿起点心再喝一口"],
        "secondary_actions": [
            "拿起{item1}咬一口，再把{item2}放回桌上",
            "坐到小椅子上，自己拿起{item1}",
            "伸手去拿{item1}，再端起{item2}",
            "把{item1}放进嘴里，再把{item2}递给老师",
        ],
        "short_sentences": [
            "{n1}拿起{item1}咬了一口。",
            "{n2}说“我要{item2}”。",
            "老师把{item2}放到桌边。",
            "{n1}吃完后把杯子放回篮子里。",
            "{n3}坐在旁边慢慢吃。",
        ],
        "long_sentences": [
            "{n1}走到点心桌前拿起{item1}。",
            "{n2}坐下来后说“我要{item2}”。",
            "老师把{item2}放到{n2}手边。",
            "{n3}吃完后把小杯子放回篮子里。",
            "{n4}看着桌上的点心又伸手拿了一块。",
            "{n1}咬了一口后转头看看旁边的小朋友。",
            "{n2}喝完后把杯子轻轻放下。",
        ],
    },
    "早操律动": {
        "materials": [
            {"label": "球", "items": ["球", "球"]},
            {"label": "纱巾", "items": ["纱巾", "纱巾"]},
            {"label": "响环", "items": ["响环", "响环"]},
            {"label": "小鼓、鼓槌", "items": ["小鼓", "鼓槌"]},
        ],
        "secondary_prefixes": ["跟着音乐做动作", "愿意和同伴一起动一动"],
        "secondary_actions": [
            "拿着{item1}碰一碰，再跟着音乐抬起手",
            "伸出小手跟着老师拍一拍",
            "把{item1}举起来，再轻轻落下来",
            "听到音乐后拿起{item1}动一动",
        ],
        "short_sentences": [
            "老师说“我们一起动一动”。",
            "{n1}拿起{item1}跟着拍手。",
            "{n2}碰了碰{n1}手里的{item1}。",
            "{n3}听到音乐后转了半圈。",
            "老师又说“停一下，再来”。",
        ],
        "long_sentences": [
            "音乐一响，{n1}先把{item1}举了起来。",
            "{n2}看见后也跟着拍了拍手。",
            "{n3}拿着{item1}走到{n1}旁边碰一碰。",
            "老师说“脚也一起抬起来”。",
            "{n4}跟着老师慢慢蹲下又站起来。",
            "{n2}停下来看了一眼老师，又继续动。",
            "{n1}把{item1}递给{n3}再接回来。",
        ],
    },
    "制作": {
        "materials": [
            {"label": "彩纸、胶棒", "items": ["彩纸", "胶棒"]},
            {"label": "海绵印章、颜料", "items": ["海绵印章", "颜料"]},
            {"label": "贴纸、白纸", "items": ["贴纸", "白纸"]},
            {"label": "蜡笔、画纸", "items": ["蜡笔", "画纸"]},
        ],
        "secondary_prefixes": ["能够自己选材料", "愿意按一按再贴上去", "教学"],
        "secondary_actions": [
            "拿起{item1}按一按，再用{item2}贴上",
            "选一张{item1}撕成小块，再放到纸上",
            "拿着{item1}在纸上点一点，再换一只手",
            "把{item1}贴在白纸上，再伸手去拿{item2}",
        ],
        "short_sentences": [
            "{n1}拿起{item1}放到桌上。",
            "{n2}伸手去拿{item2}。",
            "{n1}把一小块贴到纸上。",
            "老师说“按一按就可以了”。",
            "{n3}把做好的纸递给老师看。",
        ],
        "long_sentences": [
            "{n1}先选了一张{item1}放在桌上。",
            "{n2}拿着{item2}在旁边等着。",
            "{n1}把一小块贴到纸上后又按了按。",
            "老师说“可以再拿一块放旁边”。",
            "{n3}看见后也伸手来拿材料。",
            "{n4}把做好的一张纸递到老师面前。",
            "{n2}低头继续把边上的一块贴好。",
        ],
    },
    "主题活动": {
        "materials": [
            {"label": "图片卡", "items": ["图片卡", "图片"]},
            {"label": "绘本、图片", "items": ["绘本", "图片"]},
            {"label": "水果卡片、小篮子", "items": ["水果卡片", "小篮子"]},
            {"label": "小动物图片、托盘", "items": ["小动物图片", "托盘"]},
        ],
        "secondary_prefixes": ["教学", "阅读", "认识活动"],
        "secondary_actions": [
            "看着{item1}说出上面的东西",
            "把{item1}放进{item2}里，再说出名字",
            "翻到{item1}这一页后伸手指一指",
            "拿起{item1}和老师一起看一看",
        ],
        "short_sentences": [
            "老师拿出{item1}放在前面。",
            "{n1}伸手指了指上面的图。",
            "{n2}说出“这是这个”。",
            "老师点点头又翻到下一张。",
            "{n3}跟着把{item1}放进{item2}里。",
            "{n4}把卡片递给老师后又坐回位置上。",
            "老师把图片排开，请大家一个个看。",
        ],
        "long_sentences": [
            "老师先拿出{item1}放在桌上。",
            "{n1}伸手指了指上面的图说出名字。",
            "{n2}看见后把另一张{item1}递给老师。",
            "老师说“我们再看看这一张”。",
            "{n3}把{item1}放进{item2}里后又拿出来看。",
            "{n4}坐在旁边跟着重复了一遍。",
            "老师把图片排开，让大家一个个看。",
            "{n1}把手边的一张卡片翻过来又看了一眼。",
            "{n2}把看到的图片递到老师手里。",
        ],
    },
    "户外体育游戏": {
        "materials": [
            {"label": "球、轮滑桩", "items": ["球", "轮滑桩"]},
            {"label": "呼啦圈、地垫", "items": ["呼啦圈", "地垫"]},
            {"label": "隧道筒、垫子", "items": ["隧道筒", "垫子"]},
            {"label": "平衡木、小旗", "items": ["平衡木", "小旗"]},
        ],
        "secondary_prefixes": ["能够往前走一走", "愿意排队轮流玩", "跟着路线动一动"],
        "secondary_actions": [
            "推着{item1}绕过{item2}走到前面",
            "钻过{item1}后再踩上{item2}",
            "拿着{item1}走到终点再转回来",
            "一步一步走过{item1}，再伸手去拿{item2}",
        ],
        "short_sentences": [
            "{n1}推着{item1}往前走。",
            "{n2}在后面看着前面的路线。",
            "老师说“轮到你再出发”。",
            "{n3}走到终点后转身回来。",
            "{n1}把{item1}放到旁边。",
        ],
        "long_sentences": [
            "{n1}先推着{item1}绕过{item2}。",
            "{n2}站在后面等着轮到自己。",
            "老师说“慢慢走，脚踩稳”。",
            "{n3}走到终点后回头看了看老师。",
            "{n4}接过{item1}继续往前走。",
            "{n2}等前面空出来后才迈步出去。",
            "{n1}把{item1}放回起点又站到队尾。",
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
        "secondary_prefixes": ["重点观察", "观察记录"],
        "secondary_actions": [
            "拿起{item1}装一装，再倒进{item2}里",
            "把{item1}放在垫子上，再递给旁边的小朋友",
            "弯腰捡起{item1}，再放进{item2}",
            "推着{item1}走到一边，再拿出{item2}",
        ],
        "short_sentences": [
            "{n1}拿起{item1}装了一下。",
            "{n2}把{item2}挪到{n1}旁边。",
            "{n1}倒进去后又看了看。",
            "{n3}说“给我一点”。",
            "老师蹲下来看着他们继续玩。",
        ],
        "long_sentences": [
            "{n1}先把{item2}放在地上。",
            "{n2}拿起{item1}装了一些又倒进去。",
            "{n3}走过来说“我也来”。",
            "{n1}把手里的{item1}递给{n3}。",
            "老师蹲下来说“你们可以轮流用”。",
            "{n4}又把旁边的一份挪到垫子上。",
            "{n2}看见后继续把东西装进{item2}里。",
        ],
        "response_care": [
            "通过蹲下说明轮流顺序，帮助婴幼儿等待和交接。",
            "通过回应幼儿的目光和动作，帮助婴幼儿回到同伴游戏中。",
            "通过示范把材料轻轻递给同伴，帮助婴幼儿学着表达和协商。",
            "通过陪伴幼儿一起装和倒，帮助婴幼儿积累操作经验。",
        ],
    },
    "起床": {
        "materials": [
            {"label": "小床、鞋子", "items": ["小床", "鞋子"]},
            {"label": "被子、小袜子", "items": ["被子", "小袜子"]},
            {"label": "枕头、外套", "items": ["枕头", "外套"]},
        ],
        "secondary_prefixes": ["能在提醒下起身", "愿意跟着老师穿好鞋子"],
        "secondary_actions": [
            "坐起来后伸脚去找{item2}",
            "把{item1}推到一边，再拿起{item2}",
            "听到老师提醒后坐起来穿{item2}",
            "醒来后先拉开{item1}再伸手拿{item2}",
        ],
        "short_sentences": [
            "老师轻声叫{n1}起床。",
            "{n1}坐起来后伸脚去找{item2}。",
            "{n2}把{item1}推到一边。",
            "老师说“鞋子在这里”。",
            "{n1}低头把脚伸进去。",
            "{n2}坐在床边看着老师帮旁边的小朋友。",
            "{n1}站起来后把被角往里推了推。",
        ],
        "long_sentences": [
            "老师轻轻拍了拍{n1}说“该起床了”。",
            "{n1}坐起来后揉了揉眼睛。",
            "{n2}已经把{item1}推到一边，低头找自己的{item2}。",
            "老师把{item2}放到{n1}脚边说“先穿这一只”。",
            "{n3}坐在床边看着老师帮旁边的小朋友。",
            "{n4}穿好一只后又弯腰去找另一只。",
            "{n1}站起来后把小被子往里面推了推。",
            "{n2}把找到的一只鞋先放到脚边。",
            "老师扶着{n3}站起来整理衣角。",
        ],
    },
    "生活活动": {
        "materials": [
            {"label": "纸巾", "items": ["纸巾", "纸巾"]},
            {"label": "毛巾、水杯", "items": ["毛巾", "水杯"]},
            {"label": "洗手液、毛巾", "items": ["洗手液", "毛巾"]},
            {"label": "小杯子、纸巾", "items": ["小杯子", "纸巾"]},
        ],
        "secondary_prefixes": ["能够自己表达需要", "愿意跟着步骤做一做", "生活观察"],
        "secondary_actions": [
            "需要时去拿{item1}再找老师帮忙",
            "先伸手拿{item1}，再把{item2}放回原位",
            "走到前面说出需要，再接过{item1}",
            "把{item1}用完后放回篮子里",
        ],
        "short_sentences": [
            "{n1}走到老师面前说“要擦一擦”。",
            "老师把{item1}递到{n1}手里。",
            "{n2}看见后也走过来。",
            "{n1}用完后把{item1}放回篮子里。",
            "{n3}在旁边继续等着。",
        ],
        "long_sentences": [
            "{n1}走到老师面前说“要擦一擦”。",
            "老师把{item1}递到{n1}手里后又看了看旁边的小朋友。",
            "{n2}看见后也跟着走过来伸出手。",
            "{n3}用完{item2}后把它挂回原位。",
            "老师说“用好了要放回去”。",
            "{n4}转身去拿自己的小杯子又放回桌上。",
            "{n1}擦完后把{item1}轻轻丢进垃圾桶。",
        ],
    },
    "抱抱离园": {
        "materials": [
            {"label": "外套、书包", "items": ["外套", "书包"]},
            {"label": "水杯、书包", "items": ["水杯", "书包"]},
            {"label": "室外鞋、小书包", "items": ["室外鞋", "小书包"]},
        ],
        "secondary_prefixes": ["愿意整理好物品再离开", "能和老师说再见"],
        "secondary_actions": [
            "拿起{item1}穿好，再背起{item2}",
            "把{item1}放进{item2}里，再走到门口",
            "换好{item1}后背起{item2}",
            "拉一拉{item1}，再抬手和老师说再见",
        ],
        "short_sentences": [
            "{n1}拿起{item1}往身上套。",
            "{n2}把{item2}递到旁边。",
            "老师说“我们去门口等一等”。",
            "{n1}背好后抬手说“再见”。",
            "{n3}站在门边看着外面。",
        ],
        "long_sentences": [
            "{n1}先把{item1}穿到身上。",
            "{n2}低头把{item2}背到背上。",
            "老师说“水杯也一起带上”。",
            "{n3}把自己的东西拿好后走到门口。",
            "{n4}抬手对老师说“再见”。",
            "{n1}又回头看了一眼教室里的小朋友。",
            "老师站在旁边帮他们把背带拉整齐。",
        ],
    },
    "餐前活动": {
        "materials": [
            {"label": "小手、音乐", "items": ["小手", "音乐"]},
            {"label": "图书、地垫", "items": ["图书", "地垫"]},
            {"label": "手指玩偶", "items": ["手指玩偶", "手指玩偶"]},
        ],
        "secondary_prefixes": ["愿意和老师一起等一等", "跟着做手指动作", "愿意坐下来听一听"],
        "secondary_actions": [
            "伸出{item1}跟着老师做一做",
            "坐到{item2}上看着{item1}",
            "听到{item2}后跟着拍一拍",
            "看着老师手里的{item1}伸手碰一碰",
        ],
        "short_sentences": [
            "老师说“我们先一起等一等”。",
            "{n1}伸出{item1}跟着做动作。",
            "{n2}看着老师手里的{item1}笑了笑。",
            "{n3}坐在旁边轻轻拍手。",
            "老师又说“做完就去吃饭”。",
            "{n4}把手放在腿上等老师继续说。",
            "{n2}抬头看着前面的老师没有离开位置。",
        ],
        "long_sentences": [
            "老师先说“我们坐下来做个手指游戏”。",
            "{n1}伸出{item1}跟着老师一下一下做。",
            "{n2}看着老师手里的{item1}也伸手碰了碰。",
            "{n3}坐在地垫上跟着拍手。",
            "老师说“做完我们就去洗手”。",
            "{n4}把手放到腿上后又抬起来继续做。",
            "{n1}看见旁边的小朋友做了，也跟着再做一遍。",
            "{n2}停下来后抬头看着老师等下一步提醒。",
            "{n3}做完一遍后把手轻轻放回腿上。",
        ],
    },
    "午餐": {
        "materials": [
            {"label": "勺子、餐盘", "items": ["勺子", "餐盘"]},
            {"label": "米饭、小碗", "items": ["米饭", "小碗"]},
            {"label": "青菜、勺子", "items": ["青菜", "勺子"]},
        ],
        "secondary_prefixes": ["自主进餐", "愿意自己舀一舀", "安静坐在位置上吃饭"],
        "secondary_actions": [
            "拿起{item1}舀一口，再把掉下的饭粒放回{item2}",
            "坐在位置上拿着{item1}慢慢吃",
            "把{item1}送到嘴边，再看看桌上的{item2}",
            "自己舀起一口后继续坐在位置上",
        ],
        "short_sentences": [
            "{n1}拿起{item1}舀了一口。",
            "{n2}低头把掉下的饭粒捡回{item2}里。",
            "老师说“慢慢吃，坐在这里”。",
            "{n3}继续把{item1}送到嘴边。",
            "{n1}吃完一口后又去舀下一口。",
        ],
        "long_sentences": [
            "{n1}坐在位置上拿起{item1}慢慢吃。",
            "{n2}发现桌上掉了一点饭粒，低头把它捡回{item2}里。",
            "老师说“舀好了再送到嘴里”。",
            "{n3}把一口饭送进嘴里后又去舀下一口。",
            "{n4}看着旁边的小朋友，也把勺子放进碗里。",
            "{n1}吃完后把勺子轻轻放在碗边。",
            "{n2}继续坐在位置上没有离开桌边。",
        ],
    },
    "餐后活动": {
        "materials": [
            {"label": "积木", "items": ["积木", "积木"]},
            {"label": "图书、地垫", "items": ["图书", "地垫"]},
            {"label": "拼图、托盘", "items": ["拼图", "托盘"]},
        ],
        "secondary_prefixes": ["吃完后愿意安静玩一会", "愿意自己去选一样玩具"],
        "secondary_actions": [
            "走到一边拿起{item1}玩一玩",
            "把{item1}放在{item2}上再伸手去拿下一块",
            "翻开{item1}看一看，再坐回{item2}上",
            "拿起{item1}后坐到旁边的小椅子上",
        ],
        "short_sentences": [
            "{n1}吃完后走到一边拿起{item1}。",
            "{n2}坐在旁边看着{n1}手里的东西。",
            "{n3}也走过来拿了一份。",
            "老师说“在这里玩一会儿”。",
            "{n1}把{item1}放到{item2}上继续看。",
        ],
        "long_sentences": [
            "{n1}吃完后先走到一边拿起{item1}。",
            "{n2}看见后也坐到旁边的小椅子上。",
            "{n3}把另一份{item1}放到{item2}上慢慢摆。",
            "老师说“吃好了可以在这里看一会儿”。",
            "{n4}翻了翻手里的{item1}又递给旁边的小朋友。",
            "{n1}看了一会儿后又拿起另一块继续摆。",
            "{n2}没有说话，只是低头继续玩手里的东西。",
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


def _fill_templates(templates: list[str], mapping: dict, target_count: int, rng: random.Random) -> list[str]:
    pool = templates[:]
    rng.shuffle(pool)
    results = []
    for template in pool:
        sentence = template.format(**mapping)
        results.append(sentence)
        if len(results) >= target_count:
            break
    return results


def _compose_text(sentences: list[str], min_len: int, max_len: int) -> str:
    text = ""
    for sentence in sentences:
        if len(text) >= min_len and len(text) + len(sentence) > max_len:
            continue
        if len(text) + len(sentence) <= max_len or len(text) < min_len:
            text += sentence
        if min_len <= len(text) <= max_len:
            break
    return text[:max_len].rstrip("，。、")


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


def _select_sentences_without_overlap(
    templates: list[str],
    mapping: dict,
    target_count: int,
    rng: random.Random,
    secondary_tag: str,
) -> list[str]:
    pool = templates[:]
    rng.shuffle(pool)
    selected = []
    rejected = []
    for template in pool:
        sentence = template.format(**mapping)
        if _has_significant_overlap(secondary_tag, sentence):
            rejected.append(sentence)
            continue
        selected.append(sentence)
        if len(selected) >= target_count:
            return selected
    for sentence in rejected:
        selected.append(sentence)
        if len(selected) >= target_count:
            break
    return selected


def _sanitize_secondary(text: str) -> str:
    text = re.sub(r"\s+", "", text)
    text = text.lstrip("：:")
    text = text.rstrip("。.")
    for word in FORBIDDEN_WORDS:
        text = text.replace(word, "")
    return text


def _secondary_stem(text: str) -> str:
    return re.sub(r"（[^）]*）", "", _sanitize_secondary(text)).strip()


def _known_items() -> list[str]:
    return sorted(
        {
            item
            for tag_config in GENERATOR_CONFIG.values()
            for material in tag_config["materials"]
            for item in material["items"]
        },
        key=len,
        reverse=True,
    )


KNOWN_ITEMS = _known_items()


def _secondary_skeleton(text: str) -> str:
    skeleton = re.sub(r"（[^）]*）", "", _sanitize_secondary(text))
    for item in KNOWN_ITEMS:
        skeleton = skeleton.replace(item, "<ITEM>")
    return re.sub(r"\s+", "", skeleton)


def _secondary_lead_key(text: str) -> str:
    return _secondary_skeleton(text)[:18]


def _sanitize_blue(text: str, star: bool) -> str:
    text = text.replace("\n", "").replace("\r", "").strip()
    for word in FORBIDDEN_WORDS:
        text = text.replace(word, "")
    text = re.sub(r"[。]{2,}", "。", text)
    if not text.endswith("。"):
        text += "。"
    max_len = 125 if star else 55
    if len(text) > max_len:
        text = text[:max_len]
        last_period = text.rfind("。")
        if last_period >= max_len * 0.75:
            text = text[: last_period + 1]
    return text


def _extract_material_from_secondary(secondary_tag: str, cfg: dict) -> dict | None:
    match = re.search(r"（([^）]+)）", secondary_tag)
    if match:
        label = match.group(1)
        for material in cfg["materials"]:
            if material["label"] == label:
                return material
        parts = [part.strip() for part in label.split("、") if part.strip()]
        if parts:
            return {"label": label, "items": [parts[0], parts[-1]]}

    for material in sorted(cfg["materials"], key=lambda item: len(item["label"]), reverse=True):
        if material["label"] in secondary_tag:
            return material

    return None


def generate_secondary_tag(level1: str) -> tuple[str, dict]:
    clean_level1 = _clean_tag(level1)
    cfg = GENERATOR_CONFIG[clean_level1]
    rng = _rng_for(level1)
    material = _pick_material(cfg, rng, clean_level1)
    prefixes = cfg["secondary_prefixes"][:]
    rng.shuffle(prefixes)
    action_templates = cfg["secondary_actions"][:]
    rng.shuffle(action_templates)
    extensions = SECONDARY_EXTENSIONS[:]
    rng.shuffle(extensions)
    intros = SECONDARY_INTROS[:]
    rng.shuffle(intros)
    style_templates = SECONDARY_STYLE_TEMPLATES[:]
    rng.shuffle(style_templates)
    style_templates.sort(key=lambda item: SECONDARY_STYLE_COUNTS[clean_level1][item[0]])

    def build_secondary(style_template: str, prefix: str, intro: str, action_text: str, extension: str) -> str:
        if "：" in prefix or ":" in prefix:
            prefix = prefix.rstrip("：:")
        text = style_template.format(
            prefix=prefix,
            intro=intro,
            action=action_text,
            extension=extension,
            material=material["label"],
        )
        return _sanitize_secondary(text)

    for style_name, style_template in style_templates:
        for prefix in prefixes:
            for action_template in action_templates:
                base_action = action_template.format(
                    item1=material["items"][0],
                    item2=material["items"][-1],
                )
                for intro_index, intro in enumerate(intros):
                    for extension_index, extension in enumerate(extensions):
                        if style_name != "standard" and "材料" in intro:
                            continue
                        signature = (
                            f"{style_name}|{prefix}|{action_template}|intro:{intro_index}|extension:{extension_index}"
                        )
                        secondary = build_secondary(style_template, prefix, intro, base_action, extension)
                        stem = _secondary_stem(secondary)
                        skeleton = _secondary_skeleton(secondary)
                        lead_key = _secondary_lead_key(secondary)
                        if (
                            secondary not in USED_SECONDARY_BY_TAG[clean_level1]
                            and USED_SECONDARY_STEMS[stem] < MAX_SECONDARY_STEM_REPEAT
                            and signature not in USED_SECONDARY_SIGNATURES[clean_level1]
                            and USED_SECONDARY_SKELETONS[skeleton] < MAX_SECONDARY_SKELETON_REPEAT
                            and USED_SECONDARY_LEADS[lead_key] < MAX_SECONDARY_LEAD_REPEAT
                        ):
                            USED_SECONDARY_BY_TAG[clean_level1].add(secondary)
                            USED_SECONDARY_STEMS[stem] += 1
                            USED_SECONDARY_SIGNATURES[clean_level1].add(signature)
                            USED_SECONDARY_SKELETONS[skeleton] += 1
                            USED_SECONDARY_LEADS[lead_key] += 1
                            SECONDARY_STYLE_COUNTS[clean_level1][style_name] += 1
                            return secondary, material

    fallback_prefix = prefixes[0] if prefixes else "观察记录"
    fallback = build_secondary(
        SECONDARY_STYLE_TEMPLATES[0][1],
        fallback_prefix,
        "",
        f"围着{material['items'][0]}和{material['items'][-1]}试一试",
        "，再换一种做法",
    )
    USED_SECONDARY_BY_TAG[clean_level1].add(fallback)
    USED_SECONDARY_STEMS[_secondary_stem(fallback)] += 1
    USED_SECONDARY_SIGNATURES[clean_level1].add(f"{fallback_prefix}|fallback|{material['label']}")
    USED_SECONDARY_SKELETONS[_secondary_skeleton(fallback)] += 1
    USED_SECONDARY_LEADS[_secondary_lead_key(fallback)] += 1
    SECONDARY_STYLE_COUNTS[clean_level1][SECONDARY_STYLE_TEMPLATES[0][0]] += 1
    return fallback, material


def generate_blue_text(level1: str, secondary_tag: str, material: dict | None = None) -> str:
    clean_level1 = _clean_tag(level1)
    has_star = "★" in level1
    cfg = GENERATOR_CONFIG[clean_level1]
    rng = _rng_for(f"{level1}-blue")
    if material is None:
        material = _extract_material_from_secondary(secondary_tag, cfg)
    if material is None:
        material = _pick_material(cfg, rng, f"{clean_level1}-blue")
    names = _pick_names(rng, 4)
    mapping = {
        "n1": names[0],
        "n2": names[1],
        "n3": names[2],
        "n4": names[3],
        "item1": material["items"][0],
        "item2": material["items"][-1],
    }
    if has_star:
        sentences = _select_sentences_without_overlap(
            cfg["long_sentences"],
            mapping,
            7,
            rng,
            secondary_tag,
        )
        text = _compose_text(sentences, 84, 102)
        if clean_level1 == "户外自主游戏":
            care = rng.choice(cfg["response_care"])
            if not text.endswith("。"):
                text += "。"
            text += care
    else:
        sentences = _select_sentences_without_overlap(
            cfg["short_sentences"],
            mapping,
            5,
            rng,
            secondary_tag,
        )
        text = _compose_text(sentences, 34, 48)
    if _has_significant_overlap(secondary_tag, text):
        fallback_templates = [
            "{n1}看着老师点了点头。",
            "{n2}把手里的东西放到旁边。",
            "老师继续说“我们慢慢来”。",
            "{n3}坐在旁边看着前面的动作。",
            "{n4}做完后又看了看同伴。",
        ]
        fallback_sentences = _fill_templates(fallback_templates, mapping, 5, rng)
        min_len, max_len = (84, 102) if has_star else (34, 48)
        text = _compose_text(fallback_sentences + sentences, min_len, max_len)
        if has_star and clean_level1 == "户外自主游戏" and "帮助婴幼儿" not in text:
            care = rng.choice(cfg["response_care"])
            if not text.endswith("。"):
                text += "。"
            text += care
    return _sanitize_blue(text, has_star)


def ai_generator(level1: str) -> tuple[str, str]:
    clean_level1 = _clean_tag(level1)
    if clean_level1 not in GENERATOR_CONFIG:
        raise ValueError(f"不支持的一级标签: {level1}")

    secondary, material = generate_secondary_tag(level1)
    blue = generate_blue_text(level1, secondary, material)
    return secondary, blue
