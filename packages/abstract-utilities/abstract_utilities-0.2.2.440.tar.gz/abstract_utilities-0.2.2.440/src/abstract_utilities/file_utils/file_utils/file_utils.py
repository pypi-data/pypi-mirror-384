from pathlib import Path
from typing import *
import fnmatch, os, glob
from .filter_params import *
##from abstract_utilities import make_list,get_media_exts, is_media_type
def get_allowed_predicate(allowed=None):
    if allowed != False:
        if allowed == True:
            allowed = None
        allowed = allowed or make_allowed_predicate()
    else:
        def allowed(*args):
            return True
        allowed = allowed
    return allowed
def get_globs(items,recursive: bool = True,allowed=None):
    glob_paths = []
    items = [item for item in make_list(items) if item]
    for item in items:
        pattern = os.path.join(item, "**/*")  # include all files recursively\n
        nuItems = glob.glob(pattern, recursive=recursive)
        if allowed:
            nuItems = [nuItem for nuItem in nuItems if nuItem and allowed(nuItem)]
        glob_paths += nuItems
    return glob_paths
def get_allowed_files(items,allowed=True):
    allowed = get_allowed_predicate(allowed=allowed)
    return [item for item in items if item and os.path.isfile(item) and allowed(item)]
def get_allowed_dirs(items,allowed=False):
    allowed = get_allowed_predicate(allowed=allowed)
    return [item for item in items if item and os.path.isdir(item) and allowed(item)]

def get_filtered_files(items,allowed=None,files = []):
    allowed = get_allowed_predicate(allowed=allowed)
    glob_paths = get_globs(items)
    return [glob_path for glob_path in glob_paths if glob_path and os.path.isfile(glob_path) and glob_path not in files and allowed(glob_path)]
def get_filtered_dirs(items,allowed=None,dirs = []):
    allowed = get_allowed_predicate(allowed=allowed)
    glob_paths = get_globs(items)
    return [glob_path for glob_path in glob_paths if glob_path and os.path.isdir(glob_path) and glob_path not in dirs and allowed(glob_path)]

def get_all_allowed_files(items,allowed=None):
    dirs = get_all_allowed_dirs(items)
    files = get_allowed_files(items)
    nu_files = []
    for directory in dirs:
        files += get_filtered_files(directory,allowed=allowed,files=files)
    return files
def get_all_allowed_dirs(items,allowed=None):
    allowed = get_allowed_predicate(allowed=allowed)
    dirs = get_allowed_dirs(items)
    nu_dirs=[]
    for directory in dirs:
        nu_dirs += get_filtered_dirs(directory,allowed=allowed,dirs=nu_dirs)
    return nu_dirs
def get_files_and_dirs(
    directory: str,
    cfg: Optional["ScanConfig"] = None,
    allowed_exts: Optional[Set[str]] = False,
    unallowed_exts: Optional[Set[str]] = False,
    exclude_types: Optional[Set[str]] = False,
    exclude_dirs: Optional[List[str]] = False,
    exclude_patterns: Optional[List[str]] = False,
    add = False,
    recursive: bool = True,
    include_files: bool = True,
    **kwargs
    ):
    cfg = cfg or define_defaults(
        allowed_exts=allowed_exts,
        unallowed_exts=unallowed_exts,
        exclude_types=exclude_types,
        exclude_dirs=exclude_dirs,
        exclude_patterns=exclude_patterns,
        add=add
        )
    allowed = make_allowed_predicate(cfg)
    items=[]
    files =[]
    if recursive:
        items = get_globs(directory,recursive=recursive,allowed=allowed)
    else:
        directories = make_list(directory)
        for directory in directories:
            items +=[os.path.join(directory,item) for item in os.listdir(directory)]
    dirs = get_allowed_dirs(items,allowed=allowed)
    if include_files:
        files = get_allowed_files(items,allowed=allowed)
    return dirs,files
