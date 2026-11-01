import asyncio
import os
from pathlib import Path

import flet as ft
from androidtvremote2 import (
    AndroidTVRemote,
    CannotConnect,
    ConnectionClosed,
    InvalidAuth,
)

# Store pairing certificates privately on the phone.
DATA_DIR = Path(
    os.environ.get("FLET_APP_STORAGE_DATA")
    or (Path.home() / ".tv_remote")
)
DATA_DIR.mkdir(parents=True, exist_ok=True)
CERT_FILE = str(DATA_DIR / "cert.pem")
KEY_FILE = str(DATA_DIR / "key.pem")


async def main(page: ft.Page):
    page.title = "Android TV Remote"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    remote_state = {"remote": None}

    status = ft.Text(
        "Not connected",
        size=16,
    )

    tv_ip = ft.TextField(
        label="TV IP address",
        hint_text="Example: 192.168.1.100",
    )

    pairing_code = ft.TextField(
        label="Enter the code shown on your TV",
        visible=False,
    )

    text_input = ft.TextField(
        label="Type text for your TV",
        expand=True,
    )

    async def connect_tv(e):
        host = (tv_ip.value or "").strip()

        if not host:
            status.value = "Please enter your TV IP address."
            page.update()
            return

        try:
            status.value = "Connecting..."
            page.update()

            had_certificate = (
                os.path.exists(CERT_FILE)
                and os.path.exists(KEY_FILE)
            )

            remote = AndroidTVRemote(
                "My Android TV Remote",
                CERT_FILE,
                KEY_FILE,
                host,
            )

            remote_state["remote"] = remote

            await remote.async_generate_cert_if_missing()

            if had_certificate:
                await remote.async_connect()
                remote.keep_reconnecting()

                status.value = "Connected to your TV!"
            else:
                name, mac = await remote.async_get_name_and_mac()

                await remote.async_start_pairing()

                pairing_code.visible = True
                pair_button.visible = True

                status.value = (
                    f"Pairing with {name}. "
                    "Check your TV screen for the code."
                )

        except Exception as error:
            status.value = f"Connection error: {error}"

        page.update()

    async def finish_pairing(e):
        remote = remote_state["remote"]
        code = (pairing_code.value or "").strip()

        if remote is None or not code:
            status.value = "Enter the pairing code first."
            page.update()
            return

        try:
            status.value = "Pairing..."
            page.update()

            await remote.async_finish_pairing(code)
            await remote.async_connect()
            remote.keep_reconnecting()

            pairing_code.visible = False
            pair_button.visible = False

            status.value = "Successfully paired and connected!"

        except InvalidAuth:
            status.value = "Incorrect code. Please try again."
        except Exception as error:
            status.value = f"Pairing error: {error}"

        page.update()

    def send_key(key):
        async def handler(e):
            remote = remote_state["remote"]

            if remote is None:
                status.value = "Connect to your TV first."
            else:
                try:
                    remote.send_key_command(key)
                    status.value = f"Sent: {key}"
                except Exception as error:
                    status.value = str(error)

            page.update()

        return handler

    async def send_text(e):
        remote = remote_state["remote"]
        value = (text_input.value or "").strip()

        if remote is None:
            status.value = "Connect to your TV first."
        elif value:
            try:
                remote.send_text(value)
                status.value = "Text sent!"
                text_input.value = ""
            except Exception as error:
                status.value = str(error)

        page.update()

    pair_button = ft.ElevatedButton(
        "Complete Pairing",
        visible=False,
        on_click=finish_pairing,
    )

    page.add(
        ft.Column(
            [
                ft.Text(
                    "ANDROID TV REMOTE",
                    size=25,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Connect your phone and TV to the same Wi-Fi."
                ),
                ft.Divider(),
                tv_ip,
                ft.ElevatedButton(
                    "Connect to TV",
                    icon=ft.Icons.WIFI,
                    on_click=connect_tv,
                ),
                pairing_code,
                pair_button,
                status,
                ft.Divider(),
                ft.Text("NAVIGATION", weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.Container(width=65),
                        ft.ElevatedButton(
                            "▲",
                            on_click=send_key("DPAD_UP"),
                        ),
                        ft.Container(width=65),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "◀",
                            on_click=send_key("DPAD_LEFT"),
                        ),
                        ft.ElevatedButton(
                            "OK",
                            on_click=send_key("DPAD_CENTER"),
                        ),
                        ft.ElevatedButton(
                            "▶",
                            on_click=send_key("DPAD_RIGHT"),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.Container(width=65),
                        ft.ElevatedButton(
                            "▼",
                            on_click=send_key("DPAD_DOWN"),
                        ),
                        ft.Container(width=65),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Divider(),
                ft.Text("REMOTE CONTROLS", weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "HOME",
                            on_click=send_key("HOME"),
                        ),
                        ft.ElevatedButton(
                            "BACK",
                            on_click=send_key("BACK"),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "POWER",
                            on_click=send_key("POWER"),
                        ),
                        ft.ElevatedButton(
                            "MUTE",
                            on_click=send_key("MUTE"),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "VOL +",
                            on_click=send_key("VOLUME_UP"),
                        ),
                        ft.ElevatedButton(
                            "VOL -",
                            on_click=send_key("VOLUME_DOWN"),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.ElevatedButton(
                    "PLAY / PAUSE",
                    on_click=send_key("MEDIA_PLAY_PAUSE"),
                ),
                ft.Divider(),
                ft.Text("TEXT INPUT", weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        text_input,
                        ft.ElevatedButton(
                            "SEND",
                            on_click=send_text,
                        ),
                    ]
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
    )


ft.app(target=main)
          
