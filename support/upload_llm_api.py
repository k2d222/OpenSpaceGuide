from openai import OpenAI
import json
import argparse


client = OpenAI()

parser = argparse.ArgumentParser()
parser.add_argument('id', help='assistant ID')
parser.add_argument('input', help='input llm api JSON file')
args = parser.parse_args()

with open(args.input, 'r') as file:
    tools = json.load(file)


whitelist = [
    # 'openspace.absPath',
    # 'openspace.addCustomProperty',
    # 'openspace.addSceneGraphNode',
    # 'openspace.addScreenSpaceRenderable',
    # 'openspace.addTag',
    # 'openspace.addToPropertyValue',
    # 'openspace.appendToListProperty',
    # 'openspace.bindKey',
    # 'openspace.boundingSphere',
    # 'openspace.clearKey',
    # 'openspace.clearKeys',
    # 'openspace.configuration',
    # 'openspace.createDirectory',
    # 'openspace.createSingleColorImage',
    # 'openspace.directoryExists',
    # 'openspace.directoryForPath',
    # 'openspace.downloadFile',
    # 'openspace.dpiScaling',
    'openspace.fadeIn',
    'openspace.fadeOut',
    # 'openspace.fileExists',
    # 'openspace.getProperty', # deprecated
    # 'openspace.getPropertyValue', # deprecated
    # 'openspace.hasMission',
    'openspace.hasProperty',
    'openspace.hasSceneGraphNode',
    # 'openspace.interactionSphere',
    # 'openspace.invertBooleanProperty',
    # 'openspace.isMaster',
    # 'openspace.keyBindings',
    # 'openspace.layerServer',
    # 'openspace.loadJson',
    # 'openspace.loadMission',
    # 'openspace.makeIdentifier',
    # 'openspace.markInterestingNodes',
    # 'openspace.markInterestingTimes',
    # 'openspace.nodeByRenderableType',
    # 'openspace.printDebug',
    # 'openspace.printError',
    # 'openspace.printFatal',
    'openspace.printInfo',
    # 'openspace.printTrace',
    # 'openspace.printWarning',
    'openspace.property',
    'openspace.propertyValue',
    # 'openspace.readCSVFile',
    # 'openspace.readFile',
    # 'openspace.rebindKey',
    # 'openspace.removeCustomProperty',
    # 'openspace.removeInterestingNodes',
    # 'openspace.removeSceneGraphNode',
    # 'openspace.removeSceneGraphNodesFromRegex',
    # 'openspace.removeScreenSpaceRenderable',
    # 'openspace.removeTag',
    'openspace.resetCamera',
    # 'openspace.resetScreenshotNumber',
    # 'openspace.saveSettingsToProfile',
    'openspace.sceneGraphNodes',
    # 'openspace.screenSpaceRenderables',
    # 'openspace.setCurrentMission',
    # 'openspace.setDefaultDashboard',
    # 'openspace.setDefaultGuiSorting',
    # 'openspace.setParent',
    # 'openspace.setPathToken',
    # 'openspace.setPropertyValue',
    'openspace.setPropertyValueSingle',
    # 'openspace.setScreenshotFolder',
    'openspace.takeScreenshot',
    'openspace.toggleFade',
    # 'openspace.toggleShutdown',
    # 'openspace.unloadMission',
    # 'openspace.unzipFile',
    # 'openspace.version',
    # 'openspace.walkDirectory',
    # 'openspace.walkDirectoryFiles',
    # 'openspace.walkDirectoryFolders',
    # 'openspace.worldPosition',
    # 'openspace.worldRotation',
    # 'openspace.writeDocumentation',

    # 'openspace.action.action',
    # 'openspace.action.actions',
    # 'openspace.action.hasAction',
    # 'openspace.action.registerAction',
    # 'openspace.action.removeAction',
    # 'openspace.action.triggerAction',

    # 'openspace.asset.add',
    # 'openspace.asset.allAssets',
    # 'openspace.asset.isLoaded',
    # 'openspace.asset.remove',
    # 'openspace.asset.removeAll',
    # 'openspace.asset.rootAssets',

    # 'openspace.audio.currentlyPlaying',
    # 'openspace.audio.globalVolume',
    # 'openspace.audio.isLooping',
    # 'openspace.audio.isPaused',
    # 'openspace.audio.isPlaying',
    # 'openspace.audio.pauseAll',
    # 'openspace.audio.pauseAudio',
    # 'openspace.audio.playAllFromStart',
    # 'openspace.audio.playAudio',
    # 'openspace.audio.playAudio3d',
    # 'openspace.audio.resumeAll',
    # 'openspace.audio.resumeAudio',
    # 'openspace.audio.set3dListenerPosition',
    # 'openspace.audio.set3dSourcePosition',
    # 'openspace.audio.setGlobalVolume',
    # 'openspace.audio.setLooping',
    # 'openspace.audio.setSpeakerPosition',
    # 'openspace.audio.setVolume',
    # 'openspace.audio.speakerPosition',
    # 'openspace.audio.stopAll',
    # 'openspace.audio.stopAudio',
    # 'openspace.audio.volume',

    # 'openspace.dashboard.addDashboardItem',
    # 'openspace.dashboard.addDashboardItemToScreenSpace',
    # 'openspace.dashboard.clearDashboardItems',
    # 'openspace.dashboard.removeDashboardItem',
    # 'openspace.dashboard.removeDashboardItemsFromScreenSpace',

    # 'openspace.debugging.addCartesianAxes',
    # 'openspace.debugging.removePathControlPoints',
    # 'openspace.debugging.removeRenderedCameraPath',
    # 'openspace.debugging.renderCameraPath',
    # 'openspace.debugging.renderPathControlPoints',

    # 'openspace.event.disableEvent',
    # 'openspace.event.enableEvent',
    # 'openspace.event.registeredEvents',
    # 'openspace.event.registerEventAction',
    # 'openspace.event.unregisterEventAction',

    # 'openspace.exoplanets.addExoplanetSystem',
    # 'openspace.exoplanets.getListOfExoplanets', # deprecated
    # 'openspace.exoplanets.listAvailableExoplanetSystems',
    # 'openspace.exoplanets.listOfExoplanets',
    # 'openspace.exoplanets.loadExoplanetsFromCsv',
    # 'openspace.exoplanets.removeExoplanetSystem',

    # 'openspace.gaia.addClippingBox',
    # 'openspace.gaia.addClippingSphere',
    # 'openspace.gaia.removeClippingBox',

    # 'openspace.globebrowsing.addBlendingLayersFromDirectory',
    # 'openspace.globebrowsing.addFocusNodeFromLatLong',
    # 'openspace.globebrowsing.addFocusNodesFromDirectory',
    # 'openspace.globebrowsing.addGeoJson',
    # 'openspace.globebrowsing.addGeoJsonFromFile',
    # 'openspace.globebrowsing.addGibsLayer',
    # 'openspace.globebrowsing.addLayer',
    # 'openspace.globebrowsing.capabilitiesWMS',
    # 'openspace.globebrowsing.createGibsGdalXml',
    # 'openspace.globebrowsing.createTemporalGibsGdalXml',
    # 'openspace.globebrowsing.deleteGeoJson',
    # 'openspace.globebrowsing.deleteLayer',
    'openspace.globebrowsing.flyToGeo',
    # 'openspace.globebrowsing.flyToGeo2',
    'openspace.globebrowsing.geoPositionForCamera',
    # 'openspace.globebrowsing.getGeoPositionForCamera', # deprecated
    # 'openspace.globebrowsing.getLayers', # deprecated
    # 'openspace.globebrowsing.getLocalPositionFromGeo', # deprecated
    # 'openspace.globebrowsing.goToChunk',
    # 'openspace.globebrowsing.goToGeo',
    'openspace.globebrowsing.jumpToGeo',
    'openspace.globebrowsing.layers',
    # 'openspace.globebrowsing.loadWMSCapabilities',
    # 'openspace.globebrowsing.loadWMSServersFromFile',
    # 'openspace.globebrowsing.localPositionFromGeo',
    # 'openspace.globebrowsing.moveLayer',
    # 'openspace.globebrowsing.parseInfoFile',
    # 'openspace.globebrowsing.removeWMSServer',
    # 'openspace.globebrowsing.setNodePosition',
    # 'openspace.globebrowsing.setNodePositionFromCamera',

    # 'openspace.iswa.addCdfFiles',
    # 'openspace.iswa.addCygnet',
    # 'openspace.iswa.addKameleonPlanes',
    # 'openspace.iswa.addScreenSpaceCygnet',
    # 'openspace.iswa.removeCygnet',
    # 'openspace.iswa.removeGroup',
    # 'openspace.iswa.removeScreenSpaceCygnet',
    # 'openspace.iswa.setBaseUrl',

    # 'openspace.modules.isLoaded',

    'openspace.navigation.addGlobalRoll',
    'openspace.navigation.addGlobalRotation',
    'openspace.navigation.addLocalRoll',
    'openspace.navigation.addLocalRotation',
    'openspace.navigation.addTruckMovement',
    # 'openspace.navigation.axisDeadzone',
    # 'openspace.navigation.bindJoystickAxis',
    # 'openspace.navigation.bindJoystickAxisProperty',
    # 'openspace.navigation.bindJoystickButton',
    # 'openspace.navigation.clearJoystickButton',
    'openspace.navigation.distanceToFocus',
    # 'openspace.navigation.distanceToFocusBoundingSphere',
    # 'openspace.navigation.distanceToFocusInteractionSphere',
    # 'openspace.navigation.getNavigationState', # maybe
    # 'openspace.navigation.joystickAxis',
    # 'openspace.navigation.joystickButton',
    # 'openspace.navigation.listAllJoysticks',
    # 'openspace.navigation.loadNavigationState',
    'openspace.navigation.retargetAim',
    'openspace.navigation.retargetAnchor',
    # 'openspace.navigation.saveNavigationState',
    # 'openspace.navigation.setAxisDeadZone',
    # 'openspace.navigation.setNavigationState', # maybe
    # 'openspace.navigation.targetNextInterestingAnchor',
    # 'openspace.navigation.targetPreviousInterestingAnchor',
    # 'openspace.navigation.triggerIdleBehavior', # maybe

    # 'openspace.openglCapabilities.extensions',
    # 'openspace.openglCapabilities.glslCompiler',
    # 'openspace.openglCapabilities.gpuVendor',
    # 'openspace.openglCapabilities.hasOpenGLVersion',
    # 'openspace.openglCapabilities.isExtensionSupported',
    # 'openspace.openglCapabilities.max2DTextureSize',
    # 'openspace.openglCapabilities.max3DTextureSize',
    # 'openspace.openglCapabilities.maxAtomicCounterBufferBindings',
    # 'openspace.openglCapabilities.maxShaderStorageBufferBindings',
    # 'openspace.openglCapabilities.maxTextureUnits',
    # 'openspace.openglCapabilities.maxUniformBufferBindings',
    # 'openspace.openglCapabilities.openGLVersion',

    # 'openspace.orbitalnavigation.setRelativeMaxDistance', # maybe
    # 'openspace.orbitalnavigation.setRelativeMinDistance',

    # 'openspace.parallel.connect',
    # 'openspace.parallel.disconnect',
    # 'openspace.parallel.joinServer',
    # 'openspace.parallel.requestHostship',
    # 'openspace.parallel.resignHostship',

    # 'openspace.pathnavigation.continuePath',
    # 'openspace.pathnavigation.createPath', # maybe
    'openspace.pathnavigation.flyTo',
    # 'openspace.pathnavigation.flyToHeight',
    # 'openspace.pathnavigation.flyToNavigationState', # maybe
    'openspace.pathnavigation.isFlying',
    'openspace.pathnavigation.jumpTo',
    # 'openspace.pathnavigation.jumpToNavigationState', # maybe
    # 'openspace.pathnavigation.pausePath',
    # 'openspace.pathnavigation.skipToEnd',
    # 'openspace.pathnavigation.stopPath',
    'openspace.pathnavigation.zoomToDistance',
    # 'openspace.pathnavigation.zoomToDistanceRelative',
    'openspace.pathnavigation.zoomToFocus',

    # 'openspace.scriptScheduler.clear',
    # 'openspace.scriptScheduler.loadFile',
    # 'openspace.scriptScheduler.loadScheduledScript',
    # 'openspace.scriptScheduler.scheduledScripts',
    # 'openspace.scriptScheduler.setModeApplicationTime',
    # 'openspace.scriptScheduler.setModeRecordedTime',
    # 'openspace.scriptScheduler.setModeSimulationTime',

    # 'openspace.sessionRecording.disableTakeScreenShotDuringPlayback',
    # 'openspace.sessionRecording.enableTakeScreenShotDuringPlayback',
    # 'openspace.sessionRecording.fileFormatConversion',
    # 'openspace.sessionRecording.isPlayingBack',
    # 'openspace.sessionRecording.isRecording',
    # 'openspace.sessionRecording.setPlaybackPause',
    # 'openspace.sessionRecording.startPlayback',
    # 'openspace.sessionRecording.startPlaybackApplicationTime',
    # 'openspace.sessionRecording.startPlaybackRecordedTime',
    # 'openspace.sessionRecording.startPlaybackSimulationTime',
    # 'openspace.sessionRecording.startRecording',
    # 'openspace.sessionRecording.startRecordingAscii',
    # 'openspace.sessionRecording.stopPlayback',
    # 'openspace.sessionRecording.stopRecording',
    # 'openspace.sessionRecording.togglePlaybackPause',

    # 'openspace.skybrowser.addDisplayCopy',
    # 'openspace.skybrowser.addPairToSkyBrowserModule',
    # 'openspace.skybrowser.adjustCamera',
    # 'openspace.skybrowser.centerTargetOnScreen',
    # 'openspace.skybrowser.createTargetBrowserPair',
    # 'openspace.skybrowser.disableHoverCircle',
    # 'openspace.skybrowser.finetuneTargetPosition',
    # 'openspace.skybrowser.getListOfImages',
    # 'openspace.skybrowser.getTargetData',
    # 'openspace.skybrowser.getWwtImageCollectionUrl',
    # 'openspace.skybrowser.initializeBrowser',
    # 'openspace.skybrowser.listOfImages',
    # 'openspace.skybrowser.loadImagesToWWT',
    # 'openspace.skybrowser.loadingImageCollectionComplete',
    # 'openspace.skybrowser.moveCircleToHoverImage',
    # 'openspace.skybrowser.reloadDisplayCopyOnNode',
    # 'openspace.skybrowser.removeDisplayCopy',
    # 'openspace.skybrowser.removeSelectedImageInBrowser',
    # 'openspace.skybrowser.removeTargetBrowserPair',
    # 'openspace.skybrowser.scrollOverBrowser',
    # 'openspace.skybrowser.selectImage',
    # 'openspace.skybrowser.sendOutIdsToBrowsers',
    # 'openspace.skybrowser.setBorderColor',
    # 'openspace.skybrowser.setBorderRadius',
    # 'openspace.skybrowser.setBrowserRatio',
    # 'openspace.skybrowser.setEquatorialAim',
    # 'openspace.skybrowser.setHoverCircle',
    # 'openspace.skybrowser.setImageLayerOrder',
    # 'openspace.skybrowser.setOpacityOfImageLayer',
    # 'openspace.skybrowser.setSelectedBrowser',
    # 'openspace.skybrowser.setVerticalFov',
    # 'openspace.skybrowser.showAllTargetsAndBrowsers',
    # 'openspace.skybrowser.startFinetuningTarget',
    # 'openspace.skybrowser.startSetup',
    # 'openspace.skybrowser.stopAnimations',
    # 'openspace.skybrowser.targetData',
    # 'openspace.skybrowser.translateScreenSpaceRenderable',
    # 'openspace.skybrowser.wwtImageCollectionUrl',

    # 'openspace.space.convertFromRaDec',
    # 'openspace.space.convertToRaDec',
    # 'openspace.space.readKeplerFile',
    # 'openspace.space.tleToSpiceTranslation',

    # 'openspace.spice.convertTLEtoSPK',
    # 'openspace.spice.kernels',
    # 'openspace.spice.loadKernel',
    # 'openspace.spice.position',
    # 'openspace.spice.rotationMatrix',
    # 'openspace.spice.spiceBodies',
    # 'openspace.spice.unloadKernel',

    # 'openspace.statemachine.canGoToState',
    # 'openspace.statemachine.createStateMachine',
    # 'openspace.statemachine.currentState',
    # 'openspace.statemachine.destroyStateMachine',
    # 'openspace.statemachine.goToState',
    # 'openspace.statemachine.possibleTransitions',
    # 'openspace.statemachine.printCurrentStateInfo',
    # 'openspace.statemachine.saveToDotFile',
    # 'openspace.statemachine.setInitialState',

    # 'openspace.sync.syncResource',
    # 'openspace.sync.unsyncResource',

    # 'openspace.systemCapabilities.cacheLineSize',
    # 'openspace.systemCapabilities.cacheSize',
    # 'openspace.systemCapabilities.cores',
    # 'openspace.systemCapabilities.extensions',
    # 'openspace.systemCapabilities.fullOperatingSystem',
    # 'openspace.systemCapabilities.installedMainMemory',
    # 'openspace.systemCapabilities.L2Associativity',
    # 'openspace.systemCapabilities.os',

    # 'openspace.time.advancedTime',
    # 'openspace.time.convertTime',
    'openspace.time.currentApplicationTime',
    'openspace.time.currentTime',
    'openspace.time.currentWallTime',
    'openspace.time.deltaTime',
    # 'openspace.time.interpolateDeltaTime',
    # 'openspace.time.interpolateNextDeltaTimeStep', # maybe
    # 'openspace.time.interpolatePause',
    # 'openspace.time.interpolatePreviousDeltaTimeStep', # maybe
    # 'openspace.time.interpolateTime',
    # 'openspace.time.interpolateTimeRelative',
    # 'openspace.time.interpolateTogglePause',
    'openspace.time.isPaused',
    # 'openspace.time.pauseToggleViaKeyboard',
    'openspace.time.setDeltaTime',
    # 'openspace.time.setDeltaTimeSteps',
    # 'openspace.time.setNextDeltaTimeStep', # maybe
    'openspace.time.setPause',
    # 'openspace.time.setPreviousDeltaTimeStep', # maybe
    'openspace.time.setTime',
    # 'openspace.time.SPICE', # maybe
    'openspace.time.togglePause',
    'openspace.time.UTC',
]

print(f'{len(whitelist)} functions whitelisted')

tools_whitelisted = [t for t in tools if t['function']['name'] in whitelist]

for t in tools_whitelisted:
    t['function']['name'] = t['function']['name'].replace('openspace.', '').replace('.', '_')
    t['function']['description'] = t['function']['description'][:1000]

    # if t['function']['name'] in ['fadeIn', 'fadeOut']:
    #     t['function']['parameters']['required'].append('fadeTime')

    if t['function']['name'] == 'pathnavigation_flyTo':
        t['function']['parameters']['required'].append('duration')

    if t['function']['name'] == 'globebrowsing_jumpToGeo':
        t['function']['parameters']['required'].append('altitude')
    if t['function']['name'] == 'globebrowsing_flyToGeo':
        t['function']['parameters']['required'].append('duration')

if len(tools_whitelisted) != len(whitelist):
    print('[WARN] some whitelisted functions were not found.')

assistant = client.beta.assistants.update(args.id, tools=tools_whitelisted)

print('done')
