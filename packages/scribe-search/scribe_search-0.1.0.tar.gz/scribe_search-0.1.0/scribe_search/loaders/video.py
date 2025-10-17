import os
import tempfile

from scribe_search.exceptions import InvalidSource, ScribeSearchException

from .srt import Loader as SrtLoader

try:
    import ffmpeg
except ImportError:
    raise ScribeSearchException("Please install ffmpeg-python to use this")


class Loader:

    @staticmethod
    def load(sources: list[str]):
        for path in sources:
            # We should fail early before models take over
            if not os.path.isfile(path):
                raise InvalidSource(f"File {path} not found")
            try:
                probe = ffmpeg.probe(path)
                if not [s for s in probe["streams"] if s["codec_type"] == "subtitle"]:
                    raise InvalidSource(f"No subtitles found in video {path}")
            except Exception:
                raise InvalidSource("Error probing video")

        tmp_paths = []
        for path in sources:
            probe = ffmpeg.probe(path)
            subtitle_streams = [s for s in probe["streams"] if s["codec_type"] == "subtitle"]

            base_name = os.path.basename(path)

            for i, _stream in enumerate(subtitle_streams):

                tmp = tempfile.NamedTemporaryFile(prefix=f"{base_name}_sub{i}_", suffix=".srt", delete=False)
                tmp_path = tmp.name
                tmp.close()

                ffmpeg.input(path).output(tmp_path, map=f"0:s:{i}", **{"c:s": "srt"}).run(
                    quiet=True, overwrite_output=True
                )

                if os.path.exists(tmp_path):
                    tmp_paths.append(tmp_path)

        subs = list(SrtLoader.load(tmp_paths))

        for path in tmp_paths:
            os.remove(path)

        return subs
