#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : chat
# @Time         : 2025/8/19 13:22
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : qwen-image
import httpx
import shortuuid
from openai import AsyncOpenAI, OpenAI, AsyncStream

from meutils.pipe import *
from meutils.decorators.retry import retrying
from meutils.oss.ali_oss import qwenai_upload
from meutils.io.files_utils import to_bytes, guess_mime_type, to_url
from meutils.caches import rcache
from meutils.apis.images.edits import ImageProcess, edit_image

from meutils.llm.openai_utils import to_openai_params, create_chat_completion_chunk, token_encoder, oneturn2multiturn

from meutils.config_utils.lark_utils import get_next_token_for_polling
from meutils.schemas.openai_types import chat_completion, chat_completion_chunk, CompletionRequest, CompletionUsage, \
    ChatCompletion, Choice, ChatCompletionMessage, ChatCompletionChunk
from meutils.schemas.image_types import ImageRequest, ImagesResponse

from fake_useragent import UserAgent

ua = UserAgent()

FEISHU_URL = "https://xchatllm.feishu.cn/sheets/Bmjtst2f6hfMqFttbhLcdfRJnNf?sheet=PP1PGr"

base_url = "https://chat.qwen.ai/api/v2"
DEFAUL_MODEL = "qwen3-max"

thinking_budget_mapping = {
    "low": 1000,
    "medium": 8000,
    "high": 24000
}

COOKIE = """
cna=KP9DIEqqyjUCATrw/+LjJV8F; _bl_uid=LXmp28z7dwezpmyejeXL9wh6U1Rb; cnaui=310cbdaf-3754-461c-a3ff-9ec8005329c9; aui=310cbdaf-3754-461c-a3ff-9ec8005329c9; sca=43897cb0; _gcl_au=1.1.106229673.1748312382.56762171.1748482542.1748482541; xlly_s=1; x-ap=ap-southeast-1; acw_tc=0a03e53917509898782217414e520e5edfcdef667dcbd83b767c0ce464fad4; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjMxMGNiZGFmLTM3NTQtNDYxYy1hM2ZmLTllYzgwMDUzMjljOSIsImxhc3RfcGFzc3dvcmRfY2hhbmdlIjoxNzUwNjYwODczLCJleHAiOjE3NTM1ODE4ODV9.Npy24ubI717JmdSWMrodWSvVRHENgbJ7Knd-Yf158YE; atpsida=705b922fe336ee0d63fcc329_1750989888_2; SERVERID=e8c2af088c314df080fffe7d0976a96b|1750989892|1750910540; tfstk=gGtsWsqG4IKUeosYhNDUAMIBJRIbcvoz6-6vEKEaHGIOG-O2eZBabAYXRIR16hSOMpQpNtDMbtpTlWd2wNEAWA4XAOWy0FJtS6Ef3IDMbiQvps65XZYNg15fcKASLbor4dvGmGlra0WjM37NqSBAMS5d9TSfBJ35KivGmihEsEHyxdAMR0lwBiHCvt6uMiBYDMHC3TXOD1QY9yBR9iIAktIdpOX0DlCYWv9dtOsAMIQtdMChHfD7Ftg1sdMwtHJ00Jm2p6ZYDH6Ki1p6F9XBAwQOwwCQD9-CCN1JBhJB9QBXy3_MwXzN6UTkNTRZvlOWBCTRyhFKOivePI6WXYU5GCvpbwKt3zXhmFLRXnG76ppJBeLJBXzCdepwAw--No_MJCYllnlEqG8yUnbJXcNlTaXXNGLI9lOR4urPNGl0lJ_uc91rdva0oJN5AmdFjVAhW9X18vMQ6EbOK96ndva0oNBhCOMId5Lc.; isg=BNfX7gH7c3OJX_gfCBykQ2rtZk0hHKt-YCofVCkEq6YJWPSaPe8Dz9o-uvjGsIP2; ssxmod_itna=iqGxRDuQqWqxgDUxeKYI5q=xBDeMDWK07DzxC5750CDmxjKidKDUGQq7qdOamuu9XYkRGGm01DBL4qbDnqD80DQeDvYxk0K4MUPhDwpaW8YRw3Mz7GGb48aIzZGzY=0DgSdfOLpmxbD884rDYoDCqDSDxD99OdD4+3Dt4DIDAYDDxDWCeDBBWriDGpdhmbQVqmqvi2dxi3i3mPiDit8xi5bZendVL4zvDDlKPGf3WPt5xGnD0jmxhpdx038aoODzLiDbxEY698DtkHqPOK=MlTiRUXxAkDb9RG=Y2U3iA4G3DhkCXU3QBhxCqM2eeQmkeNzCwkjw/006DDAY2DlqTWweL04MKBeHhY5om5NUwYHuFiieQ0=/R=9iO9xTBhND4KF4dvyqz0/toqlqlzGDD; ssxmod_itna2=iqGxRDuQqWqxgDUxeKYI5q=xBDeMDWK07DzxC5750CDmxjKidKDUGQq7qdOamuu9XYkRGGmibDG85+YNY=exGa3Y64u5DBwiW7r++DxFqCdl=l77NQwckyAaCG64hkCOjO1pkcMRBdqj70N7nk=e94KEQYUxlf+2Dw=ViA+XKDde0uGS+eXgFkQqzYWe0Dd4oGbUj8L4QY4og345X2DjKDNOfQRgfeIKVRFQjqR098dBUrQsXBNQZcG1oBFAp4xkLYHl+W3OQW9ybPF4sML3t1tPX2T4DmCqKL+jN1XX94xpyA6k9+sgyBFY4zXOq7dHOuO3Gd3lidwdrk=8dNrOdrYQo33fobVS=MRF7nNQBC5d3kBbYdwtoxNBKmBiXoTfOTzOp3MT=ODXhxfO16Tta4vSW=ubtkEGgeQ/gKOwsVjmKDEY0NZ+ee7xlitvWmBbtk7ma7x1PinxtbitdadtYQOqG5AFEZbFxiSE6rDky7jiatQ0Fe7z6uDmYx4z5MGxMA5iDY7DtSLfNUYxU44D
""".strip()


