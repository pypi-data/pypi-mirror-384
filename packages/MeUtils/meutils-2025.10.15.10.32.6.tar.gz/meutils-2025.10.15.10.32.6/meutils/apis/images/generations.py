#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : generations
# @Time         : 2025/6/11 17:06
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 统一收口 todo 硅基
import os

from meutils.pipe import *
from meutils.llm.clients import AsyncClient
from meutils.llm.openai_utils import to_openai_params
from meutils.io.files_utils import to_png, to_url_fal, to_url
from meutils.notice.feishu import send_message_for_images

from meutils.schemas.image_types import ImageRequest, RecraftImageRequest, ImagesResponse

from meutils.apis.fal.images import generate as fal_generate

from meutils.apis.gitee.image_to_3d import generate as image_to_3d_generate
from meutils.apis.gitee.openai_images import generate as gitee_images_generate
from meutils.apis.volcengine_apis.images import generate as volc_generate
from meutils.apis.images.recraft import generate as recraft_generate
from meutils.apis.jimeng.images import generate as jimeng_generate
# from meutils.apis.google.images import generate as google_generate

from meutils.apis.qwen.chat import Completions as QwenCompletions
from meutils.apis.google.chat import Completions as GoogleCompletions
from meutils.apis.google.images import openai_generate
from meutils.apis.ppio.images import generate as ppio_generate
from meutils.apis.runware.images import generate as runware_generate


async def generate(
        request: ImageRequest,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
):
    if len(str(request)) < 1024:
        logger.debug(request)

    if request.model.startswith("fal-ai"):  # 国外fal
        request.image = await to_url_fal(request.image, content_type="image/png")
        response = await fal_generate(request, api_key)

        # https://fal.media/files/panda/FlN5Gk0KnHe4AXU6Jeyvo_c5795dc52214423cb6465dae8eeaa1f0.png
        # https://s3ai.cn/fal/files/panda/FlN5Gk0KnHe4AXU6Jeyvo_c5795dc52214423cb6465dae8eeaa1f0.png

        #

        # """https://fal.media/files/b/rabbit/-Cvx3pnaB0p6p_RLXlfuo.png
        # """
        # 转存
        # if response.data and request.response_format == "oss_url":
        #     urls = [dict(image_data).get("url") for image_data in response.data]
        #     urls = await to_url(urls, filename=f"{shortuuid.random()}.png")
        #
        #     response.data = [{"url": url} for url in urls]
        #
        #     return response

        if response.data and request.response_format == "oss_url":
            urls = [
                f"""https://s3ai.cn/fal/files/panda/{Path(dict(image_data).get("url", "")).name}"""

                for image_data in response.data
            ]

            response.data = [{"url": url} for url in urls] + response.data

        send_message_for_images(response.data, title=__file__)

        return response

    if request.model.startswith(("recraft",)):
        request = RecraftImageRequest(**request.model_dump(exclude_none=True))
        return await recraft_generate(request)

    if request.model.startswith(
            ("jimeng", "seed", "seededit_v3.0", "byteedit_v2.0", "i2i_portrait_photo")):  # seededit seedream
        return await volc_generate(request, api_key)

    if request.model.startswith(("jimeng")):  # 即梦 逆向
        return await jimeng_generate(request)

    if request.model in {"Hunyuan3D-2", "Hi3DGen", "Step1X-3D"}:
        return await image_to_3d_generate(request, api_key)

    if request.model in {"Qwen-Image", "FLUX_1-Krea-dev"} and request.model.endswith(("lora",)):
        return await gitee_images_generate(request, api_key)

    if request.model.startswith("qwen-image"):
        return await QwenCompletions(api_key=api_key).generate(request)

    if request.model.startswith(("google/gemini", "gemini")):  # openrouter
        if "ppi" in base_url:
            if request.size == "auto": # 不兼容
                request.size = "1024x1024"

            return await ppio_generate(request, api_key, base_url)

        elif api_key.endswith("-openai"):
            api_key = api_key.removesuffix("-openai")
            return await openai_generate(request, base_url=base_url, api_key=api_key)
        else:
            return await GoogleCompletions(base_url=base_url, api_key=api_key).generate(request)  # 原生接口

    if request.model.startswith("runware") or all(i in request.model for i in {":", "@"}):
        return await runware_generate(request, api_key)

    # 其他
    data = {
        **request.model_dump(exclude_none=True, exclude={"extra_fields", "aspect_ratio"}),
        **(request.extra_fields or {})
    }
    request = ImageRequest(**data)
    if request.model.startswith("doubao"):
        base_url = base_url or os.getenv("VOLC_BASE_URL")
        api_key = api_key.split()[0]  # 一个号并发足够

        request.stream = False
        request.watermark = False
        if request.model.startswith("doubao-seedream-4"):
            if (
                    request.image
                    and not any(
                i in str(request.image).lower() for i in {".png", ".jpg", ".jpeg", "image/png", "image/jpeg"}
            )
            ):
                logger.debug(f"{request.model}: image 不是 png 或 jpeg 格式，转换为 png 格式")

                request.image = await to_png(request.image, response_format='b64')

            if request.n > 1:
                request.sequential_image_generation = "auto"
                request.sequential_image_generation_options = {
                    "max_images": request.n
                }
        elif request.image and isinstance(request.image, list):
            request.image = request.image[0]

        if "ppi" in base_url:  # 派欧 https://ppio.com/docs/models/reference-seedream4.0 images => image
            request.images = request.image

            data = to_openai_params(request)

            client = AsyncClient(api_key=api_key, base_url=base_url)
            response = await client.images.generate(**data)
            if images := response.model_dump(exclude_none=True).get("images"):
                response.data = [{"url": image} for image in images]
                return response
            raise Exception(f"生成图片失败: {response} \n\n{request}")

    data = to_openai_params(request)

    if len(str(data)) < 1024:
        logger.debug(bjson(data))

    client = AsyncClient(api_key=api_key, base_url=base_url)
    response = await client.images.generate(**data)
    return response


