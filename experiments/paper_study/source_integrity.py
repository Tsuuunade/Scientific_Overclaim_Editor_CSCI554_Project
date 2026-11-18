"""Lossless source recovery and pre-generation plan for the 24-paper study."""
from __future__ import annotations
import argparse,concurrent.futures,difflib,hashlib,json,re,subprocess,sys,unicodedata,urllib.parse
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/paper_study'
OLD=ROOT/'experiments/results'

def sha(x):return hashlib.sha256(x if isinstance(x,bytes) else x.encode('utf-8')).hexdigest()
def readj(p):return [json.loads(x) for x in Path(p).read_text(encoding='utf-8-sig').splitlines() if x.strip()]
def writej(p,rows):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf-8')
def writejson(p,obj):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

class SourceTextParser(HTMLParser):
    BLOCK={'h1','h2','h3','h4','h5','p','div','br','li','section'}
    def __init__(self):super().__init__(convert_charrefs=True);self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in self.BLOCK:self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in self.BLOCK:self.parts.append('\n')
    def handle_data(self,data):self.parts.append(data)

def source_text(raw):
    p=SourceTextParser();p.feed(raw);p.close()
    # Preserve scientific text and comparison signs; normalize display whitespace only.
    return '\n'.join(' '.join(line.split()) for line in ''.join(p.parts).splitlines() if line.strip())

def norm(text):
    text=unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower()
    return ' '.join(re.findall(r'[a-z0-9]+',text))

def plan():
    BASE.mkdir(parents=True,exist_ok=True)
    pool=readj(OLD/'prospective_split.jsonl');cases=[r for r in pool if r['proposed_split']=='prospective_evaluation']
    dev={r['paper_group_id'] for r in pool if r['proposed_split']=='development'}
    assert len(cases)==24 and len({r['paper_group_id'] for r in cases})==24
    assert not dev&{r['paper_group_id'] for r in cases}
    value={'study_id':'paper_separated_24_v1','planned_before_generation_utc':datetime.now(timezone.utc).isoformat(),
      'case_ids':[r['example_id'] for r in cases],'paper_ids':[r['paper_group_id'] for r in cases],
      'development_paper_ids':sorted(dev),'paper_id_overlap':0,'sample_selection':'existing prospective split retained; no replacement based on model performance',
      'source_fix':'HTMLParser preserves mathematical < and >; original provider responses retained',
      'references':'assistant-generated source-based drafts before generation; zero completed human reviews on new cases',
      'execution_mode':'automated-reference feasibility evaluation; not human-validated',
      'conditions':['A_rules','B_direct_full','C_structured_curated_AI','M_simple_full','M_structured_full','M_simple_curated_AI','D_structured_retrieved'],
      'core_order':['A_rules','B_direct_full','C_structured_curated_AI'],
      'controlled_ablation':'2x2 instruction (simple/structured) by evidence (full/curated); same schema, indexing, renderer, validator, model and decoding',
      'retrieval_comparison':'C vs D uses the same structured workflow; curated reference passages are AI-selected pending human verification',
      'model':'Qwen/Qwen2.5-7B-Instruct-GGUF','revision':'bb5d59e06d9551d752d08b292a50eb208b07ab1f','quantization':'Q4_K_M','runtime':'llama.cpp b12483 CUDA 12.4',
      'temperature':0,'seed':42,'max_tokens':512,'context_size':4096,'fine_tuned':False,
      'rules':'existing fixed_rules_v1 unchanged','structured_prompt':'existing structured_v2 unchanged','direct_prompt':'existing direct_v2 unchanged',
      'simple_matched_prompt':'same task policy and JSON output contract; remove the ordered inspection instructions only',
      'ratings':'method identifiers masked for assistant output assessment; not two independent human reviewers',
      'primary_metrics':['S1 correction success','S2 unnecessary edits','S2 harmful weakening','non-abstained factual preservation','abstention by category'],
      'failures':'remain in denominators; never count as semantic success; no automatic retries or repairs',
      'case_exposure':'candidate claims were visible during source recovery; no prior model outputs on these 24; no prompt tuning after freeze',
      'claim_scope':'paper-separated machine-assessed feasibility; no population accuracy or human-validation claim'}
    path=BASE/'plan.json'
    if path.exists():
        existing=json.loads(path.read_text())
        assert existing['case_ids']==value['case_ids'];print('Existing pre-generation plan retained.')
    else:writejson(path,value)
    before={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts and 'paper_study' not in p.parts}
    if not (BASE/'prior_artifact_hashes.json').exists():writejson(BASE/'prior_artifact_hashes.json',before)
    print('Registered 24 papers with zero overlap with the 17 development papers.')

