import re

from .sb_api import SBSegment
from ...media import ChapterList as BaseChapterList, Chapter


class ChapterList(BaseChapterList):
    @staticmethod
    def from_description(description: str, duration: int) -> 'ChapterList':
        chapters: list[tuple[int, str | None]] = []

        # hh:mm:ss chapter
        # hh:mm:ss - hh:mm:ss chapter
        chapters_iter = re.finditer(r'^\s*((\d+):)?(\d+):(\d+)( ?- ?((\d+):)?(\d+):(\d+))?\s.*?(\w.*?)$',
                                    description, re.MULTILINE)

        for chapter in chapters_iter:
            hours = int(chapter.group(2)) if chapter.group(2) is not None else 0
            minutes = int(chapter.group(3)) if chapter.group(3) is not None else 0
            seconds = int(chapter.group(4)) if chapter.group(4) is not None else 0
            title = chapter.group(10).strip()

            chapters.append(((hours * 60 + minutes) * 60 + seconds, title))

        # chapter hh:mm:ss
        # chapter hh:mm:ss - hh:mm:ss
        if len(chapters) == 0:
            chapters_iter = re.finditer(r'^\s*(\w.*?):?\s.*?((\d+):)?(\d+):(\d+)( ?- ?((\d+):)?(\d+):(\d+))?$',
                                        description, re.MULTILINE)

            for chapter in chapters_iter:
                hours = int(chapter.group(3)) if chapter.group(3) is not None else 0
                minutes = int(chapter.group(4)) if chapter.group(4) is not None else 0
                seconds = int(chapter.group(5)) if chapter.group(5) is not None else 0
                title = chapter.group(1).strip()

                chapters.append(((hours * 60 + minutes) * 60 + seconds, title))

        # padding
        chapters.append((duration, None))

        # convert to Chapter objects
        return ChapterList([
            Chapter(start, end, title)
            for (start, title), (end, _) in zip(chapters, chapters[1:])
        ])

    @staticmethod
    async def from_sponsorblock(segments: list[SBSegment]) -> 'ChapterList':
        return ChapterList([
            Chapter(int(segment.start), int(segment.end), segment.category.capitalize())
            for segment in segments
        ], merge_consecutive_duplicates=False)
