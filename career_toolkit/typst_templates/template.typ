//=====================
// BOX STYLE TEMPLATE
//=====================

/* NOTE: 
To generate a job description for a specific job, attach the custom_job_schema.json file and use the following prompt- 

"using the attached job-description schema (https://jsonresume.org/job-description-schema) -- Generate a json job-description based on the following content. For missing content, you should identify assume keywords and other key content to help fit the schema.

:" 

*/

#let show_unmapped_section = false //show unmapped requirements section
#let show_work_summaries = true //show work summaries in the experience section

// ===========================
// GLOBAL STYLES 
// ===========================

// --- Fonts ---
#let font_family_default = "Roboto"
#let font_family_secondary = "Lato" // Mapped for titles and headers

// --- Font Sizes ---
#let font_size_main_title = 26pt
#let font_size_main_subtitle = 20pt
#let font_size_section_title = 12pt
#let font_size_large = 12pt
#let font_size_default = 11pt
#let font_size_medium = 10pt
#let font_size_small = 9pt // General small text, like descriptions

// --- Colors ---
#let color_text_default = luma(0)
#let color_text_alternate = luma(80) // For less important text like dates
#let color_accent = rgb("#3D3B8E")      
#let color_link = color_accent
#let color_line = rgb("6883BA")
#let color_UNMAPPED = rgb("#ff0000")      // Red for unmapped requirements

// --- Layout & Borders ---
#let page_margin_val = 0cm
#let line_stroke = 1.5pt
#let space_xlarge = 1.5em
#let space_large = 0.5em
#let space_medium = 0.4em
#let space_small = 0.2em

// ===========================
// MAIN DOCUMENT SETUP 
// ===========================

// --- Setup Resume Page ---
#let setup_page(doc_title: "Resume", doc_author: "Default Author", body_content) = {
  set document(title: doc_title, author: doc_author)
  set page(
    margin: (top: page_margin_val, bottom: page_margin_val, left: page_margin_val, right: page_margin_val)
  )
  set text(font: font_family_default, size: font_size_default, fill: color_text_default)
  body_content
}

// --- Section Break Style --- 
#let section_title_style(title_text) = {
  smallcaps(text(weight: "bold", size: font_size_section_title, font: font_family_secondary, color_accent)[#title_text])
  place(dy:-11pt, line(length: 100%, stroke: line_stroke + color_line))
  v(space_small)
}


// ===========================
// HELPER FUNCTIONS 
// ===========================

// --- Format Date ---
#let format_date_month_year(date_str) = {
  if date_str == none or date_str == "" { return "" }
  if date_str == "Present" { return "Present" }
  let parts = date_str.split("-")
  if parts.len() < 2 { return "" }
  let year = parts.at(0)
  let month_num_str = parts.at(1)
  let month_names = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
  let month_index = int(month_num_str) - 1
  if month_index < 0 or month_index >= month_names.len() { return "" }
  let month_name = month_names.at(month_index)
  return month_name + " " + year
}

// --- Format Date Range or Year Only ---
#let format_date_range(start_date, end_date, format: "range") = {
  
  // If format is "year", only show the end year
  if format == "year" {
    if end_date == "Present" or end_date == "present" {
      return "Present"
    } else if end_date != none and end_date != "" {
      // Assumes date format is "YYYY-MM"
      return end_date.split("-").at(0)
    } else {
      return ""
    }
  }

  // Default "range" behavior
  let formatted_start = format_date_month_year(start_date)
  let formatted_end = if end_date == "Present" or end_date == "present" {
    "Present"
  } else if end_date != none and end_date != "" {
    format_date_month_year(end_date)
  } else {
    ""
  }

  if formatted_start != "" and formatted_end != "" {
    formatted_start + " - " + formatted_end
  } else if formatted_start != "" {
    formatted_start
  } else {
    ""
  }
}

// --- Icon Helper Function ---
#let icon(name, shift: 1.5pt) = {
  box(
    baseline: shift,
    height: font_size_medium,
    image("icons/" + name + ".svg")
  )
  h(6pt)
}

/// --- Recursive JSON to String Converter ---
#let json_to_string(data) = {
  // Helper function to traverse the data and collect strings
  let traverse(item) = {
    if type(item) == dictionary {
      let result = ()
      for (key, value) in item {
        result = result + traverse(value)
      }
      result
    } else if type(item) == array {
      let result = ()
      for sub_item in item {
        result = result + traverse(sub_item)
      }
      result
    } else if type(item) == str {
      (item,)
    } else {
      ()
    }
  }

  traverse(data).join(" ")
}

