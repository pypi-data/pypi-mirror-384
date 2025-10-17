import datetime
import json
import re
import urllib.parse
import uuid
from enum import Enum
from typing import List

from dataclasses import dataclass

import regex
from bs4 import BeautifulSoup
from foxypack import (
    FoxyStat,
    FoxyAnalysis,
    Entity,
    Storage,
    AnswersAnalysis,
    AnswersStatistics,
)
from foxypack.entitys.balancers import BaseEntityBalancer
from foxypack.entitys.pool import EntityPool
from pydantic import BaseModel, Field
from pytubefix import Channel, YouTube


class YouTubeEnum(Enum):
    shorts = "shorts"
    video = "video"
    channel = "channel"


class YoutubeAnswersAnalysis(AnswersAnalysis):
    answer_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    code: str


class YoutubeVideoAnswersStatistics(AnswersStatistics):
    answer_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    system_id: str
    channel_id: str
    title: str
    likes: int
    link: str
    views: int
    channel_url: str
    publish_date: datetime.datetime


class HeavyYoutubeVideoAnswersStatistics(YoutubeVideoAnswersStatistics):
    pytube_ob: YouTube

    model_config = {"arbitrary_types_allowed": True}


class ExternalLink(BaseModel):
    title: str
    link: str


class YouTubeChannelAnswersStatistics(AnswersStatistics):
    answer_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    channel_id: str
    name: str
    link: str
    description: str
    country: str
    view_count: int
    subscriber: int
    number_videos: int
    data_create: datetime.date
    external_link: List[ExternalLink]


class HeavyYouTubeChannelAnswersStatistics(YouTubeChannelAnswersStatistics):
    pytube_ob: Channel

    model_config = {"arbitrary_types_allowed": True}


@Storage.register_type
@dataclass(kw_only=True)
class YoutubeProxy(Entity):
    proxy_str: str

    def __post_init__(self):
        self.proxy_comparison = {
            "http": f"{self.proxy_str}",
            "https": f"{self.proxy_str}",
        }


class FoxyYouTubeAnalysis(FoxyAnalysis):
    @staticmethod
    def get_code(link):
        parsed_url = urllib.parse.urlparse(link)
        if "watch" in parsed_url.path:
            query_params = urllib.parse.parse_qs(parsed_url.query)
            return query_params.get("v")[0].split("?")[0]
        elif "shorts" in parsed_url.path:
            return parsed_url.path.split("/shorts/")[1].split("?")[0]
        elif "@" in parsed_url.path:
            return parsed_url.path.split("@")[1]
        elif "channel" in parsed_url.path:
            return parsed_url.path.split("channel/")[1]
        elif "/" in parsed_url.path:
            return parsed_url.path.split("/")[1]
        return None

    @staticmethod
    def clean_link(link):
        parsed_url = urllib.parse.urlparse(link)
        if "watch" in parsed_url.path:
            query_params = urllib.parse.parse_qs(parsed_url.query)
            return (
                f"https://youtube.com/watch?v={query_params.get('v')[0].split('?')[0]}"
            )
        elif "shorts" in parsed_url.path:
            shorts_id = parsed_url.path.split("/shorts/")[1].split("?")[0]
            return f"https://youtube.com/watch?v={shorts_id}"
        elif "@" in parsed_url.path:
            return f"https://www.youtube.com/@{parsed_url.path.split('@')[1]}"
        elif "channel" in parsed_url.path:
            return (
                f"https://www.youtube.com/channel{parsed_url.path.split('channel')[1]}"
            )
        elif "/" in parsed_url.path:
            shorts_id = parsed_url.path.split("/")[1]
            return f"https://youtube.com/watch?v={shorts_id}"
        return parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path

    @staticmethod
    def get_type_content(link):
        parsed_url = urllib.parse.urlparse(link)
        if "watch" in parsed_url.path:
            return YouTubeEnum.video.value
        if "youtu.be" in parsed_url.netloc:
            return YouTubeEnum.video.value
        elif "shorts" in parsed_url.path:
            return YouTubeEnum.shorts.value
        elif "@" in parsed_url.path or "channel" in parsed_url.path:
            return YouTubeEnum.channel.value
        return None

    def get_analysis(self, url: str) -> AnswersAnalysis | None:
        type_content = self.get_type_content(url)
        if type_content is None:
            return None
        return YoutubeAnswersAnalysis(
            url=self.clean_link(url),
            social_platform="youtube",
            type_content=type_content,
            code=self.get_code(url),
        )


