#!/usr/bin/env python3
# gui_frontend.py (with a toggleable log console)
from __future__ import annotations

# ─── Standard library ─────────────────────────────────────────────────────────
import ast,datetime,json,os,glob,re,sys,traceback
from pathlib import Path



import pytesseract
from pdf2image import convert_from_path

# ─── Local application ─────────────────────────────────────────────────────────
from abstract_pandas import get_df
from abstract_utilities import (SingletonMeta,
                                get_logFile,
                                read_from_file,
                                make_list
                                )
from abstract_gui.QT6 import*
from PyQt6 import QtGui
from abstract_paths import *
