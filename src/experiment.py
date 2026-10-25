"""CLEAR-CRM integrated *synthetic* benchmark.

Methods referred to as 'full-input route', 'DP pooled prior', and 'fixed disclosure'
are explicit proxies, NOT reimplementations of published algorithms.  No industrial
model or secure remote execution is claimed. All seeds and outputs are stored.
"""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

FEATURES=('crm_fraction','state_of_health','contamination')
ACTIONS=('mechanical','selective','hydro')
THRESHOLDS=((0,.095),(0,.14),(0,.19),(0,.245),(1,.48),(1,.66),(1,.81),(2,.16),(2,.27),(2,.35))
POLICIES=('no_disclosure','random_two','fixed_two','entropy_two','adaptive_two','clear_cost','clear_no_dp','full_input_route')
GRID=32
CARBON_KM=np.array([19.,35.,61.])
WEIGHTS=(12.,.25,.32)

def state_samples(rng,n,family,shift=0.):
    if family==0:
        c=rng.beta(3.2,5.3,n)*.34+.035
        h=rng.beta(5.,2.7,n)*.75+.2
        q=rng.beta(2.,6.,n)*.46
    else:
        c=rng.beta(4.1,3.8,n)*.32+.045
        h=rng.beta(2.9,3.3,n)*.74+.2
        q=rng.beta(3.1,3.7,n)*.47
    return np.column_stack((c,h,np.clip(q+shift,0,1)))

def outcomes(s,mass,weights=WEIGHTS):
    """Declared toy assumptions; no inferred physical calibration."""
    s=np.atleast_2d(s); c,h,q=s.T
    y=np.column_stack((.66+.08*h-.12*q,.51+.45*h-.075*q,.94-.06*q))
    y[(q>.29)&(h<.55),2]*=.51
    recovered=mass*c[:,None]*y
    emissions=mass*np.array([.30,.49,.78])[None,:]+recovered*np.array([.65,.48,.88])[None,:]
    costs=mass*np.array([.58,.80,1.19])[None,:]+recovered*np.array([.24,.35,.45])[None,:]
    emissions+=CARBON_KM[None,:]*(.08+.0015*recovered)
    costs+=CARBON_KM[None,:]*.06
    wR,wE,wC=weights
    utility=wR*recovered-wE*emissions-wC*costs
    return recovered,emissions,costs,utility

def predicate(s,qi):
    col,cut=THRESHOLDS[qi]
    return np.atleast_2d(s)[:,col]>=cut

