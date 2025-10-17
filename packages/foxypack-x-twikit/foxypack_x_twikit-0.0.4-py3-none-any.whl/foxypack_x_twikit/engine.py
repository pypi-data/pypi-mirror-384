import re
import urllib.parse
import uuid
from enum import Enum
from dataclasses import dataclass

from twikitminifix import Client
from foxypack.entitys.balancers import BaseEntityBalancer
from foxypack.entitys.pool import EntityPool
from pydantic import Field

from foxypack import (
    FoxyStat,
    FoxyAnalysis,
    Entity,
    Storage,
    AnswersAnalysis,
    AnswersStatistics,
)


class TwitterEnum(Enum):
    tweet = "tweet"
    profile = "profile"


@Storage.register_type
@dataclass(kw_only=True)
class TwitterAccount(Entity):
    username: str
    email: str
    password: str
    cookies_file: str = "twitter_cookies.json"


class TwitterAnswersAnalysis(AnswersAnalysis):
    answer_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    code: str


class TwitterProfileAnswersStatistics(AnswersStatistics):
    answer_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    user_id: str
    username: str
    screen_name: str
    followers_count: int
    following_count: int
    tweet_count: int
    listed_count: int
    favourites_count: int
    verified: bool
    description: str
    location: str
    profile_image_url: str


class TwitterTweetAnswersStatistics(AnswersStatistics):
    answer_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    tweet_id: str
    user_id: str
    username: str
    text: str
    view_count: int
    like_count: int
    retweet_count: int
    reply_count: int
    quote_count: int
    bookmark_count: int
    language: str


class FoxyTwitterAnalysis(FoxyAnalysis):
    @staticmethod
    def get_code(link):
        # Для твитов: /status/ID
        tweet_match = re.search(r"/status/(\d+)", link)
        if tweet_match:
            return tweet_match.group(1)

        # Для профилей: /username
        profile_match = re.search(r"(?:twitter\.com|x\.com)/([^/?]+)/?$", link)
        if profile_match:
            return profile_match.group(1)

        return None

    @staticmethod
    def clean_link(link):
        parsed_url = urllib.parse.urlparse(link)
        clean_link = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        return clean_link

    @staticmethod
    def get_type_content(url: str) -> str | None:
        if "/status/" in url:
            return TwitterEnum.tweet.value
        elif re.match(r"https?://(?:twitter\.com|x\.com)/[^/?]+/?$", url):
            return TwitterEnum.profile.value
        return None

    def get_analysis(self, url: str) -> AnswersAnalysis | None:
        type_content = self.get_type_content(url)
        if type_content is None:
            return None
        return TwitterAnswersAnalysis(
            url=self.clean_link(url),
            social_platform="twitter",
            type_content=type_content,
            code=self.get_code(url),
        )


