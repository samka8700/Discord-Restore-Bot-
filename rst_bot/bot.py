# -*- coding: utf-8 -*-
import asyncio
import discord
import requests
import sqlite3
import uuid
import datetime
import re
import time
from discord.ext import tasks
from itertools import cycle
from urllib import parse
from datetime import timedelta
import setting as settings
from os import system
import requests
from discord_components import DiscordComponents, Button, ButtonStyle, Select, component, interaction, SelectOption, ActionRow
from discord_webhook import DiscordEmbed, DiscordWebhook
from discord_buttons_plugin import ButtonType

intents = discord.Intents.default()
intents.guilds = True
client = discord.Client(intents=intents)
owner = []
#end_msg = "\n\n> Dev : `! ! ! CuteStar#9999`, ㅣ [Support Server](https://starserver.co.kr/)"

# Developed by Hughes#1844 | 패치 하러 왔는데 코드 너무 더러워요 (최대한 원래 코드 스타일을 따라 만들었습니다.)

def is_expired(time):
    ServerTime = datetime.datetime.now()
    ExpireTime = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M')
    if ((ExpireTime - ServerTime).total_seconds() > 0):
        return False
    else:
        return True

def embed(embedtype, embedtitle, description):
    if (embedtype == "error"):
        return discord.Embed(color=0xff0000, title=embedtitle, description=description)
    if (embedtype == "success"):
        return discord.Embed(color=0x5c6cdf, title=embedtitle, description=description)
    if (embedtype == "warning"):
        return discord.Embed(color=0xffff00, title=embedtitle, description=description)

def get_expiretime(time):
    ServerTime = datetime.datetime.now()
    ExpireTime = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M')
    if ((ExpireTime - ServerTime).total_seconds() > 0):
        how_long = (ExpireTime - ServerTime)
        days = how_long.days
        hours = how_long.seconds // 3600
        minutes = how_long.seconds // 60 - hours * 60
        return str(round(days)) + "일 " + str(round(hours)) + "시간 " + str(round(minutes)) + "분"
    else:
        return False

def make_expiretime(days):
    ServerTime = datetime.datetime.now()
    ExpireTime_STR = (ServerTime + timedelta(days=days)).strftime('%Y-%m-%d %H:%M')
    return ExpireTime_STR

def add_time(now_days, add_days):
    ExpireTime = datetime.datetime.strptime(now_days, '%Y-%m-%d %H:%M')
    ExpireTime_STR = (ExpireTime + timedelta(days=add_days)).strftime('%Y-%m-%d %H:%M')
    return ExpireTime_STR

async def exchange_code(code, redirect_url):
    data = {
        'client_id': settings.client_id,
        'client_secret': settings.client_secret,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_url
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    while True:
        r = requests.post('%s/oauth2/token' % "https://discord.com/api", data=data, headers=headers)
        if (r.status_code != 429):
            break
        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)
    return False if "error" in r.json() else r.json()

async def refresh_token(refresh_token):
    data = {
        'client_id': settings.client_id,
        'client_secret': settings.client_secret,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    while True:
        r = requests.post('%s/oauth2/token' % "https://discord.com/api", data=data, headers=headers)
        if (r.status_code != 429):
            break
        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)
    print(r.json())
    return False if "error" in r.json() else r.json()

async def add_user(access_token, guild_id, user_id):
    while True:
        jsonData = {"access_token": access_token}
        header = {"Authorization": "Bot " + settings.token}
        r = requests.put(
            f"https://discord.com/api/guilds/{guild_id}/members/{user_id}", json=jsonData, headers=header)
        if (r.status_code != 429):
            break

        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)

    if (r.status_code == 201 or r.status_code == 204):
        return True
    else:
        print(r.json())
        return False

async def get_user_profile(token):
    header = {"Authorization": token}
    res = requests.get(
        "https://discordapp.com/api/v8/users/@me", headers=header)
    print(res.json())
    if (res.status_code != 200):
        return False
    else:
        return res.json()

def start_db():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    return con, cur

def onoff_db():
    con = sqlite3.connect("onoff.db")
    cur = con.cursor()
    return con, cur

async def is_guild(id):
    con, cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    res = cur.fetchone()
    con.close()
    if (res == None):
        return False
    else:
        return True

