#!/usr/bin/env python3
"""FLC muscular auto-digitize field trial.

READ: flc/*.pdf
WRITE: flc/_AUTO_DIGITIZE_TEST/** only
Never modifies source PDFs.

Pipeline:
1. fingerprint + PDF structural checks
2. qpdf reconstruction/linearization derivative
3. OCRmyPDF conservative routine normalization (deskew/autorotate/clean; skip existing text)
4. embedded text extraction
5. low-res page renders + image statistics
6. anomaly/duplicate detection
7. per-issue JSON + Markdown "here's what there is" seed
8. run manifest with hashes/tool versions

This is intentionally an experimental first pass. Detectors flag anomalies; only
known reversible/carrier-level repairs are automated.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, math, os, re, shutil, statistics, subprocess, sys, tempfile
from pathlib import Path

TOOLS = ["qpdf","pdfinfo","pdftotext","pdftoppm","ocrmypdf"]
def run(cmd, timeout=600):
    p=subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace", timeout=timeout)
    return p.returncode,p.stdout,p.stderr
def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def toolver(t):
    if not shutil.which(t): return None
    rc,o,e=run([t,"--version"],30); return (o or e).strip().splitlines()[0] if (o or e) else f"rc={rc}"
def parse_pdfinfo(s):
    d={}
    for line in s.splitlines():
        if ":" in line:
            k,v=line.split(":",1); d[k.strip()]=v.strip()
    return d
def pgm_stats(path):
    # P5/P6 PNM parser sufficient for pdftoppm grayscale output.
    with open(path,"rb") as f:
        magic=f.readline().strip()
        def token():
            while True:
                x=f.readline()
                if not x: return b""
                x=x.split(b"#",1)[0].strip()
                if x: return x
        dims=token().split()
        while len(dims)<2: dims += token().split()
        w,h=map(int,dims[:2]); maxv=int(token()); data=f.read()
    if magic==b"P6":
        vals=[sum(data[i:i+3])//3 for i in range(0,len(data)-2,3)]
    else: vals=list(data)
    if not vals: return {"width":w,"height":h,"mean":None,"stdev":None,"dark_fraction":None,"white_fraction":None,"entropy":None}
    n=len(vals); mean=sum(vals)/n; var=sum((x-mean)**2 for x in vals)/n
    hist=[0]*256
    for x in vals: hist[x]+=1
    ent=-sum((c/n)*math.log2(c/n) for c in hist if c)
    return {"width":w,"height":h,"mean":round(mean,3),"stdev":round(math.sqrt(var),3),
            "dark_fraction":round(sum(x<40 for x in vals)/n,5),
            "white_fraction":round(sum(x>245 for x in vals)/n,5),"entropy":round(ent,4)}
def ahash(path, size=16):
    # Hash grayscale render by block averages without image libraries.
    st=pgm_stats(path)
    with open(path,"rb") as f:
        magic=f.readline()
        toks=[]
        while len(toks)<3:
            line=f.readline()
            if not line: break
            line=line.split(b"#",1)[0]
            toks += line.split()
        w,h,maxv=map(int,toks[:3]); data=f.read()
    vals=list(data)
    if not vals: return ""
    blocks=[]
    for by in range(size):
        y0=by*h//size; y1=max(y0+1,(by+1)*h//size)
        for bx in range(size):
            x0=bx*w//size; x1=max(x0+1,(bx+1)*w//size)
            sm=ct=0
            for y in range(y0,y1):
                row=y*w
                for x in range(x0,x1): sm+=vals[row+x]; ct+=1
            blocks.append(sm/ct)
    med=statistics.median(blocks)
    bits="".join("1" if x>=med else "0" for x in blocks)
    return hex(int(bits,2))[2:].zfill(size*size//4)
def hamming_hex(a,b):
    if not a or not b or len(a)!=len(b): return 999
    return (int(a,16)^int(b,16)).bit_count()
def robust_z(vals,x):
    vals=[v for v in vals if v is not None]
    if len(vals)<5: return 0.0
    med=statistics.median(vals); mad=statistics.median(abs(v-med) for v in vals)
    return 0.0 if mad==0 else 0.6745*(x-med)/mad
def safe_write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8"); os.replace(tmp,path)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("source",type=Path)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--dpi",type=int,default=72)
    args=ap.parse_args()
    src=args.source.resolve(); out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    run_id=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+src.stem
    issue=out/src.stem; issue.mkdir(parents=True,exist_ok=True)
    manifest={"run_id":run_id,"source_path":str(src),"source_sha256":sha256(src),"source_bytes":src.stat().st_size,
              "started_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"tools":{t:toolver(t) for t in TOOLS},
              "declared_write_root":str(out),"source_preserved":True,"actions":[],"flags":[]}
    # structural check
    rc,o,e=run(["qpdf","--check",str(src)],120) if shutil.which("qpdf") else (127,"","qpdf missing")
    manifest["qpdf_check"]={"rc":rc,"stdout":o[-4000:],"stderr":e[-4000:]}
    carrier=issue/"carrier_normalized.pdf"
    if shutil.which("qpdf"):
        rc2,o2,e2=run(["qpdf","--linearize",str(src),str(carrier)],300)
        manifest["actions"].append({"operation":"qpdf_linearize_rewrite","class":"SAFE_AUTO_FIX" if rc else "AUTO_FIX_VERIFY",
          "rc":rc2,"output":carrier.name if carrier.exists() else None})
        if rc2 or not carrier.exists(): carrier=src
    else: carrier=src
    # routine scan normalization derivative
    normalized=issue/"routine_normalized.pdf"
    if shutil.which("ocrmypdf"):
        cmd=["ocrmypdf","--deskew","--rotate-pages","--clean","--skip-text","--optimize","1",
             "--output-type","pdf",str(carrier),str(normalized)]
        rc3,o3,e3=run(cmd,1800)
        manifest["actions"].append({"operation":"deskew_autorotate_clean","class":"AUTO_FIX_VERIFY","rc":rc3,
          "output":normalized.name if normalized.exists() else None,"stderr_tail":e3[-3000:]})
        if rc3 or not normalized.exists(): normalized=carrier
    else: normalized=carrier
    # info and text
    rc4,info,ie=run(["pdfinfo",str(normalized)],120)
    meta=parse_pdfinfo(info); manifest["pdfinfo"]=meta
    textfile=issue/"embedded_text.txt"
    rc5,to,te=run(["pdftotext","-layout",str(normalized),str(textfile)],300)
    if not textfile.exists(): textfile.write_text("",encoding="utf-8")
    txt=textfile.read_text(encoding="utf-8",errors="replace")
    manifest["text"]={"rc":rc5,"chars":len(txt),"replacement_chars":txt.count("\ufffd"),
      "control_chars":sum(ord(c)<32 and c not in "\n\r\t\f" for c in txt)}
    # render grayscale diagnostic pages
    pages=issue/"diagnostic_pages"; pages.mkdir(exist_ok=True)
    prefix=pages/"page"
    rc6,ro,re_=run(["pdftoppm","-gray","-r",str(args.dpi),"-pgm",str(normalized),str(prefix)],1200)
    pgms=sorted(pages.glob("page-*.pgm"))
    records=[]
    for i,p in enumerate(pgms,1):
        st=pgm_stats(p); st.update({"page":i,"file":p.name,"ahash":ahash(p),"flags":[]}); records.append(st)
    # corpus-relative anomalies
    for key in ("mean","stdev","entropy","white_fraction","dark_fraction"):
        vals=[r[key] for r in records]
        for r in records:
            z=robust_z(vals,r[key])
            if abs(z)>=4:
                r["flags"].append({"pattern":f"{key.upper()}_OUTLIER","z":round(z,2),"class":"ANOMALOUS"})
    for r in records:
        if r["white_fraction"] is not None and r["white_fraction"]>0.985:
            r["flags"].append({"pattern":"NEAR_BLANK_PAGE","class":"ANOMALOUS"})
        if r["entropy"] is not None and r["entropy"]<1.0:
            r["flags"].append({"pattern":"VERY_LOW_VISUAL_ENTROPY","class":"ANOMALOUS"})
    # duplicate/near duplicate pages
    dups=[]
    for i in range(len(records)):
        for j in range(i+1,len(records)):
            d=hamming_hex(records[i]["ahash"],records[j]["ahash"])
            if d<=4:
                dups.append({"page_a":i+1,"page_b":j+1,"hash_distance":d,
                             "pattern":"EXACT_OR_NEAR_DUPLICATE_RENDER","class":"ANOMALOUS"})
    manifest["page_render"]={"rc":rc6,"count":len(records),"expected":int(meta.get("Pages","0") or 0)}
    if manifest["page_render"]["expected"] and len(records)!=manifest["page_render"]["expected"]:
        manifest["flags"].append({"pattern":"PAGE_COUNT_CONSERVATION_FAILURE","severity":"HIGH"})
    manifest["duplicates"]=dups
    manifest["pages"]=records
    # remove bulky PGM diagnostics after extracting measurements; retained results are enough for v0.
    for p in pgms: p.unlink()
    try: pages.rmdir()
    except OSError: pass
    # derive a machine-readable and human-readable first interpretation seed
    page_flags=sum(len(r["flags"]) for r in records)
    summary=[
      f"# AUTO-DIGITIZE: {src.name}",
      "",
      "## Here's what there is — machine seed",
      "",
      f"- Source: `{src.name}` ({src.stat().st_size:,} bytes)",
      f"- SHA-256: `{manifest['source_sha256']}`",
      f"- PDF pages reported: {meta.get('Pages','unknown')}",
      f"- Diagnostic pages rendered: {len(records)}",
      f"- Embedded/layout text recovered: {len(txt):,} characters",
      f"- Page-level anomaly flags: {page_flags}",
      f"- Duplicate/near-duplicate candidates: {len(dups)}",
      f"- Structural qpdf check: {'PASS' if rc==0 else 'SUSPECT'}",
      "",
      "## Routine transformations attempted",
      "",
    ]
    for a in manifest["actions"]:
        summary.append(f"- {a['operation']}: rc={a['rc']} ({a['class']})")
    summary += ["","## Flags for editorial/technical review",""]
    if not manifest["flags"] and not dups and not page_flags: summary.append("- No automatic anomaly flags in this pass.")
    for f in manifest["flags"]: summary.append(f"- {json.dumps(f,ensure_ascii=False)}")
    for d in dups[:50]: summary.append(f"- pages {d['page_a']} / {d['page_b']}: near-duplicate render (distance {d['hash_distance']})")
    for r in records:
        for f in r["flags"]: summary.append(f"- page {r['page']}: {f['pattern']} (z={f.get('z','n/a')})")
    summary += ["","## Editorial layer","",
      "This is intentionally a machine seed, not an editorial judgment. A later ChatGPT/editorial pass should inspect the recovered text and page/component evidence, characterize contents, correct false-positive anomaly flags, and record newly learned corruption/layout patterns in the pattern registry.",
      ""]
    manifest["finished_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
    safe_write(issue/"manifest.json",json.dumps(manifest,indent=2,ensure_ascii=False))
    safe_write(issue/"HERE_IS_WHAT_THERE_IS.md","\n".join(summary))
    # top-level compact run record
    compact={"run_id":run_id,"source":src.name,"source_sha256":manifest["source_sha256"],
             "pages":len(records),"text_chars":len(txt),"page_flags":page_flags,"duplicate_candidates":len(dups),
             "qpdf_ok":rc==0,"normalized_pdf":str(normalized.relative_to(out)) if normalized!=src else None}
    safe_write(issue/"run_summary.json",json.dumps(compact,indent=2))
    print(json.dumps(compact))
if __name__=="__main__":
    main()
