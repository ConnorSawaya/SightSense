# Bare PCB prices from US and European board makers, delivered to Santa Clara, CA 95051 (checked October 13, 2026)

Board quoted everywhere: 40 mm x 100 mm rectangle (1.575 in x 3.937 in, 6.20 sq in, 40 cm2), 2 layers, FR-4, 1.6 mm, 1 oz copper, mask and silkscreen both sides, 0.15 mm (6 mil) track/space, 0.3 mm (11.8 mil) minimum drill, no special features. No Gerber files exist, so every number comes from a calculator or a published rule.

How each figure is marked:
- **[LIVE]** = read from the maker's live calculator on October 13, 2026 (built-in browser, no login, no files).
- **[PUBLISHED]** = from a published price page or rule, with my arithmetic shown.
- **[N/A]** = could not obtain (login, Gerber upload, name/email, bot check, or site error). Nothing is filled from memory.

Euro conversion: 1 EUR = 1.119 USD. This is the rate implied by AISLER's own calculator today (same quote shown as EUR 30.02 net and USD 33.59; EUR 46.04 and USD 51.51). It is not an official bank rate. Sources: [AISLER calculator, euro view](https://aisler.net/products/boards?lang=en-US), [AISLER calculator, US dollar view](https://aisler.net/en-US/products/boards).

## 1. What does an order that yields at least 5 boards, and at least 10 boards, cost at each maker?

