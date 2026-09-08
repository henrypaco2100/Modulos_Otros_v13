{
    "name": "Hemodiálisis - Demo Clínico",
    "summary": "Hoja de sesión de hemodiálisis con registro pre, intra y post",
    "version": "13.0.1.0.0",
    "category": "Healthcare",
    "author": "Demo técnico",
    "license": "LGPL-3",
    "depends": ["base", "product"],
    "data": [
        "security/ir.model.access.csv",
        "data/dialysis_sequence.xml",
        "views/dialysis_patient_views.xml",
        "views/dialysis_session_views.xml",
        "views/dialysis_menus.xml",
    ],
    "application": True,
    "installable": True,
}