// --- Levenshtein Distance for Fuzzy Matching ----
#let levenshtein_distance(a, b) = {
  // Ensure 'a' is the shorter string to optimize space
  if a.len() > b.len() {
    (a, b) = (b, a)
  }

  let (len_a, len_b) = (a.len(), b.len())
  if len_b == 0 { return len_a }

  let previous_row = range(len_a + 1)

  for i in range(len_b) {
    let current_row = (i + 1,)
    for j in range(len_a) {
      let insertions = previous_row.at(j + 1) + 1
      let deletions = current_row.at(j) + 1
      let substitutions = previous_row.at(j) + (if a.at(j) != b.at(i) { 1 } else { 0 })
      current_row.push(calc.min(insertions, deletions, substitutions))
    }
    previous_row = current_row
  }
  
  return previous_row.last()
}

// --- Unmapped Requirements Section ---
#let show_unmapped_requirements(resume_data, job_data) = {
  // 1. Check feature flag.
  if not show_unmapped_section {
    return
  }

  // 2. Gracefully handle missing or malformed data.
  if resume_data == none or job_data == none or "skills" not in job_data or type(job_data.skills) != array {
    return
  }

  // 3. Convert resume JSON to a single lowercase string for searching.
  let resume_text_corpus = lower(json_to_string(resume_data))
  let resume_words = resume_text_corpus
    .replace(",", "").replace(".", "").replace("(", "").replace(")", "")
    .split(" ").filter(w => w != "").dedup()

  // 4. Extract all skill strings from the structured job data.
  let required_skills_list = ()
  for skill_obj in job_data.skills {
    if "name" in skill_obj and skill_obj.name != none {
      required_skills_list.push(skill_obj.name)
    }
    if "keywords" in skill_obj and type(skill_obj.keywords) == array {
      for keyword in skill_obj.keywords {
        required_skills_list.push(keyword)
      }
    }
  }
  let required_skills = required_skills_list.dedup()

  // 5. Find unmapped skills with robust logic for all word lengths.
  let unmapped = ()
  for req_skill in required_skills {
    let req_lower = lower(req_skill)
    
    // Clean the requirement skill to match how the resume corpus is cleaned. E.G.,This handles cases like "AI (Artificial Intelligence)".
    let clean_req_lower = req_lower.replace("(", "").replace(")", "")

    let is_mapped = {
      // Stage 1: Direct Substring Search on the cleaned skill phrase.
      if resume_text_corpus.contains(clean_req_lower) {
        true
      } else {
      // Stage 2: Fuzzy Word-by-Word Match with improved logic.
        let req_words = clean_req_lower.split(" ").filter(w => w.len() > 0)

        req_words.all(req_word =>
          resume_words.any(res_word => {
            let distance = levenshtein_distance(req_word, res_word)

            // Improved tolerance for acronyms (3 letters or less), require an exact match (distance 0) - For longer words, allow a 30% tolerance for typos.
            let max_distance = if req_word.len() <= 3 {
              0
            } else {
              calc.floor(req_word.len() * 0.3)
            }

            distance <= max_distance
          })
        )
      }
    }

    if not is_mapped {
      unmapped.push(req_skill)
    }
  }

  // 6. Display the unmapped skills if any exist.
  if unmapped.len() > 0 {
    section_title_style("Unmapped Requirements")
    for req in unmapped {
      text(fill: color_UNMAPPED)[• #req]
      v(space_small)
    }
    v(space_large)
  }
}

// ===========================
// SECTIONS 
// ===========================