class Completions(object):
    def __init__(self, api_key: Optional[str] = None, default_model: Optional[str] = None):
        self.api_key = api_key
        self.default_model = default_model or DEFAUL_MODEL


    @retrying()
    async def generate(self, request: ImageRequest, **kwargs):

        if request.image and not request.image[-1].startswith("http"):
            request.image = await to_url(request.image, content_type="image/png")

        if isinstance(request.image, str):
            request.image = [request.image]

        _ = CompletionRequest(
            model="qwen-image",
            stream=True,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": request.prompt},

                        *[
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": url
                                }
                            }
                            for url in request.image or []
                        ]
                    ],

                }
            ],
            size=request.aspect_ratio
        )

        async for chunk in await self.create(_):
            logger.debug(chunk)
            if chunk.choices and (url := chunk.choices[0].delta.content):
                if request.response_format == "oss_url":
                    request = ImageProcess(model="clarity", image=url)
                    url = await edit_image(request)

                return ImagesResponse(data=[{"url": url}])

        raise Exception("qwen-image 生成失败, 请重试")

    async def create(self, request: CompletionRequest, cookie: Optional[str] = None, ):
        api_key = self.api_key or await get_next_token_for_polling(feishu_url=FEISHU_URL, from_redis=True)

        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            default_headers={
                'User-Agent': ua.random,
                'Cookie': cookie or COOKIE
            },

        )

        chat_id = await self.create_new_chat()

        if request.model.endswith("-thinking") or request.enable_thinking:
            request.model = request.model.removesuffix("-thinking")
            thinking_enabled = True
            thinking_budget = request.thinking_budget or 1024
        else:
            thinking_enabled = False
            thinking_budget = request.thinking_budget

        model = request.model

        payload = {
            "chat_id": chat_id,
            "stream": request.stream,
            "incremental_output": True,
            "chat_mode": "normal",
            "model": model,
            "messages": [  # todo 多轮对话： 多轮转单轮
                {
                    "role": "user",
                    # "content": request.last_user_content,

                    "content": oneturn2multiturn(request.messages),

                    "user_action": "chat",
                    "files": [],
                    # "models": [
                    #     DEFAUL_MODEL
                    # ],
                    "chat_type": "t2t",
                    # "chat_type": "t2i",
                    # "chat_type": "image_edit",

                    "sub_chat_type": "t2t",

                    "feature_config": {
                        "thinking_enabled": thinking_enabled,
                        "output_schema": "phase",
                        "thinking_budget": thinking_budget,
                    },
                    # "extra": {
                    #     "meta": {
                    #         "subChatType": "t2t"
                    #     }
                    # }
                }
            ],
            "size": request.size if hasattr(request, "size") else "1:1"
        }

        if request.model.startswith("qwen-image"):
            payload['model'] = self.default_model
            payload["messages"][0]["chat_type"] = "t2i"
            payload["messages"][0]["sub_chat_type"] = "t2i"
            payload["messages"][0]["content"] = request.last_user_content

            # logger.debug(request.last_urls)
            if image_urls := request.last_urls.get("image_url"):
                payload["messages"][0]["chat_type"] = "image_edit"
                payload["messages"][0]["files"] = [
                    {
                        "type": "image",
                        "name": "example.png",
                        "file_type": "image",
                        "showType": "image",
                        "file_class": "vision",
                        "url": url  # todo 阿里对象存储
                    }
                    for url in image_urls
                ]
        elif request.model.endswith("-search"):
            request.model = request.model.removesuffix("-search")
            payload["messages"][0]["chat_type"] = "search"
            payload["messages"][0]["feature_config"]["search_version"] = "v2"
            payload["messages"][0]["sub_chat_type"] = "search"
            payload["messages"][0]["extra"]["meta"]["subChatType"] = "search"

        elif request.last_urls:  # 通用

            files = []
            for k in ["image_url", "audio_url", "video_url", "file_url"]:
                files += [
                    {
                        # "name": "name",
                        "type": k.removesuffix("_url"),
                        "url": url
                    }
                    for url in request.last_urls.get(k, [])
                ]

            payload["messages"][0]["files"] = files

        data = to_openai_params(payload)
        data["stream"] = True  # 强制开启 stream
        logger.debug(bjson(data))
        response = await self.client.chat.completions.create(**data, extra_query={"chat_id": chat_id})
        # response = self.do_response(response)

        if isinstance(response, AsyncStream):  # todo
            if request.model.startswith("qwen-image"):  # 中转后 测试首行是否报错
                return response

            return self.stream(request, response)

            # web_search 模式下, 会返回 phase="web_search" 的 delta
            # async def gen():
            #     chunk: ChatCompletionChunk
            #     async for chunk in response:  # ChatCompletionChunk
            #         logger.debug(chunk)
            #         if chunk.choices and (delta := chunk.choices[0].delta):
            #             if hasattr(delta, "phase") and (phase := delta.phase):  # phase =="web_search"
            #                 if hasattr(delta, "extra") and (info := delta.extra.get("web_search_info")):  # todo 其他 info
            #                     logger.debug(bjson(info))
            #
            # return await gen()

        # else:

        # # 缺少 reasoning_content 与 usage
        # logger.debug(response)
        #
        # if hasattr(response, "data") and (choices := response.data.get("choices")):
        #     response = response.model_construct(id=chat_id, choices=choices)
        #     logger.debug(response)
        # # “”“    completion_tokens = len(token_encoder.encode(str(response.choices[0].message.content)))
        # # AttributeError: 'str' object has no attribute 'choices'”""
        # prompt_tokens = len(token_encoder.encode(str(request.messages)))
        # completion_tokens = len(token_encoder.encode(str(response.choices[0].message.content)))
        #
        # # logger.debug(len(token_encoder.encode(str(response.choices[0].message.content))))
        #
        # usage = {
        #     "prompt_tokens": prompt_tokens,
        #     "completion_tokens": completion_tokens,
        #     "total_tokens": prompt_tokens + completion_tokens
        # }
        # response.usage = usage
        # return response

    async def stream(self, request, chunks):
        idx = 0
        nostream_content = ""
        nostream_reasoning_content = ""
        chunk = None
        usage = None
        chunk_id = f"chatcmpl-{shortuuid.random()}"

        async for chunk in chunks:
            # logger.debug(chunk) # search 结构不一样

            if not chunk.choices: continue

            content = chunk.choices[0].delta.content or ""
            if hasattr(chunk.choices[0].delta, "phase") and chunk.choices[0].delta.phase == "think":
                chunk.choices[0].delta.content = ""
                chunk.choices[0].delta.reasoning_content = content
                nostream_reasoning_content += content

            # logger.debug(chunk.choices[0].delta.content)
            nostream_content += chunk.choices[0].delta.content
            usage = chunk.usage or usage
            chunk.id = chunk_id

            if hasattr(chunk.choices[0].delta, "status") and chunk.choices[0].delta.status == "finished":
                chunk.choices[0].finish_reason = "stop"

            if request.stream:
                yield chunk

            idx += 1
            if idx == request.max_tokens:
                break

        if not request.stream:
            logger.debug(chunk)
            if hasattr(usage, "output_tokens_details"):
                usage.completion_tokens_details = usage.output_tokens_details
            if hasattr(usage, "input_tokens"):
                usage.prompt_tokens = usage.input_tokens
            if hasattr(usage, "output_tokens"):
                usage.completion_tokens = usage.output_tokens

            chat_completion.usage = usage
            chat_completion.choices[0].message.content = nostream_content
            chat_completion.choices[0].message.reasoning_content = nostream_reasoning_content

            yield chat_completion

    async def create_new_chat(self):
        payload = {
            "title": "新建对话",
            "models": [self.default_model],
            "chat_mode": "normal",
            "chat_type": "t2i",
            "timestamp": time.time() * 1000 // 1
        }
        response = await self.client.post('/chats/new', body=payload, cast_to=object)

        if chat_id := response['data'].get('id'):
            return chat_id
        else:
            logger.error(response)
            raise Exception("insufficient")


    @property
    def models(self):
        headers = {
            'User-Agent': ua.random,
            # 'Cookie': cookie or COOKIE
        }
        response = httpx.get("https://chat.qwen.ai/api/models", headers=headers)
        # logger.debug(response.text)

        data = response.json()["data"]
        #
        return [m["id"] for m in data]


