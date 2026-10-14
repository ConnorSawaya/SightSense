# Cane board: what it costs to have made

Checked on October 13, 2026. Prices are US dollars. Nothing has been ordered, and the board is not routed yet, so these are estimates built from live quotes and published fees, not checkout totals.

The plan is turnkey assembly (PCBA) by JLCPCB. Parts are listed line by line in [`BOM.md`](BOM.md): $8.49 a board.

## Price for any number of boards

Roughly **$88 to start, plus about $12.50 a board**, delivered to Santa Clara, CA 95051 with US duty paid.

| Boards | Total | Per board |
| --- | --- | --- |
| 5 | about $150 | about $30 |
| 10 | about $214 | about $21 |
| 20 | about $340 | about $17 |

The 20-board row is less certain: its bare-board price and shipping weight were not quoted.

### Where the numbers come from

| Item | Cost | Source |
| --- | --- | --- |
| Set-up | $8.18 per order | JLCPCB price page |
| Stencil | $1.53 per order | JLCPCB price page |
| Fees for 9 part types JLCPCB does not keep loaded | $27.63 per order (9 × $3.07) | JLCPCB price page and parts library |
| Through-hole labour | $3.58 per order, plus $0.0164 a joint (22 a board) | JLCPCB price page |
| Surface-mount soldering | $0.0016 a joint (277 a board) | JLCPCB price page |
| Bare boards | $4.00 for 5, $5.00 for 10 | JLCPCB live quote |
| Parts | $8.49 a board | JLCPCB parts library |
| US tariff | 35% of the order, collected at checkout | JLCPCB US tariff FAQ, updated September 9, 2026 |
| Shipping | $26.64, UPS Express Saver, duty prepaid, 2–4 business days | JLCPCB live shipping calculator |
| California sales tax | 9.75% (Santa Clara), may add $15–$20 | Not confirmed whether JLCPCB charges it |

JLCPCB's cheaper Global Standard Direct Line ($6.95, 8–13 business days) is limited to orders of $59 or less, so an assembled order cannot use it. Checked live on JLCPCB's shipping calculator.

## Other ways it could be done

| Route, 5 boards | Total | Per board | Notes |
| --- | --- | --- | --- |
| JLCPCB assembly (the plan) | about $150 | about $30 | Above |
| Solder it yourself | about $115–$130 | about $23–$26 | Bare boards about $11 shipped, parts about $42 plus shipping and duty, stencil $7–$10. Tools not counted. Several parts are hard to solder by hand |
| PCBWay assembly | $34 before parts and duty | — | Parts priced only after a BOM upload to an account. "$29 for up to 20 boards" offer seems to cover 5 boards |
| PCBgogo, Elecrow assembly | about $135–$155 before parts | — | Already above JLCPCB's total |
| US assemblers (MacroFab, CircuitHub, Screaming Circuits) | — | — | No prices without an account |

Bare boards only, 5 boards shipped, before duty:

| Maker | Cheapest | Fastest |
| --- | --- | --- |
| JLCPCB | $10.95 (10–15 business days) | $38.24 (3–5) |
| PCBWay | $11.56 (7–13) | $31.55 (3–5) |
| Elecrow | $12.31 (9–16) | $50.54 (3–6) |
| Seeed Fusion | $18.11 (18–29) | $37.72 (6–9) |
| NextPCB | $25.96 (8–12) | $50.30 (3–6) |
| PCBgogo | $37.00 (5–8) | same |
| DigiKey DKRed (US) | $46.50, free shipping | |
| AISLER (EU) | $33.59 for 6, plus shipping and duty | |
| OSH Park (US) | $62.00 for 6, free shipping | |
| Advanced Circuits (US) | $165.00 | |

ALLPCB has suspended operations. Sunstone and Bay Area Circuits could not be priced without an account or a file.

## US import rules found (October 13, 2026)

- No duty-free allowance for parcels from China since 2025.
- Bare boards and most assemblies: about 37.5% official stacked rate. JLCPCB charges 35%, PCBWay 37.5% on bare boards and 47.5% on assembly.
- Couriers that collect duty on delivery add about $17.50 or more in fees, so duty-prepaid shipping is usually cheaper.
- Exclusions covering some bare boards are due to end November 9–10, 2026; check before ordering.

## Not done

- Component prices at DigiKey, Mouser and other US distributors (the lookup was stopped).
- Real checkout totals: these need an account and the finished board files.

## Research notes

The full notes behind these numbers, with every source, are in [`sourcing/`](sourcing/).
