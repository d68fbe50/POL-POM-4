#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2009 Pâris Quentin
# Copyright (C) 2007-2010 PlayOnLinux Team

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA. 

import os, sys, string, shutil
import wx, time, shlex
#from subprocess import Popen,PIPE

import wine_versions
import lib.playonlinux as playonlinux
import lib.wine as wine
import lib.Variables as Variables
import lib.lng as lng

class MainWindow(wx.Frame):
	def __init__(self,parent,id,title,logcheck="/dev/null",logtype=None):
		wx.Frame.__init__(self, parent, -1, title, size = (800, 600), style = wx.CLOSE_BOX | wx.CAPTION | wx.MINIMIZE_BOX)
		self.SetIcon(wx.Icon(Variables.playonlinux_env+"/etc/playonlinux.png", wx.BITMAP_TYPE_ANY))
		self.SetTitle(_('{0} debugger').format(os.environ["APPLICATION_TITLE"]))
		#self.panelFenp = wx.Panel(self, -1)
	
		self.prefixes_item = {}
		self.logs_item = {}
		
		self.splitter = wx.SplitterWindow(self, -1, style=wx.SP_NOBORDER)
		self.panelEmpty = wx.Panel(self.splitter, -1)
		self.panelNotEmpty = wx.Panel(self.splitter, -1)

		
		self.noselect = wx.StaticText(self.panelEmpty, -1, _('Please select a debug file'),pos=(0,150),style=wx.ALIGN_RIGHT)
		self.noselect.SetPosition(((570-self.noselect.GetSize()[0])/2,250))
		self.noselect.Wrap(500)
	
			
		self.images = wx.ImageList(16, 16)
				
		self.list_game = wx.TreeCtrl(self.splitter, 900, size = wx.DefaultSize, style=wx.TR_HIDE_ROOT)	
		wx.EVT_TREE_SEL_CHANGED(self, 900, self.analyseLog)

		
		self.list_game.SetSpacing(0);
		self.list_game.SetImageList(self.images)
		
			
		self.list_software()
		
		self.timer = wx.Timer(self, 1)
		self.Bind(wx.EVT_TIMER, self.AutoReload, self.timer)
		
		self.timer.Start(10)
		self.logfile = ""
		
		# Debug control
		self.panelText = wx.Panel(self.panelNotEmpty, -1, size=(590,400), pos=(2,2)) # Hack, wxpython bug
		self.log_reader = wx.TextCtrl(self.panelText, 100, "", size=wx.Size(590,400), pos=(2,2), style=Variables.widget_borders|wx.TE_RICH2|wx.TE_READONLY|wx.TE_MULTILINE)

		
		if(logcheck == "/dev/null"):
			self.HideLogFile()
		else:
			self.analyseReal(logtype,logcheck)
		
		#self.log_reader.SetDefaultStyle(wx.TextAttr(font=wx.Font(13,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL)))
	def ShowLogFile(self):
		self.splitter.Unsplit()
		self.splitter.SplitVertically(self.list_game,self.panelNotEmpty)
		self.splitter.SetSashPosition(200)
		
	def HideLogFile(self):
		self.splitter.Unsplit()
		self.splitter.SplitVertically(self.list_game,self.panelEmpty)
		self.splitter.SetSashPosition(200)
		
	def AppendStyledText(self, line):
		ins = self.log_reader.GetInsertionPoint()
		leng = len(line)
		if(leng < 100):
			self.log_reader.AppendText(line)
		
			self.bold = wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.BOLD)

			if(line[0:5] == "wine:"):
				self.log_reader.SetStyle(ins, ins+5, wx.TextAttr("red", wx.NullColour))
			
			elif(line[0:6] == "fixme:"):
				self.log_reader.SetStyle(ins, ins+leng, wx.TextAttr(wx.Colour(100,100,100), wx.NullColour))
		
			elif(self.logtype == 1 and leng > 19 and line[17:20] == " - "):
				self.log_reader.SetStyle(ins, ins+17, wx.TextAttr("black", wx.NullColour, self.bold))
			elif(self.logtype == 0 and leng > 21 and line[19:22] == " - "):
				self.log_reader.SetStyle(ins, ins+19, wx.TextAttr("black", wx.NullColour, self.bold))
			else:
				self.log_reader.SetStyle(ins, ins+leng, wx.TextAttr("black", wx.NullColour))
			
	def AutoReload(self, event):
		if(self.logfile != ""):
			self.j = 0
			while True:
				self.line = self.logfile.readline()
				if not self.line:
					break
				else:
					self.AppendStyledText(self.line)
				if(self.j > 20):
					break
				self.j += 1
					
	def analyseLog(self, event):
		parent =  self.list_game.GetItemText(self.list_game.GetItemParent(self.list_game.GetSelection()))
		selection =  self.list_game.GetItemText(self.list_game.GetSelection())
		if(parent == _("Virtual drives")):
			parent = 0
		else:
			parent = 1
		self.analyseReal(parent, selection)
		
	def analyseReal(self, parent, selection):
		self.ShowLogFile()
		self.log_reader.Clear()
		try:
			if(parent == 0):
				checkfile = Variables.playonlinux_rep+"wineprefix/"+selection+"/playonlinux.log"
				self.logfile = open(checkfile, 'r')
				self.logsize = os.path.getsize(checkfile)
				if(self.logsize - 10000 > 0):
					self.logfile.seek(self.logsize - 10000) # 10 000 latest chars should be sufficient
				self.logtype = 0

			if(parent == 1):
				checkfile = Variables.playonlinux_rep+"logs/"+selection+"/"+selection+".log"
				self.logfile = open(checkfile, 'r')
				self.logsize = os.path.getsize(checkfile)
				if(self.logsize - 10000 > 0):
					self.logfile.seek(self.logsize - 10000) # 10 000 latest chars should be sufficient	
				self.logtype = 1
		except:
			pass

	def list_software(self):
	
		
			self.prefixes = os.listdir(Variables.playonlinux_rep+"wineprefix/")
			self.prefixes.sort()

			self.logs = os.listdir(Variables.playonlinux_rep+"logs/")
			self.logs.sort()
			
			try:
				self.prefixes.remove(".DS_Store")
			except:
				pass

			self.list_game.DeleteAllItems()
			self.images.RemoveAll()
			
			root = self.list_game.AddRoot("")
			self.prefixes_entry = self.list_game.AppendItem(root, _("Virtual drives"), 0)
			self.scripts_entry = self.list_game.AppendItem(root, _("Install scripts"), 1)
			
			self.file_icone = Variables.playonlinux_env+"/resources/images/icones/generic.png"
			self.bitmap = wx.Image(self.file_icone)
			self.bitmap.Rescale(16,16,wx.IMAGE_QUALITY_HIGH)
			self.bitmap = self.bitmap.ConvertToBitmap()
			self.images.Add(self.bitmap)
			self.images.Add(self.bitmap)
			
						
			self.i = 2
			for prefix in self.prefixes:
				if(os.path.isdir(Variables.playonlinux_rep+"wineprefix/"+prefix)):

					if(os.path.exists(Variables.playonlinux_rep+"/wineprefix/"+prefix+"/icon")):
						self.file_icone = Variables.playonlinux_rep+"/wineprefix/"+prefix+"/icon"
					else:
						try:
							archdd = playonlinux.GetSettings('ARCH',prefix)
							if(archdd == "amd64"):
								archdd = "64"
							else:
								archdd = "32"
						except:
							archdd = "32"
						self.file_icone = Variables.playonlinux_env+"/resources/images/menu/virtual_drive_"+archdd+".png"

					try:
						self.bitmap = wx.Image(self.file_icone)
						self.bitmap.Rescale(16,16,wx.IMAGE_QUALITY_HIGH)
						self.bitmap = self.bitmap.ConvertToBitmap()
						self.images.Add(self.bitmap)
					except:
						pass
						
					self.prefixes_item[prefix] = self.list_game.AppendItem(self.prefixes_entry, prefix, self.i)
					self.i += 1

			for log in self.logs:
					if(os.path.isdir(Variables.playonlinux_rep+"logs/"+log)):
						self.file_icone =  Variables.playonlinux_env+"/resources/images/menu/manual.png"

						try:
							self.bitmap = wx.Image(self.file_icone)
							self.bitmap.Rescale(16,16,wx.IMAGE_QUALITY_HIGH)
							self.bitmap = self.bitmap.ConvertToBitmap()
							self.images.Add(self.bitmap)
						except:
							pass

						self.logs_item[log] = self.list_game.AppendItem(self.scripts_entry, log, self.i)
						self.i += 1
						
			self.list_game.ExpandAll()
		
	def app_Close(self, event):
		self.Destroy()

	def apply_settings(self, event):
		self.Destroy()