import os,time,random,hashlib,shutil
from flask import (Blueprint,
                   request,
                   render_template_string,
                   url_for,
                   jsonify
                   )
from abstract_utilities import SingletonMeta
from abstract_pandas import (get_df,
                             safe_excel_save,
                             is_file)
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

import os, re, json
from abstract_utilities import eatAll,read_from_file,write_to_file,safe_dump_to_json
from abstract_utilities.file_utils import *
