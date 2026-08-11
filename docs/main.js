// ---------------------------------------------------------------------------
// This file reads the list of people from docs/team-data.js and builds one
// card per person on the page. You should not need to edit this file just
// to add a new teammate — that happens in docs/team-data.js instead.
// ---------------------------------------------------------------------------

function getInitials(fullName) {
    const nameParts = fullName.trim().split(" ");
    const firstInitial = nameParts[0].charAt(0);
    const lastInitial = nameParts[nameParts.length - 1].charAt(0);
    return (firstInitial + lastInitial).toUpperCase();
}

function buildSkillTag(skillName) {
    const tag = document.createElement("li");
    tag.className = "skill-tag";
    tag.textContent = skillName;
    return tag;
}

function buildSkillsSection(skillsList) {
    const section = document.createElement("div");
    section.className = "skills-section";

    const heading = document.createElement("h3");
    heading.textContent = "Skills";
    section.appendChild(heading);

    const tagList = document.createElement("ul");
    tagList.className = "skill-tag-list";

    for (let i = 0; i < skillsList.length; i++) {
        const tag = buildSkillTag(skillsList[i]);
        tagList.appendChild(tag);
    }

    section.appendChild(tagList);
    return section;
}

function buildProjectCard(project) {
    const card = document.createElement("div");
    card.className = "project-card";

    const title = document.createElement("h4");
    title.textContent = project.title;
    card.appendChild(title);

    const description = document.createElement("p");
    description.textContent = project.description;
    card.appendChild(description);

    if (project.link) {
        const link = document.createElement("a");
        link.href = project.link;
        link.textContent = "View project";
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        card.appendChild(link);
    }

    return card;
}

function buildProjectsSection(projectsList) {
    const section = document.createElement("div");
    section.className = "projects-section";

    const heading = document.createElement("h3");
    heading.textContent = "Projects";
    section.appendChild(heading);

    for (let i = 0; i < projectsList.length; i++) {
        const projectCard = buildProjectCard(projectsList[i]);
        section.appendChild(projectCard);
    }

    return section;
}

function buildContactLinks(person) {
    const contactList = document.createElement("div");
    contactList.className = "contact-links";

    if (person.email) {
        const emailLink = document.createElement("a");
        emailLink.href = "mailto:" + person.email;
        emailLink.textContent = "Email";
        contactList.appendChild(emailLink);
    }

    if (person.github) {
        const githubLink = document.createElement("a");
        githubLink.href = person.github;
        githubLink.textContent = "GitHub";
        githubLink.target = "_blank";
        githubLink.rel = "noopener noreferrer";
        contactList.appendChild(githubLink);
    }

    if (person.linkedin) {
        const linkedinLink = document.createElement("a");
        linkedinLink.href = person.linkedin;
        linkedinLink.textContent = "LinkedIn";
        linkedinLink.target = "_blank";
        linkedinLink.rel = "noopener noreferrer";
        contactList.appendChild(linkedinLink);
    }

    return contactList;
}

function buildTeamMemberCard(person) {
    const card = document.createElement("section");
    card.className = "team-card";

    // --- top row: avatar circle + name/role/bio ------------------------
    const topRow = document.createElement("div");
    topRow.className = "team-card-top";

    const avatar = document.createElement("div");
    avatar.className = "avatar-circle";
    avatar.textContent = getInitials(person.name);
    topRow.appendChild(avatar);

    const introBlock = document.createElement("div");
    introBlock.className = "intro-block";

    const nameHeading = document.createElement("h2");
    nameHeading.textContent = person.name;
    introBlock.appendChild(nameHeading);

    const roleLine = document.createElement("p");
    roleLine.className = "role-line";
    roleLine.textContent = person.role;
    introBlock.appendChild(roleLine);

    const bioParagraph = document.createElement("p");
    bioParagraph.className = "bio-paragraph";
    bioParagraph.textContent = person.bio;
    introBlock.appendChild(bioParagraph);

    topRow.appendChild(introBlock);
    card.appendChild(topRow);

    // --- info chips: location / focus area ------------------------------
    const chipRow = document.createElement("div");
    chipRow.className = "chip-row";

    const locationChip = document.createElement("div");
    locationChip.className = "info-chip";
    locationChip.innerHTML = "<strong>Based in</strong><br>" + person.location;
    chipRow.appendChild(locationChip);

    const focusChip = document.createElement("div");
    focusChip.className = "info-chip";
    focusChip.innerHTML = "<strong>Focus area</strong><br>" + person.focusArea;
    chipRow.appendChild(focusChip);

    card.appendChild(chipRow);

    // --- skills and projects ---------------------------------------------
    card.appendChild(buildSkillsSection(person.skills));
    card.appendChild(buildProjectsSection(person.projects));

    // --- contact links -----------------------------------------------------
    card.appendChild(buildContactLinks(person));

    return card;
}

function renderTeamPage() {
    const container = document.getElementById("team-container");

    for (let i = 0; i < teamMembers.length; i++) {
        const memberCard = buildTeamMemberCard(teamMembers[i]);
        container.appendChild(memberCard);
    }
}

renderTeamPage();
