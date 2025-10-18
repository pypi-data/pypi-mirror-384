{
    "name": "Spreadsheet Board User ACL",
    "summary": """
        Restricted access to spreadsheet dashboards app.
    """,
    "author": "Mint System GmbH",
    "website": "https://www.mint-system.ch/",
    "category": "Technical",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base_user_acl", "spreadsheet_dashboard"],
    "data": ["security/security.xml", "views/menu.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
