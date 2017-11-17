# coding=utf-8

import win32api
import win32gui

hWnd = 0

def refreshWindow():
	global hWnd
	s = win32api.GetConsoleTitle()
	hWnd = win32gui.FindWindow(0,s)
	return

def FlashWindow():
	win32gui.FlashWindow(hWnd, 1)
	return

refreshWindow()
