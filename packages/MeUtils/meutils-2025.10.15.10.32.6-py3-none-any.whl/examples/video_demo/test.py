#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : test
# @Time         : 2025/10/13 17:51
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from runware import Runware, IVideoInference, IFrameImage, IMinimaxProviderSettings


async def main():
    runware = Runware(
        api_key=os.getenv("RUNWARE_API_KEY"),
    )
    await runware.connect()

    request = IVideoInference(
        positivePrompt="[Push in, Follow] A stylish woman walks down a Tokyo street filled with warm glowing neon and animated city signage. She wears a black leather jacket, a long red dress, and black boots, and carries a black purse. [Pan left] The street opens into a small plaza where street vendors sell steaming food under colorful awnings.",
        model="minimax:1@1",
        width=1366,  # Comment this to use i2v
        height=768,  # Comment this to use i2v
        duration=6,
        numberResults=1,
        includeCost=True,
        # frameImages=[  # Uncomment this to use t2v
        #     IFrameImage(
        #         inputImage= "https://raw.githubusercontent.com/adilentiq/test-images/refs/heads/main/video_inference/woman_city.png",
        #     ),
        # ]
        providerSettings=IMinimaxProviderSettings(
            promptOptimizer=True
        )
    )

    logger.debug(request)

    videos = await runware.videoInference(requestVideo=request)
    for video in videos:
        print(f"Video URL: {video.videoURL}")
        print(f"Cost: {video.cost}")
        print(f"Seed: {video.seed}")
        print(f"Status: {video.status}")


if __name__ == "__main__":
    asyncio.run(main())



"""
 curl --request POST \
  --url https://api.freepik.com/v1/ai/gemini-2-5-flash-image-preview \
  --header 'Content-Type: application/json' \
  --header 'x-freepik-api-key: FPSX3e216c84cc281f6f0f5f605334e22ad0' \
  --data '{
  "prompt": "A cat",
  "webhook_url": "https://openai-dev.chatfire.cn/v0"
}'


curl --request GET \
  --url https://api.freepik.com/v1/ai/gemini-2-5-flash-image-preview/0ef796f9-1efe-421a-935b-f1dfb4a3cb32 \
  --header 'x-freepik-api-key: FPSX3e216c84cc281f6f0f5f605334e22ad0'
"""