class YouTubeChannel:
    def __init__(
        self,
        link: str,
        object_sn: YoutubeAnswersAnalysis,
        proxy: dict = None,
        heavy_answers: bool = False,
    ):
        self._proxy = proxy
        self._heavy_answers = heavy_answers
        self._object_sn = object_sn
        self._object_channel = self.get_object_youtube(link, self._proxy)
        self.name = self._object_channel.channel_name
        self.link = self._object_channel.channel_url
        self.description = self.get_description()
        self.country = self.get_country()
        self.code = self._object_channel.channel_id
        self.view_count = self.get_view_count()
        self.data_create = self.get_data_create()
        self.number_videos = self.get_number_videos()
        self.subscriber = self.get_subscriber()
        self.external_links = self.get_external_links()

    @staticmethod
    def transform_youtube_channel_link(url: str) -> str:
        pattern = r"https://www\.youtube\.com/@([\w-]+)"
        match = re.match(pattern, url)

        if match:
            channel_name = match.group(1)
            return f"https://www.youtube.com/c/{channel_name}/videos"

        else:
            return url

    @staticmethod
    def get_object_youtube(link, proxies) -> Channel:
        channel = Channel(link, "WEB", proxies, use_po_token=True)
        return channel

    @staticmethod
    def extract_json(text):
        json_pattern = regex.compile(r"\{(?:[^{}]|(?R))*\}")
        json_matches = json_pattern.findall(str(text))
        extracted_json = []
        for match in json_matches:
            try:
                json_data = json.loads(match)
                extracted_json.append(json_data)
            except json.JSONDecodeError:
                pass
        return extracted_json

    def get_base_con(self):
        soup = BeautifulSoup(self._object_channel.about_html, "html.parser")
        script = soup.find_all("script")
        data = self.extract_json(script)
        try:
            return data[4].get("onResponseReceivedEndpoints")
        except:
            return data[3].get("onResponseReceivedEndpoints")

    def get_country(self):
        data = self.get_base_con()
        text_country = (
            data[0]
            .get("showEngagementPanelEndpoint")
            .get("engagementPanel")
            .get("engagementPanelSectionListRenderer")
            .get("content")
            .get("sectionListRenderer")
            .get("contents")[0]
            .get("itemSectionRenderer")
            .get("contents")[0]
            .get("aboutChannelRenderer")
            .get("metadata")
            .get("aboutChannelViewModel")
            .get("country")
        )
        return text_country

    def get_view_count(self):
        data = self.get_base_con()
        text_view_count = (
            data[0]
            .get("showEngagementPanelEndpoint")
            .get("engagementPanel")
            .get("engagementPanelSectionListRenderer")
            .get("content")
            .get("sectionListRenderer")
            .get("contents")[0]
            .get("itemSectionRenderer")
            .get("contents")[0]
            .get("aboutChannelRenderer")
            .get("metadata")
            .get("aboutChannelViewModel")
            .get("viewCountText")
        )
        view_count = Convert.convert_views_to_int(text_view_count)
        return view_count

    def get_number_videos(self):
        data = self.get_base_con()
        number_videos = (
            data[0]
            .get("showEngagementPanelEndpoint", {})
            .get("engagementPanel", {})
            .get("engagementPanelSectionListRenderer", {})
            .get("content", {})
            .get("sectionListRenderer", {})
            .get("contents", [{}])[0]
            .get("itemSectionRenderer", {})
            .get("contents", [{}])[0]
            .get("aboutChannelRenderer", {})
            .get("metadata", {})
            .get("aboutChannelViewModel", {})
            .get("videoCountText")
        )
        number_videos = Convert.convert_number_videos(number_videos)
        return number_videos

    def get_subscriber(self):
        data = self.get_base_con()
        text_subscriber = (
            data[0]
            .get("showEngagementPanelEndpoint")
            .get("engagementPanel")
            .get("engagementPanelSectionListRenderer")
            .get("content")
            .get("sectionListRenderer")
            .get("contents")[0]
            .get("itemSectionRenderer")
            .get("contents")[0]
            .get("aboutChannelRenderer")
            .get("metadata")
            .get("aboutChannelViewModel")
            .get("subscriberCountText")
        )
        subscriber = Convert.convert_subscribers_to_int(text_subscriber)
        return subscriber

    def get_data_create(self):
        data = self.get_base_con()
        data_create = (
            data[0]
            .get("showEngagementPanelEndpoint", {})
            .get("engagementPanel", {})
            .get("engagementPanelSectionListRenderer", {})
            .get("content", {})
            .get("sectionListRenderer", {})
            .get("contents", [{}])[0]
            .get("itemSectionRenderer", {})
            .get("contents", [{}])[0]
            .get("aboutChannelRenderer", {})
            .get("metadata", {})
            .get("aboutChannelViewModel", {})
            .get("joinedDateText", {})
            .get("content")
        )
        data_create = Convert.convert_data_create(data_create)
        return data_create

    def get_description(self):
        data = self.get_base_con()
        text_description = (
            data[0]
            .get("showEngagementPanelEndpoint")
            .get("engagementPanel")
            .get("engagementPanelSectionListRenderer")
            .get("content")
            .get("sectionListRenderer")
            .get("contents")[0]
            .get("itemSectionRenderer")
            .get("contents")[0]
            .get("aboutChannelRenderer")
            .get("metadata")
            .get("aboutChannelViewModel")
            .get("description")
        )
        return text_description

    def get_external_links(self):
        data = self.get_base_con()
        external_links = (
            data[0]
            .get("showEngagementPanelEndpoint")
            .get("engagementPanel")
            .get("engagementPanelSectionListRenderer")
            .get("content")
            .get("sectionListRenderer")
            .get("contents")[0]
            .get("itemSectionRenderer")
            .get("contents")[0]
            .get("aboutChannelRenderer")
            .get("metadata")
            .get("aboutChannelViewModel")
            .get("links")
        )
        return [
            ExternalLink(
                title=link_data.get("channelExternalLinkViewModel")
                .get("title")
                .get("content"),
                link=f"http://{link_data.get('channelExternalLinkViewModel').get('link').get('content')}",
            )
            for link_data in external_links
        ]

    @property
    def object_channel(self):
        return self._object_channel

    def get_statistics(self):
        if self._heavy_answers:
            return HeavyYouTubeChannelAnswersStatistics(
                name=self.name,
                link=self.link,
                description=self.description,
                country=self.country,
                channel_id=self.code,
                view_count=self.view_count,
                subscriber=self.subscriber,
                data_create=self.data_create,
                number_videos=self.number_videos,
                pytube_ob=self.object_channel,
                external_link=self.external_links,
            )
        else:
            return YouTubeChannelAnswersStatistics(
                name=self.name,
                link=self.link,
                description=self.description,
                country=self.country,
                channel_id=self.code,
                view_count=self.view_count,
                subscriber=self.subscriber,
                data_create=self.data_create,
                number_videos=self.number_videos,
                external_link=self.external_links,
            )

    async def get_statistics_async(self):
        if self._heavy_answers:
            return HeavyYouTubeChannelAnswersStatistics(
                name=self.name,
                link=self.link,
                description=self.description,
                country=self.country,
                channel_id=self.code,
                view_count=self.view_count,
                subscriber=self.subscriber,
                data_create=self.data_create,
                number_videos=self.number_videos,
                pytube_ob=self.object_channel,
                external_link=self.external_links,
            )
        else:
            return YouTubeChannelAnswersStatistics(
                name=self.name,
                link=self.link,
                description=self.description,
                country=self.country,
                channel_id=self.code,
                view_count=self.view_count,
                subscriber=self.subscriber,
                data_create=self.data_create,
                number_videos=self.number_videos,
                external_link=self.external_links,
            )


