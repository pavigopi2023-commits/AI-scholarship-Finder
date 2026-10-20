/* =====================================================
   AI SCHOLARSHIP FINDER — SCRIPT.JS
   2-TIER AI RECOMMENDATION SYSTEM ENGINE & ADMIN MODULE
   - Deterministic Hard Eligibility Engine
   - Content-Based AI Feature Vector Recommender
   - Personalized AI Explanation Generator
   - Admin Scholarship Management Subsystem
   ===================================================== */

/* ---------- 1. BACKEND CONNECTION SETTINGS ---------- */
const API_BASE_URL = "https://ai-scholarship-finder-6omk.onrender.com";

/* ---------- 2. GLOBAL DASHBOARD & ADMIN STATE ---------- */
let currentStudent = null;
let allMatchedScholarships = [];
let currentAdminKey = "admin123";
let adminScholarships = [];

/* ---------- 3. GRAB DOM ELEMENTS ---------- */
const form = document.getElementById("scholarshipForm");
const resultsMessage = document.getElementById("resultsMessage");
const resultsGrid = document.getElementById("resultsGrid");
const resultsCount = document.getElementById("resultsCount");
const resultsControls = document.getElementById("resultsControls");
const resultsEmpty = document.getElementById("resultsEmpty");
const profileSummaryBar = document.getElementById("profileSummaryBar");
const profileSummaryChips = document.getElementById("profileSummaryChips");
const submitButton = form ? form.querySelector(".btn-submit") : null;

// Academic Score Type Dynamic Elements
const academicScoreTypeSelect = document.getElementById("academicScoreType");
const percentageBlock = document.getElementById("percentageBlock");
const cgpaBlock = document.getElementById("cgpaBlock");
const marksBlock = document.getElementById("marksBlock");

// Search, Filter & Sort Controls
const searchBox = document.getElementById("searchBox");
const filterState = document.getElementById("filterState");
const filterCategory = document.getElementById("filterCategory");
const filterEducation = document.getElementById("filterEducation");
const filterEligibility = document.getElementById("filterEligibility");
const sortBy = document.getElementById("sortBy");
const resetFiltersBtn = document.getElementById("resetFiltersBtn");

// Admin Portal DOM Elements
const toggleAdminBtn = document.getElementById("toggleAdminBtn");
const adminSection = document.getElementById("adminSection");
const adminAuthBox = document.getElementById("adminAuthBox");
const adminDashboard = document.getElementById("adminDashboard");
const adminKeyInput = document.getElementById("adminKeyInput");
const adminLoginBtn = document.getElementById("adminLoginBtn");
const adminAuthError = document.getElementById("adminAuthError");
const adminTableBody = document.getElementById("adminTableBody");
const adminMessage = document.getElementById("adminMessage");
const addNewScholarshipBtn = document.getElementById("addNewScholarshipBtn");
const scholarshipModal = document.getElementById("scholarshipModal");
const closeModalBtn = document.getElementById("closeModalBtn");
const cancelModalBtn = document.getElementById("cancelModalBtn");
const adminScholarshipForm = document.getElementById("adminScholarshipForm");
const modalTitle = document.getElementById("modalTitle");

/* ---------- 4. DYNAMIC ACADEMIC SCORE INPUT SWITCHING ---------- */
if (academicScoreTypeSelect) {
  academicScoreTypeSelect.addEventListener("change", function () {
    const selectedType = academicScoreTypeSelect.value;
    
    if (percentageBlock) percentageBlock.style.display = "none";
    if (cgpaBlock) cgpaBlock.style.display = "none";
    if (marksBlock) marksBlock.style.display = "none";

    if (selectedType === "Percentage" && percentageBlock) {
      percentageBlock.style.display = "block";
    } else if (selectedType === "CGPA" && cgpaBlock) {
      cgpaBlock.style.display = "block";
    } else if (selectedType === "Marks" && marksBlock) {
      marksBlock.style.display = "block";
    }
  });
}

