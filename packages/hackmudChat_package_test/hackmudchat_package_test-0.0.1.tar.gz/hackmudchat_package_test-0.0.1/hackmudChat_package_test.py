"""A python implementation of the hackmud chat API, using the requests module."""

__version__ = "0.0.1"


def send(user: str, channel: str, msg: str) -> None:
    """
    Sends a message from the inputted user to the inputted channel containing the inputted msg.

    Args:
        user (str): The user to send the message from.
        channel (str): The channel to send the message to.
        msg (str): The message to send.
    """
    import requests
    import json
    from sys import path

    with open(f"{path[0]}/config.json") as f:
        config: dict = json.load(f)

    token: str = config["chat_token"]
    header: dict = config["header"]

    payload = {
        "chat_token": token,
        "username": user,
        "channel": channel,
        "msg": msg,
    }

    requests.post(
        url="https://www.hackmud.com/mobile/create_chat.json",
        headers=header,
        json=payload,
    )


def tell(user: str, target: str, msg: str) -> None:
    """
    Sends a message from the inputted user to the inputted target containing the inputted msg.

    Args:
        user (str): The user to send the message from.
        target (str): The target to send the message to.
        msg (str): The message to send.
    """
    import requests
    import json
    from sys import path

    with open(f"{path[0]}/config.json") as f:
        config: dict = json.load(f)

    token: str = config["chat_token"]
    header: dict = config["header"]

    payload = {
        "chat_token": token,
        "username": user,
        "tell": target,
        "msg": msg,
    }

    requests.post(
        url="https://www.hackmud.com/mobile/create_chat.json",
        headers=header,
        json=payload,
    )


def read(
    users: list[str], before: int | float = None, after: int | float = None
) -> dict:
    """
    Returns the messages recieved by the inputted users within the given before and after parameters.

    Args:
        users (list[str]): A list of the users who you want to read the recieved messages of.
        before (int | float, optional): A UNIX timestamp in seconds with a fractional component. Defaults to "now".
        after (int | float, optional): A UNIX timestamp in seconds with a fractional component. Defaults to 60 seconds before "now".

    Returns:
        dict: The "chats" component of the request return content.
    """
    import requests
    import json
    from sys import path
    import time

    now = time.time()

    if not before:
        before = now

    if not after:
        after = now - 60

    with open(f"{path[0]}/config.json") as f:
        config: dict = json.load(f)

    token = config["chat_token"]
    header = config["header"]

    payload = {
        "chat_token": token,
        "usernames": users,
        "before": before,
        "after": after,
    }

    chats: dict = json.loads(
        requests.post(
            url="https://www.hackmud.com/mobile/chats.json",
            headers=header,
            json=payload,
        ).content
    )["chats"]

    return chats


class ChatAPI:
    # import requests
    # import json
    from sys import path

    def __init__(self, config_file: str = f"{path[0]}/config.json"):
        self.config_file = config_file
        self.config: dict

        try:
            self.load_config()
        except FileNotFoundError:

            self.config = {"header": {"Content-Type": "application/json"}}
            self.save_config()
            self.load_config()

            self.get_token()
            self.get_users()

        self.header: dict = self.config["header"]
        self.token: str = self.config["chat_token"]
        self.users = self.get_users()

    def load_config(self):
        import json

        with open(self.config_file) as f:
            self.config: dict = json.load(f)
            self.header: dict = self.config["header"]

    def save_config(self):
        import json

        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)

    def get_token(self, chat_pass: str | None = None) -> None:
        """
        Gets a chat API token from the inputted chat_pass, which is obtained from running "chat_pass" in-game.

        Args:
            chat_pass (str | None, optional): The chat_pass to get the token from. If one is not given, prompts for it in the terminal. Defaults to None.
        """
        import requests
        import json

        self.load_config()

        if not chat_pass:
            chat_pass = input("chat_pass password: ")

        if chat_pass != "":
            self.token = json.loads(
                requests.post(
                    url="https://www.hackmud.com/mobile/get_token.json",
                    headers={"Content-Type": "application/json"},
                    json={"pass": chat_pass},
                ).content
            )["chat_token"]
            self.config["chat_token"] = self.token

            self.save_config()

    def get_users(self) -> list[str]:
        import requests
        import json

        self.load_config()

        self.config["users"] = json.loads(
            requests.post(
                url="https://www.hackmud.com/mobile/account_data.json",
                headers=self.header,
                json={"chat_token": self.token},
            ).content
        )["users"]

        self.save_config()

        return list(self.config["users"].keys())

    def send(self, user: str, channel: str, msg: str) -> None:
        """
        Sends a message from the inputted user to the inputted channel containing the inputted msg.

        Args:
            user (str): The user to send the message from.
            channel (str): The channel to send the message to.
            msg (str): The message to send.
        """
        import requests

        payload = {
            "chat_token": self.token,
            "username": user,
            "channel": channel,
            "msg": msg,
        }

        requests.post(
            url="https://www.hackmud.com/mobile/create_chat.json",
            headers=self.header,
            json=payload,
        )

    def tell(self, user: str, target: str, msg: str) -> None:
        """
        Sends a message from the inputted user to the inputted target containing the inputted msg.

        Args:
            user (str): The user to send the message from.
            target (str): The target to send the message to.
            msg (str): The message to send.
        """
        import requests

        payload = {
            "chat_token": self.token,
            "username": user,
            "tell": target,
            "msg": msg,
        }

        requests.post(
            url="https://www.hackmud.com/mobile/create_chat.json",
            headers=self.header,
            json=payload,
        )

    def read(
        self,
        *,
        after: int | float | None = 60,
        before: int | float | None = None,
        users: list[str] = None,
    ) -> dict:
        """
        Returns the messages recieved by the inputted users within the given before and after parameters.

        Args:
            after (int | float, optional): Number of seconds before "now". Defaults to 60.
            before (int | float, optional): Number of seconds before "now". Defaults to 0.
            users (list[str]): A list of the users who you want to read the recieved messages of. Defaults to all users.

        Returns:
            dict: The "chats" component of the request return content.
        """
        import requests
        import json
        import time

        now = time.time()

        if not users:
            users = self.users

        payload = {
            "chat_token": self.token,
            "usernames": users,
            "before": ((now - before) if before else None),
            "after": ((now - after) if after else None),
        }

        chats: dict = json.loads(
            requests.post(
                url="https://www.hackmud.com/mobile/chats.json",
                headers=self.header,
                json=payload,
            ).content
        )["chats"]

        return chats
