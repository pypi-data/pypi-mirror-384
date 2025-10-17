from typing import cast
from arxivfeedagent.checker import Checker
from argparse import ArgumentParser
from arxivfeedagent.library import Library
from arxivfeedagent.paper import PaperAndSummary
from arxivfeedagent.summarizer import PaperSummarizer


def main():
    parser = ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--export-format", type=str, default="markdown")
    args = parser.parse_args()

    limit: int = args.limit
    export_format: str = args.export_format

    # requirement = """I want papers that are meet one or more of following requirements
    # - About LLM agents in information retrieval
    # """
    requirement = "I want any papers that are related to LLMs."
    checker = Checker(requirement=requirement)
    summarizer = PaperSummarizer(requirement=requirement)
    library = Library.load_default()
    library.add_url("https://rss.arxiv.org/rss/cs.LG+cs.CL")
    papers = cast(
        list[PaperAndSummary],
        library.get_papers(limit=limit, checker=checker, summarizer=summarizer),
    )

    match export_format:
        case "markdown":
            print("\n".join([p.to_markdown() for p in papers]))
        case _:
            pass


if __name__ == "__main__":
    main()
