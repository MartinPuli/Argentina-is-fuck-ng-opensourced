# Review of the new PAMI report

**Reviewed:** October 9, 2026
**Pulled commit:** `fa859d5` — PAMI Data Exposure problem analysis report.
**Change:** one new 408-line document; no application code, agent implementation or deployment added. Local research edits were preserved by a fast-forward pull.

## Main conclusion

The [new report](<../../PAMI Data Exposure Problem Analysis.md>) usefully separates external intrusion, accidental publication and fraudulent use. Its strongest contribution is the distinction between a confidential clinical file, a purchasing file and the public record.

That distinction changes what a prevention demonstration must prove. The documented 2026 publication case calls for controlling the exact public package. A server-compromise demonstration must separately show access restriction and recovery. Neither scenario proves the other.

## Findings to correct or clarify

1. **Sale duration is mistaken for time after intrusion — line 236.** The report says information was advertised seven days after the attack. The cited article says the offer lasted seven days. Suggested wording: “According to the cited reporting on UFECI's findings, the information was offered for sale for seven days at 25 bitcoin.” The judicial document itself was not independently reviewed here. [Cited reporting](https://www.infobae.com/judiciales/2025/07/21/reabrieron-la-investigacion-por-el-hackeo-al-pami-encontraron-en-cordoba-un-comprador-de-la-base-de-datos-robada/).
2. **Attribute the initial removal statement — line 58.** The first report quotes PAMI's announced response. The follow-up found continuing access and new uploads. Say PAMI announced or said it had ordered removal; reserve independently observed restriction for the subsequent verification. [Initial investigation](https://chequeado.com/investigaciones/pami-expone-datos-medicos-y-documentos-sensibles-de-sus-afiliados-en-su-sitio-web/), [follow-up](https://chequeado.com/investigaciones/a-una-semana-de-la-revelacion-de-chequeado-el-pami-continua-mostrando-en-su-web-datos-privados-de-sus-afiliados/).
3. **Add support for detailed recovery claims — lines 224–226.** The linked August 2 TN article does not establish virtual-machine restoration from backups, ANMAT hosting inside PAMI, or the stated audit conclusion. Add the corresponding institutional statement or another direct source, or narrow the passage. This is a citation gap, not proof the details are false. [Current citation](https://tn.com.ar/tecno/internet/2023/08/02/pami-no-funciona-la-pagina-ni-la-app-de-la-obra-social/).

The 40-case minimum and January–February sample are supported by the original investigation. The report appropriately avoids treating those cases as a complete population count. “Purpose collapse” is a useful author interpretation of the reconstructed publication workflow; it should not become a proven cause of the separate ransomware intrusion.

## What this adds to the proposed product

The next design should distinguish three jobs:

- **Before publication:** prepare an explicitly approved public derivative, hold uncertain attachments for review, and bind approval to the exact bytes released.
- **During confirmed account compromise:** revoke the affected identity at an independent access boundary and check that another authorized service continues.
- **After repair:** verify the actual release, including old accessible paths, before declaring recovery. Preserve incident evidence separately from operational rebuilding.

This is a proposed implementation direction. The new report does not implement these controls.

## What our current experiment can and cannot show

The [publication experiment](../../experiments/publication-regression/README.md) tests a controlled release of synthetic bytes with trusted classifications. It can show that removing private source files alone leaves an unsafe cached build, and that an exact fresh release blocks that fixture.

It does not read real medical PDFs, perform OCR, identify contextual health information, authenticate two reviewers, or establish the cause of PAMI's continued exposure. A stale build is our synthetic test mechanism, not a confirmed PAMI diagnosis.

Its deliberate misclassification counterexample is especially important: private content labeled public can pass an integrity gate. A complete product needs independently evaluated classification and accountable approval, with approval invalidated after any file changes.

## Review limits

This was a complete read of the added document and a targeted source check of the main incident and recovery claims, not a full legal audit or verification of every named official and historical source. The contributed report was left unchanged; these findings are review notes.
