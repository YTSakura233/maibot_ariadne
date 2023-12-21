import base64
import re
from pathlib import Path
from typing import Union, Dict, Any
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.event.mirai import NudgeEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image
from graia.ariadne.message.parser.base import DetectPrefix, MatchRegex
from graia.ariadne.model import Group, Member
from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from Api import tool
from Api import maimaidx_music
from Api import image
from Api import maimai_best_40
from Api import maimai_best_50

channel = Channel.current()


def song_txt(music: maimaidx_music.Music):
    return MessageChain(
        f"{music.id}. {music.title}\n",
        Image(url='https://www.diving-fish.com/covers/' + maimaidx_music.get_cover_len5_id(music.id) + '.png'),
        f"\n{'/'.join(music.level)}")


def inner_level_q(ds1, ds2=None):
    result_set = []
    diff_label = ['Bas', 'Adv', 'Exp', 'Mst', 'ReM']
    if ds2 is not None:
        music_data = maimaidx_music.total_list.filter(ds=(ds1, ds2))
    else:
        music_data = maimaidx_music.total_list.filter(ds=ds1)
    for music in sorted(music_data, key = lambda i: int(i['id'])):
        for i in music.diff:
            result_set.append((music['id'], music['title'], music['ds'][i], diff_label[i], music['level'][i]))
    return result_set


# B50查询
@channel.use(ListenerSchema(listening_events=[GroupMessage, NudgeEvent]))
async def _(app: Ariadne, group: Group, member: Member, message: MessageChain = DetectPrefix('b50')):
    username = str(message).strip()
    if username == "":
        payload = {'qq': str(member.id), 'b50': True}
    else:
        payload = {'username': username, 'b50': True}
    img, success = await maimai_best_50.generate50(payload)
    if success == 400:
        await app.send_message(group, MessageChain('未找到此玩家，请确保此玩家的用户名和查分器中的用户名相同。'))
    elif success == 403:
        await app.send_message(group, MessageChain('该用户禁止了其他人获取数据'))
    else:
        await app.send_message(group, MessageChain(Image(base64=image.image_to_base64(img))))


# B40查询
@channel.use(ListenerSchema(listening_events=[GroupMessage, NudgeEvent]))
async def _(app: Ariadne, group: Group, member: Member, message: MessageChain = DetectPrefix('b40')):
    username = str(message).strip()
    if username == "":
        payload = {'qq': str(member.id)}
    else:
        payload = {'username': username}
    img, success = await maimai_best_40.generate(payload)
    if success == 400:
        await app.send_message(group, MessageChain('未找到此玩家，请确保此玩家的用户名和查分器中的用户名相同。'))
    elif success == 403:
        await app.send_message(group, MessageChain('该用户禁止了其他人获取数据'))
    else:
        await app.send_message(group, MessageChain(Image(base64=image.image_to_base64(img))))


# 歌曲分数线查询
@channel.use(ListenerSchema(listening_events=[GroupMessage, NudgeEvent]))
async def _(app: Ariadne, group: Group, member: Member, message: MessageChain = DetectPrefix('分数线')):
    r = "([绿黄红紫白])(id)?([0-9]+)"
    argv = str(message).strip().split(" ")
    if len(argv) == 1 and argv[0] == '帮助':
        s = '''此功能为查找某首歌分数线设计。
    命令格式：分数线 <难度+歌曲id> <分数线>
    例如：分数线 紫799 100
    命令将返回分数线允许的 TAP GREAT 容错以及 BREAK 50落等价的 TAP GREAT 数。
    以下为 TAP GREAT 的对应表：
    GREAT/GOOD/MISS
    TAP\t1/2.5/5
    HOLD\t2/5/10
    SLIDE\t3/7.5/15
    TOUCH\t1/2.5/5
    BREAK\t5/12.5/25(外加200落)'''
        await app.send_message(group, MessageChain(Image(base64=image.image_to_base64(image.text_to_image(s)))))
    elif len(argv) == 2:
        try:
            grp = re.match(r, argv[0]).groups()
            level_labels = ['绿', '黄', '红', '紫', '白']
            level_labels2 = ['Basic', 'Advanced', 'Expert', 'Master', 'Re:MASTER']
            level_index = level_labels.index(grp[0])
            chart_id = grp[2]
            line = float(argv[1])
            music = maimaidx_music.total_list.by_id(chart_id)
            chart: Dict[Any] = music['charts'][level_index]
            tap = int(chart['notes'][0])
            slide = int(chart['notes'][2])
            hold = int(chart['notes'][1])
            touch = int(chart['notes'][3]) if len(chart['notes']) == 5 else 0
            brk = int(chart['notes'][-1])
            total_score = 500 * tap + slide * 1500 + hold * 1000 + touch * 500 + brk * 2500
            break_bonus = 0.01 / brk
            break_50_reduce = total_score * break_bonus / 4
            reduce = 101 - line
            if reduce <= 0 or reduce >= 101:
                raise ValueError
            await app.send_message(group, MessageChain(f'''{music['title']} {level_labels2[level_index]}
分数线 {line}% 允许的最多 TAP GREAT 数量为 {(total_score * reduce / 10000):.2f}(每个-{10000 / total_score:.4f}%),
BREAK 50落(一共{brk}个)等价于 {(break_50_reduce / 100):.3f} 个 TAP GREAT(-{break_50_reduce / total_score * 100:.4f}%)'''))
        except Exception:
            await app.send_message(group, MessageChain('格式错误，输入“分数线 帮助”以查看帮助信息'))


