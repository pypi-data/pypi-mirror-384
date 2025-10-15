#!/usr/bin/env python3
from .imports import *
# -----------------------
# Utility: safe symlink
# -----------------------
def safe_symlink(src, dst):
    """Create symlink if not already valid; replace if dangling."""
    try:
        if not os.path.exists(src):
            print(f"[WARN] Missing source: {src}")
            return

        # If destination exists and is correct, skip
        if os.path.islink(dst):
            existing = os.readlink(dst)
            if os.path.abspath(existing) == os.path.abspath(src):
                return
            os.remove(dst)
        elif os.path.exists(dst):
            os.remove(dst)

        # Create relative symlink when possible
        rel_src = os.path.relpath(src, os.path.dirname(dst))
        os.symlink(rel_src, dst)
        print(f"[+] Linked {dst} -> {rel_src}")
    except Exception as e:
        print(f"[WARN] Could not link {dst} -> {src}: {e}")

# -----------------------
# Utility: extract port info from .service
# -----------------------
def parse_service_file_regex(file_path):
    """Return dict with relevant info if Flask/Gunicorn-like."""
    content = read_from_file(file_path)
    
    workdir = re.search(r"WorkingDirectory=(.*)", content)
    exec_line = re.search(r"ExecStart=(.*)", content)
    if not match or not workdir:
        return None
    port = match.group(1)
    dirname = workdir.group(1).strip()
    filename = os.path.splitext(os.path.basename(file_path))[0]
    return {
        "port": port,
        "dirname": dirname,
        "filename": filename,
        "path": file_path,
        "exec": exec_line.group(1).strip() if exec_line else "",
    }

# -----------------------
# Build Nginx snippet
# -----------------------
def make_flask_proxy(name, port, local_host=None):
    local_host = local_host or LOCAL_HOST
    return f"""
# === Flask API ===
location /{name}/ {{
    proxy_pass         {local_host}:{port};
    proxy_http_version 1.1;
    proxy_set_header   Host $host;
    proxy_set_header   X-Real-IP $remote_addr;
    proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;
    client_max_body_size 2G;
    proxy_read_timeout   3600s;
    proxy_send_timeout   3600s;
    proxy_connect_timeout 600s;
    proxy_buffering off;
}}
""".strip()
def get_lines(file_path):   
    if isinstance(file_path,str):
        contents = read_from_file(file_path)
    else:
        contents = '\n'.join(file_path)
        
    conts = contents.replace('\n',';')
    conts = conts.replace(';;',';')
    lines = conts.split(';')
    return lines
def get_includes(file_path):
    nulines = []
    
    lines = get_lines(file_path)
    for i,line in enumerate(lines):
        line = eatAll(line,[' ','\t',''])
        if line.startswith('include '):
            out = get_includes(line.split('include ')[-1])
            if isinstance(out,list):
                out = '\n'.join(out)
            lines[i] = out
    return lines
def get_full_confs(file_path=None,user_at_host=None):

    lines = get_includes(file_path)
    lines = '\n'.join(lines)
    tabs=0
    tab = ''
    lines = [line for line in lines.split('\n') if line]
    for i,line in enumerate(lines):
        line = eatAll(line,[' ','\t','','\n'])
        
        if line.endswith('{'):
            lines[i]=f"{tab}{line}"
            tab +='\t'
        elif line.endswith('}'):
            tab  = tab[:-len('\t')]
            lines[i]=f"{tab}{line}\n"
        else:
            lines[i]=f"{tab}{line}{';' if line else ''}"
    return lines

def parse_service_file(file_path):
        content = read_from_file(file_path)
        lines = content.split('\n')
        contents_js = {}
        section = None
        section_key = None
        for line in lines:
            if line and not line.startswith('#'):
                if section != None:
                    if line[-1] == '\\' and section_key != None:
                        contents_js[section][section_key].append(line)
                    else:
                        line_spl = line.split('=')
                        section_key = line_spl[0]
                        section_val = '='.join(line_spl[1:])
                        if section_key not in contents_js[section]:
                            contents_js[section][section_key] = []
                        contents_js[section][section_key].append(section_val)
                if line.startswith('['):
                    section = line.split('[')[1].split(']')[0]
                    contents_js[section] = {}
                    
        ExecStartText = ''.join(make_list(get_any_value(contents_js,'ExecStart') or []))
        host_and_port = find_host_and_port(ExecStartText)
        if host_and_port:
            host = host_and_port.get('host')
            port = host_and_port.get('port')
            WorkingDirectory = contents_js.get('WorkingDirectory')
            exec_ = os.path.join(WorkingDirectory,filename)
            host_port = f"{host}:{port}"
            filename = ExecStartText.split(host_port)[1].split(' ')[1].split(':')[0]
            contents_js.update(host_and_port)
            contents_js['path'] = file_path
            contents_js['filename'] = filename
            contents_js['dirname'] = WorkingDirectory
            contents_js['exec'] = exec_
        return contents_js
