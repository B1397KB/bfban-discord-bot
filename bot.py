import aiohttp
import discord
import requests
import json
from discord.ext import commands
import time
import function
import svg

from function import convert_time_to_hours, get_bfv_stats, generate_bfban_link, check_bfban_status, \
    get_bfban_dbid, validate_player_name, write_config

# from translations import translations
intents = discord.Intents.default()
intents.message_content = True
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)

# 读取配置文件
def read_config():
    with open('config.json', 'r') as f:
        config = json.load(f)
    return config

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
    embed.add_field(name="!banAppeals", value="石锤玩家申诉", inline=False)
    embed.add_field(name="!bfbanTimeline <names>", value="查询玩家在bfban案件的时间轴", inline=False)
    embed.add_field(name="!sitestats", value="查询网站统计", inline=False)
    await ctx.send(embed=embed)
    embed2 = discord.Embed(title="command list", description="Below is the list of available commands：",
                           color=discord.Color.gold())
    embed2.add_field(name="!checkBan <names>", value="Check player ban status", inline=False)
    embed2.add_field(name="!report", value="report player", inline=False)
    embed2.add_field(name="!getPlayerStats <names>", value="Query player simple career information", inline=False)
    embed2.add_field(name="!getPlayerAll <names>", value="Query player all career information", inline=False)
    embed2.add_field(name="!banAppeals", value="confirmed player appeal", inline=False)
    embed2.add_field(name="!bfbanTimeline <names>", value="Query the timeline of players in bfban.com", inline=False)
    embed2.add_field(name="!sitestats", value="Search bfban.com website statistics")
    await ctx.send(embed=embed2)

@commands.check(function.is_allowed_user)
@bot.command()
async def login(ctx):
    # 其他指令的实现代码
    async with aiohttp.ClientSession() as session:
        # 获取 token
        signin_url = "https://bfban.gametools.network/api/user/signin"
        get_captcha_url = "https://bfban.gametools.network/api/captcha"
        captcha_response = await session.get(get_captcha_url)
        captcha_data = await captcha_response.json()
        captcha_hash_value = captcha_data['data']['hash']
        content = captcha_data['data']['content']
        pic = svg.str_svg_2_png(content)

        # 发送并验证登录
        if captcha_response:
            file = discord.File(pic, filename="captcha.png")
            await ctx.send(file=file)
            captcha_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            captcha_value = captcha_message.content
            # json内替换为实际的用户名和密码
            configjson = read_config()
            username = configjson['bfban_account']
            password = configjson['bfban_account_password']

            payload = {
                "data": {
                    "username": username,
                    "password": password,
                    "EXPIRES_IN": 1209600000  # 可选项，过期时间（以毫秒为单位），只在 bot/dev中有效
                },
                "encryptCaptcha": captcha_hash_value,
                "captcha": captcha_value
            }

            async with session.post(signin_url, json=payload) as response:
                if response.status == 200:
                    signin_data = await response.json()
                    if signin_data.get('success') == 1:
                        bfban_token = signin_data['data']['token']
                        # 清空 bfban_token 字段内容
                        configjson['bfban_token'] = ""
                        write_config(configjson)
                        # 将 bfban_token 写入 config.json
                        configjson['bfban_token'] = bfban_token
                        write_config(configjson)
                        await ctx.send("登录成功")
                        print("Token obtained successfully:", bfban_token)
                    else:
                        print("Failed to obtain token:", signin_data.get('message'))
                else:
                    print("Signin request failed with status code:", response.status)


