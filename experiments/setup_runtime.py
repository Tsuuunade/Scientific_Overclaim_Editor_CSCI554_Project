from pathlib import Path
import subprocess,concurrent.futures,hashlib,json,zipfile,time,argparse,tempfile
parser=argparse.ArgumentParser(description='Download pinned official Qwen GGUF and Windows CUDA runtime outside the repo.')
parser.add_argument('--cache-dir',default=str(Path(tempfile.gettempdir())/'overclaim_model_cache'))
ROOT=Path(parser.parse_args().cache_dir).resolve()
ROOT.mkdir(parents=True,exist_ok=True)
MODEL_REV='bb5d59e06d9551d752d08b292a50eb208b07ab1f'
JOBS=[
 ('llama-b12483-bin-win-cuda-12.4-x64.zip','https://github.com/ggml-org/llama.cpp/releases/download/b12483/llama-b12483-bin-win-cuda-12.4-x64.zip',None),
 ('cudart-llama-bin-win-cuda-12.4-x64.zip','https://github.com/ggml-org/llama.cpp/releases/download/b12483/cudart-llama-bin-win-cuda-12.4-x64.zip',None),
 ('qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf',f'https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/{MODEL_REV}/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf','dfce12e3862a5283ccfb88221b48480e58745165de856439950d0f22590580db'),
 ('qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf',f'https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/{MODEL_REV}/qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf','539cf93f78e887edea1c04e2d7d8cdaca9d01dae9c9025bcb8accbe29df3d72a')]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def job(item):
 name,url,expected=item;p=ROOT/name
 if not p.exists():
  part=p.with_suffix(p.suffix+'.part')
  cmd=['curl.exe','--location','--fail','--retry','4','--retry-delay','3','--silent','--show-error','--connect-timeout','30','--output',str(part),url]
  with (ROOT/(name+'.download.log')).open('w') as log:
   result=subprocess.run(cmd,stdout=log,stderr=log)
  if result.returncode:raise RuntimeError('Download failed: '+name)
  part.replace(p)
 digest=sha(p)
 if expected and digest!=expected:raise RuntimeError('Checksum mismatch: '+name)
 if name.endswith('.zip'):
  dest=ROOT/'llama';dest.mkdir(exist_ok=True)
  with zipfile.ZipFile(p) as z:
   for info in z.infolist():
    target=(dest/info.filename).resolve()
    if target!=dest.resolve() and dest.resolve() not in target.parents:raise RuntimeError('Unsafe archive path')
   z.extractall(dest)
 print('READY',name,p.stat().st_size,flush=True)
 return {'filename':name,'url':url,'sha256':digest,'bytes':p.stat().st_size}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 records=list(pool.map(job,JOBS))
(ROOT/'runtime_download_manifest.json').write_text(json.dumps({'model_revision':MODEL_REV,'llama_release':'b12483','files':records},indent=2)+'\n')
print('BOOTSTRAP COMPLETE',flush=True)
