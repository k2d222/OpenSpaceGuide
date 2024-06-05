from openai import OpenAI
import asyncio
import openspace
import json
import speech_recognition as sr

sr_rec = sr.Recognizer()

ai = None

OPENSPACE_ADDRESS = 'localhost'
OPENSPACE_PORT = 4681
# Create an OpenSpaceApi instance with the OpenSpace address and port
os = openspace.Api(OPENSPACE_ADDRESS, OPENSPACE_PORT)

# This event is used to cleanly exit the event loop.
disconnect = asyncio.Event()


class AI:
    def __init__(self, targets):
        self.client = OpenAI()
        self.targets = targets
        self.conversation_history = []
        self.max_history = 10  # must be even (1 question + 1 answer)
        self.system_prompt = f'''
            You are a computer system that drives OpenSpace, an astrophysics visualization software. You are issued prompts by the user and reply JSON objects to execute the prompted task.
            It is important that you follow exactly the text format given in the examples below. the JSON object must always be valid.

            valid JSON keys are:
             - "navigate": go to a named entity, e.g. Earth, ISS, Sun, Milky Way, etc.
             - "zoom": move camera closer or further.
             - "explain": give an explanation to the question.

            valid values for "navigate" are: {', '.join(f'"{t}"' for t in targets)}
 
            Examples Below

            <user> "Go to the Moon"
            <system> {{ "navigate": "Moon" }}
            <user> "What is the diameter of the Moon?"
            <system> {{ "explain": "The diameter of the Moon is 3474 kilometers." }}
            <user> "Can you move the camera further?"
            <system> {{ "zoom": -1 }}
        '''

    def query(self, prompt):
        # return { "navigate": "Sun" }

        user_prompt = f'<user> "{prompt}"\n<system> '
        self.conversation_history.append({ "role": "user", "content": user_prompt })

        completion = self.client.chat.completions.create(
          model="gpt-3.5-turbo",
          response_format={ "type": "json_object" },
          messages=[
            {"role": "system", "content": self.system_prompt },
            *self.conversation_history,
          ]
        )

        msg = completion.choices[0].message.content
        self.conversation_history.append({ "role": "assistant", "content": msg })
        self.conversation_history = self.conversation_history[-self.max_history:]
        msg_json = json.loads(msg)
        return msg_json


def speech_prompt():
    with sr.Microphone() as source:
        print("Listening to the microphone")
        audio = sr_rec.listen(source)

        text = sr_rec.recognize_whisper_api(audio)
        print(f"whisper: '{text}'")

        return text


async def exec_navigate(lua, target):
    await lua.pathnavigation.flyTo(target)
    # await lua.setPropertyValue("NavigationHandler.OrbitalNavigator.Aim", "")
    # await lua.setPropertyValue("NavigationHandler.OrbitalNavigator.Anchor", target)
    # await lua.setPropertyValue("NavigationHandler.OrbitalNavigator.RetargetAnchor", None)


async def exec_explain(lua, exp):
    pass


async def openspace_targets(os, lua):
    nodes = await lua.sceneGraphNodes()

    def node_visible_predicate(n):
        return f'["{n}"] = openspace.hasProperty("Scene.{n}.Renderable.Enabled") and openspace.propertyValue("Scene.{n}.Renderable.Enabled")'

    script = f'return {{ {','.join(node_visible_predicate(n) for n in nodes.values())} }}'

    nodes_visible = (await os.executeLuaScript(script))['1']
    return [n for n in nodes_visible if nodes_visible[n]]


#--------------------------------MAIN FUNCTION--------------------------------
async def main(os):
    lua = await os.singleReturnLibrary()
    targets = await openspace_targets(os, lua)
    print(f'found {len(targets)} targets')
    ai = AI(targets)

    while True:
        prompt = input()
        # prompt = speech_prompt()
        resp = ai.query(prompt)
        print(f'json: {resp}')

        if 'navigate' in resp:
            target = resp['navigate']
            print(f"--> navigating to {target}")
            await exec_navigate(lua, target)
        elif 'explain' in resp:
            exp = resp['explain']
            print(f"--> explain: {exp}")
            await exec_explain(lua, exp)

    disconnect.set()


async def onConnect():
    PASSWORD = ''
    res = await os.authenticate(PASSWORD)
    if not res[1] == 'authorized':
        disconnect.set()
        return

    print("Connected to OpenSpace")

    # Create a main task to run all function logic
    asyncio.create_task(main(os), name="Main")


def onDisconnect():
    if asyncio.get_event_loop().is_running():
        asyncio.get_event_loop().stop()
    print("Disconnected from OpenSpace")
    # If connection failed this helps the program exit gracefully
    disconnect.set()


os.onConnect(onConnect)
os.onDisconnect(onDisconnect)


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
