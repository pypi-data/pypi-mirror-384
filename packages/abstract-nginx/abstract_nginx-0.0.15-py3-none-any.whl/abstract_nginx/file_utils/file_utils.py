from pathlib import Path
from abstract_utilities import *
import glob,os,logging
from typing import List, Tuple, Dict, Iterable

BASE_PREFIX = '/run/user/1000/gvfs/sftp:host=23.126.105.154,user=root'
BACKUP_DIR = "/run/user/1000/gvfs/sftp:host=23.126.105.154,user=root/etc/nginx/sites-available/backs/"
import re
SAFE = re.compile(r'[^A-Za-z0-9_\-]')   # chars we DON’T want in a pathname

def canonical(block: str) -> str:
    """Normalise a location block: collapse whitespace, drop comments."""
    lines = [ln.split('#', 1)[0].strip()          # remove inline comments
             for ln in block.splitlines()]
    return '\n'.join(ln for ln in lines if ln)    # remove blank lines
def append_unique(conf_path: Path, block: str, seen: set[str]) -> None:
    canon = canonical(block)
    if canon in seen:
        return
    seen.add(canon)

    conf_path.parent.mkdir(parents=True, exist_ok=True)
    if conf_path.exists():
        existing = conf_path.read_text(encoding='utf-8').rstrip()
        new_body = f"{existing}\n\n{block}" if existing else block
    else:
        new_body = block
    write_to_file(contents=new_body, file_path=str(conf_path))
def loc_key(raw: str) -> str:
    """
    Turn the token after `location` into a safe directory name.

    Examples
    --------
    ~^/imgs/(.+\\.(?:jpe?g|png))$   ->  imgs
    /bolshevid/                     ->  bolshevid
    = /                             ->  root
    """
    # remove modifiers like  "~", "~*", "="
    token = raw.lstrip("~*=").lstrip()
    if token.startswith("^"):              # strip regex start
        token = token[1:]
    if token.startswith("/"):
        token = token[1:]
    # cut at first regex metachar or slash group
    token = re.split(r'[(/$]', token, 1)[0]
    return "root" if token == "" else SAFE.sub("_", token)
def remove_prefix(path: os.PathLike | str) -> str:
    """Return *string* path without the BASE_PREFIX."""
    if isinstance(str(path),list):
        path = '/'.join(str(path))
    return str(path).replace(BASE_PREFIX, '')

def make_include_str(path: os.PathLike | str) -> str:
    """nginx include line with absolute path."""
    return f"include {remove_prefix(path)};"
def get_domain_name(path):
    basename = os.path.basename(path)
    filepath,ext = os.path.splitext(basename)
    return filepath
def create_domain_directory(path):
    domain_name = get_domain_name(path)
    domain_directory = f"{BASE_PREFIX}/{sites_available}/{domain_name}"
    os.makedirs(domain_directory,exist_ok=True)
    return domain_directory
def create_domain_server_dir(path):
    domain_name = get_domain_name(path)
    server_dir = create_domain_directory(path)
    directory = f"{server_dir}/servers"
    os.makedirs(directory,exist_ok=True)
    return directory
def create_server_dir(domain_path,server):
    server_dir = create_domain_server_dir(domain_path)
    directory = f"{server_dir}/{server}"
    os.makedirs(directory,exist_ok=True)
    return directory
def if_main(raw, needle, index=-2):
    if isinstance(raw, list):
        parts = tuple(raw)
    else:
        parts = Path(os.fspath(raw)).parts
    return len(parts) >= abs(index) and parts[index] == needle
def check_for_ports(all_paths):
    good_paths = []
    for path in all_paths:
        if if_main(path,'port_configs') == None:
            good_paths.append(path)
    return good_paths or all_paths
def check_against_forbidden(file_path,forbidden):
    if isinstance(file_path,list):
        file_path = '/'.join(file_path)
    if (file_path == forbidden) or (file_path in forbidden) or (len([remove_prefix(forbid) for forbid in forbidden if remove_prefix(file_path) == remove_prefix(forbid)])>0):
        return True
    return False