@bot.command()
async def sitestats(ctx):
    url = 'https://bfban.gametools.network/api/statistics?reports=%27%27&players=%27%27&confirmed=%27%27&banAppeals=%27%27&registers=%27%27&from=1514764800000'
    response = requests.get(url=url)
    stats_data = response.json()
    if stats_data.get('success') == 1:
        reports = stats_data['data']['reports']
        players = stats_data['data']['players']
        confirmed = stats_data['data']['confirmed']
        registers = stats_data['data']['registers']
        ban_appeals = stats_data['data']['banAppeals']
        embed = discord.Embed(title="Site Statistics", color=discord.Color.gold())
        if reports:
            embed.add_field(name="A total of bfban.com has been reported", value=str(reports), inline=False)
        if players:
            embed.add_field(name="Existing reported cases", value=str(players), inline=False)
        if confirmed:
            embed.add_field(name="Cases handled", value=str(confirmed), inline=False)
        if registers:
            embed.add_field(name="Registered user", value=str(registers), inline=False)
        if ban_appeals:
            embed.add_field(name="Appealed", value=str(ban_appeals), inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("无法获取站点统计信息。")

@bot.command()
async def getPlayerAll(ctx, player_name):
    url = f"https://api.gametools.network/bfv/all/?format_values=true&name={player_name}&platform=pc&lang=en-us"
    response = requests.get(url)
    data = response.json()
    if "error" in data:
        await ctx.send(f"An error occurred：{data['error']}")
    else:
        embed = discord.Embed(title="Player state", color=discord.Color.blue())
        embed.set_thumbnail(url='https://s2.loli.net/2023/05/20/fi6mjVW8zgUuOZt.png')
        # 添加参数字段
        embed.add_field(name="username", value=data.get('userName', ''), inline=True)
        embed.add_field(name="rank", value=data.get('rank', ''), inline=True)
        embed.add_field(name="SPM", value=data.get('scorePerMinute', ''), inline=True)
        embed.add_field(name="KPM", value=data.get('killsPerMinute', ''), inline=True)
        embed.add_field(name="winPercnet", value=data.get('winPercent', ''), inline=True)
        embed.add_field(name="bestClass", value=data.get('bestClass', ''), inline=True)
        embed.add_field(name="acc", value=data.get('accuracy', ''), inline=True)
        embed.add_field(name="headshots", value=data.get('headshots', ''), inline=True)
        embed.add_field(name="timePlayed", value=data.get('timePlayed', ''), inline=True)
        embed.add_field(name="KD", value=data.get('killDeath', ''), inline=True)
        embed.add_field(name="infantryKD", value=data.get('infantryKillDeath', ''), inline=True)
        embed.add_field(name="infantryKPM", value=data.get('infantryKillsPerMinute', ''), inline=True)
        embed.add_field(name="Kills", value=data.get('kills', ''), inline=True)
        embed.add_field(name="Deaths", value=data.get('deaths', ''), inline=True)
        embed.add_field(name="Wins", value=data.get('wins', ''), inline=True)
        embed.add_field(name="Loses", value=data.get('loses', ''), inline=True)
        embed.add_field(name="longestHeadShot", value=data.get('longestHeadShot', ''), inline=True)
        embed.add_field(name="revives", value=data.get('revives', ''), inline=True)
        embed.add_field(name="dogtagsTaken", value=data.get('dogtagsTaken', ''), inline=True)
        embed.add_field(name="highestKillStreak", value=data.get('highestKillStreak', ''), inline=True)
        embed.add_field(name="roundsPlayed", value=data.get('roundsPlayed', ''), inline=True)
        embed.add_field(name="headShots", value=data.get('headShots', ''), inline=True)
        embed.add_field(name="heals", value=data.get('heals', ''), inline=True)
        embed.add_field(name="killAssists", value=data.get('killAssists', ''), inline=True)
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
            weapon_info = f"**{name}** Type:{weapontype}\nKills:{kills}  KPM:{killsPerMinute}\nACC：{accuracy}  HS:{headshots}   hitVKills:{hitVKills}\n\n"
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
            vehicle_info = f"**{name}** Type:{vehicletype}\nKills:{kills}   KPM:{killsPerMinute}\n\n"
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
        embed1 = discord.Embed(title="Weapon Information", color=discord.Color.blue())
        embed1.set_thumbnail(url='https://s2.loli.net/2023/05/20/fi6mjVW8zgUuOZt.png')
        embed1.add_field(name="weapon information", value=weapons_info, inline=False)
        await ctx.send(embed=embed1)
        # 发送vehicles信息
        embed2 = discord.Embed(title="Vehicle Information", color=discord.Color.blue())
        embed2.add_field(name="Vehicle information", value=vehicles_info, inline=False)
        embed2.set_thumbnail(url='https://s2.loli.net/2023/05/20/fi6mjVW8zgUuOZt.png')
        await ctx.send(embed=embed2)
        # 发送platoons信息
        embed3 = discord.Embed(title="Platoon Information", color=discord.Color.blue())
        embed3.add_field(name="Platoon Information", value=platoons_info, inline=False)
        await ctx.send(embed=embed3)

@bot.command()
async def checkBan(ctx, names):
    try:
        ban_info = function.get_bfban_playerinfo(names)
        ban_data = ban_info['data']
        if ban_info:
            origin_persona_id = ban_data['originPersonaId']
            bfban_link = generate_bfban_link(origin_persona_id)
            origin_id = ban_data['originName']
            origin_persona_id = ban_data['originPersonaId']
            origin_user_id = ban_data['originUserId']
            cheat_methods = ban_data['cheatMethods']
            games = ban_data['games']
            games = list(games)  # 将 cheat_methods 转换为列表类型
            embed = discord.Embed(title=f'bfban.com Status for {names}', color=discord.Color.green())
            status = function.get_bfban_status(names)
            if status == "Confirmed hacker":
                embed = discord.Embed(title=f'Ban Status for {names}', color=discord.Color.red())
            # 创建富文本消息
            embed.add_field(name='URL', value=bfban_link)
            embed.add_field(name='Status', value=status)
            embed.add_field(name='Games', value=games)
            if cheat_methods:
                cheat_methods = list(cheat_methods)  # 将 cheat_methods 转换为列表类型
                embed.add_field(name='Cheat Methods', value=', '.join(cheat_methods))
            else:
                embed.add_field(name='Cheat Methods', value='None')
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


@bot.command(name='report')
async def report(ctx):
    try:
        await ctx.send("Please enter the game name (bf1 or bfv):")
        game_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        game = game_message.content.lower()
        if game != "bfv" and game != "bf1":
            await ctx.send("Wrong game, report operation has been cancelled.")
            return

        if game == "cancel" or game == "取消":
            await ctx.send("Report action canceled.")
            return

        await ctx.send("Please enter a player name:")
        originName_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        originName = originName_message.content

        valid, error_message = validate_player_name(originName)
        if not valid:
            await ctx.send(f"invalid player name: {error_message}")
            return

        stats_data = get_bfv_stats(originName)
        userId = stats_data['id']

        if check_bfban_status(originName) == "player.ok":
            bfban_link = generate_bfban_link(userId)
            await ctx.send(
                f"Note: This player already has a reported case record in the BFBan. \nLink to the BFBan page of the existing case: {bfban_link}\nDo you want to continue reporting? \nReply `Yes` to continue the report, reply `No` to cancel the report.")
            confirm_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            confirm = confirm_message.content.lower()

            if confirm == "是" and confirm == "yes" and confirm == "Yes":
                pass
            elif confirm == "否" and confirm == "No" and confirm == "no":
                await ctx.send("Report operation has been cancelled.")
                return
            else:
                await ctx.send("Invalid reply, report operation canceled.")
                return

        await ctx.send("Please enter a report description:")
        description_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        user_description = description_message.content
        description = "This report comes from discord robots"
        if game == "bfv":
            # 描述新增战绩
            bfv_description_url = f"https://api.gametools.network/bfv/all/?format_values=true&name={originName}&platform=pc&lang=en-us"
            response = requests.get(bfv_description_url)
            description_data = response.json()
            # 添加参数字段
            userName = description_data.get('userName')
            userRank = description_data.get('rank')
            userKPM = description_data.get('killsPerMinute')
            userHS = description_data.get('headshots')
            userPlayTime = description_data.get('timePlayed')
            userPlayTime = convert_time_to_hours(userPlayTime)
            userKD = description_data.get('killDeath')
            userKills = description_data.get('kills')
            userDeaths = description_data.get('deaths')
            description += f'\n玩家用户名为:{userName} 等级:{userRank} KPM:{userKPM} 爆头率:{userHS} 游玩时间:{userPlayTime}\nKD:{userKD} Kills:{userKills} Deaths:{userDeaths}\n'
            # 编译weapons字段
            weapons = description_data.get('weapons', [])
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
                weapon_info = f"{name} 类型:{weapontype}\n击杀数:{kills}  KPM:{killsPerMinute}\n命中率：{accuracy}  爆头率:{headshots}   效率:{hitVKills}\n"
                weapons_info += weapon_info
            description += f'武器信息:\n\n{weapons_info}'
            # 编译vehicles字段
            vehicles = description_data.get('vehicles', [])
            vehicles.sort(key=lambda v: v.get('kills', 0), reverse=True)  # 按击杀数降序排序
            vehicles_info = ''

            for vehicle in vehicles[:10]:  # 只输出前十个载具
                name = vehicle.get('vehicleName', '')
                vehicletype = vehicle.get('type', '')
                kills = vehicle.get('kills', '')
                killsPerMinute = vehicle.get('killsPerMinute', '')
                vehicle_info = f"{name} 类型:{vehicletype}\n击杀数:{kills}   KPM:{killsPerMinute}\n"
                vehicles_info += vehicle_info
            description += f'载具信息:\n\n{vehicles_info}'

        elif game == "bf1":
            # 描述新增战绩
            bf1_description_url = f"https://api.gametools.network/bf1/all/?format_values=true&name={originName}&platform=pc&lang=en-us"
            response = requests.get(bf1_description_url)
            description_data = response.json()
            # 添加参数字段
            userName = description_data.get('userName')
            userRank = description_data.get('rank')
            userKPM = description_data.get('killsPerMinute')
            userHS = description_data.get('headshots')
            userPlayTime = description_data.get('timePlayed')
            userPlayTime = convert_time_to_hours(userPlayTime)
            userKD = description_data.get('killDeath')
            userKills = description_data.get('kills')
            userDeaths = description_data.get('deaths')
            description += f'\n玩家用户名为:{userName} 等级:{userRank} KPM:{userKPM} 爆头率:{userHS} 游玩时间:{userPlayTime}\nKD:{userKD} Kills:{userKills} Deaths:{userDeaths}'
            # 编译weapons字段
            weapons = description_data.get('weapons', [])
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
                weapon_info = f"{name} 类型:{weapontype}\n击杀数:{kills}  KPM:{killsPerMinute}\n命中率：{accuracy}  爆头率:{headshots}   效率:{hitVKills}\n"
                weapons_info += weapon_info
            description += f'武器信息:\n\n{weapons_info}'
            # 编译vehicles字段
            vehicles = description_data.get('vehicles', [])
            vehicles.sort(key=lambda v: v.get('kills', 0), reverse=True)  # 按击杀数降序排序
            vehicles_info = ''

            for vehicle in vehicles[:10]:  # 只输出前十个载具
                name = vehicle.get('vehicleName', '')
                vehicletype = vehicle.get('type', '')
                kills = vehicle.get('kills', '')
                killsPerMinute = vehicle.get('killsPerMinute', '')
                vehicle_info = f"{name} 类型:{vehicletype}\n击杀数:{kills}   KPM:{killsPerMinute}\n"
                vehicles_info += vehicle_info
            description += f'载具信息:\n\n{vehicles_info}'

        platoon_url = f"https://api.gametools.network/bfv/all/?format_values=true&name={originName}&platform=pc&lang=en-us"
        response = requests.get(platoon_url)
        platoons_data = response.json()
        # 编译platoons字段
        platoons = platoons_data.get('platoons', [])
        platoons_info = ''
        for platoon in platoons:
            name = platoon.get('name', '')
            tag = platoon.get('tag', '')
            emblem = platoon.get('emblem', '')
            platoon_url = platoon.get('url', '')
            platoon_info: str = f"{tag} - {name}\n"
            if emblem:
                platoon_info += f"Emblem: [link]({emblem})\n"
            platoon_info += f"URL: [link]({platoon_url})\n"
            platoons_info += platoon_info
            description += f'战排信息:\n\n{platoons_info}'

        description += f'\n\n\n以下是用户提交的描述:\n\n{user_description}'

        async with aiohttp.ClientSession() as session:
            # 获取 token
            get_captcha_url = "https://bfban.gametools.network/api/captcha"
            captcha_response = await session.get(get_captcha_url)
            captcha_data = await captcha_response.json()
            captcha_hash_value = captcha_data['data']['hash']
            content = captcha_data['data']['content']
            pic = svg.str_svg_2_png(content)

        # 发送并验证登录
        if captcha_response:
            report_url = "https://bfban.gametools.network/api/player/report"
            await ctx.send("Here is the captcha:")
            file = discord.File(pic, filename="captcha.png")
            await ctx.send(file=file)
            captcha_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            captcha_value = captcha_message.content
            config = function.read_config()
            bfban_token = config['bfban_token']
            headers = {
                "x-access-token": bfban_token
            }
            body = {
                "data": {
                    "game": game,
                    "originName": originName,
                    "cheatMethods": [
                        "aimbot"
                    ],
                    "description": description
                },
                "encryptCaptcha": captcha_hash_value,
                "captcha": captcha_value
            }

            # Send the report request with the token in the headers
            report_response = requests.post(report_url, json=body, headers=headers)
            report_data = report_response.json()

            if report_data.get('code') == "report.success":
                await ctx.send(f"{ctx.author.name}Successful report！")
                await ctx.send(f"BFBAN case page link{generate_bfban_link(userId)}")
            elif report_data.get('code') == "captcha.wrong":
                await ctx.send("Captcha code error, please report again")
            else:
                await ctx.send(f"Report failed:{report_data.get('message')}")
        else:
            await ctx.send("Failed to get captcha code.")

    except Exception as e:
        await ctx.send(f"An error occurred while reporting:{str(e)}")

@bot.command(name='banAppeals')
async def banAppeals(ctx):
    try:
        await ctx.send("Please enter a player name:")
        originName_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        originName = originName_message.content
        if originName == "cancel" or originName == "取消":
            await ctx.send("The appeal operation has been cancelled.")
            return

        valid, error_message = validate_player_name(originName)
        if not valid:
            await ctx.send(f"Invalid player name:{error_message}")
            return

        stats_data = get_bfv_stats(originName)
        userId = stats_data['id']
        code = check_bfban_status(originName)['code']
        if code != "player.ok":
            await ctx.send(
                f"Note: This player has no record of reporting cases on BFBan. \nPlease report and  Confirmed hacker before appealing.")
            await ctx.send("The appeal operation has been cancelled.")
            return
        bfban_status = check_bfban_status(originName)['data']['status']
        print(bfban_status)
        if bfban_status != "1":
            await ctx.send(
                f"Note: The player does not have a Confirmed hacker and no appeal is required. \nPlease report and Confirmed hacker before appealing.")
            await ctx.send("The appeal operation has been cancelled.")
            return

        await ctx.send("Please enter a description of your appeal:")
        description_message = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        user_description = description_message.content

        description = "This appeal comes from discord robots"
        user_id = ctx.author.id
        description += f"\nAppeal user's discord ID: {user_id}"
        description += "User's Appeal Content"
        description += f'\n\n{user_description}'
        appeal_url = "https://bfban.gametools.network/api/player/banAppeal"
        config = function.read_config()
        bfban_token = config['bfban_token']
        DBid = get_bfban_dbid(originName)
        headers = {
            "x-access-token": bfban_token
        }
        body = {
            "data": {
                "toPlayerId": DBid,
                "content": description
            }
        }
        # Send the report request with the token in the headers
        report_response = requests.post(appeal_url, json=body, headers=headers)
        report_data = report_response.json()

        if report_data.get('code') == "report.success":
            await ctx.send(f"{ctx.author.name}successful appeal！")
            await ctx.send(f"BFBAN Case page link:{generate_bfban_link(userId)}")
        else:
            await ctx.send(f"Appeal failed:{report_data.get('message')}")
    except Exception as e:
        await ctx.send(f"An error occurred during the appeal process:{str(e)}")

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
        embed = discord.Embed(title=f'{playerName} career statistics', color=discord.Color.blue())
        embed.add_field(name='ID', value=UserID)
        embed.add_field(name='rank', value=rank)
        embed.add_field(name='kills', value=kills)
        embed.add_field(name='deaths', value=deaths)
        time_played = convert_time_to_hours(stats_data['timePlayed'])
        embed.add_field(name='timeplayed', value=f'{time_played:.2f}')
        embed.add_field(name='SPM', value=scorePerMinute)
        embed.add_field(name='KPM', value=killsPerMinute)
        embed.add_field(name='winPercent', value=winPercent)
        embed.add_field(name='acc', value=accuracy)
        embed.add_field(name='headshots', value=headshots)
        # 设置卡片图片
        embed.set_thumbnail(url='https://s2.loli.net/2023/05/20/fi6mjVW8zgUuOZt.png')
        # 发送富文本消息到 Discord
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f'An error occurred while retrieving player career information:{e}')

discordtoken = read_config()['discordtoken']
# 运行机器人
bot.run(discordtoken)
