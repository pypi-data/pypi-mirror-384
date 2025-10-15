from .cli import main
import asyncio


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError: 
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())