// --- Header: Name and Title ---
#let show_header(name, label) = {
    upper(text(size: font_size_main_title, weight: "bold", fill: color_accent, font: font_family_secondary)[#name])
    v(-2em)
    text(size: font_size_main_subtitle, font: font_family_secondary)[#label]
}

// --- Contact Information --- 
#let show_contact_info(
  location, 
  email, 
  phone, 
  url, 
  profiles, 
  show_location: true, 
  show_email: true, 
  show_phone: true, 
  show_url: false, 
  show_profiles: true
) = {
  section_title_style("Contact")
  if show_location and location != none and location.city != none and location.region != none {
    text(weight: "bold", size: font_size_medium)[Home:]
    v(-space_large)
    text(size: font_size_medium, fill: color_text_default, location.city + ", " + location.region)
    v(space_small)
  }
  if show_email and email != none {
    text(weight: "bold", size: font_size_medium)[Email:]
    v(-space_large)
    link("mailto:" + email, text(size: font_size_medium, fill: color_text_default, email))
    v(space_small)
  }
  if show_phone and phone != none {
    text(weight: "bold", size: font_size_medium)[Phone:]
    v(-space_large)
    text(size: font_size_medium, fill: color_text_default, phone)
    v(space_small)
  }
  if show_url and url != none {
    text(weight: "bold", size: font_size_medium)[Website:]
    h(0.5em)
    link(url, text(size: font_size_medium, fill: color_link, url.replace("https://", "").replace("http://", "")))
    linebreak()
  }
  if show_profiles and profiles != none and profiles.len() > 0 {
    for profile in profiles {
      if profile.url != none and profile.network != none {
        text(weight: "bold", size: font_size_medium)[#profile.network:]
        h(0.5em)
        link(profile.url, text(size: font_size_medium, fill: color_text_default, profile.username ))
        linebreak()
      }
    }
  }
  v(space_small)
}

// --- Summary / Profile Section ---
#let show_summary(summary_text) = {
  if summary_text != none and summary_text != "" {
    section_title_style("Profile")
    text(font_size_default)[#summary_text]
    v(space_large)
  }
}

// --- Work Experience Section ---
#let show_experience(work_data) = {
  if work_data != none and work_data.len() > 0 {
    section_title_style("Work History")
    for job in work_data {
      // Line 1: Job Position (left) and Date (right)
      block(below: 0.4em)[
        #text(weight: "bold", size: font_size_large)[#job.position]
        #h(1fr)
        #let end_date = job.at("endDate", default: "Present")
        #text(size: font_size_medium, fill: color_text_alternate)[#format_date_range(job.startDate, end_date)]
      ]

      // Line 2: Company Name (styled) on left, Location (styled) on right
      box()[
        #text(weight: "bold", size: font_size_default)[
          #link(job.url, text(fill: color_text_alternate, job.name))
        ]
        #h(1fr) // Pushes location to the right
        #let location = job.at("location", default: none)
        #if location != none and location != "" [
          #text(size: font_size_small, fill: color_text_alternate)[#location]
        ]
      ]
      v(-space_small)

      // Line 3: Conditionally show the job summary based on the flag
      if show_work_summaries {
        let job_summary = job.at("summary", default: none)
        if job_summary != none and job_summary != "" {
          // Display the summary text
          text(size: font_size_default, style: "italic")[#job_summary]
          // Add some space after the summary
          v(space_small)
        }
      }

      // Line 4+: Highlights
      let job_highlights = job.at("highlights", default: none)
      if job_highlights != none and type(job_highlights) == array and job_highlights.len() > 0 {
        for highlight in job_highlights {
          text(size: font_size_default)[- #highlight]
          v(0em)
        }
      }
      v(space_large) // Space between job entries
    }
    v(space_small)
  }
}

/// Projects Section
#let show_projects(projects_data) = {
  if projects_data != none and projects_data.len() > 0 {
    section_title_style("Projects")
    for project in projects_data {
      let end_date = project.at("endDate", default: "Present")
      // Line 1: Title, Year (left) and URL (right)
      grid(
        columns: (1fr, auto),
        gutter: 1em,
        // Left part of the grid cell
        [
          #text(weight: "bold", size: font_size_default)[#project.name], 
          #if project.roles != none and project.roles.len() > 0 {
            text(size: font_size_medium, fill: color_text_alternate)[#project.roles.first()]
          }
    
        ],
        // Right part of the grid cell
        align(right)[
          #text(size: font_size_small, fill: color_text_alternate)[ (#format_date_range(project.startDate, end_date, format: "year"))]
        ]
      )
      let project_description = project.at("description", default: none)
      if project_description != none and project_description != "" {
        v(-space_large) // Space before description
        text(size: font_size_medium)[#project_description]
      }
      v(space_large) // Space between project entries

    /*  Highlights section below the grid

          let proj_highlights = project.at("highlights", default: none)
          if proj_highlights != none and type(proj_highlights) == array and proj_highlights.len() > 0 {
            v(space_small)
            for highlight in proj_highlights {
              [• #highlight]
              v(space_small)
            }
          } 
    */
    }
    v(0.2em)
  }
}



// --- Skills Section ---
#let show_skills(skills_data) = {
  if skills_data != none and skills_data.len() > 0 {
    section_title_style("Skills")
    for skill_category in skills_data {
      text(weight: "bold", size: font_size_default)[#skill_category.name]
      let keywords = skill_category.at("keywords", default: none)
      if keywords != none and type(keywords) == array and keywords.len() > 0 {
        v(-1em) // Remove space before keywords
        for keyword in keywords {
          h(0.5em) 
          text(size: font_size_medium)[- #keyword ]
          v(-1.2em) // Remove space after each keyword
        }
      }
      v(1em) // Space between skill categories
    }
    v(space_large) // Extra space after skills section
  }
}

// --- Education Section ---
#let show_education(education_data) = {
  if education_data != none and education_data.len() > 0 {
     block(breakable: false)[
    #section_title_style("EDUCATION")
    #for edu in education_data {
      let end_date = edu.at("endDate", default: "Present")
      text(weight: "bold", size: font_size_default)[#edu.institution]
      linebreak()
      text(size: font_size_default)[#edu.studyType] + " in " + [#edu.area]
      text(size: font_size_default, fill: color_text_alternate)[ (#format_date_range(edu.startDate, end_date, format: "year"))]
      v(space_large) // Space between education entries
    }
    #v(space_small)
    ]
  }
}

// --- Achievements Section (Combined Awards and Certificates) ---
#let show_achievements(awards_data, certificates_data) = {
  let has_awards = awards_data != none and awards_data.len() > 0
  let has_certs = certificates_data != none and certificates_data.len() > 0

  if has_awards or has_certs {
    section_title_style("Achievements")

    // --- Display Awards ---
    if has_awards {
      for award in awards_data {
        // Use a bolded title, similar to a sub-heading
        text(weight: "bold", size: font_size_small)[#smallcaps[Award:]]
        linebreak()
        text(weight: "bold", size: font_size_default)[#award.title]
        linebreak()
        
        // Combine summary and awarder into a description line
        let description_parts = ()
        if award.at("summary", default: none) != none and award.summary != "" {
          description_parts.push(award.summary) 
        }
        if award.at("awarder", default: none) != none {
          description_parts.push(
            linebreak() +
            text(size: font_size_small, fill:color_text_alternate)[Awarder: #award.awarder]
          )
        }
        if description_parts.len() > 0 {
           text(size: font_size_small)[#description_parts.join(" ")]
        }
        v(space_large) // Space between entries
      }
    }

    // --- Display Certificates ---
    if has_certs {
      for cert in certificates_data {
        text(weight: "bold", size: font_size_small)[#smallcaps[Certificate:]]
        linebreak()
        text(weight: "bold", size: font_size_default)[#cert.name]
        linebreak()

        if cert.at("issuer", default: none) != none {
          text(size: font_size_small, fill:color_text_alternate)[ Issued by: #cert.issuer]
        }
        v(space_large) // Space between entries
      }
    }
    v(space_small)
  }
}

/*  REMOVED, BUT CAN BE ADDED IF DESIRED

// --- Awards Section ---
#let show_awards(awards_data) = {
  if awards_data != none and awards_data.len() > 0 {
    section_title_style("Awards")
    for award in awards_data {
      text(weight: "bold", size: font_size_default)[#award.title]
      if award.at("awarder", default: none) != none {
        text(size: font_size_small)[Awarded by: #award.awarder]
      }
      let award_date = award.at("date", default: none)
      let formatted_award_date = if award_date != none { format_date_range(award_date, none) } else { "" }
      text(size: font_size_small, fill: color_text_alternate)[#formatted_award_date]

      let award_summary = award.at("summary", default: none)
      if award_summary != none and award_summary != "" {
        v(0.2em)
        text(size: font_size_small)[#award_summary]
      }
      v(space_large) // Space between award entries
    }
    v(space_small)
  }
}

// --- Certificates Section ---
#let show_certificates(certificates_data) = {
  if certificates_data != none and certificates_data.len() > 0 {
    section_title_style("Certificates")
    for cert in certificates_data {
      text(weight: "bold", size: font_size_default)[#cert.name]
      if cert.at("issuer", default: none) != none {
        text(size: font_size_small)[Issuer: #cert.issuer]
      }
      let cert_date = cert.at("date", default: none)
      let formatted_cert_date = if cert_date != none { format_date_range(cert_date, none) } else { "" }
      text(size: font_size_small, fill: color_text_alternate)[#formatted_cert_date]
      v(space_large) // Space between certificate entries
    }
    v(space_small)
  }
}
 */
