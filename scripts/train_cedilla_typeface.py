"""Page-held-out cedilla shape experiment using human-reviewed typefaces."""
import ast,json,re,sys
from pathlib import Path
from collections import Counter
from difflib import SequenceMatcher
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as ndi
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import confusion_matrix,balanced_accuracy_score
import joblib
sys.path.insert(0,"scripts")
import external_ai_review as rev
def native_patch(scan, row, index):
    alignment = row["alignment"][index]
    mapping = row["scan_mappings"][index] if row.get("scan_mappings") else row.get("scan_mapping")
    if not alignment or not mapping:
        return None
    px = (alignment["left"] + alignment["width"] / 2) * row["image_width"] / 100
    u = np.array(mapping["dx"])
    v = np.array([-u[1], u[0]])
    centre = np.array(mapping["origin"]) + px * u + 24 * np.array(mapping["dy"])
    origin = centre - 28 * u - 24 * v
    return scan.transform((72, 48), Image.Transform.AFFINE,
                          (u[0], v[0], origin[0], u[1], v[1], origin[1]),
                          Image.Resampling.BICUBIC, fillcolor=255)

out=Path("build/cedilla-learn");out.mkdir(exist_ok=True)
def feature(p,mode):
    a=np.asarray(p,dtype=float)
    dark,light=np.percentile(a,[12,85])
    a=np.clip((light-a)/max(25,light-dark),0,1)
    if mode=="context":a=a[9:43,9:44]
    elif mode=="tight":a=a[13:39,17:38]
    elif mode=="upper":a=a[13:31,17:38]
    else:
        lab,_=ndi.label(a>.45,np.ones((3,3)))
        boxes=[]
        for k,box in enumerate(ndi.find_objects(lab),1):
            if box is None:continue
            y,x=box;h=y.stop-y.start;w=x.stop-x.start
            cx=(x.start+x.stop)/2
            if 10<=h<=32 and 5<=w<=26 and abs(cx-28)<12 and y.start>=6 and y.start<30:
                boxes.append((abs(cx-28)+abs(y.start-18)*.15,box))
        if not boxes:return None
        _,(y,x)=min(boxes,key=lambda b:b[0])
        if mode=="body":y=slice(y.start,min(y.stop,y.start+round((y.stop-y.start)*.72)))
        a=a[y,x]
    z=ndi.zoom(a,(24/a.shape[0],20/a.shape[1]),order=1)
    z=ndi.gaussian_filter(z,.6)
    return np.r_[a.shape[1]/a.shape[0],z.ravel()]

if not (out/"samples.json").exists() or "--refresh" in sys.argv:
 samples=[];missing=[]
 for n in range(438,543):
    path=Path(rev.SOURCE,f"bnf-f{n:04}.md")
    aligned=Path(f"site/assets/alignment/bnf-f{n:04}.json")
    if not path.exists() or not aligned.exists():continue
    rows={r["id"]:r for r in json.loads(aligned.read_bytes())["rows"]}
    scan=None
    for lid,line in rev.lines(rev.parse(path.read_bytes())).items():
      s=rev.plain(line);faces=[r["typeface"] for r in line["runs"] for _ in r["text"]]
      row=rows.get(lid)
      mapping={}
      if row and row.get("alignment"):
       for tag,a,b,c,d in SequenceMatcher(None,s,row["text"],autojunk=False).get_opcodes():
        if tag=="equal":mapping.update((i,c+i-a) for i in range(a,b))
      for word in re.finditer(r"[^\W\d_]+",s):
       for m in re.finditer(r"[Tt]ç",word[0]):
        i=word.start()+m.start()+1
        if not any(faces[j]=="roman" for j in range(word.start(),word.end()) if j!=i and s[j].islower()):continue
        item=dict(page=n,line=lid,offset=i,expected_text=s,expected_typeface=faces[i],typeface="italic",word=word[0],label=int(faces[i]=="italic"))
        j=mapping.get(i)
        if j is None or not row["alignment"][j] or row["alignment"][j].get("kind")!="matched":
            missing.append(item);continue
        if scan is None:
            with Image.open(f"build/nippo-jisho-images/scans/native/f{n:04}.jpg") as im:scan=im.convert("L")
        patch=native_patch(scan,row,j)
        if patch is None:missing.append(item);continue
        item["crop"]=f"{len(samples):04}.png";patch.save(out/item["crop"]);samples.append(item)
 (out/"samples.json").write_text(json.dumps(samples,ensure_ascii=False))
 (out/"missing.json").write_text(json.dumps(missing,ensure_ascii=False))
samples=json.loads((out/"samples.json").read_bytes())
results={}; models={}
for mode in ["context","glyph","body","tight","upper"]:
 features={}
 for j,s in enumerate(samples):
    with Image.open(out/s["crop"]) as p:f=feature(p,mode)
    if f is not None:features[j]=f
 ids=[j for j,s in enumerate(samples) if s["page"]<=484 and j in features]
 X=np.array([features[j] for j in ids]);Y=np.array([samples[j]["label"] for j in ids]);G=np.array([samples[j]["page"] for j in ids])
 print(mode,len(ids),Counter(Y),flush=True)
 splits=list(StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=842).split(X,Y,G))
 for name,model in [
    ("lr",make_pipeline(StandardScaler(),LogisticRegression(C=.02,class_weight="balanced",max_iter=2000))),
    ("svm",make_pipeline(StandardScaler(),SVC(C=3,gamma="scale",class_weight="balanced",probability=True,random_state=842))),
    ("trees",ExtraTreesClassifier(n_estimators=200,min_samples_leaf=3,class_weight="balanced",random_state=842,n_jobs=2))]:
    scores=np.zeros(len(ids))
    for train,test in splits:
        model.fit(X[train],Y[train]);scores[test]=model.predict_proba(X[test])[:,1]
    key=mode+"-"+name
    print(key,round(balanced_accuracy_score(Y,scores>.5),4),confusion_matrix(Y,scores>.5).tolist(),flush=True)
    results[key]=[dict(id=j,label=int(y),score=float(sc)) for j,y,sc in zip(ids,Y,scores)]
    model.fit(X,Y)
    models[key]=(model,features)
    joblib.dump(model,out/(key+".joblib"))
(out/"validation.json").write_text(json.dumps(results))
predictions=[]
for j,s in enumerate(samples):
    if s["page"]<=484:continue
    scores={key:float(model.predict_proba([features[j]])[0,1]) for key,(model,features) in models.items() if j in features}
    predictions.append(dict(id=j,**s,scores=scores))
(out/"predictions.json").write_text(json.dumps(predictions,ensure_ascii=False))

# Selective decisions: disagreements abstain; scores are not calibrated
# confidence guarantees. These thresholds were explored on the validation
# folds, so the reported precision is exploratory, not an untouched test.
selected = []
for item in predictions:
    s = item["scores"]
    keys = ["glyph-trees", "body-trees", "glyph-lr", "context-lr"]
    if not all(key in s for key in keys):
        continue
    decision = (1 if s["glyph-trees"] > .5 and s["body-trees"] > .5 else
                0 if all(s[key] < .2 for key in keys) else None)
    if decision is not None and decision != item["label"]:
        selected.append({**item, "page": f'bnf-f{item["page"]:04d}',
                         "typeface": "italic" if decision else "roman"})
(out / "selected.json").write_text(json.dumps(selected, ensure_ascii=False, indent=2))
print("Proposed changes:", Counter(x["typeface"] for x in selected))
