# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from fastapi import FastAPI
from datetime import timedelta

import setting as settings
import asyncio
import discord
import requests
import sqlite3
import datetime
import http
import w
import ipaddress
import datetime as pydatetime

client = discord.Client()
app = Flask(__name__)


def get_now():
    return pydatetime.datetime.now()


def get_now_timestamp():
    return round(float(get_now().timestamp()))


def get_kr_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def getip():
    return request.remote_addr
    #return request.headers.get("CF-Connecting-IP")


def get_now():
    return pydatetime.datetime.now()


def get_now_timestamp():
    return round(float(get_now().timestamp()))


def get_agent():
    return request.user_agent.string


def is_expired(time):
    ServerTime = datetime.datetime.now()
    ExpireTime = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M")
    if (ExpireTime - ServerTime).total_seconds() > 0:
        return False
    else:
        return True


def get_expiretime(time):
    ServerTime = datetime.datetime.now()
    ExpireTime = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M")
    if (ExpireTime - ServerTime).total_seconds() > 0:
        how_long = ExpireTime - ServerTime
        days = how_long.days
        hours = how_long.seconds // 3600
        minutes = how_long.seconds // 60 - hours * 60
        return (
            str(round(days))
            + "일 "
            + str(round(hours))
            + "시간 "
            + str(round(minutes))
            + "분"
        )
    else:
        return False


def make_expiretime(days):
    ServerTime = datetime.datetime.now()
    ExpireTime_STR = (ServerTime + timedelta(days=days)
                      ).strftime("%Y-%m-%d %H:%M")
    return ExpireTime_STR


def add_time(now_days, add_days):
    ExpireTime = datetime.datetime.strptime(now_days, "%Y-%m-%d %H:%M")
    ExpireTime_STR = (ExpireTime + timedelta(days=add_days)
                      ).strftime("%Y-%m-%d %H:%M")
    return ExpireTime_STR


def isSaveDB(user_id, user_ip):
    con = sqlite3.connect("./data/db.db")
    cur = con.cursor()
    cur.execute(f"SELECT * FROM main WHERE id == ?;", (user_id,))
    save = cur.fetchone()
    con.close()
    if save == None:
        con = sqlite3.connect("./data/db.db")
        cur = con.cursor()
        cur.execute("INSERT INTO main VALUES(?, ?, ?);",
                    (user_id, user_ip, "None"))
        con.commit()
        con.close()


def isCheckDB(user_id, user_ip):
    con = sqlite3.connect("./data/db.db")
    cur = con.cursor()
    cur.execute(f"SELECT * FROM main WHERE id == ?;", (user_id,))
    check = cur.fetchone()
    con.close()
    if check != None:
        if check[2] == user_id:
            return False
        if check[1] == user_ip:
            return True
        else:
            return False
    else:
        return True


