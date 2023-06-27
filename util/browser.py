from typing import Self

from playwright.async_api import Request, async_playwright
from playwright.async_api._generated import Response as ResponseType

from util.onlyfans_user import OnlyFansUserAccount


class OnlyFansBrowserInteraction:
    async def __async_init__(self, std_out_console) -> Self:
        self.console = std_out_console
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        self.page.on("response", self.response_logger)
        self.targetUserAccountId = ()
        self.account: OnlyFansUserAccount | None = None
        self.posts: list[dict] = list()
        self.author_id: int = None
        return self

    async def open_login_page(self, username: str, password: str):
        self.console.print("[dim]Navigating to OnlyFans login page...")
        await self.page.goto("https://onlyfans.com") # navigate to onlyfans
        self.console.print("[dim]Entering login credentials...")
        email_input = self.page.locator("input[name='email']") # get email input
        password_input = self.page.locator("input[name='password']") # get password input
        await email_input.fill(username) # enter username
        await password_input.fill(password) # enter password
        self.console.print("[dim]Logging in...") # click login
        await self.page.locator("button:has-text('Log in')").click()
        self.console.print("[dim]Waiting for user to complete captcha...")

    async def navigate_to_profile(self, profile_name: str):
        self.console.print(f"[dim]Navigating to profile { profile_name }")
        await self.page.goto(f"https://onlyfans.com/{profile_name}") # navigate to target user
        await self.page.wait_for_timeout(2000) # wait for page to load

    async def response_logger(self, response: ResponseType):
        if "posts?" in response.url: # if url contains posts?. This is OF requests for posts data
            try:
                self.posts.extend((await response.json()).get("list")) # add posts to list
            except Exception as e:
                pass
            return

        if response.url == "https://onlyfans.com/api2/v2/users/me": # this is for auth check
            try:
                self.account = OnlyFansUserAccount(**await response.json())
            except Exception as e:
                self.console.print("[red]Failed to parse account data.", e)
            return

    async def scroll_infinite(self):
        """infinite scroll logic. Kinda weird. But it works."""
        maxPageCounter = 0
        while True:
            await self.page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight)"
            )  # scroll to bottom of page
            await self.page.wait_for_timeout(500)  # wait a bit

            # if bottom == true
            if await self.page.evaluate(
                "window.innerHeight + window.scrollY >= document.body.offsetHeight"
            ):
                maxPageCounter += (
                    1  # now track that bottom has been reached maxPageCounter times.
                )
            else:
                maxPageCounter = 0  # if new content is loaded, reset the counter

            if maxPageCounter > 10:  # once 10 attempts have been made
                for _ in range(10):  # try 10 more times
                    await self.page.evaluate(
                        "window.scrollTo(0, document.body.scrollHeight)"
                    )  # scroll to bottom

                    if not await self.page.evaluate(
                        "window.innerHeight + window.scrollY >= document.body.offsetHeight"
                    ):
                        maxPageCounter += 1
                    else:
                        maxPageCounter = 0
                        break
                break

    async def close(self):
        await self.browser.close()

    async def get_author_id(self):
        """gets the author id from the link of a profile pic"""
        self.author_id = int(
            (
                await (
                    await self.page.query_selector("div.g-avatar__img-wrapper img")
                ).get_attribute("src")
            ).split("/")[-2]
        )
