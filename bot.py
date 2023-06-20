from urllib.parse import quote
import discord
import requests
from discord.ext import commands
import svg

from function import convert_time_to_hours, get_bfv_stats, generate_bfban_link, get_ban_status

# from translations import translations

intents = discord.Intents.default()
intents.message_content = True
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)


# 在机器人启动时获取 token
@bot.event
async def on_ready():
    print(f'Bot is ready. Connected as {bot.user}')


@bot.command()
async def helps(ctx):
    embed = discord.Embed(title="指令列表", description="下面是可用的指令列表：", color=discord.Color.gold())
    embed.add_field(name="!checkBan <names>", value="检查玩家封禁状态", inline=False)
    embed.add_field(name="!report", value="举报玩家", inline=False)
    embed.add_field(name="!getPlayerStats <names>", value="查询玩家简易生涯信息", inline=False)
    embed.add_field(name="!getPlayerAll <names>", value="查询玩家全部生涯信息", inline=False)
    await ctx.send(embed=embed)
    embed2 = discord.Embed(title="command list", description="Below is the list of available commands：",
                           color=discord.Color.gold())
    embed2.add_field(name="!checkBan <names>", value="Check player ban status", inline=False)
    embed2.add_field(name="!report", value="report player", inline=False)
    embed2.add_field(name="!getPlayerStats <names>", value="Query player simple career information", inline=False)
    embed2.add_field(name="!getPlayerAll <names>", value="Query player all career information", inline=False)
    await ctx.send(embed=embed2)


@bot.command()
async def login(ctx):
    # 获取 token
    signin_url = "https://bfban.gametools.network/api/user/signin"
    get_captcha_url = "https://bfban.gametools.network/api/captcha"
    captcha_response = requests.get(get_captcha_url)
    captcha_data = captcha_response['data']
    captcha_hash_value = captcha_data['hash']
    content = captcha_response['content']
    pic = svg.str_svg_2_png(content)

    # 发送并验证登录
    if captcha_response:
        await ctx.send(pic)
        captcha_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        captcha_value = captcha_message.content

        # 替换为实际的用户名和密码
        username = "DiscordBot"
        password = "discor"

        payload = {
            "data": {
                "username": username,
                "password": password,
                "EXPIRES_IN": 1209600000  # 可选项，过期时间（以毫秒为单位），只在 bot/dev 帐户中有效
            },
            "encryptCaptcha": captcha_hash_value,
            "captcha": captcha_value
        }

        response = requests.post(signin_url, json=payload)

        if response.status_code == 200:
            signin_data = response.json()
            if signin_data.get('success') == 1:
                token = signin_data['data']['token']
                print("Token obtained successfully:", token)
            else:
                print("Failed to obtain token:", signin_data.get('message'))
        else:
            print("Signin request failed with status code:", response.status_code)