def eb(embedtype, embedtitle, description):
    if (embedtype == "error"):
        return discord.Embed(color=0xff0000, title=":no_entry: " + embedtitle, description=description)
    if (embedtype == "success"):
        return discord.Embed(color=0x00ff00, title=":white_check_mark: " + embedtitle, description=description)
    if (embedtype == "warning"):
        return discord.Embed(color=0xffff00, title=":warning: " + embedtitle, description=description)
    if (embedtype == "loading"):
        return discord.Embed(color=0x808080, title=":gear: " + embedtitle, description=description)
    if (embedtype == "primary"):
        return discord.Embed(color=0x82ffc9, title=embedtitle, description=description)

async def is_guild_valid(id):
    if not (str(id).isdigit()):
        return False
    if not (await is_guild(id)):
        return False
    con, cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    guild_info = cur.fetchone()
    expire_date = guild_info[3]
    con.close()
    if (is_expired(expire_date)):
        return False
    return True

@client.event
async def on_ready():
    DiscordComponents(client)
    print(f"Login: {client.user}\nInvite Link: https://discord.com/oauth2/authorize?client_id={client.user.id}&permissions=8&scope=bot")
    status = cycle([f'{len(client.guilds)}개의 서버가 이용'])
    
    @tasks.loop(seconds=5)
    async def change_message():
        name = next(status)
        name = name.format(n=len(client.guilds))
        await client.change_presence(activity=discord.Game(name))

    change_message.start()  # change_message 루프 시작

    while True:
        await asyncio.sleep(1)

