#!/bin/sh

cp "/Users/matthewjordan/Library/Application Support/avocado/iso/test version/Test Version.bin" Atlas.nes 2> /dev/null;
if [ "$?" != "0" ]; then
	echo "ROM file \"Dragon Quest IV - Michibikareshi Monotachi (J) (PRG1) [!].nes\" not found; creating an empty file instead.";
	cat /dev/null > Atlas.bin;
fi

perl abcde/abcde.pl -cm abcde::Atlas Atlas.bin AtlasTest.txt
