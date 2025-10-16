from agno.agent import Agent, RunOutput
from agno.models.dashscope import DashScope
import json
from pydantic import BaseModel


class SearchResult(BaseModel):
    rank: str
    title: str
    url: str

class SearchResultList(BaseModel):
    results: list[SearchResult]

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

# finder1.print_response("""查询主题：人工智能  {'title': '人工智能(AI) | 联合国', 'url': 'http://www.baidu.com/link?url=1hjoC4T3J1eexteKZyjPGKyFM0h7CcLqnGete2_rBy-7TYnhPrU1kKf9ddS_Ppx4YtFsG1HGXjCgBXzfM8mj62LUB957PKCCjLP3Jp2NGqS', 'abstract': '人工智能(AI) | 联合国\n\n\n\n\n\n\n\n\n\n例如,人工智能可以通过以下方式推动可持续发展目标的落实:在医疗保健领域提供诊断和预测分析工具(目标3);在农业领域提供作物监测和提高气候抗御力(目标2和15);在教育领域提供个性化学习服务(目标4);在人道主义应急领域提供危机状况测绘服务和促进物资发放。 \n\n\nUnited Nations\n\n\n\n\n\n\n\n\n\ue680\n播报\n\n\n\ue67d\n暂停', 'rank': '8'}
# {'title': '科普| 什么是AI?什么是人工智能?一次讲明白!', 'url': 'http://www.baidu.com/link?url=LyMDW5TRpt3MFVKDEZ-XXiaWTrRMQKMneUuYtJH1wlM-CXojSR4oa-1B9rrTwOz9TYaxrvQmDBx3WK6x8EtWgVyX4u8S5IUTqFl0Dwg_Sce-PpiEDcFZUTcIIxt9NPoijBcUKRtoBucS9vG84o1svzntAUmVdQlfGJ--FE4ehvriNlxz8oVkPJkNKH_W57x18jnQgLEJNBNq3KKjJ9Yq9CWfKbMVUXWRemjvtSGSAyLeSBw69V3vVXE9bDIzVMHtLX8BNzxmBzejW3z0iIw26q', 'abstract': '科普| 什么是AI?什么是人工智能?一次讲明白!\n\n2025年5月20日AI,即人工智能(Artificial Intelligence),是一种计算机程序,它可以模拟人类的思维过程,从而实现某些人类智能的任务。作为计算机科学的一个分支,AI致力于研究、开发模仿、扩展和增强人类智能的理论、方法、技术及应用系统。简而言之,AI的目标是理解和构建能够执行...\n\n\n4\n\n\n微信公众平台\n\n\n\n\n\n\ue680\n播报\n\n\n\ue67d\n暂停', 'rank': '9'}
# {'title': '人工智能(计算机科学的一个分支) - 百度百科', 'url': 'http://www.baidu.com/link?url=mI8d7oUZndadbWKda7iufZFdfmD6urmalJWgOdBBpMjN71jv2pxqU0utPvE_oE-k2lO81_aHP_5HbSFK9UxUPLonhv-JcjDWBg9JVoYZdqk1p5oVME0ufIvvuvTeYOgptAPcVdRkv1F8FP6xxEIrC_', 'abstract': '人工智能(计算机科学的一个分支) - 百度百科\n\n2021年7月15日人工智能的定义可以分为两部分,即“人工”和“智能”。“人工”比较好理解,争议性也不大。有时我们会要考虑什么是人力所能及制造的,或者人自身的智能程度有没有高到可以创造人工智能的地步,等等。但总的来说,“人工系统”就是通常意义下的人工系统。 \n\n\n百度百科', 'rank': '10'}
# {'title': '从信息社会迈向智能社会_中央网络安全和信息化委员会办公室', 'url': 'http://www.baidu.com/link?url=mI8d7oUZndadbWKda7iufZFdfmD6urmalJWgOdBBpMlkKqlZfZf_RSq4pfXhQMFrLTO2TF5lFmQcwxn0KmySFB6spZD-wVCZyaOrfyaNGbC', 'abstract': '从信息社会迈向智能社会_中央网络安全和信息化委员会办公室\n\n2020年2月18日人工智能(AI)是指在机器上实现类似乃至超越人类的感知、认知、行为等智能的系统。与人类历史上其他技术革命相比,人工智能对人类社会发展的影响可能位居前列。人类社会也正在由以计算机、通信、互联网、大数据等技术支撑的信息社会,迈向以人工智能为关键支撑的智能社会,人类生产生活以及世界发展格局将由此发生更加深刻的改变...\n\n\n中华人民共和国国家互联网信息办公室\n\n\n\n\n\n\ue680\n播报\n\n\n\ue67d\n暂停', 'rank': '11'}
# {'title': '人工智能包括什么?从算法到应用,一文读懂它背后的硬核科技!', 'url': 'http://www.baidu.com/link?url=LyMDW5TRpt3MFVKDEZ-XXeOJ9RQiEovKhlzF07-93-L9dND7ERDoApqf2kFkdZrMKbzrHWgSaa8crGL8Kwyt7krUx5gYWLjom0u__ZxNgbi', 'abstract': '人工智能包括什么?从算法到应用,一文读懂它背后的硬核科技!\n\n\n\n\n\n\n\n\n\n2025年6月20日一、人工智能的“大脑”：算法与模型 要说人工智能的核心，那一定是算法和模型。简单来说，算法就是一套解决问题的规则，而模型则是算法的“升级版”——它通过大量数据训练，学会像人一样思考和决策。比如你刷短视频时，系统总能精准推荐你感兴趣的内容，这背后就是推荐算法在起作用。根据百科的解释，人工智能的...\n\n\n心理咨询师卓洛伊\n\n\n\n\n\n\n\n\n\ue680\n播报\n\n\n\ue67d\n暂停', 'rank': '12'}"""
#                        , stream=True)