def get_all_indexs(root_dir: str | Path, server: str):
    root_dir   = Path(root_dir)
    server_dir = root_dir / server          # …/servers/80   etc.

    parent_index = root_dir / 'index.conf'
    imports_path = server_dir / 'imports.conf'
    index_path   = server_dir / 'index.conf'

    # ── collect every *.conf inside this server tree ──────────────
    all_paths   = [str(p) for p in server_dir.rglob('*.conf')]
    index_paths = [remove_prefix(p) for p in all_paths]           # <—
    forbidden   = {remove_prefix(p) for p in (parent_index,
                                              imports_path,
                                              index_path)}

    # drop wrapper files
    index_paths = [p for p in index_paths if p not in forbidden]
    index_paths_copy = index_paths.copy()

    all_shorts: list[str] = []
    while index_paths_copy:
        # pick shortest, preferring “…/main/…”
        shortest = min(index_paths_copy,
                       key=lambda p: (0 if '/main/' in p else 1, len(p)))
        index_paths_copy.remove(shortest)
        all_shorts.append(f"include {shortest};")

    return all_shorts, imports_path, index_path, parent_index


def get_server_enclosure(root_dir,server):
    

    all_shorts,imports_path,index_path,parent_index = get_all_indexs(root_dir,server)    
    included_files = '\n\t'.join(all_shorts)
    
    write_to_file(contents=included_files,file_path= imports_path)
    tab = '\t'    
    wrapper = f"""
server {{
    listen {server};
    {tab}{make_include_str(imports_path)}
}}"""
    
    write_to_file(contents=wrapper,file_path = index_path)
    return index_path,parent_index
def get_all_serve(root_dir,domain_conf):
    index_paths = []
    for port in ['80','443']:
        index_path,parent_index = get_server_enclosure(root_dir,port)
        index_paths.append(make_include_str(index_path))
    parent_imports = '\n'.join(index_paths)
    sleak_parent_index = remove_prefix(parent_index)
    write_to_file(contents=parent_imports,file_path = parent_index)
    contents = f"include {remove_prefix(parent_index)}"
    write_to_file(contents=contents,file_path = domain_conf)
    
def create_incluse(path):
    for piece in os.path.split('/'):
        if piece in ['80','443']:
          server = piece
          break
    if os.path.isfile(path):
        path = path.replace(BASE_PREFIX,'')
        include_str = f"include {path};"
        contents = ""
        if os.path.iisfile(BASE_PREFIX):
            contents = read_from_file(BASE_PREFIX)
        if include_str not in contents:
            contents = f"{contents}\n{include_str}"
            write_to_file(contents=contents,file_path=BASE_PREFIX)
def join_make_prefix_path(path,path2):
    path = eatOuter(path,'/')
    path2 = eatInner(path2,'/')
    full_path = f"{path}/{path2}"
    os.makedirs(full_path,exist_ok=True)
    return full_path
def join_path_prefix(*paths):
    full_path=''
    for i,path in enumerate(paths):

        if isinstance(path,list):
            for end in path:
                join_make_prefix_path(full_path,end)
        else:
            full_path = join_make_prefix_path(full_path,path)


    return full_path 
# ── CONFIG ──────────────────────────────────────────────────────────────────
def get_configs(domain_name):
    REMOTE_CONF = (
        "/run/user/1000/gvfs/"
        "sftp:host=23.126.105.154,user=root"
        f"/etc/nginx/sites-available/backs/{domain_name}.back"
    )
    ROOT_OUT = (
        "/run/user/1000/gvfs/"
        "sftp:host=23.126.105.154,user=root"
        f"/etc/nginx/sites-available/{domain_name}/servers"
    )
    DOMAIN_OUT = (
        "/run/user/1000/gvfs/"
        "sftp:host=23.126.105.154,user=root"
        f"/etc/nginx/sites-available/{domain_name}"
    )
    DOMAIN_CONF = (
        "/run/user/1000/gvfs/"
        "sftp:host=23.126.105.154,user=root"
        f"/etc/nginx/sites-available/{domain_name}.conf"
    )
    path_parts = [BASE_PREFIX,'/etc/nginx/sites-available/',domain_name,'servers',['80','443']]
    join_path_prefix(*path_parts)

    return REMOTE_CONF,ROOT_OUT,DOMAIN_CONF


# ── LOGGING ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
log = logging.getLogger(__name__)

