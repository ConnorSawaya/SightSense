# Component suppliers for hand-soldering the cane board (5 and 10 boards, delivered to Santa Clara CA 95051)

DRAFT IN PROGRESS (saved early, October 13, 2026). Sections below the LCSC table are still being researched.

## LCSC: every line at the 5-board and 10-board quantity

### Takeaway
(provisional) All 42 lines priced from LCSC's product-detail JSON today. Parts only: about $53 for 5 boards and $88 for 10 boards as actually ordered (minimums and multiples), before shipping and duty. Five lines show zero stock today and need an in-stock substitute (rows marked "s").

### Cited Findings
All figures "read from the distributor today" via https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=<code> (fetched 2026-10-13 about 19:07 PDT). "Needed $" = quantity needed x the unit price at the ordered quantity; "Ordered $" = what the order line costs.

| # | Refs | Value | Part bought (LCSC code) | Per board | Min / multiple | Stock | 5 boards: need → order | Unit $ | Needed $ | Ordered $ | 10 boards: need → order | Unit $ | Needed $ | Ordered $ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | U1 | ESP32-S3-WROOM-1-N4 | ESP32-S3-WROOM-1-N4 (C2913197) ESPRESSIF | 1 | 1 / 1 | 2,543 | 5 → 5 | 4.1495 | 20.75 | 20.75 | 10 → 10 | 3.6743 | 36.74 | 36.74 |
| 2 | U2 | DRV8876PWPR | DRV8876PWPR (C575551) TI | 1 | 1 / 1 | 29,703 | 5 → 5 | 0.7860 | 3.93 | 3.93 | 10 → 10 | 0.6380 | 6.38 | 6.38 |
| 3 | U3 | TPS54302DDCR | TPS54302DDCR (C311983) TI | 1 | 5 / 5 | 58,405 | 5 → 5 | 0.3029 | 1.51 | 1.51 | 10 → 10 | 0.3029 | 3.03 | 3.03 |
| 4 | U4 | AP2112K-3.3 | AP2112K-3.3TRG1 (C51118) DIODES | 1 | 5 / 5 | 21,870 | 5 → 5 | 0.1729 | 0.86 | 0.86 | 10 → 10 | 0.1729 | 1.73 | 1.73 |
| 5 | Q1…Q2 | AO3401A | AO3401A (C15127) AOS | 3 | 5 / 5 | 120,585 | 15 → 15 | 0.1026 | 1.54 | 1.54 | 30 → 30 | 0.1026 | 3.08 | 3.08 |
| 6 | Q3 | AO3400A | AO3400A (C20917) AOS | 1 | 5 / 5 | 208,695 | 5 → 5 | 0.0898 | 0.45 | 0.45 | 10 → 10 | 0.0898 | 0.90 | 0.90 |
| 7 | D1 | SMBJ15A | SMBJ15A (C19077569) R+O | 1 | 5 / 5 | 4,470 | 5 → 5 | 0.0555 | 0.28 | 0.28 | 10 → 10 | 0.0555 | 0.56 | 0.56 |
| 8 | D4 | BAT54S | BAT54S (C7420333) R+O | 1 | 50 / 50 | 919,250 | 5 → 50 | 0.0139 | 0.07 | 0.69 | 10 → 50 | 0.0139 | 0.14 | 0.69 |
| 9 | D5…D7 | B5819W | B5819W SL (C8598) JSCJ | 3 | 20 / 20 | 3,000 | 15 → 20 | 0.0286 | 0.43 | 0.57 | 30 → 40 | 0.0286 | 0.86 | 1.14 |
| 10 | D8…D9 | H5VL10B | H5VL10B (C7420372) R+O | 2 | 50 / 50 | 10,029,550 | 10 → 50 | 0.0065 | 0.07 | 0.33 | 20 → 50 | 0.0065 | 0.13 | 0.33 |
| 11 | LED1…LED3 | Red | KT-0603R (C2286) Hubei KENTO Elec | 3 | 100 / 100 | 4,584,600 | 15 → 100 | 0.0077 | 0.12 | 0.77 | 30 → 100 | 0.0077 | 0.23 | 0.77 |
| 12 | L1 | 10uH 3.2A | FNR6045S100MT (C168076) cjiang | 1 | 10 / 10 | 11,090 | 5 → 10 | 0.1130 | 0.57 | 1.13 | 10 → 10 | 0.1130 | 1.13 | 1.13 |
| 13 | F1 | PTC 4A | BSMD2920-400-30V (C20539726) BHFUSE | 1 | 5 / 5 | 19,090 | 5 → 5 | 0.2255 | 1.13 | 1.13 | 10 → 10 | 0.2255 | 2.25 | 2.25 |
| 14 | C1 | 220uF 25V | EMK1EM221FB0D00R (C724620) AISHI | 1 | 5 / 5 | 21,925 | 5 → 5 | 0.1149 | 0.57 | 0.57 | 10 → 10 | 0.1149 | 1.15 | 1.15 |
| 15 | C3…C14 | 22uF 25V | CL31A226KAHNNNE (C12891) Samsung Electro-Mechanics | 4 | 20 / 20 | **0** | 20 → 20 | 0.1296 | 2.59 | 2.59 | 40 → 40 | 0.1296 | 5.18 | 5.18 |
| 15s | C3…C14 | 22uF 25V | TCC1206X5R226K250HT (C5448922) CCTC | 4 | 5 / 5 | 107,690 | 20 → 20 | 0.1627 | 3.25 | 3.25 | 40 → 40 | 0.1627 | 6.51 | 6.51 |
| 16 | C6 | 22nF 50V | CL10B223KB8NNNC (C21122) Samsung Electro-Mechanics | 1 | 50 / 50 | 289,400 | 5 → 50 | 0.0076 | 0.04 | 0.38 | 10 → 50 | 0.0076 | 0.08 | 0.38 |
| 17 | C8…C21 | 1uF 50V | CL10A105KB8NNNC (C15849) Samsung Electro-Mechanics | 3 | 50 / 50 | 100 | 15 → 50 | 0.0159 | 0.24 | 0.80 | 30 → 50 | 0.0159 | 0.48 | 0.80 |
| 18 | C10 | 10uF 50V | CL31A106KBHNNNE (C13585) Samsung Electro-Mechanics | 1 | 10 / 10 | **0** | 5 → 10 | 0.1600 | 0.80 | 1.60 | 10 → 10 | 0.1600 | 1.60 | 1.60 |
| 18s | C10 | 10uF 50V | HGC1206R5106K500NSPJ (C7432781) Chinocera | 1 | 10 / 10 | 647,210 | 5 → 10 | 0.1292 | 0.65 | 1.29 | 10 → 10 | 0.1292 | 1.29 | 1.29 |
| 19 | C15…C16 | 10uF 25V | CL21A106KAYNNNE (C15850) Samsung Electro-Mechanics | 2 | 20 / 20 | **0** | 10 → 20 | 0.0695 | 0.70 | 1.39 | 20 → 20 | 0.0695 | 1.39 | 1.39 |
| 19s | C15…C16 | 10uF 25V | CL21A106KAYNNNG (C318691) Samsung Electro-Mechanics | 2 | 5 / 5 | 373,030 | 10 → 10 | 0.1076 | 1.08 | 1.08 | 20 → 20 | 0.1076 | 2.15 | 2.15 |
| 20 | C19 | 22uF 6.3V | CL10A226MQ8NRNC (C59461) Samsung Electro-Mechanics | 1 | 20 / 20 | 4,412,180 | 5 → 20 | 0.0315 | 0.16 | 0.63 | 10 → 20 | 0.0315 | 0.32 | 0.63 |
| 21 | C25 | 100pF | CL10C101JB8NNNC (C14858) Samsung Electro-Mechanics | 1 | 50 / 50 | 203,300 | 5 → 50 | 0.0087 | 0.04 | 0.43 | 10 → 50 | 0.0087 | 0.09 | 0.43 |
| 22 | C26…C24 | 100nF 50V | CC0603KRX7R9BB104 (C14663) YAGEO | 10 | 50 / 50 | 58,600 | 50 → 50 | 0.0142 | 0.71 | 0.71 | 100 → 100 | 0.0142 | 1.42 | 1.42 |
| 23 | R1…R33 | 100k | 0603WAF1003T5E (C25803) UNI-ROYAL | 7 | 100 / 100 | 11,634,500 | 35 → 100 | 0.0031 | 0.11 | 0.31 | 70 → 100 | 0.0031 | 0.22 | 0.31 |
| 24 | R4…R31 | 4.7k | 0603WAF4701T5E (C23162) UNI-ROYAL | 3 | 100 / 100 | 8,276,600 | 15 → 100 | 0.0028 | 0.04 | 0.28 | 30 → 100 | 0.0028 | 0.08 | 0.28 |
| 25 | R5 | 2.2k | 0603WAF2201T5E (C4190) UNI-ROYAL | 1 | 100 / 100 | 4,474,200 | 5 → 100 | 0.0018 | 0.01 | 0.18 | 10 → 100 | 0.0018 | 0.02 | 0.18 |
| 26 | R6…R28 | 10k | 0603WAF1002T5E (C25804) UNI-ROYAL | 7 | 100 / 100 | **0** | 35 → 100 | 0.0052 | 0.18 | 0.52 | 70 → 100 | 0.0052 | 0.36 | 0.52 |
| 26s | R6…R28 | 10k | RC0603FR-0710KL (C98220) YAGEO | 7 | 100 / 100 | 4,330,300 | 35 → 100 | 0.0034 | 0.12 | 0.34 | 70 → 100 | 0.0034 | 0.24 | 0.34 |
| 27 | R10 | 220 | 0603WAF2200T5E (C22962) UNI-ROYAL | 1 | 100 / 100 | 606,500 | 5 → 100 | 0.0035 | 0.02 | 0.35 | 10 → 100 | 0.0035 | 0.04 | 0.35 |
| 28 | R13 | 13k | 0603WAF1302T5E (C22797) UNI-ROYAL | 1 | 100 / 100 | 99,600 | 5 → 100 | 0.0029 | 0.01 | 0.29 | 10 → 100 | 0.0029 | 0.03 | 0.29 |
| 29 | R14…R29 | 1k | 0603WAF1001T5E (C21190) UNI-ROYAL | 3 | 100 / 100 | 1,172,800 | 15 → 100 | 0.0020 | 0.03 | 0.20 | 30 → 100 | 0.0020 | 0.06 | 0.20 |
| 30 | R19…R20 | 5.1k | 0603WAF5101T5E (C23186) UNI-ROYAL | 2 | 100 / 100 | 19,297,900 | 10 → 100 | 0.0015 | 0.01 | 0.15 | 20 → 100 | 0.0015 | 0.03 | 0.15 |
| 31 | R25…R27 | 22k | 0603WAF2202T5E (C31850) UNI-ROYAL | 2 | 100 / 100 | 2,308,300 | 10 → 100 | 0.0042 | 0.04 | 0.42 | 20 → 100 | 0.0042 | 0.08 | 0.42 |
| 32 | R32 | 100 | 0603WAF1000T5E (C22775) UNI-ROYAL | 1 | 100 / 100 | 3,694,900 | 5 → 100 | 0.0026 | 0.01 | 0.26 | 10 → 100 | 0.0026 | 0.03 | 0.26 |
| 33 | R34…R2 | 47k | 0603WAF4702T5E (C25819) UNI-ROYAL | 2 | 100 / 100 | **0** | 10 → 100 | 0.0021 | 0.02 | 0.21 | 20 → 100 | 0.0021 | 0.04 | 0.21 |
| 33s | R34…R2 | 47k | RC0603FR-0747KL (C105579) YAGEO | 2 | 100 / 100 | 150,400 | 10 → 100 | 0.0031 | 0.03 | 0.31 | 20 → 100 | 0.0031 | 0.06 | 0.31 |
| 34 | J1 | 12V battery | DC-005-5A-2.0 (C381116) XKB Connection | 1 | 5 / 5 | 19,870 | 5 → 5 | 0.2633 | 1.32 | 1.32 | 10 → 10 | 0.2633 | 2.63 | 2.63 |
| 35 | J2 | Motor | KF128-5.08-2P-AA (C474952) Cixi Kefa Elec | 1 | 5 / 5 | 57,930 | 5 → 5 | 0.1937 | 0.97 | 0.97 | 10 → 10 | 0.1937 | 1.94 | 1.94 |
| 36 | J3…J7 | Kill switch / Talk but | B2B-XH-A(LF)(SN) (C158012) JST | 3 | 20 / 20 | 227,480 | 15 → 20 | 0.0409 | 0.61 | 0.82 | 30 → 40 | 0.0409 | 1.23 | 1.64 |
| 37 | J5 | Encoder | B4B-XH-A(LF)(SN) (C144395) JST | 1 | 10 / 10 | 150,250 | 5 → 10 | 0.0600 | 0.30 | 0.60 | 10 → 10 | 0.0600 | 0.60 | 0.60 |
| 38 | J6 | I2C | PZ254V-11-04P (C2691448) XFCN | 1 | 20 / 20 | 807,840 | 5 → 20 | 0.0276 | 0.14 | 0.55 | 10 → 20 | 0.0276 | 0.28 | 0.55 |
| 39 | J8 | Serial | PZ254V-11-03P (C2937625) XFCN | 1 | 50 / 50 | 824,850 | 5 → 50 | 0.0199 | 0.10 | 1.00 | 10 → 50 | 0.0199 | 0.20 | 1.00 |
| 40 | J11 | Firmware | TYPE-C-31-M-12 (C165948) Korean Hroparts Elec | 1 | 5 / 5 | 375,650 | 5 → 5 | 0.1879 | 0.94 | 0.94 | 10 → 10 | 0.1879 | 1.88 | 1.88 |
| 41 | SW1…SW2 | Reset / Boot | TS-1187A-B-A-B (C318884) XKB Connection | 2 | 20 / 20 | 74,020 | 10 → 20 | 0.0207 | 0.21 | 0.41 | 20 → 20 | 0.0207 | 0.41 | 0.41 |
| 42 | SW3 | Power | MSK12C02 (C431540) SHOU HAN | 1 | 10 / 10 | 169,550 | 5 → 10 | 0.0571 | 0.29 | 0.57 | 10 → 10 | 0.0571 | 0.57 | 0.57 |


