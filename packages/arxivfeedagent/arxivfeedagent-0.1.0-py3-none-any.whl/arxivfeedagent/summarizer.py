from dataclasses import dataclass
import re

from arxivfeedagent.paper import Paper, PaperAndSummary

from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # required, but unused
)


@dataclass(frozen=True)
class PaperSummarizer:
    requirement: str

    def summarize(self, paper: Paper) -> PaperAndSummary:
        response = client.chat.completions.create(
            model="qwen3:4b",
            messages=[
                {
                    "role": "user",
                    "content": f"""I have the following requirements and a research paper which meets the requirements. Summarize the paepr with a focus on the provided requirements in one sentence. Do not say that the paper matches the requirement, just produce a summary about the paper.
                    Requirements: {self.requirement}
                    Paper:
                      Title: {paper.title}
                      Abstract: {paper.abstract}""",
                },
            ],
        )
        res_cont = response.choices[0].message.content
        res_cont = res_cont if res_cont else ""
        res_cont = re.sub(r"<think>.+<\/think>", "", res_cont, flags=re.DOTALL)
        res_cont = res_cont if res_cont else ""
        res_cont = res_cont.strip()

        return PaperAndSummary(paper=paper, summary=res_cont)


@dataclass(frozen=True)
class MultiSummarizer:
    def summarize(self, papers: list[PaperAndSummary]) -> str:
        paper_infos: str = "\n\n".join(
            [f"Title: {p.paper.title}\nSummary: {p.summary}" for p in papers]
        )
        response = client.chat.completions.create(
            model="qwen3:4b",
            messages=[
                {
                    "role": "user",
                    "content": f"""Summarize the following list of papers (title and short summary) in one sentence like headline of a news letter. Use a few words to describe each paper.

                    Papers:
                      {paper_infos}""",
                },
            ],
        )
        res_cont = response.choices[0].message.content
        res_cont = res_cont if res_cont else ""
        res_cont = re.sub(r"<think>.+<\/think>", "", res_cont, flags=re.DOTALL)
        res_cont = res_cont if res_cont else ""
        res_cont = res_cont.strip()

        return res_cont
