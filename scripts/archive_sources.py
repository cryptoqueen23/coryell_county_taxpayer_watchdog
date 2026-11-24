import hashlib, json, pathlib, urllib.request
root = pathlib.Path("archive")
root.mkdir(exist_ok=True)
(root / "README.md").write_text("Original public PDFs are stored by SHA-256. Existing fingerprints are never replaced automatically. Unmatched downloads are not promoted to canonical sources.\n")
p = pathlib.Path("canon.json")
docs = json.loads(p.read_text())
for d in docs:
    url = d.get("url") or ""
    expected = d.get("sha256")
    if not expected or not url.startswith("https://"):
        print("SKIP unpinned source", d["id"])
        continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"TaxpayerWatchdogArchive/1.0"})
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read(50_000_001)
        if len(data)>50_000_000 or not data.startswith(b"%PDF-"):
            raise ValueError("Not an eligible PDF")
        digest = hashlib.sha256(data).hexdigest()
        if digest != expected.lower():
            raise ValueError("Fingerprint mismatch; manual review required: "+digest)
        target = root / (digest+".pdf")
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
            raise ValueError("Existing archive integrity failure")
        if not target.exists():
            target.write_bytes(data)
        d["archiveUrl"] = "https://raw.githubusercontent.com/cryptoqueen23/coryell_county_taxpayer_watchdog/main/"+str(target)
        print("VERIFIED", d["id"], digest)
    except Exception as exc:
        print("PENDING", d["id"], str(exc))
p.write_text(json.dumps(docs, ensure_ascii=False, indent=2)+"\n")