listed parts (ignoring stock): 5 boards needed 42.91 ordered 53.39 ; 10 boards needed 79.58 ordered 86.10
with in-stock substitutes:     5 boards needed 43.74 ordered 53.35 ; 10 boards needed 81.25 ordered 87.80
net weight g {5: 136.72, 10: 202.73000000000002}

### LCSC cart, read in a guest cart on lcsc.com today (Ship To: United States, 95051) -- raw notes, to be tidied
- 10-board cart (42 lines, substitutes for the 5 zero-stock lines; C15849 1uF 50V went to 0 stock between 19:07 and 19:55 and shows "50 - Backordered"): Merchandise Total $87.83, Merchandise Discount -$6.13 (three lines zeroed as free samples: C51118 $1.73, C311983 $3.03, C20917 $0.90; plus 5-8% promo on C20539726, C7432781, C2691448, C2937625, C165948, C431540), Estimated Weight 1,500 g, no handling fee, no duty/tariff line. Shipping options: Global Direct Standard Line $15.87 (7-15 business days); 4PX $32.12 (5-10); DHL Express $45.48 (3-7); UPS $47.75 (3-7); FedEx International Priority $50.09 (3-7); FedEx International Economy $51.62 (4-8). Total with Global Direct $97.57.
- 5-board cart: Merchandise Total $53.37, Merchandise Discount -$3.13, Estimated Weight 1,500 g. Global Direct Standard Line $12.85 (7-15 business days); 4PX $25.51 (5-10); DHL Express $45.48 (3-7); UPS $47.75 (3-7); FedEx International Priority $49.15 (3-7); FedEx International Economy $50.70 (4-8). Total with Global Direct $63.09.
- 1-module cart ($4.15): Global Direct $7.91, 4PX $15.05, DHL $38.71, UPS $40.41, FedEx IP $42.96, FedEx IE $43.83; Estimated Weight 1,000 g; Handling Fee $3, waived at $15 merchandise ("Add $10.85+ to waive $3 fee").
- Cart text: "Customers are responsible for any duties and taxes imposed by customs at the destination. For DDP (Delivered Duty Paid) inquiries, please contact our customer service team."
- Lead time shown per line: "In Stock, Estimated lead time: 1-2 business days".
