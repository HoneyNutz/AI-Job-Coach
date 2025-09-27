//=====================
// BOX STYLE RESUME
//=====================
 
// --- Import the Template ---
#import "template.typ": show_header, show_contact_info, show_summary, show_experience, show_projects, show_skills, show_unmapped_requirements, show_education, show_achievements, setup_page
//show_awards, show_certificates

// --- Load Resume Data ---
#let resume = json("resume.json") // Load condensed resume JSON
#let custom_data = json("job_description.json") // custom job description JSON

// --- Side Bar Coloring ---
#let bar_color = rgb(242,242,242)
#let title_color = luma(255)

// --- Define the Document Sections ---
#let page_header = show_header(resume.basics.name, resume.basics.label)

#let secondary_content = block[
        #show_contact_info(resume.basics.location, resume.basics.email, resume.basics.phone, resume.basics.url, resume.basics.profiles)
        #show_skills(resume.skills)
        #show_education(resume.education)
        #show_unmapped_requirements(resume, custom_data)
        #show_achievements(resume.awards, resume.certificates)
        //#show_awards(resume.awards)
        //#show_certificates(resume.certificates)
        //#show_languages(resume.languages)
        //#show_interests(resume.interests)
      ]

#let primary_content = block[
        #show_summary(resume.basics.summary)
        #show_experience(resume.work)
        #show_projects(resume.projects)
        //#show_publications(resume.publications)
      ]

// --- Define the Page Layout and Content Order ---
#setup_page(
  doc_title: resume.basics.name + " - Resume",
  doc_author: resume.basics.name,
  
  //PRIMARY LAYOUT
  grid(
    columns: (1fr,) * 12, // Creates 12 columns of equal width
    rows: (auto, auto, auto, auto),


    // --- Row 1 ---
    grid.cell(colspan: 3, fill: bar_color)[#v(3em)],
    grid.cell(colspan: 9)[],

    // --- Row 2 ---
    grid.cell(colspan: 2, fill: bar_color)[],
    grid.cell(colspan: 8, fill: title_color)[
      #block(
        width: 100%,
        stroke: 2pt, 
        inset: 3em, 
        radius: 1pt)[#align(center)[#page_header]]],
    grid.cell(colspan: 2)[],

    // --- Row 3 ---
    grid.cell(colspan: 3, inset: 2em, fill: bar_color)[#secondary_content],
    grid.cell(colspan: 9, inset: 2em)[#primary_content],
  
    // --- Row 4 ---
    grid.cell(colspan: 3, fill: bar_color)[#v(100%)],
    grid.cell(colspan: 9)[],
  )
)
