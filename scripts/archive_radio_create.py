#!/usr/bin/env python

import random
import os
import fnmatch
import math

def locate(pattern, root):
	dirlist = []
	for path, dirs, files in os.walk(os.path.abspath(root)):
		for filename in fnmatch.filter(files, pattern):
			dirlist.append(os.path.join(path, filename))
	return dirlist

NUM_ADS = 3
PATH_ADS = "/media/itunes/iTunes/iTunes Media/_Other/ads"

NUM_SHOWS = 1
PATH_SHOWS = "/media/itunes/iTunes/iTunes Media/_Other/shows"

NUM_SONGS = 5
SONG_ROOT = "/media/itunes/iTunes/iTunes Media"
SONGS_LIST = "/home/pi/service/playlists/oldmusic.m3u"

def pick_songs():
	song_pl = open(SONGS_LIST, 'r')
	list_songs = []
	for fn in song_pl.readlines():
		list_songs.append(os.path.join(SONG_ROOT, fn.rstrip('\n')))
	return list_songs	

def pick_shows():
	return locate("*.mp3", PATH_SHOWS)

def pick_ads():
	return locate("*.mp3", PATH_ADS)

def create_playlist():
	list_ads = pick_ads()
	list_shows = pick_shows()
	list_songs = pick_songs()

	pl_len = int(max( 	math.ceil(len(list_songs)/NUM_SONGS),
						math.ceil(len(list_shows)/NUM_SHOWS) ))

	"""
	Basic playlist generation algorithm
	
	- Pick either a show-block or song-block at random;
	- Follow it up with an ad break;
	- Repeat.
	"""

	playlist = []

	for i in range(0, pl_len, 1):	

		if (len(list_ads) == 0):
			list_ads = pick_ads()
		if (len(list_songs) == 0):
			list_songs = pick_songs()
		if (len(list_shows) == 0):
			list_shows = pick_shows()
			
		TYPE_SHOW = 0
		TYPE_SONG = 1
		type = random.randint(0,1)
		if (type == TYPE_SHOW):
			for t in range(0, NUM_SHOWS, 1):
				try:
					playlist.append(list_shows.pop(random.randint(0, len(list_shows)-1)))
				except:
					pass
		elif (type == TYPE_SONG):
			for t in range(0, NUM_SONGS, 1):
				try:
					playlist.append(list_songs.pop(random.randint(0, len(list_songs)-1)))
				except:
					pass
	
		for t in range(0, NUM_ADS, 1):
			try:
				playlist.append(list_ads.pop(random.randint(0, len(list_ads)-1)))
			except:
				pass

	for fn in playlist:
		print fn


create_playlist()
