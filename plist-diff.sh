#!/bin/bash

# This file has been inspired by this code https://gist.github.com/scottrigby/4a3606491113224cbff325e9c8c73213
# examples
# ./plist-diff.sh /tmp/config-240921-201043 /tmp/config-240921-223419
# ./plist-diff.sh /tmp/config-240921-201043/com.apple.SoftwareUpdate.plist /tmp/config-240921-223419/com.apple.SoftwareUpdate.plist

# Function to convert plist to XML
convert_plist() {
    plutil -convert xml1 -o - "$1"
}

# Check if the first argument is a directory
if [ -d "$1" ]; then
    a=$(find "$1" -name '*.plist' -exec plutil -convert xml1 -o - {} +)
else
    a=$(convert_plist "$1")
fi

# Check if the second argument is a directory
if [ -d "$2" ]; then
    b=$(find "$2" -name '*.plist' -exec plutil -convert xml1 -o - {} +)
else
    b=$(convert_plist "$2")
fi

# The -u flag displays line numbers with "+" and "-" (rather than ">" and "<").
# The optional colordiff binary defaults to green/red.
# Less -R is used to emulate vi.
if command -v colordiff &> /dev/null; then
    diff -u <(echo "$a") <(echo "$b") "${@:3}" | colordiff
else
    diff -u <(echo "$a") <(echo "$b") "${@:3}"
fi
