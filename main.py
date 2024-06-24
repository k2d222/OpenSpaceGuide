from openai import OpenAI as OpenAI_
import asyncio
import openspace
import json
import speech_recognition as sr
import argparse
import keyboard
import collections
from persistence import Persistent
from openspace_commands import *


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


# caching openai calls to save network time and money
OpenAI = Persistent(OpenAI_) if args.persistent else OpenAI_


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



class AI:
    def __init__(self, location, date, targets):
        self.start_location = location
        self.start_date = date
        self.targets = targets

        self.client = OpenAI()
        self.assistant = self.client.beta.assistants.retrieve(args.assistant)
        self.thread = self.client.beta.threads.create()
        self.system_prompt = self._sys_prompt()

    def _sys_prompt(self):
        return f'''
You are a computer system that drives OpenSpace, an astrophysics visualization software. You are issued prompts by the user and reply JSON objects to execute the prompted task.
It is important that you follow exactly the text format given in the examples below. the JSON object must always be valid.

valid JSON keys are:
 - "navigate": go to a target, e.g. "Earth", "ISS", "Sun", etc.
 - "zoom": move camera closer or further.
 - "pan": rotate the camera horizontally (azimuth) around the current target, in degrees.
 - "tilt": rotate the camera vertically (elevation) around the current target, in degrees.
 - "explain": give an explanation to the question.
 - "date": change the simulation date in the format "YYYY-MM-DD".
 - "speed": set the simulation speed, in seconds per second.
 - "toggle": enable/disable rendering of a target.
 - "clarify": the request was not understood, ask for clarification.
 - "chain": specify a chain of actions to accomplish.

initial date is "{self.start_date}".
initial speed is 1.
initial target for "navigate" is "{self.start_location}".
valid targets for "navigate" are: {', '.join(f'"{t}"' for t in self.targets)}

Examples Below

<user> "Go to the Moon"
<system> {{ "navigate": "Moon" }}
<user> "What is the diameter of the Moon?"
<system> {{ "explain": "The diameter of the Moon is 3474 kilometers." }}
<user> "Can you move the camera further?"
<system> {{ "zoom": -10.0 }}
<user> "Can you go to January 5th, 2013?"
<system> {{ "date": "2013-01-05" }}
<user> "Can I see the back side of the Moon?"
<system> {{ "pan": 180 }}
<user> "Can I see the north pole?"
<system> {{ "tilt": 90 }}
<user> "Hide the Sun"
<system> {{ "toggle": "Sun" }}
<user> "What is the Blasuzrd"
<system> {{ "clarify": "Sorry, I don't know what is a 'Blasuzrd'" }}
<user> "Increase the simulation speed"
<system> {{ "speed": 10 }}
<user> "Go to the sun, then set the date to February 10, 2020."
<system> {{ "chain": [ {{ "navigate": "Sun" }}, {{ "date": "2020-02-10" }} ] }}
<user> "Go to the north pole of the earth"
<system> {{ "chain": [ {{ "navigate": "Earth" }}, {{ "tilt": 90 }} ] }}
'''

    async def query(self, prompt, os):
        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role='user',
            content=prompt
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
        )

        print('run: ')
        print(run)

        if run.status == 'requires_action' and run.required_action.type == 'submit_tool_outputs':
            calls = run.required_action.submit_tool_outputs.tool_calls
            print('calls:')
            print(calls)
            outputs = []

            for call in calls:
                fn = call.function.name.replace('_', '.')
                args = json.loads(call.function.arguments)
                lua_script = f'{fn}'
                print(f'script: {lua_script} args: {args}')
                res = await os.executeLuaFunction(fn, args.keys(), True)
                print(f'res: {res}')
                outputs.append({ 'tool_call_id': call.id, 'output': res })

            run = self.client.beta.threads.runs.submit_tool_outputs(
              thread_id=self.thread.id,
              run_id=run.id,
              tool_outputs=outputs
            )

            print('run2:')
            print(run)

        print('steps: ')
        print(steps)
        # return steps.data


def keyboard_prompt():
    print('prompt> ', end='')
    return input()


#--------------------------------MAIN FUNCTION--------------------------------
os = openspace.Api(args.address, args.port)
disconnect = asyncio.Event()
speech = SpeechToText() if args.input == 'speech' else None


async def main(os):
    lua = await os.singleReturnLibrary()
    targets = args.targets or await openspace_visible_targets(os, lua)
    initial_date = await openspace_date(lua)
    initial_target = await openspace_target(lua)
    print(f'initial date: {initial_date}')
    print(f'initial target: {initial_target}')
    print(f'found {len(targets)} targets')

    ai = AI(initial_target, initial_date, targets)

    if args.text_widget:
        await openspace_create_text_widget(lua)

    while True:
        prompt = speech.listen() if args.input == 'speech' else keyboard_prompt()
        await show_user_prompt(lua, prompt)
        resp = await ai.query(prompt, os)
        print(f'json: {resp}')

        if isinstance(resp, list):
            for req in resp:
                await exec_request(lua, req)
        else:
            await exec_request(lua, resp)


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

loop = asyncio.new_event_loop()
loop.run_until_complete(mainLoop())
loop.run_forever()
