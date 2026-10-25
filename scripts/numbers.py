from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
s=json.load(open(R/'outputs/main/statistics.json'))
v=s['main'];p=s['paired'];pr=s['proof'];hv=s['hypervolume'];priv=s['privacy']
def get(base,metric):return next(x for x in p if x['comparison']==base and x['metric']==metric)
def f(x,n=3):return f'{x:.{n}f}'
D={
'FixedRegret':f(v['fixed_two']['regret_mean']),
'ClearRegret':f(v['clear_cost']['regret_mean']),
'ClearQueries':f(v['clear_cost']['n_queries_mean']),
'RegretDiff':f(get('fixed','regret')['mean_diff']),
'RegretCIlo':f(get('fixed','regret')['ci_low']),
'RegretCIhi':f(get('fixed','regret')['ci_high']),
'RegretPercent':f(100*(1-v['clear_cost']['regret_mean']/v['fixed_two']['regret_mean']),1),
'QueryPercent':f(100*(1-v['clear_cost']['n_queries_mean']/2),1),
'RecoveredDiff':f(get('fixed','recovered_kg')['mean_diff']),
'AlwaysRegret':f(v['adaptive_two']['regret_mean']),
'AlwaysRegretDiff':f(get('always-query','regret')['mean_diff']),
'AlwaysRegretCIlo':f(get('always-query','regret')['ci_low']),
'AlwaysRegretCIhi':f(get('always-query','regret')['ci_high']),
'ClearMAE':f(v['clear_cost']['attack_c_joint_mean'],4),
'FixedMAE':f(v['fixed_two']['attack_c_joint_mean'],4),
'AlwaysMAE':f(v['adaptive_two']['attack_c_joint_mean'],4),
'MAEDiff':f(get('fixed','attack_c_joint')['mean_diff'],4),
'MAECIlo':f(get('fixed','attack_c_joint')['ci_low'],4),
'MAECIhi':f(get('fixed','attack_c_joint')['ci_high'],4),
'OraclePriorMAE':f(priv['full_private_no_output_attack_mae'],4),
'OracleRouteMAE':f(priv['full_private_route_attack_mae'],4),
'OracleSettingMAE':f(priv['full_private_setting_attack_mae'],4),
'ProofN':str(pr['runs']),
'ProofTime':f(pr['median_prove_ms'],1),
'VerifyTime':f(pr['median_verify_ms'],1),
'ProofBytes':f(pr['median_proof_bytes'],0),
'MassResidual':f(s['mass_conservation_max_abs_residual'],3),
'FixedHV':f(hv['fixed_two'],4),
'ClearHV':f(hv['clear_cost'],4),
'AlwaysHV':f(hv['adaptive_two'],4),
'EntropyHV':f(hv['entropy_two'],4),
'OracleHV':f(hv['full_input_route'],4),
}
(R/'tables/numbers.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in D.items())+'\n')
print('stats macros',len(D))
