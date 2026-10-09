# Demo script (about 2 minutes)

1. **The problem (20 s).** Show the Chequeado headline. "In May, PAMI published retirees' medical histories, disability certificates and ID copies on its public purchasing site. Local offices attached the whole clinical file to each purchase. Nobody checked before it went live."
2. **Live page (40 s).** Press **Send 8 office files** and let it run: each file shows its steps as the agent works (read, find IDs, AkashML check, decide, Guild note).
3. **Purchase page (30 s).** Wheelchair purchase from UGL Jujuy:
   - Spec sheet and supplier quote: **public**. Point out the company CUIT is recognized as public business data.
   - Medical summary: **withheld**. DNI, CUIL with valid check digit, affiliate number, birth date, address, all masked, each citing the law.
   - Scanned DNI and disability certificate: **withheld**. No text layer, read with OCR.
4. **Review queue (30 s).** Prosthesis spec and bed spec are **held**. "No name, no ID number. But age, town, hospital and date point to one person. Our pattern checks missed the bed entirely. The open model on AkashML caught it." Show the Guild agent's brief. Approve one with a reviewer name.
5. **Public portal (15 s).** Only cleared files are listed. "3 documents with personal or health data: not published." Paste a withheld file's URL: 404. The check runs on every request.
6. **Dashboard (15 s).** ClickHouse audit log: decisions by office, what the gate catches, gate latency, who approved what.
7. **Close (10 s).** "Transparency stays. Medical evidence stays inside. Open source, so any agency can run it without a procurement process."

All data is fictional and watermarked. No real government system is connected.
