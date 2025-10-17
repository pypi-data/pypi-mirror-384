import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ScribeSearch: Semantic search over SRT, YouTube, or local videos.")
    parser.add_argument(
        "--source-type",
        "-t",
        type=str,
        choices=["srt", "youtube", "video", "auto"],
        default="auto",
        help="Source type, srt file, youtube or local video. Defaults to auto and tries to infer the source.",
    )
    parser.add_argument("source", type=str, nargs="+", help="YouTube URLs, path to .srt files, or local video files")
    parser.add_argument("--query", "-q", type=str, help="Semantic search query")
    parser.add_argument("--top", "-n", type=int, default=5, help="Number of top results to return")
    return parser.parse_args()