# 今日mai
wm_list = ['拼机', '推分', '越级', '下埋', '夜勤', '练底力', '练手法', '打旧框', '干饭', '抓绝赞', '收歌']


@channel.use(ListenerSchema(listening_events=[GroupMessage, NudgeEvent]))
async def _(app: Ariadne, group: Group, member: Member, message: MessageChain = DetectPrefix(['今日舞萌', '今日mai'])):
    qq = int(member.id)
    h = tool.hash(qq)
    rp = h % 100
    wm_value = []
    for i in range(11):
        wm_value.append(h & 3)
        h >>= 2
    s = f'今日人品值:{rp}\n'
    for i in range(11):
        if wm_value[i] == 3:
            s += f'宜 {wm_list[i]}\n'
        elif wm_value[i] == 0:
            s += f'忌 {wm_list[i]}\n'
    s += '平哥提醒您：打机时不要大力拍打或滑动哦\n今日推荐歌曲：'
    music = maimaidx_music.total_list[h % len(maimaidx_music.total_list)]
    await app.send_message(group, MessageChain(
        s, music.id + '. ' + music.title + '\n',
        Image(url='https://www.diving-fish.com/covers/' + maimaidx_music.get_cover_len5_id(music.id) + '.png'),
        f"\n{'/'.join(music.level)}"))


# 铺面信息
@channel.use(ListenerSchema(listening_events=[GroupMessage, NudgeEvent], decorators=[MatchRegex(regex=r"^([绿黄红紫白]?)id([0-9]+)")]))
async def _(app: Ariadne, group: Group, member: Member,
            message: MessageChain):
    regex = "([绿黄红紫白]?)id([0-9]+)"
    groups = re.match(regex, str(message)).groups()
    print(groups[0])
    level_labels = ['绿', '黄', '红', '紫', '白']
    if groups[0] != "":
        try:
            level_index = level_labels.index(groups[0])
            level_name = ['Basic', 'Advanced', 'Expert', 'Master', 'Re: MASTER']
            name = groups[1]
            music = maimaidx_music.total_list.by_id(name)
            print(music)
            chart = music['charts'][level_index]
            ds = music['ds'][level_index]
            level = music['level'][level_index]
            file = f"https://www.diving-fish.com/covers/{maimaidx_music.get_cover_len5_id(music['id'])}.png"
            if len(chart['notes']) == 4:
                msg = f'''{level_name[level_index]} {level}({ds})
TAP: {chart['notes'][0]}
HOLD: {chart['notes'][1]}
SLIDE: {chart['notes'][2]}
BREAK: {chart['notes'][3]}
谱师: {chart['charter']}'''
            else:
                msg = f'''{level_name[level_index]} {level}({ds})
TAP: {chart['notes'][0]}
HOLD: {chart['notes'][1]}
SLIDE: {chart['notes'][2]}
TOUCH: {chart['notes'][3]}
BREAK: {chart['notes'][4]}
谱师: {chart['charter']}'''
            await app.send_message(group,
                                   MessageChain(f"{music['id']}. {music['title']}\n",
                                                Image(url=file), msg
                                                )
                                   )
        except Exception as e:
            await app.send_message(group, str(e))
    else:
        name = groups[1]
        music = maimaidx_music.total_list.by_id(name)
        try:
            file = f"https://www.diving-fish.com/covers/{maimaidx_music.get_cover_len5_id(music['id'])}.png"
            await app.send_message(
                group,
                MessageChain(f"{music['id']}. {music['title']}\n",
                             Image(url=file),
                             f"艺术家: {music['basic_info']['artist']}\n分类: {music['basic_info']['genre']}\nBPM: {music['basic_info']['bpm']}\n版本: {music['basic_info']['from']}\n难度: {'/'.join(music['level'])}"
                             )
            )
        except Exception:
            await app.send_message(group, MessageChain("未找到该乐曲"))


