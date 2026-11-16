# Building the cane board yourself

What 5 bare boards, a stencil and the parts cost if you solder them yourself, instead of ordering them assembled. Prices read live on October 17, 2026 unless marked; tariffs are estimates.

The parts list for this is [`export/hand-build-bom.csv`](export/hand-build-bom.csv): every part, what to buy for 5 boards with a few spares, the LCSC number, and how hard it is to solder by hand.

## Bare boards (JLCPCB, 5 boards, 4 layers, 46 × 100 mm, 1.6 mm)

| Finish | Green | Black |
| --- | --- | --- |
| HASL with lead | $8.00 | $16.00 |
| Lead-free HASL | $13.10 | $21.10 |
| ENIG (flat gold) | $25.10 | $33.10 |

Black adds $8.00 whatever the finish. Leaded HASL is fine for a hand build; ENIG is flatter, which helps the paste on the motor driver and the USB-C socket, but triples the price.

## Stencil

A steel stencil for the top side: $7.22 (JLCPCB, frameless, 380 × 280 mm, 0.96 kg). It puts paste on every pad in one pass, including the pads under the ESP32 and the motor driver. JLCPCB pre-collects 90% duty on stencils on its duty-paid lines.

## Shipping from JLCPCB to the US

| Method | Boards only (0.20 kg) | Stencil only (0.96 kg) | Time |
| --- | --- | --- | --- |
| Global Standard Direct Line | $7.13 | $18.72 | 8–13 business days |
| UPS Express Saver (duty paid) | $26.64 | $31.73 | 2–4 business days |
| DHL Express (duty paid) | $31.59 | $33.03 | 2–4 business days |

The Direct Line takes orders up to $59 and 1.5 kg. Boards and stencil together were not quoted; expect about $19–22 on the Direct Line (estimate). JLCPCB does not say whether the Direct Line includes duty.

## Parts (LCSC)

All 40 lines in stock at LCSC: **$72.39** for 5 boards, buying each part's minimum or a few spares (about 20% extra on small parts, one spare motor driver). Seven parts were out of stock and are replaced by the same part from another maker, or the same value and size:

| Designed | Replacement | Why it is the same |
| --- | --- | --- |
| SMBJ15A, C19077569 | SMBJ15A (MDD), C113988 | Same part |
| B5819W, C8598 | B5819W-G (JSCJ), C164911 | Same part |
| 22 µF 25 V 1206, C12891 | 22 µF 35 V X5R 1206 (Chinocera), C22367833 | Same size, higher voltage |
| 10 kΩ 0603, C25804 | NQ03WAF1002T5E (UNI-ROYAL), C965184 | Same value and size |
| 47 kΩ 0603, C25819 | 0603WAD4702T5E (UNI-ROYAL), C2767079 | Same value, 0.5% |
| 1 µF 50 V 0603, C15849 | CSA0603X5R105K500JT (HRE), C20070310 | Same value and rating |
| 1 kΩ 0603, C21190 | FRC0603F1001TS (FOJAN), C2907002 | Same value and size |

LCSC shipping to the US: about $12.85 on its Global Direct line, 7–15 business days (read October 13 for a cart of these parts). LCSC leaves duty to the buyer; at 37.5% on passives and connectors and 50% on chips that could be up to about $30 if customs bills it (estimate).

The prices are LCSC's and change daily; stock can run out between now and ordering.

### DigiKey and Mouser (checked October 17)

Dearer, and short of several parts. One-piece prices against LCSC's: ESP32 module $5.21 at both (LCSC $4.46), DRV8876 $1.95 at Mouser (LCSC $0.71), AO3401A $0.52 at DigiKey (LCSC $0.10). Neither stocks the USB-C socket, the 4 A 30 V fuse or the barrel jack; Mouser has no XT30 and no Alpha & Omega transistors, and DigiKey lists only a different maker's XT30. Both ship from the US, but both now pass tariffs on: DigiKey on the invoice, Mouser as a fee of about 8–20% on many parts. DigiKey's ground shipping is $4.99–8.49. Many DigiKey prices sat behind a human check and were not read.

## What it adds up to (5 boards, green, cheapest shipping)

| | About |
| --- | --- |
| Boards | $8.00 |
| Stencil | $7.22 |
| JLCPCB shipping and duty | $20–31 (estimate) |
| Parts | $72.39 |
| LCSC shipping and duty | $13–43 (estimate) |
| **Total** | **about $120–160** |

Against about $263 for the same 5 boards assembled by JLCPCB. Tools are extra: a hot plate at least 100 × 100 mm, solder paste, flux, solder wick, fine tweezers and a magnifier, roughly $60–100.

## How hard it is

82 parts on the top side: 5 hard (the ESP32 module and the motor driver have pads underneath; the USB-C socket's 16 pins bridge easily; two diodes are 1 × 0.6 mm), 55 fiddly (0603 parts and SOT-23s) and 22 easy (through-hole plugs, the 5 V module and large parts). With a stencil and a hot plate all the surface parts are soldered at once; the 9 through-hole parts go on afterwards with an iron.
