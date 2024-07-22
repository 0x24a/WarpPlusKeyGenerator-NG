import httpx
import logging
import rich
import time
import random
import argparse
import traceback

logger = logging.getLogger("WarpGeneratorNG")

BASE_KEYS = [
    "a6p7K2e0-Z7ej890B-T12p8vb7",
    "56Rt0O2S-6XF74gq0-8F127pKj",
    "751xJA0Z-x4N6J7k1-i1C5I87e",
    "t6u13bA9-Dj926li0-7XUr05s8",
    "YUK9l850-ZO2K164I-92d35NIy",
    "Z9Jnd751-C078ocv6-8n341Kse",
    "39U0YG1q-d5KyB312-0Hnw596J",
    "58o1A9hB-9wb142nS-0896mkFi",
    "70I4JrU6-25Y4HAt1-53gIt84u",
    "7348MJEz-75d3Q9Js-71HFM6I4",
]  # My keys, do not abuse uwu

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


def cli(num: int):
    rich.print("[bold][yellow]WARP+ Key Generator[/yellow][/bold]")
    rich.print("By [blue]0x24a[/blue], Version [bold][green]v0.0.3[/green][/bold]\n")
    rich.print(f"Loaded [blue][yellow]{len(BASE_KEYS)}[/yellow][/blue] Base Keys")
    keys = []
    for i in range(1, num + 1):
        rich.print(f"\nGenerating... [yellow]({i}/{num})[/yellow]")
        sleep_time = 30
        while 1:
            try:
                key = generate_key(random.choice(BASE_KEYS))
                keys.append(key)
                break
            except KeyboardInterrupt:
                rich.print(f"[red]Cancelled[/red]")
                exit(1)
            except BaseException as e:
                sleep_time += 30
                tb = traceback.format_tb()
                tb = "\n".join(["[red]ERR![/red]\t[yellow]"+tb_line+"[/yellow]" for tb_line in tb.split('\n')])
                rich.print(tb)
                rich.print(f"[green]Retrying after {sleep_time}s...[/green]")
                time.sleep(sleep_time)
        rich.print(
            f"Account Type: \t[green][bold]{key.account_type}[/bold][/green]\nData Limit: \t[green][bold]{key.referral_count} GiB[/bold][/green]\nLicense Key: \t[green][bold]{key.license_code}[/bold][/green]"
        )
    rich.print(
        "\nKeys:\n"
        + "\n".join(
            [f"[bold][yellow]{key.license_code}[/yellow][/bold]" for key in keys]
        )
    )
    return keys


def file_output(num: int, filename: str):
    try:
        file = open(filename, "w+")
    except:
        rich.print("[red]Failed to open file[/red]")
        exit(1)
    keys: list[GenerateResults] = cli(num=num)
    keys = [key.license_code for key in keys]
    file.write("\n".join(keys))
    file.close()
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
    args: argparse.Namespace = parser.parse_args()
    if not args.output:
        cli(args.quantity)
        exit(0)
    else:
        file_output(args.quantity, args.output)
        exit(0)