# 查歌
@channel.use(ListenerSchema(listening_events=[GroupMessage, NudgeEvent], decorators=[MatchRegex(regex=r"^查歌.+")]))
async def _(app: Ariadne, group: Group, member: Member,
            message: MessageChain):
    regex = "查歌(.+)"
    name = re.match(regex, str(message)).groups()[0].strip()
    if name == "":
        return
    res = maimaidx_music.total_list.filter(title_search=name)
    if len(res) == 0:
        await app.send_message(group, MessageChain('没有找到这样的乐曲。'))
    elif len(res) < 50:
        search_result = ""
        for music in sorted(res, key=lambda i: int(i['id'])):
            search_result += f"{music['id']}. {music['title']}\n"
        await app.send_message(group, MessageChain(search_result.strip()))
    else:
        await app.send_message(group, MessageChain(f"结果过多（{len(res)} 条），请缩小查询范围。"))


# mai什么
@channel.use(ListenerSchema(listening_events=[GroupMessage, NudgeEvent], decorators=[MatchRegex(regex=r".*mai.*什么")]))
async def _(app: Ariadne, group: Group, member: Member,
            message: MessageChain):
    await app.send_message(group, song_txt(maimaidx_music.total_list.random()))


# 随个谱
@channel.use(ListenerSchema(listening_events=[GroupMessage, NudgeEvent], decorators=[MatchRegex(regex=r"^随个(?:dx|sd|标准)?[绿黄红紫白]?[0-9]+\+?")]))
async def _(app: Ariadne, group: Group, member: Member,
            message: MessageChain):
    regex = "随个((?:dx|sd|标准))?([绿黄红紫白]?)([0-9]+\+?)"
    res = re.match(regex, str(message).lower())
    try:
        if res.groups()[0] == "dx":
            tp = ["DX"]
        elif res.groups()[0] == "sd" or res.groups()[0] == "标准":
            tp = ["SD"]
        else:
            tp = ["SD", "DX"]
        level = res.groups()[2]
        if res.groups()[1] == "":
            music_data = maimaidx_music.total_list.filter(level=level, type=tp)
        else:
            music_data = maimaidx_music.total_list.filter(level=level, diff=['绿黄红紫白'.index(res.groups()[1])], type=tp)
        if len(music_data) == 0:
            rand_result = "没有这样的乐曲哦。"
        else:
            rand_result = song_txt(music_data.random())
            await app.send_message(group, MessageChain(rand_result))
    except Exception as e:
        print(e)
        await app.send_message(group, MessageChain("随机命令错误，请检查语法"))


# 查定数
@channel.use(ListenerSchema(listening_events=[GroupMessage, NudgeEvent]))
async def _(app: Ariadne, group: Group, member: Member,
            message: MessageChain = DetectPrefix(['inner_level', '定数查歌 ', '定数'])):
    argv = str(message).strip().split(' ')
    print(argv)
    if len(argv) > 2 or len(argv) == 0:
        print("123" + str(len(argv)))
        print(1)
        await app.send_message(group, MessageChain("命令格式为\n定数查歌 <定数>\n定数查歌 <定数下限> <定数上限>"))
        return
    elif len(argv) == 1:
        print("233" + str(len(argv)))
        print(2)
        result_set = inner_level_q(float(argv[0]))
    else:
        print(argv)
        print(1)
        result_set = inner_level_q(float(argv[0]), float(argv[1]))
    if len(result_set) > 50:
        await app.send_message(group, MessageChain(f"结果过多（{len(result_set)} 条），请缩小搜索范围。"))
        return
    s = ""
    for elem in result_set:
        s += f"{elem[0]}. {elem[1]} {elem[3]} {elem[4]}({elem[2]})\n"
    await app.send_message(group, MessageChain(s.strip()))


# 帮助
@channel.use(ListenerSchema(listening_events=[GroupMessage, NudgeEvent]))
async def _(app: Ariadne, group: Group, member: Member,
            message: MessageChain = DetectPrefix(['maihelp', 'mai帮助'])):
    help_str = '''可用命令如下：
    今日舞萌 查看今天的舞萌运势
    XXXmaimaiXXX什么 随机一首歌
    随个[dx/标准][绿黄红紫白]<难度> 随机一首指定条件的乐曲
    查歌<乐曲标题的一部分> 查询符合条件的乐曲
    [绿黄红紫白]id<歌曲编号> 查询乐曲信息或谱面信息
    <歌曲别名>是什么歌 查询乐曲别名对应的乐曲
    定数查歌 <定数>  查询定数对应的乐曲
    定数查歌 <定数下限> <定数上限>
    分数线 <难度+歌曲id> <分数线> 详情请输入“分数线 帮助”查看'''
    await app.send_message(group, MessageChain(help_str))