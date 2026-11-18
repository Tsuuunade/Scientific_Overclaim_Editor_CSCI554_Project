"""Make standalone scientific result figures from the saved summary."""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from source_integrity import BASE

def main():
 summary=json.loads((BASE/'summary.json').read_text());g=summary['methods'];out=BASE/'figures';out.mkdir(exist_ok=True)
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
 ms=['A_rules','B_direct_full','C_structured_curated_AI','D_structured_retrieved'];labels=['A: rules','B: direct','C: curated','D: retrieved'];colors=['#8d99ae','#457b9d','#238b79','#bc6c25']
 fig,axs=plt.subplots(1,3,figsize=(11.2,4.1))
 for ax,key,title,den in zip(axs,['S1_causal_correction','S2_unnecessary_edits','S4_correct_abstention'],['Causal claims corrected\nHigher is better','Supported claims edited\nLower is better','Source-insufficient cases: abstention\nHigher is better'],[2,5,7]):
  vals=[g[m][key]['numerator'] for m in ms];ax.bar(np.arange(4),vals,color=colors,width=.64)
  ax.set_xticks(np.arange(4),labels,rotation=28,ha='right');ax.set_ylim(0,den*1.22);ax.set_yticks(range(den+1));ax.set_title(title,fontsize=10.5);ax.set_ylabel('Cases');ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
  for i,v in enumerate(vals):ax.text(i,v+.035*den,f'{v}/{den}',ha='center',va='bottom',fontsize=10)
 fig.suptitle('Paper-separated editor feasibility study',fontsize=14,y=.99)
 fig.text(.5,.025,'24 papers. Categories and semantic ratings are automated drafts. Independent human validation is pending.',ha='center',fontsize=9)
 fig.tight_layout(rect=[0,.13,1,.90])
 for ext in ['png','svg']:fig.savefig(out/f'core_comparison.{ext}',dpi=200,bbox_inches='tight')
 plt.close(fig)
 fig,axs=plt.subplots(1,2,figsize=(7.8,4.0));matrix_methods=[['M_simple_full','M_structured_full'],['M_simple_curated_AI','C_structured_curated_AI']]
 for ax,key,title,den in zip(axs,['S3_scope_or_certainty_repair','S2_unnecessary_edits'],['Scope / certainty repairs\nHigher is better','Supported claims edited\nLower is better'],[6,5]):
  vals=np.array([[g[m][key]['numerator'] for m in row] for row in matrix_methods]);im=ax.imshow(vals,vmin=0,vmax=den,cmap='Blues',aspect='auto');ax.set_xticks([0,1],['Instruction\nremoved','Structured\ninstruction']);ax.set_yticks([0,1],['Full abstract','Curated passages']);ax.set_title(title,fontsize=11)
  for i in range(2):
   for j in range(2):ax.text(j,i,f'{vals[i,j]}/{den}',ha='center',va='center',fontsize=16,color='white' if vals[i,j]>den*.55 else '#18384d')
 fig.suptitle('Matched instruction and evidence comparison',fontsize=13,y=1.02);fig.text(.5,.01,'Same schema, renderer, model and decoding. One instruction bundle changes. Automated draft ratings.',ha='center',fontsize=8.8);fig.tight_layout(rect=[0,.07,1,.96])
 for ext in ['png','svg']:fig.savefig(out/f'matched_ablation.{ext}',dpi=200,bbox_inches='tight')
 plt.close(fig);print('Saved 4 standalone PNG/SVG figures.')
if __name__=='__main__':main()