class YouTubeVideo:
    def __init__(
        self,
        link: str,
        object_sn: YoutubeAnswersAnalysis,
        proxy: dict | None = None,
        heavy_answers: bool = False,
    ):
        self._proxy = proxy
        self._heavy_answers = heavy_answers
        self._object_sn = object_sn
        self._object_youtube = self.get_object_youtube(link, self._proxy)
        self.title = self._object_youtube.title
        self.likes = self.get_like_num(self._object_youtube)
        self.link = self._object_youtube.watch_url
        self.code = self._object_youtube.channel_id
        self.views = self._object_youtube.views
        self.system_id = self._object_youtube.video_id
        self.channel_url = self._object_youtube.channel_url
        self.publish_date = self._object_youtube.publish_date

    @staticmethod
    def get_object_youtube(link, proxy) -> YouTube:
        youtube = YouTube(link, "WEB", proxies=proxy)
        return youtube

    @staticmethod
    def get_like_num(youtube: YouTube) -> bool | int:
        like_template = r"like this video along with (.*?) other people"
        text = str(youtube.initial_data)
        matches = re.findall(like_template, text, re.MULTILINE)
        if len(matches) >= 1:
            like_str = matches[0]
            return int(like_str.replace(",", ""))
        return False

    @classmethod
    def __str__(cls) -> str:
        return "video"

    @property
    def object_youtube(self):
        return self._object_youtube

    def get_statistics(self):
        if self._heavy_answers:
            return HeavyYoutubeVideoAnswersStatistics(
                title=self.title,
                likes=self.likes,
                link=self.link,
                channel_id=self.code,
                views=self.views,
                system_id=self.system_id,
                channel_url=self.channel_url,
                publish_date=self.publish_date,
                pytube_ob=self.object_youtube,
            )
        else:
            return YoutubeVideoAnswersStatistics(
                title=self.title,
                likes=self.likes,
                link=self.link,
                channel_id=self.code,
                views=self.views,
                system_id=self.system_id,
                channel_url=self.channel_url,
                publish_date=self.publish_date,
            )

    async def get_statistics_async(self):
        if self._heavy_answers:
            return HeavyYoutubeVideoAnswersStatistics(
                title=self.title,
                likes=self.likes,
                link=self.link,
                channel_id=self.code,
                views=self.views,
                system_id=self.system_id,
                channel_url=self.channel_url,
                publish_date=self.publish_date,
                pytube_ob=self.object_youtube,
            )
        else:
            return YoutubeVideoAnswersStatistics(
                title=self.title,
                likes=self.likes,
                link=self.link,
                channel_id=self.code,
                views=self.views,
                system_id=self.system_id,
                channel_url=self.channel_url,
                publish_date=self.publish_date,
            )


