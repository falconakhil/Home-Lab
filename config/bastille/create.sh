
#!/bin/sh
set -eu

BASTILLE_DIR="/usr/local/bastille"
JAILS_DIR="$BASTILLE_DIR/jails"

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this script as root."
    exit 1
fi

if ! command -v bastille >/dev/null 2>&1; then
    echo "Error: Bastille is not installed."
    exit 1
fi

for dir in */; do
    [ -d "$dir" ] || continue

    jail="${dir%/}"

    # Only process directories containing saved jail configs.
    [ -f "$dir/jail.conf" ] || [ -f "$dir/fstab" ] || continue

    echo
    echo "=== Jail: $jail ==="

    root="$JAILS_DIR/$jail/root"

    if [ ! -d "$root" ]; then
        printf "FreeBSD release for %s (e.g. 15.0-RELEASE): " "$jail"
        read -r release

        [ -n "$release" ] || {
            echo "Release is required; skipping $jail."
            continue
        }

        printf "Jail IP address (or blank if not applicable): "
        read -r ip

        printf "Network interface (or blank if not applicable): "
        read -r iface

        if [ -n "$ip" ] && [ -n "$iface" ]; then
            bastille create "$jail" "$release" "$ip" "$iface"
        else
            bastille create "$jail" "$release"
        fi
    else
        echo "Jail root already exists; skipping creation."
    fi

    dest="$JAILS_DIR/$jail"
    mkdir -p "$dest"

    # Preserve the existing generated jail configuration before
    # restoring the saved version.
    if [ -f "$dir/jail.conf" ]; then
        if [ -f "$dest/jail.conf" ]; then
            cp -p "$dest/jail.conf" "$dest/jail.conf.before-restore"
        fi
        cp -p "$dir/jail.conf" "$dest/jail.conf"
        echo "Restored jail.conf"
    fi

    if [ -f "$dir/fstab" ]; then
        if [ -f "$dest/fstab" ]; then
            cp -p "$dest/fstab" "$dest/fstab.before-restore"
        fi
        cp -p "$dir/fstab" "$dest/fstab"
        echo "Restored fstab"
    fi
done

echo
echo "Finished processing saved jail configurations."
echo "Inspect the configuration and verify networking before starting jails."

