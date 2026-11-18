"""Create blank reference-review materials for the 24 prospective cases."""
import html,json
from final_pipeline import OUT,readj,writej,sentences
rows=[r for r in readj(OUT/'prospective_split.jsonl') if r['proposed_split']=='prospective_evaluation']
blank=[];parts=['<!doctype html><meta charset="utf-8"><title>Prospective reference review</title><style>body{font:17px Georgia;max-width:1000px;margin:40px auto;line-height:1.5}article{page-break-after:always;border-top:1px solid #999;margin-top:40px;padding-top:20px}pre{white-space:pre-wrap;font:inherit}h2{font:24px Arial}</style><h1>Prospective reference review</h1><p>Confirm the publication match. Assess the entire scientific statement. Record the category, necessary action, exact evidence spans and rationale. These cases have not been human-verified or used for model-quality claims.</p>']
for r in rows:
 cid=r['example_id'];parts.append('<article><h2>'+html.escape(cid)+'</h2><p>'+html.escape(r.get('source_url',''))+'</p><h3>Original claim</h3><pre>'+html.escape(r['original_claim'])+'</pre><h3>Complete abstract with character offsets</h3>')
 for s in sentences(r['source_text']):parts.append('<p><b>['+str(s['start'])+':'+str(s['end'])+']</b> '+html.escape(s['text'])+'</p>')
 parts.append('</article>')
 blank.append({'example_id':cid,'paper_group_id':r['paper_group_id'],'source_sha256':r['source_sha256'],
  'reviewer_id':'','reviewer_provenance':'human','prior_answer_exposure':'','publication_match':'',
  'stratum':'','expected_action':'','evidence_offsets':[],'reference_revision':'','rationale':'','review_status':'pending'})
(OUT/'prospective_reference_packet.html').write_text('\n'.join(parts),encoding='utf-8');writej(OUT/'blank_prospective_reference_reviews.jsonl',blank)
print('Prepared',len(blank),'prospective reference records. Answers and identities are blank.')
