"""Create source-based draft references before model generation.

These annotations were made by the coding assistant after reading all 24 abstracts.
They are NOT human gold labels. Each decision and retained source passage is reviewable.
"""
from __future__ import annotations
import collections,json,sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from final_pipeline import sentences
from source_integrity import BASE,readj,sha,writej,writejson

# Case order is fixed by plan.json, not by any editor result.
# None means retain the full abstract: absence claims need full-source context.
DRAFTS=[
('S4',None,'missing_delivery_route',
 'The abstract supports the CEP290 mechanism and an optic-cup intervention. It does not establish a simple injection into the eye. This scientific delivery detail cannot be confirmed from the supplied abstract.',
 ['CEP290-related childhood blindness','optic-cup mechanism','potential intervention, not an established clinical treatment'],None,False),
('UNRESOLVED',None,'evaluative_novelty',
 'A phase 1 trial and patient responses are documented. Whether breakthrough and world-first constitute a scientific overclaim is not operationalized by the current content policy. Do not force this into a supported or causal-overclaim category.',
 ['phase 1 trial','relapsed/refractory B-cell malignancies','responses differ by malignancy'],None,False),
('UNRESOLVED',None,'virulence_endpoint_boundary',
 'Growth, attachment, biofilms and infection-relevant mechanisms are supported experimentally. The claim calls these virulence, but the abstract does not report an infection or direct virulence assay. This endpoint-label boundary requires domain review.',
 ['salad-leaf juice experimentally increases Salmonella growth','attachment and biofilm changes','laboratory evidence, not observed consumer illness'],None,False),
('S4',None,'missing_colour_result_and_conflicting_efficacy',
 'The primary visual-acuity endpoint was not significant. Post hoc subgroup secondary endpoints favored treatment. Colour sensitivity was measured but its results are not reported. A complete correction of the vision-and-colour claim cannot be verified.',
 ['randomized placebo-controlled trial','primary endpoint not significant','post hoc discordant-acuity subgroup','colour results absent'],None,False),
('S2',[1,3,7,13,14,18,19,21],'supported_hedged_intervention',
 'The claim describes potential prevention in adults with type 1 diabetes. Randomized crossover trials found less overnight hypoglycaemia and a cautious conclusion. Potential does not assert complete prevention or established routine efficacy.',
 ['artificial pancreas','potential benefit','night-time hypoglycaemia','adults with type 1 diabetes'],None,True),
('S4',None,'unverified_condition_invariance',
 'Organic milk had higher mean beneficial fatty-acid concentrations. Strong season-management interactions and weather-related variation are reported. The abstract does not give stratified comparisons sufficient to verify higher levels regardless of season or weather.',
 ['higher aggregate beneficial fatty-acid concentrations','seasonal and between-year variation','between-brand variation'],None,False),
('UNRESOLVED',None,'hedged_clinical_implication',
 'The cohort supports a continuum of pregnancy blood-pressure risk. It does not test whether a new diagnostic definition identifies additional at-risk women. The claim is explicitly hypothetical, so the boundary between a plausible implication and an unsupported clinical claim needs adjudication.',
 ['normal-pregnancy cohort','blood-pressure trajectories','risk-factor associations','no tested diagnostic benefit'],None,False),
('S4',None,'unverified_dose_and_route_equivalence',
 'The experiment used vaporized THC with specified milligram doses and a top-up. No equivalence to smoking a single spliff is established. Acute reduced effort choices are supported, but the draft dose and route cannot be verified.',
 ['acute THC experiment','17 participants','reduced high-effort choices','vaporized treatment, not verified smoking equivalence'],None,False),
('S3',[1,3,7,10,13,14,19],'population_scope',
 'Lower mortality is reported in older Medicare inpatients cared for by general internists. The claim generalizes to US patients without that clinically important age and care-setting restriction. The association and chronic-condition comparison should be preserved.',
 ['older Medicare hospital patients','general internists','lower adjusted mortality with international graduates','more chronic conditions'],
 'In the United States, older Medicare patients admitted to hospital had lower death rates when treated by internationally trained general internists than by US medical graduates, despite having more chronic conditions.',False),
('S4',None,'missing_numeric_effect',
 'The abstract supports lifespan extension in male and female fruit flies. It does not report a 16 percent effect or a low-dose comparison. These details cannot be verified by weakening the wording.',
 ['fruit flies, not human longevity','lifespan extension','16 percent absent'],None,False),
('UNRESOLVED',None,'health_implication_boundary',
 'The source recommends transport plans for increasing health-enhancing physical activity. The claim also says improving health, although clinical health outcomes were not measured. Because this is phrased as a suggested strategy, a domain reviewer should decide whether the implication exceeds the source.',
 ['repeated workplace surveys','more walking','cycling change not significant','physical activity rather than measured clinical benefit'],None,False),
('S2',[0,1,2,5,6,7,8,9],'supported_association',
 'The headline states a link, not causation or increased risk for every defect. The review finds positive associations for specific defects, with mixed directions across others. Do not reinterpret the general category birth defects as all defects.',
 ['maternal smoking','associations with specific birth defects','no causal proof'],None,False),
('S3',[0,3,6,7,8,9,12],'species_and_outcome_scope',
 'The study analyzes neural-network development in C. elegans. Human mental health was not studied. Replace the human and healthy-mental-development extrapolation with the observed worm-network relationship, without inventing a human result.',
 ['C. elegans','early-born neurons','long-distance and high-degree connectivity','suggested mechanism, not human mental-health evidence'],
 'A study of neural-network development in C. elegans suggests that early contact between neurons may help establish long-distance and highly connected networks.',False),
('S2',[1,2,3,5,6,7,10,11],'supported_animal_intervention',
 'The claim explicitly limits the demonstrated benefits to mice and describes clinical trials as a next step. The source reports significant disease-modifying effects in DMD models and says the data warrant clinical trials.',
 ['benefits in mice','DMD drug candidate','clinical trials proposed, not completed'],None,True),
('S3',[1,3,11,12,15,16,17,18,20,21,23],'age_and_eligibility_scope',
 'The evidence concerns vitamin A supplementation in children aged 6 months to 5 years, with a recommendation for those at risk of deficiency. Below five also includes younger infants. Preserve the supported mortality, illness and vision benefits while restricting the age and eligibility scope.',
 ['children aged 6 months to 5 years','risk of deficiency','mortality and specific illness/vision outcomes','potential benefit'],
 'An international review suggests that vitamin A supplementation in children aged 6 months to 5 years who are at risk of deficiency could reduce mortality, some illnesses and vision problems, particularly in low and middle income countries.',False),
('S1',[1,2,3,4,6,7,8],'causal_strength',
 'Functional networks in depressed patients were compared with healthy controls. The study observes uncoupling in depression; it does not establish that depression causes it. Preserve the observed circuit difference without assigning a causal direction.',
 ['MRI comparison','patients with depression','reduced hate-circuit connectivity','association, not established causal direction'],
 'MRI study finds reduced connectivity in the brain\'s hate circuit in patients with depression.',False),
('S3',[2,4,6,11,13,15,17,18,19,22,24,25],'treatment_and_population_scope',
 'A small randomized trial supports pain reduction after IVIG in refractory CRPS. General treatment of the immune system in all CRPS patients is broader than the studied intervention and population. Preserve the experimental benefit rather than automatically replacing it with an association.',
 ['IVIG, not any immune treatment','refractory CRPS','small randomized crossover trial','lower pain than saline','uncertain generalizability'],
 'A small randomized trial found that intravenous immunoglobulin reduced pain in patients with refractory Complex Regional Pain Syndrome, although larger studies are needed.',False),
('S1',[0,2,4,5,6,7],'causal_strength_and_conditional_relation',
 'The observational finding is that the physician-age/mortality association was absent among high-volume physicians. It does not show that treating more patients protects anyone. A correction must preserve this conditional relation rather than inventing an overall high-volume mortality reduction.',
 ['observational study','physician age and patient mortality','no age association in high-volume physicians','no established protective effect of volume'],
 'Among physicians treating high volumes of patients, physician age was not associated with patient mortality.',False),
('S4',None,'missing_clinical_outcomes',
 'The abstract characterizes severe dendritic-cell, monocyte, B-cell and NK-cell deficiencies. It does not report hereditary leukaemia or lung disease. The claim may refer to other information, but these clinical outcomes cannot be verified from this source.',
 ['immune-cell deficiency syndrome','preserved Langerhans cells and tissue macrophages','leukaemia and lung outcomes absent'],None,False),
('S3',[4,6,7,9,10,12,14,15,16,17,19],'uncertainty_and_outcome_scope',
 'No significant difference in total infarct size was found, with an interval compatible with differences. This does not prove no increase in damage. The study also found more non-IRA infarctions. Restrict the reassurance to the actual total-infarct-size finding and preserve that qualification.',
 ['randomized STEMI multivessel trial','total infarct size not significantly different','non-IRA infarctions increased','no equivalence proof'],
 'In this randomized trial of STEMI patients with multivessel disease, complete revascularization did not show a statistically significant difference in total infarct size, although non-IRA infarctions increased.',False),
('S2',[1,3,5,6,7,10,11],'supported_experimental_effect',
 'The same children viewed toy and food commercials on separate occasions and selected more fat-rich and carbohydrate-rich items after food advertising. The claim is about preference, not consumption or obesity. An automatic change from increases to is associated with would weaken this supported experimental comparison.',
 ['food versus toy commercials','children\'s reported food preferences','fat-rich and carbohydrate-rich choices','no claim of obesity or actual intake'],None,True),
('S3',[1,3,4,8,9,10,12,13,15],'mechanism_to_clinical_risk_scope',
 'In vitro LDL characteristics and rat arterial-wall deposition support increased atherogenicity. The conclusion says these may explain cardiovascular risk in diabetes. The claim states increased heart-disease risk as a consequence; preserve the mechanistic findings and qualify the clinical interpretation.',
 ['MG-modified LDL','laboratory and rat evidence','increased atherogenic characteristics','possible explanation of cardiovascular risk, not measured clinical risk increase'],
 'Scientists have identified a mechanism by which modified LDL shows increased atherogenic characteristics in laboratory studies, which may help explain higher cardiovascular risk in diabetes.',False),
('S2',[3,4,5,7,8,9,10,12],'supported_sex_specific_association',
 'The source reports higher colorectal-cancer incidence with deprivation in men but not women. The claim retains men and describes a difference rather than a causal effect. It need not repeat every location and date to report this study association.',
 ['men','deprived versus affluent areas','higher bowel-cancer incidence','association, not causation'],None,False),
('S4',None,'missing_disease_and_lives_saved_quantity',
 'The abstract validates a pancreatic-cancer risk algorithm. It does not evaluate bowel cancer or estimate thousands of lives saved. Neither a diagnostic algorithm nor cautious could wording establishes that clinical outcome and quantity.',
 ['pancreatic-cancer risk algorithm','primary-care cohort','risk prediction, not measured mortality benefit','bowel cancer and thousands of lives saved absent'],None,False)
]

