import numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from skimage import data
from skimage.transform import resize
import os
OUT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'results')+'/'
INK='#141A2A'; MUTED='#5B6275'; SURF='#FCFCFB'
GOOD,WARN,BAD='#0ca30c','#fab219','#d03b3b'
BLUE,ORANGE='#2a78d6','#eb6834'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':13,'axes.edgecolor':'#C9C6BF','axes.labelcolor':INK,'xtick.color':MUTED,'ytick.color':MUTED,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.facecolor':'white'})
SEQ=LinearSegmentedColormap.from_list('blue',['#f4f7fc','#9ec5f4','#3987e5','#1c5cab','#0d366b'])
import csv, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LUT=np.zeros((16,16),dtype=np.int64)
for r in csv.DictReader(open(os.path.join(ROOT,'data','rca_simulated_truth_table.csv'))):
    if r['Cin']=='0': LUT[int(r['A']),int(r['B'])]=int(r['simulated'])
IDEAL=np.array([[a^b for b in range(16)] for a in range(16)])
def hyb(A,B,k,n=8):
    out=np.zeros_like(A); c=np.zeros_like(A)
    for i in range(n):
        a,b=(A>>i)&1,(B>>i)&1
        if i<k: s=a^b^c if i==0 else ((a+(1-b)+c)>=2).astype(np.int64)
        else: s=a^b^c; c=(a&b)|(a&c)|(b&c)
        out|=s<<i
    return out|(c<<n)
gray=lambda x: x if x.ndim==2 else x[...,:3].mean(axis=2)
def norm(x):
    x=resize(gray(x),(256,256),anti_aliasing=True); return (x-x.min())/(x.max()-x.min())
yy,xx=np.mgrid[0:256,0:256]/255
P={'moon+coins':(norm(data.moon()),norm(data.coins())),'brick+gravel':(norm(data.brick()),norm(data.gravel())),'gradient+blob':(xx,np.exp(-((xx-.5)**2+(yy-.5)**2)/.05))}
def blend(S,T,a,kind):
    if kind in('theory','sim'):
        s=np.round((1-a)*S*15).astype(np.int64); t=np.round(a*T*15).astype(np.int64)
        return s+t,(IDEAL if kind=='theory' else LUT)[s,t]
    k=int(kind[1:]); s=np.round((1-a)*S*255).astype(np.int64); t=np.round(a*T*255).astype(np.int64)
    return s+t,hyb(s,t,k)
# ---------- F1 pies
def pies(designs, labels, fname, suptitle, legend):
    fig,ax=plt.subplots(1,len(designs),figsize=(5.2*len(designs),5.4))
    stats={}
    for axx,(kind,title,thr) in zip(ax,designs):
        d=np.concatenate([np.abs(e-ap).ravel() for e,ap in (blend(S,T,0.5,kind) for S,T in P.values())])
        cats=[(d==0).mean(),((d>=1)&(d<=thr)).mean(),(d>thr).mean()]
        stats[kind]=[round(100*c,1) for c in cats]
        w,_=axx.pie(cats,colors=[GOOD,WARN,BAD],startangle=90,counterclock=False,wedgeprops=dict(width=0.42,edgecolor='white',linewidth=2))
        axx.text(0,0.08,f'{100*cats[0]:.0f}%',ha='center',va='center',fontsize=26,fontweight='bold',color=INK)
        axx.text(0,-0.22,'exact',ha='center',va='center',fontsize=13,color=MUTED)
        axx.set_title(title,fontsize=14,color=INK,pad=10)
        axx.text(0,-1.38,f'{labels[1]} {100*cats[1]:.0f}%  ·  {labels[2]} {100*cats[2]:.0f}%',ha='center',fontsize=13,color=INK)
    fig.legend(w,legend,loc='lower center',ncol=3,frameon=False,fontsize=13)
    fig.suptitle(suptitle,fontsize=16,color=INK,x=0.02,ha='left')
    fig.tight_layout(rect=(0,0.08,1,0.93)); fig.savefig(OUT+fname,dpi=150); plt.close(fig)
    print(fname,stats)
pies([('theory','QCA 4-bit RCA\nin theory (equations)',2),('sim','QCA 4-bit RCA\nsimulated layout',2)],['exact','minor','major'],
     'f1_pies_4bit.png','4-bit QCA RCA: pixel errors, α = 0.5, 3 image pairs',
     ['Exact pixel','Minor error (1–2 of 15 levels)','Major error (3+ levels)'])
pies([('k1','8-bit hybrid\n1 approximate bit',2),('k2','8-bit hybrid\n2 approximate bits',2),('k4','8-bit hybrid\n4 approximate bits',2)],['exact','invisible','visible'],
     'f1_pies_hybrid.png','8-bit hybrid adder: pixel errors, α = 0.5, 3 image pairs',
     ['Exact pixel','Invisible error (1–2 of 255 levels)','Visible error (3+ levels)'])
