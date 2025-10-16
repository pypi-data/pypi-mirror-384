from time import time
from agno.agent import Agent
from agno.models.dashscope import DashScope
from agno.agent import Agent
from WebSearch.baiduSearchTool import BaiduSearchTools
import json
from pydantic import BaseModel
import asyncio

"""流程是首先使用百度搜索工具获取相关信息，然后将这些信息传递给不同的FinderAgent进行处理：将返回的内容根据相关度进行Rank的重排
    ，最后由主Agent整合各个子Agent的输出并且将所有的结果的75%通过FetchPage得到具体内容，最后将相关的信息进行整合得到
    自己整合的title、url、abstract，生成最终的回答。"""

class SearchResult(BaseModel):
    rank: str
    title: str
    url: str

class SearchResultList(BaseModel):
    results: list[SearchResult]

class AllResult(BaseModel):
    title: str
    url: str
    mostRelativeContent: str



manager = Agent(
    model=DashScope(id="qwen-plus"),
    description="Rerank the search results based on their relevance to the topic of the user input query.",
    instructions=[
        "You are a Summizer specialized in summarizing results based on their relevance to the topic of the user input query.",
        "Ensure that your ranking is clear and well-justified, explaining why certain results are ranked higher than others.",
        "Output as json format.",
    ],
    output_schema=AllResult,
    markdown=True
)

finder1 = Agent(
    model=DashScope(id="qwen-flash"),
    description="Rerank the search results based on their relevance to the topic of the user input query.",
    instructions=[
            "遍历提供的每条结果，结合标题、摘要和 url 判断与查询主题的相关度。所有输入的文章都要保留下来",
            "输出一个 JSON 对象，键名为 results，值为按相关度排序的数组。数组元素必须包含 rank、title、url 三个字段。",
            "rank 必须从 1 开始按相关度顺序递增，不得跳号或重复。",
            "示例输出: {\"results\": [{\"rank\": \"1\", \"title\": \"...\", \"url\": \"https://...\"}]}。",
    ],
    output_schema=SearchResultList,
    markdown=False,
)
finder2 = Agent(
    model=DashScope(id="qwen-flash"),
    description="Rerank the search results based on their relevance to the topic of the user input query.",
    instructions=[
            "遍历提供的每条结果，结合标题、摘要和 url 判断与查询主题的相关度。所有输入的文章都要保留下来",
            "输出一个 JSON 对象，键名为 results，值为按相关度排序的数组。数组元素必须包含 rank、title、url 三个字段。",
            "rank 必须从 1 开始按相关度顺序递增，不得跳号或重复。",
            "示例输出: {\"results\": [{\"rank\": \"1\", \"title\": \"...\", \"url\": \"https://...\"}]}。",
    ],
    output_schema=SearchResultList,
    markdown=False,
)
finder3 = Agent(
    model=DashScope(id="qwen-flash"),
    description="Rerank the search results based on their relevance to the topic of the user input query.",
    instructions=[
            "遍历提供的每条结果，结合标题、摘要和 url 判断与查询主题的相关度。所有输入的文章都要保留下来",
            "输出一个 JSON 对象，键名为 results，值为按相关度排序的数组。数组元素必须包含 rank、title、url 三个字段。",
            "rank 必须从 1 开始按相关度顺序递增，不得跳号或重复。",
            "示例输出: {\"results\": [{\"rank\": \"1\", \"title\": \"...\", \"url\": \"https://...\"}]}。",
    ],
    output_schema=SearchResultList,
    markdown=False,
)



async def filterAnswer(query, max_results, language="zh"):
    Tools = BaiduSearchTools()
    AllResult = json.loads(Tools.baidu_search(query, max_results*2, language))
    Result1 = AllResult[0:max_results//3]
    Result2 = AllResult[max_results//3:2*max_results//3]
    Result3 = AllResult[2*max_results//3:max_results]

    filter1 = await finder1.arun(
        f"User input query: {query}. {json.dumps(Result1, indent=2, ensure_ascii=False)}",
        stream=False
    )
    filter2 = await finder2.arun(
        f"User input query: {query}. {json.dumps(Result2, indent=2, ensure_ascii=False)}",
        stream=False
    )
    filter3 = await finder3.arun(
        f"User input query: {query}. {json.dumps(Result3, indent=2, ensure_ascii=False)}",
        stream=False
    )


    finalResult = []
    if filter1.content and isinstance(filter1.content.results, list):
        finalResult.extend(item.model_dump() for item in filter1.content.results)
    if filter2.content and isinstance(filter2.content.results, list):
        finalResult.extend(item.model_dump() for item in filter2.content.results)
    if filter3.content and isinstance(filter3.content.results, list):
        finalResult.extend(item.model_dump() for item in filter3.content.results)


    finalResult = [item for item in finalResult if str(item.get('rank')) not in ('3', '4')]
    for idx, item in enumerate(finalResult, start=1):
        item['rank'] = str(idx)
        item['Content'] = await Tools.async_fetch_page(item['url'])

    return finalResult




if __name__ == "__main__":
    beginTime = time()
    searchRank = asyncio.run(filterAnswer("人工智能", 6))
    endTime = time()
    print(f"程序执行耗时: {endTime - beginTime:.2f} 秒")


    # print(searchRank)
    # searchResults = manager.run(f"User input query: {userInputQuery}" + json.dumps(searchRank, ensure_ascii=False, indent=2), stream=False)
    # print(searchResults.content)

