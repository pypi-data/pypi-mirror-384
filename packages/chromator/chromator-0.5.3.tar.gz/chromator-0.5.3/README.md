# Chromator: Color shades generator

[![Poetry](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/githuib/chromator/master/assets/logo.json)](https://pypi.org/project/chromator)
[![PyPI - Version](https://img.shields.io/pypi/v/chromator)](https://pypi.org/project/chromator/#history)
[![PyPI - Python Versions](https://img.shields.io/pypi/pyversions/chromator)](https://pypi.org/project/chromator)

## Installation

```commandline
pip install chromator
```

## Usage

### General help

```commandline
$ chromator -h 
usage: css-shades [-h] [-c COLOR1] [-k COLOR2] [-s STEP] [-e EXTRAPOLATE] [-i] label

positional arguments:
  label

options:
  -h, --help            show this help message and exit
  -c, --color1 COLOR1
  -k, --color2 COLOR2
  -s, --step STEP
  -e, --extrapolate EXTRAPOLATE
  -i, --inclusive
```

### Shades as CSS variables, based on one input color:

```commandline
$ chromator bad-ass -c bada55 -s 10 
/*
Based on:

#bada55:
- Hue: 100.6°
- Saturation: 82.9%
- Lightness: 82.5%
*/
--bad-ass-10: #181e06;
--bad-ass-20: #2b340e;
--bad-ass-30: #3f4c18;
--bad-ass-40: #556523;
--bad-ass-50: #6b7f2e;
--bad-ass-60: #839a3a;
--bad-ass-70: #9bb646;
--bad-ass-80: #b4d352;
--bad-ass-90: #cdf05f;
```

### Shades as CSS variables, based on two input colors:

```commandline
$ chromator worse-ass -c bada55 -k b000b5 -s 10 -e 50 
/*
Based on:

#bada55:
- Hue: 100.6°
- Saturation: 82.9%
- Lightness: 82.5%

#b000b5:
- Hue: 305.5°
- Saturation: 100.0%
- Lightness: 42.1%
*/
--worse-ass-10: #380039;
--worse-ass-20: #5a005d;
--worse-ass-30: #86066c;
--worse-ass-40: #b5116b;
--worse-ass-50: #e91d39;
--worse-ass-60: #da762a;
--worse-ass-70: #daa13a;
--worse-ass-80: #dbc84b;
--worse-ass-90: #d3ef5e;
```
