
#!/bin/sh
set -eu
umask 077

SRC="/usr/local/bastille/jails"

if [ ! -d "$SRC" ]; then
    echo "Error: $SRC not found."
    exit 1
fi

find "$SRC" -type d -name root -prune -o \
    -type f \( -name jail.conf -o -name fstab \) -print |
while IFS= read -r file; do
    jail_dir=$(dirname "$file")
    jail_name=$(basename "$jail_dir")
    filename=$(basename "$file")

    mkdir -p "$jail_name"
    cp -p "$file" "$jail_name/$filename"

    echo "Copied: $jail_name/$filename"
done

echo "Done: jail configurations copied into the current directory."