# "flux.1-krea-dev"

if __name__ == '__main__':
    # arun(generate(ImageRequest(model="flux", prompt="笑起来")))
    # arun(generate(ImageRequest(model="FLUX_1-Krea-dev", prompt="笑起来")))

    token = f"""{os.getenv("VOLC_ACCESSKEY")}|{os.getenv("VOLC_SECRETKEY")}"""
    # arun(generate(ImageRequest(model="seed", prompt="笑起来"), api_key=token))

    request = ImageRequest(model="doubao-seedream-4-0-250828", prompt="a dog", size="1K")

    request = ImageRequest(
        model="doubao-seedream-4-0-250828",
        prompt="将小鸭子放在t恤上,生成1:2比例图",
        size="1k",
        # image=[
        #     "https://v3.fal.media/files/penguin/XoW0qavfF-ahg-jX4BMyL_image.webp",
        #     "https://v3.fal.media/files/tiger/bml6YA7DWJXOigadvxk75_image.webp"
        # ]
    )

    request = ImageRequest(
        **{"model": "doubao-seedream-4-0-250828", "prompt": "a cat", "n": 2, "size": "1024x1024",
           "response_format": "url"}

    )

    # todo: tokens 4096 1张

    # 组图
    # request = ImageRequest(
    #     model="doubao-seedream-4-0-250828",
    #     prompt="参考这个LOGO，做一套户外运动品牌视觉设计，品牌名称为GREEN，包括包装袋、帽子、纸盒、手环、挂绳等。绿色视觉主色调，趣味、简约现代风格",
    #     image="https://ark-project.tos-cn-beijing.volces.com/doc_image/seedream4_imageToimages.png",
    #     n=3
    # )

    # arun(generate(request, api_key=os.getenv("FFIRE_API_KEY"), base_url=os.getenv("FFIRE_BASE_URL")))  # +"-29494"

    # print(not any(i in str(request.image) for i in {".png", ".jpeg", "image/png", "image/jpeg"}))

    api_key = "sk_fRr6ieXTMfym7Q6cnbj0YBlB1QsE74G8ygqIE2AyGz0"
    base_url = "http://all.chatfire.cn/ppinfra/v1"

    arun(generate(request, api_key=api_key, base_url=base_url))
