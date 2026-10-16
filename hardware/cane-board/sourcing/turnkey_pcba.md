# Turnkey PCBA cost, lead time and shipping for 5 and 10 cane boards (prices read October 13, 2026)

How to read these notes

- Every figure carries one of three labels: **[LIVE]** = read from the company's live calculator on October 13, 2026 (US Pacific evening; October 14 morning China time); **[PUBLISHED]** = from a published price or help page; **[NO ACCOUNT]** = could not be obtained without logging in, creating an account or uploading a file (none of which was done).
- The job entered everywhere: 40 x 100 mm, 2 layers, FR-4, 1.6 mm, 1 oz, HASL, green, 1 design; top-side assembly; 42 unique parts (BOM lines); 86 parts per board = 78 surface-mount (about 277 joints) + 8 through-hole (22 joints); no BGA. Quantities 5 and 10.
- No calculator asked for a ZIP code. All shipping figures are to "United States" as a country; the ZIP could not be entered anywhere without an account.
- No parts price was guessed. Where parts need a BOM upload, the parts line is "their quote".
- "Excluding parts" totals are sums made in these notes from the labelled figures; they are not quotes.

## Key question 1: Assembly charge, set-up/stencil/NRE fees, parts pricing rule, bare-board price and total at each company (5 and 10 boards)

### Takeaway
Only four China-based companies give an assembly labour price from numbers alone: PCBWay ($29.00 for 5, $156.20 for 10), PCBgogo ($116.60 / $140.75), Elecrow ($108 + $12 stencil / $109 + $12) and JLCPCB (already costed at $91.39 for 5 including parts). Nobody except JLCPCB prices the parts without a BOM upload to an account, and none of the US assemblers or Bittele shows any assembly price without an account; ALLPCB has suspended its website operations and its calculator returns no price.

### Cited Findings

Summary table (all USD; shipping and duty are in key question 3)

| Company | Assembly labour, 5 | Assembly labour, 10 | Set-up / stencil / NRE | Bare boards, 5 / 10 | Parts | Sum excluding parts and shipping, 5 / 10 |
| --- | --- | --- | --- | --- | --- | --- |
| JLCPCB (given, not re-quoted) | $7.60 soldering | not quoted | $9.71 set-up and stencil + $27.63 for 9 Extended part types | $4.00 / $5.00 [LIVE] | $42.45 for 5 (own catalogue) | $48.94 / not quoted |
| PCBWay | $29.00 [LIVE] | $156.20 [LIVE] | none shown in calculator | $5.00 / $5.00 (leaded HASL; $18.18 for 10 with lead-free HASL) [LIVE] | their quote; "We do not mark up on the parts cost" [PUBLISHED] | $34.00 / $161.20 |
| PCBgogo | $116.60 [LIVE] | $140.75 [LIVE] | stencil fixed at "Yes", not itemised | $5.00 / $5.00 [LIVE] | their quote after registering and uploading; "Components Cost $30 OFF" badge | $121.60 / $145.75 |
| Elecrow | $108.00 [LIVE] | $109.00 [LIVE] | stencil $12.00 [LIVE] | $4.90 / $4.90 [LIVE] | their quote within 1 working day | $124.90 / $125.90 |
| Seeed Fusion | [NO ACCOUNT] | [NO ACCOUNT] | "Setup Cost" and "Consumptive Material Cost" lines exist but show $0.00 until a BOM is uploaded | $9.90 / $9.90 [LIVE] | [NO ACCOUNT] | PCB only: $9.90 / $9.90 |
| NextPCB | [NO ACCOUNT / needs centroid + BOM upload] | same | not shown | $19.99 / $19.99 (48 h); first order $0.10 [LIVE] | [NO ACCOUNT] | PCB only: $19.99 / $19.99 |
| ALLPCB | calculator returns no price; site operations suspended | same | – | – | – | not orderable |
| Bittele (Canada) | [NO ACCOUNT] | [NO ACCOUNT] | [NO ACCOUNT] | $127.29 / $131.81 [LIVE] | [NO ACCOUNT] | PCB only: $127.29 / $131.81 |
| MacroFab, CircuitHub, Screaming Circuits, AdvancedPCB / Advanced Assembly (US) | [NO ACCOUNT] | [NO ACCOUNT] | [NO ACCOUNT] | [NO ACCOUNT] | [NO ACCOUNT] | nothing obtainable |

