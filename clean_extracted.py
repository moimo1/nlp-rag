"""
clean_extracted.py
------------------
Reads OCR-extracted .txt files from ExtractedText/ and writes fully cleaned,
standardized, and preprocessed versions to CleanedText/.

Key cleaning and preprocessing capabilities:
  1. Watermark stripping: catches all CamScanner variants across pages.
  2. Noise elimination: removes OCR hallucinations from logos, stamps, graphics,
     and dotted/dashed table borders without discarding real text.
  3. Preservation of legitimate historical records, legal references, and
     international student guidelines previously lost to over-aggressive filtering.
  4. Context-aware OCR corrections: repairs corrupted names, school departments,
     degree acronyms, emails, phone numbers, and web URLs.
  5. Multi-column and table restructuring: formats undergraduate/graduate tuition
     and school fee sections into clean, standardized Markdown tables.
  6. Bullet and typography normalization: standardizes all bullet styles to '* ',
     cleans scan-edge artifacts, and balances spacing.
  7. Table serialization: exports a unified, comprehensive converted_tables.csv.
"""

import os
import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "ExtractedText"
OUTPUT_DIR = BASE_DIR / "CleanedText"
TABLES_CSV_PATH = OUTPUT_DIR / "converted_tables.csv"

PAGE_MARKER_RE = re.compile(r"^--- Page \d+ ---$")

# ---------------------------------------------------------------------------
# 1. Exact or Substring Noise Patterns (Logos, Graphics, Separator Hallucinations)
# ---------------------------------------------------------------------------
DROP_EXACT_PATTERNS = [
    # CamScanner Watermarks
    r"^\s*(?:\(?\d+\)?\s*)?(?:ics\s+)?camscanner\s*$",
    r"^\s*camscanner\s*$",
    r"^\s*\(3\s*camscanner\s*$",
    r"^\s*ics\s*camscanner\s*$",
    # Stray punctuation / logo noise
    r"^\s*\|\s*$",
    r"^\s*@\s*$",
    r"^\s*\{\s*Y\s*$",
    r"^\s*\{\s*$",
    r"^\s*e@?\s*$",
    r"^\s*e\s+e\s*$",
    r"^\s*eee.*$",
    r"^\s*—+\s*$",
    r"^.*abe\s*$",
    r"^\s*N\s*\"\s*$",
    r"^\s*af\s*\|\s*$",
    r"^\s*S\s+nt\s+&\s*$",
    r"^\s*Sai\s+5\s*$",
    r"^\s*e\s+2\s*$",
    r"^\s*-\s+the\s*$",
    r"^\s*P\s+ait\s*$",
    r"^\s*&\.\.\s*$",
    r"^\s*Te\s*$",
    r"^\s*OI\s*$",
    r"^\s*i\s*$",
    r"^\s*a\s*$",
    r"^\s*0\s*$",
    r"^\s*a\s+PERC\s*$",
    r"^\s*,\s*oy\s+kaw\s+Debate.*$",
    r"^\s*\.\s*Louisien\s+oommunity.*$",
    r"^\s*aw\s+Journal.*$",
    r"^\s*Adin\.\s*$",
    r"^\s*h\s*\|\s*Philippines\s*2600\)?\s*$",
    r"^\s*ret\s*\\+\s*$",
    r"^\s*[\W_]*wer\s*\|\s*he\s*$",
    r"^\s*anh\s*$",
    r"^\s*a\)\s*me\s*$",
    r"^\s*:\s*~~\s*[\W_]*$",
    r"^\s*cs\s*[—\-]+\s*$",
    r"^\s*!\s*a\s*;\s*ae\s*$",
    r"^\s*i-\s*bs\s+r\s+oe\s*$",
    r"^\s*Se:\s*54\s+7\s*:\s*$",
    r"^\s*4\s+ju\s+pn\s*$",
    r"^\s*ry\s+Nf\s*$",
    r"^\s*gi\\+y\s*$",
    r"^\s*SMES\s*$",
    r"^\s*1\s+SRiae\s*$",
    r"^\s*;\s*Toe\s+cree\s*$",
    r"^\s*sone\.\s*$",
    r"^\s*[\W_]*J\s+r\s*$",
    r"^\s*,\s*F\s+Seal\s+J\s+Bits\s+4\s*$",
    r"^\s*eb\s+ee\s*$",
    r"^\s*j\s+gets\s+>\s+a\s*\..*$",
    r"^\s*gam\]\.\s*$",
    r"^\s*v\s+[·•\*\.]+\s+at\s+oy\s+aw\s+by\s+ol\s*$",
    r"^\s*a\s+ee\s+i\s+ve\s*$",
    r"^\s*Tynnded\s+hy\s+the.*$",
    r"^\s*\|\s*Philippines\}2600ss.*$",
    r"^\s*Me:\s*\*\s*\.\s*Bia\s+ae\s*$",
    r"^\s*—\s*\|\s*$",
    r"^\s*—+\s*$",
    # Table border noise
    r"^\s*dia\s+naa\s+a\s*$",
    r"^\s*es\s+lll\s+ali\s+alain\s*$",
    r"^\s*Pats\.\.\.\s+acim\s*$",
    r"^\s*\(ahi\s+EE\s*$",
    r"^\s*Patho\s+RPS\s+Slacks.*$",
    r"^\s*PS;\s*A\s+elle\s+teal\s+cast\s*$",
    r"^\s*a:\s*Na\s+lalate\s+tell\s+hata\s*$",
    r"^\s*tea\s+eRe\s+cal\s*$",
    r"^\s*\|\s*antilieinegle\s*$",
    r"^\s*ene\s+nla\s+iretircnetncidintiihll\s*$",
    r"^\s*ee\s+NU\s+tad\s+ate\s*$",
    r"^\s*eal\s+ee\s+eG:\s+dal\s*$",
    r"^\s*a=\s*eee\s*$",
    r"^\s*cent\s+ee\s+EEA\s+TATA\s*$",
    r"^\s*SN\s+cinta\s+lnia\s+Diino\s+ES\s*$",
    r"^\s*Pincethntedtini\s+x\s+Meek!.*$",
    r"^\s*Snctsinihiiihchhiaeennaliant.*$",
    r"^\s*A\s+oan\s+ieee\s+ON\s*$",
    r"^\s*ed\s+hte\s+ha\s+ENE\s+Td\s+Sec\s*$",
    r"^\s*Flat\s+nce\s+ly\s+nanan\s*$",
    r"^\s*>\s*i\s+A\s+AT\s*\|\s*$",
    r"^\s*Ni\.\.\.\s+a\s*$",
    r"^\s*\(iii\s+oc\s+as\s+es\s+wosiceis.*$",
    r"^\s*Iaieininemmpeersseibceeitommsan.*$",
    r"^\s*COURSE\s+een\s*$",
]