# ── LOW-LEVEL HELPERS ───────────────────────────────────────────────────────
def brace_split(text: str, outer_keyword: str = "server") -> List[str]:
    """
    Return each `outer_keyword { … }` block at top level, preserving nesting.
    Works even if other braces exist inside comments/strings.
    """
    blocks, buff, depth = [], [], 0
    in_outer = False
    i, n = 0, len(text)

    while i < n:
        if not in_outer and text.startswith(outer_keyword, i):
            in_outer = True

        ch = text[i]
        if in_outer:
            buff.append(ch)
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    blocks.append("".join(buff))
                    buff.clear()
                    in_outer = False
        i += 1
    return blocks


def first_token(line: str) -> str:
    return line.split(maxsplit=1)[0] if line else ""


def clean(line: str) -> str:
    return eatAll(line, [" ", "\t", "\n"])


def parse_listen(block: str) -> str | None:
    for raw in block.splitlines():
        line = clean(raw)
        if line.startswith("listen"):
            return line.split(";")[0].split()[1]
    return None

def get_port(block):
    lines = block.split('\n')
    for line in lines:
        if clean(line).startswith('proxy_pass'):
            listen_port = line.split(';')[0].split(':')[-1]
            return listen_port
def location_blocks(block: str) -> Iterable[Tuple[str, str]]:
    seen_blocks = set()
    for part in brace_split(block, "location"):
        head = part.split("{", 1)[0]
        tail = part  # full block text
        if not head.strip():
            continue

        try:
            path = head.split()[1]
        except IndexError:
            path = "/"

        # Normalize path
        if not path.startswith("/") or len(re.sub(r"[a-zA-Z]", "", path)) > len(path) * 0.8:
            path = '/rndm/'

        # Avoid exact duplicates
        if part.strip() not in seen_blocks:
            seen_blocks.add(part.strip())
            yield path, tail
def main_blocks(block: str) -> Iterable[Tuple[str, str]]:
    tail = block[len(block.split('{')[0])+1:].split('location')[0]
    path = '/main/'
    yield path, tail
def mkdir_chain(root: Path, *segments: str) -> Path:
    """
    Descend from *root*, creating every directory in *segments*.
    Each segment may itself contain slashes (e.g. 'foo/bar/baz').
    Returns the final Path.
    """
    p = root
    for seg in segments:
        if not seg:
            continue
        # split again so 'foo/bar' works
        for part in Path(seg).parts:
            if part in ("", "/"):
                continue
            p /= part
        p.mkdir(exist_ok=True)
    return p

# ── MAIN ────────────────────────────────────────────────────────────────────
def main(domain_name) -> None:
    REMOTE_CONF,ROOT_OUT,DOMAIN_CONF = get_configs(domain_name)
    raw_conf = read_from_file(REMOTE_CONF)
    servers = brace_split(raw_conf, "server")
    #input(servers)
    # … inside main(domain_name) … -------------------------------------------
    for srv in servers:
        listen_port = parse_listen(srv) or "unknown"
        main_dir    = mkdir_chain(Path(ROOT_OUT), listen_port)
        srv_dir     = mkdir_chain(main_dir, "port_configs")

        seen_rndm: set[str] = set()          # <── NEW: one per server block
        wrote_any = False
        
        for blocks in [location_blocks(srv),main_blocks(srv)]:
            for loc_path, loc_block in blocks:
                clean_dir = loc_key(loc_path)
                port      = get_port(loc_block)

                if port:
                    final_dir = mkdir_chain(srv_dir, port, clean_dir)
                else:
                    final_dir = mkdir_chain(main_dir, clean_dir)

                conf_path = final_dir / "index.conf"

                if clean_dir == "rndm":
                    append_unique(conf_path, loc_block, seen_rndm)
                else:
                    # regular locations: overwrite (or create) once
                    conf_path.parent.mkdir(parents=True, exist_ok=True)
                    write_to_file(contents=loc_block, file_path=str(conf_path))

                wrote_any = True

        # keep bodies of server{} without locations
        if not wrote_any:
            body = srv.split("{", 1)[1].rsplit("}", 1)[0]
            main_conf = mkdir_chain(main_dir, "main") / "index.conf"
            main_conf.parent.mkdir(parents=True, exist_ok=True)
            write_to_file(contents=body, file_path=str(main_conf))
    # -------------------------------------------------------------------------
            


    log.info("Done: %d server blocks processed.", len(servers))
    get_all_serve(ROOT_OUT,DOMAIN_CONF)
    

