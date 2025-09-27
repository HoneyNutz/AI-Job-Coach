// coverletter.typ (Formatted with the exact resume grid)

// --- Import Shared Styles & Functions ---
#import "template.typ": setup_page, space_xlarge, space_large, space_medium, space_small, font_size_default, font_size_medium, font_size_small, font_size_section_title, font_family_secondary

// --- Load Personal Data ---
#let resume = json("resume.json")

// --- Define Layout Colors (to match resume) ---
#let bar_color = rgb(242, 242, 242)
#let title_color = luma(255) // White, for backgrounds
#let color_accent = rgb("#3D3B8E")

// ===============================================================
// --- MANUAL: EDIT RECIPIENT DETAILS & LETTER CONTENT BELOW ---
// ===============================================================

#let recipient_name = "Talent Management Team"
#let recipient_title = "Talent Acquisition"
#let company_name = "<COMPANY NAME>"
#let company_address = "<ADDRESS>"

#let letter_body = [
#lorem(50)

#lorem(65)

#lorem(85)
]

// ===============================================================
// --- END OF MANUAL EDITING SECTION ---
// ===============================================================

// --- Cover Letter Building Blocks ---

// Styled block for sidebar information.
#let info_block(title, body) = {
  text(font: font_family_secondary, weight: "bold", size: font_size_section_title)[#title]
  v(-1em)
  line(length: 100%, stroke: 0.5pt + luma(180))
  v(space_small)
  body
}

// --- Define Content for Grid Cells (matching resume variable names) ---

// Corresponds to the resume's header block.
#let page_header = {
  align(center)[
    #upper(text(size: 26pt, weight: "bold", fill: color_accent, font: font_family_secondary)[#resume.basics.name])
    #v(-2em)
    #text(size: 20pt, font: font_family_secondary)[#resume.basics.label]
  ]
}

// Corresponds to the resume's `secondary_content`  sidebar.
#let secondary_content = stack(dir: ttb, spacing: space_xlarge)[
  #info_block("From:", [
    #text(weight: "bold")[#resume.basics.name] \
    #resume.basics.location.address \
    #resume.basics.location.city, #resume.basics.location.region //#resume.basics.location.postalCode \
    #link("mailto:" + resume.basics.email, resume.basics.email) \
    #resume.basics.phone
  ])
  #v(2em)
  #info_block("To:", [
    #text(weight: "bold")[#recipient_name] \
    #recipient_title \
    #company_name \
    #company_address
  ])
]

  #let primary_content = stack(dir: ttb, spacing: space_xlarge)[
  
  #text("Dear " + recipient_name + h(1fr) +
    datetime.today().display("[month repr:long] [day], [year]"))
  #set par(first-line-indent: 2em, justify: true)
  #text(font_size_default)[#letter_body]
  
  #stack(dir: ttb, spacing: 0.5em)[
      Sincerely,
      #v(3em) // Space for signature
      #resume.basics.name
  ]
]


// --- Main Document Assembly ---

#setup_page(
  doc_title: resume.basics.name + " - Cover Letter",
  doc_author: resume.basics.name,
  
  // Using the exact grid layout from resume.typ
  grid(
    columns: (1fr,) * 12, // Creates 12 columns of equal width
    rows: (auto, auto, auto, auto),

    // --- Row 1: Top spacing ---
    grid.cell(colspan: 3, fill: bar_color)[#v(3em)],
    grid.cell(colspan: 9)[],

    // --- Row 2: Header Block ---
    grid.cell(colspan: 2, fill: bar_color)[],
    grid.cell(colspan: 8, fill: title_color)[
      #block(
        width: 100%,
        stroke: 2pt, 
        inset: 3em, // Matches resume's inset
        radius: 1pt)[#align(center)[#page_header]]
    ],
    grid.cell(colspan: 2)[],

    // --- Row 3: Main Content ---
    grid.cell(colspan: 3, inset: 2em, fill: bar_color)[#secondary_content],
    grid.cell(colspan: 9, inset: 2em)[#primary_content],
  
    // --- Row 4: Bottom spacing to extend sidebar ---
    grid.cell(colspan: 3, fill: bar_color)[#v(100%)],
    grid.cell(colspan: 9)[],
  )
)