class Convert:
    @staticmethod
    def convert_views_to_int(views_str: str) -> int:
        try:
            clean_str = views_str.replace(",", "").replace(" views", "").strip()
            return int(clean_str)
        except Exception:
            return 0

    @staticmethod
    def convert_subscribers_to_int(subscribers_str: str) -> int:
        clean_str = subscribers_str.replace(" subscribers", "").strip()

        if "K" in clean_str:
            return int(float(clean_str.replace("K", "")) * 1000)
        elif "M" in clean_str:
            return int(float(clean_str.replace("M", "")) * 1000000)
        else:
            return int(clean_str)

    @staticmethod
    def convert_number_videos(number_videos: str) -> int:
        try:
            return int(number_videos.split(" ")[0])
        except ValueError:
            long_int = number_videos.split(" ")[0].split(",")
            return int(f"{long_int[0]}{long_int[1]}")
        except Exception:
            return 0

    @staticmethod
    def convert_data_create(data_create: str) -> datetime.date:
        date_part = data_create.replace("Joined ", "")
        joined_date = datetime.datetime.strptime(date_part, "%b %d, %Y").date()
        return joined_date


class FoxyYouTubeStat(FoxyStat):
    def __init__(
        self,
        entity_pool: EntityPool | None = None,
        entity_balancer: BaseEntityBalancer | None = None,
        heavy_answers: bool = False,
    ):
        self.entity_pool = entity_pool
        self.entity_balancer = entity_balancer
        self.heavy_answers = heavy_answers

    def get_stat(
        self, answers_analysis: YoutubeAnswersAnalysis
    ) -> AnswersStatistics | None:
        try:
            proxy = self.entity_balancer.get(YoutubeProxy)
            self.entity_balancer.release(proxy)
            proxy = proxy.proxy_comparison
        except (LookupError, AttributeError):
            proxy = None
        if answers_analysis.type_content == YouTubeEnum.channel.value:
            return YouTubeChannel(
                link=answers_analysis.url,
                object_sn=answers_analysis,
                proxy=proxy,
                heavy_answers=self.heavy_answers,
            ).get_statistics()
        else:
            return YouTubeVideo(
                link=answers_analysis.url,
                object_sn=answers_analysis,
                proxy=proxy,
                heavy_answers=self.heavy_answers,
            ).get_statistics()

    async def get_stat_async(
        self, answers_analysis: YoutubeAnswersAnalysis
    ) -> AnswersStatistics | None:
        try:
            proxy = self.entity_balancer.get(YoutubeProxy)
            self.entity_balancer.release(proxy)
            proxy = proxy.proxy_comparison
        except (LookupError, AttributeError):
            proxy = None
        if answers_analysis.type_content == YouTubeEnum.channel.value:
            statistics = await YouTubeChannel(
                link=answers_analysis.url,
                object_sn=answers_analysis,
                proxy=proxy,
                heavy_answers=self.heavy_answers,
            ).get_statistics_async()
            return statistics
        else:
            statistics = await YouTubeVideo(
                link=answers_analysis.url,
                object_sn=answers_analysis,
                proxy=proxy,
                heavy_answers=self.heavy_answers,
            ).get_statistics_async()
            return statistics