def local_dp_hist(rng,epsilon=2.,clients=4,training_per_client=550,non_iid=True):
    """Disjoint client-level vector histograms. One row contributes to three
    attributes, so per-record composed bound <= 3*epsilon for add/remove
    adjacency. If each physical actor holds its own attribute, it is epsilon
    for that feature's owner; no query/decision-output DP claim.
    Noise is added at client before simulated integer secret-sharing aggregation.
    """
    training=[]; aggregate=np.zeros((2,3,GRID))
    pooled=np.zeros_like(aggregate)
    P=(1<<61)-1; scale=100000
    # shared integer envelopes, no persistence of simulated client secrets
    share0=np.zeros_like(aggregate,dtype=np.int64)
    share1=np.zeros_like(aggregate,dtype=np.int64)
    for family in range(2):
        for client in range(clients):
            s=state_samples(rng,training_per_client,family)
            # non-IID sampling from locally shifted product experience
            if non_iid:
                offsets=np.array([(client-1.5)*.002,(client-1.5)*.008,(client-1.5)*.006])
                s=np.clip(s+offsets[None,:],0,1)
            training.append(pd.DataFrame({'family':family,'client':client,'c':s[:,0], 'h':s[:,1], 'q':s[:,2]}))
            for feat in range(3):
                hist,_=np.histogram(s[:,feat],bins=GRID,range=(0,1))
                pooled[family,feat]+=hist
                n=hist.astype(float)
                if np.isfinite(epsilon):
                    n+=rng.laplace(0,1/epsilon,size=GRID)
                # postprocessing of noisy histogram
                quant=np.rint(n*scale).astype('int64')
                mask=rng.integers(0,10**9,size=GRID,dtype='int64')
                share0[family,feat]=(share0[family,feat]+mask)%P
                share1[family,feat]=(share1[family,feat]+(quant-mask))%P
    recovered=(share0+share1)%P
    recovered=np.where(recovered>P//2,recovered-P,recovered)/scale
    aggregate=np.clip(recovered,0,None)
    aggregate+=.05
    aggregate/=aggregate.sum(axis=2,keepdims=True)
    pooled=pooled+.05
    pooled=pooled/pooled.sum(axis=2,keepdims=True)
    return aggregate,pooled,pd.concat(training,ignore_index=True)

def particles(rng,hist,family,n):
    cols=[]
    for j in range(3):
        idx=rng.choice(GRID,size=n,p=hist[family,j]); cols.append((idx+rng.random(n))/GRID)
    return np.column_stack(cols)

def query_value(posterior,util,used,mode):
    base=np.max(util.mean(axis=0)); best_q=None; best=-np.inf
    for qi in range(len(THRESHOLDS)):
        if qi in used: continue
        mask=predicate(posterior,qi)
        p=mask.mean()
        if p<.035 or p>.965: continue
        if mode=='entropy': gain=-(p*np.log2(p)+(1-p)*np.log2(1-p))
        else: gain=p*np.max(util[mask].mean(axis=0))+(1-p)*np.max(util[~mask].mean(axis=0))-base
        if gain>best:best=gain;best_q=qi
    return best_q,float(best)

def decide(policy,state,mass,p0,rng,budget=2,query_cost=.7,weights=WEIGHTS):
    transcript=[]; post=p0
    if policy=='full_input_route':
        return int(np.argmax(outcomes(state,mass,weights)[-1][0])),transcript
    if policy=='no_disclosure':budget=0
    for step in range(budget):
        if policy=='fixed_two': qi=([1,5,8,2][step%4])
        elif policy=='random_two':qi=int(rng.choice([i for i in range(len(THRESHOLDS)) if i not in [x[0] for x in transcript]]))
        else:
            u=outcomes(post,mass,weights)[-1]
            qi,gain=query_value(post,u,[x[0] for x in transcript],'entropy' if policy=='entropy_two' else 'evsi')
            if qi is None or (policy in ('clear_cost','clear_no_dp') and gain<=query_cost):break
        ans=int(predicate(state,qi)[0]);transcript.append((qi,ans))
        mask=predicate(post,qi)==bool(ans)
        if mask.any():post=post[mask]
        if len(post)<2:break
    a=int(np.argmax(outcomes(post,mass,weights)[-1].mean(axis=0)))
    return a,transcript

def adversary(state,mass,family,transcript,action,attack_prior,policy,weights):
    post=attack_prior.copy()
    for q,ans in transcript:
        mask=predicate(post,q)==bool(ans)
        if mask.any():post=post[mask]
    estimate_t=np.median(post,axis=0)
    # Full-input baseline's route is a private-state function; invert it.
    # For pure transcript-based decision policies, the released action is a
    # deterministic post-processing of transcript+public DPP+public model.
    # It therefore cannot add information in the ideal setting.
    if policy=='full_input_route':
        routes=np.argmax(outcomes(post,mass,weights)[-1],axis=1)
        match=routes==action
        if match.any():post=post[match]
    estimate_joint=np.median(post,axis=0)
    return estimate_t,estimate_joint

def one_run(seed,products=140,nparticles=320,epsilon=2.,budget=2,shift=0.,weights=WEIGHTS,train_clients=4):
    rng=np.random.default_rng(seed)
    hist,pooled,train=local_dp_hist(rng,epsilon=epsilon,clients=train_clients)
    result=[]; lineage=[]
    for i in range(products):
        family=int(rng.integers(0,2)); mass=float(rng.uniform(60,140))
        state=state_samples(rng,1,family,shift=shift)
        posterior=particles(rng,hist,family,nparticles)
        posterior_raw=particles(rng,pooled,family,nparticles)
        # attacker has independent, strong distributional side information
        attacker=state_samples(np.random.default_rng(seed*100000+i+34),1200,family)
        rec,emis,cost,util=outcomes(state,mass,weights)
        oracle=int(np.argmax(util[0]));uopt=float(util[0,oracle])
        for pol in POLICIES:
            r0=np.random.default_rng(seed*10000000+i*127+sum(map(ord,pol)))
            pp=posterior_raw if pol=='clear_no_dp' else posterior
            a,tr=decide(pol,state,mass,pp,r0,budget,query_cost=.7,weights=weights)
            at,aj=adversary(state,mass,family,tr,a,attacker,pol,weights)
            row=dict(seed=seed,item=i,family=family,policy=pol, mass=float(mass), private_c=float(state[0,0]),private_h=float(state[0,1]),private_q=float(state[0,2]),action=ACTIONS[a],oracle_action=ACTIONS[oracle],recovered_kg=float(rec[0,a]),emissions_kg=float(emis[0,a]),cost_units=float(cost[0,a]),utility=float(util[0,a]),regret=float(uopt-util[0,a]),n_queries=len(tr),query_ids=';'.join(str(q) for q,b in tr),answers=''.join(str(b) for q,b in tr),attack_c_transcript=float(abs(at[0]-state[0,0])),attack_c_joint=float(abs(aj[0]-state[0,0])),attack_h_joint=float(abs(aj[1]-state[0,1])),attack_q_joint=float(abs(aj[2]-state[0,2])),epsilon_feature=epsilon,shift=shift,weights=str(tuple(weights)))
            result.append(row)
            if pol=='clear_cost':
                crm_in=mass*state[0,0];r=float(rec[0,a]); residue=float(crm_in-r)
                lineage.append(dict(seed=seed,item=i,parent=f'P{seed}_{i}',parent_active=False,child_recovered=f'R{seed}_{i}',child_residue=f'W{seed}_{i}',crm_input_kg=crm_in,recovered_kg=r,residue_kg=residue,mass_residual_kg=crm_in-r-residue))
    return pd.DataFrame(result),pd.DataFrame(lineage),train,hist

def aggregate(df):
    metrics=['recovered_kg','emissions_kg','cost_units','utility','regret','n_queries','attack_c_transcript','attack_c_joint','attack_h_joint','attack_q_joint']
    per=df.groupby(['seed','policy'])[metrics].mean().reset_index()
    summary=per.groupby('policy')[metrics].agg(['mean','std'])
    summary.columns=['_'.join(x) for x in summary.columns]
    return per,summary.reset_index()

def run(args):
    target=Path(args.output);target.mkdir(parents=True,exist_ok=True)
    all_df=[];all_l=[];train_sample=None;hist_example=None
    for seed in range(args.start_seed,args.start_seed+args.seeds):
        df,l,train,hist=one_run(seed,args.products,args.particles,args.epsilon,args.budget)
        all_df.append(df);all_l.append(l)
        if train_sample is None:train_sample=train.copy();hist_example=hist.copy()
        print('completed seed',seed,'products',len(df)//len(POLICIES),flush=True)
    df=pd.concat(all_df,ignore_index=True); lineage=pd.concat(all_l,ignore_index=True)
    per,summ=aggregate(df)
    df.to_csv(target/'decisions.csv',index=False);lineage.to_csv(target/'passport_lineage.csv',index=False)
    per.to_csv(target/'per_seed.csv',index=False);summ.to_csv(target/'summary.csv',index=False)
    train_sample.to_csv(target/'synthetic_training.csv',index=False)
    np.save(target/'federated_noisy_histograms.npy',hist_example)
    # Pre-specified sensitivity / robustness dimensions. Subsample for tractable WSL replay.
    sweeps=[]
    for scenario,vals in [('budget',[0,1,2,3,4]),('epsilon',[.5,2.,8.,float('inf')]),('shift',[0.,.06,.12]),('weights',[(12.,.15,.22),(12.,.25,.32),(12.,.40,.48)])]:
        for val in vals:
            kw=dict(products=args.sweep_products,nparticles=args.particles,epsilon=args.epsilon,budget=args.budget,shift=0.,weights=WEIGHTS)
            if scenario=='budget':kw['budget']=val
            elif scenario=='epsilon':kw['epsilon']=val
            elif scenario=='shift':kw['shift']=val
            else:kw['weights']=val
            for seed in range(args.start_seed,args.start_seed+args.sweep_seeds):
                d,_,_,_=one_run(seed,**kw)
                p,_=aggregate(d)
                p=p[p.policy.isin(['fixed_two','adaptive_two','entropy_two','clear_cost','clear_no_dp','full_input_route'])].copy()
                p['scenario']=scenario;p['value']=str(val);sweeps.append(p)
    sweep=pd.concat(sweeps,ignore_index=True);sweep.to_csv(target/'sweeps.csv',index=False)
    meta=dict(start_seed=args.start_seed,seeds=args.seeds,products_per_seed=args.products,total_products=args.seeds*args.products,particles=args.particles,attack_particles=1200,features=list(FEATURES),predicates=len(THRESHOLDS),epsilon_per_feature=args.epsilon,record_level_epsilon_upper_bound=3*args.epsilon,clients_per_tier=4,number_of_tiers=3,scope='entirely synthetic, simulated local clients and two-server aggregation; no hardware TEE, no paper algorithm replicas',weights=WEIGHTS,setup='emissions and costs include stylised route-dependent transport terms; no validated LCA',sweep_seeds=args.sweep_seeds,sweep_products=args.sweep_products)
    (target/'metadata.json').write_text(json.dumps(meta,indent=2))
    print('\nMAIN MEANS:\n',summ[['policy','regret_mean','recovered_kg_mean','n_queries_mean','attack_c_joint_mean']].to_string(index=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='outputs');p.add_argument('--seeds',type=int,default=12);p.add_argument('--start-seed',type=int,default=100);p.add_argument('--products',type=int,default=140);p.add_argument('--particles',type=int,default=320);p.add_argument('--epsilon',type=float,default=2.);p.add_argument('--budget',type=int,default=2);p.add_argument('--sweep-seeds',type=int,default=4);p.add_argument('--sweep-products',type=int,default=70);run(p.parse_args())
