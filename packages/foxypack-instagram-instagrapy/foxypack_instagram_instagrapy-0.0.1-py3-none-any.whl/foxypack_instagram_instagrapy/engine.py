import re
import urllib.parse
import uuid
from enum import Enum
from dataclasses import dataclass

from instagrapi import Client
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


class InstagramEnum(Enum):
    reel = "reel"
    reels = "reels"
    post = "post"
    page = "page"


@Storage.register_type
@dataclass(kw_only=True)
class InstagramAccount(Entity):
    login_account: str | None = None
    password: str | None = None
    path_session_file: str | None = None


class InstagramAnswersAnalysis(AnswersAnalysis):
    answer_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    code: str


class InstagramUserAnswersStatistics(AnswersStatistics):
    answer_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    pk: int
    username: str
    full_name: str
    media_count: int
    follower_count: int
    following_count: int


class InstagramMediaAnswersStatistics(AnswersStatistics):
    answer_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    pk: int
    instagram_id: str
    view_count: int
    video_duration: float
    like_count: int
    play_count: int
    caption_text: str
    comment_count: int


class FoxyInstagramAnalysis(FoxyAnalysis):
    @staticmethod
    def get_code(link):
        match = re.search(r"/(p|reel|reels)/([^/?]+)", link)
        if match:
            return match.group(2)

        page_match = re.search(r"instagram\.com/([^/?]+)", link)
        return page_match.group(1) if page_match else None

    @staticmethod
    def clean_link(link):
        parsed_url = urllib.parse.urlparse(link)
        clean_link = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        return clean_link

    @staticmethod
    def get_type_content(url: str) -> str | None:
        parsed_url = urllib.parse.urlparse(url)
        match parsed_url.path.strip("/").split("/"):
            case ["reel" | "reels", *rest]:
                return InstagramEnum.reel.value
            case ["p", *rest]:
                return InstagramEnum.post.value
            case [username, *rest] if username:
                return InstagramEnum.page.value
            case _:
                return None

    def get_analysis(self, url: str) -> AnswersAnalysis | None:
        type_content = self.get_type_content(url)
        if type_content is None:
            return None
        return InstagramAnswersAnalysis(
            url=self.clean_link(url),
            social_platform="instagram",
            type_content=type_content,
            code=self.get_code(url),
        )


class FoxyInstagramStat(FoxyStat):
    def __init__(
        self,
        entity_pool: EntityPool | None = None,
        entity_balancer: BaseEntityBalancer | None = None,
    ):
        self.entity_pool = entity_pool
        self.entity_balancer = entity_balancer

    def get_stat(
        self, answers_analysis: InstagramAnswersAnalysis
    ) -> AnswersStatistics | None:
        try:
            instagram_account = self.entity_balancer.get(InstagramAccount)
            self.entity_balancer.release(instagram_account)
            instagram_client = Client()
            try:
                instagram_client.load_settings(instagram_account.path_session_file)
            except FileNotFoundError:
                instagram_client.login(
                    instagram_account.login_account, instagram_account.password
                )
                instagram_client.dump_settings(instagram_account.path_session_file)
        except (LookupError, AttributeError):
            raise Exception("There is no way to request data without an account")
        match answers_analysis.type_content:
            case InstagramEnum.page.value:
                user_id = instagram_client.user_id_from_username(answers_analysis.code)
                data_user = instagram_client.user_info(user_id)
                return InstagramUserAnswersStatistics(
                    pk=data_user.pk,
                    username=data_user.username,
                    full_name=data_user.full_name,
                    media_count=data_user.media_count,
                    follower_count=data_user.follower_count,
                    following_count=data_user.following_count,
                )
            case InstagramEnum.reel.value:
                media_id = instagram_client.media_pk_from_url(answers_analysis.url)
                media_info = instagram_client.media_info(media_id)
                return InstagramMediaAnswersStatistics(
                    pk=media_info.pk,
                    instagram_id=media_info.id,
                    view_count=media_info.view_count,
                    video_duration=media_info.video_duration,
                    like_count=media_info.like_count,
                    play_count=media_info.play_count,
                    caption_text=media_info.caption_text,
                    comment_count=media_info.comment_count,
                )
            case InstagramEnum.post.value:
                media_id = instagram_client.media_pk_from_url(answers_analysis.url)
                media_info = instagram_client.media_info(media_id)
                return InstagramMediaAnswersStatistics(
                    pk=media_info.pk,
                    instagram_id=media_info.id,
                    view_count=media_info.view_count,
                    video_duration=media_info.video_duration,
                    like_count=media_info.like_count,
                    play_count=media_info.play_count,
                    caption_text=media_info.caption_text,
                    comment_count=media_info.comment_count,
                )
        return None

    async def get_stat_async(
        self, answers_analysis: InstagramAnswersAnalysis
    ) -> AnswersStatistics | None:
        pass