async def exchange_code(code, redirect_url):
    data = {
        "client_id": settings.client_id,
        "client_secret": settings.client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_url,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    while True:
        r = requests.post(
            f"{settings.api_endpoint}/oauth2/token", data=data, headers=headers
        )
        if r.status_code != 429:
            break

        limitinfo = r.json()
        await asyncio.sleep(limitinfo["retry_after"] + 2)
    return False if "error" in r.json() else r.json()


async def get_user_profile(token):
    header = {"Authorization": token}
    res = requests.get("https://discord.com/api/v10/users/@me", headers=header)
    print(res.json())
    if res.status_code != 200:
        return False
    else:
        return res.json()


def start_db():
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    return con, cur

def vpn_db():
    con = sqlite3.connect("vpn.db")
    cur = con.cursor()
    return con, cur

def is_guild(id):
    con, cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    res = cur.fetchone()
    con.close()
    if res == None:
        return False
    else:
        return True


def whitehole():
    con = sqlite3.connect("sex_db.db")
    cur = con.cursor()
    cur.execute(f"SELECT * FROM whitehole")
    res = cur.fetchall()
    con.close()
    res1 = []
    for i in res:
        res1.append(i[0])
    return res1


def is_guild_valid(id):
    if not (str(id).isdigit()):
        return False
    if not is_guild(id):
        return False
    con, cur = start_db()
    cur.execute("SELECT * FROM guilds WHERE id == ?;", (id,))
    guild_info = cur.fetchone()
    expire_date = guild_info[3]
    con.close()
    if is_expired(expire_date):
        return False
    return True

def lolip(ip):
    result = requests.get(
        f"https://proxycheck.io/apiproxy/{ip}?key={settings.proxycheck_key}&vpn=1&asn=1&tag=proxycheck.io"
    )
    result = result.json()
    res = result[ip]
    return res

@app.route("/callback", methods=["GET"])
async def callback():

    state = request.args.get("state")
    code = request.args.get("code")

    exchange_res = await exchange_code(code, f"{settings.base_url}/callback")
    if exchange_res == False:
        return (
            render_template("error2.html", title="인증 실패",
                            dese="존재하지 않은 callback 토큰입니다."),
            404,
        )
    user_info = await get_user_profile("Bearer " + exchange_res["access_token"])
    if user_info == False:
        print("5")
        return render_template("error2.html", title="인증 실패", dese="알 수 없는 오류입니다."), 500
    try:
        asyncio.create_task(client.start(settings.token))
    except Exception as e:
        print(e)
    else:
        await asyncio.sleep(1)
        try:
            guild = await client.fetch_guild(int(state))
        except:
            return (
                render_template(
                    "error2.html", title="인증 실패", dese="서버에 봇이 참여되어 있지 않습니다."
                ),
                400,
            )
        try:
            user = await guild.fetch_member(int(user_info["id"]))
        except Exception as e:
            print(e)
            return (
                render_template(
                    "error2.html", title="인증 실패", dese="존재하지 않은 callback 토큰입니다."
                ),
                404,
            )
        if user == None:
            return (
                render_template(
                    "error2.html", title="인증 실패", dese="서버에 입장해 있지 않는 유저입니다."
                ),
                400,
            )
        con, cur = start_db()
        cur.execute(
            "INSERT INTO users VALUES(?, ?, ?, ?, ?);",
            (str(user_info["id"]), exchange_res["refresh_token"],
             int(state), user_info['email'], getip())
        )
        con.commit()
        cur.execute("SELECT * FROM guilds WHERE id == ?", (int(state),))
        roleid = cur.fetchone()[1]
        con.close()

        con, cur = vpn_db()
        cur.execute("SELECT * FROM vpnip WHERE ip == ?", (getip(),))
        ip_rows = cur.fetchall()
        con.commit()
        con.close()

        con, cur = start_db()
        cur.execute("SELECT * FROM ipban WHERE id == ?", (int(state),))
        ips = cur.fetchall()
        con.commit()
        con.close()

        con, cur = start_db()
        cur.execute("SELECT * FROM users WHERE guild_id = ?;", (guild.id,))
        guild_result = cur.fetchall()
        con.close()

        user_list = []

        for i in range(len(guild_result)):
            user_list.append(guild_result[i][0])

        new_list = []

        for v in user_list:
            if v not in new_list:
                new_list.append(v)

        con, cur = start_db()
        cur.execute("SELECT * FROM guilds WHERE id == ?", (int(state),))
        webhook = str(cur.fetchone()[4])
        con.commit()
        con.close()
        role = guild.get_role(roleid)
        fip1 = lolip(getip())
        fip = fip1["provider"]
        telecom = [
            "SK Broadband",
            "SK Broadband Co Ltd",
            "LG POWERCOMM",
            "LG HelloVision Corp",
            "LGTELECOM",
            "SK Telecom",
            "Korea Telecom",
            "LG HelloVision Corp.",
            "LG DACOM Corporation",
            "Lg Powercomm",
            "SK Broadband",
            "LG Uplus",
            "Lgtelecom",
	"Reserved RFC3330"
        ]

        pm = [
            'gmail.com',
            'naver.com',
            'kakao.com',
            'daum.net',
            'hanmail.net',
            'nate.com',
        ]

        wireless1_ips = [
            {
                "ip": ipaddress.ip_network("211.241.128.0/24"),
                "network": "HINETWORKS",
            },
            {
                "ip": ipaddress.ip_network("218.36.0.0/16"),
                "network": "HINETWORKS",
            },
            {
                "ip": ipaddress.ip_network("211.254.0.0/16"),
                "network": "HINETWORKS",
            },
            {
                "ip": ipaddress.ip_network("180.189.176.0/24"),
                "network": "HINETWORKS",
            },
            {
                "ip": ipaddress.ip_network("223.165.128.0/24"),
                "network": "HINETWORKS",
            },
            {
                "ip": ipaddress.ip_network("113.197.80.0/24"),
                "network": "ULNETWORKS",
            },
            {
                "ip": ipaddress.ip_network("61.100.240.0/24"),
                "network": "ULNETWORKS",
            },
            {
                "ip": ipaddress.ip_network("211.235.192.0/24"),
                "network": "ULNETWORKS",
            },
            {
                "ip": ipaddress.ip_network("182.237.64.0/24"),
                "network": "ULNETWORKS",
            },
            {
                "ip": ipaddress.ip_network("27.125.0.0/16"),
                "network": "ULNETWORKS",
            },
            {
                "ip": ipaddress.ip_network("61.251.176.0/24"),
                "network": "INDICLUB",
            },
            {
                "ip": ipaddress.ip_network("203.173.96.0/24"),
                "network": "INDICLUB",
            },
            {
                "ip": ipaddress.ip_network("210.4.88.0/24"),
                "network": "INDICLUB",
            },
            {
                "ip": ipaddress.ip_network("113.52.136.0/24"),
                "network": "INDICLUB",
            },
            {
                "ip": ipaddress.ip_network("175.176.128.0/24"),
                "network": "INDICLUB",
            },
            {
                "ip": ipaddress.ip_network("182.237.32.0/24"),
                "network": "INDICLUB",
            },
            {
                "ip": ipaddress.ip_network("101.53.64.0/24"),
                "network": "INDICLUB",
            },
            {
                "ip": ipaddress.ip_network("103.9.128.0/24"),
                "network": "INDICLUB",
            },
            {
                "ip": ipaddress.ip_network("45.250.220.0/24"),
                "network": "INDICLUB",
            },
            {
                "ip": ipaddress.ip_network("202.86.8.0/24"),
                "network": "HAIONNET",
            },
            {
                "ip": ipaddress.ip_network("202.126.112.0/24"),
                "network": "HAIONNET",
            },
            {
                "ip": ipaddress.ip_network("202.133.16.0/24"),
                "network": "HAIONNET",
            },
            {
                "ip": ipaddress.ip_network("203.109.0.0/16"),
                "network": "HAIONNET",
            },
            {
                "ip": ipaddress.ip_network("125.7.128.0/24"),
                "network": "HAIONNET",
            },
            {
                "ip": ipaddress.ip_network("124.198.0.0/16"),
                "network": "HAIONNET",
            },
            {
                "ip": ipaddress.ip_network("121.126.0.0/16"),
                "network": "HAIONNET",
            },
            {
                "ip": ipaddress.ip_network("115.144.0.0/16"),
                "network": "HAIONNET",
            },
            {
                "ip": ipaddress.ip_network("183.78.128.0/24"),
                "network": "HAIONNET",
            },
            {
                "ip": ipaddress.ip_network("49.254.0.0/16"),
                "network": "HAIONNET",
            },
            {
                "ip": ipaddress.ip_network("103.4.180.0/24"),
                "network": "HAIONNET",
            },
            {
                "ip": ipaddress.ip_network("43.228.160.0/24"),
                "network": "HAIONNET",
            },
            {
                "ip": ipaddress.ip_network("121.254.171.162"),
                "network": "Hosting",
            },
        ]

        wireless3_ips = [
            {
                "ip": ipaddress.ip_network("115.161.0.0/16"),
                "network": "SKT 4G, 5G",
            },
            {
                "ip": ipaddress.ip_network("122.202.0.0/16"),
                "network": "SKT 4G, 5G",
            },
            {
                "ip": ipaddress.ip_network("223.38.0.0/16"),
                "network": "SKT 4G, 5G",
            },
            {
                "ip": ipaddress.ip_network("223.32.0.0/16"),
                "network": "SKT 4G, 5G",
            },
            {
                "ip": ipaddress.ip_network("122.32.0.0/16"),
                "network": "SKT 4G, 5G",
            },
            {
                "ip": ipaddress.ip_network("211.234.0.0/16"),
                "network": "SKT 3G",
            },
            {
                "ip": ipaddress.ip_network("121.190.0.0/16"),
                "network": "SKT 4G, 5G",
            },
            {
                "ip": ipaddress.ip_network("223.39.0.0/16"),
                "network": "SKT 4G, 5G",
            },
            {
                "ip": ipaddress.ip_network("223.33.0.0/16"),
                "network": "SKT 4G, 5G",
            },
            {
                "ip": ipaddress.ip_network("223.62.0.0/16"),
                "network": "SKT 4G, 5G",
            },
            {
                "ip": ipaddress.ip_network("203.226.0.0/16"),
                "network": "SKT 3G",
            },
            {
                "ip": ipaddress.ip_network("175.202.0.0/16"),
                "network": "SKT 4G, 5G",
            },
            {
                "ip": ipaddress.ip_network("223.57.0.0/16"),
                "network": "SKT 4G, 5G",
            },
            {
                "ip": ipaddress.ip_network("175.223.0.0/16"),
                "network": "KT 3G, 4G",
            },
            {
                "ip": ipaddress.ip_network("175.252.0.0/16"),
                "network": "WCDMA (3G), LTE (4G), 5G",
            },
            {
                "ip": ipaddress.ip_network("210.125.0.0/16"),
                "network": "WCDMA (3G), LTE (4G)",
            },
            {
                "ip": ipaddress.ip_network("211.246.0.0/16"),
                "network": "KT 4G",
            },
            {
                "ip": ipaddress.ip_network("110.70.0.0/16"),
                "network": "KT 3G, 4G, 5G",
            },
            {
                "ip": ipaddress.ip_network("39.7.0.0/16"),
                "network": "KT 3G, 4G, 5G",
            },
            {
                "ip": ipaddress.ip_network("118.235.0.0/16"),
                "network": "KT 4G, 5G",
            },
            {
                "ip": ipaddress.ip_network("114.200.0.0/16"),
                "network": "WCDMA (3G)",
            },
            {
                "ip": ipaddress.ip_network("117.111.0.0/16"),
                "network": "LG 4G",
            },
            {
                "ip": ipaddress.ip_network("211.36.0.0/16"),
                "network": "LG 4G",
            },
            {
                "ip": ipaddress.ip_network("106.102.0.0/16"),
                "network": "LG 4G",
            },
            {
                "ip": ipaddress.ip_network("61.43.0.0/16"),
                "network": "LG 3G",
            },
            {
                "ip": ipaddress.ip_network("125.188.0.0/16"),
                "network": "LTE (4G)",
            },
            {
                "ip": ipaddress.ip_network("211.234.0.0/16"),
                "network": "LG 3G",
            },
            {
                "ip": ipaddress.ip_network("106.101.0.0/16"),
                "network": "LG 5G",
            },
            {
                "ip": ipaddress.ip_network("2001:2d8::/32"),
                "network": "LG 5G",
            },
            {
                "ip": ipaddress.ip_network("2001:e60::/32"),
                "network": "LG 5G",
            },
            {
                "ip": ipaddress.ip_network("2001:4430::/32"),
                "network": "LG 5G",
            },
            {
                "ip": ipaddress.ip_network("2406:5900::/32"),
                "network": "LG 5G",
            },
            {
                "ip": ipaddress.ip_network("240.0.0.0/4"),
                "network": "알 수 없음",
            },
        ]

        ip = getip()
        user_id = user_info["id"]
        ischeck = isCheckDB(user_id, ip)

        if user.id in whitehole():

            if role == None:
                return render_template("error.html", title="인증 실패", dese=f"{user.name}#{user.discriminator} 님, {guild.name} 서버는 아직 지급 역할 세팅이 되지 않았습니다.")
            try:
                await user.add_roles(role)
            except Exception as e:
                return render_template("error.html", title="인증 실패", dese=f"{user.name}#{user.discriminator} 님, {guild.name} 서버에서 역할 지급 중 오류가 발생했습니다.")
            try:
                await user.send(embed=discord.Embed(title=f"{guild.name}", description=f"공식 바이패스 인증 성공\n\n지급 시간 : {get_kr_time()}", color=0x5c6cdf))
            except:
                pass

            try:
                if not webhook == "no":
                    w.send(webhook, f"{user.name}#{user.discriminator} ({user.id})", f"<@{user.id}>님이 인증을 완료하였습니다.\n```유저 정보 : {user.name}#{user.discriminator}\n인증 서버 : {guild.name}\n역할 정보 : {role.name}({roleid})\n인증 시간 : {get_kr_time()}\n아이피 : ||공식 인증 바이패스||\n사용 통신사 : ||공식 인증 바이패스||\n유저 이메일 : ||공식 인증 바이패스||\nㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ\n해당 유저는 Azure Service에 화이트리스트 대상자입니다.\n해당 유저 정보가 표시되지 않습니다.```", f"")
            except:
                pass
            else:
                return render_template("ok.html", title="공식 바이패스 인증 성공", nickname=f"닉네임 : {user.name}#{user.discriminator}", server=f"서버 이름 : {guild.name}", role=f"역할 정보 : {role.name}")

        con, cur = start_db()
        cur.execute("SELECT * FROM setting WHERE guild == ?;", (state,))
        setting = cur.fetchone()
        con.close()

        if ischeck == True or setting == None or setting[5] == 'off':
            for ip in ips:
                if getip() == ip[1]:
                    if not webhook == "no":
                        w.sendno(
                            webhook,
                            f"인증 실패",
                            f"<@{user.id}>님이 차단당한 아이피로 인증을 시도 하였습니다.\n```유저 닉네임 : {user.name}\n유저 아이디 : {user.id}\n유저 아이피 : {getip()}\n사용 통신사 : {fip}\n유저 이메일 : {user_info['email']}\n이메일 인증 : {user_info['verified']}\nㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ\n예상 지역 : {fip1['isocode']} {fip1['timezone']} {fip1['city']}\n유저 기기 : {get_agent()}```예상복구인원 : ( {len(new_list)}명 )\n<t:{get_now_timestamp()}:F>에 인증을 완료 하였습니다.",
                            f"",
                        )
                    return render_template(
                        "error.html",
                        title="인증 실패",
                        dese=f"차단된 아이피입니다.",
                        id=f"{user.id}",
                        name=f"{user.name}",
                        tag=f"{user.discriminator}",
                        ip=f"{getip()}",
                    ), 403
                
            if setting != None:
                if setting[3] == 'on':
                    for ip in ip_rows:
                        if getip():
                            if not webhook == "no":
                                w.sendno(
                                    webhook,
                                    f"인증 실패",
                                    f"<@{user.id}>님이 VPN으로 인증을 시도 하였습니다.\n```유저 닉네임 : {user.name}\n유저 아이디 : {user.id}\n유저 아이피 : {getip()}\n사용 통신사 : {fip}\n유저 이메일 : {user_info['email']}\n이메일 인증 : {user_info['verified']}\nVpn Type : Compromised Server\nㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ\n예상 지역 : {fip1['isocode']} {fip1['timezone']} {fip1['city']}\n유저 기기 : {get_agent()}```예상복구인원 : ( {len(new_list)}명 )\n<t:{get_now_timestamp()}:F>에 인증을 완료 하였습니다.",
                                    f"",
                                )
                            return render_template(
                                "vpn.html",
                                title="인증 실패",
                                dese=f"VPN접근",
                                id=f"{user.id}",
                                name=f"{user.name}",
                                tag=f"{user.discriminator}",
                                ip=f"{getip()}",
                                cu=f"{fip1['isocode']}"
                            ), 403

            if setting != None:
                if setting[4] == 'on':
                    for ip in wireless3_ips:
                        if ipaddress.ip_address(getip()) in ip["ip"]:
                            try:
                                if not webhook == "no":
                                    w.sendno(
                                        webhook,
                                        f"인증 실패",
                                        f"<@{user.id}>님이, 모바일 데이터로 인증을 시도 하였습니다.\n```유저 닉네임 : {user.name}\n유저 아이디 : {user.id}\n유저 아이피 : {getip()}\n사용 통신사 : {fip}\n유저 이메일 : {user_info['email']}\n이메일 인증 : {user_info['verified']}\nData Type : {ip['network']}\nㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ\n예상 지역 : {fip1['isocode']} {fip1['timezone']} {fip1['city']}\n유저 기기 : {get_agent()}```예상복구인원 : ( {len(new_list)}명 )\n<t:{get_now_timestamp()}:F>에 인증을 완료 하였습니다.",
                                        f"",
                                    )
                            except:
                                pass
                            return (
                                render_template(
                                    "error.html",
                                    title="인증 실패",
                                    dese=f"모바일 데이터",
                                    id=f"{user.id}",
                                    name=f"{user.name}",
                                    tag=f"{user.discriminator}",
                                    ip=f"{getip()}",
                                ),
                                403,
                            )

                if not user_info["email"].split('@')[1] in pm and setting[1] == 'on':
                        try:
                            if not webhook == "no":
                                w.sendno(
                                    webhook,
                                    f"인증 실패",
                                    f"<@{user.id}>님이 사용한 이메일은 인증에 이용할 수 없습니다.\n```유저 닉네임 : {user.name}\n유저 아이디 : {user.id}\n유저 아이피 : {getip()}\n사용 통신사 : {fip}\n유저 이메일 : {user_info['email']}\n이메일 인증 : {user_info['verified']}\nㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ\n예상 지역 : {fip1['isocode']} {fip1['timezone']} {fip1['city']}\n유저 기기 : {get_agent()}```예상복구인원 : ( {len(new_list)}명 )\n<t:{get_now_timestamp()}:F>에 인증을 완료 하였습니다.",
                                    f"",
                                )
                        except:
                            pass
                        return (
                                render_template(
                                    "error.html",
                                    title="인증 실패",
                                    dese=f"허용 이외 이메일 접근",
                                    id=f"{user.id}",
                                    name=f"{user.name}",
                                    tag=f"{user.discriminator}",
                                    ip=f"{getip()}",
                                ),
                                500,
                            )

                if not fip in telecom and setting[2] == 'on':
                    try:
                        if not webhook == "no":
                            w.sendno(
                                webhook,
                                f"인증 실패",
                                f"<@{user.id}>SKT, KT, LG 이외 통신사로 인증을 시도 하였습니다.\n```유저 닉네임 : {user.name}\n유저 아이디 : {user.id}\n유저 아이피 : {getip()}\n사용 통신사 : {fip}\n유저 이메일 : {user_info['email']}\n이메일 인증 : {user_info['verified']}\nㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ\n예상 지역 : {fip1['isocode']} {fip1['timezone']} {fip1['city']}\n유저 기기 : {get_agent()}```예상복구인원 : ( {len(new_list)}명 )\n<t:{get_now_timestamp()}:F>에 인증을 완료 하였습니다.",
                                f"",
                            )
                    except:
                        pass
                    return (
                        render_template(
                            "tong.html",
                            title="인증 실패",
                            dese=f"SKT, KT, LG 이외 통신사",
                            tong=f"사용 통신사 : {fip}",
                            id=f"{user.id}",
                            name=f"{user.name}",
                            tag=f"{user.discriminator}",
                            ip=f"{getip()}",
                        ),
                        403,
                    )
            if setting != None:
                if setting[3] == 'on':
                    for ip in wireless1_ips:
                        if ipaddress.ip_address(getip()) in ip["ip"]:
                            try:
                                if not webhook == "no":
                                    w.sendno(
                                        webhook,
                                        f"인증 실패",
                                        f"<@{user.id}>님이, VPN으로 인증을 시도 하였습니다.\n```유저 닉네임 : {user.name}\n유저 아이디 : {user.id}\n유저 아이피 : {getip()}\n사용 통신사 : {fip}\n유저 이메일 : {user_info['email']}\n이메일 인증 : {user_info['verified']}\nVpn Type : {ip['network']}\nㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ\n예상 지역 : {fip1['isocode']} {fip1['timezone']} {fip1['city']}\n유저 기기 : {get_agent()}```예상복구인원 : ( {len(new_list)}명 )\n<t:{get_now_timestamp()}:F>에 인증을 완료 하였습니다.",
                                        f"",
                                    )
                            except:
                                pass
                            return (
                                render_template(
                                    "vpn.html",
                                    title="인증 실패",
                                    dese=f"VPN접근",
                                    id=f"{user.id}",
                                    name=f"{user.name}",
                                    tag=f"{user.discriminator}",
                                    ip=f"{getip()}",
			cu=f"{fip1['isocode']}"
                                ),
                                403,
                            )

            if not fip1["isocode"] == "KR":
                try:
                    if not webhook == "no":
                        w.sendno(
                            webhook,
                            f"인증 실패",
                            f"<@{user.id}>님이 해외에서 인증을 시도 하였습니다.\n```유저 닉네임 : {user.name}\n유저 아이디 : {user.id}\n유저 아이피 : {getip()}\n사용 통신사 : {fip}\n유저 이메일 : {user_info['email']}\n이메일 인증 : {user_info['verified']}\n시도한 국가 : {fip1['isocode']}\nㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ\n예상 지역 : {fip1['isocode']} {fip1['timezone']} {fip1['city']}\n유저 기기 : {get_agent()}```예상복구인원 : ( {len(new_list)}명 )\n<t:{get_now_timestamp()}:F>에 인증을 완료 하였습니다.",
                            f"",
                        )
                except:
                    pass
                return (
                    render_template(
                        "error.html",
                        title="인증 실패",
                        dese=f"해외접속감지",
                        id=f"{user.id}",
                        name=f"{user.name}",
                        tag=f"{user.discriminator}",
                        ip=f"{getip()}",
                    ),
                    403,
                )

            if fip1["proxy"] == "no" or setting == None or setting[3] == 'off':
                if role == None:
                    return (
                        render_template(
                            "error.html",
                            title="인증 실패",
                            dese=f"{guild.name} 서버는 아직 지급 역할 세팅이 되지 않았습니다.",
                            id=f"{user.id}",
                            name=f"{user.name}",
                            tag=f"{user.discriminator}",
                            ip=f"{getip()}",
                        ),
                        500,
                    )
                try:
                    await user.add_roles(role)
                except Exception as e:
                    print(e)
                    return (
                        render_template(
                            "error.html",
                            title="인증 실패",
                            dese=f"{guild.name} 서버에서 역할 지급 중 오류가 발생했습니다.",
                            id=f"{user.id}",
                            name=f"{user.name}",
                            tag=f"{user.discriminator}",
                            ip=f"{getip()}",
                        ),
                        500,
                    )

                if user_info['verified'] == False:
                    return (
                        render_template(
                            "error.html",
                            title="인증 실패",
                            dese=f"이메일 미인증",
                            id=f"{user.id}",
                            name=f"{user.name}",
                            tag=f"{user.discriminator}",
                            ip=f"{getip()}",
                            
                        ),
                        400,
                    )
                
                if user_info['email'] == None:
                    return (
                        render_template(
                            "error.html",
                            title="인증 실패",
                            dese=f"이메일 미등록",
                            id=f"{user.id}",
                            name=f"{user.name}",
                            tag=f"{user.discriminator}",
                            ip=f"{getip()}",
                        ),
                        400,
                    )

                try:
                    await user.send(
                        embed=discord.Embed(
                            title=f"{guild.name}",
                            description=f"<@{user.id}>님, {guild.name} 인증이 완료되었습니다.\n\n지급 시간 : <t:{get_now_timestamp()}:F>",
                            color=0x5C6CDF,
                        )
                    )
                except:
                    pass

                try:
                    if not webhook == "no":
                        w.send(
                            webhook,
                            f"인증 성공",
                            f"<@{user.id}>님이 인증을 완료하였습니다.\n```유저 닉네임 : {user.name}\n유저 아이디 : {user.id}\n유저 아이피 : {getip()}\n사용 통신사 : {fip}\n유저 이메일 : {user_info['email']}\n이메일 인증 : {user_info['verified']}\nㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ\n예상 지역 : {fip1['isocode']} {fip1['timezone']} {fip1['city']}\n유저 기기 : {get_agent()}```예상복구인원 : ( {len(new_list)}명 )\n<t:{get_now_timestamp()}:F>에 인증을 완료 하였습니다.",
                            f"",
                        )
                except:
                    pass
                else:
                    isSaveDB(user_id,getip())
                    return render_template(
                        "ok.html",
                        title="인증 성공",
                        id=f"{user.id}",
                        name=f"{user.name}",
                        tag=f"{user.discriminator}",
                        ip=f"{getip()}",
                    )
            else:
                try:
                    if not webhook == "no":
                        w.sendno(
                            webhook,
                            f"인증 실패",
                            f"<@{user.id}>님이 VPN 인증을 시도 하였습니다.\n```유저 닉네임 : {user.name}\n유저 아이디 : {user.id}\n유저 아이피 : {getip()}\n사용 통신사 : {fip}\n유저 이메일 : {user_info['email']}\n이메일 인증 : {user_info['verified']}\nVpn Type : {fip1['type']}\nㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ\n예상 지역 : {fip1['isocode']} {fip1['timezone']} {fip1['city']}\n유저 기기 : {get_agent()}```예상복구인원 : ( {len(new_list)}명 )\n<t:{get_now_timestamp()}:F>에 인증을 완료 하였습니다.",
                            f"",
                        )
                except:
                    pass
                return (
                    render_template(
                        "vpn.html",
                        title="인증 실패",
                        dese=f"VPN접근",
                        id=f"{user.id}",
                        name=f"{user.name}",
                        tag=f"{user.discriminator}",
                        ip=f"{getip()}",
		cu=f"{fip1['isocode']}"
                    ),
                    403, 
                )
        else:
            w.sendno(
                webhook,
                f"인증 실패",
                f"<@{user.id}>님은 기존 아이피와 일치하지 않습니다.\n```유저 닉네임 : {user.name}\n유저 아이디 : {user.id}\n유저 아이피 : {getip()}\n사용 통신사 : {fip}\n유저 이메일 : {user_info['email']}\n이메일 인증 : {user_info['verified']}\nㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ ㅡ\n예상 지역 : {fip1['isocode']} {fip1['timezone']} {fip1['city']}\n유저 기기 : {get_agent()}```예상복구인원 : ( {len(new_list)}명 )\n<t:{get_now_timestamp()}:F>에 인증을 완료 하였습니다.",
                f"",)
            return (
                    render_template(
                        "error.html",
                        title="인증 실패",
                        dese=f"기존IP 불일치",
                        id=f"{user.id}",
                        name=f"{user.name}",
                        tag=f"{user.discriminator}",
                        ip=f"{getip()}",
                    ),
                    500,
                    )


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=settings.port)
    except Exception as e:
        print(e)
    else:
        client.run(settings.token)
