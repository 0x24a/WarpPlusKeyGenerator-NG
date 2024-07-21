import httpx
import logging
import rich
import time
import random
import sys

logger = logging.getLogger("WarpGeneratorNG")

BASE_KEYS = [
    "Ep3021DM-Wp9V6M37-51U3EaN7",
    "XW84D29C-35b6OQ1i-3L24lzD9",
    "n9F47fk8-K0RJC548-WF6k89Y3",
    "35N8Hj4R-3A2a4Nn8-7z98xI2Y",
    "V409lBw1-30a4ktY9-17ZR85gb",
    "4D0Ux39r-0NZ25lt6-AL9d45n6",
    "29x1Oph0-XC0oD132-726pM8DX",
    "19V3Pd0r-BAo7w980-W72Se5t1",
    "d1N82e7t-3D5Ba98T-9zX5y78C",
    "a5E4W71j-9Ye2J4r3-bm9M26O8",
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
    rich.print("By [blue]0x24a[/blue], Version [bold][green]v0.0.1[/green][/bold]\n")
    rich.print(f"Loaded [blue][yellow]{len(BASE_KEYS)}[/yellow][/blue] Base Keys")
    keys = []
    for i in range(1, num + 1):
        rich.print(f"\nGenerating... [yellow]({i}/{num})[/yellow]")
        sleep_time = 0
        while 1:
            try:
                key = generate_key(random.choice(BASE_KEYS))
                keys.append(key)
                break
            except KeyboardInterrupt:
                rich.print(f"[red]Cancelled[/red]")
                exit(1)
            except:
                sleep_time += 30
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


if __name__ == "__main__":
    if len(sys.argv) == 1:
        rich.print(f"Generate Number: ", end="")
        num = input()
        if not num.isdigit():
            rich.print(f"[bold][red]Invaild number.[/red][/bold]")
            exit(1)
        num = int(num)
        cli(num)
    else:
        cli(int(sys.argv[1]))
