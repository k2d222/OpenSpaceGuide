async def exec_navigate(lua, target):
    await lua.pathnavigation.flyTo(target)
    # await lua.setPropertyValue("NavigationHandler.OrbitalNavigator.Aim", "")
    # await lua.setPropertyValue("NavigationHandler.OrbitalNavigator.Anchor", target)
    # await lua.setPropertyValue("NavigationHandler.OrbitalNavigator.RetargetAnchor", None)


async def exec_rotate(lua, pan, tilt):
    # XXX: openspace's rotation seems broken (doubled degrees)
    await lua.navigation.addGlobalRotation(pan / 2.0, tilt / 2.0)


async def exec_zoom(lua, z_truck):
    # distance = await lua.navigation.distanceToFocus()
    await lua.navigation.addTruckMovement(0, z_truck)


async def exec_date(lua, date):
    time = f"{date}T00:00:00"
    await lua.time.setTime(time)


async def exec_speed(lua, speed):
    await lua.time.setDeltaTime(speed)


async def exec_toggle(lua, node):
    prop = f"Scene.{node}.Renderable.Enabled"
    state = await lua.propertyValue(prop)
    await lua.setPropertyValueSingle(prop, not state)


async def exec_explain(lua, explain):
    pass


async def exec_clarify(lua, clarify):
    pass


async def exec_pause(lua):
    lua.time.togglePause()


async def openspace_visible_targets(os, lua):
    nodes = await lua.sceneGraphNodes()

    def node_visible_predicate(n):
        return f'["{n}"] = openspace.hasProperty("Scene.{n}.Renderable.Enabled") and openspace.propertyValue("Scene.{n}.Renderable.Enabled")'

    script = f'return {{ {','.join(node_visible_predicate(n) for n in nodes.values())} }}'

    nodes_visible = (await os.executeLuaScript(script))['1']
    return [n for n in nodes_visible if nodes_visible[n]]


async def openspace_date(lua):
    return (await lua.time.UTC())[:10]


async def openspace_target(lua):
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