/* ---------- 5. STUDENT FORM SUBMIT HANDLER ---------- */
if (form) {
  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const scoreType = academicScoreTypeSelect ? academicScoreTypeSelect.value : "Percentage";

    // Read form input values
    const studentData = {
      fullName: document.getElementById("fullName").value.trim(),
      age: document.getElementById("age") ? document.getElementById("age").value.trim() : "",
      gender: document.getElementById("gender") ? document.getElementById("gender").value : "",
      state: document.getElementById("state") ? document.getElementById("state").value : "",
      educationLevel: document.getElementById("educationLevel").value,
      course: document.getElementById("course") ? document.getElementById("course").value : "",
      academicScoreType: scoreType,
      marks: document.getElementById("marks") ? document.getElementById("marks").value.trim() : "",
      cgpa: document.getElementById("cgpa") ? document.getElementById("cgpa").value.trim() : "",
      obtainedMarks: document.getElementById("obtainedMarks") ? document.getElementById("obtainedMarks").value.trim() : "",
      maxMarks: document.getElementById("maxMarks") ? document.getElementById("maxMarks").value.trim() : "",
      income: document.getElementById("income").value.trim(),
      category: document.getElementById("category").value,
    };

    // Validate form inputs
    const isValid = validateForm(studentData);
    if (!isValid) {
      return;
    }

    // Process dynamic academic scores
    let academicScore = 0;
    let computedMarks = 0;
    let obtainedMarksNum = null;
    let maxMarksNum = null;

    if (scoreType === "Percentage") {
      academicScore = parseFloat(studentData.marks);
      computedMarks = academicScore;
    } else if (scoreType === "CGPA") {
      academicScore = parseFloat(studentData.cgpa);
      computedMarks = academicScore * 10.0; // Proportional fallback for legacy representation
    } else if (scoreType === "Marks") {
      obtainedMarksNum = parseFloat(studentData.obtainedMarks);
      maxMarksNum = parseFloat(studentData.maxMarks);
      academicScore = obtainedMarksNum;
      computedMarks = (obtainedMarksNum / maxMarksNum) * 100.0;
    }

    // Build clean student profile object
    const student = {
      fullName: studentData.fullName,
      name: studentData.fullName,
      age: studentData.age !== "" ? parseInt(studentData.age, 10) : null,
      gender: studentData.gender,
      educationLevel: studentData.educationLevel,
      education: studentData.educationLevel,
      course: studentData.course,
      academic_score_type: scoreType,
      academic_score: academicScore,
      obtained_marks: obtainedMarksNum,
      max_marks: maxMarksNum,
      marks: computedMarks,
      income: parseFloat(studentData.income),
      family_income: parseFloat(studentData.income),
      state: studentData.state,
      category: studentData.category,
    };

    currentStudent = student;

    // Show loading state
    setLoadingState(true);
    resultsMessage.textContent = "Running 2-Tier AI Recommendation Engine...";
    resultsMessage.classList.remove("results-message--error");
    resultsGrid.innerHTML = "";
    resultsEmpty.style.display = "none";

    try {
      // Step 1: Save student profile to Flask backend
      await saveStudentToBackend(student);

      // Step 2: Fetch recommendations from Flask AI Recommendation API
      const recData = await fetchRecommendationsFromBackend(student);

      allMatchedScholarships = recData.map(function (item) {
        // Formulate reason items for checklist
        const reasonsList = [];
        (item.passed_criteria || []).forEach(function (passed) {
          reasonsList.push({ text: passed, passed: true, type: "passed" });
        });
        (item.failed_criteria || []).forEach(function (failed) {
          reasonsList.push({ text: failed, passed: false, type: "failed" });
        });
        (item.not_applicable_criteria || []).forEach(function (na) {
          reasonsList.push({ text: na, passed: true, type: "not_applicable" });
        });

        return Object.assign({}, item, {
          matchPercent: item.ai_match_score || item.matchPercent || 0,
          reasons: reasonsList
        });
      });

      resultsMessage.textContent = "";
      resultsControls.style.display = "flex";
      profileSummaryBar.style.display = "flex";

      // Step 3: Render Profile Context & Dashboard Results
      renderProfileSummary(student);
      applyFiltersAndRender();

      // Smooth scroll down to dashboard results
      document.getElementById("scholarships").scrollIntoView({ behavior: "smooth" });

    } catch (error) {
      showConnectionError(error);
    } finally {
      setLoadingState(false);
    }
  });
}