def prepare():
 rows=readj(BASE/'sources/cases.jsonl');plan=json.loads((BASE/'plan.json').read_text())
 assert len(rows)==len(DRAFTS)==24
 assert [r['example_id'] for r in rows]==plan['case_ids']
 refs=[]
 for r,(cat,chosen,issue,reason,facts,correction,strong) in zip(rows,DRAFTS):
  ss=sentences(r['source_text']);chosen=list(range(len(ss))) if chosen is None else chosen
  passages=[dict(ss[k],source_sentence_id=k) for k in chosen]
  for p in passages:assert r['source_text'][p['start']:p['end']]==p['text']
  refs.append({'example_id':r['example_id'],'paper_group_id':r['paper_group_id'],'source_sha256':r['source_sha256'],
   'category':cat,'expected_action':{'S1':'revise','S2':'unchanged','S3':'revise','S4':'abstain','UNRESOLVED':None}[cat],
   'issue_type':issue,'rationale':reason,'supported_facts_to_preserve':facts,'illustrative_correction':correction,
   'strong_causal_control':strong,'curated_evidence':'\n\n'.join(p['text'] for p in passages),'curated_passages':passages,
   'curation_rule':'full abstract retained for missing-information and unresolved cases; relevant design, results and qualifications retained for other cases',
   'annotation_provenance':'coding_assistant_source_review','human_verified':False,'human_reviewer_ids':[],
   'reference_status':'PROVISIONAL_AUTOMATED_REFERENCE','uncertainty':'domain review required for all references; unresolved cases excluded only from category-specific correctness estimates, never from the output inventory'})
 path=BASE/'references.jsonl'
 if path.exists():assert path.read_text(encoding='utf-8')==''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in refs),'References are frozen; create a new study to change them.'
 else:writej(path,refs)
 freeze={'created_before_generation_utc':datetime.now(timezone.utc).isoformat(),'reference_file_sha256':sha(path.read_bytes()),
  'source_file_sha256':sha((BASE/'sources/cases.jsonl').read_bytes()),'n_cases':24,'category_counts':dict(collections.Counter(r['category'] for r in refs)),
  'strong_causal_controls':sum(r['strong_causal_control'] for r in refs),'human_verified_cases':0,'independent_human_output_ratings':0,
  'case_removal_or_replacement':False,'policy':'source fidelity, not scientific truth; no causal claim inferred from association; retain warranted experimental effects; clinical populations/outcomes matter; missing precise details require abstention; unresolved policy boundaries remain unresolved',
  'instructions_ablation_scope':'remove the ordered-assessment plus preservation/minimal-change instruction sentence bundle; all other prompt text, schema, renderer and model settings held fixed; not a test of hidden reasoning'}
 if not (BASE/'reference_freeze.json').exists():writejson(BASE/'reference_freeze.json',freeze)
 print(json.dumps(freeze,indent=2))

if __name__=='__main__':prepare()
