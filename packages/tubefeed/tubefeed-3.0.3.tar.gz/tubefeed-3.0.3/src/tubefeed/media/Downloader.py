import asyncio
import logging
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile

from .ChapterList import ChapterList


class Downloader:
    def __init__(self, url: str, download_format: str, reencode_format: str = None, reencode_bitrate: str = None):
        self.url: str = url
        self.download_format: str = download_format
        self.reencode_format: str = reencode_format
        self.reencode_bitrate: str = reencode_bitrate

    async def download_to(self,
                          output_path: Path,
                          max_download_rate: str = None,
                          chapters: ChapterList = None,
                          logger: logging.Logger = None):
        if logger is None:
            logger = logging

        # prepare temporary files
        with NamedTemporaryFile(suffix='.metadata', mode='w', encoding='utf-8', delete_on_close=False) as metadata_file:
            # store chapters if there are is more than one
            if chapters is not None and len(chapters) > 1:
                metadata_file.write(';FFMETADATA1\n')

                for chapter in chapters:
                    metadata_file.write('[CHAPTER]\n')
                    metadata_file.write('TIMEBASE=1/1\n')
                    metadata_file.write(f'START={chapter.start}\n')
                    metadata_file.write(f'END={chapter.end}\n')
                    metadata_file.write(f'TITLE={chapter.title}\n')

                metadata_path = Path(metadata_file.name)
            else:
                metadata_path = None

            metadata_file.close()  # Close it, so ffmpeg can read a flushed file.

            # start download function in background
            yt_dlp_options = {
                'f': self.download_format,
                'r': max_download_rate
            }

            if self.reencode_format is None:
                ffmpeg_options = {
                    'c:a': 'copy'
                }
            else:
                ffmpeg_options = {
                    'c:a': self.reencode_format,
                    'b:a': self.reencode_bitrate if self.reencode_format is not None else '96k'
                }

            # Use a normal subprocess for yt-dlp. The output is piped to ffmpeg
            # and therefore does not block the thread anyway.
            yt_dlp_command = [
                'yt-dlp',
                '-q',
                *(
                    e
                    for k, v in yt_dlp_options.items()
                    if v is not None
                    for e in (f'-{k}', str(v))
                ),
                '-o', '-',
                self.url
            ]
            logger.info(' '.join(yt_dlp_command))

            yt_dlp_process = subprocess.Popen(
                yt_dlp_command,
                stdout=subprocess.PIPE
            )

            # Use an async process for ffmpeg.
            ffmpeg_command = [
                'ffmpeg',
                '-v', 'warning',
                '-i', '-',
                *(('-i', str(metadata_path.absolute())) if metadata_path is not None else ()),
                '-map', '0:a:0',
                *(
                    e
                    for k, v in ffmpeg_options.items()
                    if v is not None
                    for e in (f'-{k}', str(v))
                ),
                *(('-map_chapters', '1') if metadata_path is not None else ()),
                '-y',
                str(output_path.absolute())
            ]
            logger.info(' '.join(ffmpeg_command))

            ffmpeg_process = await asyncio.create_subprocess_exec(
                *ffmpeg_command,
                stdin=yt_dlp_process.stdout
            )

            # Wait for the download to finish.
            return_code = await ffmpeg_process.wait()

            # Handle errors in case the return code is not 0.
            if return_code:
                # TODO error handling
                print('return code not 0')
