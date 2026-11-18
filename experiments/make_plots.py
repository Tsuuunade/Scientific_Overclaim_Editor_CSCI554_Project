"""Export standalone presentation figures from recorded counts, without making slides."""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from final_pipeline import OUT

report=json.loads((OUT/'runs/development_v2/summary.json').read_text())
out=OUT/'figures';out.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
methods=['A','B','C','D_v1','D_v2','D_matched'];labels=['Rules','Direct','Reviewed\nevidence','Top 2','Neighbors','Top-k\nmatched']
counts=[report['methods'][m]['unnecessary_edits_on_clean_supported_controls']['numerator'] for m in methods]
fig,ax=plt.subplots(figsize=(10,5.2));bars=ax.bar(labels,counts,color=['#75818A','#1F668C','#B8633C','#B8633C','#B8633C','#B8633C'],width=.62)
ax.set_ylim(0,2.65);ax.set_yticks([0,1,2]);ax.set_ylabel('Supported claims changed (out of 2)');ax.set_title('Unnecessary edits on two reviewer-supported controls',loc='left',fontweight='bold',pad=20)
for b,n in zip(bars,counts):ax.text(b.get_x()+b.get_width()/2,n+.08,f'{n}/2',ha='center',fontweight='bold',fontsize=13)
fig.text(.12,.035,'Development feasibility only. Controls: CAL-02 and CAL-07. Not held-out performance.',fontsize=10,color='#4B5563')
fig.subplots_adjust(bottom=.2,top=.82,left=.12,right=.98)
for ext in ('png','svg'):fig.savefig(out/f'control_edits.{ext}',dpi=180)
plt.close(fig)
fig,ax=plt.subplots(figsize=(8,5.2));vals=[0,report['methods']['C']['valid_outputs']['numerator']]
bars=ax.bar(['Original structured\nworkflow','Indexed evidence +\nconstrained JSON'],vals,color=['#75818A','#1F668C'],width=.5)
ax.set_ylim(0,9.8);ax.set_yticks([0,2,4,6,8]);ax.set_ylabel('Structurally valid C outputs (out of 8)');ax.set_title('Output validation improved after an implementation change',loc='left',fontweight='bold',fontsize=13,pad=20)
for b,n in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,n+.25,f'{n}/8',ha='center',fontweight='bold')
fig.text(.12,.035,'Schema validity does not establish semantic correctness. Different development workflows.',fontsize=9.5,color='#4B5563')
fig.subplots_adjust(bottom=.22,top=.82,left=.12,right=.98)
for ext in ('png','svg'):fig.savefig(out/f'schema_validity.{ext}',dpi=180)
plt.close(fig);print('Saved PNG and SVG result figures in experiments/results/figures')
