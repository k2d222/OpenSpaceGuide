from openai import OpenAI
import asyncio
import openspace
import json
import speech_recognition as sr

r = sr.Recognizer()
with sr.Microphone() as source:
    print("Listening to the microphone")
    audio = r.listen(source, phrase_time_limit=3)

try:
    print("Whisper thinks you said " + r.recognize_whisper(audio, language="english"))
except sr.UnknownValueError:
    print("Whisper could not understand audio")
except sr.RequestError as e:
    print(f"Could not request results from Whisper; {e}")

exit(0)

ai = OpenAI()

OPENSPACE_ADDRESS = 'localhost'
OPENSPACE_PORT = 4681
# Create an OpenSpaceApi instance with the OpenSpace address and port
os = openspace.Api(OPENSPACE_ADDRESS, OPENSPACE_PORT)

# This event is used to cleanly exit the event loop.
disconnect = asyncio.Event()


async def query_ai(query):
    # return { "navigate": "Sun" }

    system_prompt = '''
You are a computer system that drives OpenSpace, an astrophysics visualization software. You are issued prompts by the user and reply JSON objects to execute the prompted task.
It is important that you follow exactly the text format given in the examples below. the JSON object must always be valid.

valid json keys are:
 - "navigate": go to a named entity, e.g. Earth, ISS, Sun, Milky Way, etc.
 - "zoom": move camera closer or further.
 - "explain": give an explanation to the question.
 
Examples Below

<user> "Go to the Moon"
<system> { "navigate": "Moon" }
<user> "What is the diameter of the Moon?"
<system> { "explain": "The diameter of the Moon is 3474 kilometers." }
<user> "Can you move the camera further?"
<system> { "zoom": -1 }
'''

    user_prompt = f'<user> "{query}"\n<system> '

    completion = ai.chat.completions.create(
      model="gpt-3.5-turbo",
      response_format={ "type": "json_object" },
      messages=[
        {"role": "system", "content": system_prompt },
        {"role": "user", "content": user_prompt }
      ]
    )

    msg = completion.choices[0].message.content
    print(f'msg: {msg}')
    msg_json = json.loads(msg)
    return msg_json


async def exec_navigate(lua, target):
    await lua.pathnavigation.flyTo(target)
    # await lua.setPropertyValue("NavigationHandler.OrbitalNavigator.Aim", "")
    # await lua.setPropertyValue("NavigationHandler.OrbitalNavigator.Anchor", target)
    # await lua.setPropertyValue("NavigationHandler.OrbitalNavigator.RetargetAnchor", None)


async def exec_explain(lua, exp):
    pass

#--------------------------------MAIN FUNCTION--------------------------------
async def main(lua):
    while True:
        query = input()
        resp = await query_ai(query)
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
    lua = await os.singleReturnLibrary()

    # Create a main task to run all function logic
    asyncio.create_task(main(lua), name="Main")


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