designs=[('theory','QCA 4-bit RCA\nin theory (equations)','4-bit'),('sim','QCA 4-bit RCA\nsimulated layout','4-bit'),('k2','8-bit hybrid\n2 approximate bits','8-bit'),('k4','8-bit hybrid\n4 approximate bits','8-bit')]
# ---------- F2 input-pair error map (4-bit, Cin=0)
A,B=np.meshgrid(np.arange(16),np.arange(16),indexing='ij'); ex=A+B
fig,ax=plt.subplots(1,2,figsize=(13,6))
for axx,(M,t) in zip(ax,[(IDEAL,'In theory (paper equations)'),(LUT,'Simulated Fig 9 layout')]):
    ed=np.abs(ex-M)
    im=axx.imshow(ed,cmap=SEQ,vmin=0,vmax=30,origin='lower')
    axx.set_title(f'{t}\nwrong for {100*np.mean(ed>0):.0f}% of pairs, mean error {ed.mean():.1f}',fontsize=14,color=INK)
    axx.set_xlabel('B (0–15)'); axx.set_ylabel('A (0–15)'); axx.set_xticks([0,5,10,15]); axx.set_yticks([0,5,10,15])
cb=fig.colorbar(im,ax=ax,fraction=0.025,pad=0.02); cb.set_label('error distance |exact − approximate|')
fig.suptitle('Where the 4-bit adder goes wrong: every (A, B) input pair, Cin = 0',fontsize=16,color=INK,x=0.02,ha='left')
fig.savefig(OUT+'f2_input_error_map.png',dpi=150,bbox_inches='tight'); plt.close(fig)
# ---------- F3 error heatmaps on an image (moon+coins), % of full scale
S,T=P['moon+coins']
fig,ax=plt.subplots(1,4,figsize=(17,4.9))
for axx,(kind,title,depth) in zip(ax,designs):
    e,ap=blend(S,T,0.5,kind); full=15 if depth=='4-bit' else 255
    im=axx.imshow(100*np.abs(e-ap)/full,cmap=SEQ,vmin=0,vmax=50)
    axx.set_title(title.replace('\n',', '),fontsize=12.5,color=INK); axx.axis('off')
cb=fig.colorbar(im,ax=ax,fraction=0.015,pad=0.01); cb.set_label('pixel error, % of full scale')
fig.suptitle('Error maps, moon + coins, α = 0.5 (darker = bigger error)',fontsize=16,color=INK,x=0.02,ha='left')
fig.savefig(OUT+'f3_error_maps.png',dpi=150,bbox_inches='tight'); plt.close(fig)
# ---------- F4 error histogram 4-bit theory vs simulated
fig,ax=plt.subplots(figsize=(12,5))
lv=np.arange(0,17)
for off,(kind,lab,col) in zip((-0.2,0.2),[('theory','In theory (equations)','#86b6ef'),('sim','Simulated layout',BLUE)]):
    d=np.concatenate([np.abs(e-ap).ravel() for e,ap in (blend(S_,T_,0.5,kind) for S_,T_ in P.values())])
    h=np.array([np.mean(d==v) for v in lv])*100
    ax.bar(lv+off,h,width=0.38,color=col,label=lab)
ax.set_xlabel('pixel error (grey levels, 4-bit scale 0–15)'); ax.set_ylabel('share of pixels (%)'); ax.set_xticks(lv)
ax.legend(frameon=False); ax.grid(axis='y',color='#ECE9E3'); ax.set_axisbelow(True)
ax.set_title('Error size distribution, α = 0.5: the layout flaw adds large errors',fontsize=15,color=INK,loc='left')
fig.tight_layout(); fig.savefig(OUT+'f4_error_hist.png',dpi=150); plt.close(fig)
# ---------- F5 PSNR by image pair and alpha (4-bit theory vs sim)
fig,ax=plt.subplots(figsize=(12,5))
labels=[];th=[];sm=[]
for name,(S_,T_) in P.items():
    for a in (0.2,0.5,0.8):
        r=[]
        for kind in ('theory','sim'):
            e,ap=blend(S_,T_,a,kind); mse=np.mean((e-ap)**2.0); r.append(10*np.log10(225/mse))
        labels.append(f'{name}\nα={a}'); th.append(r[0]); sm.append(r[1])
x=np.arange(len(labels))
ax.bar(x-0.2,th,0.38,color='#86b6ef',label='In theory (equations)'); ax.bar(x+0.2,sm,0.38,color=BLUE,label='Simulated layout')
ax.set_xticks(x); ax.set_xticklabels(labels,fontsize=10); ax.set_ylabel('PSNR (dB)'); ax.legend(frameon=False)
ax.grid(axis='y',color='#ECE9E3'); ax.set_axisbelow(True)
ax.set_title('4-bit QCA RCA: PSNR for every image pair and blending factor',fontsize=15,color=INK,loc='left')
fig.tight_layout(); fig.savefig(OUT+'f5_psnr_by_pair.png',dpi=150); plt.close(fig)
print('done')
