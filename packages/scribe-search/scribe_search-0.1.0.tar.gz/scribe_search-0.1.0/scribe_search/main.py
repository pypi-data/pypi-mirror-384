import sys

from scribe_search.exceptions import ScribeSearchException
from scribe_search.utils import scribe_search

from .cli import parse_args


def main():
    args = parse_args()

    source = None
    try:
        results = scribe_search(args.source_type, args.source, args.query, args.top)
    except ScribeSearchException as e:
        print(e)
        sys.exit(1)

    for result in results:
        if result.chunk.source != source:
            source = result.chunk.source
            print()
            print(result.chunk.source)
            print(len(result.chunk.source) * "*")
        print(result)


if __name__ == "__main__":
    main()
