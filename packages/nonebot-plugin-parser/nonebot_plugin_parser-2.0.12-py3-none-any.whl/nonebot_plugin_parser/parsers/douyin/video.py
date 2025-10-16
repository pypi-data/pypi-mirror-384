from typing import Any

from msgspec import Struct, field

from ...exception import ParseException


class Avatar(Struct):
    url_list: list[str]


class Author(Struct):
    nickname: str
    avatar_thumb: Avatar | None = None
    avatar_medium: Avatar | None = None


class PlayAddr(Struct):
    url_list: list[str]


class Cover(Struct):
    url_list: list[str]


class Video(Struct):
    play_addr: PlayAddr
    cover: Cover
    duration: int


class Image(Struct):
    video: Video | None = None
    url_list: list[str] = field(default_factory=list)


class VideoData(Struct):
    create_time: int
    author: Author
    desc: str
    images: list[Image] | None = None
    video: Video | None = None

    @property
    def image_urls(self) -> list[str]:
        return [image.url_list[0] for image in self.images] if self.images else []

    @property
    def video_url(self) -> str | None:
        return self.video.play_addr.url_list[0].replace("playwm", "play") if self.video else None

    @property
    def cover_url(self) -> str | None:
        return self.video.cover.url_list[0] if self.video else None

    @property
    def avatar_url(self) -> str | None:
        if avatar := self.author.avatar_thumb:
            return avatar.url_list[0]
        elif avatar := self.author.avatar_medium:
            return avatar.url_list[0]
        return None


class VideoInfoRes(Struct):
    item_list: list[VideoData] = field(default_factory=list)

    @property
    def video_data(self) -> VideoData:
        if len(self.item_list) == 0:
            raise ParseException("can't find data in videoInfoRes")
        return self.item_list[0]


class VideoOrNotePage(Struct):
    videoInfoRes: VideoInfoRes


class LoaderData(Struct):
    video_page: VideoOrNotePage | None = field(name="video_(id)/page", default=None)
    note_page: VideoOrNotePage | None = field(name="note_(id)/page", default=None)


class RouterData(Struct):
    loaderData: LoaderData
    errors: dict[str, Any] | None = None

    @property
    def video_data(self) -> VideoData:
        if page := self.loaderData.video_page:
            return page.videoInfoRes.video_data
        elif page := self.loaderData.note_page:
            return page.videoInfoRes.video_data
        raise ParseException("can't find video_(id)/page or note_(id)/page in router data")