/* ---------- 6. FILTER & SORT DASHBOARD LOGIC ---------- */
function applyFiltersAndRender() {
  if (!allMatchedScholarships || allMatchedScholarships.length === 0) {
    return;
  }

  const query = searchBox ? searchBox.value.trim().toLowerCase() : "";
  const stateVal = filterState ? filterState.value : "all";
  const catVal = filterCategory ? filterCategory.value : "all";
  const eduVal = filterEducation ? filterEducation.value : "all";
  const eligVal = filterEligibility ? filterEligibility.value : "all";
  const sortVal = sortBy ? sortBy.value : "match";

  // Filter dataset
  let filtered = allMatchedScholarships.filter(function (item) {
    if (query !== "") {
      const nameMatch = (item.name || "").toLowerCase().includes(query);
      const providerMatch = (item.provider || "").toLowerCase().includes(query);
      const descMatch = (item.description || "").toLowerCase().includes(query);
      const stateMatch = (item.state || "").toLowerCase().includes(query);
      const catMatch = (item.category || "").toLowerCase().includes(query);

      if (!nameMatch && !providerMatch && !descMatch && !stateMatch && !catMatch) {
        return false;
      }
    }

    if (stateVal !== "all") {
      const itemState = (item.state || "").trim().toLowerCase();
      if (itemState !== "all" && itemState !== stateVal.trim().toLowerCase()) {
        return false;
      }
    }

    if (catVal !== "all") {
      const itemCat = (item.category || "").trim().toLowerCase();
      if (itemCat !== "all" && itemCat !== catVal.trim().toLowerCase()) {
        return false;
      }
    }

    if (eduVal !== "all") {
      const itemEdu = (item.education || "").trim().toLowerCase();
      if (itemEdu !== "all" && itemEdu !== eduVal.trim().toLowerCase()) {
        return false;
      }
    }

    if (eligVal === "eligible" && !item.eligible) {
      return false;
    }
    if (eligVal === "partial" && item.eligible) {
      return false;
    }

    return true;
  });

  // Sort dataset
  filtered.sort(function (a, b) {
    if (sortVal === "amount") {
      return (b.amount || 0) - (a.amount || 0);
    } else if (sortVal === "deadline") {
      if (!a.deadline) return 1;
      if (!b.deadline) return -1;
      return a.deadline.localeCompare(b.deadline);
    } else {
      // Default: Best AI Match
      return (b.eligible ? 1 : 0) - (a.eligible ? 1 : 0) || (b.matchPercent - a.matchPercent);
    }
  });

  if (resultsCount) {
    resultsCount.textContent = filtered.length;
  }

  if (filtered.length === 0) {
    resultsGrid.style.display = "none";
    resultsEmpty.style.display = "flex";
  } else {
    resultsEmpty.style.display = "none";
    resultsGrid.style.display = "grid";
    renderScholarshipCards(filtered);
  }
}

// Event Listeners for Filters, Search & Reset Controls
if (searchBox) searchBox.addEventListener("input", applyFiltersAndRender);
if (filterState) filterState.addEventListener("change", applyFiltersAndRender);
if (filterCategory) filterCategory.addEventListener("change", applyFiltersAndRender);
if (filterEducation) filterEducation.addEventListener("change", applyFiltersAndRender);
if (filterEligibility) filterEligibility.addEventListener("change", applyFiltersAndRender);
if (sortBy) sortBy.addEventListener("change", applyFiltersAndRender);

if (resetFiltersBtn) {
  resetFiltersBtn.addEventListener("click", function () {
    if (searchBox) searchBox.value = "";
    if (filterState) filterState.value = "all";
    if (filterCategory) filterCategory.value = "all";
    if (filterEducation) filterEducation.value = "all";
    if (filterEligibility) filterEligibility.value = "all";
    if (sortBy) sortBy.value = "match";
    applyFiltersAndRender();
  });
}

