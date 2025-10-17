from dataclasses import dataclass
import feedparser

from arxivfeedagent.paper import Paper


@dataclass(frozen=True)
class FeedLoader:
    url: str

    def load(self) -> list[Paper]:
        entries = feedparser.parse(self.url).entries
        papers = [Paper.from_entry(entry) for entry in entries]
        return papers