@bot.command()
async def getPlayerAll(ctx, player_name):
    url = f"https://api.gametools.network/bfv/all/?format_values=true&name={player_name}&platform=pc&lang=zh-cn"
    response = requests.get(url)
    data = response.json()
    print(data)
    if "error" in data:
        await ctx.send(f"发生错误：{data['error']}")
    else:
        embed = discord.Embed(title="玩家状态", color=discord.Color.blue())
        embed.set_thumbnail(url='https://s2.loli.net/2023/05/20/fi6mjVW8zgUuOZt.png')
        # 添加参数字段
        embed.add_field(name="用户名", value=data.get('userName', ''), inline=True)
        embed.add_field(name="等级", value=data.get('rank', ''), inline=True)
        embed.add_field(name="SPM", value=data.get('scorePerMinute', ''), inline=True)
        embed.add_field(name="KPM", value=data.get('killsPerMinute', ''), inline=True)
        embed.add_field(name="胜率", value=data.get('winPercent', ''), inline=True)
        embed.add_field(name="最佳兵种", value=data.get('bestClass', ''), inline=True)
        embed.add_field(name="acc", value=data.get('accuracy', ''), inline=True)
        embed.add_field(name="爆头率", value=data.get('headshots', ''), inline=True)
        embed.add_field(name="游戏时间", value=data.get('timePlayed', ''), inline=True)
        embed.add_field(name="KD", value=data.get('killDeath', ''), inline=True)
        embed.add_field(name="步兵KD", value=data.get('infantryKillDeath', ''), inline=True)
        embed.add_field(name="步兵KPM", value=data.get('infantryKillsPerMinute', ''), inline=True)
        embed.add_field(name="Kills", value=data.get('kills', ''), inline=True)
        embed.add_field(name="Deaths", value=data.get('deaths', ''), inline=True)
        embed.add_field(name="Wins", value=data.get('wins', ''), inline=True)
        embed.add_field(name="Loses", value=data.get('loses', ''), inline=True)
        embed.add_field(name="最长爆头距离", value=data.get('longestHeadShot', ''), inline=True)
        embed.add_field(name="救援数", value=data.get('revives', ''), inline=True)
        embed.add_field(name="抢夺狗牌数", value=data.get('dogtagsTaken', ''), inline=True)
        embed.add_field(name="最高连杀数", value=data.get('highestKillStreak', ''), inline=True)
        embed.add_field(name="总局数", value=data.get('roundsPlayed', ''), inline=True)
        embed.add_field(name="爆头击杀数", value=data.get('headShots', ''), inline=True)
        embed.add_field(name="治疗数", value=data.get('heals', ''), inline=True)
        embed.add_field(name="助攻击杀数", value=data.get('killAssists', ''), inline=True)
        await ctx.send(embed=embed)
        # 编译weapons字段
        weapons = data.get('weapons', [])
        weapons.sort(key=lambda w: w.get('kills', 0), reverse=True)  # 按击杀数降序排序
        weapons_info = ''

        for weapon in weapons[:10]:  # 只输出前十个武器
            name = weapon.get('weaponName', '')
            kills = weapon.get('kills', '')
            accuracy = weapon.get('accuracy', '')
            weapontype = weapon.get('type', '')
            killsPerMinute = weapon.get('killsPerMinute', '')
            headshots = weapon.get('headshots', '')
            hitVKills = weapon.get('hitVKills', '')
            weapon_info = f"**{name}** 类型:{weapontype}\n击杀数:{kills}  KPM:{killsPerMinute}\n命中率：{accuracy}  爆头率:{headshots}   效率:{hitVKills}\n\n"
            weapons_info += weapon_info

        # 编译vehicles字段
        vehicles = data.get('vehicles', [])
        vehicles.sort(key=lambda v: v.get('kills', 0), reverse=True)  # 按击杀数降序排序
        vehicles_info = ''

        for vehicle in vehicles[:10]:  # 只输出前十个载具
            name = vehicle.get('vehicleName', '')
            vehicletype = vehicle.get('type', '')
            kills = vehicle.get('kills', '')
            killsPerMinute = vehicle.get('killsPerMinute', '')
            vehicle_info = f"**{name}** 类型:{vehicletype}\n击杀数:{kills}   KPM:{killsPerMinute}\n\n"
            vehicles_info += vehicle_info

        # 编译platoons字段
        platoons = data.get('platoons', [])
        platoons_info = ''

        for platoon in platoons:
            name = platoon.get('name', '')
            tag = platoon.get('tag', '')
            emblem = platoon.get('emblem', '')
            platoon_url = platoon.get('url', '')
            platoon_info: str = f"**{tag} - {name}**\n"
            if emblem:
                platoon_info += f"Emblem: [link]({emblem})\n"
            platoon_info += f"URL: [link]({platoon_url})\n\n"
            platoons_info += platoon_info

        # 发送weapons信息 将embed发送到Discord
        embed1 = discord.Embed(title="武器信息", color=discord.Color.blue())
        embed1.set_thumbnail(url='https://s2.loli.net/2023/05/20/fi6mjVW8zgUuOZt.png')
        embed1.add_field(name="武器信息", value=weapons_info, inline=False)
        await ctx.send(embed=embed1)
        # 发送vehicles信息
        embed2 = discord.Embed(title="载具信息", color=discord.Color.blue())
        embed2.add_field(name="载具信息", value=vehicles_info, inline=False)
        embed2.set_thumbnail(url='https://s2.loli.net/2023/05/20/fi6mjVW8zgUuOZt.png')
        await ctx.send(embed=embed2)
        # 发送platoons信息
        embed3 = discord.Embed(title="团队信息", color=discord.Color.blue())
        embed3.add_field(name="团队信息", value=platoons_info, inline=False)
        await ctx.send(embed=embed3)