/* ---------- 7. RENDER PROFILE SUMMARY BAR ---------- */
function renderProfileSummary(student) {
  if (!profileSummaryChips) return;
  profileSummaryChips.innerHTML = "";

  let acadLabel = `📊 ${student.marks}% Marks`;
  if (student.academic_score_type === "CGPA") {
    acadLabel = `📊 ${student.academic_score} / 10 CGPA`;
  } else if (student.academic_score_type === "Marks" && student.obtained_marks && student.max_marks) {
    acadLabel = `📊 ${student.obtained_marks}/${student.max_marks} Marks`;
  }

  const chips = [
    { label: "🎓 " + student.educationLevel },
    { label: "📍 " + student.state },
    { label: acadLabel },
    { label: "💰 ₹" + Number(student.income).toLocaleString("en-IN") },
    { label: "🏷️ " + student.category }
  ];

  if (student.age) {
    chips.push({ label: "🎂 Age: " + student.age });
  }

  if (student.course) {
    chips.splice(1, 0, { label: "📚 " + student.course });
  }

  chips.forEach(function (chip) {
    const span = document.createElement("span");
    span.className = "profile-summary-chip";
    span.textContent = chip.label;
    profileSummaryChips.appendChild(span);
  });
}

/* ---------- 8. BACKEND COMMUNICATION ---------- */
async function saveStudentToBackend(student) {
  let response;
  try {
    response = await fetch(API_BASE_URL + "/students", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: student.fullName,
        fullName: student.fullName,
        education: student.educationLevel,
        educationLevel: student.educationLevel,
        academic_score_type: student.academic_score_type,
        academic_score: student.academic_score,
        obtained_marks: student.obtained_marks,
        max_marks: student.max_marks,
        marks: student.marks,
        family_income: student.income,
        income: student.income,
        state: student.state,
        category: student.category,
        age: student.age,
        gender: student.gender,
        course: student.course
      }),
    });
  } catch (networkError) {
    throw new Error("SERVER_UNREACHABLE");
  }

  const data = await response.json();
  if (!response.ok || !data.success) {
    throw new Error(data.message || "Unable to save student profile.");
  }
  return data;
}

async function fetchRecommendationsFromBackend(student) {
  let response;
  try {
    response = await fetch(API_BASE_URL + "/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(student)
    });
  } catch (networkError) {
    throw new Error("SERVER_UNREACHABLE");
  }

  if (!response.ok) {
    throw new Error("Unable to load AI scholarship recommendations.");
  }

  const data = await response.json();
  return data.recommendations || [];
}

function showConnectionError(error) {
  if (error.message === "SERVER_UNREACHABLE") {
    resultsMessage.textContent =
      "We couldn't connect to the scholarship AI recommendation service. Please make sure the Flask backend is running on https://ai-scholarship-finder-6omk.onrender.com/";
  } else {
    resultsMessage.textContent = error.message || "Something went wrong. Please try again.";
  }
  resultsMessage.classList.add("results-message--error");
}

function setLoadingState(isLoading) {
  if (submitButton) {
    submitButton.disabled = isLoading;
    submitButton.textContent = isLoading ? "Running AI Engine..." : "Find My Scholarships →";
  }
}

/* ---------- 9. FORM VALIDATION ---------- */
function validateForm(data) {
  let isValid = true;
  clearErrors();
  if (resultsMessage) resultsMessage.classList.remove("results-message--error");

  if (!data.fullName || data.fullName.trim() === "") {
    showError("fullName", "Please enter your full name.");
    isValid = false;
  }

  // Age is OPTIONAL
  if (data.age !== "" && (isNaN(data.age) || Number(data.age) <= 0 || Number(data.age) > 100)) {
    showError("age", "Please enter a valid age.");
    isValid = false;
  }

  if (!data.gender) {
    showError("gender", "Please select your gender.");
    isValid = false;
  }

  if (!data.state) {
    showError("state", "Please select your state.");
    isValid = false;
  }

  if (!data.educationLevel) {
    showError("educationLevel", "Please select your education level.");
    isValid = false;
  }

  if (!data.course) {
    showError("course", "Please select your course / field of study.");
    isValid = false;
  }

  // Dynamic Academic Score Validation
  if (data.academicScoreType === "Percentage") {
    if (data.marks === "") {
      showError("marks", "Please enter your academic percentage.");
      isValid = false;
    } else if (isNaN(data.marks) || Number(data.marks) < 0 || Number(data.marks) > 100) {
      showError("marks", "Please enter your percentage between 0 and 100.");
      isValid = false;
    }
  } else if (data.academicScoreType === "CGPA") {
    if (data.cgpa === "") {
      showError("cgpa", "Please enter your CGPA score.");
      isValid = false;
    } else if (isNaN(data.cgpa) || Number(data.cgpa) < 0 || Number(data.cgpa) > 10) {
      showError("cgpa", "Please enter your CGPA score between 0 and 10.0.");
      isValid = false;
    }
  } else if (data.academicScoreType === "Marks") {
    if (data.obtainedMarks === "" || isNaN(data.obtainedMarks) || Number(data.obtainedMarks) < 0) {
      showError("obtainedMarks", "Please enter valid obtained marks.");
      isValid = false;
    }
    if (data.maxMarks === "" || isNaN(data.maxMarks) || Number(data.maxMarks) <= 0) {
      showError("maxMarks", "Please enter valid maximum marks (> 0).");
      isValid = false;
    }
    if (Number(data.obtainedMarks) > Number(data.maxMarks)) {
      showError("obtainedMarks", "Obtained marks cannot exceed maximum marks.");
      isValid = false;
    }
  }

  if (data.income === "") {
    showError("income", "Please enter your family income.");
    isValid = false;
  } else if (isNaN(data.income) || Number(data.income) < 0) {
    showError("income", "Family income must be a valid non-negative number.");
    isValid = false;
  }

  if (!data.category) {
    showError("category", "Please select your category.");
    isValid = false;
  }

  return isValid;
}

