from reader import make_reader, Reader
from arxivfeedagent.checker import Checker
from arxivfeedagent.paper import Paper, PaperAndSummary
from dataclasses import dataclass

from arxivfeedagent.summarizer import PaperSummarizer


@dataclass(frozen=True)
class Library:
    reader: Reader

    @classmethod
    def load_default(cls) -> "Library":
        reader = make_reader("debug.sqlite")
        return cls(reader)

    def add_url(self, url: str) -> None:
        self.reader.add_feed(url, exist_ok=True)
        self.reader.update_feeds()

    def get_papers(
        self,
        limit: int = 25,
        checker: Checker | None = None,
        summarizer: PaperSummarizer | None = None,
    ) -> list[Paper] | list[PaperAndSummary]:
        self.reader.update_feeds()
        entries = self.reader.get_entries(limit=limit, read=False)
        papers = []
        for entry in entries:
            self.reader.mark_entry_as_read(entry)
            paper = Paper.from_entry(entry)

            if checker and summarizer:
                is_relevant = checker.is_paper_relevant(paper)
                if is_relevant:
                    paper_and_summary = summarizer.summarize(paper)
                    self.reader.set_tag(entry, "is_relevant", True)
                    self.reader.set_tag(
                        entry, "generated_summary", paper_and_summary.summary
                    )
                    papers.append(paper_and_summary)
                    print(entry.id)
            else:
                papers.append(Paper.from_entry(entry))
        return papers
