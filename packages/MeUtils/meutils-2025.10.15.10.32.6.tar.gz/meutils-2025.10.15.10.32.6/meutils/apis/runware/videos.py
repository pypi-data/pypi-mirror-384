#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : videos
# @Time         : 2025/10/13 13:46
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 


from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.llm.clients import AsyncClient
from meutils.notice.feishu import send_message_for_images
from meutils.io.files_utils import to_url, to_url_fal
from meutils.schemas.video_types import SoraVideoRequest, Video

from openai import APIStatusError

from meutils.apis.translator import deeplx


async def generate(request: SoraVideoRequest, api_key: str, base_url: Optional[str] = None):

    payload = [
        {
            "taskType": "videoInference",

            "taskUUID": str(uuid.uuid4()),


            "model": request.model,
            "positivePrompt": request.prompt,

            "includeCost": True,

        }
    ]

    payload[0]["width"], payload[0]["height"] = map(int, request.size.split("x"))

    # 图生
    if image := request.input_reference:
        if not image.startswith("http"):  # 转换为url
            image = await to_url_fal(image, content_type="image/png")

        payload[0]["frameImages"] = [{"inputImage": image}]

    logger.debug(bjson(payload))
    try:
        client = AsyncClient(base_url="https://api.runware.ai/v1", api_key=api_key, timeout=300)
        response = await client.post(
            "/",
            body=payload,
            cast_to=object
        )

        logger.debug(bjson(response))

    except APIStatusError as e:
        if (errors := e.response.json().get("errors")):
            logger.debug(bjson(errors))

        raise e



async def get_task(task_id):
    payload = [
        {
            "taskType": "getResponse",

            "taskUUID": task_id,

        }
    ]

    api_key = "Fk3Clsgcwc3faIvbsjDajGFATJLfaWpE"
    client = AsyncClient(base_url="https://api.runware.ai/v1", api_key=api_key, timeout=300)
    response = await client.post(
        "/",
        body=payload,
        cast_to=object
    )
    logger.debug(bjson(response))


from runware import Runware, IVideoInference, IGoogleProviderSettings, IFrameImage

if __name__ == '__main__':
    model = "openai:3@1"

    request = SoraVideoRequest(model=model)

    # arun(generate(request, api_key="Fk3Clsgcwc3faIvbsjDajGFATJLfaWpE"))


    arun(get_task("8a5a1c09-d0a5-4b1b-9b67-8943cacc935f"))

    # {
    #     "data": [
    #         {
    #             "taskType": "videoInference",
    #             "taskUUID": "8a5a1c09-d0a5-4b1b-9b67-8943cacc935f"
    #         }
    #     ]
    # }
