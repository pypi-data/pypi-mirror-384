import asyncio
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from pydantic import BaseModel
from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools
from agno.agent import Agent
from baiduSearchTool import BaiduSearchTools


class searchResult(BaseModel):
    OrderNum: int
    title: str
    url: str
    abstract: str

class searchAllResult(BaseModel):
    OrderNum: int
    title: str
    url: str
    abstract: str
    content: str

class rankResult(BaseModel):
    URL: str
    rank: int

littleAgent1 = Agent(
    tools=[GoogleSearchTools()],
    model=OpenAILike(id="qwen-flash", api_key="sk-24af89ee61384059bde783db1cd6818f", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"),
    description="You are a search agent that helps users find the most relevant information using Baidu.",
    instructions=[
        "Given a research result, respond with a list which includes the URL and relative rank.",
    ],
    output_schema=rankResult,
    markdown=False,
)

littleAgent2 = Agent(
    tools=[GoogleSearchTools()],
    model=OpenAILike(id="qwen-flash"),
    description="You are a search agent that helps users find the most relevant information using Baidu.",
    instructions=[
        "Given a research result, respond with a list which includes the URL and relative rank.",
    ],
    output_schema=rankResult,
    markdown=False,
)

littleAgent3 = Agent(
    tools=[GoogleSearchTools()],
    model=OpenAILike(id="qwen-flash"),
    description="You are a search agent that helps users find the most relevant information using Baidu.",
    instructions=[
        "Given a research result, respond with a list which includes the URL and relative rank.",
    ],
    output_schema=rankResult,
    markdown=False,
)

biggerAgent = Agent(
    tools=[GoogleSearchTools()],
    model=OpenAILike(id="qwen-plus"),
    markdown=False,
)

searcher = BaiduSearchTools()

async def run_agent(agent, query):
    """异步运行Agent的搜索任务"""
    loop = asyncio.get_event_loop()
    # 使用to_thread将同步的agent.run包装成异步
    result = await loop.run_in_executor(None, agent.run, query)
    return result

async def run_all_agents(query: str):
    """并发运行三个Agent"""
    # 使用gather并发执行
    results = await asyncio.gather(
        run_agent(littleAgent1, query),
        run_agent(littleAgent2, query),
        run_agent(littleAgent3, query)
    )
    return results

def search(query: str, max_results: int = 15, language: str = "zh") -> str:
    """Execute Baidu search and return results

    Args:
        query (str): Search keyword
        max_results (int, optional): Maximum number of results to return, default 5
        language (str, optional): Search language, default Chinese

    Returns:
        str: A JSON formatted string containing the search results.
    """
    results = searcher.baidu_search(query=query, max_results=max_results, language=language)
    section1 = results[0:max_results//3]
    section2 = results[max_results//3:max_results*2//3]
    section3 = results[max_results*2//3:max_results]
    
    return results

if __name__ == "__main__":
    # print(searcher.baidu_search("What is the capital of France?"))
    # print(searcher.fetch_page("https://en.wikipedia.org/wiki/France"))
    # littleAgent1.run(searcher.baidu_search("What is the capital of France?"))

    from typing import List

    from agno.agent import Agent
    from agno.models.dashscope import DashScope
    from pydantic import BaseModel, Field


    class MovieScript(BaseModel):
        name: str = Field(..., description="Give a name to this movie")
        setting: str = Field(
            ..., description="Provide a nice setting for a blockbuster movie."
        )
        ending: str = Field(
            ...,
            description="Ending of the movie. If not available, provide a happy ending.",
        )
        genre: str = Field(
            ...,
            description="Genre of the movie. If not available, select action, thriller or romantic comedy.",
        )
        characters: List[str] = Field(..., description="Name of characters for this movie.")
        storyline: str = Field(
            ..., description="3 sentence storyline for the movie. Make it exciting!"
        )


    # Agent that returns a structured output
    structured_output_agent = Agent(
        model=DashScope(id="qwen-plus", api_key="sk-b5ee4168837640b1af2695fa72ab41c5"),
        description="You write movie scripts and return them as structured data.",
        output_schema=MovieScript,
    )

    structured_output_agent.print_response(
        "Create a movie script about llamas ruling the world. "
        "Return with: name (movie title), setting, ending, genre, "
        "characters (list of character names), and storyline (3 sentences)."
    )

        