response: RunOutput = finder1.run("""查询主题：人工智能  {'title': '人工智能(AI) | 联合国', 'url': 'http://www.baidu.com/link?url=1hjoC4T3J1eexteKZyjPGKyFM0h7CcLqnGete2_rBy-7TYnhPrU1kKf9ddS_Ppx4YtFsG1HGXjCgBXzfM8mj62LUB957PKCCjLP3Jp2NGqS', 'abstract': '人工智能(AI) | 联合国\n\n\n\n\n\n\n\n\n\n例如,人工智能可以通过以下方式推动可持续发展目标的落实:在医疗保健领域提供诊断和预测分析工具(目标3);在农业领域提供作物监测和提高气候抗御力(目标2和15);在教育领域提供个性化学习服务(目标4);在人道主义应急领域提供危机状况测绘服务和促进物资发放。 \n\n\nUnited Nations\n\n\n\n\n\n\n\n\n\ue680\n播报\n\n\n\ue67d\n暂停', 'rank': '8'}
{'title': '科普| 什么是AI?什么是人工智能?一次讲明白!', 'url': 'http://www.baidu.com/link?url=LyMDW5TRpt3MFVKDEZ-XXiaWTrRMQKMneUuYtJH1wlM-CXojSR4oa-1B9rrTwOz9TYaxrvQmDBx3WK6x8EtWgVyX4u8S5IUTqFl0Dwg_Sce-PpiEDcFZUTcIIxt9NPoijBcUKRtoBucS9vG84o1svzntAUmVdQlfGJ--FE4ehvriNlxz8oVkPJkNKH_W57x18jnQgLEJNBNq3KKjJ9Yq9CWfKbMVUXWRemjvtSGSAyLeSBw69V3vVXE9bDIzVMHtLX8BNzxmBzejW3z0iIw26q', 'abstract': '科普| 什么是AI?什么是人工智能?一次讲明白!\n\n2025年5月20日AI,即人工智能(Artificial Intelligence),是一种计算机程序,它可以模拟人类的思维过程,从而实现某些人类智能的任务。作为计算机科学的一个分支,AI致力于研究、开发模仿、扩展和增强人类智能的理论、方法、技术及应用系统。简而言之,AI的目标是理解和构建能够执行...\n\n\n4\n\n\n微信公众平台\n\n\n\n\n\n\ue680\n播报\n\n\n\ue67d\n暂停', 'rank': '9'}
{'title': '人工智能(计算机科学的一个分支) - 百度百科', 'url': 'http://www.baidu.com/link?url=mI8d7oUZndadbWKda7iufZFdfmD6urmalJWgOdBBpMjN71jv2pxqU0utPvE_oE-k2lO81_aHP_5HbSFK9UxUPLonhv-JcjDWBg9JVoYZdqk1p5oVME0ufIvvuvTeYOgptAPcVdRkv1F8FP6xxEIrC_', 'abstract': '人工智能(计算机科学的一个分支) - 百度百科\n\n2021年7月15日人工智能的定义可以分为两部分,即“人工”和“智能”。“人工”比较好理解,争议性也不大。有时我们会要考虑什么是人力所能及制造的,或者人自身的智能程度有没有高到可以创造人工智能的地步,等等。但总的来说,“人工系统”就是通常意义下的人工系统。 \n\n\n百度百科', 'rank': '10'}
{'title': '从信息社会迈向智能社会_中央网络安全和信息化委员会办公室', 'url': 'http://www.baidu.com/link?url=mI8d7oUZndadbWKda7iufZFdfmD6urmalJWgOdBBpMlkKqlZfZf_RSq4pfXhQMFrLTO2TF5lFmQcwxn0KmySFB6spZD-wVCZyaOrfyaNGbC', 'abstract': '从信息社会迈向智能社会_中央网络安全和信息化委员会办公室\n\n2020年2月18日人工智能(AI)是指在机器上实现类似乃至超越人类的感知、认知、行为等智能的系统。与人类历史上其他技术革命相比,人工智能对人类社会发展的影响可能位居前列。人类社会也正在由以计算机、通信、互联网、大数据等技术支撑的信息社会,迈向以人工智能为关键支撑的智能社会,人类生产生活以及世界发展格局将由此发生更加深刻的改变...\n\n\n中华人民共和国国家互联网信息办公室\n\n\n\n\n\n\ue680\n播报\n\n\n\ue67d\n暂停', 'rank': '11'}
{'title': '人工智能包括什么?从算法到应用,一文读懂它背后的硬核科技!', 'url': 'http://www.baidu.com/link?url=LyMDW5TRpt3MFVKDEZ-XXeOJ9RQiEovKhlzF07-93-L9dND7ERDoApqf2kFkdZrMKbzrHWgSaa8crGL8Kwyt7krUx5gYWLjom0u__ZxNgbi', 'abstract': '人工智能包括什么?从算法到应用,一文读懂它背后的硬核科技!\n\n\n\n\n\n\n\n\n\n2025年6月20日一、人工智能的“大脑”：算法与模型 要说人工智能的核心，那一定是算法和模型。简单来说，算法就是一套解决问题的规则，而模型则是算法的“升级版”——它通过大量数据训练，学会像人一样思考和决策。比如你刷短视频时，系统总能精准推荐你感兴趣的内容，这背后就是推荐算法在起作用。根据百科的解释，人工智能的...\n\n\n心理咨询师卓洛伊\n\n\n\n\n\n\n\n\n\ue680\n播报\n\n\n\ue67d\n暂停', 'rank': '12'}"""
                       , stream=False)

# parsed = SearchResultList.model_validate_json(response.content)

results_json = json.dumps(response.content.model_dump(), ensure_ascii=False, indent=2)
print(results_json)