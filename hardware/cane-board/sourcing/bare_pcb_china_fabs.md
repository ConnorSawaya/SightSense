# Bare PCB prices from China-based prototype makers, shipped to the San Francisco Bay Area (read October 13, 2026)

How to read these notes

- Every figure carries one of three marks: **[LIVE]** = read from the maker's live instant-quote calculator (page text or the JSON the page requested), **[PUBLISHED]** = from a published help, notice or price page, **[N/A]** = could not obtain. Arithmetic done by the researcher is marked **[CALC]** and appears only under "Inferences".
- All live quotes were read on **October 13, 2026 between about 19:07 and 19:30 PDT** (October 14, about 10:07 to 10:30 China time; PCBgogo's panel showed "CHN Time Zone (GMT+8): 2026/10/14 10:14:51"). No login, no account, no Gerber upload, nothing added to a cart. Cookie banners were not accepted.
- **None of the seven calculators accepts a ZIP code at the quote stage.** Each takes only the country ("United States"). the Bay Area ZIP could therefore not be entered anywhere; all shipping prices below are each maker's rate for "United States". A ZIP-specific or remote-area adjustment, if any, appears only at checkout behind a login.
- Board entered everywhere: 100 mm x 40 mm, 2 layers, FR-4, 1.6 mm, 1 oz, green mask, white silkscreen, single piece (no panel), 1 design, no castellated holes, no gold fingers, no impedance control. Minimum track/space 6/6 mil and minimum drill 0.3 mm were selected where the form offers them (see the per-maker option list in the first section for the forms that do not).

## 1. Board price for 5 and for 10 pieces, standard build time, and paid faster build

### Takeaway
For this 40 x 100 mm board the makers fall into three price bands for the bare boards alone: about $4 to $5 for either 5 or 10 pieces (JLCPCB, PCBWay, PCBgogo, Elecrow, all with leaded HASL), $9.90 (Seeed Fusion), and $19.99 (NextPCB, unless the new-customer price applies). ALLPCB returned no price at all: its site carries a notice that the website has suspended operations. Choosing lead-free HASL takes the board off the cheapest tier at several makers (PCBWay 10 pcs $5.00 -> $18.18, PCBgogo 10 pcs $5.00 -> $24.90, Seeed 5 pcs $9.90 -> $17.90), while at JLCPCB and Elecrow it adds only $1.20 to $2.00.

### Cited Findings

Summary table (bare boards only, no shipping, no duty)

| Maker | 5 pcs, HASL with lead | 10 pcs, HASL with lead | Lead-free HASL | Standard build | Paid faster build |
| --- | --- | --- | --- | --- | --- |
| JLCPCB | $4.00 [LIVE] | $5.00 [LIVE] | 5 pcs $5.20, 10 pcs $6.30 [LIVE] | 2 days, $0 [LIVE] | 24 hours, +$7.60 [LIVE] |
| PCBWay | $5.00 [LIVE] | $5.00 [LIVE] | 5 pcs $5.00, 10 pcs $18.18 [LIVE] | 24 hours [LIVE] | "Extra Urgent" 12 hours: 5 pcs $94.56 total (leaded) / $99.53 (lead-free); 10 pcs $99.53 (leaded) / $104.51 (lead-free) [LIVE] |
| ALLPCB | [N/A] | [N/A] | [N/A] | [N/A] | [N/A] |
| PCBgogo | $5.00 [LIVE] | $5.00 [LIVE] | 10 pcs $24.90 [LIVE]; 5 pcs [N/A, not read] | 2-3 days [LIVE] | None offered on the $5 leaded price. With lead-free, 10 pcs: 24 hours $49.24 total, 12 hours $133.79 total (shown as "Original: $143.86") [LIVE] |
| NextPCB | $19.99 [LIVE] | $19.99 [LIVE] | Same $19.99 (lead-free is the default; leaded gave the same price at 10 pcs) [LIVE] | 48 hours [LIVE] | 24 hours, $24.99 total (+$5.00) [LIVE] |
| Elecrow | $4.90 [LIVE] | $4.90 [LIVE] | 10 pcs $6.90 [LIVE]; 5 pcs [N/A, not read] | 3-5 working days [LIVE] | "Rush 48h (+$5)", "Rush 24h (+$16)" [LIVE] |
| Seeed Fusion | $9.90 [LIVE] | $9.90 [LIVE] | 5 pcs $17.90 [LIVE]; 10 pcs [N/A, not read] | 3 ~ 4 working days [LIVE] | None shown on the quote page [LIVE] |

Per-maker detail, with the exact options selected

- **JLCPCB** [LIVE]. Options: Base Material FR-4; Layers 2; Dimensions 40 x 100 mm; PCB Qty 5 then 10; Product Type "Industrial/Consumer electronics"; Different Design 1; Delivery Format "Single PCB"; PCB Thickness 1.6 mm; PCB Color Green; Silkscreen White; Material Type "FR4 TG135"; Surface Finish "HASL(with lead)" (then "LeadFree HASL" as a comparison); Outer Copper Weight 1 oz; Via Covering Tented; Min via hole size/diameter 0.3 mm/(0.4/0.45 mm) (default); Board Outline Tolerance +/-0.2 mm (Regular); Electrical Test "Flying Probe Fully Test"; Gold Fingers No; Castellated Holes No; Edge Plating No. The standard form has no minimum track/space selector. Result, 5 pcs: Charge Details "Special Offer $4.00", Via Covering $0.00, Surface Finish $0.00; "PCB Build Time: 2 days $0.00; 24 hours $7.60; 24 hours PCBA Only $0.00"; "Calculated Price $4.00 Web / $2.00 JLCONE Desktop"; weight 0.19 kg. With LeadFree HASL the Surface Finish line becomes $1.20 and the total $5.20 (JLCONE Desktop $3.20). Result, 10 pcs: Special Offer $5.00, total $5.00 with leaded HASL; LeadFree HASL adds $1.30, total $6.30; build options unchanged (2 days $0.00, 24 hours $7.60); weight 0.26 kg; the 10-piece panel shows "Order on JLCONE Desktop: Save $1-$20 Per Order" instead of a second price. The price API response for 5 pcs confirms `"achieveDateList"`: "2 days" price 0.00 and "24 hours" price 7.60. — [JLCPCB instant quote](https://cart.jlcpcb.com/quote)
- **PCBWay** [LIVE]. Options: Board type "Single pieces"; Different design in panel 1; Size 100 x 40 mm; Quantity 5 then 10; Layers 2; Material FR-4; FR4-TG "TG 150-160" (default; the page says 2-layer boards are upgraded to S1000H TG150 for free); Thickness 1.6; Min track/spacing 6/6mil; Min hole size 0.3mm; Solder mask Green; Silkscreen White; Edge connector No; Surface finish "HASL lead free" (the page default) and "HASL with lead"; Via process Tenting vias; Finished copper 1 oz Cu; Remove product No. "No". Results: 5 pcs lead-free "24hours $5.00", "Extra Urgent! $99.53"; 5 pcs leaded "24hours $5.00", "Extra Urgent! $94.56"; 10 pcs lead-free "24hours $18.18", "Extra Urgent! $104.51"; 10 pcs leaded "24hours $5.00", "Extra Urgent! $99.53". The build-time JSON labels the urgent option "express 12hours". The Price Comparison Matrix for lead-free showed 10 pcs $18.18, 15 pcs $29.35, 20 pcs $31.94 (24 hours each). The panel states "Final price is subject to our review." Removing PCBWay's order number from the board is offered as "Yes (extra +$1.5)". — [PCBWay instant quote](https://www.pcbway.com/orderonline.aspx)
- **ALLPCB** [N/A]. Options entered: FR-4, 2 layers, 100 x 40 mm, Single PCB, 5 pcs, 1.6, Green, White, "HASL Lead Free" (default), 1oz, 6/6mil, 0.3mm, Tenting Vias, castellated None, PTH copper 18um. Pressing "Quote Now" returned the notice "Instant online quotation is not available for the current parameters. Please use 'Quote by Salesperson' :)" and the price request (`PcbOnline.ashx?act=CalcPcbPrice`) came back with an empty list. A site-wide banner reads: "Due to adjustments to the Company's corporate governance structure, our website will temporarily suspend operations effective immediately. Outstanding orders and services will still be fulfilled as agreed. For more information, please contact your dedicated customer service representative." The notice record carries a start time of 2026-06-24 16:00 UTC (June 25 China time). The "Quote by Salesperson" form was not used. — [ALLPCB instant quote](https://www.allpcb.com/online_pcb_quote_new.html)
- **PCBgogo** [LIVE]. Options: Material "Normal FR-4 Board"; Different Design in Panel 1; Size 100 x 40 mm; Quantity 5 then 10; Panel Way "Single piece"; Layers 2; FR4-TG "TG 150"; Thickness 1.6; Min Track/Spacing 6/6mil; Min Hole Size 0.3mm; Solder Mask Green; Silkscreen White; Gold Fingers No; Surface Finish "HASL with lead" (the page default), with the "replace HASL to ENIG randomly" consent left at No; Via Process Tenting vias; Finished Copper 1 oz. Results: 5 pcs "2-3 days $5.00"; 10 pcs "2-3 days $5.00". The Price Comparison Matrix (leaded) showed 5 -> $5.00, 10 -> $5.00, 15 -> $25.41, 20 -> $28.96, 25 -> $32.52, 30 -> $36.09, all "2-3 days". With "HASL lead free", 10 pcs: "2-3 days $24.90; 12hours Original: $143.86 $133.79; 24hours $49.24". The panel says "The price is rough quote." — [PCBgogo instant quote](https://www.pcbgogo.com/pcb-fabrication-quote.html)
- **NextPCB** [LIVE]. Options: Standard PCB; Material FR-4; Layer Count 2; Different Designs 1; Size 100 x 40 mm; Quantity 5 then 10; Board Type "Single piece"; TG Rating "TG130(Random)"; PCB Thickness 1.6mm; Solder Mask Green; Silkscreen White; Outer Copper 1oz; Trace Width/Spacing 6/6mil; Min. Drill Hole 0.3mm; Via Processing "Tented Vias"; Surface Finish "Lead free HASL" (default) and "HASL"; Impedance No; Edge Connector Bevel No; Plated Half-holes No; Edge Plating No; "100% FPT for Prototypes"; IPC Level 2. Results for both 5 and 10 pcs: "48 hours $19.99", "24 hours $24.99"; the panel shows "PCB Cost [1st Order] $0.1" with $19.99 struck through. The price JSON gives 5 pcs `unit_price 4.00, sub_total 19.99, deltime "48 hours"` and 10 pcs `unit_price 2.00, sub_total 19.99`; next tiers 50 pcs $54.38, 100 pcs $83.93 (72 hours), 200 pcs $130.81. Switching to leaded "HASL" at 10 pcs left $19.99 / $24.99 unchanged. The page states "100% E-test & AOI Passed for Every Piece. Default is Lead-free HASL." — [NextPCB instant quote](https://www.nextpcb.com/pcb-quote)
- **Elecrow** [LIVE]. Options: Base Material "Fr-4 PCB"; Layer "2 layer"; Dimensions 100 x 40 mm; PCB Qty 5 then 10; Different PCB Design 1; PCB Thickness 1.6; PCB Color Green; Silkscreen White; Surface Finish "HASL" (then "HASL Lead Free" at 10 pcs); Castellated Hole No; Copper Weight 1oz; Production Time "3-5 working days". The form has no track/space or drill-size selector. Results: 5 pcs $4.90 (weight 150 g); 10 pcs $4.90 (weight 240 g); 10 pcs lead-free $6.90. Production Time options: "Rush 24h(+$16)", "Rush 48h(+$5)", "3-5 working days". — [Elecrow PCB quote](https://www.elecrow.com/pcb-manufacturing.html)
- **Seeed Studio Fusion** [LIVE]. Options ("Quickturn PCB/PCBA" tab): Base Material "FR-4 TG130"; 2 layers; PCB Dimension 100 x 40 mm; PCB Quantity 10 then 5; 1 design; Thickness 1.60; PCB Color Green; Surface Finish "HASL" (then "HASL Lead Free" at 5 pcs); Minimum Solder Mask Dam "0.4mm" (default); Copper Weight 1oz; Minimum Drill Hole Size 0.3mm; Castellated Holes No; Trace Width/Spacing 6/6 mil; Impedance Control No. The form has no silkscreen colour selector. Results: 10 pcs "USD$9.90", "Production Time 3 ~ 4 Working Days", weight 0.13 kg; 5 pcs USD$9.90, weight 0.0640 kg; 5 pcs lead-free USD$17.90. No faster-build option is shown. — [Seeed Fusion PCB quote](https://www.seeedstudio.com/fusion_pcb.html)

### Inferences
- [CALC] Per-board price before shipping: JLCPCB $0.80 (5) / $0.50 (10); PCBWay, PCBgogo $1.00 / $0.50; Elecrow $0.98 / $0.49; Seeed $1.98 / $0.99; NextPCB $4.00 / $2.00 (NextPCB's own JSON gives the same unit prices).
- At JLCPCB, PCBWay, PCBgogo and Elecrow, 10 boards cost the same as 5 or $1 more, so quantity does not drive the decision; shipping and duty do.
- Leaded HASL is what the cheap tier is built around at PCBWay (10 pcs), PCBgogo and Seeed. If lead-free is required, JLCPCB (+$1.20/+$1.30) and Elecrow (+$2.00 at 10 pcs) are the only two where it stays cheap.
- The JLCPCB "$2.00 JLCONE Desktop" figure is a channel-specific price for 5 pieces ordered through JLCPCB's desktop program, not the web price; see section 6.

### Gaps
- ALLPCB: no price, build time or shipping could be obtained. The site says its website has suspended operations; the only path offered is a salesperson quote form, which was not used.
- Lead-free prices not read: PCBgogo at 5 pcs, Elecrow at 5 pcs, Seeed at 10 pcs.
- JLCPCB and Elecrow do not ask for minimum track/space, and Elecrow does not ask for drill size, so those two quotes are not confirmed against 0.15 mm / 0.3 mm inside the calculator. Capability pages were not checked.
- PCBWay ("Final price is subject to our review") and PCBgogo ("rough quote") state that the instant price can change after file review; there are no Gerbers yet, so that review could not happen.
- Chinese public-holiday schedules and file-review time were not checked; build times are as stated by each calculator.

## 2. Shipping methods to the USA, price and stated transit time

### Takeaway
Every maker that quoted offers an express courier at roughly $26 to $32 for this parcel (2 to 5 business days) and, except PCBgogo, an economy line at about $6 to $10 (6 to 13 business days; 15 to 25 at Seeed). The cheapest express read was PCBWay DHL at $26.55 and JLCPCB UPS Express Saver (DDP) at $26.64; the cheapest economy lines were NextPCB 4PX $5.97, PCBWay Global Direct $6.56 and JLCPCB Global Standard Direct Line $6.95 (5 pcs).

### Cited Findings

All prices are for "United States" (no ZIP field exists). Transit times are the makers' own stated figures, counted from dispatch.

- **JLCPCB, 5 pcs (0.19 kg)** [LIVE, from the `calculateGoodsFreight` JSON and the on-page shipping table]: UPS Express Saver (DDP) $26.64, 2-4 business days; DHL Express (DDP) $31.44, 2-4 business days (pre-selected); DHL Express (not DDP) $31.44, 2-4 business days; FedEx Express (DDP) $31.70, 2-5 business days; Global Standard Direct Line $6.95, 8-13 business days, restrictions "<=1.5kg, <=$59, <=55x40cm"; My DHL / UPS / FedEx Account $2.00 each (ships on the customer's own courier account); Sea Shipment not available (100-10000 kg). — [JLCPCB instant quote](https://cart.jlcpcb.com/quote)
- **JLCPCB, 10 pcs (0.26 kg)** [LIVE]: UPS Express Saver (DDP) $26.64; DHL Express (DDP) $31.44; DHL Express $31.44; FedEx Express (DDP) $31.70; Global Standard Direct Line $7.92, 8-13 business days. — [JLCPCB instant quote](https://cart.jlcpcb.com/quote)
- JLCPCB's freight JSON also carries its own delivery statistics for US parcels [LIVE]: Global Standard Direct Line delivered within 7 business days 26.05%, within 10 business days 81.08%, within 15 business days 99.53%; plain DHL Express delivered within 5 business days 76.85%, within 7 business days 95.73%. — [JLCPCB instant quote](https://cart.jlcpcb.com/quote)
- JLCPCB's hover note on the cost column: "The shipping cost provided is for reference only. The final shipping cost will be confirmed at checkout." [LIVE] — [JLCPCB instant quote](https://cart.jlcpcb.com/quote)
- **PCBWay, 5 pcs (0.07 kg)** [LIVE]: DHL $26.55, 2-4 business days; DHL(DTP) $28.20, 2-4 business days; FedEx-FICP(DDP) $33.01, 3-5 business days; FedEx-IP $35.88, 3-5; FedEx-FICP $32.19, 3-5; FedEx-IP(DDP) $36.79, 3-5; Global Standard Shipping $6.74, 7-12 business days; Global Direct Shipping $6.56, 6-12 business days; USPS $12.81, 6-12 business days; SF Express(DDP) $22.04, 6-8 business days; "Other shipping way: Contact us". With DHL selected the panel showed "Shipment Date 2026/10/16 AM, Delivery Date 2026/10/19". — [PCBWay instant quote](https://www.pcbway.com/orderonline.aspx)
- **PCBWay, 10 pcs (0.14 kg)** [LIVE]: DHL $26.55; DHL(DTP) $28.20; FedEx-FICP(DDP) $33.26; FedEx-IP $36.12; FedEx-FICP $32.43; FedEx-IP(DDP) $37.04; Global Standard Shipping $7.68, 7-12; Global Direct Shipping $7.43, 6-12; USPS $14.31, 6-12; SF Express(DDP) $22.04, 6-8. — [PCBWay instant quote](https://www.pcbway.com/orderonline.aspx)
- PCBWay's general shipping page: "International Express - Shipments are delivered in 3-7 days after it leaves our International shipping facility"; "International Economy - ... 5-20 days"; page "Last updated on 22/02/2024" [PUBLISHED]. — [PCBWay shipping information](https://www.pcbway.com/helpcenter/shipping_instructions/International_Order___Shipping_Information.html)
- **PCBgogo, 5 pcs (calculator weight 0.570 kg)** [LIVE]: DHL $32, 3-5 days; DHL(DDP) $32, 3-5 days; FedEx-IP $59, 3-5 days; "Other shipping way: Contact us for shipping method details". No postal or economy line is listed. — [PCBgogo instant quote](https://www.pcbgogo.com/pcb-fabrication-quote.html)
- **PCBgogo, 10 pcs (calculator weight 0.640 kg)** [LIVE]: DHL $32; DHL(DDP) $32; FedEx-IP $60; all 3-5 days. — [PCBgogo instant quote](https://www.pcbgogo.com/pcb-fabrication-quote.html)
- **NextPCB, 5 pcs (0.08 kg) and 10 pcs (0.15 kg), identical prices** [LIVE, from the `ajax/express` JSON]: DHL $25.31, "2-5 business days" (the panel displays $15.31 with $25.31 struck through, see section 6); 4PX $5.97, "6-10 business days", `money_limit` 150.00; "Your Shipping Account" $0, "5-10 days". No FedEx, UPS or postal option was returned for the US. — [NextPCB instant quote](https://www.nextpcb.com/pcb-quote)
- NextPCB's shipping page gives general times: DHL "normally takes 2-4 business days", FedEx "3-7 business days", Hongkong Post "15-30 business days" [PUBLISHED]. — [NextPCB shipment page](https://www.nextpcb.com/shipment)
- **Elecrow, 5 pcs (150 g)** [LIVE]: "ShenZhenDHL (2-5 Business Days) $29.64"; "Economy Express ZT (10-12 Business Days) $7.46"; "UPS Direct Line (12-15 Business Days) $43.18"; "UPS (6-9 Business Days) $33.34"; "FedEx IP (3-5 Business Days) $49.28"; "Economy Express (6-11 Business Days) $7.41". — [Elecrow PCB quote](https://www.elecrow.com/pcb-manufacturing.html)
- **Elecrow, 10 pcs (240 g)** [LIVE]: ShenZhen DHL $29.64; Economy Express ZT $8.79; UPS Direct Line $43.18; UPS $33.34; FedEx IP $49.28; Economy Express $9.67. — [Elecrow PCB quote](https://www.elecrow.com/pcb-manufacturing.html)
- **Seeed Fusion, 5 pcs (0.064 kg)** [LIVE]: DHL $27.82, 3-5 working days; FedEx9610 $65.21, 3-7 working days; Epacket $8.21, 15-25 working days; Yan Wen $14.99, 10-17 working days. — [Seeed Fusion PCB quote](https://www.seeedstudio.com/fusion_pcb.html)
- **Seeed Fusion, 10 pcs (0.13 kg)** [LIVE]: DHL $27.82, 3-5 working days; FedEx9610 $65.21, 3-7; Epacket $9.86, 15-25; Yan Wen $15.86, 10-17. — [Seeed Fusion PCB quote](https://www.seeedstudio.com/fusion_pcb.html)
- **ALLPCB**: shipping panel stayed empty ("--") because no price was calculated [N/A]. — [ALLPCB instant quote](https://www.allpcb.com/online_pcb_quote_new.html)

### Inferences
- Express freight is essentially a flat minimum charge at this weight: going from 5 to 10 boards changed no express price at JLCPCB, PCBWay (DHL), PCBgogo (DHL), NextPCB, Elecrow (DHL) or Seeed (DHL). Economy lines rise by about $1 to $2.
- Shipping, not the boards, is the main cost at every maker: the cheapest express option is 5 to 6.5 times the board price at the $4 to $5 makers.
- PCBgogo's calculator weight (0.57 to 0.64 kg) is several times what the other calculators give for the same boards (0.06 to 0.26 kg); it looks like a fixed packaging allowance. It does not matter to the price read, which is a flat $32.
- PCBWay's stated dates (ship October 16 AM, deliver October 19, for a quote made October 14 China time) imply about 5 to 6 calendar days order-to-door on plain DHL if files pass review the same day.

### Gaps
- No ZIP-level rate could be read anywhere; whether that ZIP attracts any surcharge is not visible without logging in. It is a major metro address, so a remote-area fee would be unexpected, but that is not confirmed.
- JLCPCB warns that the final shipping cost is confirmed only at checkout (login required).
- Whether JLCPCB lets an individual (non-company) customer pick the non-DDP "DHL Express" line could not be tested without an account; its published rule is in section 3.
- Transit times are stated ranges; only JLCPCB publishes delivery statistics. No customs-delay allowance is included by any maker.

## 3. US tariff, duty, tax or "customs" charge: is it shown, how much, and who collects it

### Takeaway
No instant-quote page shows a US tariff amount; where a maker collects duty in advance (JLCPCB's DDP lines, PCBWay's DTP/DDP lines), the amount appears only at order submission, behind a login. Published rates as of the latest notices: JLCPCB pre-collects 35% on PCBs and 90% on stencils for US DDP orders and does not refund differences; PCBWay estimates 37.5% on PCBs and 77.90% on stencils. PCBgogo, NextPCB, Elecrow and Seeed publish no current US duty-prepayment scheme that could be found, and their pages say duties are the buyer's responsibility, normally collected by the courier.

### Cited Findings

What the quote pages show

- JLCPCB: the quote panel has no tariff line. The price JSON contains the fields `tariffChargesMoney`, `tariffRate`, `tariffServiceMoney` and `saleTaxMoney`, all `null` at the quote stage [LIVE]. Four of the five US shipping lines are labelled DDP (UPS Express Saver, DHL Express, FedEx Express) [LIVE]. — [JLCPCB instant quote](https://cart.jlcpcb.com/quote)
- PCBWay: the quote panel states "Notice: Customs duties and VAT are not included!" [LIVE]. The hover text on the DTP/DDP lines reads: "Pre-pay customs duties & taxes by PCBWay are required for DHL (DTP), and DTP charges service fee. The above fees (duties & taxes and service fee) are calculated when order is confirmed, and here shows only shipping cost." [LIVE] — [PCBWay instant quote](https://www.pcbway.com/orderonline.aspx)
- PCBgogo: lists "DHL(DDP)" at the same $32 as plain DHL; the explanatory pop-up for it contains only the word "undefined" (a page fault), so no terms are shown [LIVE]. — [PCBgogo instant quote](https://www.pcbgogo.com/pcb-fabrication-quote.html)
- NextPCB: no tariff line. The DHL option carries the tip "If your package is required to undergo an inspection for customs clearance, it may generate customs fees or other processing fees. Duties are based on the customs requirements of the destination country/region" [LIVE]. — [NextPCB instant quote](https://www.nextpcb.com/pcb-quote)
- Elecrow and Seeed Fusion: no tariff, duty or tax line or note on the quote page [LIVE]. — [Elecrow PCB quote](https://www.elecrow.com/pcb-manufacturing.html); [Seeed Fusion PCB quote](https://www.seeedstudio.com/fusion_pcb.html)

Published rules, by maker

- JLCPCB FAQ ("Last updated on Sep 08, 2026") [PUBLISHED]: tariff components listed as "Provisional Tariff: 10% (effective Feb 24, 2026-Jul 24, 2026)", "122 Tariff: 12.5% (New, effective July 24, 2026) (Official 122 Tariff is set at 12.5% but JLC Tariff is set at 10%)", "Section 301 Tariffs: 25%", "Regular Tariffs: under applicable HS codes: 0~7.5%", "Total tariff rate: About 35%~92.5%". Its rate table (an image on the page) lists **PCB 35.00%, SMT 35.00%, Stencil 90.00%**. — [JLCPCB U.S. Tariff Policy FAQ](https://jlcpcb.com/help/article/us-tariff-policy-faq)
- JLCPCB, same FAQ [PUBLISHED]: "For U.S. Individual Customer Orders: JLCPCB will ship goods using DDP (Delivered Duty Paid) terms. For U.S. Company Customer Orders: JLCPCB encourages DDP terms but also supports CPT (Carriage Paid To) terms." "You only need to prepay taxes when placing your order". "For orders where we charges tariffs in the range of 35%-90%, we will not refund or charge the difference because the rate is average". Under CPT "the recipient is responsible for paying taxes directly to the logistics provider or U.S. Customs." For UPS and FedEx B2C shipments the carrier "requires the use of DDP". — [JLCPCB U.S. Tariff Policy FAQ](https://jlcpcb.com/help/article/us-tariff-policy-faq)
- JLCPCB's running notice confirms the 35.00% PCB rate from March 17, 2026 and records that from April 22, 2025 "DHL Express and FedEx Express options are now restricted to corporate customers only" while "YunExpress small packet options and self-use DHL, FedEx account (Non-DDP) remain unaffected" [PUBLISHED]. The page does not say what the tariff percentage is applied to (product value only, or product plus freight), and does not mention the Global Standard Direct Line. — [JLCPCB policy adjustments notice](https://jlcpcb.com/blog/logistics-policy-updates-due-to-the-us-tariff-on-china)
- PCBWay notice, section "Updated on August 15 2026" [PUBLISHED]: "Current Tax Rates for Various PCBWay Products: PCB: 37.5%; SMT: 47.50%; Stencils: 77.90%; Wire Harnesses: 52.60%". An undated-year earlier section ("Update on Dec 31th") listed bare PCBs 45% and SMT stencils 88%. — [PCBWay tariff notice](https://www.pcbway.com/blog/News/Impact_of_the_New_U_S_Tariff_Policy_on_Customs_Clearance_51dff4fd.html)
- PCBWay notice, section "Updated on May 8th / May 15th" (year not printed; 2025 from context) [PUBLISHED]: recommends "DDP (Delivered Duty Paid) logistics services with prepaid tariffs, such as: 1. DHL DTP (Duty & Tax Prepaid), SF express"; "DHL DTP will prepay customs duties & taxes"; "3. Global Direct Shipping: Duties included in shipping costs ... The logistics provider does not accept U.S.-bound shipments with a declared value exceeding $60 USD (inclusive)"; "4. Global Standard Shipping, USPS: Prepaid tax fee: A 30% duty rate (based on declared value) will be charged upon package arrival. No refunds, no additional charges, and no tax invoice provided." — [PCBWay tariff notice](https://www.pcbway.com/blog/News/Impact_of_the_New_U_S_Tariff_Policy_on_Customs_Clearance_51dff4fd.html)
- PCBWay staff replies under the same notice (September 25, 2025) [PUBLISHED, comment thread]: for FedEx-IP(DDP) "the service fee and MPF are included" and "You can see the tariff details when you submit order". — [PCBWay tariff notice](https://www.pcbway.com/blog/News/Impact_of_the_New_U_S_Tariff_Policy_on_Customs_Clearance_51dff4fd.html)
- PCBgogo help article (posted "Jun 04.2021") [PUBLISHED]: "customs tax fees are not included in the product prices, neither in the shipping cost you paid to us"; "PCBgogo will never pay for the custom tax fees"; "Import duties, taxes and other customs-related fees are usually collected by the shipping company at the time of delivery." The article does not mention DDP. — [PCBgogo customs duties help](https://www.pcbgogo.com/help/Do_I_have_to_pay_customs_duties_and_import_duties_when_ordering_from_PCBgogo_.html)
- NextPCB's own August 2026 article [PUBLISHED] describes the stack on China-made PCBs as the 25% Section 301 layer plus a new 12.5% layer effective July 24, 2026 (total 37.5% over MFN "frequently 0%" for HTS 8534.00), notes that "Some 2- and 4-layer bare PCBs hold exclusions", says the Section 122 10% surcharge ran February 24 to July 24, 2026, and flags November 10, 2026 as the date Section 301 exclusions are scheduled to expire. It does not say how NextPCB collects duty on its own shipments. — [NextPCB tariffs article](https://www.nextpcb.com/blog/pcb-manufacturing-tariffs-2026-china-sourcing)
- Elecrow shipping page [PUBLISHED]: "Taxes and import duties are not included in the shipping cost." "You should expect to pay any amount charged by the government in your respective country." No US-specific or DDP text. — [Elecrow shipping information](https://www.elecrow.com/shippinginfo)
- Seeed's only tariff notice found is dated May 14, 2025 [PUBLISHED]: it anticipated the rate "will likely be reduced to 30%" and set a "Reimbursement for Overpayments, Payment for Underpayments" policy for customers who "have already prepaid tariffs". No 2026 update was found. — [Seeed tariff notice](https://www.seeed.cc/post/navigating-recent-u-s-tariff-adjustment-update)

Independent context and cross-checks

- Altium's article (created April 14, 2026; data "as of March 20, 2026") states that bare boards under HTSUS 8534.00.00 were then shielded from the 25% Section 301 rate by an exclusion, leaving a 10% stack, and that "Absent a renewal, bare board duties will jump from 10% to a combined 35% overnight" after November 10, 2026. It also states "all shipments from China and Hong Kong now require formal entry regardless of value" and that the Merchandise Processing Fee is "subject to a minimum of $33.58 ... per entry". — [Altium, The 2026 Tariff Reset](https://resources.altium.com/p/tariff-reset-pcb-workarounds); partly contradicted on entry thresholds by [JLCPCB U.S. Tariff Policy FAQ](https://jlcpcb.com/help/article/us-tariff-policy-faq), which says for DHL "all shipments with a declared value exceeding $800 must undergo formal customs declaration" and for UPS that informal clearance applies when "total shipment value is less than $2,500 and individual item value is less than $250"
- User reports, 2026, cross-check only: an EEVblog poster (April 25, 2026) listed a JLCPCB DDP order with PCB $66.32 + assembly $1,302.52, shipping $169.19, "customs" $479.11 and sales tax $127.56 charged at checkout; another poster worked the customs figure out as about 35% of PCB plus assembly. A May 11, 2026 poster reported DHL brokerage fees of "~$20" on a CPT order and said DDP brokerage is usually inside the shipping charge. A May 23, 2026 poster reported 43% on a PCB-only DDP order about a month earlier. — [EEVblog, "JLC tarriffs etc. to US ?"](https://www.eevblog.com/forum/manufacture/jlc-tarriffs-etc-to-us/)

### Inferences
- [CALC] At the published rates the duty on these boards is small in dollars: JLCPCB 35% x $4.00 = $1.40 (5 pcs) or 35% x $5.00 = $1.75 (10 pcs); PCBWay 37.5% x $5.00 = $1.88. These assume the percentage is applied to the product price only; neither maker publishes the base, and the EEVblog example fits product-value-only (35% of $1,368.84 = $479.09 against $479.11 charged).
- Two different readings of the law are in circulation for a 2-layer bare board. The makers' notices apply roughly 35% to 37.5% (25% Section 301 plus the 12.5% layer of July 24, 2026). Altium (March 2026) and NextPCB (August 2026) both say 2- and 4-layer bare boards hold a Section 301 exclusion scheduled to end November 10, 2026, which would make the statutory rate lower than what JLCPCB pre-collects. JLCPCB says it does not refund the difference at its averaged rates. For a $4 to $5 order the gap is under $1.50, so it does not change the ranking.
- The practical risk on a small parcel is not the percentage but fixed fees on non-prepaid express lines (courier advancement or brokerage charges, and a possible MPF minimum). Lines sold as duty-prepaid (JLCPCB DDP, PCBWay DTP/DDP and Global Direct) remove that uncertainty; plain DHL at PCBWay, PCBgogo, NextPCB, Elecrow and Seeed leaves it open.
- JLCPCB may add California sales tax at checkout: its price JSON has a `saleTaxMoney` field and a 2026 user report shows sales tax on a US order. No amount for that ZIP could be read without logging in.

### Gaps
- No tariff, duty or sales-tax dollar amount could be read for this order at any maker: all of them compute it after login, at order submission. Published rates are given instead.
- JLCPCB: whether the Global Standard Direct Line is duty-prepaid, and at what rate, is not stated on its FAQ or notice pages.
- PCBWay: the DTP/DDP service-fee amount is not published on the pages read; the economy-line duty rules come from a 2025-dated section of a notice whose latest dated update is August 15, 2026, so they may have changed.
- PCBgogo "DHL(DDP)": terms could not be read (pop-up shows "undefined"); its only duty help page dates from 2021.
- NextPCB (4PX and DHL), Elecrow (all lines) and Seeed (all lines): no current statement on whether US duty is prepaid, who collects it, or any courier fee. The NextPCB tariffs article and the Seeed 2025 notice do not settle it.
- Courier-side fixed fees (DHL/FedEx/UPS duty-advancement or brokerage fee, MPF) for a sub-$20 China-origin parcel: sources conflict (Altium and NextPCB say formal entry and an MPF minimum of $33.58 apply to all China parcels; JLCPCB's FAQ gives $800 and $2,500 thresholds). No 2026 user report for a bare-PCB order this small was found to settle it.
- US tariff law is changing: the notices cite a new layer from July 24, 2026 and an exclusion expiry on November 10, 2026. Rates here are as published on the dates shown, not verified against US Customs sources.

## 4. Solder-paste stencil added to the same order (framed and frameless)

### Takeaway
A frameless stencil adds $5.00 (Elecrow) to $13.96 (NextPCB) and a framed one $11.28 (JLCPCB) to $17.54 (NextPCB), but the bigger effect is on shipping and duty: a framed stencil pushes the parcel to 1.2 to 2 kg and express freight to $40 to $52, and makers that publish rates apply 77.9% to 90% duty to stencils. A small frameless stencil (JLCPCB custom 100 x 150 mm at $7.22, Seeed 10 x 15 cm at $8.90, Elecrow 15 x 15 cm at $5.00) keeps the parcel light.

### Cited Findings

| Maker | Frameless | Framed | Stencil options selected |
| --- | --- | --- | --- |
| JLCPCB | $7.22 [LIVE] (standard 380 x 280 mm, valid area 360 x 200 mm, 0.8 kg; a custom size of 100 x 150 mm priced the same $7.22) | $11.28 [LIVE] (470 x 370 mm, valid area 290 x 190 mm, 1.5 kg) | Framework No/Yes; Top only; Qty 1; Thickness "Select by JLCPCB"; "Solder paste stencil"; Stencil Build Time 1-2 days $0.00 |
| PCBWay | $10.00 [LIVE] ("Non-framework", "Custom Size (Valid area 190x290mm)") | $15.00 [LIVE] ("Framework", 370x470mm, valid area 190x290mm) | Top; Qty 1; 0.12mm; fiducials None; electropolishing No |
| PCBgogo | $10.00 [LIVE] ("Non-framework", "Custom Size (Valid area 190x290mm)") | $15.00 [LIVE] ("Framework", 370x470mm, valid area 190x290mm) | Top; Qty 1; 0.12mm; fiducials None; electropolishing No |
| NextPCB | $13.96 [LIVE] ("Non-framework", 280x380mm) | $17.54 [LIVE] ("Framework", 370x470mm, valid area 190x290mm) | "PCB+Stencil" tab; Stencil for Solder Paste; Top; 0.10mm; fiducials None; stencil build 48 hours |
| Elecrow | $5.00 [LIVE] ("Stencil 10cm X 10cm no frame"; "Stencil 15cm X 15cm no frame" also $5.00) | $12.90 [LIVE] ("Stencil 30cm X 40cm (+$12.9)"); 37cm X 47cm is "+$15" | Side as defaulted ("Bottom"); Qty 1; "No Fiducial" |
| Seeed Fusion | $8.90 [LIVE] ("10.0cm * 15.0cm Frameless - eff.8*13"); $9.90 for "28.0cm * 38.0cm Frameless - eff.19*29" | $14.50 [LIVE] ("30.0cm * 40.0cm - eff.13*21") | Sides as defaulted ("Top and bottom on the same stencil"); Qty 1; 0.12mm; "No Fiducial"; Polished |
| ALLPCB | [N/A] | [N/A] | |

Sources for the table: [JLCPCB instant quote](https://cart.jlcpcb.com/quote); [PCBWay instant quote](https://www.pcbway.com/orderonline.aspx); [PCBgogo instant quote](https://www.pcbgogo.com/pcb-fabrication-quote.html); [NextPCB instant quote](https://www.nextpcb.com/pcb-quote); [Elecrow PCB quote](https://www.elecrow.com/pcb-manufacturing.html); [Seeed Fusion PCB quote](https://www.seeedstudio.com/fusion_pcb.html)

Effect on shipping (same order: boards plus one stencil)

- JLCPCB, 10 boards + frameless custom 100 x 150 mm (0.59 kg) [LIVE]: UPS Express Saver (DDP) $31.73; DHL Express (DDP) $32.86; FedEx Express (DDP) $44.35; Global Standard Direct Line $13.55. With the standard 380 x 280 mm frameless sheet (1.22 kg): DHL Express (DDP) $37.41. With the framed stencil (1.95 kg): UPS Express Saver (DDP) $43.25; DHL Express (DDP) $40.34; FedEx Express (DDP) $53.11; Global Standard Direct Line not offered (over its 1.5 kg limit). JLCPCB's other frameless sizes run from 420 x 320 mm at $12.64 up to 700 x 600 mm at $28.40. — [JLCPCB instant quote](https://cart.jlcpcb.com/quote)
- PCBWay, 10 boards + frameless (0.44 kg) [LIVE]: DHL $28.95; DHL(DTP) $30.66; FedEx-FICP(DDP) $38.74; Global Standard Shipping $11.45; Global Direct Shipping $10.67; USPS $19.86; SF Express(DDP) $27.77. With the framed stencil (1.64 kg): DHL $40.28. — [PCBWay instant quote](https://www.pcbway.com/orderonline.aspx)
- PCBgogo [LIVE]: the shipping estimate stayed at DHL $32.00 and 0.640 kg after adding either stencil, so the calculator does not appear to weigh the stencil. — [PCBgogo instant quote](https://www.pcbgogo.com/pcb-fabrication-quote.html)
- NextPCB, 10 boards + frameless 280 x 380 mm (1.15 kg) [LIVE]: DHL $37.66; 4PX $20.88. With the framed stencil: DHL $51.38; 4PX $35.80. — [NextPCB instant quote](https://www.nextpcb.com/pcb-quote)
- Elecrow, 10 boards + frameless 10 x 10 or 15 x 15 cm (740 g) [LIVE]: ShenZhen DHL $40.79; Economy Express ZT $17.20; Economy Express $22.07; UPS $34.63; FedEx IP $58.87. With the framed 30 x 40 cm stencil (1240 g): DHL $51.94; Economy Express ZT $24.70; Economy Express $34.47; UPS $42.24; FedEx IP $73.01. — [Elecrow PCB quote](https://www.elecrow.com/pcb-manufacturing.html)
- Seeed Fusion, 5 boards + frameless 10 x 15 cm (0.36 kg) [LIVE]: DHL $27.82 (unchanged). With the 28 x 38 cm frameless sheet (0.56 kg) or the framed 30 x 40 cm stencil (0.86 kg): DHL $108.38. — [Seeed Fusion PCB quote](https://www.seeedstudio.com/fusion_pcb.html)

Duty on stencils

- JLCPCB pre-collects 90.00% on stencils for US DDP orders [PUBLISHED]. — [JLCPCB U.S. Tariff Policy FAQ](https://jlcpcb.com/help/article/us-tariff-policy-faq)
- PCBWay lists stencils at 77.90% (August 15, 2026) [PUBLISHED]. — [PCBWay tariff notice](https://www.pcbway.com/blog/News/Impact_of_the_New_U_S_Tariff_Policy_on_Customs_Clearance_51dff4fd.html)

### Inferences
- [CALC] Lowest add-on cost for a usable frameless stencil with 10 boards, before duty: Elecrow $5.00 stencil + $8.41 extra economy freight ($17.20 - $8.79) = $13.41; JLCPCB $7.22 + $5.63 extra on the Global Standard line ($13.55 - $7.92) = $12.85, or $7.22 + $5.09 extra on UPS DDP ($31.73 - $26.64) = $12.31; PCBWay $10.00 + $3.24 extra on Global Direct ($10.67 - $7.43) = $13.24; Seeed $8.90 + $0 extra on DHL = $8.90.
- [CALC] Stencil duty at published rates: JLCPCB 90% x $7.22 = $6.50 (frameless) or 90% x $11.28 = $10.15 (framed); PCBWay 77.9% x $10.00 = $7.79 or 77.9% x $15.00 = $11.69. The duty roughly doubles the stencil's cost at these two makers.
- A 10 x 10 cm sheet (Elecrow's default) leaves no margin around a 100 mm long board; the 15 x 15 cm sheet costs the same. Seeed's 10 x 15 cm sheet has an effective area of 8 x 13 cm, which covers the 40 x 100 mm board.
- A framed stencil is poor value for a one-off small board: it adds weight, freight and duty, and blocks the cheap economy line at JLCPCB.

### Gaps
- Stencil defaults differ between makers (top only, bottom, or top and bottom on one sheet; 0.10 or 0.12 mm). Prices were read at each maker's default side setting and may differ slightly for other choices.
- PCBgogo's shipping for an order with a stencil could not be read (the estimate ignores the stencil).
- Stencil duty rates for PCBgogo, NextPCB, Elecrow and Seeed: not published on the pages found.
- ALLPCB: no stencil quote.

## 5. Cheapest total landed cost and fastest total, per maker

### Takeaway
Before duty, the cheapest way to get these boards to the door is JLCPCB on its economy line ($10.95 for 5, $12.92 for 10) or PCBWay on Global Direct ($11.56 for 5, $12.43 for 10), with Elecrow close behind ($12.31 / $13.69); all three take roughly 7 to 17 business days. The fastest stated totals are 3 to 5 business days at JLCPCB (24-hour build plus UPS DDP, $38.24 / $39.24 before duty) and PCBWay (standard 24-hour build plus DHL, $31.55 for either quantity before duty), which makes PCBWay the cheapest fast option on the calculators' own numbers.

### Cited Findings
The inputs for this section are the live board prices in section 1, the live shipping prices in section 2 and the published duty rates in section 3; the totals themselves are the researcher's arithmetic and are listed under Inferences. Sources: [JLCPCB instant quote](https://cart.jlcpcb.com/quote); [PCBWay instant quote](https://www.pcbway.com/orderonline.aspx); [PCBgogo instant quote](https://www.pcbgogo.com/pcb-fabrication-quote.html); [NextPCB instant quote](https://www.nextpcb.com/pcb-quote); [Elecrow PCB quote](https://www.elecrow.com/pcb-manufacturing.html); [Seeed Fusion PCB quote](https://www.seeedstudio.com/fusion_pcb.html); [JLCPCB U.S. Tariff Policy FAQ](https://jlcpcb.com/help/article/us-tariff-policy-faq); [PCBWay tariff notice](https://www.pcbway.com/blog/News/Impact_of_the_New_U_S_Tariff_Policy_on_Customs_Clearance_51dff4fd.html)

- PCBWay is the only maker whose calculator states calendar dates for the order: with DHL, "Shipment Date 2026/10/16 AM" and "Delivery Date 2026/10/19" for a quote made on 2026-10-14 China time [LIVE]. — [PCBWay instant quote](https://www.pcbway.com/orderonline.aspx)

### Inferences

All rows are [CALC]: board price + rush fee (if any) + shipping, leaded HASL, regular (not new-customer) prices, **before any US duty, tax or courier fee**. "Days" = stated build time + stated transit, in business days, with no allowance for file review, weekends, holidays or customs.

Cheapest total

| Maker | Route | 5 pcs total | per board | 10 pcs total | per board | Days, order to door |
| --- | --- | --- | --- | --- | --- | --- |
| JLCPCB | 2-day build + Global Standard Direct Line | $10.95 ($4.00 + $6.95) | $2.19 | $12.92 ($5.00 + $7.92) | $1.29 | 10-15 |
| PCBWay | 24-hour build + Global Direct Shipping | $11.56 ($5.00 + $6.56) | $2.31 | $12.43 ($5.00 + $7.43) | $1.24 | 7-13 |
| Elecrow | 3-5 day build + Economy Express (5 pcs) / Economy Express ZT (10 pcs) | $12.31 ($4.90 + $7.41) | $2.46 | $13.69 ($4.90 + $8.79) | $1.37 | 9-16 (5 pcs); 13-17 (10 pcs on ZT; Economy Express at $14.57 gives 9-16) |
| Seeed Fusion | 3-4 day build + Epacket | $18.11 ($9.90 + $8.21) | $3.62 | $19.76 ($9.90 + $9.86) | $1.98 | 18-29 |
| NextPCB | 48-hour build + 4PX | $25.96 ($19.99 + $5.97) | $5.19 | $25.96 | $2.60 | 8-12 |
| PCBgogo | 2-3 day build + DHL or DHL(DDP) (no economy line) | $37.00 ($5.00 + $32.00) | $7.40 | $37.00 | $3.70 | 5-8 |
| ALLPCB | could not obtain | | | | | |

Fastest total

| Maker | Route | 5 pcs total | per board | 10 pcs total | per board | Days, order to door |
| --- | --- | --- | --- | --- | --- | --- |
| PCBWay | standard 24-hour build + DHL | $31.55 ($5.00 + $26.55) | $6.31 | $31.55 | $3.16 | 3-5 (calculator's own dates: about 5-6 calendar days) |
| JLCPCB | 24-hour build (+$7.60) + UPS Express Saver (DDP) | $38.24 ($4.00 + $7.60 + $26.64) | $7.65 | $39.24 ($5.00 + $7.60 + $26.64) | $3.92 | 3-5 |
| NextPCB | 24-hour build + DHL | $50.30 ($24.99 + $25.31) | $10.06 | $50.30 | $5.03 | 3-6 |
| Elecrow | Rush 24h (+$16) + ShenZhen DHL | $50.54 ($4.90 + $16.00 + $29.64) | $10.11 | $50.54 | $5.05 | 3-6 |
| PCBgogo | 2-3 day build + DHL (no rush on the $5 price) | $37.00 | $7.40 | $37.00 | $3.70 | 5-8 |
| Seeed Fusion | 3-4 day build + DHL (no rush offered) | $37.72 ($9.90 + $27.82) | $7.54 | $37.72 | $3.77 | 6-9 |
| ALLPCB | could not obtain | | | | | |

Useful middle options, [CALC], before duty

- JLCPCB, standard 2-day build + UPS Express Saver (DDP): $30.64 (5 pcs, $6.13 each) or $31.64 (10 pcs, $3.16 each); 4-6 business days. This is the cheapest duty-prepaid express route found.
- PCBWay, 24-hour build + DHL(DTP): $33.20 for either quantity, 3-5 business days, plus duty and a service fee shown only at order submission.
- PCBWay 12-hour "Extra Urgent" build + DHL: $121.11 (5 pcs leaded: $94.56 + $26.55); it saves about half a day for about $90.
- Elecrow, Rush 48h (+$5) + DHL: $39.54; 4-7 business days.

Estimated duty added to the above, [CALC] from published rates applied to the product price only (an assumption; see section 3)

- JLCPCB (35%, pre-collected on DDP lines): +$1.40 (5 pcs) / +$1.75 (10 pcs) on the standard build; +$4.06 / +$4.41 if the 24-hour fee is also dutiable. Totals then: cheapest about $12.35 / $14.67 if the economy line is charged the same rate (not confirmed); fastest about $42.30 / $43.65.
- PCBWay (37.5% estimate): +$1.88 on DHL or DHL(DTP) lines, giving about $33.42 on plain DHL; on Global Direct the notice says duty is inside the freight price, so $11.56 / $12.43 would already be landed; on Global Standard or USPS the notice quotes a 30% prepaid tax fee (+$1.50).
- PCBgogo, NextPCB, Elecrow, Seeed: no maker-published rate. At the 37.5% used by PCBWay's notice the duty would be about $1.88 (PCBgogo), $7.50 (NextPCB at $19.99), $1.84 (Elecrow) and $3.71 (Seeed), plus whatever fee the courier charges for collecting it.

Reading across the tables

- For 5 or 10 boards with no hurry, JLCPCB and PCBWay are within about a dollar of each other before duty and both are under $13; PCBWay's economy line is stated as a few days faster (7-13 against 10-15 business days) and its notice says duty is included in that line's freight.
- For speed, PCBWay's standard build is already 24 hours, so its fastest route costs no rush fee; JLCPCB matches the stated days only with its $7.60 24-hour option.
- PCBgogo, NextPCB and Seeed are not competitive for this board at regular prices: PCBgogo has no economy shipping, NextPCB's board price is four to five times the others, and Seeed is both dearer and slower.

### Gaps
- All totals exclude US duty, sales tax and courier fees because no calculator shows them; the duty lines above are estimates.
- "Days" are the makers' stated ranges added together; real elapsed time also depends on file review, the order cut-off time, weekends, Chinese holidays and US customs, none of which the calculators state (PCBWay's stated dates are the one exception).
- JLCPCB's economy line: duty treatment not confirmed, so its landed figure is uncertain by about $1.40 to $1.75.
- ALLPCB: nothing obtained.

## 6. Minimum order quantity, first-order coupons and new-customer prices (kept separate from the normal prices above)

### Takeaway
Five pieces is the smallest quantity every calculator offers. Several new-customer offers would change the ranking if they apply: NextPCB shows a "1st Order" board price of $0.10 instead of $19.99 plus $10 off DHL, PCBgogo advertises a $1 first prototype with up to $25 off DHL shipping, and JLCPCB issues a $6 new-user PCB coupon and a $10 shipping coupon. None of these could be tested because all require an account.

### Cited Findings
- Minimum quantity: the quantity pickers start at 5 pieces at JLCPCB, PCBWay, ALLPCB, PCBgogo, NextPCB, Elecrow and Seeed Fusion [LIVE]. — [JLCPCB instant quote](https://cart.jlcpcb.com/quote); [PCBWay instant quote](https://www.pcbway.com/orderonline.aspx); [ALLPCB instant quote](https://www.allpcb.com/online_pcb_quote_new.html); [PCBgogo instant quote](https://www.pcbgogo.com/pcb-fabrication-quote.html); [NextPCB instant quote](https://www.nextpcb.com/pcb-quote); [Elecrow PCB quote](https://www.elecrow.com/pcb-manufacturing.html); [Seeed Fusion PCB quote](https://www.seeedstudio.com/fusion_pcb.html)
- JLCPCB, channel price: the 5-piece quote shows "$4.00 Web" beside "$2.00 JLCONE Desktop"; the 10-piece quote shows "Order on JLCONE Desktop: Save $1-$20 Per Order" [LIVE]. — [JLCPCB instant quote](https://cart.jlcpcb.com/quote)
- JLCPCB press release dated Aug 22, 2026 [PUBLISHED]: "The signature $2 PCB deal will no longer be available on the JLCPCB website and can only be ordered via JLCONE Desktop"; "a random discount between $1 and $20 will be automatically applied to your order total"; "JLCPCB's special shipping rates have now moved exclusively to JLCONE Desktop"; a welcome coupon package worth "$104 USD". — [JLCPCB JLCONE announcement](https://jlcpcb.com/news/jlcpcb-jlcone-desktop-app)
- JLCPCB new-customer coupons ("Last updated on Sep 09, 2026") [PUBLISHED]: "$6 New User PCB Coupon - Orders over $2 (excluding shipping)"; a $7 New User PCB Stencil coupon (orders over $1); a $10 New User Shipping coupon (shipping orders over $15); "Each coupon must be redeemed separately." The quote page sidebar also shows coupon chips "Save $30.00" and "Save $20.00" [LIVE], whose terms were not read. — [JLCPCB new customer coupons](https://jlcpcb.com/help/article/new-customer-coupons)
- PCBWay: the site header shows "New here? Get a $5.00 Coupon!" [LIVE]; terms not read. — [PCBWay instant quote](https://www.pcbway.com/orderonline.aspx)
- PCBgogo new-user offer [PUBLISHED]: "New users can receive a $1 prototyping discount on their first order"; "New users can enjoy free shipping on their first order, with up to $25 off shipping"; banner says free shipping "to North America and Europe by DHL"; material FR-4; "Expedited service is not available for this orders"; one use per shipping address; not combinable with other offers. The quote page also shows banners for "New User Welcome Coupons ... For Business Users $300, For Individual Users $200" and an "11th Anniversary 10% Off" sale [LIVE]; their terms were not read. — [PCBgogo $1 prototype offer](https://www.pcbgogo.com/1_pcb_prototype_and_free_shipping.html)
- NextPCB: the quote shows "PCB Cost [1st Order] $0.1" against $19.99, and the DHL estimate as $15.31 against $25.31 [LIVE]. Its promotion page says "PCBs Starting from USD$0.1 for New Customers", up to $20 off the PCB order plus an "extra $10 off shipping", the shipping discount applying to DHL and FedEx only, and the offer "expected to end by 12/30/2026" [PUBLISHED]. — [NextPCB instant quote](https://www.nextpcb.com/pcb-quote); [NextPCB discount page](https://www.nextpcb.com/blog/nextpcb-discount)
- Seeed Fusion: coupons offered on the quote page include "PCB Shipping Coupon $5.00 - $5 off for PCB shipping; Valid for 30 days after claiming; One coupon per order", listed as valid until 2026-11-12; the other coupons shown are for PCBA or for orders over $300 [LIVE]. — [Seeed Fusion PCB quote](https://www.seeedstudio.com/fusion_pcb.html)
- Elecrow: no new-customer price or coupon is shown on the PCB quote page [LIVE]. — [Elecrow PCB quote](https://www.elecrow.com/pcb-manufacturing.html)

### Inferences
- [CALC] If the NextPCB first-order price applies as displayed: $0.10 + $15.31 (DHL after $10 off) = $15.41 for 5 or 10 boards in a stated 4 to 7 business days (48-hour build), or $0.10 + $5.97 (4PX, no shipping discount) = $6.07 in 8 to 12 business days. That would make NextPCB the cheapest of all for a first order.
- [CALC] If the PCBgogo first-order offer applies as described: about $1 for the boards plus $32 - $25 = $7 DHL, about $8 total in 5 to 8 days. The page's wording on the board discount is not fully clear, so treat this as approximate.
- [CALC] If JLCPCB's $6 new-user PCB coupon applies to a $4.00 or $5.00 order, the boards are free and only shipping and duty remain; with the $10 shipping coupon on a $26.64 UPS DDP shipment the freight would be $16.64. The rules say each coupon is redeemed separately, so both may not be usable on one order.
- [CALC] Through the JLCONE Desktop channel the 5-piece price is $2.00 instead of $4.00, a $2 saving that does not change the ranking.
- Because 10 boards cost the same as 5 or $1 more at four makers, there is no minimum-order reason to pick 5.

### Gaps
- No coupon or first-order price could be applied or verified: all require creating an account, which was out of bounds. Amounts are as displayed or published.
- Exact terms of the PCBWay $5 coupon, the JLCPCB $30/$20 sidebar coupons and the PCBgogo $200/$300 welcome coupons were not read.
- Whether NextPCB's $0.10 price survives checkout for this exact board, and whether it can be combined with 4PX, is unknown.
- Other China-based makers: none was quoted. No source found in this research showed another well-known China-based maker clearly cheaper or faster than the best figures above (about $11 to $13 delivered on an economy line; 3 to 5 business days by express). A search of comparison articles turned up only vendor-written pieces, which were not used as price sources.
