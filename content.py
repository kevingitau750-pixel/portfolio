"""
Single source of truth for every piece of text, link and image on the site.

Edit THIS file to update the portfolio — the pages read from here and never
hard-code content. Anything still marked ``TODO`` is a placeholder for you to
fill in; those render as a small hint instead of breaking the page.

Image paths are relative to ``portfolio/assets/`` (e.g. ``"headshot.jpg"`` ->
``portfolio/assets/headshot.jpg``). Leave an image value as ``None`` and the
page falls back to a clean icon placeholder, so the site always renders.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Identity  — shown in the header, browser tab, and About page
# ---------------------------------------------------------------------------
PROFILE = {
    "name": "Kevin Gitau",
    "tagline": "Aeronautical Engineer · Aviation & Space Systems",
    "location": "Nairobi, Kenya",
    "headshot": None,  # add "headshot.jpg" to portfolio/assets/
    "summary": (
        "Aeronautical engineer (B.Eng, Technical University of Kenya) working "
        "across aviation regulation, airframe design and space systems. "
        "Experience spans KCAA-compliant drone-operations oversight, "
        "structural design and fabrication of solid-propellant rockets, and "
        "model-based systems engineering for spacecraft. I combine hands-on "
        "manufacturing with structural/CFD analysis, Python tooling and "
        "SysML v2, and I am focused on a career in the aviation industry "
        "applying that analytical and technical background."
    ),
    "focus_areas": [
        "Airframe structural design & analysis",
        "Aviation regulation & airworthiness (KCAA)",
        "Model-based systems engineering (SysML v2)",
        "CubeSat & space systems architecture",
        "CFD & structural simulation",
        "Manufacturing & composite fabrication",
    ],
    "resume_file": None,  # see note at bottom of file before enabling this
}

# ---------------------------------------------------------------------------
# Contact / links
# ---------------------------------------------------------------------------
CONTACT = {
    "email": "kevingitau750@gmail.com",
    "phone": "+254 742 726 989",   # set to None to hide it on the public site
    "linkedin": "https://www.linkedin.com/in/kevin-gitau-5227a22b0",
    "github": "TODO: https://github.com/your-handle",
    "website": None,
}

# ---------------------------------------------------------------------------
# Projects  — the portfolio. One dict per project.
# ---------------------------------------------------------------------------
PROJECTS = [
    {
        "title": "LEO Responsive Satellite-Based Flight Data Recorder (FDR)",
        "icon": "sat",
        "period": "2025 · Pending publication",
        "role": "Researcher · Final-year project",
        "summary": (
            "A Low Earth Orbit satellite-based backup Flight Data Recorder "
            "that addresses the limitations of conventional black-box recovery "
            "in remote, oceanic and conflict-zone crash scenarios."
        ),
        "highlights": [
            "Architected an end-to-end pipeline: real-time flight-data "
            "reception, on-orbit storage aboard a LEO platform, and ground-"
            "station relay for rapid post-incident retrieval",
            "Exploited LEO characteristics — low latency, high revisit rate, "
            "global coverage — to shrink the data-blackout window inherent to "
            "traditional FDR systems",
        ],
        "tech": ["Space systems", "Aviation safety", "Satellite comms", "Systems engineering"],
        "image": None,
        "links": {},
        "featured": True,
    },
    {
        "title": "FloodSat — CubeSat flood early-warning system for Kenya",
        "icon": "globe",
        "period": "2024–2025",
        "role": "Team lead",
        "summary": (
            "A model CubeSat mission concept for near-real-time flood early "
            "warning across Kenya's high-risk flood plains and river basins, "
            "developed with the Kenya Space Agency and the Italian Space "
            "Agency at the Luigi Broglio Space Centre, Malindi."
        ),
        "highlights": [
            "Led a multidisciplinary student team representing the Technical "
            "University of Kenya",
            "Defined mission architecture: payload selection, data "
            "acquisition, downlink strategy and ground-segment integration",
            "Two weeks on-site at Malindi interfacing with ground-station and "
            "orbital-tracking infrastructure; exposure to bilateral space-"
            "agency programme management and mission reviews",
        ],
        "tech": ["CubeSat", "Mission design", "Ground segment", "Remote sensing"],
        "image": None,
        "links": {},
        "featured": True,
    },
    {
        "title": "MBSE spacecraft systems model — SysML v2",
        "icon": "hub",
        "period": "2025",
        "role": "Developer",
        "summary": (
            "SysML v2 textual models of a multi-subsystem aerospace system — "
            "part definitions, typed port hierarchies, interface definitions "
            "and inter-subsystem signal flows (electrical harnesses, command "
            "uplinks, telemetry downlinks, data buses)."
        ),
        "highlights": [
            "Authored KerML/SysML v2 XMI serialisations conformant with the "
            "OMG SysML v2.0 specification (September 2025)",
            "Reverse-engineered subsystem decomposition from CATIA Magic MSoSA "
            "into standards-compliant SysML v2 models across avionics "
            "subsystems (primary/backup OBCs, C&DH, software)",
        ],
        "tech": ["SysML v2", "KerML", "CATIA Magic (Cameo)", "MBSE"],
        "image": None,
        "links": {},
        "featured": True,
    },
    {
        "title": "SysML v2 Wirelist Generator",
        "icon": "hub",
        "period": "2025",
        "role": "Developer",
        "summary": (
            "Streamlit tool that parses a SysML v2 model of an aerospace "
            "system and produces a formatted Excel wirelist — all "
            "connections, per-subsystem sheets, unconnected-port checks, "
            "external interfaces and a summary."
        ),
        "highlights": [
            "MBSE applied directly to electrical-harness definition",
            "Automated cross-checking of unconnected ports",
            "One-click Excel export for downstream electrical design",
        ],
        "tech": ["Python", "SysML v2", "Streamlit", "openpyxl", "pandas"],
        "image": None,
        "links": {},
        "featured": False,
    },
    {
        "title": "Starlink LEO constellation visualizer",
        "icon": "sat",
        "period": "2025",
        "role": "Developer",
        "summary": (
            "3D globe (CesiumJS) with live SGP4 orbit propagation of the "
            "Starlink constellation from cached CelesTrak TLEs, plus area-of-"
            "interest field-of-view and pass analysis with a scrubbable "
            "simulation clock and Excel/CSV/KML export."
        ),
        "highlights": [
            "Real look-angle geometry (elevation-angle visibility test)",
            "Full-catalogue multi-hour pass reports generated server-side",
            "Ground-track computation and KML export for GIS tools",
        ],
        "tech": ["JavaScript", "CesiumJS", "satellite.js / SGP4", "Python", "skyfield"],
        "image": None,
        "links": {},
        "featured": False,
    },
    {
        "title": "Novel Space Equity Index (SEI) framework",
        "icon": "globe",
        "period": "Pending publication",
        "role": "Researcher",
        "summary": (
            "A quantitative framework for measuring and promoting fair, "
            "inclusive participation of all nations in space exploration, "
            "technology and governance, regardless of economic status."
        ),
        "highlights": [
            "Defined space equity across three dimensions — access, benefit "
            "and contribution",
            "Designed the SEI as a policy instrument for space agencies, UN "
            "COPUOS and emerging spacefaring nations to benchmark equity over "
            "time",
        ],
        "tech": ["Space policy", "Equity frameworks", "Space governance"],
        "image": None,
        "links": {},
        "featured": False,
    },
    {
        "title": "Quantum-classical framework for Space Traffic Management",
        "icon": "sat",
        "period": "Pending publication",
        "role": "Contributor",
        "summary": (
            "A hierarchical quantum-classical framework for autonomous Space "
            "Traffic Management, addressing growing collision risk in Low "
            "Earth Orbit."
        ),
        "highlights": [
            "Helped formulate satellite collision avoidance as dual QUBO "
            "problems solvable by quantum annealing and gate-based quantum "
            "computing",
            "Modelled a synthetic 1,000-satellite LEO constellation to "
            "identify and prioritise high-risk collision pairs",
        ],
        "tech": ["Quantum computing", "Orbital mechanics", "Collision avoidance"],
        "image": None,
        "links": {},
        "featured": False,
    },
]

# ---------------------------------------------------------------------------
# Experience  — reverse-chronological
# ---------------------------------------------------------------------------
EXPERIENCE = [
    {
        "title": "Assistant UTO & Remote Operator Certificate Administrator",
        "org": "Geoid Technologies Limited",
        "location": "Nairobi, Kenya",
        "start": "Jan 2026",
        "end": "Present",
        "bullets": [
            "Participate in internal and external audits in accordance with "
            "KCAA regulations, and develop the resulting Corrective Action "
            "Plans (CAPs)",
            "Contributed to the overhaul revision of the Remote Aircraft "
            "Operator Certificate and Unmanned Training Organization manuals",
            "Ensure commercial drone operations comply with Kenya Civil "
            "Aviation Authority regulations",
            "Support facilitation of UTO training programmes to KCAA standards",
        ],
        "tags": ["KCAA", "Airworthiness", "Auditing", "UAS operations"],
    },
    {
        "title": "Learning Officer & Co-founder",
        "org": "CubeKraft",
        "location": "Nairobi, Kenya",
        "start": "Jan 2025",
        "end": "Present",
        "bullets": [
            "Co-founded a student-led space-technology startup providing "
            "education on CubeSat systems for research and training",
            "Lead the development and training division, designing hands-on "
            "learning programmes to build capacity in the space sector",
            "Developed a standard curriculum and facilitated technical "
            "workshops for new cohorts from the Technical University of Kenya "
            "and Kenyatta University",
        ],
        "tags": ["CubeSat", "Curriculum", "Training"],
    },
    {
        "title": "Airframe Engineer Intern",
        "org": "Nakuja Project",
        "location": "Kiambu, Kenya",
        "start": "Jul 2025",
        "end": "Dec 2025",
        "bullets": [
            "Contributed to the design, research and fabrication of solid-"
            "propellant rockets",
            "Structural design and analysis of rocket airframes — optimised "
            "body-tube geometry and material selection for the N-4 system",
            "Fabricated and assembled body tubes using composite layup and "
            "machining; supported launchpad design, welding and mechanical "
            "testing",
            "Prepared technical documentation, SolidWorks CAD models and test "
            "reports across design iterations",
        ],
        "tags": ["Airframe", "Structures", "Composites", "SolidWorks"],
    },
]

EDUCATION = [
    {
        "qualification": "B.Eng, Aeronautical Engineering",
        "org": "The Technical University of Kenya",
        "location": "Nairobi, Kenya",
        "start": "",
        "end": "Nov 2025",
        "details": [
            "Second-class honours (upper division)",
            "Final-year project: Development of a Low Earth Orbit responsive "
            "satellite-based Flight Data Recorder",
            "Relevant coursework: Aircraft Design, Propulsion Systems, Flight "
            "Mechanics, Control Systems, Space Systems Engineering, Aviation "
            "Legislation, CAD",
        ],
    },
]

# Licences, ratings and short courses
CERTIFICATIONS = [
    {"name": "Ansys Associate — Foundations in Stress Analysis", "issuer": "Ansys", "year": "2025"},
    {"name": "CubeSat Training", "issuer": "Luigi Broglio – Malindi Space Centre", "year": "2024–2025"},
    {"name": "Understanding Space", "issuer": "Teaching Science & Technology, Inc.", "year": "2024–2025"},
    {"name": "Engineering Job Simulation", "issuer": "British Airways (Forage)", "year": "2026"},
]

# ---------------------------------------------------------------------------
# Skills  — grouped; each skill is (name, level 1–5). Adjust levels freely.
# ---------------------------------------------------------------------------
SKILLS = {
    "Engineering & analysis": [
        ("Airframe structural analysis", 4),
        ("CFD simulation", 3),
        ("CAD (SolidWorks, CATIA)", 4),
        ("Manufacturing & composite fabrication", 4),
        ("Propulsion & flight mechanics", 3),
    ],
    "Systems & software": [
        ("Systems modelling (SysML v2 / KerML)", 4),
        ("CATIA Magic / Cameo MSoSA", 3),
        ("Python", 4),
        ("Ansys", 3),
        ("CubeSat & space-system architecture", 4),
    ],
    "Aviation & professional": [
        ("Aviation law & regulation (KCAA)", 4),
        ("Airworthiness auditing & CAPs", 3),
        ("Technical writing & documentation", 4),
        ("Project management", 3),
        ("Team leadership", 4),
    ],
}

# ---------------------------------------------------------------------------
# Professional memberships
#   Not on the résumé — fill in any student/professional bodies you belong to
#   (e.g. RAeS, AIAA, Engineers Board of Kenya / IEK, Kenya Space sector groups).
# ---------------------------------------------------------------------------
MEMBERSHIPS = [
    {
        "body": "TODO: e.g. Royal Aeronautical Society (RAeS)",
        "grade": "TODO: e.g. Student Affiliate",
        "since": "TODO: YYYY",
        "number": None,
        "note": None,
    },
    {
        "body": "TODO: e.g. Engineers Board of Kenya (EBK)",
        "grade": "TODO: e.g. Graduate Engineer",
        "since": "TODO",
        "number": None,
        "note": None,
    },
]

# ---------------------------------------------------------------------------
# NOTE on the résumé download:
#   The PDF you shared contains three referees' personal phone numbers and
#   e-mail addresses. Do not publish that version. Make a public copy with the
#   referees replaced by "References available on request", save it as
#   portfolio/assets/resume.pdf, then set PROFILE["resume_file"] = "resume.pdf".
# ---------------------------------------------------------------------------
