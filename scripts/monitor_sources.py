import hashlib, json, pathlib, urllib.request, datetime
p=pathlib.Path("source-monitor.json")
old=json.loads(p.read_text()) if p.exists() else {}
previous={x["id"]:x for x in old.get("records",[])}
records=[]
for d in json.loads(pathlib.Path("canon.json").read_text()):
    url=d.get("url") or ""
    if not url.startswith("https://"):
        continue
    row={"id":d["id"],"title":d["title"],"url":url}
    prior=previous.get(d["id"],{})
    baseline=prior.get("baseline") if prior.get("url")==url else None
    row["baseline"]=baseline
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"TaxpayerWatchdogMonitor/1.0"})
        with urllib.request.urlopen(req,timeout=45) as res:
            data=res.read(50000001)
        if len(data)>50000000 or not data.startswith(b"%PDF-"):
            raise ValueError("Non-PDF or oversized response; manual review")
        digest=hashlib.sha256(data).hexdigest()
        row["observedSha256"]=digest
        row["baseline"]=baseline or digest
        expected=d.get("sha256")
        row["status"]="changed_review_required" if digest!=row["baseline"] or (expected and digest!=expected) else ("unchanged" if baseline else "initial_observation")
    except Exception as exc:
        row["status"]="unavailable_or_non_pdf"
        row["detail"]=str(exc)
    records.append(row)
p.write_text(json.dumps({"checkedAt":datetime.datetime.now(datetime.timezone.utc).isoformat(),"records":records},indent=2)+"\n")
