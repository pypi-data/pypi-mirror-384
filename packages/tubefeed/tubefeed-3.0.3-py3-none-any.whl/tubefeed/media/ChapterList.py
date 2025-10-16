from .Chapter import Chapter


class ChapterList(list[Chapter]):
    def __init__(self, chapters: list[Chapter], merge_consecutive_duplicates: bool = True):
        i = 0
        while i < len(chapters) - 1:
            if chapters[i].title == chapters[i + 1].title and merge_consecutive_duplicates:
                chapters[i + 1].start = chapters[i].start
                del chapters[i]
            else:
                i += 1

        super().__init__(chapters)

    @staticmethod
    def from_video(title: str, duration: int) -> 'ChapterList':
        return ChapterList([
            Chapter(0, duration, title)
        ])

    def __and__(self, other: 'ChapterList') -> 'ChapterList':
        chapters = []

        sources = [self, other]
        pos = [0, 0]

        while True:
            if pos[0] < len(sources[0]) and pos[1] < len(sources[1]):
                if abs(sources[0][pos[0]].start - sources[1][pos[1]].start) < 5:
                    use = [0, 1]
                elif sources[0][pos[0]].start < sources[1][pos[1]].start:
                    use = [0]
                else:
                    use = [1]
            elif pos[0] < len(sources[0]):
                use = [0]
            elif pos[1] < len(sources[1]):
                use = [1]
            else:
                break

            start = min(sources[i][pos[i]].start for i in use)
            end = min((
                max((
                    *(
                        sources[i][pos[i]].end
                        for i in use
                        if sources[i][pos[i]].end < 5 + min((
                        *(
                            sources[i][pos[i]].end
                            for i in use
                        ),
                    ))
                    ),
                )),
                *(
                    sources[i][pos[i]].start
                    for i in (0, 1)
                    if pos[i] < len(sources[i]) and i not in use
                ),
            ))

            chapters.append(Chapter(start, end, sources[use[-1]][pos[use[-1]]].title))

            for i in use:
                sources[i][pos[i]].start = end

            for i in (0, 1):
                if pos[i] < len(sources[i]) and sources[i][pos[i]].end <= end:
                    pos[i] += 1

        return ChapterList(chapters)
