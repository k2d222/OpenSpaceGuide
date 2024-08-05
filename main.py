from openai import AsyncOpenAI as AsyncOpenAI_, AsyncAssistantEventHandler
import asyncio
import openspace
import json
import speech_recognition as sr
import argparse
import keyboard
import collections
from persistence import Persistent
import openspace_commands as oscmd
import functools


def parse_args():
    parser = argparse.ArgumentParser(prog='OpenSpaceGuide', description='steer OpenSpace with ChatGPT')
    parser.add_argument('--address', default='localhost', help='OpenSpace server address')
    parser.add_argument('--port', type=int, default=4681, help='OpenSpace server port')
    parser.add_argument('--password', default='', help='OpenSpace server password')
    parser.add_argument('--input', choices=['speech', 'keyboard'], help='use keyboard or text-to-speech input')
    parser.add_argument('--targets', help='comma-separated list of OpenSpace navigation targets that the AI should be aware of (default is all visible targets)')
    parser.add_argument('--trigger', help='trigger keyboard key to start/stop listening')
    parser.add_argument('--text-widget', action='store_true', help='use a ScreenSpaceText widget in OpenSpace for explanations')
    parser.add_argument('--microphone', type=int, help='microphone index to use (see printed available microphones)')
    parser.add_argument('--assistant', type=str, help='OpenAI assistant ID')
    parser.add_argument('--persistent', action='store_true', help='cache identical OpenAI API calls')
    args = parser.parse_args()
    return args


args = parse_args()
print('args:', args)

loop = asyncio.new_event_loop()

# caching openai calls to save network time and money
AsyncOpenAI = Persistent(AsyncOpenAI_) if args.persistent else AsyncOpenAI_


class SpeechToText:
    def __init__(self):
        mics = sr.Microphone.list_microphone_names()
        print(f'available microphone(s):\n - {'\n - '.join(mics)}')

        self.sr_rec = sr.Recognizer()
        self.sr_mic = sr.Microphone(args.microphone)

        print('calibrating microphone')
        self.calibrate()


    def calibrate(self):
        with self.sr_mic as source:
            self.sr_rec.adjust_for_ambient_noise(source)


    def _audio_triggered(self, timeout):
        with self.sr_mic as source:
            print(f'waiting for trigger ({args.trigger})')
            keyboard.wait(args.trigger)

            seconds_per_buffer = float(source.CHUNK) / source.SAMPLE_RATE
            elapsed_time = 0

            frames = collections.deque()

            print('listening to the microphone')
            while elapsed_time < timeout and keyboard.is_pressed(args.trigger):
                buffer = source.stream.read(source.CHUNK)
                if len(buffer) == 0:
                    break
                frames.append(buffer)
                elapsed_time += seconds_per_buffer

            frame_data = b''.join(frames)

            return sr.AudioData(frame_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
            # return self.sr_rec.record(source, 2)


    def _audio_untriggered(self, timeout):
        with self.sr_mic as source:
            print("listening to the microphone")
            return self.sr_rec.listen(source, timeout)


    def listen(self, timeout=10):
        audio = self._audio_triggered(timeout) if args.trigger is not None else self._audio_untriggered(timeout)
        print("processing audio")
        text = self.sr_rec.recognize_whisper_api(audio)
        print(f"whisper: '{text}'")
        return text


class AIEventHandler(AsyncAssistantEventHandler):
    def __init__(self, ai, os, lua):
        super().__init__()
        self.ai = ai
        self.os = os
        self.lua = lua
        self.text = ''

    async def on_event(self, evt):
        if evt.event == 'thread.run.requires_action':
            await self.handle_requires_action(evt.data)


    async def on_text_created(self, text) -> None:
        print("assistant> ", end="", flush=True)


    async def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)
        await oscmd.show_text(self.lua, snapshot.value)


    async def on_text_done(self, text):
        print('')
        await oscmd.show_text(self.lua, text.value)


    async def handle_requires_action(self, data):
        outputs = []

        for tool_call in data.required_action.submit_tool_outputs.tool_calls:
            fn = 'openspace.' + tool_call.function.name.replace('_', '.')
            args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
            print(f'assistant> [calling {tool_call.function.name} with args {args}]')
            res = await os.executeLuaFunction(fn, list(args.values()), True)
            res = json.dumps(res)
            print(f' -> call res: {res}')
            outputs.append({
                'tool_call_id': tool_call.id,
                'output': res
            })

        async with self.ai.client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.ai.thread.id,
            run_id=self.current_run.id,
            tool_outputs=outputs,
            event_handler=AIEventHandler(self.ai, self.os, self.lua),
        ) as stream:
            await stream.until_done()


class AI:
    def __init__(self, location, date, targets):
        self.start_location = location
        self.start_date = date
        self.targets = targets

    async def init(self):
        self.client = AsyncOpenAI()
        self.assistant = await self.client.beta.assistants.retrieve(args.assistant)
        self.thread = await self.client.beta.threads.create()

    async def run_query(self, prompt, os, lua):
        await self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role='user',
            content=prompt
        )

        async with self.client.beta.threads.runs.stream(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            event_handler=AIEventHandler(self, os, lua),
        ) as stream:
            await stream.until_done()
            print('stream done')


async def keyboard_prompt():
    print('prompt> ', end='')
    return await loop.run_in_executor(None, input)


#--------------------------------MAIN FUNCTION--------------------------------
os = openspace.Api(args.address, args.port)
disconnect = asyncio.Event()
speech = SpeechToText() if args.input == 'speech' else None


async def main(os):
    lua = await os.singleReturnLibrary()
    targets = args.targets or await oscmd.visible_targets(os, lua)
    initial_date = await oscmd.date(lua)
    initial_target = await oscmd.target(lua)
    print(f'initial date: {initial_date}')
    print(f'initial target: {initial_target}')
    print(f'found {len(targets)} targets')

    ai = AI(initial_target, initial_date, targets)
    await ai.init()

    if args.text_widget:
        await oscmd.create_text_widget(lua)

    while True:
        prompt = speech.listen() if args.input == 'speech' else await keyboard_prompt()
        await oscmd.show_user_prompt(lua, prompt)
        await ai.run_query(prompt, os, lua)

    disconnect.set()


async def on_connect():
    res = await os.authenticate(args.password)
    if not res[1] == 'authorized':
        disconnect.set()
        return

    print("Connected to OpenSpace")

    # Create a main task to run all function logic
    asyncio.create_task(main(os), name="Main")


def on_disconnect():
    if asyncio.get_event_loop().is_running():
        asyncio.get_event_loop().stop()
    print("Disconnected from OpenSpace")
    # If connection failed this helps the program exit gracefully
    disconnect.set()


os.onConnect(on_connect)
os.onDisconnect(on_disconnect)


# Main loop serves as an entry point to allow for authentication before running any other
# logic. This part can be skipped if no authentication is needed, reducing the overhead of
# creating multiple tasks before main() is run.
async def mainLoop():
    os.connect()
    # Wait for the disconnect event to be set
    await disconnect.wait()
    os.disconnect()

loop.run_until_complete(mainLoop())
print('done')