DROP_REGEXES = [re.compile(p, re.IGNORECASE) for p in DROP_EXACT_PATTERNS]

def should_drop_line(line):
    s = line.strip()
    if not s:
        return False
    # Preserve markdown table separator (e.g. |---|---|)
    if re.match(r"^\|?\s*[-:]+\s*\|[-| :]+$", s):
        return False
    for r in DROP_REGEXES:
        if r.match(s):
            return True
    # Pure symbol noise without digits (e.g. "*", "~", "#", "...")
    if re.match(r"^[\W_]+$", s):
        return True
    # Isolated 1-2 character non-alphanumeric noise
    if len(s) <= 2 and not s.isalnum():
        return True
    return False

# ---------------------------------------------------------------------------
# 2. Comprehensive OCR and Content Replacements
# ---------------------------------------------------------------------------
REPLACEMENTS = [
    # Global Misread Words
    (r"\bManagernent\b", "Management"),
    (r"\bmanagernent\b", "management"),
    (r"\bDepartrnent\b", "Department"),
    (r"\bdepartrnent\b", "department"),
    (r"\bEnvironrnent\b", "Environment"),
    (r"\benvironrnent\b", "environment"),
    (r"\bGovernrnent\b", "Government"),
    (r"\bgovernrnent\b", "government"),
    (r"\bStaternent\b", "Statement"),
    (r"\bstaternent\b", "statement"),
    (r"\bIrnplementation\b", "Implementation"),
    (r"\birnplementation\b", "implementation"),
    (r"\bInforrnation\b", "Information"),
    (r"\binforrnation\b", "information"),
    (r"\bCornputer\b", "Computer"),
    (r"\bcornputer\b", "computer"),
    (r"\bCornputing\b", "Computing"),
    (r"\bcornputing\b", "computing"),
    (r"\bCornmerce\b", "Commerce"),
    (r"\bcornmerce\b", "commerce"),
    (r"\bPhillppines\b", "Philippines"),
    (r"\bPhilipines\b", "Philippines"),
    (r"\btechnolagy\b", "technology"),
    (r"\bTechnolagy\b", "Technology"),
    (r"\bteennalogy\b", "technology"),
    (r"\bTeennalogy\b", "Technology"),
    (r"\bMathematies\b", "Mathematics"),
    (r"\bmathematies\b", "mathematics"),
    (r"\bEdueation\b", "Education"),
    (r"\bedueation\b", "education"),
    (r"\bNuterhel\b", "Maternal"),
    (r"\bsgents\b", "agents"),
    (r"\bniemational\b", "international"),
    (r"\binternationational\b", "international"),
    (r"\bone-\s*-time-payment\b", "one-time payment"),
    (r"“Out-of-\s*-State-Fee”", "“Out-of-State Fee”"),
    (r"Schoo[!\]}]", "School"),
    (r"\bCalleg\b", "College"),
    (r"\bauthorizeg\b", "authorized"),
    (r"2010-201\]", "2010-2011"),
    (r"2026\s*-\s*2097", "2026 - 2027"),
    (r"A[¥\?]:?2026\s*-\s*2027", "AY 2026 - 2027"),
    (r"@siu\.edu\.ph", "@slu.edu.ph"),
    (r"@sliu\.edu\.ph", "@slu.edu.ph"),
    (r"NaagmMission@(?:siu|slu)\.edu\.ph", "admissions@slu.edu.ph"),
    (r"https:/Awww\.facebook\.com/slu\.u?\s*ro\.?", "https://www.facebook.com/slu.uro"),
    (r"Wwww,slu\.edu\.ph", "www.slu.edu.ph"),
    (r"steladean@slu\.edu,ph\s*[a-z]?", "steladean@slu.edu.ph"),
    (r"sasclerk@slu\.edu,ph", "sasclerk@slu.edu.ph"),
    (r"\bAlltransfer\b", "All transfer"),
    (r"\bIfthe\b", "If the"),
    (r"\bFora\b", "For a"),
    (r"\bautomaticallydenied\b", "automatically denied"),
    (r"anot hei [‘']HEI, he/s", "another HEI, he/she"),
    (r"\bcurrentyear\b", "current year"),
    (r"\bFullonline\b", "Full online"),
    (r"\bBaguioGity\b", "Baguio City"),
    (r"Computer Sience", "Computer Science"),
    (r"\bpROGRAMS OFFERED\b", "PROGRAMS OFFERED"),
    (r"\bpoctor\b", "Doctor"),
    (r"\bpachelot\b", "Bachelor"),
    (r"\bgachelor\b", "Bachelor"),
    (r"\bgcience\b", "Science"),
    (r"BSM LS", "BSMLS"),
    (r"BSIMA", "BSMA"),
    (r"BAP Osc", "BAPOLSCI"),
    (r"BAPOLSCL", "BAPOLSCI"),
    (r"Novernber", "November"),
    (r"Exarnination", "Examination"),
    (r"Censure Examination", "Licensure Examination"),
    (r"topnotehe!", "topnotcher"),
    (r"ValUe-Jaden", "value-laden"),
    (r"ofbiopageof passport", "of bio page of passport"),
    (r"in thei [‘']country 2 et", "in their country"),
    (r"bachelor['’]s degree or maste \(", "bachelor’s degree or master’s degree"),
    (r"\bspecia\b", "special"),
    (r"Graduate Progran", "Graduate Program"),
    (r"Tranklifie", "Trunkline"),
    (r"Pownded", "Founded"),
    (r"Ssasdean@", "sasdean@"),
    (r"a\)\s*sassec@", "sassec@"),
    (r"i\]\s*sas\.admission@", "sas.admission@"),
    (r"wilh\.\s*\n\s*take the Personality Testand go through", "will take the Personality Test and go through"),
    (r"ee Oe / ADMISSION\s*\n\s*\|\s*INFORMATION", "ADMISSION INFORMATION"),
    (r"ee Oe / ADMISSION \| INFORMATION", "ADMISSION INFORMATION"),
    (r"\\+?\s*ADMISSION\s+wri/\)\s+INFORMATION", "ADMISSION INFORMATION"),
    (r"—[\"']\s*abe\s*\n\s*ADMISSION INFORMATION", "ADMISSION INFORMATION"),
    (r"\(then College Saint Louis College of Law\)", "(then Saint Louis College of Law)"),
    (r"\(then Calleg\s*\n\s*Saint Louis College of Law\)", "(then Saint Louis College of Law)"),
    (r"Top-Performing Schooll\b", "Top-Performing School"),

    # SAMCIS Specific
    (r"niemational busin sand information teennalogy\s*erivir HmmMents",
     "international business and information technology environments"),
    (r"SAINT LOUIS UNIVERSITY y\b", "SAINT LOUIS UNIVERSITY"),
    (r"Accountancy ang\b", "Accountancy and"),
    (r"original Schoolk\b", "original Schools"),
    (r"AFFILIATIONS 4\b", "AFFILIATIONS"),
    (r"CHED 4\s*\n\s*Centers of Development", "CHED Centers of Development"),
    (r"CHED 4\b", "CHED"),
    (r"SCHEMA \| The Official Student Publication of =",
     "SCHEMA | The Official Student Publication of"),
    (r"School of Accountancy, Management, 4\b", "School of Accountancy, Management,"),
    (r"Computing and Information Studies as\b", "Computing and Information Studies"),
    (r'Integrated Confederacy "Ais', "Integrated Confederacy"),
    (r"Junior Financial Executives of the Philippines:\s*\n\s*_?\s*Saint Louis University Chapter\s*[a-z]?",
     "Junior Financial Executives of the Philippines - Saint Louis University Chapter"),
    (r"“\+\s*Junior Philippine Institute of Accountants\s*[a-z]?",
     "* Junior Philippine Institute of Accountants"),
    (r"_\*\s*Louisians Imbibed with Genuine Spirit for a?\s*\n\s*_\.\s*Hospitality Transformation\s*[a-z]?",
     "* LIGHT (Louisians Imbibed with Genuine Spirit for Hospitality Transformation)"),
    (r"_\*\s*Marketing Mixers\s*\|+", "* Marketing Mixers"),
    (r"'# Rated: Production Guild\s*[a-z]?", "* Rated: Production Guild"),
    (r"\*\s*Society of Integrated Comimercians for Academic\s*\n\s*Progress\s*;\s*[‘' ]*ia\s+al",
     "* Society of Integrated Commercians for Academic Progress"),
    (r"\+\s*Young Entrepreneurs['’]Society", "* Young Entrepreneurs' Society"),
    (r"\bBSIMA\b\s*Accounting", "BSMA (Bachelor of Science in Management Accounting)"),
    (r"8s8AMKIOMGMT-BA\s*=\s*PAP\s*11,884\.00\s*PhP\s*37,172\.00",
     "BSBA MKTGMGMT-BA PhP 11,884.00 PhP 37,172.00"),
    (r"BSHM\s*\._—\s*PhP['’]11,965\.00\s*_—\s*PhP\.\s*37,253\.00",
     "BSHM PhP 11,965.00 PhP 37,253.00"),
    (r"BSCOMPSCI\b", "BSCS"),
    (r"Motel Suite Setierien mee a sa Cookery",
     "* Model Suite\n* Kitchen and Cookery Laboratory"),
    (r"avails Campus, Bakakeng", "Maryheights Campus, Bakakeng"),
    (r"etieesGta inkline \(LocaliNumber\.- 504\)", "Trunkline (Local Number - 504)"),

    # SAS Specific
    (r"BAGUIO CITY, PHILIPPINES py\b", "BAGUIO CITY, PHILIPPINES"),
    (r"4 ADMISSIO\s*\n\s*y INFORMATIO", "ADMISSION INFORMATION"),
    (r"of origin ie ae\b", "of origin"),
    (r"[°\*\s]*Documentary\s+cl\s*earal.*?\n[\s_\-\*]*arenon\s+Filipinos.*?\n.*?to\s+settle.*?",
     "* Documentary clearance\n* Qualified applicants who are non-Filipinos and/or graduates of international schools will be required to settle a one-time payment of an Out-of-State Fee."),
    (r"ag oo aeergineeting\b", "Doctorate Programs:\n* Doctor of Engineering"),
    (r"Education Major in Science\s*\n\s*Education\s*;\s*", "Education Major in Science Education\n"),
    (r"w/ specialization in:\s*\n\s*o Pharmacognosy\s*© Industrial Pharmacy\s*\n\s*> Medicinal Chemistry",
     "with specialization in:\n* Pharmacognosy\n* Industrial Pharmacy\n* Medicinal Chemistry"),
    (r"\bursing Administration\b", "* Nursing Administration"),
    (r"€r in Information Technology\b", "Computing and Information Technology Programs:\n* Master in Information Technology"),
    (r"chereducation Prearatns,?", "Teacher Education Programs:"),
    (r"Tea! s in Special Education", "* Master of Arts in Special Education"),
    (r"[‘' ]*eee \| peng in Cathdlic Educational Leadership and\s*\n\s*[’'\* ]*ement",
     "* Master of Arts in Catholic Educational Leadership and Management"),
    (r"wares f Arts in Educational Management", "* Master of Arts in Educational Management"),
    (r"\.?\s*ante of Science in Physical Education and Sports",
     "* Master of Science in Physical Education and Sports"),
    (r":?\s*aa of Arts in Education with areas of specialization\s*\n\s*4 Early Childhood Education Inclusive Education\s*\n\s*o Language Education o Social Studies\s*\n\s*© Science Education",
     "* Master of Arts in Education with areas of specialization in: Early Childhood Education, Inclusive Education, Language Education, Social Studies, Science Education"),
    (r"\{atural Sciences Programs|jatural Sciences Programs", "Natural Sciences Programs:"),
    (r"agineering Programs", "Engineering Programs:"),
    (r"rent of Science in Environmental Engineering", "* Master of Science in Environmental Engineering"),
    (r"[“\"]\s*ster of Science in Environmental Engineering major\s*\n\s*Moen Environmental Measures and Processes",
     "* Master of Science in Environmental Engineering major in Mining Environmental Measures and Processes"),
    (r"[“\"]\s*ster of Science in Management Engineering", "* Master of Science in Management Engineering"),
    (r"eae in Manufacturing Engineering and\s*\n\s*[‘']sNagement", "* Master in Manufacturing Engineering and Management"),

    # SOL Specific
    (r"\|\s*4F Silang Building, SLU MainCampus,\s*sd", "4F Diego Silang Building, SLU Main Campus,"),
    (r"\|\s*A Bonifacio St\., Baguio City, Benguet, =", "A. Bonifacio St., Baguio City, Benguet,"),
    (r"Philippines 2600 oats roe \.", "Philippines 2600"),
    (r"\*\(63\) \(74\) 442 3043 \+\(63\) \(74\) 443 200\)", "+(63) (74) 442 3043 +(63) (74) 443 2001"),
    (r"SAINT LOUIS UNIVERSITY At\?", "SAINT LOUIS UNIVERSITY"),
    (r"marked the birth o[¢c]", "marked the birth of"),
    (r"then Calleg\s*\n\s*Saint Louis College", "then Saint Louis College"),
    (r"Transcript of Records i\b", "Transcript of Records"),
    (r"Notarized Certificate of Employment \(for these", "Notarized Certificate of Employment (for employed applicants)"),
    (r"\+\s*Other documents may be needed as determine\s*\n\s*ve by\. SLU SOL",
     "* Other documents may be needed as determined by SLU SOL"),
    (r"Php 509 for the examination fee", "Php 500 for the examination fee"),
    (r"Higher Educational os\s*\n\s*Institution", "Higher Educational Institution"),
    (r"40% to 59\.9 99% i\s*\n\s*of the total", "40% to 59.99% of the total"),
    (r"All\s*transfer students may\s*be ——~~\s*\n\s*admitted with a condition Ny\)\s*\n\s*that ee not have \\ eo\. 6\)",
     "All transfer students may be admitted with the condition that they should not have any failing grades."),
    (r"e 2025 Bar Examinations top-performing Schoo\]?", "* 2025 Bar Examinations Top-Performing School"),
    (r"o Ranked 2\" in the 11-50 examinees Catego\s*\n\s*the 2025 Bar Examinations With a 97\.14%, 'Y of\s*\n\s*passing rate for first-time takers",
     "* Ranked 2nd in the 11-50 examinees Category of the 2025 Bar Examinations with a 97.14% passing rate for first-time takers"),
    (r"o Ranked 4\" inthe 51-100 examinees Category fo,\s*\n\s*both first time takers and re-takers with an\s*\n\s*83\.33% passing rate",
     "* Ranked 4th in the 51-100 examinees Category for both first-time takers and re-takers with an 83.33% passing rate"),
    (r"Juris Doctor \(3\.D\.\)", "Juris Doctor (J.D.)"),
    (r"Full face-to-face\s+e\s+Audit Courses", "* Full face-to-face\n* Audit Courses"),
    (r"Full online until 3(?:\s*rd)?\s*year\s+[©®e\ufffd]\s+Refresher courses", "* Full online until 3rd year\n* Refresher courses"),
    (r"Master of Laws \(L\.L\.M\.\)\s*\n\s*[©®\*]*\s*Fullonline", "Master of Laws (LL.M.)\n* Full online"),
    (r"\*\s*\*+\s*Debate and Mooting", "* Debate and Mooting"),
    (r"rounded on April 18, 2015, the CJIMM CLAO", "Founded on April 18, 2015, the CJMM CLAO"),
    (r":\s*Moot Court E Low Library", "* Moot Court\n* Law Library"),

    # SOM Specific
    (r"frorn CHED\b", "from CHED"),
    (r"frorn two", "from two"),
    (r"\" “aboratory Room Lecture ROOM\s*\n\s*bh Anatomy Laboratory Anatomage Table",
     "* Laboratory Room\n* Lecture Room\n* Anatomy Laboratory\n* Anatomage Table"),

    # SONAHBS Specific
    (r"\|\s*\"?\s*«?\s*4F Jose Rizal Building, SLU Main\"?Campusy?\s*=?",
     "4F Jose Rizal Building, SLU Main Campus,"),
    (r"A\. Bonifacio St, BaguioGity,Benguet,", "A. Bonifacio St., Baguio City, Benguet,"),
    (r"Philippines 2600 :?", "Philippines 2600"),
    (r"\* 5F Diego Silang Building, SLU Main Campus", "5F Diego Silang Building, SLU Main Campus,"),
    (r"A\. Bonifacio St,, Baguio City»Benguet,", "A. Bonifacio St., Baguio City, Benguet,"),
    (r"Trunkline \(Local Number for Nursing - 294\)\s*\n\s*\(Allied Health \+ Biological Scienees\*22\)\)",
     "Trunkline: Local 294 (Nursing), Local 221 (Allied Health and Biological Sciences)"),
    (r"SAINT LOUIS UNIVERSITY <7\"", "SAINT LOUIS UNIVERSITY"),
    (r"BAGUIO GITY, PHILIPPINES at", "BAGUIO CITY, PHILIPPINES"),
    (r"Biologica\}\s*\n\s*Sciences is a reunification of two schools: the Schoo\}",
     "Biological Sciences is a reunification of two schools: the School of Natural Sciences (SNS), which was once the"),
    (r"Bie international students.*?undertake the English Proficiency Tes[t]?",
     "All international students shall undergo review of their documents and when warranted after due assessment, shall undertake the English Proficiency Test.",
     re.DOTALL),
    (r":\s*pachelot of Science in Medical Laboratory\s*\n\s*gcience \(BSM LS\)",
     "* Bachelor of Science in Medical Laboratory Science (BSMLS)"),
    (r"\*\s*gachelor of Science in Pharmacy \(BS Pharm\)",
     "* Bachelor of Science in Pharmacy (BS Pharm)"),
    (r"\.\s*Bachelor of Science In Physical Therapy \(BSPT\)",
     "* Bachelor of Science in Physical Therapy (BSPT)"),
    (r"\.\s*Bachelor of Science in Radiologic Technology\s*\n\s*\(BSRT\)",
     "* Bachelor of Science in Radiologic Technology (BSRT)"),
    (r"achelo! of Science in Biology \(BSBIO - MB\)",
     "* Bachelor of Science in Biology (BSBIO - MB)"),
    (r"Censure Examination with a top six topnotehe!",
     "Licensure Examination with a top six topnotcher."),
    (r": VU SONAHBS is fourth Top-Performing Schoo!\"",
     "* SLU SONAHBS is fourth Top-Performing School in"),

    # STELA Specific
    (r"A\. Bonifacio Street\) Baguio City, Benguet, cs", "A. Bonifacio St., Baguio City, Benguet, Philippines 2600"),
    (r"SAINT LOUIS UNIVERSITY &k\s*\n\s*BAGUIO CITY, PHILIPPINES nis",
     "SAINT LOUIS UNIVERSITY\nBAGUIO CITY, PHILIPPINES"),
    (r"Libera\] Arts", "Liberal Arts"),
    (r"In academic year 2016-2017 and under the Visionary\s*\n\s*both schools have been strategically merged",
     "In academic year 2016-2017 and under the visionary leadership of Rev. Fr. Gilbert B. Sales, CICM, both schools have been strategically merged"),
    (r"Council \(TEC\) Mt :?", "Council (TEC)"),
    (r"\(PAASCU\) ya\b", "(PAASCU)"),
    (r"SLU Political Sclence", "SLU Political Science"),
    (r"take the Personality Testand go through\s*\n\s*an Intery w\. All i national st der :?",
     "take the Personality Test and go through an interview.\n* All international students shall undergo review of their documents and when warranted after due assessment, shall undertake the English Proficiency Test."),
    (r"\*\s*Bachélor of Arts in Philosophy \(BAPHILO\)", "* Bachelor of Arts in Philosophy (BAPHILO)"),
    (r"\+\s*Bachelor of Arts in Political Science \(BAP Osc\)", "* Bachelor of Arts in Political Science (BAPOLSCI)"),
    (r"Audio - Visual Room TV Broadcasting Studio\s*\n\s*Radio Bre adcasting Booth Aquatics Fact",
     "* Audio-Visual Room\n* TV Broadcasting Studio\n* Radio Broadcasting Booth\n* Aquatics Facility\n* Physical Education and Recreation Center (PERC)"),
]

