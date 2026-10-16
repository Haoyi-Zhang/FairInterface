"""Direct vector schematics for exact-port fairness interfaces."""
import argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle,FancyArrowPatch,PathPatch
from matplotlib.path import Path as Curve

plt.rcParams.update({"font.family":"STIXGeneral","font.size":10,"mathtext.fontset":"stix",
                     "pdf.fonttype":42,"ps.fonttype":42,"text.usetex":False})
def node(ax,x,y,label,port=False):
    ax.add_patch(Circle((x,y),.20,facecolor="white",edgecolor="black",lw=.9,zorder=3))
    if port:ax.add_patch(Circle((x,y),.245,facecolor="none",edgecolor="black",lw=.8,zorder=3))
    ax.text(x,y,label,ha="center",va="center",zorder=4)
def edge(ax,a,b,label,pos,dashed=False):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle="-|>",mutation_scale=9,color="black",
                                lw=.9,linestyle="--" if dashed else "-",shrinkA=13,shrinkB=13))
    ax.text(*pos,label,ha="center",va="center")
def finish(fig,ax,out,name):
    ax.set_axis_off()
    fig.canvas.draw()
    for text in ax.texts:
        b=text.get_window_extent()
        if b.x0<fig.bbox.x0-1 or b.y0<fig.bbox.y0-1 or b.x1>fig.bbox.x1+1 or b.y1>fig.bbox.y1+1:
            raise ValueError("Label outside canvas: "+text.get_text())
    fig.savefig(out/name,metadata={"CreationDate":None,"ModDate":None})
    plt.close(fig)
def capacity(out):
    fig,ax=plt.subplots(figsize=(4.7,2.7))
    fig.subplots_adjust(left=.02,right=.98,bottom=.03,top=.98)
    ax.set(xlim=(0,4.2),ylim=(-.15,2.8),aspect="equal")
    for x,y,l,port in [(.5,1.35,"$p$",True),(2,2.35,"$u$",False),(2,.55,"$v$",False),(3.5,1.35,"$q$",True)]:
        node(ax,x,y,l,port)
    edge(ax,(.5,1.35),(2,2.35),r"$\{a\}$",(1.04,2.05))
    edge(ax,(2,2.35),(3.5,1.35),r"$\varnothing$",(2.95,2.06))
    edge(ax,(.5,1.35),(2,.55),r"$\{b\}$",(1.03,.71))
    edge(ax,(2,.55),(3.5,1.35),r"$\varnothing$",(2.98,.72))
    path=Curve([(3.53,1.10),(3.9,-.15),(.15,-.15),(.47,1.10)],
               [Curve.MOVETO,Curve.CURVE4,Curve.CURVE4,Curve.CURVE4])
    ax.add_patch(FancyArrowPatch(path=path,arrowstyle="-|>",mutation_scale=9,lw=.9,color="black"))
    ax.text(2,.04,r"$\varnothing$",ha="center",va="center")
    finish(fig,ax,out,"excursion-capacity.pdf")
def enabling(out):
    fig,ax=plt.subplots(figsize=(4.4,1.8))
    fig.subplots_adjust(left=.02,right=.98,bottom=.03,top=.97)
    ax.set(xlim=(-.15,4.4),ylim=(0,1.9),aspect="equal")
    node(ax,1.1,.9,"$p$",True)
    ax.add_patch(Rectangle((3.3,.65),.7,.5,facecolor="white",edgecolor="black",lw=.9))
    ax.text(3.65,.9,"$T$",ha="center",va="center")
    ax.add_patch(FancyArrowPatch((1.35,.9),(3.3,.9),arrowstyle="-|>",
                                mutation_scale=9,color="black",linestyle="--",lw=.9))
    ax.text(2.35,1.14,r"$\{f\}$",ha="center",va="center")
    path=Curve([(.92,1.08),(-.08,2.35),(-.08,-.55),(.92,.72)],
               [Curve.MOVETO,Curve.CURVE4,Curve.CURVE4,Curve.CURVE4])
    ax.add_patch(FancyArrowPatch(path=path,arrowstyle="-|>",mutation_scale=9,lw=.9,color="black"))
    ax.text(.10,.9,r"$\varnothing$",ha="center",va="center")
    finish(fig,ax,out,"late-bound-enabling.pdf")
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir",type=Path,default=Path(__file__).resolve().parent)
    args=ap.parse_args();args.outdir.mkdir(parents=True,exist_ok=True)
    capacity(args.outdir);enabling(args.outdir)
    print("Two exact-port vector schematics generated; labels within canvas.")
if __name__=="__main__":main()
