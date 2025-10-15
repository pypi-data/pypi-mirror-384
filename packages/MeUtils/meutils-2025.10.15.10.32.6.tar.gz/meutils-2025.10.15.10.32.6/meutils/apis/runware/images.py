#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : runware
# @Time         : 2025/10/9 16:34
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : https://runware.ai/models#video-featured

from meutils.pipe import *
from meutils.db.redis_db import redis_aclient
from meutils.llm.clients import AsyncClient
from meutils.notice.feishu import send_message_for_images
from meutils.io.files_utils import to_url, to_url_fal
from meutils.schemas.image_types import ImageRequest, RecraftImageRequest, ImagesResponse
from openai import APIStatusError

from meutils.apis.translator import deeplx


async def generate(request: ImageRequest, api_key: str, base_url: Optional[str] = None):
    payload = {
        **request.model_dump(exclude_none=True, exclude={"extra_fields", "aspect_ratio"}),
        **(request.extra_fields or {})
    }
    payload = [
        {
            "taskUUID": str(uuid.uuid4()),
            "taskType": "imageInference",
            "model": request.model,
            "positivePrompt": await deeplx.llm_translate(request.prompt),

            "numberResults": request.n,
            # "width": 1024,
            # "height": 1024,  # aspect_ratio todo 如何映射到 width/height
            "aspectRatio": request.aspect_ratio,

            "includeCost": True,
            "outputFormat": "PNG",
            "outputType": [
                "URL"
            ],

            **payload
        }
    ]

    if image_urls := request.image_urls:
        if not image_urls[0].startswith("http"):  # 转换为url
            image_urls = await to_url_fal(image_urls, content_type="image/png")

        payload[0]["referenceImages"] = image_urls

    if aspect_ratio_mapping := await redis_aclient.get(f"runware:{request.model}"):
        aspect_ratio_mapping = aspect_ratio_mapping.decode()
        logger.debug(aspect_ratio_mapping)

        aspect_ratio_mapping = json.loads(aspect_ratio_mapping)

        size = aspect_ratio_mapping.get(request.aspect_ratio, "1024x1024")
        if size and isinstance(size, list):
            size = size[-1]  # 取最高清

        payload[0]["width"], payload[0]["height"] = map(int, size.split("x"))

    logger.debug(bjson(payload))
    try:
        client = AsyncClient(base_url="https://api.runware.ai/v1", api_key=api_key, timeout=300)
        response = await client.post(
            "/",
            body=payload,
            cast_to=object
        )

        if data := response.get("data"):
            for d in data:
                d["url"] = d["imageURL"]

            payload[0]["data"] = data
            send_message_for_images(payload[0], title=__name__)  # 存图片

            return ImagesResponse(data=data)
        elif errors := response.get("errors"):
            raise Exception(errors[0].get("message"))

    except APIStatusError as e:
        if (errors := e.response.json().get("errors")):
            logger.debug(bjson(errors))
            if (
                    any(i.lower() in str(errors).lower() for i in {"width/height", "unsupportedDimensions"})
                    and not await redis_aclient.get(f"runware:{request.model}")
                    and (v := errors[0].get("allowedValues", ""))

            ):
                logger.debug(v)
                await redis_aclient.set(f"runware:{request.model}", json.dumps(v), ex=30 * 24 * 3600)

        raise e


if __name__ == '__main__':
    model = "google:2@1"
    # model = "google:2@3"
    # model = "bfl:3@1"
    # model = "bfl:4@1"

    # model = "google:4@1" # gemini

    # prompt = "一个裸体少女"
    prompt = "a cat"
    request = ImageRequest(model=model, prompt=prompt, aspect_ratio="1:2")

    data = {
        "model": model,
        "prompt": "Turn this person into a character figure, the character sits on a Siberian tiger, the tiger's hair is black and yellow, the tiger's hair is very dense. Behind it, place a PS5 box with the character’s image and the game's name \"Black Myth: Zhong Kui\" printed on it, and a computer showing the Blender modeling process on its screen. In front of the box, add a round plastic base with the character figure standing on it. This figurine is made of PVC, and set the scene indoors.   (flux-kontext-pro)",
        "negative_prompt": "",
        "n": 1,
        "response_format": "url",
        "size": "1152x2048",
        "num_inference_steps": 20,
        "seed": None,
        "aspect_ratio": "9:16"
    }
    request = ImageRequest(**data)
    # request = ImageRequest(
    #     model=model,
    #     prompt="将鸭子放在女人的t恤上",
    #     aspect_ratio="1:1",
    #     image=[
    #         "https://v3.fal.media/files/penguin/XoW0qavfF-ahg-jX4BMyL_image.webp",
    #         "https://v3.fal.media/files/tiger/bml6YA7DWJXOigadvxk75_image.webp"
    #     ]
    # )
    #
    # data = {"model": model, "prompt": "Generate a professional studio portrait of a Asian woman. ", "image": [],
    #  "size": "16:9", "aspect_ratio": "16:911"}
    data = {"model": model, "prompt": "Generate a professional studio portrait of a Asian woman. ", "image": [],
            "size": "4x3000"}
    request = ImageRequest(**data)


    logger.debug(request)
    arun(generate(request, api_key="Fk3Clsgcwc3faIvbsjDajGFATJLfaWpE"))
