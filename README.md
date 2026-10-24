# medal-e-ink

An e-ink digital photo frame built from a Raspberry Pi 4B and a Waveshare 7.3" Spectra 6 (E6) panel (800×480 pixels, 6 colors).

The current version shows a single picture. Once the refresh finishes, the panel keeps the image without power.

## Hardware

Plug the Waveshare HAT onto the Pi's 40-pin header, or wire the driver board to these pins:

| e-Paper | Pi pin (BCM)     |
|---------|------------------|
| VCC     | 3.3V             |
| GND     | GND              |
| DIN     | MOSI (GPIO 10)   |
| CLK     | SCLK (GPIO 11)   |
| CS      | CE0 (GPIO 8)     |
| DC      | GPIO 25          |
| RST     | GPIO 17          |
| BUSY    | GPIO 24          |
| PWR     | GPIO 18          |

### Frame window

The panel sits behind a frame whose opening is 110.85 mm wide and the full panel height. The panel has 0.2 mm pixels, so the visible area is the centre 554 × 480 pixels (columns 123 to 676). Pictures are cropped to that window. The hidden strips on the left and right are left white.

## Install on the Pi

On Raspberry Pi OS Lite:

```sh
sudo apt-get install -y git
git clone https://github.com/J-Britten/medal-e-ink.git ~/medal-e-ink
cd ~/medal-e-ink
./install.sh
sudo reboot          # only if the script asks for it
```

`install.sh` does the following:

- installs Pillow, numpy, spidev and gpiozero from apt
- enables SPI
- adds your user to the `spi` and `gpio` groups
- links the `photoframe` command into `/usr/local/bin`

## Usage

```sh
photoframe show ~/pictures/holiday.jpg
photoframe show photo.jpg --rotate 90          # frame mounted in portrait
photoframe show photo.jpg --fit contain        # letterbox instead of crop
photoframe show portrait.jpg --align top       # keep the top of a tall picture
photoframe show photo.jpg --saturation 1.5     # punchier colors
photoframe clear                               # white screen
```

A refresh takes about 30 seconds and the screen flashes several times while it runs. This is normal for Spectra 6 panels.

### Preview without hardware

To see the dithered result before sending it to the panel, run this on any machine that has Pillow and numpy:

```sh
python3 -m photoframe show photo.jpg --preview preview.png
```

### Options

| Option         | Default | Meaning                                                                 |
|----------------|---------|-------------------------------------------------------------------------|
| `--rotate`     | `0`     | How the panel is mounted, in degrees clockwise. Use 90 or 270 for portrait. |
| `--fit`        | `cover` | `cover` crops the picture to fill the window. `contain` adds white bars. |
| `--align`      | `center`| Which part of the picture to keep when cropping: `top`, `bottom`, `left`, `right`, combinations like `top-left`, or fractions `x,y` from 0 to 1 (e.g. `0.5,0.3`). With `contain`, it positions the picture in the window. |
| `--window-mm`  | `110.85`| Width of the frame opening, centred on the panel. Use `160` for the whole panel. |
| `--saturation` | `1.2`   | Color boost applied before dithering. The panel's inks are muted.        |
| `--contrast`   | `1.0`   | Contrast adjustment.                                                    |
| `--no-dither`  | off     | Map each pixel to the nearest color without dithering.                  |

## Layout

- [photoframe/epd.py](photoframe/epd.py): panel driver, adapted from Waveshare's `epd7in3e.py`
- [photoframe/image.py](photoframe/image.py): fits, enhances, dithers and packs the picture
- [photoframe/cli.py](photoframe/cli.py): the command-line interface
