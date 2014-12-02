#!/bin/bash
#cd music/itunes_mnt
cd /media/itunes/iTunes/iTunes\ Media/

FIND_CMD="find ."

BASE_OPT="\( -iname '*.mp3' -o -iname '*.flac' -o -iname '*.m4a' \)"
PATH_FIX_CMD="sed -e 's/^\.\///g'" 

OTHER_DIR="./_Other"

create_pl()
{
	sh -c "$FIND_CMD $FIND_OPT | $PATH_FIX_CMD > $PL"
#	echo "$FIND_CMD $FIND_OPT | $PATH_FIX_CMD > $PL"
}

# iTunes Search
FIND_OPT="$BASE_OPT -print -o \( -wholename '$OTHER_DIR' -prune \)"
PL="/home/pi/service/playlists/itunes.m3u"
create_pl

# Radio Archive
FIND_OPT="$BASE_OPT -a \( -wholename '$OTHER_DIR/*' \
-o -wholename './*Bogart*' \
-o -wholename './Billie Holiday/*' \
-o -wholename './Glenn Miller/*' \
-o -wholename './Fats Waller/*' \
-o -wholename './*Confidential*/*' \
-o -iname '04 La Mer*' \
-o -iname '07 If I Did*' \
-o -iname '08 If I Did*' \
-o -iname '09 The Best Things*' \
-o -iname '10 It Had*' \
-o -iname '13 Wrap Your*' \
-o -iname '14 Just Walking*' \
-o -iname '16 Brother, Can*' \
-o -iname '17 Bei Bir *' \
-o -iname '24 Liza*' \
-o -iname '25 Twentieth*' \
-o -iname '29 Beyond*' \
-o -iname '36 It*' \
-o -iname '40 God Bless*' \
-o -iname '41 You*' \
-o -iname '46 World Weary*' \
-o -iname '47 This Is a*' \
-o -iname '48 You*' \
-o -iname '49 Let*' \
-o -iname '50 Avalon*' \
-o -iname '51 Just One*' \
-o -iname '52 Wild*' \
-o -iname '*193*' \)"
PL="/home/pi/service/playlists/oldmusic.m3u"
create_pl
