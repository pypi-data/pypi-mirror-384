from dotenv import load_dotenv
load_dotenv()

import unittest
unittest.TestLoader.sortTestMethodsUsing = None

import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