@bot.command()
async def checkBan(ctx, names):
    try:
        ban_data = get_ban_status(names)
        ban_info = ban_data['names'].get(names.lower())

        if ban_info:
            origin_persona_id = ban_info['originPersonaId']
            bfban_link = generate_bfban_link(origin_persona_id)
            status = ban_info['status']
            is_hacker = ban_info['hacker']
            origin_id = ban_info['originId']
            origin_persona_id = ban_info['originPersonaId']
            origin_user_id = ban_info['originUserId']
            cheat_methods = ban_info['cheatMethods']
            embed = discord.Embed(title=f'Ban Status for {names}', color=discord.Color.green())
            if not cheat_methods:
                is_hacker = False
            if status == 0:
                status = "待处理/即将石锤"
            if status == 1:
                status = "石锤"
                embed = discord.Embed(title=f'Ban Status for {names}', color=discord.Color.red())
            if status == 2:
                status = "待自证"
            if status == 5:
                status = "讨论中"
            if status == 8:
                status = "刷枪"
            if status == 3:
                status = "MOSS自证"

            # 创建富文本消息
            embed.add_field(name='URL', value=bfban_link)
            embed.add_field(name='Status', value=status)
            embed.add_field(name='Is Hacker', value=is_hacker)
            embed.add_field(name='Origin ID', value=origin_id)
            embed.add_field(name='Origin Persona ID', value=origin_persona_id)
            embed.add_field(name='Origin User ID', value=origin_user_id)

            # 设置卡片图片
            embed.set_thumbnail(url='https://s2.loli.net/2023/05/20/fi6mjVW8zgUuOZt.png')
            # 发送富文本消息到 Discord
            await ctx.send(embed=embed)
        else:
            await ctx.send("No ban information found for the specified name.")
    except Exception as e:
        await ctx.send(f'An error occurred while fetching BFBAN data: {e}')


def validate_player_name(name):
    encoded_name = quote(name)
    url = f"https://api.gametools.network/bfv/stats/?format_values=true&name={encoded_name}&platform=pc&lang=zh-cn"
    response = requests.get(url)
    data = response.json()
    if "error" in data:
        return False, data["error"]
    elif "userName" in data and data["userName"] == name:
        return True, ""
    else:
        return False, "找不到该玩家。"