# ---------------------------------------------------------------------------
# 3. Markdown Fee Table Formatters
# ---------------------------------------------------------------------------
def format_fee_tables(text, filename):
    """
    Detects fee sections in text and transforms them into clean Markdown tables.
    """
    if "SAMCIS" in filename:
        samcis_table = """### First Year First Semester School Fees (AY 2026 - 2027)
* Fees are subject to change with prior notice and consultation.

| Program Code | Program Name | Required Downpayment (Partial) | Full Payment |
|---|---|---|---|
| BSAC | Bachelor of Science in Accountancy | PhP 12,627.00 | PhP 36,601.00 |
| BSMA | Bachelor of Science in Management Accounting | PhP 12,627.00 | PhP 36,601.00 |
| BSENTREP-BA | BS in Entrepreneurship (Business Analytics) | PhP 11,884.00 | PhP 37,172.00 |
| BSBA FINMAN-BA | BSBA major in Financial Management (Business Analytics) | PhP 11,884.00 | PhP 37,172.00 |
| BSHM | Bachelor of Science in Hospitality Management | PhP 11,965.00 | PhP 37,253.00 |
| BSBA MKTGMGMT-BA | BSBA major in Marketing Management (Business Analytics) | PhP 11,884.00 | PhP 37,172.00 |
| BSTM | Bachelor of Science in Tourism Management | PhP 11,965.00 | PhP 37,253.00 |
| BSCS | Bachelor of Science in Computer Science | PhP 26,476.00 | PhP 49,924.00 |
| BSIT | Bachelor of Science in Information Technology | PhP 24,476.00 | PhP 49,924.00 |"""
        text = re.sub(
            r"FIRST YEAR FIRST SEMESTER\s*\n\s*SCHOOL FEES AS OF AY 2026 - 2027.*?(?=--- Page|\Z)",
            samcis_table + "\n\n",
            text,
            flags=re.DOTALL
        )

    elif "SOM" in filename:
        som_table = """### First Year First Semester School Fees (AY 2026 - 2027)
* Fees are subject to change with prior notice and consultation.

| Program Code | Program Name | Required Downpayment (Partial) | Full Payment |
|---|---|---|---|
| APMED | Accelerated Pathway for Medicine | PhP 18,947.00 | PhP 42,491.00 |
| MD | Doctor of Medicine | PhP 55,000.00 | PhP 138,283.00 |

* Note: Above fees apply for new entrants. Old Students: PhP 135,503.00."""
        text = re.sub(
            r"FIRST YEAR FIRST SEMESTER\s*\n\s*SCHOOL FEES AS OF AY 2026 - 209?7.*?(?=SCHOOL-BASED FACILITIES|\Z)",
            som_table + "\n\n",
            text,
            flags=re.DOTALL
        )

    elif "SONAHBS" in filename:
        sonahbs_table = """### First Year First Semester School Fees (AY 2026 - 2027)
* Fees are subject to change with prior notice and consultation.

| Program Code | Program Name | Required Downpayment (Partial) | Full Payment |
|---|---|---|---|
| BSBIO-MB | BS in Biology major in Microbiology | PhP 14,670.00 | PhP 35,598.00 |
| BS MLS | BS in Medical Laboratory Science | PhP 13,252.00 | PhP 35,052.00 |
| BS PHARM | BS in Pharmacy | PhP 16,412.00 | PhP 39,956.00 |
| BS RADTECH | BS in Radiologic Technology | PhP 15,002.00 | PhP 35,930.00 |
| BSN | BS in Nursing | PhP 16,230.00 | PhP 49,378.00 |"""
        text = re.sub(
            r"FIRST YEAR FIRST SEMESTER\s*\n\s*SCHOOL FEES AS OF AY 2026 - 2027.*?(?=RECOGNITIONS|\Z)",
            sonahbs_table + "\n\n",
            text,
            flags=re.DOTALL
        )

    elif "STELA" in filename:
        stela_table = """### First Year First Semester School Fees (AY 2026 - 2027)
* Fees are subject to change with prior notice and consultation.

| Program Code | Program Name | Required Downpayment (Partial) | Full Payment |
|---|---|---|---|
| BA COMM | Bachelor of Arts in Communication | PhP 11,884.00 | PhP 33,242.00 |
| BAPHILO | Bachelor of Arts in Philosophy | PhP 11,884.00 | PhP 33,242.00 |
| BAPOLSCI | Bachelor of Arts in Political Science | PhP 11,884.00 | PhP 33,242.00 |
| BS PSYCH | Bachelor of Science in Psychology | PhP 12,906.00 | PhP 34,706.00 |
| BA SWK | Bachelor of Science in Social Work | PhP 11,884.00 | PhP 30,626.00 |
| BSED | Bachelor of Secondary Education | PhP 11,884.00 | PhP 33,242.00 |
| BSNED | Bachelor of Special Needs Education | PhP 11,784.00 | PhP 35,758.00 |
| BPED | Bachelor of Physical Education | PhP 11,884.00 | PhP 33,242.00 |
| BEED | Bachelor of Elementary Education | PhP 11,884.00 | PhP 33,242.00 |"""
        text = re.sub(
            r"FIRST YEAR FIRST SEMESTER\s*\n\s*SCHOOL FEES AS OF AY 2026 - 2027.*?(?=--- Page|\Z)",
            stela_table + "\n\n",
            text,
            flags=re.DOTALL
        )

    return text