function showError(fieldId, message) {
  const field = document.getElementById(fieldId);
  const errorEl = document.getElementById("error-" + fieldId);
  if (field) field.classList.add("input-error");
  if (errorEl) errorEl.textContent = message;
}

function clearErrors() {
  const errorEls = document.querySelectorAll(".error-message");
  errorEls.forEach(function (el) { el.textContent = ""; });
  const fields = document.querySelectorAll(".input-error");
  fields.forEach(function (field) { field.classList.remove("input-error"); });
}

/* ---------- 10. RENDER SCHOLARSHIP CARDS DASHBOARD ---------- */
function formatAmount(amount) {
  if (amount === null || amount === undefined || amount === "" || amount === 0) {
    return "Tuition Fee Waiver / Support";
  }
  return "₹" + Number(amount).toLocaleString("en-IN");
}

function formatDate(dateStr) {
  if (!dateStr) return "Rolling Deadline";
  try {
    const parts = dateStr.split("-");
    if (parts.length === 3) {
      return parts[2] + "/" + parts[1] + "/" + parts[0];
    }
  } catch (e) {}
  return dateStr;
}

function renderScholarshipCards(scholarships) {
  if (!resultsGrid) return;
  resultsGrid.innerHTML = "";

  let highestScore = 0;
  scholarships.forEach(function (s) {
    if (s.eligible && s.matchPercent > highestScore) {
      highestScore = s.matchPercent;
    }
  });

  scholarships.forEach(function (scholarship, index) {
    const card = document.createElement("article");
    const isBestMatch = (index === 0 && scholarship.eligible && scholarship.matchPercent === highestScore);
    
    card.className = "scholarship-card" + (isBestMatch ? " scholarship-card--best-match" : "");

    let badgeClass = "match-badge--low";
    if (scholarship.matchPercent >= 75) {
      badgeClass = "match-badge--high";
    } else if (scholarship.matchPercent >= 45) {
      badgeClass = "match-badge--medium";
    }

    const eligPillHtml = scholarship.eligible
      ? '<span class="eligibility-pill eligibility-pill--eligible">✓ Eligible</span>'
      : '<span class="eligibility-pill eligibility-pill--partial">⚠ Ineligible</span>';

    const bestMatchRibbon = isBestMatch
      ? '<div class="best-match-badge">🤖 AI Best Match</div>'
      : '';

    let reasonsHtml = "";
    (scholarship.reasons || []).forEach(function (reason) {
      let itemClass = "match-reasons__item--pass";
      let icon = "✓";
      if (reason.type === "failed" || !reason.passed) {
        itemClass = "match-reasons__item--fail";
        icon = "✗";
      } else if (reason.type === "not_applicable") {
        itemClass = "match-reasons__item--na";
        icon = "ℹ";
      }
      reasonsHtml +=
        '<li class="match-reasons__item ' + itemClass + '">' +
          '<span class="match-reasons__icon">' + icon + "</span>" +
          "<span>" + reason.text + "</span>" +
        "</li>";
    });

    let aiExplanationHtml = "";
    if (scholarship.ai_explanation) {
      aiExplanationHtml =
        '<div class="ai-explanation-box" style="background: #eff6ff; border-left: 3px solid #2563eb; padding: 10px 14px; border-radius: 6px; font-size: 0.85rem; color: #1e3a8a; margin-top: 8px;">' +
          '<strong>🤖 AI Recommendation:</strong> ' + scholarship.ai_explanation +
        '</div>';
    }

    let applyBtnHtml = "";
    if (scholarship.application_url && scholarship.application_url.trim() !== "") {
      applyBtnHtml =
        '<a href="' + scholarship.application_url + '" target="_blank" rel="noopener noreferrer" class="btn btn--primary btn-apply">' +
          'Apply Now &rarr;' +
        '</a>';
    } else {
      applyBtnHtml = '<div class="btn-apply--disabled">Portal Details via Provider</div>';
    }

    // Format Academic Requirement String
    let acadReqStr = "Not specified";
    const reqType = scholarship.academic_requirement_type || "Percentage";
    const reqScore = scholarship.minimum_academic_score || scholarship.minimum_marks;
    if (reqType === "CGPA" && reqScore) {
      acadReqStr = `Minimum CGPA: ${reqScore}`;
    } else if (reqType === "Percentage" && reqScore) {
      acadReqStr = `Minimum Percentage: ${reqScore}%`;
    } else if (reqType === "Marks" && reqScore) {
      acadReqStr = `Minimum Marks: ${reqScore}`;
    } else if (reqType === "None" || !reqScore) {
      acadReqStr = "Academic: Open / Not specified";
    }

    // Format Age Limit String
    let ageStr = "None";
    if (scholarship.age_limit) {
      ageStr = `≤ ${scholarship.age_limit} yrs`;
    }

    card.innerHTML =
      bestMatchRibbon +
      '<div class="scholarship-card__header">' +
        '<div>' +
          '<h3 class="scholarship-card__name">' + scholarship.name + "</h3>" +
          '<div class="scholarship-card__provider">' + scholarship.provider + "</div>" +
        "</div>" +
        '<div class="scholarship-card__badges">' +
          '<span class="match-badge ' + badgeClass + '">🤖 ' + scholarship.matchPercent + "% AI Match</span>" +
          eligPillHtml +
        "</div>" +
        "</div>" +
      '<div class="scholarship-card__amount">' + formatAmount(scholarship.amount) + "</div>" +
      '<p class="scholarship-card__description">' + (scholarship.description || "") + "</p>" +
      aiExplanationHtml +
      '<div class="scholarship-card__meta-grid" style="margin-top: 12px;">' +
        '<div class="meta-item"><span class="meta-item__label">Education</span><span class="meta-item__value">' + (scholarship.education || "All") + '</span></div>' +
        '<div class="meta-item"><span class="meta-item__label">Course</span><span class="meta-item__value">' + (scholarship.course || "All") + '</span></div>' +
        '<div class="meta-item"><span class="meta-item__label">State</span><span class="meta-item__value">' + (scholarship.state || "All States") + '</span></div>' +
        '<div class="meta-item"><span class="meta-item__label">Category</span><span class="meta-item__value">' + (scholarship.category || "All") + '</span></div>' +
        '<div class="meta-item"><span class="meta-item__label">Academics</span><span class="meta-item__value">' + acadReqStr + '</span></div>' +
        '<div class="meta-item"><span class="meta-item__label">Income Ceiling</span><span class="meta-item__value">' + (scholarship.maximum_income ? "≤ " + formatAmount(scholarship.maximum_income) : "No Limit") + '</span></div>' +
        '<div class="meta-item"><span class="meta-item__label">Age Limit</span><span class="meta-item__value">' + ageStr + '</span></div>' +
        '<div class="meta-item"><span class="meta-item__label">Deadline</span><span class="meta-item__value">' + formatDate(scholarship.deadline) + '</span></div>' +
      "</div>" +
      '<div class="match-reasons">' +
        '<div class="match-reasons__title">Why this matches you:</div>' +
        '<ul class="match-reasons__list">' + reasonsHtml + "</ul>" +
      "</div>" +
      applyBtnHtml;

    resultsGrid.appendChild(card);
  });
}

