# coding=utf-8
'''
任务栏窗口闪烁api
'''

import win32api
import win32gui

hWnd = 0

def refreshWindow():
	'''更新窗口句柄'''
	global hWnd
	s = win32api.GetConsoleTitle()
	hWnd = win32gui.FindWindow(0,s)
	return

def flash():
	'''任务栏闪烁'''
	win32gui.FlashWindowEx(hWnd, 0, 1, 1000)
	return

refreshWindow()
