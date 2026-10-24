#!/usr/bin/env bash
# Set up a Raspberry Pi (Pi OS Lite) to drive the Waveshare 7.3" Spectra 6 panel.
# Run from the repo checkout as your normal user: ./install.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NEED_REBOOT=0

echo "==> Installing system packages"
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pil python3-numpy python3-spidev python3-gpiozero python3-lgpio

echo "==> Enabling SPI"
if [ "$(sudo raspi-config nonint get_spi)" != "0" ]; then
    sudo raspi-config nonint do_spi 0
    NEED_REBOOT=1
fi

echo "==> Granting $USER access to SPI and GPIO"
for group in spi gpio; do
    if ! id -nG "$USER" | grep -qw "$group"; then
        sudo usermod -aG "$group" "$USER"
        NEED_REBOOT=1
    fi
done

echo "==> Installing 'photoframe' command"
sudo ln -sf "$REPO_DIR/bin/photoframe" /usr/local/bin/photoframe

echo
if [ "$NEED_REBOOT" = 1 ] || [ ! -e /dev/spidev0.0 ]; then
    echo "Done. Reboot once (sudo reboot) so SPI and group changes take effect."
else
    echo "Done. Try: photoframe show /path/to/picture.jpg"
fi