def make_allowed_predicate(cfg: ScanConfig) -> Callable[[str], bool]:
    def allowed(path: str) -> bool:
        p = Path(path)
        name = p.name.lower()
        path_str = str(p).lower()
        # A) directories
        if cfg.exclude_dirs:
            for dpat in cfg.exclude_dirs:
                if dpat in path_str or fnmatch.fnmatch(name, dpat.lower()):
                    if p.is_dir() or dpat in path_str:
                        return False

        if cfg.exclude_patterns:
            # B) filename patterns
            for pat in cfg.exclude_patterns:
                if fnmatch.fnmatch(name, pat.lower()):
                    return False

        # C) extension gates
        if p.is_file():
            ext = p.suffix.lower()
            if (cfg.allowed_exts and ext not in cfg.allowed_exts) or (cfg.unallowed_exts and ext in cfg.unallowed_exts):
                return False
        return True
    return allowed
def collect_filepaths(
    directory: List[str],
    cfg: ScanConfig=None,
    allowed_exts: Optional[Set[str]] = False,
    unallowed_exts: Optional[Set[str]] = False,
    exclude_types: Optional[Set[str]] = False,
    exclude_dirs: Optional[List[str]] = False,
    exclude_patterns: Optional[List[str]] = False,
    add=False,
    allowed: Optional[Callable[[str], bool]] = None,
    **kwargs
    ) -> List[str]:
    cfg = cfg or define_defaults(
                                allowed_exts=allowed_exts,
                                unallowed_exts=unallowed_exts,
                                exclude_types=exclude_types,
                                exclude_dirs=exclude_dirs,
                                exclude_patterns=exclude_patterns,
                                add = add
                                )
    allowed = allowed or make_allowed_predicate(cfg)
    directories = make_list(directory)
    roots = [r for r in directories if r]

    # your existing helpers (get_dirs, get_globs, etc.) stay the same
    original_dirs = get_allowed_dirs(roots, allowed=allowed)
    original_globs = get_globs(original_dirs)
    files = get_allowed_files(original_globs, allowed=allowed)

    for d in get_filtered_dirs(original_dirs, allowed=allowed):
        files += get_filtered_files(d, allowed=allowed, files=files)

    # de-dupe while preserving order
    seen, out = set(), []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def _fast_walk(
    root: Path,
    exts: Iterable[str],
    skip_dirs: Iterable[str] = (),
    skip_patterns: Iterable[str] = (),
) -> List[Path]:
    exts = tuple(exts)
    skip_dirs = set(sd.lower() for sd in skip_dirs or ())
    skip_patterns = tuple(sp.lower() for sp in (skip_patterns or ()))

    out = []
    for p in root.rglob("*"):
        # skip directories by name hit
        if p.is_dir():
            name = p.name.lower()
            if name in skip_dirs:
                # rglob doesn't let us prune mid-iteration cleanly; we just won't collect under it
                continue
            # nothing to collect for dirs
            continue

        # file filters
        name = p.name.lower()
        if any(fnmatch.fnmatch(name, pat) for pat in skip_patterns):
            continue
        if p.suffix.lower() in exts:
            out.append(p)

    # de-dup and normalize
    return sorted({pp.resolve() for pp in out})


def enumerate_source_files(
    src_root: Path,
    cfg: Optional["ScanConfig"] = None,
    *,
    exts: Optional[Iterable[str]] = None,
    fast_skip_dirs: Optional[Iterable[str]] = None,
    fast_skip_patterns: Optional[Iterable[str]] = None,
) -> List[Path]:
    """
    Unified enumerator:
      - If `cfg` is provided: use collect_filepaths(...) with full rules.
      - Else: fast walk using rglob over `exts` (defaults to EXTS) with optional light excludes.
    """
    src_root = Path(src_root)

    if cfg is not None:
        files = collect_filepaths([str(src_root)], cfg=cfg)
        return sorted({Path(f).resolve() for f in files})

    # Fast mode
    return _fast_walk(
        src_root,
        exts or EXTS,
        skip_dirs=fast_skip_dirs or (),
        skip_patterns=fast_skip_patterns or (),
    )