/* ---------- 11. ADMIN MANAGEMENT SUBSYSTEM ---------- */

if (toggleAdminBtn) {
  toggleAdminBtn.addEventListener("click", function (e) {
    e.preventDefault();
    if (adminSection.style.display === "none") {
      adminSection.style.display = "block";
      adminSection.scrollIntoView({ behavior: "smooth" });
    } else {
      adminSection.style.display = "none";
    }
  });
}

if (adminLoginBtn) {
  adminLoginBtn.addEventListener("click", function () {
    const key = adminKeyInput.value.trim();
    if (!key) {
      adminAuthError.textContent = "Please enter Admin Key.";
      adminAuthError.style.display = "block";
      return;
    }

    currentAdminKey = key;
    loadAdminDashboard();
  });
}

async function loadAdminDashboard() {
  try {
    adminAuthError.style.display = "none";
    adminMessage.textContent = "Loading database scholarship listings...";
    
    const response = await fetch(API_BASE_URL + "/admin/scholarships", {
      headers: { "X-Admin-Key": currentAdminKey }
    });

    const data = await response.json();
    if (!response.ok || !data.success) {
      adminAuthError.textContent = data.message || "Invalid Admin Secret Key.";
      adminAuthError.style.display = "block";
      return;
    }

    adminAuthBox.style.display = "none";
    adminDashboard.style.display = "block";
    adminMessage.textContent = "";
    adminScholarships = data.scholarships || [];
    renderAdminTable(adminScholarships);
  } catch (err) {
    adminAuthError.textContent = "Unable to connect to Flask backend.";
    adminAuthError.style.display = "block";
  }
}

