#!/bin/sh

cp "/Users/matthewjordan/Library/Application Support/avocado/iso/test version/Test Version.bin" Atlas.bin 2> /dev/null;
if [ "$?" != "0" ]; then
	echo "ROM file \"TokiMeki Memorial.bin\" not found; creating an empty file instead.";
	cat /dev/null > Atlas.bin;
fi

perl abcde/abcde.pl -cm abcde::Atlas Atlas.bin Atlas.txt