### Takeaway
Cheapest board-only prices found: AISLER lead-free HASL Budget at $33.59 for 6 and $51.51 for 12 (but shipping from Germany and US import duty are extra and unpriced), DigiKey DKRed at $46.50 for 5 and $93.00 for 10 with free US shipping (formula price; live calculator blocked), and OSH Park at $62.00 for 6 and $124.00 for 12 with free US shipping. The classic US quick-turn shops are several times dearer ($165/$330 at Advanced Circuits' $33 special, $285.75/$476.00 at PCB Unlimited), and Sunstone and Bay Area Circuits could not be priced at all.

### Cited Findings

**Summary of board-only prices (before shipping and tax)**

| Maker | Yield for "at least 5" | Price | Yield for "at least 10" | Price | Finish | Mark |
|---|---|---|---|---|---|---|
| OSH Park, 2-layer Prototype | 6 (2 sets of 3) | $62.00 ($10.33 each) | 12 (4 sets of 3) | $124.00 ($10.33 each) | ENIG, purple mask | [PUBLISHED] |
| OSH Park, Super Swift | 6 | $124.00 ($20.67 each) | 12 | $248.00 | ENIG | [PUBLISHED] |
| OSH Park, Medium Run | not possible (under 100 sq in) | - | 20 (124 sq in) | $124.00 ($6.20 each) | ENIG | [PUBLISHED], see note |
| DigiKey DKRed | 5 | $46.50 ($9.30 each) | 10 | $93.00 ($9.30 each) | ENIG, red mask | [PUBLISHED]; live calculator [N/A] |
| AISLER, HASL lead-free, Budget | 6 | $33.59 ($5.60 each) | 12 | $51.51 ($4.29 each) | Lead-free HASL | [LIVE] |
| AISLER, ENIG, Budget | 6 | $41.72 ($6.95 each) | 12 | $67.78 ($5.65 each) | ENIG | [LIVE] |
| AISLER, HASL lead-free, Blitz | 6 | $59.15 ($9.86 each) | 12 | $93.69 ($7.81 each) | Lead-free HASL | [LIVE] |
| AISLER, ENIG, Blitz | 6 | $70.20 ($11.70 each) | 12 | $115.81 ($9.65 each) | ENIG | [LIVE] |
| Advanced Circuits (AdvancedPCB), "$33 Each" special | 5 | $165.00 ($33 each) | 10 | $330.00 ($33 each) | Lead-free HASL (maker may substitute ENIG or silver free) | [PUBLISHED]; quote tool [N/A] |
| Sunstone Circuits | - | [N/A] | - | [N/A] | - | quote site returned 404 |
| Bay Area Circuits | - | [N/A] | - | [N/A] | - | needs name + email or Gerbers |
| PCB Unlimited, USA Quickturn "Standard Specs", 5-day | 5 | $285.75 ($57.15 each) | 10 | $476.00 ($47.60 each) | ENIG | [LIVE] |
| Extra: Eurocircuits (Belgium), PCB proto / STANDARD pool | 5 | EUR 77.75 net = $87.00 ($17.40 each) | 10 | EUR 109.10 net = $122.08 ($12.21 each) | "Any lead-free finish" | [LIVE] |
| Extra: PCB Universe (Vancouver, WA), low-cost prototype | 5 | $139.20 ($27.84 each) | 10 | $217.50 ($21.75 each) | Leaded HASL | [LIVE] |

**OSH Park (Oregon, made in USA)**
- [PUBLISHED] 2-layer Prototype: "$5 per square inch, per set of 3", FR4, purple mask, ENIG, 1.6 mm, 1 oz; 2-layer design rules 6 mil trace/space, 10 mil drill. The board fits. Arithmetic: 6.20 sq in x $5 = $31.00 per set of 3; 2 sets = 6 boards = $62.00; 4 sets = 12 boards = $124.00 — [OSH Park services](https://docs.oshpark.com/services/)
- [PUBLISHED] Super Swift: "$10 per square inch, per set of 3": $62.00 per 3, $124.00 for 6, $248.00 for 12 — [OSH Park services](https://docs.oshpark.com/services/)
- [PUBLISHED] Medium Run: "$1 per square inch", "100 square inch minimum", "must be in multiple of 10". Read as a board count in tens: 10 boards = 62 sq in (under the minimum, not allowed); 20 boards = 124 sq in = $124.00, the same money as 12 prototype boards — [OSH Park services](https://docs.oshpark.com/services/)
- No set-up fee or minimum order is listed for the prototype services — [OSH Park services](https://docs.oshpark.com/services/)

**DigiKey DKRed (US-made per forum reply)**
- [PUBLISHED] "Starting at $1.50 Per Square Inch", "Minimum of 4 Copies", ENIG, DigiKey red mask, white silkscreen, 62 mil, 1 oz, minimum trace and space 5 mil, minimum drill 8 mil, 2 or 4 layers. The board fits — [DKRed page](https://www.digikey.com/en/resources/dkred)
- [PUBLISHED] The rule is per board: "For standard 2 layer board orders, the price per square inch per board is $1.50", with the worked example "6 square inches x $1.50 = $9 per PCB ... x 4 boards = $36". Arithmetic for this board: 6.20 x $1.50 = $9.30 each; 5 = $46.50; 10 = $93.00. Any quantity of 4 or more appears allowed (no multiples rule stated) — [DigiKey forum, DKRed](https://forum.digikey.com/t/dkred-an-extension-of-digi-keys-pcb-builder/12855)
- [N/A] Live price: the PCB Builder page (https://www.digikey.com/en/pcb-builder/?p=dkred) showed a Cloudflare "Verify you are human" check, which I did not attempt — [DKRed PCB Builder](https://www.digikey.com/en/pcb-builder/?p=dkred)
- A forum reply says "The DKRed PCBs are US-made, as indicated on the DKRed landing page" (poster not labelled as staff, January 2023) — [DigiKey forum](https://forum.digikey.com/t/where-are-dkred-pcbs-produced/27779)

**AISLER (Germany / Netherlands; "100% Made in Europe")**
- Rule: "For a bare board, three is the minimum ... ordered in multiples of three"; price = fixed job fee + area x rate x quantity; no charge for drills or vias — [AISLER Beautiful Boards](https://aisler.net/en-US/products/boards)
- [LIVE] Options chosen: 2 layers, 40 x 100 mm, 1.6 mm, 35 um copper, green mask, white silkscreen, US dollar view ("incl. 0% sales tax"). Results: HASL Lead Free + Budget: 6 = $33.59, 12 = $51.51 (dispatch "in 10 business days"). HASL Lead Free + Blitz: 6 = $59.15, 12 = $93.69 (2 business days). ENIG + Budget: 6 = $41.72, 12 = $67.78 (10 business days). ENIG + Blitz: 6 = $70.20, 12 = $115.81 (5 business days) — [AISLER calculator, US dollar view](https://aisler.net/en-US/products/boards)
- [LIVE] Same quotes in the euro view include 19% German VAT: HASL Budget 6 = EUR 35.72 (VAT 5.70, net 30.02), 12 = EUR 54.79 (net 46.04); ENIG Budget 6 = EUR 44.38 (net 37.29), 12 = EUR 72.09 (net 60.58); HASL Blitz 6 = EUR 62.92, 12 = EUR 99.65; ENIG Blitz 6 = EUR 74.67, 12 = EUR 123.18 — [AISLER calculator, euro view](https://aisler.net/products/boards?lang=en-US)
- [PUBLISHED] The community price list gives 2-layer 1.6 mm HASL Budget as EUR 12.00 job fee + EUR 0.067/cm2, ENIG Budget EUR 12.00 + 0.097, HASL Blitz EUR 22.00 + 0.129, ENIG Blitz EUR 22.00 + 0.17, all net of VAT — [AISLER "Our Simple Pricing"](https://community.aisler.net/t/our-simple-pricing/102)

**Advanced Circuits / AdvancedPCB (4pcb.com now redirects to advancedpcb.com)**
- [PUBLISHED] "$33 Each" special: "Order 3 or more boards that fit the specifications below, and we'll give you a special price of $33 each." 2 layers, FR-4, 0.062", 1 oz finished copper, lead-free HAL ("may also use ENIG or silver at no additional charge"), green LPI mask, white legend on 1 or 2 sides, minimum 0.006" line/space, minimum 0.010" hole, up to 60 sq in, 5-day lead time. Arithmetic: 5 x $33 = $165.00; 10 x $33 = $330.00 — [AdvancedPCB $33 Each special](https://www.advancedpcb.com/en-us/33-each-special/)
- [PUBLISHED] Restrictions on the special: maximum 35 drilled holes per square inch (about 217 holes on this 6.2 sq in board), no slots or overlapping drill hits, no internal cutouts, no scoring or tab routing, one part number per order ($50 lot charge for multiple images) — [AdvancedPCB $33 Each special](https://www.advancedpcb.com/en-us/33-each-special/)
- [N/A] Standard-spec instant quote: "Log in to MyAdvancedPCB to get a pcb quote online and place your order." The "Start Your Quote" button goes to a my4pcb.com login — [AdvancedPCB where to buy](https://www.advancedpcb.com/en-us/where-to-buy/)
- Other fixed-price specials listed: $66 Each 4-layer, $99 Each RF, $99 Each aluminum clad, and "Bare Bones" 2-layer (price behind login). The home page also advertises "$250 off your first purchase" on registration; terms were not visible — [AdvancedPCB home](https://www.advancedpcb.com/en-us/)
- BareBones is "made without solder mask or silkscreen", so it does not meet this spec — [AdvancedPCB blog](https://www.advancedpcb.com/en-us/resources/blog/looking-for-cheap-pcb-prototyping-options/)

**Sunstone Circuits (Oregon; a division of ASC)**
- [N/A] Price: the "Quote Now" link (https://onequote.sunstone.com/), the form address (https://onequote.sunstone.com/onequote-form/) and the old address (https://quoting.sunstone.com/quoteQT.aspx) all returned "HTTP Error 404. The requested resource is not found." on October 13, 2026, in the browser and by direct request, twice about an hour apart — [Sunstone OneQuote](https://onequote.sunstone.com/)
- [N/A] The only other instant-quote form (on the QuickTurn landing page) asks for an email address, which I did not enter — [Sunstone QuickTurn landing page](https://www.sunstone.com/quickturn-pcb-landing-page)
- [PUBLISHED] No prices are published. Pricing is "a more dynamic quoting structure based on board size, quantities and your specific design parameters" — [Sunstone OneQuote FAQs](https://www.sunstone.com/pcb-resources/onequote-faqs)
- [PUBLISHED] ValueProto (the budget service): up to 100 boards, finish "Immersion Silver or Tin Lead (HASL)", minimum trace and space 0.006", smallest drilled hole 0.015", green mask up to 2 sides, white legend 0-2 sides, "Free UPS ground shipping" — [Sunstone ValueProto](https://www.sunstone.com/pcb-products/pcb-manufacturing/valueproto)

**Bay Area Circuits (Fremont, CA)**
- [N/A] Price: InstantDFM offers "a Budgeting Estimate only (no file upload)", but the form requires NAME and EMAIL before the estimate button; the full quote needs Gerber or ODB++ upload. I entered nothing — [InstantDFM](https://instantdfm.bayareacircuits.com/)
- [PUBLISHED] No prices are published: "InstantDFM will generate a custom price based on desired specifications, quantities, and turnaround time" — [Bay Area Circuits prototypes](https://bayareacircuits.com/prototype-printed-circuit-boards-pcbs/)
- [PUBLISHED] Quantities: "we commonly build as few as 1-2 quantity prototype orders" — [BAC help: quantities](https://bayareacircuits.zendesk.com/hc/en-us/articles/4405057787675-What-are-the-minimum-and-maximum-quantities-BAC-can-offer)

**PCB Unlimited (Tualatin, OR; USA Quickturn service)**
- [LIVE] Options chosen on the USA Quickturn quote form: quantities 5, 10, 50, 100; 0.062"; 2 layers; 3.937 x 1.575 in; "FR4 Tg180 / Lead Free HASL"; 1 oz outer; minimum trace/space 0.006"; smallest hole "10 - 11.9 mils"; green mask both sides; white silkscreen both sides; individual boards; UL Certification and Date Code boxes were ticked by default — [PCB Unlimited USA Quickturn](https://www.pcbunlimited.com/products/usa-quickturn-pcbs)
- [LIVE] "Standard Specs" table (0.062", ENIG, FR4 Tg180, green mask, white silkscreen, 1 oz; cut-off noon Pacific), price per board: qty 5 = $94.10 (1 day), $67.20 (2 days), $62.20 (3 days), $57.15 (5 days); qty 10 = $78.40, $56.00, $51.80, $47.60. Totals at 5 days: 5 x $57.15 = $285.75; 10 x $47.60 = $476.00 — [PCB Unlimited USA Quickturn](https://www.pcbunlimited.com/products/usa-quickturn-pcbs)
- [LIVE] "Selected Specs" table (my exact options, lead-free HASL), price per board: qty 5 = $311.40 (1 day), $271.80 (2), $261.00 (3), $243.00 (4); qty 10 = $155.70, $135.90, $130.50, $121.50. Either quantity totals $1,215.00 at 4 days, so this is a flat lot price — [PCB Unlimited USA Quickturn](https://www.pcbunlimited.com/products/usa-quickturn-pcbs)
- [PUBLISHED] Included on USA Quickturn: any drill 0.008" or larger, trace/space down to 5/5 mil, "NRE & Electrical Testing Included" — [PCB Unlimited USA Quickturn](https://www.pcbunlimited.com/products/usa-quickturn-pcbs)
- PCB Unlimited also sells China-made and Taiwan-made boards ("Best Prices", "International Shipping Cost Included", import tariffs charged by the shipping company). These are offshore, so not priced here — [PCB Unlimited China PCBs](https://www.pcbunlimited.com/products/offshore-pcbs)

**Extra 1: Eurocircuits (Belgium), public calculator, no login needed for the board price**
- [LIVE] Options: 2 layers, 100 x 40 mm, single PCB, FR-4 Improved, 1.55 mm, Tg 145-150 C, 18 um foil (about 35 um finished), green mask top and bottom, white legend top and bottom (bottom changed from the default "None"; price did not change), "Any lead-free finish", 0.150 mm track and isolation, smallest final hole 0.25 mm, bare-board test yes, technology class 6C — [Eurocircuits calculator](https://be.eurocircuits.com/shop/assembly/configurator.aspx)
- [LIVE] Quantity 5 (calculator picks "PCB proto service"): EUR 15.55 each, EUR 77.75 net, EUR 94.08 with 21% Belgian VAT, 3 working days; 2 working days = EUR 36.27 each, EUR 181.35 net — [Eurocircuits calculator](https://be.eurocircuits.com/shop/assembly/configurator.aspx)
- [LIVE] Quantity 10 (calculator switches to "STANDARD pool service"): EUR 10.91 each, EUR 109.10 net, EUR 132.01 with VAT, at 5 or 7 working days (same price). PCB proto for 10 costs more: EUR 207.80 net at 3 working days, EUR 261.40 at 2 — [Eurocircuits calculator](https://be.eurocircuits.com/shop/assembly/configurator.aspx)
- In dollars at 1.119: 5 = $87.00; 10 = $122.08; 5 in 2 working days = $202.93 (my conversion) — [Eurocircuits calculator](https://be.eurocircuits.com/shop/assembly/configurator.aspx)

**Extra 2: PCB Universe (Vancouver, WA), public price table, no login**
- [LIVE] 2-layer "Low Cost PCB Prototypes", entered 3.937 x 1.575 in: 4 = $116.00 ($29.00 each), 5 = $139.20 ($27.84), 6 = $163.56, 7 = $182.70, 8 = $197.20, 9 = $208.80, 10 = $217.50 ($21.75). Minimum 4, maximum 10, "FREE = Tooling & Test", lead time 8 days. The page script uses one price table for any board up to 35 sq in, so size does not change the price — [PCB Universe prototype pricing](https://www.pcbuniverse.com/pcbu-prototype.php)
- [PUBLISHED] Spec of that service: 0.062" FR4 (140 C Tg), 1 oz, minimum hole 12 mil, minimum trace/space 5 mil, "Lead Solder (HASL)", green mask both sides, white silkscreen both sides, no slots, cutouts, arrays or UL marks, credit card only — [PCB Universe prototype pricing](https://www.pcbuniverse.com/pcbu-prototype.php)
- PCB Universe does not make boards itself: it uses "ISO certified and UL registered PCB manufacturers, both domestically and offshore" — [PCB Universe about](https://www.pcbuniverse.com/pcbu-about.php)

**Makers checked and rejected as extras (no public instant price)**
- Sierra Circuits (Sunnyvale, CA, "All fabrication and assembly are done domestically"): the instant quote link redirects to a login page — [Sierra Circuits quick-turn](https://www.protoexpress.com/products/quick-turn-pcb/), [Sierra Circuits login](https://www.protoexpress.com/customer-portal/instant-online-quote)
- Epec InstantPCBQuote: "Register to Quote and Order Your PCBs" — [Epec](https://epectec.com/instantpcbquote/)

### Inferences
- AISLER's live calculator is about EUR 2 above its published list: the two live points per service solve to a job fee of EUR 14.00 (Budget) and EUR 22.00 (Blitz) with rates of about EUR 0.0668/cm2 (HASL Budget), 0.0970 (ENIG Budget), 0.1286 (HASL Blitz) and 0.1698 (ENIG Blitz). The community list still says EUR 12.00 for Budget, so the list is stale; the page headline "Starting at just EUR 14.20" agrees with the live figure.
- AISLER's US dollar view shows the net (ex-VAT) price converted to dollars, so German VAT is not charged on a US order; US import duty is a separate cost (see question 4).
- At PCB Unlimited, only the "Standard Specs" (ENIG) row is sensible: choosing lead-free HASL moved the quote to a flat $1,215-$1,557 lot price. The Standard Specs line does not say how many silkscreen sides it covers.
- This board's 0.3 mm (11.8 mil) minimum drill is under PCB Universe's 12 mil minimum and well under Sunstone ValueProto's 0.015" (0.38 mm) minimum. For those two services the smallest via drill would have to grow, or a dearer service be used.
- Advanced Circuits' $33 special caps drilled holes at 35 per sq in, about 217 holes on this board. The board is unrouted, so the hole count is unknown; a via-heavy layout could lose the special price.
- DKRed is priced per board with no set multiple, so it is the only low-cost option that yields exactly 5 or exactly 10.
- For OSH Park, 20 boards on Medium Run cost the same $124.00 as 12 prototype boards, at the price of a longer wait.

### Gaps
- DigiKey DKRed live price, the price of its 5-day quick turn, and whether "Starting at $1.50" still equals $1.50 for a 2-layer board today: calculator blocked by a human-verification check.
- Sunstone Circuits: no price at all (quote site down, landing-page form needs an email).
- Bay Area Circuits: no price at all (name and email, or Gerbers, required).
- Advanced Circuits standard-spec and BareBones prices: login required.
- Where PCB Universe's low-cost prototype boards are made (US or offshore) is not stated for that service.
- OSH Park's "multiple of 10" Medium Run wording is ambiguous in the docs; I read it as board quantity.

## 2. What is the standard turn time and the price of faster options?

### Takeaway
Standard build times run from 3 working days (Eurocircuits, 5 boards) and 5 days (Advanced Circuits special, PCB Unlimited) to about 10 business days (AISLER Budget, DKRed standard) and 9-12 calendar days (OSH Park). Faster service roughly doubles the price at OSH Park and AISLER; PCB Unlimited's 1-day turn costs about 65% more than its 5-day turn.

### Cited Findings

| Maker | Standard turn | Faster option and its price | Mark |
|---|---|---|---|
| OSH Park | Prototype "ships in 9-12 calendar days" | Super Swift "ships in 4-5 business days" at $10/sq in per 3 (6 boards $124.00 instead of $62.00). Medium Run 12-21 calendar days | [PUBLISHED] |
| DigiKey DKRed | "Built in 5 to 10 business days"; forum: standard 10 business days | Quick turn 5 business days; price [N/A] | [PUBLISHED] |
| AISLER | Budget: dispatch in 10 business days (HASL and ENIG) | Blitz: HASL 2 business days (6 = $59.15 vs $33.59), ENIG 5 business days (6 = $70.20 vs $41.72) | [LIVE] |
| Advanced Circuits | $33 special: 5-day lead time | Same-day, next-day and "Weekend Wonder" turns exist; prices [N/A] (login) | [PUBLISHED] |
| Sunstone | "1 day to 3 weeks" through OneQuote | prices [N/A] | [PUBLISHED] |
| Bay Area Circuits | Chosen in InstantDFM; "as little as 24 hours" | prices [N/A] | [PUBLISHED] |
| PCB Unlimited | 5 business days: $57.15 each (5), $47.60 each (10) | 3 days $62.20 / $51.80; 2 days $67.20 / $56.00; 1 day $94.10 / $78.40 each | [LIVE] |
| Eurocircuits | 5 boards: 3 working days; 10 boards: 7 working days proposed (5 at the same price) | 5 boards in 2 working days EUR 181.35 (vs 77.75); 10 boards in 3 working days EUR 207.80, in 2 EUR 261.40 (vs 109.10) | [LIVE] |
| PCB Universe | 8 days (business days) | Faster only through its standard quote page; not priced | [LIVE] |

- OSH Park turn times per service — [OSH Park services](https://docs.oshpark.com/services/)
- DKRed: "Built in 5 to 10 business days" — [DKRed page](https://www.digikey.com/en/resources/dkred); "Standard DKRed boards have a build time of 10 business days. Quick turn DKRed boards have a build time of 5 business days. Please note transit time is not included within build time." — [DigiKey forum, DKRed](https://forum.digikey.com/t/dkred-an-extension-of-digi-keys-pcb-builder/12855)
- AISLER dispatch estimates read with each quote — [AISLER calculator](https://aisler.net/en-US/products/boards). Its service status page (dated September 14, 2026) lists the same figures as both target and current: 2-layer HASL Budget 10 working days, HASL Blitz 2, ENIG Budget 10, ENIG Blitz 5, prototype stencil 3; design deadline "6AM CET on a business day" — [AISLER service status](https://community.aisler.net/t/service-status/399)
- Advanced Circuits $33 special "Lead time: 5 days" — [AdvancedPCB $33 Each special](https://www.advancedpcb.com/en-us/33-each-special/). Instant-quote prototypes "typically ship in 1-5 business days" — [AdvancedPCB where to buy](https://www.advancedpcb.com/en-us/where-to-buy/). "Same-day and weekend wonder offers"; "if DHL is selected, your order could be delayed 1 day" — [AdvancedPCB turn times](https://www.advancedpcb.com/en-us/resources/turn-times/)
- Sunstone: "you can instantly quote most PCB configurations from 1 day to 3 weeks. Some limitations apply for the shorter lead times." — [Sunstone lead times](https://www.sunstone.com/pcb-manufacturing-capabilities/lead-times)
- Bay Area Circuits: "We can produce two-layer PCBs on the same day we receive your files" — [Bay Area Circuits prototypes](https://bayareacircuits.com/prototype-printed-circuit-boards-pcbs/). Day counting: an order placed before 5 pm on a business day makes that day Day 0; weekends are not counted — [BAC help: lead time](https://bayareacircuits.zendesk.com/hc/en-us/articles/208041617-How-is-production-lead-time-calculated-or-how-can-I-determine-what-day-my-order-will-ship)
- PCB Unlimited: "Lead Time Days are business days until the order ships, does not include transit time or cost. The next business day is Day 1." Standard Specs cut-off is noon Pacific; add one day for major US holidays — [PCB Unlimited USA Quickturn](https://www.pcbunlimited.com/products/usa-quickturn-pcbs)
- Eurocircuits showed estimated shipment dates of 19-10-2026 for the 3-working-day order and 26-10-2026 for the 7-working-day order — [Eurocircuits calculator](https://be.eurocircuits.com/shop/assembly/configurator.aspx)
- PCB Universe "Manufacturing Lead Time: 8 Days" — [PCB Universe prototype pricing](https://www.pcbuniverse.com/pcbu-prototype.php)

### Inferences
- If the boards are needed within about a week of ordering, the realistic choices with a known price are OSH Park Super Swift ($124 for 6), PCB Unlimited ($286-$471 for 5) and Advanced Circuits' 5-day special ($165 for 5). AISLER Blitz and Eurocircuits build as fast but add transatlantic shipping and customs time.
- DKRed's 10-business-day standard build is about two calendar weeks before free shipping starts, similar to OSH Park's 9-12 calendar days.

### Gaps
- Price of DKRed's 5-day quick turn.
- Price of any expedite at Advanced Circuits, Sunstone and Bay Area Circuits.

## 3. What does shipping to ZIP 95051 cost and how long does it take? Is local pickup possible at Bay Area Circuits?

### Takeaway
Free domestic shipping is published by OSH Park (USPS First Class, 1-5 business days), DigiKey DKRed and Sunstone (UPS Ground). Bay Area Circuits confirms free "Will Call / Local Pickup" at its Fremont plant. No maker's paid shipping price to 95051 could be read, because every checkout needs an account; AISLER and Eurocircuits in particular show shipping only after login, and AISLER's free shipping does not apply to the US.

### Cited Findings

| Maker | Cheapest option | Fastest option | Ships from | Mark |
|---|---|---|---|---|
| OSH Park | USPS First Class, $0, 1-5 business days, tracked | FedEx Standard / Priority Overnight $20-45, next business day; USPS Priority $6.70-7.35, 2-3 business days | Lake Oswego, Oregon | [PUBLISHED] |
| DigiKey DKRed | "Free Shipping - To US Addresses"; carrier and transit not stated | not stated | not stated | [PUBLISHED] |
| AISLER | To the US: UPS only at present; price shown only at checkout [N/A]; UPS Expedited 3-10 business days | UPS Express 2-5 business days; price [N/A] | Germany | [PUBLISHED] |
| Advanced Circuits | [N/A]; carriers UPS, FedEx, DHL | [N/A] | not stated | [PUBLISHED] |
| Sunstone | UPS Ground free in the continental US | 2nd Day Air and Next Day at carrier rates [N/A]; Saturday delivery $25-$50 extra | not stated | [PUBLISHED] |
| Bay Area Circuits | Will Call / Local Pickup, Fremont, $0 | UPS at cost, price [N/A] | Fremont, CA | [PUBLISHED] |
| PCB Unlimited | [N/A] (cart only) | [N/A] | company in Tualatin, OR | - |
| Eurocircuits | [N/A] ("Login for available shipment dates, options and prices") | [N/A] | Europe | [LIVE] note |
| PCB Universe | [N/A] | [N/A] | not stated | - |

- OSH Park domestic table: USPS First Class 1-5 business days $0; USPS Priority 2-3 business days $6.70-7.35; USPS Express 1-2 business days $25-30; UPS Ground 1-7 business days "Varies"; FedEx Express Saver 1-3 business days $7-15; FedEx Two Day $7-15; FedEx Standard Overnight $20-30; FedEx Priority Overnight $20-45; FedEx First Overnight $50+. "All PCBs ship from Lake Oswego, Oregon, and are fully manufactured in the United States." All domestic options are tracked — [OSH Park shipping](https://docs.oshpark.com/submitting-orders/shipping-information/)
- DKRed: "Free Shipping - To US Addresses" — [DKRed page](https://www.digikey.com/en/resources/dkred); "DKRed orders have free shipping to all United States locations" — [DigiKey forum, DKRed](https://forum.digikey.com/t/dkred-an-extension-of-digi-keys-pcb-builder/12855)
- AISLER: "Prices are calculated at checkout after selecting a shipping address and are based on your shipping address and order value." USA transit table: DHL Warenpost 6-18 business days, DHL Parcel 4-14, UPS Expedited 3-10, UPS Express 2-5. USA notice (updated 2025-09-25): Warenpost "still not available", "we cannot ship via DHL to the US at the moment", "This also affects our free shipping option", and "UPS has introduced additional customs handling fees to all US-bound shipments ... these costs are added to our calculated shipping prices" — [AISLER shipping methods](https://community.aisler.net/t/shipping-methods/672)
- AISLER service status (September 14, 2026): DHL to the USA postponed; "UPS still ships there but adds a 2.5 EUR fee per parcel"; Express UPS to non-EU countries 2-4 business days — [AISLER service status](https://community.aisler.net/t/service-status/399)
- AISLER's product page still advertises "Shipping worldwide for free", which conflicts with its own US notice — [AISLER Beautiful Boards](https://aisler.net/en-US/products/boards); contradicted by [AISLER shipping methods](https://community.aisler.net/t/shipping-methods/672)
- Advanced Circuits names UPS, FedEx and DHL but publishes no rates — [AdvancedPCB turn times](https://www.advancedpcb.com/en-us/resources/turn-times/)
- Sunstone: Ground "Continental US customers (FREE)"; 2nd Day Air and Next Day offered, costs "calculated directly from UPS and FedEx websites"; Saturday delivery "$25-$50 (based on location)" — [Sunstone shipping policy](https://www.sunstone.com/pcb-resources/customer-support/shipping-policy); ValueProto lists "Free UPS ground shipping" — [Sunstone ValueProto](https://www.sunstone.com/pcb-products/pcb-manufacturing/valueproto)
- Bay Area Circuits local pickup: "We also offer a Will Call / Local Pickup option for local Silicon Valley customers ... select the 'Will Call / Local Pickup' option from the shipping menu. Once the order is complete you will receive an email that states 'READY FOR PICKUP'. Orders may be picked up Monday through Friday between the hours of 9am and 6pm PST." UPS is the only carrier in the online store and "we do not mark up shipping cost; our costs are your costs" — [BAC help: shipping from the online store](https://bayareacircuits.zendesk.com/hc/en-us/articles/208041657-Is-UPS-the-only-shipping-option-available-from-the-online-store)
- Bay Area Circuits pickup timing: "please plan to do so the business day following the manufacturing due date between the hours of 9am and 5pm" — [BAC help: lead time](https://bayareacircuits.zendesk.com/hc/en-us/articles/208041617-How-is-production-lead-time-calculated-or-how-can-I-determine-what-day-my-order-will-ship)
- Bay Area Circuits address: 44358 Old Warm Springs Blvd, Fremont, CA 94538 — [Bay Area Circuits](https://bayareacircuits.com/)
- Bay Area Circuits can also ship by FedEx or USPS on custom orders, with a possible one-day delay, or on the customer's carrier account — [BAC help: shipping options](https://bayareacircuits.zendesk.com/hc/en-us/articles/4405057729691-What-shipping-options-does-BAC-offer)
- PCB Unlimited address: 10191 SW Avery Street, Tualatin, OR 97062; no shipping rates on the site outside the cart — [PCB Unlimited contact](https://www.pcbunlimited.com/contact-us)
- Eurocircuits calculator footnote: "Login for available shipment dates, options and prices" — [Eurocircuits calculator](https://be.eurocircuits.com/shop/assembly/configurator.aspx)
- Sierra Circuits (Sunnyvale, about the same distance as Fremont) lists "FedEx/UPS, Will Call" as shipping options, but it could not be priced — [Sierra Circuits quick-turn](https://www.protoexpress.com/products/quick-turn-pcb/)

### Inferences
- The two help-centre articles give different Bay Area Circuits pickup hours (9am-6pm and 9am-5pm); both were last updated about three years ago, so the hours should be confirmed by phone (510-933-9000).
- Lake Oswego (OSH Park), Tualatin (PCB Unlimited) and Sunstone are all in Oregon, so ground shipping to Santa Clara should sit at the short end of the carriers' ranges, but no maker publishes a transit time to this ZIP.
- AISLER's two notices disagree on wording but agree on the effect: a US order today goes by UPS, costs money, and carries a customs handling surcharge.

### Gaps
- Paid shipping price to 95051 at every maker (all need an account or cart): AISLER UPS, Eurocircuits, Advanced Circuits, PCB Unlimited, PCB Universe, Bay Area Circuits UPS.
- DKRed carrier and transit time.
- Whether Sunstone's free Ground offer applies to every OneQuote order or only ValueProto.

## 4. Any sales tax to California, minimum order charge, set-up or tooling fee?

### Takeaway
The Santa Clara combined sales tax rate is 9.750%; Bay Area Circuits says it charges California tax by default and DigiKey says it collects by ship-to address, while the other US makers publish nothing and the European makers show 0% US tax but leave import duty to the buyer. None of the priced makers adds a tooling or set-up fee; the real constraints are minimum quantities (3, 4 or sets of 3) and area minimums.

### Cited Findings
- Sales tax rate: City of Santa Clara, Santa Clara County, 9.750%, rate table effective October 1, 2026 — [CDTFA rates](https://www.cdtfa.ca.gov/taxes-and-fees/rates.aspx)
- Bay Area Circuits: "By default, all orders shipping to California will have sales tax applied", refundable with a resale certificate — [BAC help: sales tax](https://bayareacircuits.zendesk.com/hc/en-us/articles/207330478-What-determines-whether-sales-tax-is-added-to-my-order)
- DigiKey: it "meets the nexus requirements in most jurisdictions and is therefore required to collect tax unless a properly executed exemption certificate is provided"; tax follows the ship-to address (read from a search summary of the page, not the page itself) — [DigiKey sales tax help](https://www.digikey.com/en/help-support/payment-and-pricing/sales-tax-exemption-certificates)
- OSH Park's docs do not mention sales tax — [OSH Park shipping](https://docs.oshpark.com/submitting-orders/shipping-information/)
- AISLER's US dollar view shows "incl. 0% sales tax ($0.00)"; its published prices are "net prices, and VAT should be added where required" — [AISLER calculator](https://aisler.net/en-US/products/boards), [AISLER "Our Simple Pricing"](https://community.aisler.net/t/our-simple-pricing/102)
- Import duty on European boards: "the threshold of duty-free shipments is suspended and import duties are now imposed on all shipments"; customers pay duties and taxes; "It is currently not possible to reliably calculate and pay these duties in advance" — [AISLER shipping methods](https://community.aisler.net/t/shipping-methods/672)
- Minimum order and fees, by maker:
  - OSH Park: sets of 3; Medium Run 100 sq in minimum; no fee listed — [OSH Park services](https://docs.oshpark.com/services/)
  - DKRed: minimum 4 boards; no minimum charge stated; board size at least 0.5 x 0.5 in; an account is needed to order but not to upload — [DKRed page](https://www.digikey.com/en/resources/dkred), [DigiKey PCB FAQ](https://www.digikey.com/en/resources/design-tools/pcb-faqs)
  - AISLER: minimum 3, multiples of 3; fixed job fee (EUR 12.00 Budget on the list; about EUR 14.00 in the live calculator) is the only set-up charge — [AISLER "Our Simple Pricing"](https://community.aisler.net/t/our-simple-pricing/102)
  - Advanced Circuits $33 special: minimum 3 boards; $50 lot charge only for multiple images or step-and-repeat — [AdvancedPCB $33 Each special](https://www.advancedpcb.com/en-us/33-each-special/)
  - PCB Unlimited: "NRE & Electrical Testing Included"; prototype quote covers up to 100 boards — [PCB Unlimited USA Quickturn](https://www.pcbunlimited.com/products/usa-quickturn-pcbs)
  - PCB Universe: minimum 4, maximum 10; "No Hidden Charges! FREE Tooling and Electrical Test!" — [PCB Universe prototype pricing](https://www.pcbuniverse.com/pcbu-prototype.php)
  - Eurocircuits: no separate tooling line in the quote; bare-board testing "Yes" is included in the price shown — [Eurocircuits calculator](https://be.eurocircuits.com/shop/assembly/configurator.aspx)
  - Sierra Circuits (not priced): $100 lot charge for multiple parts, slots or cutouts beyond allowance — [Sierra Circuits quick-turn](https://www.protoexpress.com/products/quick-turn-pcb/)

### Inferences
- If a US maker charges California tax on this order it would be 9.75% of the board price: $6.05 on OSH Park's $62.00, $4.53 on DKRed's $46.50, $16.09 on Advanced Circuits' $165.00, $27.86 on PCB Unlimited's $285.75 (my arithmetic; only Bay Area Circuits and DigiKey state that they collect).
- For AISLER and Eurocircuits the buyer should expect a duty bill from UPS on top of the dollar price; neither maker quotes the amount, so their landed cost cannot be closed out from public pages.

### Gaps
- Whether OSH Park, Advanced Circuits, Sunstone, PCB Unlimited and PCB Universe charge California sales tax (not published; visible only at checkout).
- The US duty rate and UPS brokerage fee for bare boards from Germany or Belgium: no maker states it, and I did not research tariff schedules (outside this assignment's sources).

## 5. For each maker: total landed cost for 5 and for 10, price per board, and total days from order to door

### Takeaway
With every cost known, only OSH Park and DKRed can be fully totalled: DKRed is about $46.50-$51.03 for 5 and $93.00-$102.07 for 10 in roughly 2-3 weeks, and OSH Park is $62.00-$68.05 for 6 and $124.00-$136.09 for 12 in about 10-19 calendar days. AISLER has the lowest board price but an unknown shipping and duty bill; everything else is $139 and up before shipping.

### Cited Findings

Landed cost = board price + cheapest shipping + California tax where the maker is known or likely to charge it. A range shows "without tax - with 9.75% tax". All totals are my arithmetic on the cited prices.

| Maker and service | Order for at least 5: landed | Per board | Order for at least 10: landed | Per board | Days, order to door | What is still unknown |
|---|---|---|---|---|---|---|
| DigiKey DKRed, standard [PUBLISHED] | 5 boards: $46.50 + $0 shipping = $46.50; $51.03 with tax | $9.30-$10.21 | 10 boards: $93.00; $102.07 with tax | $9.30-$10.21 | 5-10 business days build + transit (not stated) | Live price, transit time |
| OSH Park Prototype [PUBLISHED] | 6 boards: $62.00 + $0 = $62.00; $68.05 if taxed | $10.33-$11.34 | 12 boards: $124.00; $136.09 if taxed | $10.33-$11.34 | 9-12 calendar days + 1-5 business days USPS = about 10-19 calendar days | Whether tax is charged |
| OSH Park Super Swift [PUBLISHED] | 6 boards: $124.00 + $6.70-7.35 Priority = $130.70-$131.35; add $12.09 if taxed | $21.78-$21.89 | 12 boards: $248.00 + $6.70-7.35 = $254.70-$255.35 | $21.23-$21.28 | 4-5 business days + 2-3 business days = 6-8 business days | Whether tax is charged |
| AISLER HASL Budget [LIVE] | 6 boards: $33.59 + UPS [N/A] + duty [N/A] | $5.60 + | 12 boards: $51.51 + UPS [N/A] + duty [N/A] | $4.29 + | 10 business days + UPS Expedited 3-10 = 13-20 business days | Shipping, duty |
| AISLER HASL Blitz [LIVE] | 6 boards: $59.15 + UPS [N/A] + duty [N/A] | $9.86 + | 12 boards: $93.69 + UPS + duty | $7.81 + | 2 business days + UPS Express 2-5 = 4-7 business days | Shipping, duty |
| Advanced Circuits $33 special [PUBLISHED] | 5 boards: $165.00 + shipping [N/A]; tax would add $16.09 | $33.00 + | 10 boards: $330.00 + shipping [N/A]; tax would add $32.18 | $33.00 + | 5 days + transit [N/A] | Shipping, tax, first-order discount terms |
| PCB Unlimited USA Quickturn, 5-day [LIVE] | 5 boards: $285.75 + shipping [N/A]; tax would add $27.86 | $57.15 + | 10 boards: $476.00 + shipping [N/A]; tax would add $46.41 | $47.60 + | 5 business days + transit [N/A] | Shipping, tax |
| PCB Unlimited, 1-day [LIVE] | 5 boards: $470.50 + shipping [N/A] | $94.10 + | 10 boards: $784.00 + shipping [N/A] | $78.40 + | 1 business day + transit [N/A] | Shipping, tax |
| Eurocircuits [LIVE] | 5 boards: $87.00 (EUR 77.75) + shipping [N/A] + duty [N/A] | $17.40 + | 10 boards: $122.08 (EUR 109.10) + shipping + duty | $12.21 + | 3 working days (5) or 5-7 working days (10) + transit [N/A] | Shipping, duty |
| PCB Universe [LIVE] | 5 boards: $139.20 + shipping [N/A] | $27.84 + | 10 boards: $217.50 + shipping [N/A] | $21.75 + | 8 business days + transit [N/A] | Shipping, tax, origin |
| Sunstone Circuits | [N/A] | - | [N/A] | - | 1 day to 3 weeks build; Ground shipping free | Everything but shipping |
| Bay Area Circuits | [N/A] | - | [N/A] | - | Build time chosen at quote; pickup the business day after the due date | Price |

Sources for the inputs: [OSH Park services](https://docs.oshpark.com/services/), [OSH Park shipping](https://docs.oshpark.com/submitting-orders/shipping-information/), [DKRed page](https://www.digikey.com/en/resources/dkred), [DigiKey forum, DKRed](https://forum.digikey.com/t/dkred-an-extension-of-digi-keys-pcb-builder/12855), [AISLER calculator](https://aisler.net/en-US/products/boards), [AISLER shipping methods](https://community.aisler.net/t/shipping-methods/672), [AdvancedPCB $33 Each special](https://www.advancedpcb.com/en-us/33-each-special/), [PCB Unlimited USA Quickturn](https://www.pcbunlimited.com/products/usa-quickturn-pcbs), [Eurocircuits calculator](https://be.eurocircuits.com/shop/assembly/configurator.aspx), [PCB Universe prototype pricing](https://www.pcbuniverse.com/pcbu-prototype.php), [Sunstone shipping policy](https://www.sunstone.com/pcb-resources/customer-support/shipping-policy), [BAC help: lead time](https://bayareacircuits.zendesk.com/hc/en-us/articles/208041617-How-is-production-lead-time-calculated-or-how-can-I-determine-what-day-my-order-will-ship), [CDTFA rates](https://www.cdtfa.ca.gov/taxes-and-fees/rates.aspx)

Arithmetic check:
- OSH Park: 6.20 x 5 = 31.00 per 3; x2 = 62.00; x4 = 124.00; 62.00 x 1.0975 = 68.05; 124.00 x 1.0975 = 136.09.
- DKRed: 6.20 x 1.50 = 9.30; x5 = 46.50; x10 = 93.00; x1.0975 = 51.03 and 102.07.
- Advanced Circuits: 33 x 5 = 165; 33 x 10 = 330; 9.75% = 16.09 and 32.18.
- PCB Unlimited: 57.15 x 5 = 285.75; 47.60 x 10 = 476.00; 94.10 x 5 = 470.50; 78.40 x 10 = 784.00.
- Eurocircuits: 77.75 x 1.119 = 87.00; 109.10 x 1.119 = 122.08.
- PCB Universe: 27.84 x 5 = 139.20; 21.75 x 10 = 217.50.

### Inferences
- Ranking by known landed cost for at least 5 boards: DKRed ($46.50-$51.03) < OSH Park ($62.00-$68.05) < OSH Park Super Swift (about $131) < PCB Universe ($139.20 + shipping) < Advanced Circuits ($165 + shipping) < PCB Unlimited ($285.75 + shipping). AISLER ($33.59) and Eurocircuits ($87.00) would need shipping plus duty to stay under about $13-$28 (AISLER) to beat DKRed or OSH Park, which is unlikely for a tracked UPS parcel from Germany, but this is an estimate, not a quote.
- For at least 10 boards the same order holds: DKRed ($93.00-$102.07) < OSH Park ($124.00-$136.09 for 12, or $124.00 for 20 on Medium Run) < PCB Universe ($217.50 +) < Advanced Circuits ($330 +) < PCB Unlimited ($476 +).
- The fastest fully priced route is OSH Park Super Swift at about 6-8 business days door to door; PCB Unlimited's 1-day build could be faster but its shipping price and time are unknown.
- Bay Area Circuits is the only maker where transit time is zero (pickup in Fremont), but without a price it cannot be ranked.
- The day totals are sums of the makers' own build and transit ranges, not delivery promises.

### Gaps
- A complete landed cost for AISLER, Eurocircuits, Advanced Circuits, PCB Unlimited and PCB Universe (shipping and, for the European two, duty are missing).
- Any cost at Sunstone and Bay Area Circuits.
- Actual transit days to 95051 for every carrier option except OSH Park's published ranges.

## 6. Stencil: price and lead time for a frameless stainless stencil about 40 x 100 mm

### Takeaway
OSH Stencils is the clear choice: 4 mil stainless at $1.60 per square inch including the border, so roughly $10-$26 depending on border width, shipped within 1 business day from $2.95. AISLER's stencil is cheaper on paper (about $9.85) but only comes with an AISLER order from Germany; PCB Unlimited's prototype stencil is $125 and Eurocircuits' is about $34.50.

### Cited Findings
- [PUBLISHED] OSH Stencils price model: "Our prices are based on your total order size per material in square inches ... (including borders)." Stainless steel: 3 mil $1.70/sq in, 4 mil $1.60/sq in, 5 mil $1.70/sq in, 6 and 8 mil $1.75/sq in; discount "$0.01 per 1 sqin above 12"; minimum price $0.75/sq in (4 mil). Example given: "4mil Stainless Steel 18 sqin ($0.06/sqin discount): 18 x $1.54 = $27.72". Polyimide film: 3 mil $0.80/sq in, 5 mil $0.90/sq in. No charge for border engraving — [OSH Stencils, Pricing tab](https://www.oshstencils.com/)
- [PUBLISHED] Arithmetic for a 4 mil stainless stencil on this board (the stencil is cut to the paste area plus a border the buyer sets; the border width is chosen in the uploader and the default is not published):
  - Board outline only, no border: 1.575 x 3.937 = 6.20 sq in x $1.60 = $9.92
  - 0.5 in border all round: 2.575 x 4.937 = 12.71 sq in x $1.60 = $20.34
  - 0.75 in border all round: 3.075 x 5.437 = 16.72 sq in, $0.04 discount, x $1.56 = $26.08
  - 1 in border all round: 3.575 x 5.937 = 21.22 sq in, $0.09 discount, x $1.51 = $32.05
  — [OSH Stencils, Pricing tab](https://www.oshstencils.com/)
- [PUBLISHED] OSH Stencils lead time and shipping: "We strive to ship orders within 1 business day, weekends and holidays excluded." Domestic USPS First Class with tracking $2.95+, USPS Priority $7.25+, FedEx Ground $11.00+, Express Saver $11.30+, 2 Day $12.80+, Standard Overnight $12.85+, Priority Overnight $13.10+. "Rush Processing (Same day Shipping) is available for some Stainless Steel stencil orders received before 2PM MST." — [OSH Stencils, Shipping tab](https://www.oshstencils.com/)
- [PUBLISHED] OSH Stencils also sells framed stainless stencils from $165 (14 x 14 in) — [OSH Stencils, Pricing tab](https://www.oshstencils.com/)
- [PUBLISHED] AISLER prototype stencil: "Stencil Price = Job Fee + Area x Area-usage Fee x Factor", job fee EUR 5.00, EUR 0.095 per cm2, one side. Arithmetic: 5.00 + 40 x 0.095 = EUR 8.80 net, about $9.85 at 1.119. AISLER's own example: 7.0 x 5.0 cm one-sided = EUR 8.33 — [AISLER "Our Simple Pricing"](https://community.aisler.net/t/our-simple-pricing/102)
- AISLER stencil lead time: 3 working days; it is added to a project that has paste layers ("we'll cut it to match the boards") — [AISLER service status](https://community.aisler.net/t/service-status/399), [AISLER Beautiful Boards](https://aisler.net/en-US/products/boards)
- [LIVE] PCB Unlimited "Prototype SMT Stencils" (frameless, laser-cut stainless, up to 12 x 10 in): unit price $125.00 for "Only the foil", up to 3000 apertures; stencil kit +$20.00; "Lead Time: 24-Hour Turn" — [PCB Unlimited prototype stencils](https://www.pcbunlimited.com/products/prototype-smt-stencils)
- PCB Unlimited advertises "30% Off on Laser Cut SMT Stencils with your PCBs", which would make it $87.50 if it applies to this item (my arithmetic) — [PCB Unlimited](https://www.pcbunlimited.com/)
- [LIVE] Eurocircuits top stencil added to the same quote: EUR 30.84 net (EUR 37.32 with VAT), 130 um, 140 x 80 mm with 20 mm borders; about $34.51 at 1.119 — [Eurocircuits calculator](https://be.eurocircuits.com/shop/assembly/configurator.aspx)
- Sunstone: stencils can be added to a PCB order; the only published price is "Oversized (above 10"x12") $175"; standard and frameless prices are not published — [Sunstone stencils](https://www.sunstone.com/pcb-products/pcb-solder-stencils)
- DigiKey PCB Builder: "Stencils are not available at this time." — [DigiKey PCB FAQ](https://www.digikey.com/en/resources/design-tools/pcb-faqs)
- OSH Park's services list contains boards only, no stencil — [OSH Park services](https://docs.oshpark.com/services/)

### Inferences
- A realistic OSH Stencils total for this board is about $23-$29 delivered (4 mil stainless with a 0.5-0.75 in border, $20.34-$26.08, plus $2.95 First Class), arriving a few days after a 1-business-day cut. The exact figure depends on the paste-layer extents and the border chosen at upload.
- A stencil can be ordered from OSH Stencils independently of where the boards are made, so it does not tie the board order to any maker.
- AISLER's stencil only makes sense if the boards also come from AISLER, since it ships in the same UPS parcel and carries the same duty question.

### Gaps
- OSH Stencils' default border width and its exact price for this design: needs a paste-layer file upload and an account.
- Stencil availability and price at Advanced Circuits, Bay Area Circuits (its help centre has a "Desktop Stencil Tutorial" but no price) and PCB Universe: not found on public pages.
- Sunstone's price for a small frameless stencil: not published and the quote site was down.