function renderAdminTable(scholarships) {
  if (!adminTableBody) return;
  adminTableBody.innerHTML = "";

  scholarships.forEach(function (sch) {
    const tr = document.createElement("tr");
    tr.style.borderBottom = "1px solid #f1f5f9";

    const reqStr = (sch.academic_requirement_type || "Percentage") + ": " + (sch.minimum_academic_score || sch.minimum_marks || "Open");
    const incStr = sch.maximum_income ? "≤ ₹" + Number(sch.maximum_income).toLocaleString("en-IN") : "Open";

    tr.innerHTML =
      '<td style="padding: 12px 16px; font-weight: 600;">' + sch.id + '</td>' +
      '<td style="padding: 12px 16px; font-weight: 600; color: #1e293b;">' + sch.name + '</td>' +
      '<td style="padding: 12px 16px; color: #64748b;">' + sch.provider + '</td>' +
      '<td style="padding: 12px 16px; color: #059669; font-weight: 600;">' + formatAmount(sch.amount) + '</td>' +
      '<td style="padding: 12px 16px;">' + reqStr + '</td>' +
      '<td style="padding: 12px 16px;">' + incStr + '</td>' +
      '<td style="padding: 12px 16px;">' + (sch.state || "All") + '</td>' +
      '<td style="padding: 12px 16px; display: flex; gap: 6px;">' +
        '<button class="btn btn--secondary btn--sm btn-edit-sch" data-id="' + sch.id + '" style="padding: 4px 8px; font-size: 0.78rem;">Edit</button>' +
        '<button class="btn btn--secondary btn--sm btn-del-sch" data-id="' + sch.id + '" style="padding: 4px 8px; font-size: 0.78rem; color: #dc2626; border-color: #fca5a5;">Delete</button>' +
      '</td>';

    adminTableBody.appendChild(tr);
  });

  // Attach Edit and Delete Listeners
  document.querySelectorAll(".btn-edit-sch").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const id = parseInt(btn.getAttribute("data-id"), 10);
      openScholarshipModal(id);
    });
  });

  document.querySelectorAll(".btn-del-sch").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const id = parseInt(btn.getAttribute("data-id"), 10);
      deleteScholarshipRecord(id);
    });
  });
}

if (addNewScholarshipBtn) {
  addNewScholarshipBtn.addEventListener("click", function () {
    openScholarshipModal(null);
  });
}

if (closeModalBtn) closeModalBtn.addEventListener("click", closeModal);
if (cancelModalBtn) cancelModalBtn.addEventListener("click", closeModal);

function closeModal() {
  if (scholarshipModal) scholarshipModal.style.display = "none";
}

