#!/usr/bin/env python3
"""Serve dist under a non-root prefix; verify every published file over HTTP."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.request import urlopen
from urllib.parse import quote
import threading,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'dist';PREFIX='/showcase/'
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(D),**kw)
 def log_message(self,*a):pass
 def translate_path(self,path):
  if not path.startswith(PREFIX):return str(D/'__no_root_fallback__')
  return super().translate_path('/'+path[len(PREFIX):])
def main():
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{server.server_port}{PREFIX}'
 results=[]
 try:
  for p in sorted(D.rglob('*')):
   if not p.is_file():continue
   relative=str(p.relative_to(D));url=base+quote(relative)
   with urlopen(url) as response:
    data=response.read();assert response.status==200;assert data==p.read_bytes();results.append(dict(path=relative,status=200,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
  with urlopen(base) as response:assert b'Two copies. One rule. One clock.' in response.read()
 finally:server.shutdown();server.server_close()
 print(json.dumps(dict(status='PASS_SUBPATH_HTTP_REPLAY',prefix=PREFIX,files_checked=len(results),all_bytes_match=True,browser_rendering=False,files=results),indent=2))
if __name__=='__main__':main()