# ---------------------------------------------------------------------------
# 4. Bullet Normalization
# ---------------------------------------------------------------------------
BULLET_CHARS = set("•*«»§¢°´'’¤+·®©")

def normalize_bullets(line):
    s = line.strip()
    if not s or PAGE_MARKER_RE.match(s) or s.startswith("|") or s.startswith("#"):
        return s

    # Starts with a bullet glyph
    if s[0] in BULLET_CHARS and len(s) > 1:
        return "* " + s[1:].lstrip()

    # Starts with 'e ' or 'o ' or '- ' before text
    if len(s) >= 3 and s[0] in "eo-" and s[1] == " ":
        return "* " + s[2:].lstrip()

    return s

# ---------------------------------------------------------------------------
# 5. Core Cleaning Function
# ---------------------------------------------------------------------------
def clean_text(raw_text, filename=""):
    text = raw_text

    # Apply all targeted regex replacements
    for pattern_data in REPLACEMENTS:
        if len(pattern_data) == 3:
            pattern, repl, flags = pattern_data
            text = re.sub(pattern, repl, text, flags=flags)
        else:
            pattern, repl = pattern_data
            text = re.sub(pattern, repl, text, flags=re.MULTILINE)

    # Format fee sections into structured Markdown tables
    text = format_fee_tables(text, filename)

    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        # Page markers are preserved intact with spacing
        if PAGE_MARKER_RE.match(stripped):
            cleaned_lines.append("")
            cleaned_lines.append(stripped)
            cleaned_lines.append("")
            continue

        # Check and drop noise
        if should_drop_line(stripped):
            continue

        # If it's a markdown table row or markdown heading, preserve prefix!
        if stripped.startswith("|") or stripped.startswith("#"):
            cleaned = stripped
        else:
            # Clean leading pipe / artifact noise
            cleaned = re.sub(r"^[\|\_\#\:\.\,]+\s*", "", stripped).strip()
            cleaned = normalize_bullets(cleaned)

            # Clean trailing scan-edge artifacts (isolated single char or punctuation)
            cleaned = re.sub(r"\s+[\|\_\#\:\.\,\=\~\-]$", "", cleaned).strip()

        if cleaned:
            cleaned_lines.append(cleaned)

    # Collapse consecutive blank lines
    result = []
    blank = False
    for l in cleaned_lines:
        if not l:
            if not blank:
                result.append("")
                blank = True
        else:
            result.append(l)
            blank = False

    return "\n".join(result).strip() + "\n"

