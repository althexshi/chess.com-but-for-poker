// ---------------------------------------------------------------------------
// This file is the ONLY file you need to edit to add yourself to the team
// page. Everything else (docs/main.js) just reads this list and builds the
// page from it.
//
// To add a new person:
//   1. Copy one whole object below, from the opening "{" to the closing "},"
//   2. Paste it right before the closing "];" at the bottom of this file
//   3. Fill in your own details
//
// Every field is a plain string, except "skills" and "projects", which are
// lists. Leave "github" or "linkedin" as an empty string ("") if you do not
// want to share that link.
// ---------------------------------------------------------------------------

const teamMembers = [
    {
        name: "Jorge Maldonado",
        role: "Machine Learning & Backend",
        location: "TODO: add your city/state",
        focusArea: "Behavioral Risk Screening",
        bio: "TODO: write two or three sentences about yourself here. " +
             "Talk about how you got interested in this project, what you " +
             "have been working on, and what you want to learn next.",
        skills: [
            "Python",
            "pandas",
            "scikit-learn",
            "XGBoost",
            "FastAPI",
            "Streamlit",
            "Git & GitHub",
            "Jupyter Notebook"
        ],
        projects: [
            {
                title: "Poker AI Coach with Addiction Screening",
                description: "An AI poker coach that teaches Hold'em strategy " +
                              "while screening for loss-chasing and gambling-risk " +
                              "behavior patterns.",
                link: "https://github.com/althexshi/chess.com-but-for-poker"
            }
        ],
        email: "maldonadoj747@gmail.com",
        github: "",
        linkedin: ""
    }
];
