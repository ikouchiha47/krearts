import asyncio

from dotenv import load_dotenv

from cinema.agents.filmmaker.crew import Enhancer, ScriptWriter, ScriptWriterSchema
from cinema.context import DirectorsContext
from cinema.pipeline.script_writing import ScriptWritingPipeline
from cinema.providers.shared import MediaLib
from cinema.registry import GeminiHerd, OpenAiHerd


async def run_script_writer():
    medialib = MediaLib(
        image_urls=[
            "https://images.unsplash.com/photo-1657223144998-e5aa4fa2db7c?ixlib=rb-4.1.0&q=85&fm=jpg&crop=entropy&cs=srgb&dl=robert-torres-oDrBOovU5A8-unsplash.jpg&w=640",
        ]
    )

    ctx = DirectorsContext(
        # llmstore=OpenAiHerd,
        llmstore=GeminiHerd,
        debug=True,
    )
    script_writer = ScriptWriter(ctx, medialib)
    enhancer = Enhancer(ctx)

    pipeline = ScriptWritingPipeline(
        script_writer,
        enhancer,
    )

    inputs = ScriptWriterSchema(
        images=medialib.images(),
        script=(
            "A versatile headphone, can be worn by office goers, "
            "gym, running, evening walks. Use graphical match cuts to "
            "make the engage the users, and a punchier storyline."
        ),
        characters=[],
        examples=ScriptWriter.load_examples(),
    )

    await pipeline.run(inputs)


if __name__ == "__main__":
    load_dotenv()

    asyncio.run(run_script_writer())
