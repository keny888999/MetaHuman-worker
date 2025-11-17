from agno.agent import Agent, RunOutput
from agno.media import Image
from agno.models.dashscope import DashScope
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools import Toolkit
from rich.pretty import pprint
import json
import httpx
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager

db = SqliteDb(db_file="agno.db")


def get_top_hackernews_stories(num_stories: int = 10) -> str:
    """
    Use this function to get top stories from Hacker News.

    Args:
        num_stories (int): Number of stories to return. Defaults to 10.

    Returns:
        str: JSON string of top stories.
    """

    # Fetch top story IDs
    response = httpx.get('https://hacker-news.firebaseio.com/v0/topstories.json')
    story_ids = response.json()

    # Fetch story details
    stories = []
    for story_id in story_ids[:num_stories]:
        story_response = httpx.get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json')
        story = story_response.json()
        if "text" in story:
            story.pop("text", None)
        stories.append(story)
    return json.dumps(stories)


class compute(Toolkit):
    def add(a, b):
        """Use this function to compute a+b.

        Args:
            a(int): the number of a.            
            b(int): the number of v.            

        Returns:
            The result of a+b.
        """
        return a + b


metrics = None


def post_hook(run_output: RunOutput):
    global metrics

    pprint({
        "input_tokens": run_output.metrics.input_tokens,
        "output_tokens": run_output.metrics.output_tokens,
        "total_tokens": run_output.metrics.total_tokens
    })

    if metrics is None:
        metrics = run_output.metrics
    else:
        metrics += run_output.metrics


model = DashScope(
    id="qwen-flash-2025-07-28",
    enable_thinking=False,
    api_key="sk-8d6fadb22aeb4d03b23e403909a781f8",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")


# db.clear_memories()

memory_manager = MemoryManager(
    db=db,
    # Select the model used for memory creation and updates. If unset, the default model of the Agent is used.
    # model=model,
    # You can also provide additional instructions
    # additional_instructions="Don't store the user's real name",
)

agent = Agent(
    model=model,
    db=db,
    add_history_to_context=True,
    num_history_runs=3,
    # memory_manager=memory_manager,
    # enable_user_memories=True,

    instructions=["Always include sources"],  # "Search web using tools"
    # tools=[compute(), DuckDuckGoTools()],
    post_hooks=[post_hook]
)

# image_url = "https://img.alicdn.com/imgextra/i1/O1CN01gDEY8M1W114Hi3XcN_!!6000000002727-0-tps-1024-406.jpg"

if False:
    agent.print_response(
        # "How do I solve this problem? Please think through each step carefully.",
        # images=[Image(url=image_url)],
        "记住这个信息:丽丽是一个学生，擅长画画和跳舞,这是一个不可以变更的事实",
        stream=True,
        user_id="8880",
        session_id="123"
    )

while True:
    user_input = input("请输入文字（输入'exit'退出）: ")
    if user_input.lower() == 'exit':
        print("程序退出")
        break
    else:
        agent.print_response(
            user_input,
            stream=True,
            user_id="8880",
            session_id="123"
        )


pprint({
    "input_tokens": metrics.input_tokens,
    "output_tokens": metrics.output_tokens,
    "total_tokens": metrics.total_tokens
})