@client.event
async def on_message(message):

    if message.content.startswith(".영구차단"):
        if message.author.id == int(settings.admin_id):
            try:
                user_id = message.content.split(" ")[1]
                user_ip = message.content.split(" ")[2]
                p = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
                a = re.search(p, user_ip)

                if a == None:
                    return await message.channel.send("아이피를 제대로 입력 해 주세요.")
            except Exception as e:
                return await message.channel.send(embed=embed("error", "Azure User Backup", "```.영구차단 <유저아이디> <아이피> 형식으로 작성해 주세요.```"))
            con = sqlite3.connect("./data/db.db")
            cur = con.cursor()
            cur.execute(f"SELECT * FROM main WHERE id == ?;", (user_id,))
            save = cur.fetchone()
            con.close()
            if save == None:
                con = sqlite3.connect("./data/db.db")
                cur = con.cursor()
                cur.execute("INSERT INTO main VALUES(?, ?, ?);", (user_id, user_ip,user_id))
                con.commit()
                con.close()
            else:
                await message.channel.send(embed=embed("error", "Azure User Backup", "이미 등록된 유저입니다."))
                return
            await message.channel.send(embed=embed("error", "Azure User Backup", "등록이 정상적으로 완료 되엇습니다."))
        else:
            return await message.channel.send(f"<@{message.author.id}>님은 관리자가 아닙니다!")

    # 추가 패치 Hughes
    try:
        if message.author.guild_permissions.administrator:
            if (message.content == (".설정값")):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                    return
                con, cur = start_db()
                cur.execute("SELECT * FROM setting WHERE guild == ?;", (message.guild.id,))
                setting = cur.fetchone()
                con.close()
                
                if setting != None:
                    con, cur = start_db()
                    cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                    guild = cur.fetchone()
                    con.close()
                    await message.reply(f'''
```
\'{message.guild.name}\' 서버의 설정값
지급되는 권한 : {guild[1]}
이메일 필터링 : {setting[1]}
통신사 필터링 : {setting[2]}
VPN 필터링 : {setting[3]}
데이터 필터링 : {setting[4]}
IP체크 필터링 : {setting[5]}
```
''')
                else:
                    con, cur = start_db()
                    cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                    guild = cur.fetchone()
                    con.close()
                    await message.reply(f'''
```
\'{message.guild.name}\' 서버의 설정값
지급되는 권한 : {guild[1]}

필터가 활성화 되어 있지 않습니다
'.필터링 활성화' 명령어로 필터링을 활성화 해주세요
```
''')

            if (message.content == (".필터링 활성화")):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                    return
                con, cur = start_db()
                cur.execute("SELECT * FROM setting WHERE guild == ?;", (message.guild.id,))
                setting = cur.fetchone()
                con.close()
                
                if setting != None:
                    return await message.reply(f'필터링이 이미 활성화 되어 있습니다')
                else:
                    con, cur = start_db()
                    cur.execute("INSERT INTO setting VALUES(?, ?, ?, ?, ?, ?);", (message.guild.id, 'on', 'on', 'on', 'on', 'on',))
                    con.commit()
                    con.close()
                    return await message.reply(f'필터링이 활성화 되었습니다')

            if message.content.startswith(".필터링"):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                    return

                try:
                    target = message.content.split(" ")[1] # 적용할 기능
                    of = message.content.split(" ")[2] # 적용여부
                except Exception as e:
                    return await message.channel.send(embed=embed("error", "Azure User Backup", "```.필터링 <이메일/통신사/VPN/데이터/IP체크> <적용/해제> 형식으로 작성해 주세요.```"))
                
                _json = {
                    '이메일': 'email',
                    '통신사': 'isp',
                    'VPN': 'vpn',
                    '데이터': 'data',
                    'IP체크': 'ischeck',
                }
                
                if target in _json:
                    con, cur = start_db()
                    cur.execute("SELECT * FROM setting WHERE guild == ?;", (message.guild.id,))
                    setting = cur.fetchone()
                    con.close()
                    
                    if setting == None:
                        return await message.reply(f'필터링이 활성화 되어있지 않습니다\n**\'.필터링 활성화\' 명령어로 활성화 해주세요**')

                    _target = _json[target]

                    if of == '적용':
                        con, cur = start_db()
                        cur.execute(f"UPDATE setting SET {_target} = ? WHERE guild = ?;", ('on', message.guild.id,))
                        con.commit()
                        con.close()
                        return await message.reply(f'{target} 필터링이 활성화 되었습니다')
                    elif of == '해제':
                        con, cur = start_db()
                        cur.execute(f"UPDATE setting SET {_target} = ? WHERE guild = ?;", ('off', message.guild.id,))
                        con.commit()
                        con.close()
                        return await message.reply(f'{target} 필터링이 비활성화 되었습니다')
                    else:
                        return await message.channel.send(embed=embed("error", "Azure User Backup", "```.필터링 <이메일/통신사/VPN/데이터/IP체크> <적용/해제> 형식으로 작성해 주세요.```"))
                else:
                    return await message.channel.send(embed=embed("error", "Azure User Backup", "```.필터링 <이메일/통신사/VPN/데이터/IP체크> <적용/해제> 형식으로 작성해 주세요.```"))
            
            # 관리자 명령어
            if message.author.id == int(settings.admin_id):
                if message.content.startswith(".복구블랙유저"):
                    if not (await is_guild_valid(message.guild.id)):
                        await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                        return

                    try:
                        id = message.content.split(" ")[1] # 유저아이디
                    except Exception as e:
                        return await message.channel.send(embed=embed("error", "Azure User Backup", "```.복구블랙(유저/서버) <유저아이디> 형식으로 작성해 주세요.```"))
                    
                    con, cur = start_db()
                    cur.execute("INSERT INTO rb_user VALUES(?);", (id,))
                    con.commit()
                    con.close()
                    await message.reply(f'{id} 유저가 복구 불가 설정이 되었습니다')

                if message.content.startswith(".복구허용1"):
                    if not (await is_guild_valid(message.guild.id)):
                        await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                        return

                    try:
                        id = message.content.split(" ")[1] # 서버아이디
                    except Exception as e:
                        return await message.channel.send(embed=embed("error", "Azure User Backup", "```.복구허용 <서버아이디> 형식으로 작성해 주세요.```"))

                    con, cur = start_db()
                    cur.execute("INSERT INTO rb_guild VALUES(?);", (id,))
                    con.commit()
                    con.close()
                    await message.reply(f'{id} 서버를 복구 화이트리스트에 추가 하였습니다.')

                if message.content.startswith(".서버정리"):
                    await message.reply(f'서버 정리가 시작되었습니다')

                    nolicense = []
                    fewuser = []

                    async for guild in client.fetch_guilds():
                        server = guild.id

                        con, cur = start_db()
                        cur.execute("SELECT * FROM users WHERE guild_id = ?;", (server,))
                        guild_result = cur.fetchall()
                        con.close()

                        if not (await is_guild(message.guild.id)):
                            await guild.leave()
                            nolicense.append(f'{guild.name}({guild.id})')
                        elif 5 > len(guild_result):
                            await guild.leave()
                            fewuser.append(f'{guild.name}({guild.id})')

                    fewuserStr = '\n'.join(fewuser)
                    nolicenseStr = '\n'.join(nolicense)
                    await message.reply(f"""```
서버가 정리되었습니다

TOTAL {len(fewuser) + len(nolicense)}
인원 미달 {len(fewuser)}
라이센스 미등록 {len(nolicense)}

요구인원 미달 서버
{fewuserStr}

라이센스 미등록 서버
{nolicenseStr}
```""")
    except:
        pass
    # 추가 패치 Hughes

    if (message.content.startswith(".명령어")):
        if message.author.guild_permissions.administrator:
            await message.reply(embed=discord.Embed(color=0x5c6cdf, title="Azure User Backup", description=f"```ㅡㅡㅡㅡㅡ 필수명령어 ㅡㅡㅡㅡㅡ\n.등록 [라이센스] : 라이센스를 등록합니다.\n.웹훅 [웹훅] : 인증이 완료된 유저를 웹훅에 표시합니다.\n.권한 [@권한] : 인증 완료 시 부여할 역할을 지정합니다.\n.인증 : 인증 메시지를 보냅니다.\n.필터링 활성화 : 각종 필터링을 활성화 합니다.\n\nㅡㅡㅡㅡㅡ 사용자지정 ㅡㅡㅡㅡㅡ\n.커스텀인증 : 인증 메시지를 커스텀합니다.\n.색깔 : 원하는 임베드 색깔을 지정할 수 있습니다.\n.필터링 <이메일/통신사/VPN/데이터> <적용/해제>\n\nㅡㅡㅡㅡㅡ 기타명령어 ㅡㅡㅡㅡㅡ\n.설정값 : 설정된 값을 확인합니다.\n.라이센스 : 라이센스 정보를 조회합니다.\n.웹훅보기 : 인증 로그가 지정되어 있는 웹훅을 표시합니다.\n.복구 [복구키] : 지급된 복구키로 유저 복구를 시작합니다.\n.청소 [개수] : 입력한 개수만큼 메시지를 삭제합니다.\n.명령어 : 유저복구봇 모든 명령어를 확인합니다.\n.차단 [아이피] : 인증을 제한할 아이피를 지정합니다.\n.차단해제 [아이피] : 인증 제한한 아이피 차단을 해제합니다.\n.차단리스트 : 차단되어 있는 모든 아이피를 확인합니다.\n.차단모두해제 : 차단되어 있는 모든 아이피를 해제합니다.```"))

    if message.author.id == int(settings.admin_id):

        if (message.content.startswith(".생성 ")):
            amount = message.content.split(" ")[1]
            long = message.content.split(" ")[2]
            if (amount.isdigit() and int(amount) >= 1 and int(amount) <= 50):
                con, cur = start_db()
                generated_key = []
                for n in range(int(amount)):
                    key = str(uuid.uuid4())
                    generated_key.append(key)
                    cur.execute("INSERT INTO licenses VALUES(?, ?);", (key, int(long)))
                con.commit()
                con.close()
                generated_key = "\n".join(generated_key)
                await message.channel.send(embed=discord.Embed(title="생성 성공", description="디엠을 확인해주세요.", color=0x5c6cdf))
                await message.author.send(generated_key)
                webhook = DiscordWebhook(username="Azure User Backup", avatar_url="https://media.discordapp.net/attachments/1046158801180573839/1046846995660288191/3.png", url="https://discord.com/api/webhooks/1041346408088866856/rcK_gf1WddAfoOSpi_8Aeax4MKtjXTCbOdBOUp29yJZc-ZVmws9EGHbHAAUzZToMjPjO")
                eb = DiscordEmbed(title='라이센스 생성 로그', description=f'```유저 : {message.author.name}#{message.author.discriminator} ({message.author.id})\n개수 : {amount}\n기간 : {long} 일\n라이센스 : {generated_key}```', color=0x5c6cdf)
                webhook.add_embed(eb)
                webhook.execute()
            else:
                await message.channel.send(embed=embed("error", "생성 실패", "최대 50개까지 생성 가능합니다."))

        if (message.content.startswith(".서버리스트")):
            guild_list = client.guilds
            for i in guild_list:
                await message.channel.send("서버 ID: {}/ 서버 이름: {}".format(i.id, i.name))

    try:
        if message.author.guild_permissions.administrator:
            if (message.content == (".웹훅보기")):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                    return
                con, cur = start_db()
                cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                guild_info = cur.fetchone()
                con.close()
                if guild_info[4] == "no":
                    await message.channel.send(embed=embed("error", "Azure User Backup", "웹훅이 없습니다."))
                    return
                await message.reply(f"{guild_info[4]}")

            if (message.content == (".라이센스")):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "유효한 라이센스가 존재하지 않습니다."))
                    return
                con, cur = start_db()
                cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                guild_info = cur.fetchone()
                con.close()

                con, cur = start_db()
                cur.execute("SELECT * FROM users WHERE guild_id = ?;", (message.guild.id,))
                guild_result = cur.fetchall()
                con.close()

                user_list = []

                for i in range(len(guild_result)):
                    user_list.append(guild_result[i][0])
                
                new_list = []

                for v in user_list:
                    if v not in new_list:
                        new_list.append(v)

                await message.channel.send(embed=embed("success", "Azure User Backup", f"만료일 : `{guild_info[3]}`\n남은 기간 : `{get_expiretime(guild_info[3])}`\n 인증 유저 수 : `{len(new_list)}`명"))
    except:
        pass

    try:
        if (message.guild != None or message.author.id in owner or message.author.guild_permissions.administrator):
            if (message.content.startswith(".등록 ")):
                license_number = message.content.split(" ")[1]
                con, cur = start_db()
                cur.execute("SELECT * FROM licenses WHERE key == ?;", (license_number,))
                key_info = cur.fetchone()
                if (key_info == None):
                    con.close()
                    await message.channel.send(embed=embed("error", "Azure User Backup", "존재하지 않거나 이미 사용된 라이센스입니다."))
                    return
                cur.execute("DELETE FROM licenses WHERE key == ?;", (license_number,))
                con.commit()
                con.close()
                key_length = key_info[1]

                if (await is_guild(message.guild.id)):
                    con, cur = start_db()
                    cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                    guild_info = cur.fetchone()
                    expire_date = guild_info[3]
                    if (is_expired(expire_date)):
                        new_expiredate = make_expiretime(key_length)
                    else:
                        new_expiredate = add_time(expire_date, key_length)
                    cur.execute("UPDATE guilds SET expiredate = ? WHERE id == ?;", (new_expiredate, message.guild.id))
                    con.commit()
                    con.close()
                    await message.channel.send(embed=embed("success", "Azure User Backup", f"{key_length} 일 라이센스가 성공적으로 연장되었습니다."))
                    webhook = DiscordWebhook(username="Azure User Backup", avatar_url="https://media.discordapp.net/attachments/1046158801180573839/1046846995660288191/3.png", url="https://discord.com/api/webhooks/1041346408088866856/rcK_gf1WddAfoOSpi_8Aeax4MKtjXTCbOdBOUp29yJZc-ZVmws9EGHbHAAUzZToMjPjO")
                    eb = DiscordEmbed(title='서버 연장 로그', description=f'```유저 : {message.author.name}#{message.author.discriminator} ({message.author.id})\n서버 이름 : {message.guild.name}\n서버 아이디 : {message.guild.id}\n기간 : {key_length} 일\n라이센스 : {message.content.split(" ")[1]}```', color=0x5c6cdf)
                    webhook.add_embed(eb)
                    webhook.execute()
                else:
                    con, cur = start_db()
                    new_expiredate = make_expiretime(key_length)
                    recover_key = str(uuid.uuid4())[:8].upper()
                    cur.execute("INSERT INTO guilds VALUES(?, ?, ?, ?, ?, ?);", (message.guild.id, 0, recover_key, new_expiredate, "no", "파랑"))
                    con.commit()
                    con.close()
                    await message.channel.send(f"{message.author.mention}님 디엠을 확인해주세요.")
                    await message.author.send(embed=embed("success", f"{message.guild.name}", f"복구키 : **`{recover_key}`**\n복구키는 복구를 할 때 쓰이니 꼭 기억해주세요.\n.필터링 활성화 를 입력해 주세요."))
                    webhook = DiscordWebhook(username="Azure User Backup", avatar_url="https://media.discordapp.net/attachments/1046158801180573839/1046846995660288191/3.png", url="https://discord.com/api/webhooks/1041346408088866856/rcK_gf1WddAfoOSpi_8Aeax4MKtjXTCbOdBOUp29yJZc-ZVmws9EGHbHAAUzZToMjPjO")
                    eb = DiscordEmbed(title='서버 등록 로그', description=f'```유저 : {message.author.name}#{message.author.discriminator} ({message.author.id})\n서버 이름 : {message.guild.name}\n서버 아이디 : {message.guild.id}\n기간 : {key_length} 일\n라이센스 : {message.content.split(" ")[1]}```', color=0x5c6cdf)
                    webhook.add_embed(eb)
                    webhook.execute()
    except AttributeError:
        pass

    try:
        if message.author.guild_permissions.administrator:
            if (message.content == ".인증"):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                    return
                await message.delete()
                con, cur = start_db()
                cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                server_info = cur.fetchone()
                con.close()
                if server_info[5] == "파랑":
                    color = 0x5c6cdf
                if server_info[5] == "빨강":
                    color = 0xff4848
                if server_info[5] == "초록":
                    color = 0x00ff27
                if server_info[5] == "검정":
                    color = 0x010101
                if server_info[5] == "회색":
                    color = 0xd1d1d1
                await message.channel.send(embed=discord.Embed(color=color, title=f"{message.guild.name}", description=f"Please authorize your account [here](https://discord.com/api/oauth2/authorize?client_id={settings.client_id}&redirect_uri={settings.base_url}%2Fcallback&response_type=code&scope=identify%20email%20guilds.join&state={message.guild.id}) to see other channels.\n다른 채널을 보려면 [여기](https://discord.com/api/oauth2/authorize?client_id={settings.client_id}&redirect_uri={settings.base_url}%2Fcallback&response_type=code&scope=identify%20email%20guilds.join&state={message.guild.id}) 를 눌러 계정을 인증해주세요."),
                components=[
                    ActionRow(
                        Button(style=ButtonType().Link, label="인증하러 가기",
                            url=f"https://discord.com/api/oauth2/authorize?client_id={settings.client_id}&redirect_uri={settings.base_url}%2Fcallback&response_type=code&scope=identify%20email%20guilds.join&state={message.guild.id}")
                    )
                ])

            if (message.content == ".커스텀인증"):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                    return
                await message.delete()
                custom = await message.channel.send(embed=discord.Embed(title='Azure User Backup', description='설정할 인증 메시지를 입력해주세요.',color=0x5c6cdf))
                def check(msg):
                    return (msg.author.id == message.author.id)
                try:
                    msg = await client.wait_for("message", timeout=60, check=check)
                except asyncio.TimeoutError:
                    await message.channel.send(embed=discord.Embed(title="시간 초과",color=0x5c6cdf))
                con, cur = start_db()
                cur.execute("SELECT * FROM guilds WHERE id == ?;", (message.guild.id,))
                server_info = cur.fetchone()
                con.close()
                if server_info[5] == "파랑":
                    color = 0x5c6cdf
                if server_info[5] == "빨강":
                    color = 0xff4848
                if server_info[5] == "초록":
                    color = 0x00ff27
                if server_info[5] == "검정":
                    color = 0x010101
                if server_info[5] == "회색":
                    color = 0xd1d1d1
                await custom.delete()
                await msg.delete()
                await message.channel.send(embed=discord.Embed(color=color, title=f"{message.guild.name}", description=f"{msg.content}"),
                components=[
                    ActionRow(
                        Button(style=ButtonType().Link, label="인증하러 가기",
                            url=f"https://discord.com/api/oauth2/authorize?client_id={settings.client_id}&redirect_uri={settings.base_url}%2Fcallback&response_type=code&scope=identify%20email%20guilds.join&state={message.guild.id}")
                    )
                ])

            if message.content.startswith(".차단 "):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                    return
                p = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
                ip = message.content.split(" ")[1]
                a = re.search(p, ip)
                if a == None:
                    await message.reply("아이피를 제대로 입력해주세요.")
                    return
                con, cur = start_db()
                cur.execute("INSERT INTO ipban VALUES(?, ?);", (int(message.guild.id), ip))
                con.commit()
                con.close()
                await message.reply(embed=embed("success", "Azure User Backup", f"```{ip}를 차단 시켰습니다.```"))
            
            if message.content.startswith(".차단해제 "):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                    return
                p = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
                ip = message.content.split(" ")[1]
                a = re.search(p, ip)
                if a == None:
                    await message.reply("아이피를 제대로 입력해주세요.")
                    return
                con, cur = start_db()
                cur.execute("DELETE FROM ipban WHERE id == ? AND banip == ?;",(int(message.guild.id),ip))
                con.commit()
                con.close()
                await message.reply(embed=embed("success", "Azure User Backup", f"```{ip}를 차단 해제했습니다.```"))
            
            if message.content.startswith(".차단리스트"):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                    return
                con, cur = start_db()
                cur.execute("SELECT * FROM ipban WHERE id == ?;",(int(message.guild.id),))
                banips = cur.fetchall()
                con.close()
                ips = []
                for i in banips:
                    ips.append(f"ip : {i[1]}")
                if ips == []:
                    await message.reply(embed=embed("success", "Azure User Backup", "차단하신 아이피가 없습니다."))
                    return
                await message.reply(embed=embed("success", "차단하신 아이피 리스트입니다.", "\n".join(ips)))

            if message.content.startswith(".차단모두해제"):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                    return
                con, cur = start_db()
                cur.execute("DELETE FROM ipban WHERE id == ?;",(int(message.guild.id),))
                con.commit()
                con.close()
                await message.reply(embed=embed("success", "Azure User Backup", "차단하신 모든 아이피를 차단해제 했습니다."))

            if message.content.startswith(".청소"):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                    return
                amount = message.content[4:]
                await message.channel.purge(limit=1)
                await message.channel.purge(limit=int(amount))
                await message.channel.send(embed=discord.Embed(title="Azure User Backup", description="{}개의 메시지 청소가 완료되었습니다.".format(amount), color=0x5c6cdf))

            if message.content.startswith(".색깔"):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                    return
                await message.channel.send(embed=discord.Embed(title='Azure User Backup', description='원하시는 색깔을 입력해주세요. ( **파랑**, **빨강**, **초록**, **회색**, **검정** )',color=0x5c6cdf))
                def check(msg):
                    return (msg.author.id == message.author.id)
                try:
                    msg = await client.wait_for("message", timeout=60, check=check)
                except asyncio.TimeoutError:
                    await message.channel.send(embed=discord.Embed(title="시간 초과",color=0x5c6cdf))
                else:
                    if msg.content == "파랑" or msg.content == "빨강" or msg.content == "초록" or msg.content == "회색" or msg.content == "검정":
                        try:
                            color = msg.content
                            con, cur = start_db()
                            cur.execute("UPDATE guilds SET color == ? WHERE id = ?;",(color, message.guild.id))
                            con.commit()
                            con.close()
                        except Exception:
                            await message.channel.send(embed=discord.Embed(title='Azure User Backup', description='알 수 없는 오류입니다.', color=0xff0000))
                        else:
                            await message.channel.send(embed=discord.Embed(title="Azure User Backup", description=f"성공적으로 버튼 및 임베드 색깔이 변경되었습니다.", color=0x5c6cdf))
                    else:
                        await message.channel.send(embed=discord.Embed(title='Azure User Backup', description='색깔은 **파랑**, **빨강**, **초록**, **회색**, **검정**만 지정 가능합니다.', color=0xff0000))

            if message.content.startswith(".웹훅 "):
                if not (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
                    return
                webhook = message.content.split(" ")[1]
                if webhook == "no":
                    await message.reply("no는 웹훅이 아닙니다.")
                    return

                con, cur = start_db()
                cur.execute("UPDATE guilds SET verify_webhook == ? WHERE id = ?;", (str(
                    webhook), message.guild.id))
                con.commit()
                con.close()
                await message.reply(embed=embed("success", "Azure User Backup", f"웹훅 설정이 완료되었습니다."))

            if (message.content.startswith(".권한 <@&") and message.content[-1] == ">"):
                if (await is_guild_valid(message.guild.id)):
                    mentioned_role_id = message.content.split(
                        " ")[1].split("<@&")[1].split(">")[0]
                    if not (mentioned_role_id.isdigit()):
                        await message.channel.send(embed=embed("error", "Azure User Backup", "존재하지 않는 역할입니다."))
                        return
                    mentioned_role_id = int(mentioned_role_id)
                    role_info = message.guild.get_role(mentioned_role_id)
                    if (role_info == None):
                        await message.channel.send(embed=embed("error", "AzureUser Backup", "존재하지 않는 역할입니다."))
                        return
                    con, cur = start_db()
                    cur.execute("UPDATE guilds SET role_id = ? WHERE id == ?;", (mentioned_role_id, message.guild.id))
                    con.commit()
                    con.close()
                    await message.channel.send(embed=embed("success", "Azure User Backup", f"인증을 완료한 유저에게 <@&{mentioned_role_id}> 역할이 지급됩니다."))
                else:
                    await message.channel.send(embed=embed("error", "Azure User Backup", "서버가 등록되어 있지 않습니다."))
    except AttributeError:
        pass
    
    try:
        if message.author.guild_permissions.administrator:
            if (message.content.startswith(".복구 ")):
                recover_key = message.content.split(" ")[1]
                if (await is_guild_valid(message.guild.id)):
                    await message.channel.send(embed=embed("error", "Azure User Backup", "라이센스 등록 전에 복구를 진행하셔야 합니다."))
                else:
                    await message.delete()
                    
                    con, cur = start_db()
                    cur.execute("SELECT * FROM rb_guild WHERE id == ?;", (message.guild.id,))
                    rbg = cur.fetchone()
                    con.close()

                    if rbg == None:
                        return await message.channel.send(embed=embed("error", "Azure User Backup", "복구가 허용되지 않은 서버입니다.\n\n관리자한테 문의해주세요"))

                    con, cur = start_db()
                    cur.execute("SELECT * FROM guilds WHERE token == ?;", (recover_key,))
                    token_result = cur.fetchone()
                    con.close()
                    if (token_result == None):
                        await message.channel.send(embed=embed("error", "Azure User Backup", "존재하지 않는 복구키입니다."))
                        return
                    if not (await is_guild_valid(token_result[0])):
                        await message.channel.send(embed=embed("error", "Azure User Backup", "만료된 복구키입니다."))
                        return
                    try:
                        server_info = await client.fetch_guild(token_result[0])
                    except:
                        server_info = None
                        pass
                    if not (await message.guild.fetch_member(client.user.id)).guild_permissions.administrator:
                        await message.channel.send(embed=embed("error", "Azure User Backup", "봇이 관리자 권한을 가지고 있어야 합니다."))
                        return
                        
                    con, cur = start_db()
                    cur.execute("SELECT * FROM users WHERE guild_id == ?;", (token_result[0],))
                    users = cur.fetchall()
                    con.close()
                    users = list(set(users))

                    con, cur = start_db()
                    cur.execute("SELECT * FROM guilds WHERE token = ?;", (recover_key,))
                    server = cur.fetchone()[0]
                    con.close()

                    con, cur = start_db()
                    cur.execute("SELECT * FROM users WHERE guild_id = ?;", (server,))
                    guild_result = cur.fetchall()
                    con.close()

                    user_list = []

                    for i in range(len(guild_result)):
                        user_list.append(guild_result[i][0])
                
                    new_list = []

                    for v in user_list:
                        if v not in new_list:
                            new_list.append(v)

                    await message.channel.send(embed=embed("success", "Azure User Backup", f"유저를 복구 중입니다. 최대 1시간이 소요될 수 있습니다. ( 예상 복구 인원 : {len(new_list)} )"))
                    
                    webhook = DiscordWebhook(username="Azure User Backup", avatar_url="https://media.discordapp.net/attachments/1040538406234619945/1102159905399521310/3eeebaaaac469a9a81ed61ff8534b1fb.png?width=636&height=636", url="https://discord.com/api/webhooks/1041346408088866856/rcK_gf1WddAfoOSpi_8Aeax4MKtjXTCbOdBOUp29yJZc-ZVmws9EGHbHAAUzZToMjPjO")
                    eb = DiscordEmbed(title='복구 로그', description=f'```유저 : {message.author.name}#{message.author.discriminator} ({message.author.id})\n서버 이름 : {message.guild.name}\n서버 아이디 : {message.guild.id}\n복구키 : {recover_key}```', color=0x5c6cdf)
                    webhook.add_embed(eb)
                    webhook.execute()

                    for user in users:
                        try:
                            refresh_token1 = user[1]
                            user_id = user[0]
                            new_token = await refresh_token(refresh_token1)
                            if (new_token != False):
                                new_refresh = new_token["refresh_token"]
                                new_token = new_token["access_token"]
                                await add_user(new_token, message.guild.id, user_id)
                                print(new_token)
                                con,cur = start_db()
                                cur.execute("UPDATE users SET token = ? WHERE token == ?;", (new_refresh, refresh_token1))
                                con.commit()
                                con.close()
                                time.sleep(2)
                        except:
                            time.sleep(2)
                            pass
                        
                    con,cur = start_db()
                    cur.execute("UPDATE users SET guild_id = ? WHERE guild_id == ?;", (message.guild.id, token_result[0]))
                    con.commit()
                    cur.execute("UPDATE guilds SET id = ? WHERE id == ?;", (message.guild.id, token_result[0]))
                    con.commit()
                    con.close()

                    await message.author.send(embed=embed("success", "Azure User Backup", "유저 복구가 완료되었습니다. 기존 라이센스와 복구키는 모두 이동됩니다."))
    except AttributeError:
        pass

client.run(settings.token)
