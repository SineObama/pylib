# coding=utf-8

import win32api
import win32gui

hWnd = 0

def refreshWindow():
	'''更新窗口句柄'''
	global hWnd
	s = win32api.GetConsoleTitle()
	hWnd = win32gui.FindWindow(0,s)
	return

def FlashWindow():
	'''任务栏闪烁'''
	win32gui.FlashWindow(hWnd, 1)
	return

refreshWindow()
