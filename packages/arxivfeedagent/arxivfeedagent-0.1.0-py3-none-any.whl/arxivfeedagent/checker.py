from dataclasses import dataclass
from openai import OpenAI
import openai
from pydantic import BaseModel

from arxivfeedagent.paper import Paper


class IsRelevant(BaseModel):
    is_relevant: bool


@dataclass(frozen=True)
class Checker:
    requirement: str

    def is_paper_relevant(self, paper: Paper) -> bool:
        client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        try:
            completion = client.beta.chat.completions.parse(
                temperature=0,
                model="qwen3:4b",
                messages=[
                    {
                        "role": "user",
                        "content": f"""
                        Check if the following paper matches the requirements:

                        Requirements: {self.requirement}

                        Paper:
                          Title: {paper.title}
                          Abstract: {paper.abstract}
                    """,
                    }
                ],
                response_format=IsRelevant,
            )

            response = completion.choices[0].message
            if response.parsed:
                return response.parsed.is_relevant
            elif response.refusal:
                print(response.refusal)
            return False
        except Exception as e:
            if type(e) is openai.LengthFinishReasonError:
                print("Too many tokens: ", e)
            else:
                print(e)
            return False
