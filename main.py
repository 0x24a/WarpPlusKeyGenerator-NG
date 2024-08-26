import httpx
import logging
import rich
import time
import random
import argparse
import traceback
import os
import shutil
from datetime import datetime

logger = logging.getLogger("WarpGeneratorNG")

FALLBACK_BASE_KEYS = [
    "578Ko2xd-36K7DMX2-4V812ame",
    "94lB36du-4960HEzs-68E5jd3I",
    "28R1r9iF-6Li9Kq27-U514Yx8l",
    "k18ba35e-5whgj679-8Pi34nI2",
    "3MqFO712-DL4Q678q-5R6DN2z0",
    "2F05CD1P-7CJ0g2I5-B3hO4b56",
    "68y15EAJ-C3519JfR-zve6847x",
    "7I8n60ds-Chy26D57-5W21IFH8",
    "U4C071LW-JhT604K8-3a6s27uT",
    "aAsQ1072-fy983J0c-r432m6ZG",
]

WARP_CLIENT_HEADERS = {
    "CF-Client-Version": "a-6.11-2223",
    "Host": "api.cloudflareclient.com",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
    "User-Agent": "okhttp/3.12.1",
}  # From Cloudflare Warp APK

get_auth_headers = lambda token: {
    "Content-Type": "application/json; charset=UTF-8",
    "Authorization": f"Bearer {token}",
}

get_auth_headers_get = lambda token: {"Authorization": f"Bearer {token}"}


class User:
    def __init__(self, user_id: str, license_code: str, token: str) -> None:
        self.user_id = user_id
        self.license_code = license_code
        self.token = token


class GenerateResults:
    def __init__(
        self, account_type: str, referral_count: int, license_code: str
    ) -> None:
        self.account_type = account_type
        self.referral_count = referral_count
        self.license_code = license_code

    def __repr__(self) -> str:
        return f"WarpGenerateResults(account_type={self.account_type}, referral_count={self.referral_count}, license_code={self.license_code})"


def register_single():
    logger.debug("Start registering new account")
    logger.debug("Creating HTTP/2 Transport")
    client = httpx.Client(
        base_url="https://api.cloudflareclient.com/v0a2223",
        headers=WARP_CLIENT_HEADERS,
        timeout=30,
    )
    logger.debug("Registering")
    request = client.post("/reg").json()
    client.close()
    user_id = request["id"]
    license_code = request["account"]["license"]
    token = request["token"]
    logger.debug("Registered")
    return User(user_id=user_id, license_code=license_code, token=token)


def generate_key(base_key: str) -> GenerateResults:
    logger.debug("Start generating new key")
    logger.debug("Creating HTTP/2 Transport")
    client = httpx.Client(
        base_url="https://api.cloudflareclient.com/v0a2223",
        headers=WARP_CLIENT_HEADERS,
        timeout=30,
    )
    logger.debug("Registering User 1")
    user1 = register_single()
    logger.debug("Registering User 2")
    user2 = register_single()

    logger.debug("Referring U2 -> U1")
    client.patch(
        f"/reg/{user1.user_id}",
        headers=get_auth_headers(user1.token),
        json={"referrer": user2.user_id},
    )
    logger.debug("Removing U2")
    client.delete(f"/reg/{user2.user_id}", headers=get_auth_headers_get(user2.token))
    logger.debug("Referring BaseKey -> U1")
    client.put(
        f"/reg/{user1.user_id}/account",
        headers=get_auth_headers(user1.token),
        json={"license": base_key},
    )
    logger.debug("Referring U1")
    client.put(
        f"/reg/{user1.user_id}/account",
        headers=get_auth_headers(user1.token),
        json={"license": user1.license_code},
    )
    logger.debug("Getting account details")
    request = client.get(
        f"/reg/{user1.user_id}/account", headers=get_auth_headers_get(user1.token)
    )
    account_type = request.json()["account_type"]
    referral_count = request.json()["referral_count"]
    license_code = request.json()["license"]
    client.delete(f"/reg/{user1.user_id}", headers=get_auth_headers_get(user1.token))
    client.close()
    return GenerateResults(
        account_type=account_type,
        referral_count=referral_count,
        license_code=license_code,
    )