def recover_one(r):
    pmid=r['paper_group_id'].split(':')[1]
    rawfile=BASE/'sources/raw'/f'{pmid}.json';rawfile.parent.mkdir(parents=True,exist_ok=True)
    if not rawfile.exists():
        url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?'+urllib.parse.urlencode({'query':f'EXT_ID:{pmid} AND SRC:MED','format':'json','resultType':'core','pageSize':2})
        p=subprocess.run(['curl.exe','-f','-L','--silent','--show-error','--retry','2','--connect-timeout','20','--max-time','90',url],capture_output=True)
        if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
        data=json.loads(p.stdout);data['_source_request_url']=url;writejson(rawfile,data)
    raw=rawfile.read_bytes();data=json.loads(raw)
    found=[x for x in data['resultList']['result'] if x.get('pmid',x.get('id'))==pmid and x.get('source')=='MED']
    assert len(found)==1,pmid
    article=found[0];html=article['abstractText'];text=source_text(html)
    assert norm(r['aligned_abstract_conclusion']) in norm(text),r['example_id']
    unsafe=[m.group(0) for m in re.finditer(r'<[^>]+>',html) if not re.match(r'</?[A-Za-z][A-Za-z0-9]*(?:\s[^>]*)?/?>$',m.group(0))]
    return dict(r,source_text=text,source_sha256=sha(text),source_parser='HTMLParser-v1',source_raw_path=str(rawfile.relative_to(BASE)),source_raw_sha256=sha(raw),
      source_request_url=data['_source_request_url'],article_title=source_text(article['title']),doi=article.get('doi'),pmid=pmid,
      old_source_sha256=r['source_sha256'],old_source_chars=len(r['source_text']),new_source_chars=len(text),
      old_regex_would_remove_plain_scientific_text=[{'length':len(x),'preview':x[:180]} for x in unsafe],
      publication_match='automatic exact PMID plus normalized aligned-excerpt containment',human_verified=False)

def recover():
    wanted=json.loads((BASE/'plan.json').read_text())['case_ids'];pool=readj(OLD/'prospective_split.jsonl')
    rows=[r for r in pool if r['example_id'] in wanted]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:result=list(ex.map(recover_one,rows))
    writej(BASE/'sources/cases.jsonl',result)
    fixes=[{'example_id':r['example_id'],'old_chars':r['old_source_chars'],'new_chars':r['new_source_chars'],'removed_chunks':r['old_regex_would_remove_plain_scientific_text']} for r in result if r['old_regex_would_remove_plain_scientific_text']]
    writejson(BASE/'sources/integrity_report.json',{'n_cases':len(result),'matched_paper_ids':len({r['paper_group_id'] for r in result}),'scientific_text_loss_cases_fixed':len(fixes),'fixes':fixes,'raw_original_files_overwritten':False,'source_jsonl_sha256':sha((BASE/'sources/cases.jsonl').read_bytes())})
    print('Recovered',len(result),'complete sources;',len(fixes),'had text at risk under the old regex.')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('command',choices=['plan','recover']);args=ap.parse_args()
    plan() if args.command=='plan' else recover()