# ---------------------------------------------------------------------------
# 6. Generate Unified converted_tables.csv
# ---------------------------------------------------------------------------
def generate_tables_csv(output_path):
    csv_rows = [
        "COURSE,REQUIRED DOWNPAYMENT PARTIAL,FULL,SCHOOL",
        # SOM
        "APMED,PhP 18947.00,PhP 42491.00,SOM",
        "MD,PhP 55000.00,PhP 138283.00,SOM",
        # SONAHBS
        "BS BIO - MB,PhP 14670.00,PhP 35598.00,SONAHBS",
        "BS MLS,PhP 13252.00,PhP 35052.00,SONAHBS",
        "BS PHARM,PhP 16412.00,PhP 39956.00,SONAHBS",
        "BS RADTECH,PhP 15002.00,PhP 35930.00,SONAHBS",
        "BSN,PhP 16230.00,PhP 49378.00,SONAHBS",
        # STELA
        "BA COMM,PhP 11884.00,PhP 33242.00,STELA",
        "BA PHILO,PhP 11884.00,PhP 33242.00,STELA",
        "BA POLSCI,PhP 11884.00,PhP 33242.00,STELA",
        "BS PSYCH,PhP 12906.00,PhP 34706.00,STELA",
        "BA SWK,PhP 11884.00,PhP 30626.00,STELA",
        "BSED,PhP 11884.00,PhP 33242.00,STELA",
        "BSNED,PhP 11784.00,PhP 35758.00,STELA",
        "BPED,PhP 11884.00,PhP 33242.00,STELA",
        "BEED,PhP 11884.00,PhP 33242.00,STELA",
        # SAMCIS
        "BSAC,PhP 12627.00,PhP 36601.00,SAMCIS",
        "BSMA,PhP 12627.00,PhP 36601.00,SAMCIS",
        "BSENTREP-BA,PhP 11884.00,PhP 37172.00,SAMCIS",
        "BSBA FINMAN-BA,PhP 11884.00,PhP 37172.00,SAMCIS",
        "BSHM,PhP 11965.00,PhP 37253.00,SAMCIS",
        "BSBA MKTGMGMT-BA,PhP 11884.00,PhP 37172.00,SAMCIS",
        "BSTM,PhP 11965.00,PhP 37253.00,SAMCIS",
        "BSCS,PhP 26476.00,PhP 49924.00,SAMCIS",
        "BSIT,PhP 24476.00,PhP 49924.00,SAMCIS",
    ]
    output_path.write_text("\n".join(csv_rows) + "\n", encoding="utf-8")
    print(f"[OK] Generated {output_path.name} ({len(csv_rows)-1} course fee entries across 4 schools)")

# ---------------------------------------------------------------------------
# 7. Main Entry Point
# ---------------------------------------------------------------------------
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    txt_files = sorted(INPUT_DIR.glob("*.txt"))

    if not txt_files:
        print(f"No .txt files found in {INPUT_DIR}")
        return

    for txt_path in txt_files:
        raw = txt_path.read_text(encoding="utf-8")
        cleaned = clean_text(raw, filename=txt_path.name)

        out_path = OUTPUT_DIR / txt_path.name
        out_path.write_text(cleaned, encoding="utf-8")

        original_lines = len(raw.splitlines())
        cleaned_lines = len(cleaned.splitlines())
        print(f"[OK] {txt_path.name:22s} | {original_lines:3d} lines -> {cleaned_lines:3d} lines")

    generate_tables_csv(TABLES_CSV_PATH)
    print(f"\nAll cleaned files successfully saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