@bot.command(name='report')
async def report(ctx):
    try:
        await ctx.send("请输入游戏名称（bf1 或 bfv）：")
        game_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        game = game_message.content.lower()

        if game == "cancel" or game == "取消":
            await ctx.send("举报操作已取消。")
            return

        await ctx.send("请输入玩家名称：")
        originName_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        originName = originName_message.content

        valid, error_message = validate_player_name(originName)
        if not valid:
            await ctx.send(f"无效的玩家名称：{error_message}")
            return

        stats_data = get_bfv_stats(originName)
        userId = stats_data['id']

        # Check if player has any cases in BFBan
        bfban_cases_url = f"https://bfban.gametools.network/api/player?userId={userId}"
        bfban_cases_response = requests.get(bfban_cases_url)
        bfban_cases_data = bfban_cases_response.json()

        if 'data' in bfban_cases_data and bfban_cases_data['data']:
            bfban_link = generate_bfban_link(userId)
            await ctx.send(
                f"注意：该玩家已经有在 BFBan 中的举报案件记录。\n已有案件的 BFBan 页面链接：{bfban_link}\n是否要继续举报？\n回复 `是` 继续举报，回复 `否` 取消举报。")
            confirm_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            confirm = confirm_message.content.lower()

            if confirm == "是":
                pass
            elif confirm == "否":
                await ctx.send("已取消举报操作。")
                return
            else:
                await ctx.send("无效的回复，已取消举报操作。")
                return

        await ctx.send("请输入举报描述：")
        description_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        description = description_message.content
        print(description)

        # Obtain the captcha from the API
        captcha_url = "https://bfban.gametools.network/api/captcha"
        captcha_response = requests.get(captcha_url)
        captcha_data = captcha_response.json()

        if captcha_data.get('success') == 1:
            hash_value = captcha_data['data']['hash']
            # svg_content = captcha_data['data']['content']

            # await ctx.send("请输入验证码：")
            # captcha_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            # captcha = captcha_message.content

            # Prepare the request payload
            report_url = "https://bfban.gametools.network/api/player/report"
            payload = {
                "data": {
                    "game": game,
                    "originName": originName,
                    "cheatMethods": "aimbot",
                    "videoLink": "",
                    "description": description
                },
                "encryptCaptcha": hash_value,
                "captcha": " "
            }

            # Sign in to obtain the token
            signin_url = "https://bfban.gametools.network/api/user/signin"
            signin_payload = {
                "data": {
                    "username": "username",
                    "password": "password",
                    "EXPIRES_IN": 86400000  # 24 hours expiration time
                },
                "encryptCaptcha": hash_value,
                "captcha": " "
            }
            signin_response = requests.post(signin_url, json=signin_payload)
            signin_data = signin_response.json()

            if signin_data.get('success') == 1:
                token = signin_data['data']['token']
                headers = {
                    "x-access-token": token
                }

                # Send the report request with the token in the headers
                report_response = requests.post(report_url, json=payload, headers=headers)
                report_data = report_response.json()

                if report_data.get('success') == 1:
                    await ctx.send("举报成功！")
                    await ctx.send(f"案件页面链接：{ctx.author.name}")
                else:
                    await ctx.send(f"举报失败：{report_data.get('message')}")
            else:
                await ctx.send("登录失败，无法获取令牌。")
        else:
            await ctx.send("获取验证码失败。")

    except Exception as e:
        await ctx.send(f"举报过程中出现错误：{str(e)}")


@bot.command()
async def getPlayerStats(ctx, names):
    try:
        stats_data = get_bfv_stats(names)
        # 提取所需的玩家数据
        playerName = stats_data['userName']
        UserID = stats_data['id']
        rank = stats_data['rank']
        kills = stats_data['kills']
        deaths = stats_data['deaths']
        scorePerMinute = stats_data['scorePerMinute']
        killsPerMinute = stats_data['killsPerMinute']
        winPercent = stats_data['winPercent']
        accuracy = stats_data['accuracy']
        headshots = stats_data['headshots']
        # 创建富文本消息
        embed = discord.Embed(title=f'{playerName} 的生涯统计', color=discord.Color.blue())
        embed.add_field(name='ID', value=UserID)
        embed.add_field(name='等级', value=rank)
        embed.add_field(name='击杀数', value=kills)
        embed.add_field(name='死亡数', value=deaths)
        time_played = convert_time_to_hours(stats_data['timePlayed'])
        embed.add_field(name='游戏时长', value=f'{time_played:.2f}')
        embed.add_field(name='SPM', value=scorePerMinute)
        embed.add_field(name='KPM', value=killsPerMinute)
        embed.add_field(name='胜率', value=winPercent)
        embed.add_field(name='acc', value=accuracy)
        embed.add_field(name='爆头率', value=headshots)
        # 设置卡片图片
        embed.set_thumbnail(url='https://s2.loli.net/2023/05/20/fi6mjVW8zgUuOZt.png')
        # 发送富文本消息到 Discord
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f'获取玩家生涯信息时发生错误：{e}')


# 运行机器人
bot.run('MTEwOTEzMjE2NjEzNjM0MDU4MA.GXFNgo.F6dXYjZbqH5FGAdikdCKfbh0O9dgL97i503Xgw')
