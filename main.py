import asyncio
import json
import os
import time
import uuid

import requests
from rich.console import Console
from rich.prompt import Prompt
from rich.style import Style
from rich.progress import track
from rich import print

from util.browser import OnlyFansBrowserInteraction

console = Console() # used to print to console


def download_all_posts(posts: list[dict], target_user: str, author_id: int):
    try:
        os.mkdir(f"./{target_user}")
        os.mkdir(f"./{target_user}/videos")
        os.mkdir(f"./{target_user}/images") # create directories
    except FileExistsError:
        console.print(
            "[red]Target user directory already exists. Please delete it and try again."
        )
        console.print(
            "[red]Press enter to continue. This will write all the files to an existing directory."
        )
        console.print("[red]Press CTRL+C to exit.") # warning
        console.input() # input to dismiss warning
    for post in track(posts, description="Downloading posts..."): # iter posts
        author: str = post.get("author").get("id") # get the post author id
        if author != author_id: # check if the author is the target author
            continue
        for m in post.get("media"): # iter media
            postType: str = m.get("type") # get post type
            path: str = ( # create path
                f"./{target_user}/videos/{uuid.uuid4()}.mp4"
                if postType == "video"
                else f"./{target_user}/images/{uuid.uuid4()}.jpg"
            )
            with open(path, "wb+") as file: # wrtie file
                request = requests.get(m.get("full"))
                print(
                    f"[dim] Status Code: {request.status_code} | {post.get('id')} => {path}" # show user
                )
                file.write(request.content)


async def main(): # main function
    console.rule("Only Save") # print title
    username: str = Prompt.ask( # get username
        "[yellow]Enter your OnlyFans username/email",
    )
    password: str = Prompt.ask( # get password
        "[yellow]Enter your OnlyFans password",
    )
    target_user: str = Prompt.ask( # get target user
        "[yellow]Enter the OnlyFans account you would ike to download from",
    )

    try:
        assert username
        assert password
        assert target_user   # check if all inputs are valid
    except AssertionError:
        console.print("[red]Invalid input. Make sure none of the prompts were missed.")

    console.print("[green]Input accepted. Starting OnlySave...") # start
    console.print("[dim]Starting python-playwright chromium browser")
    # show browser
    browserManager = await OnlyFansBrowserInteraction().__async_init__(console) # init browser
    # nav to onlyfans
    # enter password
    # enter username
    # click login
    await browserManager.open_login_page(username, password)
    # wait for user to complete captcha
    console.print("[green]Complete the captcha to continue...")
    console.print("[dim]Validating Login State...")
    while not browserManager.account: # wait for login. User will complete captcha
        console.print("[dim]Waiting for login state to be validated...")
        await asyncio.sleep(1)
    console.print("[green]Authentication successful.") # login successful
    console.print(f"[yellow]OnlyFansUserAccount({browserManager.account})")
    await browserManager.navigate_to_profile(target_user) # nav to target user
    await asyncio.sleep(1) # wait for page to load
    await browserManager.get_author_id() # get author id
    await browserManager.scroll_infinite() # scroll to bottom of page
    console.print("[green]Done.") # done
    console.print("[dim]Closing browser...")
    await browserManager.close() 
    console.print("[green]Browser closed.")
    console.print("[dim]Downloading posts...")
    download_all_posts(browserManager.posts, target_user, browserManager.author_id) # download posts


if __name__ == "__main__":
    asyncio.run(main())
