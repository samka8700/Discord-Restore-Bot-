import requests


def send(url, title, discription, content):
    data = {
        "username": "Azure Restoration 3",
        "content": content,
        "avatar_url": "https://media.discordapp.net/attachments/1040538406234619945/1091929134378266726/20221022_111525.png?width=559&height=559"

    }

    data["embeds"] = [
        {
            "description": discription,
            "title": title,
            "color": 0x1477e1
        }
    ]

    result = requests.post(url, json=data)

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print("Payload delivered successfully, code {}.".format(result.status_code))

def sendno(url, title, discription, content):
    data = {
        "username": "Azure Restoration 3",
        "content": content,
        "avatar_url": "https://media.discordapp.net/attachments/1040538406234619945/1091929134378266726/20221022_111525.png?width=559&height=559"

    }

    data["embeds"] = [
        {
            "description": discription,
            "title": title,
            "color": 0xff4040
        }
    ]

    result = requests.post(url, json=data)

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print("Payload delivered successfully, code {}.".format(result.status_code))