PCBWay
- Assembly service price for 5 boards is $29.00 ($5.8 each), shown beside a struck-through $270.31; the same panel lists 20 pcs $315.45, 50 pcs $374.78, 200 pcs $700.37, and says "Final price is subject to our review." Inputs: Turnkey; Single pieces; Top side; quantity 5; sensitive components No; accept China-made substitutes No; unique parts 42; SMD parts 78; BGA/QFP parts 0; through-hole parts 8; ship to United States. [LIVE] — [PCBWay assembly calculator](https://www.pcbway.com/quotesmt.aspx)
- Assembly service price for 10 boards with the same inputs is $156.20 ($15.6 each); no struck-through price and no $29 offer. [LIVE] — [PCBWay assembly calculator](https://www.pcbway.com/quotesmt.aspx)
- With "BGA/QFP parts" set to 1 or 2 instead of 0, the 5-board price is $90.78 and the $29 price disappears. [LIVE] — [PCBWay assembly calculator](https://www.pcbway.com/quotesmt.aspx)
- The calculator states: "Price does not include PCB fabrication or the cost of components, exact quotation will be updated after all the files you uploaded pass review." [LIVE] — [PCBWay assembly calculator](https://www.pcbway.com/quotesmt.aspx)
- Bare boards, 100 x 40 mm, 2 layers, FR-4 TG150-160, 1.6 mm, 1 oz, green/white, 6/6 mil, 0.3 mm holes, 24-hour build: 5 pcs $5.00 (HASL with lead or lead-free); 10 pcs $5.00 with "HASL with lead" but $18.18 with the default "HASL lead free"; "Extra Urgent" $94.56–$104.51. [LIVE] — [PCBWay PCB calculator](https://www.pcbway.com/orderonline.aspx)
- Parts: "We do not mark up on the parts cost"; parts come from dependable suppliers "even when they aren't the cheapest" and the customer approves before purchase. [PUBLISHED] — [PCBWay assembly capabilities](https://www.pcbway.com/pcb_prototype/PCB_assembly_Capabilities.html)
- "All components are procured exclusively from authorized distributors on a project basis." [PUBLISHED] — [PCBWay assembly calculator page text](https://www.pcbway.com/quotesmt.aspx)
- Stencil: the assembly page says "PCBA provides free stencil" and, in the same block, lists "$15/pcs"; the page does not resolve the two. The calculator showed no stencil line. [PUBLISHED] — [PCBWay PCB assembly page](https://www.pcbway.com/pcb-assembly.html)
- Parts cost, attrition extras and minimum buy quantities: [NO ACCOUNT] (BOM upload and review needed). — [PCBWay assembly calculator](https://www.pcbway.com/quotesmt.aspx)

PCBgogo
- Assembly cost with Turnkey, Stencil "Yes" (cannot be switched off), Top side, X-ray No, conformal coating No, 42 unique parts, 78 SMD parts, 8 through-hole parts: 5 boards $116.60; 10 boards $140.75; 20 boards $164.90; 1 board $50.00. [LIVE] — [PCBgogo PCBA calculator](https://www.pcbgogo.com/pcba-quote.html)
- The price is driven mainly by the unique-part count: the same 5 boards with 20 unique parts are $50.00; removing the 8 through-hole parts changes nothing ($116.60). [LIVE] — [PCBgogo PCBA calculator](https://www.pcbgogo.com/pcba-quote.html)
- "Price does not include PCB fabrication or the cost of components"; "The price is rough quote. If you need the accurate price with components cost, please register and upload the files." [LIVE] — [PCBgogo PCBA calculator](https://www.pcbgogo.com/pcba-quote.html)
- The Turnkey and Combo options carry a "Components Cost $30 OFF" badge; no terms are shown. [LIVE] — [PCBgogo PCBA calculator](https://www.pcbgogo.com/pcba-quote.html)
- Bare boards, 100 x 40 mm, 2 layers, FR-4 TG150, 1.6 mm, 1 oz, HASL with lead, green/white: $5.00 for 5 and $5.00 for 10, build time 2–3 days. [LIVE] — [PCBgogo PCB calculator](https://www.pcbgogo.com/pcb-fabrication-quote.html)
- Parts price, mark-up rule and attrition: [NO ACCOUNT]; the assembly page publishes no rates. — [PCBgogo assembly page](https://www.pcbgogo.com/pcb-assembly.html)

Elecrow
- With PCBA Qty 5, 42 unique parts, 86 components, 100 x 40 mm, United States: Assembly Cost $108.00, Stencil Cost $12.00, PCB Cost $4.90, Components Cost $0.00 (not yet quoted); "PCBA Cost USD$120.00". [LIVE] — [Elecrow PCB assembly page](https://www.elecrow.com/pcb-assembly.html)
- With PCBA Qty 10: Assembly Cost $109.00, Stencil $12.00, PCB $4.90; "PCBA Cost USD$121.00". [LIVE] — [Elecrow PCB assembly page](https://www.elecrow.com/pcb-assembly.html)
- Sensitivity: 20 unique parts instead of 42 gives $85.00 assembly for 5 boards; 50 components instead of 86 gives $107.00. The price is driven by unique parts, hardly by part count or quantity. [LIVE] — [Elecrow PCB assembly page](https://www.elecrow.com/pcb-assembly.html)
- Formula: "PCBA Quotation = PCB Cost + Stencil Cost + Components Cost + Assembly Cost + Flashing/Testing Cost." Components are priced line by line on a quotation sheet: "Project manager will give the quotation within 1 working day after you submitted enquire." [PUBLISHED] — [Elecrow PCB assembly page](https://www.elecrow.com/pcb-assembly.html)
- Attrition/minimum buys: for 0603/0805/1206 resistors, capacitors and diodes, minimum 50 pieces plus 30 extra; for 0201/0402, minimum 100 plus 50 extra; expensive parts (ICs, connectors) "1-5 pieces based on the total quantity of assemblies." [PUBLISHED] — [Elecrow PCB assembly page](https://www.elecrow.com/pcb-assembly.html)
- Visual inspection is free; an ICT fixture is $300–$1000 per project if wanted; functional test is described as free (one passage limits this to orders over $2000). The stencil is kept three months and not shipped unless asked. [PUBLISHED] — [Elecrow PCB assembly page](https://www.elecrow.com/pcb-assembly.html)
- Orders up to 20 pieces "may" be quoted instantly; "When the price of some materials cannot be obtained online, manual quotation is required." Lead-free assembly only. [PUBLISHED] — [Elecrow PCB assembly page](https://www.elecrow.com/pcb-assembly.html)

Seeed Studio Fusion
- Bare boards 100 x 40 mm, 2 layers, FR-4 TG130, 1.6 mm, HASL, green, 1 oz, 6/6 mil, 0.3 mm holes: $9.90 for 5 and $9.90 for 10; production time 3–4 working days. [LIVE] — [Seeed Fusion order page](https://www.seeedstudio.com/fusion_pcb.html)
- With "PCB Assembly" switched on and PCBA Qty 5, the page shows PCBA Cost, Setup Cost, Consumptive Material Cost, Component Cost and Assembly Cost all at $0.00 and the message "Please login / create an account before uploading your file." All assembly figures are therefore [NO ACCOUNT]. — [Seeed Fusion order page](https://www.seeedstudio.com/fusion_pcb.html)
- "The displayed price is an estimate. Please register and upload your design files to get an accurate quote with component costs." "Final payment will be adjusted after review of unmatched components." [LIVE] — [Seeed Fusion order page](https://www.seeedstudio.com/fusion_pcb.html)
- Coupons shown on the order page (valid until 2026-11-12, 30 days after claiming, one per order): "$50 off PCBA order for new customers. Valid for orders over $1"; "PCBA Special for new customer; $10 off for orders over $1"; "$40 off for orders over $300"; "$5 off for PCB shipping". [LIVE] — [Seeed Fusion order page](https://www.seeedstudio.com/fusion_pcb.html)
- "No Operation Fees on orders over 100 pcs" (the fee for smaller orders is not stated); "No minimum order requirements"; parts priced from Seeed's Open Parts Libraries (over 150,000 local in-stock parts) and live DigiKey/Mouser pricing. [PUBLISHED] — [Seeed PCB assembly page](https://www.seeedstudio.com/pcb-assembly.html)

NextPCB
- Assembly step asks for a centroid file and a BOM file before any "BOM Cost" or "SMT Cost" appears (both show $0.00); assembly labour and parts are [NO ACCOUNT / no upload]. — [NextPCB assembly quote](https://www.nextpcb.com/pcb-assembly-quote)
- Bare boards 100 x 40 mm, 2 layers, FR-4 TG130, 1.6 mm, green, 1 oz, default lead-free HASL: $19.99 at 48 hours or $24.99 at 24 hours, the same for 5 pcs (0.02 m²) and 10 pcs (0.04 m²); a "1st Order" price of $0.10 is shown. [LIVE] — [NextPCB PCB quote](https://www.nextpcb.com/pcb-quote)
- "Expedited production schedules can increase pcb assembly prices by up to 33%." No set-up, stencil, per-joint or mark-up figures are published. [PUBLISHED] — [NextPCB turnkey cost article (posted Sept 2022, updated Nov 2025)](https://nextpcb.com/news/turnkey-pcb-assembly-cost-in-nextpcb)

ALLPCB
- The site carries a banner: "Due to adjustments to the Company's corporate governance structure, our website will temporarily suspend operations effective immediately. Outstanding orders and services will still be fulfilled as agreed." The notice record on the site has a start time of 2026-06-24 16:00 UTC and was created 2026-06-25. [LIVE] — [ALLPCB PCBA quote page](https://www.allpcb.com/pcba_quote.html)
- The PCBA calculator (5 pcs, 40 x 100 mm, single side, 42 unique parts, 277 SMD joints, 22 DIP joints, no panelisation) returned an empty price list and "PCB Assembly Cost: 0". [LIVE] — [ALLPCB PCBA quote page](https://www.allpcb.com/pcba_quote.html)
- Its landing page still advertises "$35 /10 pcs" PCBA and "$30 off Shipping" with no terms. [PUBLISHED] — [ALLPCB online assembly quote page](https://www.allpcb.com/online_pcb_assembly_quote.html)

Bittele Electronics (Canada; production in Shenzhen, option of Malaysia for US clients)
- Bare boards from the online tool (turn-key project, 5 pcs, 40 x 100 mm, 2 layers, 1.0 oz, 1.6 mm, FR4 TG150, green/white, HASL lead-free, 8/8 mil, 0.20 mm drill, IPC Class 2): unit $33.94, extended $169.72, discount −$42.43, total $127.29, lead time 5 days. Price matrix: 10 pcs $131.81; 15 pcs $136.32; 20 pcs $140.83, all 5 days. [LIVE] — [Bittele online ordering](https://www.7pcb.com/Order-PCB)
- The BOM and Assembly Specs steps open a sign-in / registration box; assembly labour, fees and parts are [NO ACCOUNT]. — [Bittele online ordering](https://www.7pcb.com/Order-PCB)
- Published example (vendor blog, date not shown): 20 boards of 80 x 124 mm, 2 layers, one-sided, lead-free, 41 BOM lines, 43 SMT parts priced at $875 for assembly in China with a 4–5 day turn; parts are a separate cost. — [Bittele blog on assembly prices](https://www.7pcb.com/blog/prototype-printed-circuit-board-pcb-assembly-prices-china)
- The online tool gives "a 25% discount on all fabrication orders"; "Our BOM pricing tool ensures you receive the lowest price for your order." [PUBLISHED] — [Bittele online ordering](https://www.7pcb.com/Order-PCB)

US assemblers
- Screaming Circuits: "Create Standard Quote" leads to a portal sign-in; "Custom Quote" leads to an upload page; the public site has only a contact form. The FAQ says the online quote gives "Instant multiline quoting" and a custom quote takes "within 3 business days". No prices, NRE or mark-up are published. [NO ACCOUNT] — [Screaming Circuits home](https://www.screamingcircuits.com/); [Screaming Circuits FAQ](https://www.screamingcircuits.com/faq)
- Screaming Circuits "will order a stencil when needed" and does not make bare boards itself; it orders them through its partner Sunstone Circuits. [PUBLISHED] — [Screaming Circuits FAQ](https://www.screamingcircuits.com/faq)
- CircuitHub: "Upload your PCB design and receive a ready-to-order quote for turnkey assembly in minutes"; the instant-quote button goes to sign-up. Its pricing page says it shows "Price and lead time examples for three boards of varying complexity", but those sit in an embedded app that rendered blank. [NO ACCOUNT] — [CircuitHub platform](https://circuithub.com/platform); [CircuitHub pricing](https://circuithub.com/pricing)
- MacroFab: "Upload your BOM and Gerbers or native design files. Get a detailed, itemized quote ready to order"; quotes show per-unit labour beside material cost and tariff at component level. No prices, NRE or mark-up are published; the old /pricing page returns "Access Denied". [NO ACCOUNT] — [MacroFab PCB assembly](https://macrofab.com/pcb-assembly); [MacroFab FabIQ](https://nws.macrofab.com/fabiq/)
- AdvancedPCB (formerly Advanced Circuits): the "Quote PCB Assembly" button goes to a login page (my4pcb.com); no assembly prices or promotions are published; the listed $33/$66/$99 specials are bare-board offers. [NO ACCOUNT] — [AdvancedPCB assembly services](https://www.advancedpcb.com/en-us/solutions/assembly-services/); [AdvancedPCB home](https://www.advancedpcb.com/en-us/)
- Advanced Assembly (aapcb.com): the site refused the connection on October 13, 2026. Advanced Assembly (Aurora, Colorado) was acquired by Summit Interconnect in 2022; its 2019 "PCB Xpert" online quote tool needed a BOM upload. — [Circuits Assembly on the acquisition](https://circuitsassembly.com/ca/editorial/menu-news/37415-summit-interconnect-acquires-advanced-assembly-royal-circuits.html); [Circuits Assembly on PCB Xpert](https://www.circuitsassembly.com/ca/current/31622-advanced-assembly-introduces-pcb-xpert-a-new-solution-for-ordering-pcbs-and-assembly-online.html)

Other assemblers checked for public instant pricing
- PCBCart's "PCB Assembly Quote" is a form that asks for a name, e-mail and BOM and promises a quotation "within 24-48 hours"; it is not an instant calculator and was not used. — [PCBCart assembly quote](https://www.pcbcart.com/assembly)
- No further assembler with a clearly competitive public calculator was confirmed. A web search named PCBSync (Shenzhen) and ADCOProto (Michigan, BOM upload) as having calculators; neither was opened or verified. — [Circuits Assembly on ADCOProto](https://circuitsassembly.com/ca/current/33729-michigan-based-pcb-assembler-launched-adcoproto-an-instant-prototype-costing-tool-for-design-engineers.html)

JLCPCB (only the bare-board line was re-read, as a check)
- Bare boards 100 x 40 mm, 2 layers: $4.00 for 5 (matches the known breakdown) and $5.00 for 10; PCB build time 2 days at no charge, 24 hours +$7.60. The assembly step asks for Gerber files before it will proceed. [LIVE] — [JLCPCB quote page](https://cart.jlcpcb.com/quote)

### Inferences
- PCBWay is the cheapest assembly labour for 5 boards by a wide margin ($29.00 against $108–$117 at Elecrow and PCBgogo), but only while its promotional price holds; at 10 boards its labour ($156.20) is the highest of the three, and Elecrow ($109 + $12 stencil) and PCBgogo ($140.75) hardly rise with quantity.
- Because PCBWay states it buys from authorised distributors without mark-up, and PCBgogo and Elecrow quote parts line by line, their parts lines for this BOM could differ a lot from JLCPCB's $8.49 a board (JLCPCB sells from its own catalogue). This is unknown until each company quotes the BOM; the difference could go either way and should not be assumed.
- Elecrow's published attrition rule (50 minimum + 30 extra for each 0603/0805/1206 passive value) means roughly 20 passive lines would each be bought as 80 or more pieces whatever the board count, so its parts line will not halve between 10 and 5 boards.
- An extrapolation, not a quote: scaling the known JLCPCB 5-board breakdown to 10 boards (bare boards $5.00 read live; set-up/stencil $9.71 and Extended fees $27.63 unchanged; soldering and parts doubled to $15.20 and $84.90) gives about $142 before shipping and duty. JLCPCB should be re-quoted for 10.
- Sums excluding parts and shipping: 5 boards — PCBWay $34.00, JLCPCB $48.94, PCBgogo $121.60, Elecrow $124.90; 10 boards — Elecrow $125.90, PCBgogo $145.75, PCBWay $161.20 (JLCPCB about $57.50 by the extrapolation above).

### Gaps
- Parts price at every company except JLCPCB: needs a BOM upload to an account (PCBWay, PCBgogo, Elecrow, Seeed, NextPCB, Bittele and all US assemblers).
- Assembly labour, set-up and stencil at Seeed Fusion, NextPCB, Bittele, MacroFab, CircuitHub, Screaming Circuits, AdvancedPCB and Advanced Assembly: not shown without an account or file upload.
- Whether PCBWay charges for the stencil on a $29 order: its page says both "free stencil" and "$15/pcs"; the calculator shows no stencil line.
- Firmware programming / NRE fees: none of the calculators priced them (PCBWay and ALLPCB list "firmware loading"/"IC programming" as options without a price).
- Seeed's "operation fee" and per-part assembly rates: the only detailed explanation found is a 2018 blog post that could not be opened (HTTP 403); no current figures were found.
- CircuitHub's published price examples could not be read (embedded app did not render).

## Key question 2: Minimum order quantity, standard lead time (including buying parts) and paid faster options

### Takeaway
No company in the list has a minimum above 5 boards. Published build times are mostly "after parts are in hand": PCBWay 3–5 days, NextPCB 5 days, Seeed 7 working days with stock parts or 20 with bought-in parts, Elecrow about 3 weeks overall, Bittele 5–16 days, and the US houses 3–10 days. The time to buy parts is published only by Seeed (17 working days) and Elecrow (7–14 days local, 10–21 days imported).

### Cited Findings
- PCBWay: "Our minimum is as low as 5 pieces"; "Our assembly time ranges from 24 Hours to a few weeks"; the turn-time "begins immediately after all the parts are ready" and all files are complete. [PUBLISHED] — [PCBWay assembly capabilities](https://www.pcbway.com/pcb_prototype/PCB_assembly_Capabilities.html)
- PCBWay's assembly page lists "PCBA lead time 3-5 days" beside "$29/20 pcs", and "as quick as 24 hours with 98% on time delivery". [PUBLISHED] — [PCBWay PCB assembly page](https://www.pcbway.com/pcb-assembly.html)
- PCBWay bare boards: 24-hour build at the base price; for an order placed October 13 the calculator showed shipment 2026/10/16 AM and DHL delivery 2026/10/19; "Extra Urgent" is $94.56–$104.51 for these boards. [LIVE] — [PCBWay PCB calculator](https://www.pcbway.com/orderonline.aspx)
- PCBgogo: minimum order 1 piece; "PCBA Lead time according to quotation list from our sales" (no number); bare boards 2–3 days; "PCB fabrication will be started immediately once we confirmed your PCBA order." [LIVE / PUBLISHED] — [PCBgogo PCBA calculator](https://www.pcbgogo.com/pcba-quote.html); [PCBgogo assembly page](https://www.pcbgogo.com/pcb-assembly.html)
- Elecrow: minimum order 1 piece; general lead time "3 weeks (Exact lead time will be given by the project manager)"; local-market parts "within 7-14 days", imported parts (Mouser/DigiKey/Element14) 10–21 days; assembly starts "within 8-48 hours if all necessary files and the parts are ready"; rush is offered "without charging any extra fee"; photo confirmation of a sample may add 2–3 days. [PUBLISHED] — [Elecrow PCB assembly page](https://www.elecrow.com/pcb-assembly.html)
- Seeed Fusion: "No minimum order requirements"; "Fast Turnkey PCBA from 7 working days" when all parts come from its Open Parts Libraries; an expedite service exists but no price is given. [PUBLISHED] — [Seeed PCB assembly page](https://www.seeedstudio.com/pcb-assembly.html)
- Seeed Fusion: "Production time (7 days) = PCB Manufacture (4 days) + Assembly (3 days)" for all-OPL orders; "Production time (20 days) = Parts Procurement (17 days) + Assembly (3 days)" with externally sourced parts; working days, order confirmation to dispatch, shipping excluded (article last modified 2018/11/25). [PUBLISHED] — [Seeed lead-time article](https://support.seeed.cc/portal/en/kb/articles/what-is-the-lead-time-for-seeed-fusion-pcb-assembly-orders)
- Seeed bare boards: 3–4 working days; a "PCBA Expedited Service" tick-box exists on the order form (price not shown without a BOM). [LIVE] — [Seeed Fusion order page](https://www.seeedstudio.com/fusion_pcb.html)
- NextPCB: quantity menu starts at 5; bare boards 48 hours ($19.99) or 24 hours ($24.99) [LIVE]; the article lists "24 hours Launch (parts ready)" and "5 Days Standard Turnaround"; expedite can add up to 33% [PUBLISHED]. — [NextPCB PCB quote](https://www.nextpcb.com/pcb-quote); [NextPCB turnkey cost article](https://nextpcb.com/news/turnkey-pcb-assembly-cost-in-nextpcb)
- JLCPCB: quantity menu starts at 5; PCB build 2 days at no charge or 24 hours for +$7.60. [LIVE] — [JLCPCB quote page](https://cart.jlcpcb.com/quote)
- Bittele: "Typical turnaround times range from 5 to 16 days" depending on complexity and volume; bare boards 5 days in the online tool; no minimum stated ("prototype and low- to mid-volume"). [PUBLISHED / LIVE] — [Bittele assembly page](https://www.7pcb.com/PCB-Assembly-China); [Bittele online ordering](https://www.7pcb.com/Order-PCB)
- Screaming Circuits: "The minimum order size is one"; the FAQ mentions "5- and 10-day assembly times" and "24- and 48-hour assembly orders"; turn time starts the day all materials are received by the noon cut-off. [PUBLISHED] — [Screaming Circuits FAQ](https://www.screamingcircuits.com/faq)
- CircuitHub: "Select a lead time as fast as 3 days"; its live metric says 81% of orders shipped within 3 days and 98.23% shipped on time; no minimum stated. [PUBLISHED] — [CircuitHub platform](https://circuithub.com/platform)
- CircuitHub keeps small orders on its fast prototype lines if they have no firmware, no more than 500 through-hole placements and no more than 50 unique through-hole part numbers per order, no more than 5 BOM lines of 0201 parts, and boards under 400 mm. [PUBLISHED] — [CircuitHub docs](https://docs.circuithub.com/getting-a-quote/cost-and-lead-time-triggers-for-prototypes)
- MacroFab: "No contracts, no minimums"; minimum billable board area 1 in²; no lead time stated. [PUBLISHED] — [MacroFab PCB assembly](https://macrofab.com/pcb-assembly)
- AdvancedPCB: "no minimum order quantities"; quick-turn "3, 5, and 10-day turns"; "many standard prototype orders completed in 5 to 10 business days"; assembly time starts after fabrication and once all parts are received. [PUBLISHED] — [AdvancedPCB assembly services](https://www.advancedpcb.com/en-us/solutions/assembly-services/)

### Inferences
- This job (no firmware, 8 through-hole parts on 6 lines, 0603 smallest passives) stays under every CircuitHub "prototype line" limit, so its fastest lead times should be available; the price is unknown.
- A cane board that needs its ESP32 flashed at the factory would trip CircuitHub's "No firmware" limit; flashing after delivery over the USB-C socket avoids that.
- For PCBWay, PCBgogo and NextPCB the real lead time is build time plus an unpublished parts-buying time plus quote review; only Seeed and Elecrow publish the parts-buying time.

### Gaps
- Parts procurement time at PCBWay, PCBgogo, NextPCB, Bittele and all US assemblers: not published.
- Prices of expedite options at every company except NextPCB's "up to 33%": not shown without a BOM-based quote.
- MacroFab lead times: not on its public pages.
- JLCPCB assembly build time for this order was not read (the assembly step needs Gerber files); only the PCB build time was visible.

## Key question 3: Shipping methods, prices and transit times to that ZIP; US tariff, duty and tax; California sales tax and US build for US assemblers

### Takeaway
Express courier from China costs $27–$33 for a parcel of this size and takes 2–5 business days at every company; economy lines cost $7–$15 and take 6–13 business days. JLCPCB pre-collects 35% duty at checkout on US orders; PCBWay and PCBgogo offer duty-prepaid courier options but their ordinary quotes say duties are not included, so a US buyer should expect roughly 35–37.5% on the declared value either at checkout or from the courier.

### Cited Findings

JLCPCB shipping and duty (the only JLCPCB items requested)
- Shipping options to the United States for a 5-board bare-PCB cart (0.19 kg): UPS Express Saver (DDP) $26.64, 2–4 business days; DHL Express (DDP) $31.44, 2–4 business days; DHL Express $31.44, 2–4 business days; FedEx Express (DDP) $31.70, 2–5 business days; Global Standard Direct Line $6.95, 8–13 business days, limited to ≤1.5 kg, ≤$59 and ≤55 x 40 cm; own DHL/UPS/FedEx account $2.00; sea shipment only for 100–10,000 kg. [LIVE] — [JLCPCB quote page](https://cart.jlcpcb.com/quote)
- At 0.26 kg (10 bare boards) the express prices are unchanged and Global Standard Direct Line is $7.92; at 0.54 kg (30 bare boards) DHL Express (DDP) is $32.86. [LIVE] — [JLCPCB quote page](https://cart.jlcpcb.com/quote)
- Global Standard Direct Line delivery record shown by JLCPCB: 3.24% delivered within 5 business days, 26.05% within 7, 81.08% within 10, 99.53% within 15. [LIVE] — [JLCPCB quote page](https://cart.jlcpcb.com/quote)
- JLCPCB's pre-collected US DDP tariff rates since March 17, 2026: PCB 35.00%, SMT (PCBA) 35.00%, stencil 90.00%. [PUBLISHED] — [JLCPCB tariff policy updates](https://jlcpcb.com/blog/logistics-policy-updates-due-to-the-us-tariff-on-china)
- JLCPCB's FAQ (last updated Sep 09, 2026) lists Section 301 at 25% plus a 10% provisional tariff, total "About 35%~92.5%"; for the 35%–90% range JLCPCB will "not refund or charge the difference". US individual orders must ship DDP; US companies may choose CPT and pay import taxes themselves. No separate brokerage or handling fee is listed. [PUBLISHED] — [JLCPCB US tariff FAQ](https://jlcpcb.com/help/article/us-tariff-policy-faq)
- The FAQ does not say what value the 35% is applied to. A May 2026 forum post reports $479.11 customs on about $1,369 of PCB and assembly charges (about 35%). [user report, cross-check only] — [EEVblog forum thread](https://www.eevblog.com/forum/manufacture/jlc-tarriffs-etc-to-us/)

PCBWay
- Shipping options to the United States for the 5-board assembly quote (0.50 kg): DHL $28.95, 2–4 business days; DHL (DTP) $30.66, 2–4; FedEx-FICP (DDP) $39.03, 3–5; FedEx-IP $41.99, 3–5; FedEx-FICP $38.06, 3–5; FedEx-IP (DDP) $43.06, 3–5; Global Standard Shipping $14.81, 7–12; Global Direct Shipping $13.58, 6–12; USPS $22.05, 6–12; SF Express (DDP) $27.77, 6–8 business days. [LIVE] — [PCBWay assembly calculator](https://www.pcbway.com/quotesmt.aspx)
- The assembly quote shows "Shipping: $28.95" and "Order discount: $-28.95", so shipping nets to $0 on both the 5-board ($29.00 total) and 10-board ($156.20 total) quotes; the page advertises "PCB Assembly UP to $30 Freight Deduction". [LIVE] — [PCBWay assembly calculator](https://www.pcbway.com/quotesmt.aspx)
- "Notice: Customs duties and VAT are not included!" For the DTP/DDP options: "Pre-pay customs duties & taxes by PCBWay are required for DHL (DTP), and DTP charges service fee. The above fees (duties & taxes and service fee) are calculated when order is confirmed, and here shows only shipping cost." [LIVE] — [PCBWay assembly calculator](https://www.pcbway.com/quotesmt.aspx)
- A bare-PCB-only order of 5 boards (0.07 kg) is quoted $26.55 by DHL, with no discount. [LIVE] — [PCBWay PCB calculator](https://www.pcbway.com/orderonline.aspx)
- User report (December 2024, before the 2025–26 changes): a US customer was charged about $588 import duty on a $711 flex PCBA order from PCBWay. [user report, cross-check only] — [PCBWay Q&A](https://www.pcbway.com/project/question/Excessive_import_duty_to_USA.html)

PCBgogo
- Bare-PCB cart to the United States (0.57–0.64 kg): DHL $32, 3–5 days; DHL (DDP) $32, 3–5 days; FedEx-IP $60, 3–5 days. [LIVE] — [PCBgogo PCB calculator](https://www.pcbgogo.com/pcb-fabrication-quote.html)
- On the assembly quote the shipping line reads "$?" (0.500 kg, 3–5 days); the price is [NO ACCOUNT]. — [PCBgogo PCBA calculator](https://www.pcbgogo.com/pcba-quote.html)
- The shipping guide gives general times (DHL 3–7 business days, FedEx 4–7, EMS 15–30) and says nothing about US duties or DDP fees. [PUBLISHED] — [PCBgogo shipping guide](https://www.pcbgogo.com/shipping_method_guide.html)

Elecrow
- Shipping to the United States for the 5-board assembly (100 x 40 mm): ShenZhen DHL $29.64; UPS $33.34; UPS Direct Line $43.18; FedEx IP $49.28; Economy Express ZT $8.57; Economy Express $9.30. For 10 boards the express prices are the same and Economy Express ZT is $10.57, Economy Express $12.65. Transit times are not shown. [LIVE] — [Elecrow PCB assembly page](https://www.elecrow.com/pcb-assembly.html)

Seeed Fusion
- Shipping estimate to the United States for the bare boards: $27.82 by DHL, 3–5 working days (0.064 kg for 5, 0.13 kg for 10). [LIVE] — [Seeed Fusion order page](https://www.seeedstudio.com/fusion_pcb.html)
- The PCB Assembly option carries a "FREE express shipping!" badge, and the assembly page says "Free Shipping on all PCBA orders." [LIVE / PUBLISHED] — [Seeed Fusion order page](https://www.seeedstudio.com/fusion_pcb.html); [Seeed PCB assembly page](https://www.seeedstudio.com/pcb-assembly.html)
- Seeed's only tariff notice found is dated May 14, 2025 (expected about 30%, with "Reimbursement for Overpayments, Payment for Underpayments"); it is out of date. [PUBLISHED] — [Seeed tariff notice](https://www.seeedstudio.com/blog/2025/05/14/navigating-recent-u-s-tariff-adjustment-update/)

NextPCB
- Shipping estimate to the United States for the bare boards by DHL: $15.31 shown beside $25.31, 2–5 business days (0.08 kg for 5, 0.15 kg for 10). [LIVE] — [NextPCB PCB quote](https://www.nextpcb.com/pcb-quote)
- NextPCB's own August 2026 article says China-origin PCBs and assemblies face a combined Section 301 rate of 37.5% (25% plus a 12.5% layer from July 24, 2026) on top of the base duty, that the $800 de minimis exemption no longer applies to China, that a Merchandise Processing Fee minimum of about $33.58 applies per formal entry, and that 178 exclusions (many for 2- and 4-layer bare boards) are due to expire November 10, 2026. It does not say whether NextPCB ships duty-paid. [PUBLISHED, vendor blog] — [NextPCB tariff article](https://www.nextpcb.com/blog/pcb-manufacturing-tariffs-2026-china-sourcing)

Bittele
- "We use Fedex international Priority (Overnight Service)"; the online estimate excludes shipping. [LIVE] — [Bittele online ordering](https://www.7pcb.com/Order-PCB)
- Bittele's tariff page (latest notice 09/23/2025) says every US shipment "is subject to duties, taxes, fees, and additional documentation" and asks clients for "duty/tax payer details"; it gives no rates. US clients can order assembly from a Malaysia facility (notice of 02/11/2025). [PUBLISHED] — [Bittele tariff statement](https://www.7pcb.com/Tariff-Statement)

US assemblers: location and tax
- Screaming Circuits: default carrier UPS at the service level the customer picks; the only address given is in Canby, Oregon 97013; sales tax is not mentioned. [PUBLISHED] — [Screaming Circuits FAQ](https://www.screamingcircuits.com/faq)
- MacroFab: "ITAR-registered manufacturing facilities in the United States"; corporate office in Houston, Texas; shipping and tax not stated. [PUBLISHED] — [MacroFab FabIQ](https://nws.macrofab.com/fabiq/); [MacroFab PCB assembly](https://macrofab.com/pcb-assembly)
- AdvancedPCB describes itself as a "U.S.-based operation" with domestic manufacturing; no city is named for assembly. [PUBLISHED] — [AdvancedPCB assembly services](https://www.advancedpcb.com/en-us/solutions/assembly-services/)
- CircuitHub offers standard and expedited shipping and customer courier accounts; factory location and sales tax are not stated on the pages read. [PUBLISHED] — [CircuitHub docs](https://docs.circuithub.com/getting-started/concepts)
- The combined sales tax rate for the Bay Area ZIP used is listed as 9.75% as of September 2026 (after a district change on April 1, 2026); this is from secondary rate tables, not the state lookup. — Kintsugi's county rate table; [TaxCloud 2026 update](https://taxcloud.com/sales-tax-radar/2026-california-sales-tax-updates)

### Inferences
- JLCPCB duty estimate for the known 5-board order: 35% of $91.39 is about $31.99, if the rate is applied to the goods total (the forum report suggests it is). With UPS Express Saver (DDP) at $26.64 that makes about $150.02 landed; with DHL Express (DDP) about $154.82. These are estimates: the shipping price was read for a bare-board cart (0.19–0.54 kg cost $31.44–$32.86 by DHL), and the assembled weight could not be read without Gerber files.
- JLCPCB's cheap Global Standard Direct Line is limited to "≤$59"; if that is the order value, the $91.39 order cannot use it and express DDP ($26.64 and up) is the realistic choice.
- PCBWay's ordinary DHL price is duty-unpaid: the courier would bill duty (and possibly its own fee) on delivery, at about 35–37.5% of whatever value PCBWay declares. Its DTP/DDP options add duty plus a service fee at order confirmation; neither amount is visible before an order exists.
- Seeed's free express shipping on assembly orders is worth about $28 against the others, and its $50 new-customer assembly coupon could remove most or all of a small order's labour charge; both need an account to confirm.
- US-built boards carry no import duty but, if the seller collects California tax, 9.75% is added; Chinese sellers showed no sales-tax line in any calculator.

### Gaps
- No calculator accepted the Bay Area ZIP; ZIP-specific rates (and any remote-area surcharge) were not obtainable without an account.
- Exact duty and "service fee" for PCBWay DHL (DTP)/FedEx (DDP), PCBgogo DHL (DDP) and whatever Elecrow, Seeed and NextPCB do for US orders in 2026: not published on the pages found; no 2026 tariff notice was found for PCBWay, PCBgogo, Elecrow or Seeed.
- Sources disagree on the legal make-up of the extra layer after July 24, 2026: JLCPCB's FAQ still pre-collects 35% (25% + 10%), while NextPCB's article gives 37.5% (25% + 12.5%). The current statutory rate was not checked against official US sources here.
- What "ZT" and "Direct Line" mean in Elecrow's shipping list, and their transit times: Elecrow's shipping page returned a 404.
- Whether Screaming Circuits, MacroFab, CircuitHub and AdvancedPCB collect California sales tax, their shipping prices to that ZIP, and CircuitHub's factory location: not found on public pages.
- JLCPCB shipping price for the actual assembled parcel: needs Gerber files in the cart.

## Key question 4: Conditions on headline offers, and whether this job qualifies

### Takeaway
PCBWay's "$29 for up to 20 boards" assembly offer has no published conditions, but the live calculator applies it only to small total part counts: this job gets $29 for 5 or 6 boards and loses it from 7 boards up, and loses it at any quantity if one part is counted as BGA/QFP. Seeed's coupons and free shipping, PCBgogo's "$30 off components" and NextPCB's "Free for 10pcs" banner all need an account or have terms that are not shown.

### Cited Findings
- PCBWay advertises "Only 29$ for 20pcs PCBA & Component sourcing & Online quote & 24h delivery services" and "$29/20 pcs", with no stated limits on part count, package type or board size. [PUBLISHED] — [PCBWay PCB assembly page](https://www.pcbway.com/pcb-assembly.html)
- Live probes of PCBWay's calculator (Turnkey, single pieces, top side, United States; inputs given as quantity / unique parts / SMD parts per board / BGA-QFP parts / through-hole parts per board), all [LIVE] — [PCBWay assembly calculator](https://www.pcbway.com/quotesmt.aspx):
  - 5 / 42 / 78 / 0 / 8 → $29.00 (this job, 430 parts in total)
  - 6 / 42 / 78 / 0 / 8 → $29.00 (516 parts)
  - 7 / 42 / 78 / 0 / 8 → $117.15 (602 parts)
  - 8 / 42 / 78 / 0 / 8 → $130.08
  - 10 / 42 / 78 / 0 / 8 → $156.20 (860 parts)
  - 20 / 42 / 78 / 0 / 8 → $315.45
  - 5 / 42 / 78 / 1 / 8 and 5 / 42 / 78 / 2 / 8 → $90.78
  - 5 / 42 / 101 / 0 / 8 → $29.00 (545 parts); 6 / 42 / 84 / 0 / 8 → $29.00 (552 parts)
  - 10 / 42 / 50 / 0 / 8 → $29.00 (580 parts); 10 / 42 / 50 / 0 / 10 → $116.64 (600 parts)
  - 5 / 60 / 78 / 0 / 8 → $29.00; 5 / 100 / 100 / 0 / 8 → $107.52
  - 20 / 42 / 25 / 0 / 5 → $261.44 (600 parts); 21 / 42 / 20 / 0 / 2 → $270.56
  - 20 / 10 / 30 / 0 / 0 → $88.00, shown beside a struck-through $124.25
- PCBWay's quote panel says "Final price is subject to our review", and the calculator text says the exact quotation follows file review. [LIVE] — [PCBWay assembly calculator](https://www.pcbway.com/quotesmt.aspx)
- PCBWay's up-to-$30 freight deduction appeared on both the $29.00 and the $156.20 assembly quotes. [LIVE] — [PCBWay assembly calculator](https://www.pcbway.com/quotesmt.aspx)
- Seeed Fusion coupons: "$50 off PCBA order for new customers. Valid for orders over $1. Valid for 30 days after claiming. One coupon per order" and a "$10 off" PCBA special for new customers, both shown as valid until 2026-11-12. [LIVE] — [Seeed Fusion order page](https://www.seeedstudio.com/fusion_pcb.html)
- Seeed's older "free assembly for 5 PCBs" offer: its help centre has an entry about the offer's termination (text not retrieved); the current order page does not show it. [search result only] — [Seeed Fusion PCB Assembly FAQ index](https://support.seeedstudio.com/knowledgebase/topics/150804-fusion-pcb-assembly-faq)
- NextPCB's site banner advertises "Free for 10pcs" and "50%OFF for 100pcs" turnkey assembly without terms on the page read. Its 100-piece offer needs exactly 100 PCBA pieces and assembly fees of at least $300, excludes components, and expires December 31, 2026 (page updated June 2026). [PUBLISHED] — [NextPCB free assembly article](https://www.nextpcb.com/blog/free-pcb-assembly); [NextPCB turnkey cost article](https://nextpcb.com/news/turnkey-pcb-assembly-cost-in-nextpcb)
- An older NextPCB offer page (found in search, not opened) is described as free assembly for up to 5 boards limited to 30 or fewer unique BOM lines and 100 or fewer parts per board, with PCBs, parts and shipping still charged. [search result only] — [NextPCB free assembly (mobile page)](https://mobile.nextpcb.com/blog/Free-PCB-Assembly)
- NextPCB "1st Order" bare-board price of $0.10 instead of $19.99. [LIVE] — [NextPCB PCB quote](https://www.nextpcb.com/pcb-quote)
- PCBgogo "Components Cost $30 OFF" on turnkey orders; no terms shown. [LIVE] — [PCBgogo PCBA calculator](https://www.pcbgogo.com/pcba-quote.html)
- ALLPCB "$35 /10 pcs" PCBA and "$30 off Shipping": not usable while the site's operations are suspended. [PUBLISHED / LIVE] — [ALLPCB online assembly quote page](https://www.allpcb.com/online_pcb_assembly_quote.html); [ALLPCB PCBA quote page](https://www.allpcb.com/pcba_quote.html)
- JLCPCB shows "Assembly cost starting from $0 with coupon" and "Save $30.00 / Save $20.00" coupon tags on its quote page; terms need an account. [LIVE] — [JLCPCB quote page](https://cart.jlcpcb.com/quote)

### Inferences
- The probes fit one rule: PCBWay's $29 price applies when quantity is at most 20, no part is entered as BGA/QFP, the unique-part count is below some limit between 60 and 100, and the total number of parts in the order (boards x parts per board) is below about 600 (580 qualifies, 600 does not). This rule is inferred from the calculator; PCBWay does not publish it.
- This job qualifies at 5 boards (430 parts) and at 6 boards (516 parts), and does not qualify at 10 boards (860 parts). "Up to 20 boards" is true only for boards with fewer than about 30 parts each.
- The biggest risk to the $29 price is PCBWay's file review: if its engineers class the HTSSOP-16 with thermal pad, the ESP32-S3-WROOM-1 module (pads under the body) or the 16-pin USB-C socket as a BGA/QFP-type part, the 5-board labour becomes $90.78. Nothing on the site defines the class.
- Ten boards ordered as two separate 5-board assembly orders would each price at $29 in the calculator; whether PCBWay would accept that on review is unknown.
- Under the older NextPCB terms described in search (30 unique lines, 100 parts per board), this 42-line board would not qualify for free assembly; the current "Free for 10pcs" terms are not known.

### Gaps
- PCBWay's written terms for the $29 offer: its promotion page carries the terms only as images; no text version was found.
- Terms of NextPCB's "Free for 10pcs", PCBgogo's "$30 off components" and JLCPCB's assembly coupons: not shown without an account.
- Whether Seeed's $50 new-customer coupon can be combined with free shipping, and what Seeed's labour and set-up come to for this board: needs an account and BOM upload.

## Key question 5: Ranking by landed cost (5 and 10 boards) and by days from order to door

### Takeaway
A complete landed total can be built only for JLCPCB: about $150 for 5 boards with pre-paid duty (an estimate). On the parts-excluded figures that could be read, PCBWay is cheapest for 5 boards ($34.00 with shipping netted to zero) and Elecrow or PCBgogo for 10 ($136–$178 with shipping), but every one of those still needs a parts quote and duty added, so no company other than JLCPCB can be ranked on true landed cost yet. On speed, the US assemblers and JLCPCB/PCBWay by express courier are the fastest on paper; Seeed with bought-in parts and Elecrow are the slowest.

### Cited Findings
- JLCPCB, 5 boards: $91.39 goods including parts (given), plus express DDP shipping $26.64 (UPS) to $31.70 (FedEx) [LIVE], plus 35% pre-collected duty [PUBLISHED]. — [JLCPCB quote page](https://cart.jlcpcb.com/quote); [JLCPCB tariff policy updates](https://jlcpcb.com/blog/logistics-policy-updates-due-to-the-us-tariff-on-china)
- PCBWay, 5 boards: assembly $29.00 + boards $5.00 + shipping $28.95 − $28.95 discount = $34.00 before parts and duty; 10 boards: $156.20 + $5.00 (leaded HASL) = $161.20 before parts and duty. [LIVE] — [PCBWay assembly calculator](https://www.pcbway.com/quotesmt.aspx); [PCBWay PCB calculator](https://www.pcbway.com/orderonline.aspx)
- Elecrow: its own total for 5 boards with ShenZhen DHL is "Total Price USD$ 154.54" (assembly $108 + stencil $12 + PCB $4.90 + shipping $29.64) before parts; for 10 boards $155.54. With Economy Express ZT the sums are $133.47 and $136.47. [LIVE] — [Elecrow PCB assembly page](https://www.elecrow.com/pcb-assembly.html)
- PCBgogo: 5 boards $116.60 + $5.00 + $32 DHL = $153.60 before parts; 10 boards $140.75 + $5.00 + $32 = $177.75 before parts (shipping read from the bare-PCB calculator). [LIVE] — [PCBgogo PCBA calculator](https://www.pcbgogo.com/pcba-quote.html); [PCBgogo PCB calculator](https://www.pcbgogo.com/pcb-fabrication-quote.html)
- Bittele: bare boards alone are $127.29 (5) and $131.81 (10) before any assembly, parts or shipping. [LIVE] — [Bittele online ordering](https://www.7pcb.com/Order-PCB)
- Lead-time figures used for the speed ranking are those cited under key question 2 and the transit times under key question 3. — [PCBWay PCB assembly page](https://www.pcbway.com/pcb-assembly.html); [Seeed lead-time article](https://support.seeed.cc/portal/en/kb/articles/what-is-the-lead-time-for-seeed-fusion-pcb-assembly-orders); [Elecrow PCB assembly page](https://www.elecrow.com/pcb-assembly.html); [CircuitHub platform](https://circuithub.com/platform); [Screaming Circuits FAQ](https://www.screamingcircuits.com/faq); [AdvancedPCB assembly services](https://www.advancedpcb.com/en-us/solutions/assembly-services/)

### Inferences

Cost ranking, 5 boards (sums made here; "+ parts" means the company's own parts quote is still missing; duty for China-origin goods is roughly 35–37.5% of declared value unless stated)

| Rank | Company | What is known | Still to add |
| --- | --- | --- | --- |
| 1 (only complete total) | JLCPCB | about $150.02 landed: $91.39 + $26.64 UPS DDP + about $31.99 duty (estimate) | nothing, but re-check shipping with the real parcel weight |
| likely lowest before parts | PCBWay | $34.00 with shipping netted to zero ($95.78 if a part is classed BGA/QFP) | parts quote; duty (courier-collected, or pre-paid plus service fee) |
| 3 | Elecrow | $133.47 (economy line) or $154.54 (DHL) | parts quote; duty |
| 4 | PCBgogo | $153.60 with DHL | parts quote (a "$30 off" badge applies); duty |
| not rankable | Seeed Fusion | PCB $9.90; shipping stated free on assembly orders; $50 new-customer coupon | labour, set-up, materials, parts; duty |
| not rankable | NextPCB | PCB $19.99 ($0.10 on a first order); DHL $15.31 | labour, fees, parts; duty |
| not rankable, clearly dearer | Bittele | PCB alone $127.29 | assembly, parts, FedEx shipping, duty |
| not rankable | MacroFab, CircuitHub, Screaming Circuits, AdvancedPCB / Advanced Assembly | nothing public | everything; sales tax 9.75% if collected; no import duty on US-built boards |
| not orderable | ALLPCB | site operations suspended | – |

Cost ranking, 10 boards

| Rank | Company | What is known | Still to add |
| --- | --- | --- | --- |
| likely lowest | JLCPCB | not quoted; an extrapolation of the 5-board breakdown gives about $142 goods including parts, so roughly $219–$224 landed with express DDP and 35% duty (estimate, to be re-quoted) | a real 10-board quote |
| lowest before parts | Elecrow | $136.47 (economy line) or $155.54 (DHL) | parts quote; duty |
| 3 | PCBWay | $161.20 with shipping netted to zero | parts quote; duty |
| 4 | PCBgogo | $177.75 with DHL | parts quote; duty |
| not rankable | Seeed, NextPCB, Bittele, all US assemblers | as for 5 boards (Bittele PCB alone $131.81) | as for 5 boards |

- Per board, on the figures above: JLCPCB about $30.00 landed for 5 (estimate) and about $22 for 10 (extrapolation); PCBWay $6.80 a board for 5 and $16.12 for 10 before parts and duty; Elecrow $26.69–$30.91 for 5 and $13.65–$15.55 for 10 before parts and duty; PCBgogo $30.72 for 5 and $17.78 for 10 before parts and duty.
- For PCBWay to beat JLCPCB's roughly $150 landed for 5 boards, its parts quote plus duty would have to stay under about $116; for Elecrow ($133.47–$154.54) and PCBgogo ($153.60) the known costs alone are already within about $17 of, or above, JLCPCB's whole landed total, so they will almost certainly be dearer for 5 boards once parts and duty are added.
- For 10 boards, Elecrow, PCBWay and PCBgogo are each at $136–$178 before parts and duty, against an extrapolated JLCPCB figure of about $142 including parts; JLCPCB is very likely the cheapest at 10 as well, subject to a real quote.

Speed ranking, order to door (built from published build and transit times; parts-buying time is unpublished at most companies, so these are estimates)

| Rank | Company | Published basis | Estimated order-to-door |
| --- | --- | --- | --- |
| 1 | CircuitHub (US) | lead time "as fast as 3 days"; 81% of orders shipped within 3 days | under a week plus domestic shipping; price unknown |
| 2 | Screaming Circuits (US) | 24-hour, 48-hour, 5-day and 10-day assembly after materials arrive; boards bought in from Sunstone | about 1–3 weeks depending on turn chosen; price unknown |
| 3 | AdvancedPCB (US) | 3, 5 and 10-day turns; "5 to 10 business days" typical, after fab and parts | about 1–3 weeks; price unknown |
| 4 | JLCPCB | PCB 2 days (24 h for $7.60); express 2–4 business days | assembly build time not read; shipping adds 2–4 business days, or 8–13 by the economy line |
| 5 | PCBWay | PCB 24 h; "PCBA lead time 3-5 days" once parts are ready; DHL 2–4 business days | roughly 1.5–2.5 weeks once the quote is approved; parts-buying time unknown |
| 6 | NextPCB | "5 Days Standard Turnaround" with parts ready; DHL 2–5 business days | roughly 2–3 weeks; parts-buying time unknown |
| 7 | Bittele | turnkey "5 to 16 days"; FedEx International Priority | roughly 1.5–4 weeks |
| 8 | PCBgogo | PCB 2–3 days; assembly time only "according to quotation list from our sales"; DHL 3–5 days | unknown until quoted |
| 9 | Seeed Fusion | 7 working days if every part is in its stock library, 20 working days otherwise; DHL 3–5 working days | about 2 weeks at best; about 5 weeks with bought-in parts (whether this BOM's parts are in Seeed's stock library is unknown) |
| 10 | Elecrow | "3 weeks" general; parts 7–14 days local or 10–21 days imported | about 4 weeks with express shipping; longer by the economy line |
| – | MacroFab | no lead time published | unknown |
| – | ALLPCB | not taking new orders | – |

- The US assemblers are the fastest on paper and avoid import duty, but none publishes a price; for a 5–10 board order they are very likely several times the China totals (Bittele's bare boards alone cost more than JLCPCB's whole assembled order), though that cannot be shown without an account-based quote.

### Gaps
- True landed totals for every company except JLCPCB: blocked by the missing parts quotes and, for China-origin shipments other than JLCPCB, by unpublished duty handling.
- A real JLCPCB quote for 10 boards (the figure above is an extrapolation of the 5-board breakdown).
- Any price at all from MacroFab, CircuitHub, Screaming Circuits, AdvancedPCB / Advanced Assembly and, for assembly, Bittele, Seeed and NextPCB: each needs an account and a BOM (and usually Gerber) upload. With no routed board yet, CircuitHub and MacroFab cannot quote at all, since both start from design files.
- Parts-buying time at PCBWay, PCBgogo, NextPCB and the US assemblers, which decides the real order of the speed table.