def cli(num: int, base_keys: list[str] = [], language: str = "en"):
    if language == "CN":
        rich.print("[bold][yellow]WARP+ 密钥生成器[/yellow][/bold]")
        rich.print("By [blue]0x24a[/blue], 版本 [bold][green]v0.0.4[/green][/bold]")
    else:
        rich.print("[bold][yellow]WARP+ Key Generator[/yellow][/bold]")
        rich.print("By [blue]0x24a[/blue], Version [bold][green]v0.0.4[/green][/bold]")
    
    if not base_keys:
        if language == "CN":
            rich.print("[green]从Github Repo加载basekeys...[/green]")
        else:
            rich.print("[green]Loading basekeys from the Github Repo...[/green]")
        try:
            request = httpx.get(
                "https://raw.githubusercontent.com/0x24a/WarpPlusKeyGenerator-NG/main/BASE_KEYS.txt",
                timeout=5,
            ).text
            keys = request.split("\n")
            for key in keys:
                assert len(key) == 26
                assert key.count("-") == 2
            base_keys = keys
        except:
            if language == "CN":
                rich.print("[yellow]从repo加载basekeys失败，使用备用basekeys...[/yellow]")
            else:
                rich.print("[yellow]Failed to load basekeys from the repo. Using the fallback basekeys...[/yellow]")
            base_keys = FALLBACK_BASE_KEYS
    else:
        for key in base_keys:
            if len(key) != 26 or key.count("-") != 2:
                if language == "CN":
                    rich.print(f"[red]无效的base_key: {key}[/red]")
                else:
                    rich.print(f"[red]Invaild base_key: {key}[/red]")
                exit(1)
    if language == "CN":
        rich.print(f"\n加载了 [blue][yellow]{len(base_keys)}[/yellow][/blue] 个Base Keys")
    else:
        rich.print(f"\nLoaded [blue][yellow]{len(base_keys)}[/yellow][/blue] Base Keys")
    result_keys: list[GenerateResults] = []
    for i in range(1, num + 1):
        if language == "CN":
            rich.print(f"\n生成中... [yellow]({i}/{num})[/yellow]")
        else:
            rich.print(f"\nGenerating... [yellow]({i}/{num})[/yellow]")
        sleep_time = 30
        while 1:
            try:
                single_key = generate_key(random.choice(base_keys))
                result_keys.append(single_key)
                break
            except KeyboardInterrupt:
                if language == "CN":
                    rich.print(f"[red]已取消[/red]")
                else:
                    rich.print(f"[red]Cancelled[/red]")
                exit(1)
            except BaseException as e:
                sleep_time += 30
                tb = traceback.format_exc()
                tb = "\n" + "\n".join(
                    [
                        "[red]ERR![/red]\t[yellow]" + tb_line + "[/yellow]"
                        for tb_line in tb.split("\n")
                    ]
                )
                rich.print(tb)
                if language == "CN":
                    rich.print(f"\n[green]将在 {sleep_time}s 后重试...[/green]")
                else:
                    rich.print(f"\n[green]Retrying after {sleep_time}s...[/green]")
                time.sleep(sleep_time)
        if language == "CN":
            rich.print(
                f"账户类型: \t[green][bold]{single_key.account_type}[/bold][/green]\n数据限制: \t[green][bold]{single_key.referral_count} GiB[/bold][/green]\n许可证密钥: \t[green][bold]{single_key.license_code}[/bold][/green]"
            )
            if single_key.referral_count <= 1:
                rich.print(f"[red]警告[/red]\t[yellow]检测到生成问题，请在 https://github.com/0x24a/WarpPlusKeyGenerator-NG/issues 打开一个issue[/yellow]")
        else:
            rich.print(
                f"Account Type: \t[green][bold]{single_key.account_type}[/bold][/green]\nData Limit: \t[green][bold]{single_key.referral_count} GiB[/bold][/green]\nLicense Key: \t[green][bold]{single_key.license_code}[/bold][/green]"
            )
            if single_key.referral_count <= 1:
                rich.print(f"[red]WARN[/red]\t[yellow]Generation problems detected, please open an issue at https://github.com/0x24a/WarpPlusKeyGenerator-NG/issues[/yellow]")
    if language == "CN":
        rich.print(
            "\n密钥:\n"
            + "\n".join(
                [f"[bold][yellow]{key.license_code}[/yellow][/bold]" for key in result_keys]
            )
        )
    else:
        rich.print(
            "\nKeys:\n"
            + "\n".join(
                [f"[bold][yellow]{key.license_code}[/yellow][/bold]" for key in result_keys]
            )
        )
    return result_keys


def file_output(num: int, filename: str, append: bool, base_keys: list[str] = [], language: str = "en"):
    if os.path.exists(filename) and not append:
        shutil.move(filename, f"{filename}.{datetime.now()}bkp")
    try:
        file = open(filename, "w+" if not append else "a")
    except:
        if language == "CN":
            rich.print("[red]打开文件失败[/red]")
        else:
            rich.print("[red]Failed to open file[/red]")
        exit(1)
    keys: list[GenerateResults] = cli(num=num, base_keys=base_keys, language=language)
    key_codes = [key.license_code for key in keys]
    file.write("\n".join(key_codes) + "\n")
    file.close()
    if language == "CN":
        rich.print(
            f"[bold][yellow]已将 {len(keys)} 个密钥写入 {filename} ![/yellow][/bold]"
        )
    else:
        rich.print(
            f"[bold][yellow]Wrote {len(keys)} key(s) to {filename} ![/yellow][/bold]"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="WarpPlusKeyGenerator-NG",
        description="Generates Warp+ Keys",
        epilog="Made with ❤️ by 0x24a",
    )
    parser.add_argument(
        "-q", "--quantity", default=1, type=int, help="Key quantity", required=False
    )
    parser.add_argument(
        "-o", "--output", help="Output the keys to a file.", default=None
    )
    parser.add_argument(
        "-a", "--append", action='store_true', default=False, help="Wether to append to file(if not flagged then overwrite)."
    )
    parser.add_argument(
        "-b", "--basekeys", help="Specify comma-separated basekeys.", default=None
    )
    parser.add_argument(
        "-l", "--language", help="Specify language (CN for Chinese, EN for English, default is English).", default="en", choices=["CN", "EN"]
    )
    args: argparse.Namespace = parser.parse_args()
    if not args.output:
        cli(args.quantity, args.basekeys.split(",") if args.basekeys else [], args.language)
        exit(0)
    else:
        file_output(args.quantity, args.output, args.append, args.basekeys.split(",") if args.basekeys else [], args.language)
        exit(0)
