#!/usr/bin python3
from mutagen.mp3 import MP3
import random
import PySimpleGUI as sg
import glob
import time
import vlc
import math
from os import path

width = 500
height = 60



themewindow = [[sg.Combo(sg.theme_list(), key='theme')],
			   [sg.Button('Show Theme')]]

themewin = sg.Window('Theme Selection', themewindow, finalize=True)
event, values = themewin.read()

sg.theme(values['theme'])
themewin.close()


bonusColor = sg.theme_element_background_color()
normalColor = sg.theme_button_color()[1]
progressColor = 'red'
outlineColor = sg.theme_element_text_color()
tapeEndColor = sg.theme_background_color()
backgroundColor = sg.theme_slider_color()

def calculateTimePerPixel(Time):
	return math.ceil(Time/2*60/width)

timePerPixel = calculateTimePerPixel(90)

playbackframe = [[sg.Combo(['Side A', 'Side B'], key='side'), sg.Button('Start New', key='startnew'), sg.Button('Resume', key='resume', disabled=True), sg.Checkbox('Bonus', key='bonus', enable_events=True, default=True), sg.Button('Play Tone', key='playtone'), sg.Button('Stop', key='stop', disabled=True)],
			     [sg.Text('Playing:'), sg.Text('', key='playing', size=(30, 1))],
			     [sg.ProgressBar(1000, orientation='h', size=(45,10), key='progress')]]

tapepreviewframe = [[sg.T('Time per Pixel:'), sg.Text(str(timePerPixel), key='timeperpixel'), sg.T('seconds'), sg.Button('Show Preview Details', key='showdetails')],
				    [sg.Graph(canvas_size=(width,height), graph_bottom_left=(0,height), graph_top_right=(width,0), background_color=backgroundColor, key='graph')]]

mainwindow = [[sg.T("Tape Length:"), sg.Slider(range=(5,120), key='tapelen', resolution=5, orientation='h', enable_events=True, default_value=90), sg.T("minutes"), sg.T("Warning: Tape Too Short!", visible=False, key='tapewarn')],
			 [sg.T('Silence Between Tracks:'), sg.Slider(range=(1,20), key='silencelen', enable_events=True, orientation='h', default_value=5), sg.T('seconds')],
			 [sg.T('Seed:'), sg.In(key='seed', default_text=str(time.time())), sg.Button('Refresh Seed', key='refreshseed')],
			 [sg.Frame('Playback', playbackframe)],
			 [sg.Frame('Tape Preview', tapepreviewframe)]]


window = sg.Window('Tape Recording', mainwindow, finalize=True)

oldtapelen = 0
oldbonus = False
oldtimeperpixel = 0
oldsilencelen = 0

allBonus = [[],[]]
playedBonus = []
preview = []

def resetSeed(seed):
	try:
		random.seed(float(seed))
	except:
		random.seed(seed)

def calculateLengths(files):
	lengths = []
	for i in range(0, len(files)):
		lengths.append(MP3(files[i]).info.length)
	return lengths
		
def readyBonusPlayback():
	global allBonus, playedBonus
	allBonus = [glob.glob('Bonus/*.mp3'), []]
	
	for i in range(0, len(playedBonus)):
		allBonus[0].remove(playedBonus[i])
	
	allBonus[1] = calculateLengths(allBonus[0])
		
def nextBonusTrack(timeRemaining):
	global allBonus, playedBonus
	for i in range(len(allBonus[0])-1, -1, -1):
		if allBonus[1][i] >= timeRemaining:
			allBonus[0].pop(i)
			allBonus[1].pop(i)
	if len(allBonus[0]) < 1:
		return False
	elif len(allBonus[0]) < 2:
		index = 0
	else:
		index = random.randint(0, len(allBonus[0])-1)
	trackname = allBonus[0].pop(index)
	allBonus[1].pop(index)
	playedBonus.append(trackname)
	return trackname or False

def updateGraph(tapelen, bonus, silencelen, seed):
	resetSeed(seed)
	
	graph = window['graph']
	if True:
		graph.Erase()
		sideA = [glob.glob('A/*.mp3'),calculateLengths(glob.glob('A/*.mp3'))]
		sideB = [glob.glob('B/*.mp3'),calculateLengths(glob.glob('B/*.mp3'))]
		sides = [sideA, sideB]
		
		bonusA = []
		bonusB = []
		global playedBonus
		playedBonus = []
		tooShort = False
		
		for i in range(0,2):
			# do this twice, one for each side
			currenttime = 0
			for x in range(0, len(sides[i][0])):
				graph.DrawRectangle((math.ceil(currenttime / timePerPixel), (height*i/2)), (math.ceil((sides[i][1][x]+currenttime)/timePerPixel), height*(i+1)/2), fill_color=normalColor, line_color=outlineColor)
				currenttime = currenttime + sides[i][1][x] + silencelen
			
			if bonus:
				
				readyBonusPlayback()
				# handle bonus recording
				track = nextBonusTrack((tapelen*60)/2 - currenttime)
				while track:
					if i == 0:
						bonusA.append(track)
					else:
						bonusB.append(track)
					graph.DrawRectangle((math.ceil(currenttime / timePerPixel), (height*i/2)), (math.ceil((MP3(track).info.length+currenttime)/timePerPixel), height*(i+1)/2), fill_color=bonusColor, line_color=outlineColor)
					
					currenttime = currenttime + MP3(track).info.length + silencelen
					track = nextBonusTrack((tapelen*60)/2 - currenttime)
			if currenttime > math.ceil(tapelen*30):
				tooShort = True
				
			graph.DrawRectangle((math.ceil(tapelen*30/timePerPixel), 0), (width, height), fill_color=tapeEndColor, line_color=tapeEndColor)
			window['tapewarn'].update(visible=tooShort)
			window.finalize()
		global preview
		preview = [[sideA[0], bonusA], [sideB[0], bonusB]]

