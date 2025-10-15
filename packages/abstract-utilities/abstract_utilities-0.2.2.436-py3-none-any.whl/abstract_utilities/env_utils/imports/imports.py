import os
from dotenv import load_dotenv
from ...string_clean import eatAll,eatInner,eatOuter,safe_split
from ...compare_utils import line_contains
from ...type_utils import is_list,is_bool
from ...path_utils import get_slash,path_join,if_not_last_child_join,get_home_folder,simple_path_join,is_file
DEFAULT_FILE_NAME = '.env'
DEFAULT_KEY = 'MY_PASSWORD'