class FoxyTwitterStat(FoxyStat):
    def __init__(
        self,
        entity_pool: EntityPool | None = None,
        entity_balancer: BaseEntityBalancer | None = None,
    ):
        self.entity_pool = entity_pool
        self.entity_balancer = entity_balancer

    def _get_twitter_client(self) -> Client:
        """Получение клиента Twitter из аккаунта"""
        try:
            twitter_account = self.entity_balancer.get(TwitterAccount)
            self.entity_balancer.release(twitter_account)

            client = Client("en-US")
            try:
                client.load_cookies(twitter_account.cookies_file)
            except FileNotFoundError:
                # Для асинхронного логина нужно использовать async версию
                # В синхронном контексте это может вызвать проблемы
                import asyncio

                asyncio.run(
                    client.login(
                        auth_info_1=twitter_account.username,
                        auth_info_2=twitter_account.email,
                        password=twitter_account.password,
                    )
                )
                client.save_cookies(twitter_account.cookies_file)

            return client
        except (LookupError, AttributeError):
            raise Exception("There is no way to request data without an account")

    def get_stat(
        self, answers_analysis: TwitterAnswersAnalysis
    ) -> AnswersStatistics | None:
        client = self._get_twitter_client()

        match answers_analysis.type_content:
            case TwitterEnum.profile.value:
                import asyncio

                user_data = asyncio.run(
                    client.get_user_by_screen_name(answers_analysis.code)
                )
                return TwitterProfileAnswersStatistics(
                    user_id=user_data.id,
                    username=user_data.screen_name,
                    screen_name=user_data.name,
                    followers_count=getattr(user_data, "followers_count", 0),
                    following_count=getattr(user_data, "following_count", 0),
                    tweet_count=getattr(user_data, "statuses_count", 0),
                    listed_count=getattr(user_data, "listed_count", 0),
                    favourites_count=getattr(user_data, "favourites_count", 0),
                    verified=getattr(user_data, "verified", False),
                    description=getattr(user_data, "description", ""),
                    location=getattr(user_data, "location", ""),
                    profile_image_url=getattr(user_data, "profile_image_url", ""),
                )

            case TwitterEnum.tweet.value:
                import asyncio

                tweet_data = asyncio.run(client.get_tweet_by_id(answers_analysis.code))
                return TwitterTweetAnswersStatistics(
                    tweet_id=tweet_data.id,
                    user_id=tweet_data.user.id,
                    username=tweet_data.user.screen_name,
                    text=getattr(tweet_data, "text", ""),
                    view_count=getattr(tweet_data, "view_count", 0),
                    like_count=getattr(tweet_data, "favorite_count", 0),
                    retweet_count=getattr(tweet_data, "retweet_count", 0),
                    reply_count=getattr(tweet_data, "reply_count", 0),
                    quote_count=getattr(tweet_data, "quote_count", 0),
                    bookmark_count=getattr(tweet_data, "bookmark_count", 0),
                    language=getattr(tweet_data, "lang", ""),
                )

        return None

    async def get_stat_async(
        self, answers_analysis: TwitterAnswersAnalysis
    ) -> AnswersStatistics | None:
        try:
            twitter_account = self.entity_balancer.get(TwitterAccount)
            self.entity_balancer.release(twitter_account)

            client = Client("en-US")
            try:
                client.load_cookies(twitter_account.cookies_file)
            except FileNotFoundError:
                await client.login(
                    auth_info_1=twitter_account.username,
                    auth_info_2=twitter_account.email,
                    password=twitter_account.password,
                )
                client.save_cookies(twitter_account.cookies_file)

        except (LookupError, AttributeError):
            raise Exception("There is no way to request data without an account")

        match answers_analysis.type_content:
            case TwitterEnum.profile.value:
                user_data = await client.get_user_by_screen_name(answers_analysis.code)
                return TwitterProfileAnswersStatistics(
                    user_id=user_data.id,
                    username=user_data.screen_name,
                    screen_name=user_data.name,
                    followers_count=getattr(user_data, "followers_count", 0),
                    following_count=getattr(user_data, "following_count", 0),
                    tweet_count=getattr(user_data, "statuses_count", 0),
                    listed_count=getattr(user_data, "listed_count", 0),
                    favourites_count=getattr(user_data, "favourites_count", 0),
                    verified=getattr(user_data, "verified", False),
                    description=getattr(user_data, "description", ""),
                    location=getattr(user_data, "location", ""),
                    profile_image_url=getattr(user_data, "profile_image_url", ""),
                )

            case TwitterEnum.tweet.value:
                tweet_data = await client.get_tweet_by_id(answers_analysis.code)
                return TwitterTweetAnswersStatistics(
                    tweet_id=tweet_data.id,
                    user_id=tweet_data.user.id,
                    username=tweet_data.user.screen_name,
                    text=getattr(tweet_data, "text", ""),
                    view_count=getattr(tweet_data, "view_count", 0),
                    like_count=getattr(tweet_data, "favorite_count", 0),
                    retweet_count=getattr(tweet_data, "retweet_count", 0),
                    reply_count=getattr(tweet_data, "reply_count", 0),
                    quote_count=getattr(tweet_data, "quote_count", 0),
                    bookmark_count=getattr(tweet_data, "bookmark_count", 0),
                    language=getattr(tweet_data, "lang", ""),
                )

        return None