def guiState(state):
	window['tapelen'].update(disabled=(not state))
	window['silencelen'].update(disabled=(not state))
	window['seed'].update(disabled=(not state))
	window['refreshseed'].update(disabled=(not state))
	window['side'].update(disabled=(not state))
	window['startnew'].update(disabled=(not state))
	if state:
		if (path.exists('progress.csv')):
			window['resume'].update(disabled=False)
	else:
		window['resume'].update(disabled=(not state))
	window['bonus'].update(disabled=(not state))
	window['playtone'].update(disabled=(not state))
	window['stop'].update(disabled=state)
	window.finalize()
	
def printTrackLayout():
	global preview
	text = [['== Side A ==', '== Side A - Bonus =='],['== Side B ==', '== Side B - Bonus ==']]
	sg.Print('')
	sg.Print('['+time.strftime('%I:%M:%S')+']')
	for a in range(0, 2):
		for b in range(0, 2):
			sg.Print(text[a][b])
			for x in range(0, len(preview[a][b])):
				sg.Print(preview[a][b][x] + ' - ' + str(int(MP3(preview[a][b][x]).info.length)) + ' seconds')
	
def playFile(file, starttime, strip, side):
	p = vlc.MediaPlayer(file)
	window['playing'].update(str(file))
	window.Finalize()
	length = int(MP3(file).info.length)
	p.play()
	event, value = window.read(timeout = 300)
	while (p.is_playing() == 1 and event != None and event != 'stop'):
		event, value = window.read(timeout = 300)
		window['progress'].UpdateBar(int(p.get_position() * 1000))
		if starttime != 0 and event != None:
			window['graph'].RelocateFigure(strip, math.ceil((time.time() - starttime)/timePerPixel), height*side/2)
			window['graph'].BringFigureToFront(strip)
		if event == 'showdetails':
			printTrackLayout()
	if event == None:
		exit()
	window['progress'].UpdateBar(0)
	window['playing'].update('Nothing')
	window.Finalize()
	if event == 'stop':
		p.stop()
		return False
	return True

def silence(delaytime, starttime, strip, side):
	t0 = time.time()
	window['playing'].update('Waiting for ' + str(delaytime) + ' seconds.')
	window.Finalize()
	while ((time.time() - t0) < delaytime):
		window['progress'].UpdateBar(((time.time() - t0) / delaytime) * 1000)
		time.sleep(0.1)
		if starttime != 0 and event != None:
			window['graph'].RelocateFigure(strip, math.ceil((time.time() - starttime)/timePerPixel), height*side/2)
			window['graph'].BringFigureToFront(strip)
		if event == 'showdetails':
			printTrackLayout()
	window['progress'].UpdateBar(0)
	window['playing'].update('Nothing')
	window.Finalize()
	
def playSide(side, silencelen):
	if side == 'Side A':
		side = 0
	elif side == 'Side B':
		side = 1
	else:
		return
	guiState(False)
	starttime = time.time()
	rect = window['graph'].DrawRectangle((0,height*side/2), (2, height*(side+1)/2), line_color=progressColor, fill_color=progressColor)
	for x in range(0, 2):
		for i in range(0, len(preview[side][x])):
			if not playFile(preview[side][x][i], starttime, rect, side):
				guiState(True)
				return
			silence(silencelen, starttime, rect, side)
	guiState(True)
	
while True:
	event, values = window.read()
	
	if event == sg.WIN_CLOSED:
		break
	
	try:
		values['silencelen'] = int(values['silencelen'] or 5)
	except:
		values['silencelen'] = 5
		window['silencelen'].update(value='5')
		
	try:
		values['tapelen'] = int(values['tapelen'] or 90)
	except:
		values['tapelen'] = 90
		window['tapelen'].update(value='90')
		
	if event == 'refreshseed':
		window['seed'].update(value=str(time.time()))
	elif event == 'playtone':
		guiState(False)
		playFile('TONE.mp3', 0, 0, 0)
		guiState(True)
	elif event == 'showdetails':
		printTrackLayout()
	elif event == 'startnew':
		playSide(values['side'], values['silencelen'])
		
	timePerPixel = calculateTimePerPixel(values['tapelen'])
	window['timeperpixel'].update(value=timePerPixel)
	updateGraph(values['tapelen'], values['bonus'], values['silencelen'], values['seed'])
	
	window.Finalize()
	