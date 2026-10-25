"""Compute all data-derived tables and manuscript figures from stored CSV only."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import t
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/main';FIG=ROOT/'figures';TAB=ROOT/'tables'
FIG.mkdir(exist_ok=True);TAB.mkdir(exist_ok=True)

def paired(per,pol1,pol2,metric):
 a=per[per.policy==pol1].set_index('seed')[metric]
 b=per[per.policy==pol2].set_index('seed')[metric]
 d=(a-b).dropna();v=d.to_numpy();n=len(v);avg=v.mean();se=v.std(ddof=1)/np.sqrt(n)
 return {'mean_diff':float(avg),'ci_low':float(avg-t.ppf(.975,n-1)*se),'ci_high':float(avg+t.ppf(.975,n-1)*se),'n':int(n)}

def texescape(s):return str(s).replace('_',r'\_')

def main():
 dec=pd.read_csv(OUT/'decisions.csv');per=pd.read_csv(OUT/'per_seed.csv');summary=pd.read_csv(OUT/'summary.csv');sw=pd.read_csv(OUT/'sweeps.csv');proof=pd.read_csv(OUT/'proof_benchmarks.csv')
 # paired results / portable JSON summary
 comparisons=[]
 for name,other in [('fixed','fixed_two'),('entropy','entropy_two'),('random','random_two'),('always-query','adaptive_two'),('no-dp','clear_no_dp')]:
  for metric in ('regret','n_queries','attack_c_joint','recovered_kg','emissions_kg','cost_units'):
   d=paired(per,'clear_cost',other,metric)
   comparisons.append(dict(comparison=name,metric=metric,**d))
 comp=pd.DataFrame(comparisons);comp.to_csv(OUT/'paired_comparisons.csv',index=False)
 # show action conditional leakage exact in model for transcript-only actions
 subset=dec[dec.policy!='full_input_route'];delta=np.max(np.abs(subset.attack_c_joint-subset.attack_c_transcript))
 assert delta<1e-12,delta
 line=pd.read_csv(OUT/'passport_lineage.csv');assert np.abs(line.mass_residual_kg).max()<1e-10
 # Additional private-setting release risks for a full-input solver (not CLEAR)
 setting_rows=[]
 from sys import path as syspath
 syspath.insert(0,str(ROOT/'src'))
 from experiment import state_samples,outcomes
 oracle=dec[dec.policy=='full_input_route'].copy()
 for z in oracle.itertuples(index=False):
  state=np.array([z.private_c,z.private_h,z.private_q]);rng=np.random.default_rng(int(z.seed)*100000+int(z.item)+34)
  prior=state_samples(rng,1600,int(z.family))
  s_obs=round(.6*state[0]+.25*state[1],2)
  pred=np.round(.6*prior[:,0]+.25*prior[:,1],2)
  post=prior[pred==s_obs]
  if len(post)==0:post=prior[np.abs(pred-s_obs)<=.01]
  if len(post)==0:post=prior
  setting_rows.append(dict(seed=z.seed,item=z.item,setting=s_obs,c_abs_err_setting=abs(np.median(post[:,0])-state[0]),c_abs_err_route=z.attack_c_joint,c_abs_err_no_output=z.attack_c_transcript))
 setting=pd.DataFrame(setting_rows);setting.to_csv(OUT/'additional_private_setting_attack.csv',index=False)
 # produce 3-dimensional normalized multiobjective nondomination from weight scenario sweep + main results
 # Limits fixed a priori for these synthetic toy scales; higher is better in all axes
 panel=sw[sw.scenario=='weights'].groupby(['value','policy'])[['recovered_kg','emissions_kg','cost_units','regret','n_queries']].mean().reset_index()
 panel['rnorm']=np.clip(panel.recovered_kg/28,0,1)
 panel['enorm']=np.clip(1-panel.emissions_kg/150,0,1)
 panel['cnorm']=np.clip(1-panel.cost_units/225,0,1)
 Z=panel[['rnorm','enorm','cnorm']].to_numpy();nd=np.array([not any(np.all(Z[j]>=Z[i]) and np.any(Z[j]>Z[i]) for j in range(len(Z)) if i!=j) for i in range(len(Z))]);panel['nondominated']=nd
 panel.to_csv(OUT/'three_objective_pareto.csv',index=False)
 # common deterministic Sobol-like MC reference: explicitly approximate and reproducible
 rng=np.random.default_rng(1991);u=rng.uniform(0,1,(40000,3))
 hv={}
 for policy,pp in panel.groupby('policy'):
  zz=pp[['rnorm','enorm','cnorm']].to_numpy()
  dom=np.any(np.all(u[:,None,:]<=zz[None,:,:],axis=2),axis=1)
  hv[policy]=float(dom.mean())
 (OUT/'hypervolume.json').write_text(json.dumps({'definition':'Monte Carlo estimated normalized 3-objective dominated volume, reference (0,0,0), fixed R/28, 1-E/150,1-C/225; 40,000 uniform points, weight sweep only','values':hv},indent=2))
 # export compact table tex automatically
 display=['clear_cost','adaptive_two','clear_no_dp','fixed_two','entropy_two','random_two','no_disclosure','full_input_route']
 idx=summary.set_index('policy')
 rows=[]
 for p in display:
  v=idx.loc[p]
  rows.append(f"{texescape(p)} & {v['recovered_kg_mean']:.3f} & {v['emissions_kg_mean']:.2f} & {v['cost_units_mean']:.2f} & {v['regret_mean']:.3f} & {v['n_queries_mean']:.3f} & {v['attack_c_joint_mean']:.4f} \\\\")
 (TAB/'policy_rows.tex').write_text('\n'.join(rows)+'\n\\bottomrule\n')
 cr=comp[comp.comparison.isin(['fixed','always-query','entropy'])]
 rows=[]
 for x in cr.itertuples(index=False):
  rows.append(f"{texescape(x.comparison)} & {texescape(x.metric)} & {x.mean_diff:+.4f} & [{x.ci_low:+.4f}, {x.ci_high:+.4f}] \\\\")
 (TAB/'paired_rows.tex').write_text('\n'.join(rows)+'\n\\bottomrule\n')
 # Figures follow data only
 plt.rcParams.update({'font.size':10,'figure.dpi':130})
 view=idx.loc[display[:6]]
 fig,ax=plt.subplots(figsize=(8,4))
 means=view['regret_mean'].values;sem=view['regret_std'].values/np.sqrt(12)
 ax.bar(np.arange(len(view)),means,yerr=1.96*sem,capsize=3)
 ax.set_xticks(np.arange(len(view)),[x.replace('_','\n') for x in view.index]);ax.set_ylabel('Mean scalar-utility regret (lower is better)');fig.tight_layout();fig.savefig(FIG/'fig02_regret.png',dpi=180);plt.close(fig)
 fig,ax=plt.subplots(figsize=(8,4))
 ax.scatter(view.n_queries_mean,view.attack_c_joint_mean,s=90)
 for p,rr in view.iterrows():ax.annotate(p.replace('_',' '),(rr.n_queries_mean,rr.attack_c_joint_mean),xytext=(5,4),textcoords='offset points',fontsize=8)
 ax.set_xlabel('Boolean answers released per product');ax.set_ylabel('Joint-view CRM reconstruction MAE (higher means worse attacker)');fig.tight_layout();fig.savefig(FIG/'fig03_disclosure_attack.png',dpi=180);plt.close(fig)
 fig,ax=plt.subplots(figsize=(7.2,4.5))
 for p in display[:6]:
  rr=idx.loc[p];ax.scatter(rr.regret_mean,rr.attack_c_joint_mean,s=90,label=p.replace('_',' '))
 ax.set_xlabel('Mean decision regret (lower is better)');ax.set_ylabel('Joint-view CRM inference MAE (higher means worse attacker)');ax.legend(fontsize=8,loc='best');fig.tight_layout();fig.savefig(FIG/'fig04_privacy_utility.png',dpi=180);plt.close(fig)
 for scenario,figfile,ymetric,ylabel in [('budget','fig05_budget_regret.png','regret','Mean regret'),('epsilon','fig06_epsilon_regret.png','regret','Mean regret'),('shift','fig07_shift_regret.png','regret','Mean regret')]:
  ss=sw[sw.scenario==scenario].copy()
  ss['xx']=ss.value.astype(str).replace({'inf':'50'}).astype(float)
  fig,ax=plt.subplots(figsize=(7,4.5))
  for p in ['clear_cost','fixed_two','adaptive_two','clear_no_dp']:
   g=ss[ss.policy==p].groupby('xx')[ymetric].mean().sort_index()
   ax.plot(g.index,g.values,'-o',label=p.replace('_',' '))
  ax.set_xlabel({'budget':'Maximum predicate budget','epsilon':'Training histogram epsilon per attribute (50 = no noise)','shift':'Added contamination shift'}[scenario]);ax.set_ylabel(ylabel);ax.legend(fontsize=8);fig.tight_layout();fig.savefig(FIG/figfile,dpi=180);plt.close(fig)
 fig,ax=plt.subplots(figsize=(7.5,4.5))
 pp=panel[panel.policy.isin(['clear_cost','fixed_two','adaptive_two'])]
 for p,g in pp.groupby('policy'):
  ax.scatter(g.emissions_kg,g.recovered_kg,s=90,label=p.replace('_',' '));
 ax.set_xlabel('Mean emissions per product (kg CO$_2$e)');ax.set_ylabel('Mean recovered CRM (kg)');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(FIG/'fig08_3obj_projection.png',dpi=180);plt.close(fig)
 fig,ax=plt.subplots(figsize=(7.2,4.2))
 ax.boxplot([proof.prove_ms,proof.verify_ms]);ax.set_xticks([1,2],['Proof generation','Proof verification'])
 ax.set_ylabel('Runtime per proof (ms)');fig.tight_layout();fig.savefig(FIG/'fig09_proof_latency.png',dpi=180);plt.close(fig)
 fig,ax=plt.subplots(figsize=(7.5,4.5))
 m=setting[['c_abs_err_no_output','c_abs_err_route','c_abs_err_setting']].mean();ax.bar(["No output","Route-only","Route + private setpoint"],m.values)
 ax.set_ylabel('Attacker CRM fraction MAE (higher is worse attacker)');fig.tight_layout();fig.savefig(FIG/'fig10_action_leakage.png',dpi=180);plt.close(fig)
 # core mechanism schematic (draw, no stock graphics)
 fig,ax=plt.subplots(figsize=(9,5));ax.set_xlim(0,12);ax.set_ylim(0,6);ax.axis('off')
 from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
 def box(x,y,w,h,label,fc):
  ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.1',fc=fc,ec='#404850',lw=1.3));ax.text(x+w/2,y+h/2,label,ha='center',va='center',fontsize=9)
 def arrow(x,y,xx,yy):ax.add_patch(FancyArrowPatch((x,y),(xx,yy),arrowstyle='-|>',mutation_scale=15,lw=1.3,color='#404850'))
 box(.3,4.6,3,1,'BoL (composition)\nprivate firms', '#ddebf7');box(4.4,4.6,3,1,'MoL (health/history)\nprivate firms','#ddebf7');box(8.5,4.6,3,1,'EoL (process model)\nprivate firms','#ddebf7')
 box(.5,2.8,4,1,'Local histograms + DP noise\n2-share aggregation (emulated)','#fce8ca');box(6.1,2.8,5.2,1,'Commitments, signed epoch, threshold proof\nfinite-domain OR ZK (separate test)','#fce8ca')
 box(3.7,1,4.6,1,'Decision-conditioned EVSI controller\nAuthorized transcript and stop rule','#d7f1d9')
 box(9.1,.9,2.4,1.2,'Treatment route\n+ mass ledger','#e9d6eb')
 for x in (1.8,5.9,10):arrow(x,4.6,x,4)
 arrow(2.5,2.8,4.8,2.1);arrow(8.6,2.8,7.1,2.1);arrow(8.3,1.5,9.1,1.5)
 ax.text(6,0.15,'Simulated vertical partitions and horizontally distributed priors; cryptographic module tested separately',ha='center',fontsize=9)
 fig.tight_layout();fig.savefig(FIG/'fig01_architecture.png',dpi=180);plt.close(fig)
 summary_info={'main':summary.set_index('policy').to_dict('index'),'paired':comp.to_dict('records'),'proof':{'runs':int(len(proof)),'median_prove_ms':float(proof.prove_ms.median()),'median_verify_ms':float(proof.verify_ms.median()),'median_proof_bytes':float(proof.proof_bytes.median()),'all_valid':bool(proof.valid.all())},'privacy':{'max_action_additional_leakage_for_transcript_policies':float(delta),'full_private_route_attack_mae':float(idx.loc['full_input_route','attack_c_joint_mean']),'full_private_no_output_attack_mae':float(idx.loc['full_input_route','attack_c_transcript_mean']),'full_private_setting_attack_mae':float(setting.c_abs_err_setting.mean())},'mass_conservation_max_abs_residual':float(np.abs(line.mass_residual_kg).max()),'hypervolume':hv,'pareto_nondominated_counts':panel[panel.nondominated].policy.value_counts().to_dict()}
 (OUT/'statistics.json').write_text(json.dumps(summary_info,indent=2))
 print('Wrote 9 plots, 2 LaTeX tables, paired CIs, action attacks, approximate Pareto and all statistics.');print(comp[(comp.comparison=='fixed')].to_string(index=False))

if __name__=='__main__':main()