function openScholarshipModal(schId) {
  adminScholarshipForm.reset();
  document.getElementById("adminSchId").value = "";

  if (schId) {
    modalTitle.textContent = "Edit Scholarship Record #" + schId;
    const sch = adminScholarships.find(s => s.id === schId);
    if (sch) {
      document.getElementById("adminSchId").value = sch.id;
      document.getElementById("adminSchName").value = sch.name || "";
      document.getElementById("adminSchProvider").value = sch.provider || "";
      document.getElementById("adminSchDesc").value = sch.description || "";
      document.getElementById("adminSchAmount").value = sch.amount || "";
      document.getElementById("adminSchIncome").value = sch.maximum_income || "";
      document.getElementById("adminSchScoreType").value = sch.academic_requirement_type || "Percentage";
      document.getElementById("adminSchMinScore").value = sch.minimum_academic_score || sch.minimum_marks || "";
      document.getElementById("adminSchEducation").value = sch.education || "Undergraduate";
      document.getElementById("adminSchState").value = sch.state || "All";
      document.getElementById("adminSchCategory").value = sch.category || "All";
      document.getElementById("adminSchCourse").value = sch.course || "All";
      document.getElementById("adminSchGender").value = sch.gender || "All";
      document.getElementById("adminSchAge").value = sch.age_limit || "";
      document.getElementById("adminSchDeadline").value = sch.deadline || "";
      document.getElementById("adminSchUrl").value = sch.application_url || "";
    }
  } else {
    modalTitle.textContent = "Add New Scholarship";
  }

  scholarshipModal.style.display = "flex";
}

if (adminScholarshipForm) {
  adminScholarshipForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    const schId = document.getElementById("adminSchId").value;
    const payload = {
      name: document.getElementById("adminSchName").value.trim(),
      provider: document.getElementById("adminSchProvider").value.trim(),
      description: document.getElementById("adminSchDesc").value.trim(),
      amount: document.getElementById("adminSchAmount").value ? parseFloat(document.getElementById("adminSchAmount").value) : 0,
      maximum_income: document.getElementById("adminSchIncome").value ? parseFloat(document.getElementById("adminSchIncome").value) : null,
      academic_requirement_type: document.getElementById("adminSchScoreType").value,
      minimum_academic_score: document.getElementById("adminSchMinScore").value ? parseFloat(document.getElementById("adminSchMinScore").value) : null,
      minimum_marks: document.getElementById("adminSchMinScore").value ? parseFloat(document.getElementById("adminSchMinScore").value) : 0,
      education: document.getElementById("adminSchEducation").value,
      state: document.getElementById("adminSchState").value,
      category: document.getElementById("adminSchCategory").value,
      course: document.getElementById("adminSchCourse").value,
      gender: document.getElementById("adminSchGender").value,
      age_limit: document.getElementById("adminSchAge").value ? parseInt(document.getElementById("adminSchAge").value, 10) : null,
      deadline: document.getElementById("adminSchDeadline").value,
      application_url: document.getElementById("adminSchUrl").value.trim()
    };

    try {
      let url = API_BASE_URL + "/admin/scholarships";
      let method = "POST";
      if (schId) {
        url = API_BASE_URL + "/admin/scholarships/" + schId;
        method = "PUT";
      }

      const res = await fetch(url, {
        method: method,
        headers: {
          "Content-Type": "application/json",
          "X-Admin-Key": currentAdminKey
        },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        alert("Error: " + (data.message || "Operation failed."));
        return;
      }

      closeModal();
      loadAdminDashboard();
    } catch (err) {
      alert("Network error: Unable to update scholarship.");
    }
  });
}

async function deleteScholarshipRecord(schId) {
  if (!confirm("Are you sure you want to delete scholarship #" + schId + "?")) {
    return;
  }

  try {
    const res = await fetch(API_BASE_URL + "/admin/scholarships/" + schId, {
      method: "DELETE",
      headers: { "X-Admin-Key": currentAdminKey }
    });
    const data = await res.json();
    if (!res.ok || !data.success) {
      alert("Error: " + (data.message || "Failed to delete scholarship."));
      return;
    }

    loadAdminDashboard();
  } catch (err) {
    alert("Network error: Unable to delete scholarship.");
  }
}