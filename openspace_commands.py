import textwrap

def asciify(text):
    return text.replace('°', 'deg')

def _wrap(text):
    text = asciify(text)
    lines = text.splitlines()
    wrapped = '\n'.join([textwrap.fill(line, width=70) for line in lines])
    return wrapped.ljust(70, ' ')


async def show_text(lua, text):
    wrapped = _wrap(text)
    if await lua.hasProperty("ScreenSpace.OpenSpaceGuide.Text"):
        await lua.setPropertyValueSingle("ScreenSpace.OpenSpaceGuide.Text", wrapped)


async def show_user_prompt(lua, text):
    wrapped = _wrap(text)
    if await lua.hasProperty("ScreenSpace.OpenSpaceGuide_user.Text"):
        await lua.setPropertyValueSingle("ScreenSpace.OpenSpaceGuide_user.Text", wrapped)

async def exec_navigate(lua, target):
    await show_text(lua, f'Navigating to {target}')
    await lua.pathnavigation.flyTo(target)


async def exec_rotate(lua, pan, tilt):
    # XXX: openspace's rotation seems broken (doubled degrees)
    await show_text(lua, f'Rotating by ({pan}deg,{tilt}deg)')
    await lua.navigation.addGlobalRotation(pan / 2.0, tilt / 2.0)


async def exec_zoom(lua, z_truck):
    # distance = await lua.navigation.distanceToFocus()
    await show_text(lua, f'{"de" if z_truck < 0 else ""}zooming')
    await lua.navigation.addTruckMovement(0, z_truck)


async def exec_date(lua, date):
    await show_text(lua, f'Setting the date to {date}')
    time = f"{date}T00:00:00"
    await lua.time.setTime(time)


async def exec_speed(lua, speed):
    await show_text(lua, f'Setting the speed to {speed} seconds per second')
    await lua.time.setDeltaTime(speed)


async def exec_toggle(lua, node):
    await show_text(lua, f'Toggling {node}')
    prop = f"Scene.{node}.Renderable.Enabled"
    state = await lua.propertyValue(prop)
    await lua.setPropertyValueSingle(prop, not state)


async def create_text_widget(lua):
    if await lua.hasProperty("ScreenSpace.OpenSpaceGuide.Enabled"):
        print('OpenSpaceGuide ScreenSpaceRenderable already exists')
        await lua.setPropertyValueSingle("ScreenSpace.OpenSpaceGuide.Enabled", True)
    else:
        w1 = {
             "Identifier": "OpenSpaceGuide",
             "Name": "OpenSpaceGuide AI",
             "Type": "ScreenSpaceText",
             "UseRadiusAzimuthElevation": True,
             "RadiusAzimuthElevation": [1.0, -0.45, 0.1],
             "Text": "Chat-GPT explanation goes here."
        }
        w2 = {
             "Identifier": "OpenSpaceGuide_user",
             "Name": "OpenSpaceGuide User",
             "Type": "ScreenSpaceText",
             "UseRadiusAzimuthElevation": True,
             "RadiusAzimuthElevation": [1.0, 0.45, 0.1],
             "Text": "User prompt goes here."
        }
        await lua.addScreenSpaceRenderable(w1)
        await lua.addScreenSpaceRenderable(w2)
        print('created OpenSpaceGuide ScreenspaceRenderable')


async def exec_explain(lua, explain):
    await show_text(explain)


async def exec_clarify(lua, clarify):
    wrapped = '\n'.join(textwrap.wrap(clarify, width=70))
    await show_text(lua, wrapped)


async def exec_pause(lua):
    await show_text(lua, 'Toggling the simulation')
    lua.time.togglePause()


async def visible_targets(os, lua):
    nodes = await lua.sceneGraphNodes()

    def node_visible_predicate(n):
        return f'["{n}"] = openspace.hasProperty("Scene.{n}.Renderable.Enabled") and openspace.propertyValue("Scene.{n}.Renderable.Enabled")'

    script = f'return {{ {','.join(node_visible_predicate(n) for n in nodes.values())} }}'

    nodes_visible = (await os.executeLuaScript(script))['1']
    return [n for n in nodes_visible if nodes_visible[n]]


async def date(lua):
    return (await lua.time.UTC())[:10]


async def target(lua):
    return await lua.propertyValue('NavigationHandler.OrbitalNavigator.Anchor')


async def exec_request(lua, req):
    if 'navigate' in req:
        target = req['navigate']
        print(f"--> navigating to {target}")
        await exec_navigate(lua, target)
    elif 'pan' in req:
        pan = req['pan']
        print(f"--> panning {pan} degrees")
        await exec_rotate(lua, pan, 0)
    elif 'tilt' in req:
        tilt = req['tilt']
        print(f"--> tilting {tilt} degrees")
        await exec_rotate(lua, 0, tilt)
    elif 'zoom' in req:
        zoom = req['zoom']
        print(f"--> zoom {zoom}")
        await exec_zoom(lua, zoom)
    elif 'explain' in req:
        explain = req['explain']
        print(f"--> explain: {explain}")
        await exec_explain(lua, explain)
    elif 'date' in req:
        date = req['date']
        print(f"--> set date to {date}")
        await exec_date(lua, date)
    elif 'speed' in req:
        speed = req['speed']
        print(f"--> set speed to {speed} s/s")
        await exec_speed(lua, speed)
    elif 'toggle' in req:
        toggle = req['toggle']
        print(f"--> toggling visibility of {toggle}")
        await exec_toggle(lua, toggle)
    elif 'clarify' in req:
        clarify = req['clarify']
        print(f"--> clarify: {clarify}")
        await exec_clarify(lua, clarify)
    elif 'chain' in req:
        chain = req['chain']
        for r in chain:
            await exec_request(lua, r)
    else:
        print("--> unexpected ai request")