if __name__ == '__main__':
    # print(Completions().models)
    token = """
    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjMxMGNiZGFmLTM3NTQtNDYxYy1hM2ZmLTllYzgwMDUzMjljOSIsImxhc3RfcGFzc3dvcmRfY2hhbmdlIjoxNzUwNjYwODczLCJleHAiOjE3NjA1MTMwMTR9.qOB1oMB_Z1zA7hejAjlBYOsI1Q1WDEJjMG3zTeeRCq4
     """.strip()

    # content = [
    #     {"type": "text", "text": "南京今天天气"},
    # ]
    #
    # content = [
    #     {"type": "text", "text": "a dog"},
    # ]
    #
    # content = [
    #     {"type": "text", "text": "a dog"},
    # ]

    content = [
        {"type": "text", "text": """
        # 身份
你是一个高精度的【视频内容转录员】。

# 核心任务
你的唯一任务是：以【时间戳】为单位，逐字逐句、逐个动作地记录视频中的所有视听信息。你必须像法庭书记员一样，做到100%的客观和精确。

# 输出格式 (必须严格遵守)
使用以下格式，为每个独立事件创建新的一行：
[HH:MM:SS] [类别]: [内容]

# “类别”包括：
- **[台词]**: 记录人物说的每一句话。如果能识别说话人，格式为 `[台词-人名]`. 如果不能，格式为 `[台词-男/女]`.
- **[画面]**: 描述场景、环境、人物外貌、表情和关键物品。
- **[动作]**: 描述人物的所有具体动作。
- **[音效]**: 记录所有非对话的声音，如(敲门声), (汽车鸣笛)。

# 绝对禁止
- 禁止进行任何总结、分析或评论。
- 禁止使用任何剧本格式。
- 禁止省略任何细节。
- 你的所有输出都必须是简体中文。
        """},
        {"type": "video_url", "video_url": {
            "url": "https://qwen-webui-prod.oss-accelerate.aliyuncs.com/310cbdaf-3754-461c-a3ff-9ec8005329c9/b813de59-c7d6-4c58-9f0d-0a8a283ca41b_1%20%282%29.mp4?x-oss-security-token=CAISzwJ1q6Ft5B2yfSjIr5nsCI7Qt5tAhKunaFGDilI6QLpppIPvoDz2IHhMenlvAewetvg2nGBT7fkflrN6SJtIXleCZtF94plR7QKoZ73Zocur7LAJksVu3r1e%2F0WpsvXJasDVEfn%2FGJ70GX2m%2BwZ3xbzlD0bAO3WuLZyOj7N%2Bc90TRXPWRDFaBdBQVGAAwY1gQhm3D%2Fu2NQPwiWf9FVdhvhEG6Vly8qOi2MaRmHG85R%2FYsrZN%2BNmgecP%2FNpE3bMwiCYyPsbYoJvab4kl58ANX8ap6tqtA9Arcs8uVa1sruE3ebbqLqoE3dFMgPvhhQPEZtpj6krhxuanUj5Q8SO%2FTtljJOs62Z%2FdDoKOscIvBXr6yRaJvreicfPqb1%2FQnHpLpLAPa1a4HqTQbIAuUI3bCJL8U1AEJVr6kzHkNhYYrssUUla4R5TGOWbJLJyr%2BHN3xuRqAAZjIuAflHa2njQWXjxvTYM83wepsCAQnJw79bVYI%2FDbZWdln2va6OOjJNxwvdbV42mujTd5qofC%2Bb39J0q5fX6w%2FRanfViZwgN0Bd9tLLLzrjMl02ZLDtq14O5yVY2Z0qyJGw7AAy01Hsjn8BmYaWX19LEfLWe6hrq%2FjSnA9JCUfIAA%3D&x-oss-date=20251008T091359Z&x-oss-expires=300&x-oss-signature-version=OSS4-HMAC-SHA256&x-oss-credential=STS.NZYC4dZDa3iLjw2nRoL5EKFDB%2F20251008%2Fap-southeast-1%2Foss%2Faliyun_v4_request&x-oss-signature=96ae6ce2d0e12e73cc709a1855b772ca2dc9f63be10399fbcdfd4d63f8e53e8d"}}
    ]

    # content = [
    #     {"type": "text", "text": "a dog" * 10000 + "\n\n一共多少个词"},
    # ]

    # content = [
    #     {"type": "text", "text": "一句话总结"},
    #
    #     {
    #         "type": "video_url",
    #         "video_url": {
    #             "url": "https://lmdbk.com/5.mp4",
    #         }
    #     },
    #
    # ]
    # ['qwen3-max', 'qwen3-vl-plus', 'qwen3-coder-plus', 'qwen3-omni-flash']

    request = CompletionRequest(
        # model="qwen3-235b-a22b",
        # model="qwen3-max",

        model="qwen3-vl-plus",
        # model="qwen3-coder-plus",
        # model="qwen3-omni-flash",
        # model="qwen3-235b-a22b-search",

        # model="qwen-image",


        messages=[
            {
                "role": "user",
                "content": content,
            },

            # {
            #     "role": "user",
            #     "content": "hi",
            # },

            # {
            #     "role": "user",
            #     "content": "1+1",
            # },
            # {
            #     "role": "assistant",
            #     "content": "3",
            # },
            # {
            #     "role": "user",
            #     "content": "错了",
            # }
        ],
        # stream=True,

        # enable_thinking=True,

        size="1:1"

    )

    logger.debug(request.last_urls)


    # async def main():
    #     response = await Completions(api_key=token).create(request)
    #
    #     if isinstance(response, AsyncStream):
    #         async for chunk in response:
    #             logger.debug(chunk)
    #     elif isinstance(response, AsyncGenerator):
    #         async for chunk in response:
    #             logger.debug(chunk)
    #     else:
    #         logger.debug(response)
    #
    #
    # arun(main())

    request = ImageRequest(
        model="qwen-image",
        prompt="把小鸭子放在女人的T恤上面",

        # image="https://v3.fal.media/files/penguin/XoW0qavfF-ahg-jX4BMyL_image.webp",
        # image=[
        #     "https://v3.fal.media/files/penguin/XoW0qavfF-ahg-jX4BMyL_image.webp",
        #     "https://v3.fal.media/files/tiger/bml6YA7DWJXOigadvxk75_image.webp"
        # ]
    )
    arun(Completions(api_key=token).generate(request))

#