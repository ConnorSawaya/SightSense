# Cane board: what it costs to have made

Checked on October 13 and 14, 2026. Prices are US dollars. Nothing has been ordered, so these are estimates built from live quotes and published fees, not checkout totals.

The plan is turnkey assembly (PCBA) by JLCPCB. Parts are listed line by line in [`BOM.md`](BOM.md): $10.48 a board.

## Current estimate, October 14

For the board as it stands: 46 × 100 mm, 4 copper layers, black solder mask, the ready-made 5 V module, the XT30 motor socket and 7 Extended part lines. Worked out from the fees below; not a checkout total.

Roughly **$74 to start, plus the bare boards, plus about $15.30 a board**, delivered to the San Francisco Bay Area with the 35% US tariff paid.

| Boards | Total | Per board |
| --- | --- | --- |
| 5 | about $172 | about $34 |
| 10 | about $260 | about $26 |

- Bare boards, 5 at 4 layers black: $16.00 (JLCPCB live quote for 40 × 100 mm; the 46 mm width was not re-quoted). The 10-board price was not quoted; $25 is assumed.
- The module costs about $2 a board more than the converter built from parts, but saves two Extended lines ($6.14 an order) and the converter's layout risk.
- Choosing green mask saves about $11 on 5 boards.

Earlier figures, kept for comparison: the 2-layer green design with 9 Extended lines came to about $150 for 5 and $214 for 10 ($88 to start plus $12.50 a board).

### Where the numbers come from

| Item | Cost | Source |
| --- | --- | --- |
| Set-up | $8.18 per order | JLCPCB price page |
| Stencil | $1.53 per order | JLCPCB price page |
| Fees for 7 part types JLCPCB does not keep loaded | $21.49 per order (7 × $3.07) | JLCPCB price page and parts library |
| Through-hole labour | $3.58 per order, plus $0.0164 a joint (about 25 a board) | JLCPCB price page |
| Surface-mount soldering | $0.0016 a joint (277 a board) | JLCPCB price page |
| Bare boards | $16.00 for 5 at 4 layers black ($4.00 for 2 layers green) | JLCPCB live quote |
| Parts | $10.48 a board | JLCPCB parts library |
| US tariff | 35% of the order, collected at checkout | JLCPCB US tariff FAQ, updated September 9, 2026 |
| Shipping | $26.64, UPS Express Saver, duty prepaid, 2–4 business days | JLCPCB live shipping calculator |
| California sales tax | About 9–10%, may add $15–$20 | Not confirmed whether JLCPCB charges it |

JLCPCB's cheaper Global Standard Direct Line ($6.95, 8–13 business days) is limited to orders of $59 or less, so an assembled order cannot use it. Checked live on JLCPCB's shipping calculator.

## Other ways it could be done

| Route, 5 boards | Total | Per board | Notes |
| --- | --- | --- | --- |
| JLCPCB assembly (the plan) | about $172 | about $34 | Above, 4 layers black |
| Solder it yourself (2-layer figures, not updated) | about $115–$130 | about $23–$26 | Bare boards about $11 shipped, parts about $42 plus shipping and duty, stencil $7–$10. Tools not counted. Several parts are hard to solder by hand |
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
