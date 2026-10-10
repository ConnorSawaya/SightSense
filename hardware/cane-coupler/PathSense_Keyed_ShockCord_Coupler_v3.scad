// PathSense keyed two-piece shaft coupler v3
// For 18 mm OD x 16 mm ID carbon-fiber tube
// One insert is permanently bonded in Tube A and carries a smaller keyed male tongue.
// A separate receiver insert is permanently bonded in Tube B.
// A continuous axial hole passes >=1/8 in shock cord.

$fn = 128;

// ---------- Tube / fit parameters ----------
tube_od = 18.0;
tube_id = 16.0;
insert_od = 15.70;       // slight clearance for epoxy / real tube tolerance

// ---------- Main (male) insert ----------
main_barrel_len = 42.0;  // glued inside Tube A
male_len = 20.0;         // protruding keyed tongue
male_w = 10.0;           // keyed rectangular tongue width
male_h = 8.5;            // keyed rectangular tongue height
male_tip_len = 2.0;      // tapered lead-in

// ---------- Receiver insert ----------
receiver_len = 34.0;     // glued inside Tube B
socket_depth = 20.5;
socket_w = 10.35;        // 0.35 mm total clearance vs tongue
socket_h = 8.85;
lead_depth = 2.0;
lead_w = 10.85;
lead_h = 9.35;

// ---------- Shock cord ----------
// 1/8 in = 3.175 mm. 4.2 mm gives comfortable threading clearance.
cord_hole_d = 4.20;

// ---------- Glue grooves ----------
groove_count = 3;
groove_depth = 0.35;
groove_width = 1.4;
groove_start = 7.0;
groove_pitch = 8.0;

// display mode: "main", "receiver", "exploded", "assembled", "demo"
MODE = "demo";

module barrel_with_grooves(len) {
    difference() {
        cylinder(d=insert_od, h=len);
        // shallow annular epoxy relief grooves
        for (i=[0:groove_count-1]) {
            z0 = groove_start + i*groove_pitch;
            translate([0,0,z0])
                difference() {
                    cylinder(d=insert_od+0.4, h=groove_width);
                    cylinder(d=insert_od-2*groove_depth, h=groove_width+0.02);
                }
        }
    }
}

module rounded_rect_prism(w,h,l,r=0.8) {
    // hull of 4 cylinders gives rounded rectangle cross section
    rr = min(r, min(w,h)/2 - 0.01);
    hull() {
        for (x=[-w/2+rr, w/2-rr])
            for (y=[-h/2+rr, h/2-rr])
                translate([x,y,0]) cylinder(r=rr, h=l);
    }
}

module male_tongue() {
    // body + tapered lead-in tip
    rounded_rect_prism(male_w, male_h, male_len-male_tip_len, 0.9);
    translate([0,0,male_len-male_tip_len])
        hull() {
            rounded_rect_prism(male_w, male_h, 0.01, 0.9);
            translate([0,0,male_tip_len])
                rounded_rect_prism(male_w-1.0, male_h-1.0, 0.01, 0.8);
        }
}

module main_insert() {
    difference() {
        union() {
            barrel_with_grooves(main_barrel_len);
            translate([0,0,main_barrel_len]) male_tongue();
        }
        // continuous shock-cord bore
        translate([0,0,-0.5]) cylinder(d=cord_hole_d, h=main_barrel_len+male_len+1.0);
    }
}

module socket_cutout() {
    // main keyed socket
    rounded_rect_prism(socket_w, socket_h, socket_depth+0.2, 1.0);
    // larger lead-in at mouth
    rounded_rect_prism(lead_w, lead_h, lead_depth, 1.1);
}

module receiver_insert() {
    difference() {
        barrel_with_grooves(receiver_len);
        // keyed female slot opens at z=0 and extends inward
        translate([0,0,-0.1]) socket_cutout();
        // continuous cord bore through full receiver
        translate([0,0,-0.5]) cylinder(d=cord_hole_d, h=receiver_len+1.0);
    }
}

module tube_segment(len=58) {
    difference() {
        cylinder(d=tube_od, h=len);
        translate([0,0,-0.5]) cylinder(d=tube_id, h=len+1.0);
    }
}

module demo_exploded() {
    // Male/main piece, tongue pointing right
    color([0.70,0.72,0.75])
        rotate([0,90,0]) main_insert();
    // Receiver piece aligned with tongue, spaced apart
    translate([main_barrel_len+male_len+25+receiver_len,0,0])
        color([0.45,0.48,0.52])
            rotate([0,-90,0]) receiver_insert();
}

module demo_with_tubes() {
    // Tube A extends left-to-right and ends exactly where the male tongue begins.
    color([0.12,0.12,0.14,0.32])
        rotate([0,90,0]) tube_segment(52);
    translate([10,0,0])
        color([0.72,0.74,0.78])
            rotate([0,90,0]) main_insert();

    // Tube B is a separate section. The female receiver is glued flush into its open end.
    translate([95,0,0]) {
        color([0.12,0.12,0.14,0.32])
            rotate([0,90,0]) tube_segment(52);
        color([0.46,0.49,0.54])
            rotate([0,90,0]) receiver_insert();
    }

    // 1/8 in shock cord shown in red; CAD bore itself is 4.2 mm.
    color([0.90,0.08,0.08])
        translate([-6,0,0])
            rotate([0,90,0]) cylinder(d=3.175, h=160);
}

if (MODE == "main") {
    main_insert();
} else if (MODE == "receiver") {
    receiver_insert();
} else if (MODE == "exploded") {
    demo_exploded();
} else if (MODE == "assembled") {
    // receiver socket aligned over male tongue with full engagement
    main_insert();
    translate([0,0,main_barrel_len+male_len])
        rotate([180,0,0]) receiver_insert();
} else {
    demo_with_tubes();
}
