import os,tempfile,shutil,logging,ezodf,fnmatch,pytesseract,pdfplumber
import pandas as pd
import geopandas as gpd
from datetime import datetime
from pathlib import Path
from typing import *
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from pdf2image import convert_from_path   # only used for OCR fallback
from ...abstract_classes import SingletonMeta
from ..pdf_utils import *
from ...read_write_utils import *
