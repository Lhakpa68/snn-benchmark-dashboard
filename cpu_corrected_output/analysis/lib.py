import sqlite3, math, statistics as stt
import numpy as np
from scipy import stats
TDP=55.0
def load(db, groups=None):
    c=sqlite3.connect(db)
    w="task in ('inference','scalability')"
    args=()
    if groups:
        w+=" and run_group in (%s)"%",".join("?"*len(groups)); args=tuple(groups)
    runs=[dict(zip(["fb","task","n","phase","i","t","rss","cpu","e"],r)) for r in c.execute(
        f"select framework||'/'||backend,task,network_size,phase,run_index,runtime_s,peak_rss_mb,cpu_pct,energy_j from runs where {w} order by id",args)]
    cond={}
    for r in c.execute(f"select framework||'/'||backend,task,network_size,phase,runtime_median_s,peak_rss_mb,cpu_pct,energy_median_j,eflop,spikes,cv_pct,runtime_min_s,runtime_max_s,compile_dominated from conditions where {w} order by id",args):
        cond[(r[0],r[1],r[2],r[3])]=dict(med=r[4],rss=r[5],cpu=r[6],e=r[7],eflop=r[8],spikes=r[9],cv=r[10],mn=r[11],mx=r[12],cd=r[13])
    return runs,cond
def ktau(a,b):
    n=len(a);C=D=ta=tb=0
    for i in range(n):
        for j in range(i+1,n):
            da=a[i]-a[j];db=b[i]-b[j];p=da*db
            if p>0:C+=1
            elif p<0:D+=1
            else:
                if da==0:ta+=1
                if db==0:tb+=1
    n0=n*(n-1)/2
    return (C-D)/math.sqrt((n0-ta)*(n0-tb))
def fit(ns,ts):
    x=np.log(ns);y=np.log(ts);r=stats.linregress(x,y);return r.slope,r.rvalue**2,r.stderr
SIZES=[100,500,1000,5000,10000]
def backends(cond): return sorted({k[0] for k in cond})
def sc(cond,fb,n,field="med"):
    return cond[(fb,"scalability",n,"simulate")][field]
