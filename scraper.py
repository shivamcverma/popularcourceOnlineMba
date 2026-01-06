from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import re
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

PCOMBA_O_URL="https://www.shiksha.com/online-mba-chp"
PCOMBA_C_URL="https://www.shiksha.com/online-mba-courses-chp"
PCOMBA_S_URL="https://www.shiksha.com/online-mba-syllabus-chp"
PCOMBA_JOB_URL = "https://www.shiksha.com/online-mba-jobs-chp"
PCOMBA_ADDMISSION_URL="https://www.shiksha.com/online-mba-admission-chp"
PCOMBA_Q_URL = "https://www.shiksha.com/tags/mba-pgdm-tdp-422"
PCOMBA_QD_URL="https://www.shiksha.com/tags/mba-pgdm-tdp-422?type=discussion"


def create_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

# ---------------- UTILITIES ----------------
def scroll_to_bottom(driver, scroll_times=3, pause=1.5):
    for _ in range(scroll_times):
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(pause)




def extract_overview_data(driver):
    driver.get(PCOMBA_O_URL)
    WebDriverWait(driver, 15)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    section = soup.find("section", id="chp_section_overview")

    data = {}
    title = soup.find("div",class_="a54c")
    h1 = title.text.strip()
    data["title"] = h1
    # Updated Date
    updated_div = section.select_one(".f48b div span")
    data["updated_on"] = updated_div.get_text(strip=True) if updated_div else None

    # Author Info
    author_block = section.select_one(".be8c p._7417 a")
    author_role = section.select_one(".be8c p._7417 span.b0fc")
    data["author"] = {
        "name": author_block.get_text(strip=True) if author_block else None,
        "profile_url": author_block["href"] if author_block else None,
        "role": author_role.get_text(strip=True) if author_role else None
    }

    section = soup.find(id="wikkiContents_chp_section_overview_0")
    overview_paras = []
    
    if section:
        for p in section.find_all("p"):
            text = p.get_text(" ", strip=True)
            # Only take paragraphs with more than 50 characters (adjust as needed)
            if text and len(text) > 50:
                overview_paras.append(text)
    
    data["overview"] = overview_paras
        
    # Highlights Table
    highlights = {}
    table = section.find("table")
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all(["td", "th"])
            if len(cols) == 2:
                highlights[cols[0].get_text(strip=True)] = cols[1].get_text(" ", strip=True)
    data["highlights"] = highlights

    iframe = section.select_one(".vcmsEmbed iframe")
    
    if iframe:
        data["youtube_video"] = iframe.get("src") or iframe.get("data-src")
    else:
        data["youtube_video"] = None

    # FAQs
    faqs = []
    faq_questions = section.select(".sectional-faqs > div.html-0")
    faq_answers = section.select(".sectional-faqs > div._16f53f")

    for q, a in zip(faq_questions, faq_answers):
        question = q.get_text(" ", strip=True).replace("Q:", "").strip()
        answer = a.get_text(" ", strip=True).replace("A:", "").strip()
        faqs.append({
            "question": question,
            "answer": answer
        })

    data["faqs"] = faqs
    toc = []
    toc_wrapper = soup.find("ul", id="tocWrapper")
    if toc_wrapper:
        for li in toc_wrapper.find_all("li"):
            toc.append({
                "title": li.get_text(" ", strip=True),
            })
    data["table_of_contents"] = toc


    # ==============================
    # ELIGIBILITY SECTION
    # ==============================
    eligibility_section = soup.find("section", id="chp_section_eligibility")
    eligibility_data = {}

    if eligibility_section:

        # Heading
        heading = eligibility_section.find("h2")
        eligibility_data["title"] = heading.get_text(strip=True) if heading else None

        # Main content block
        content_block = eligibility_section.select_one(".wikkiContents")

        # Paragraphs
        paras = []
        if content_block:
            for p in content_block.find_all("p"):
                text = p.get_text(" ", strip=True)
                if text:
                    paras.append(text)
        eligibility_data["description"] = paras

        # Bullet points
        bullets = []
        if content_block:
            for li in content_block.find_all("li"):
                bullets.append(li.get_text(" ", strip=True))
        eligibility_data["criteria_points"] = bullets

        # YouTube Video inside eligibility
        iframe = eligibility_section.find("iframe")
        eligibility_data["youtube_video"] = iframe.get("src") if iframe else None

        # Admission Steps
        admission_steps = []
        for ol in eligibility_section.find_all("ol"):
            for li in ol.find_all("li"):
                admission_steps.append(li.get_text(" ", strip=True))
        eligibility_data["admission_process"] = admission_steps

        # ==============================
        # ELIGIBILITY FAQs
        # ==============================
        faqs = []
        faq_questions = eligibility_section.select(".sectional-faqs > div.html-0")
        faq_answers = eligibility_section.select(".sectional-faqs > div._16f53f")

        for q, a in zip(faq_questions, faq_answers):
            faqs.append({
                "question": q.get_text(" ", strip=True).replace("Q:", "").strip(),
                "answer": a.get_text(" ", strip=True).replace("A:", "").strip()
            })

        eligibility_data["faqs"] = faqs

    data["eligibility_section"] = eligibility_data

    # SYLLABUS & SPECIALIZATION SECTION
    # ==============================
    syllabus_section = soup.find("section", id="chp_section_popularspecialization")
    syllabus_data = {}

    if syllabus_section:

        # Section Title
        title = syllabus_section.find("h2")
        syllabus_data["title"] = title.get_text(strip=True) if title else None

        content_block = syllabus_section.select_one(".wikkiContents")

        # Intro Paragraphs
        intro_paras = []
        if content_block:
            for p in content_block.find_all("p"):
                text = p.get_text(" ", strip=True)
                if text and "Source:" not in text:
                    intro_paras.append(text)
        syllabus_data["description"] = intro_paras

        # ==============================
        # SEMESTER-WISE SYLLABUS TABLE
        # ==============================
        semester_syllabus = {}

        tables = content_block.find_all("table") if content_block else []

        if tables:
            syllabus_table = tables[0]   # ✅ FIRST table only
            current_semester = None

            for row in syllabus_table.find_all("tr"):
                th = row.find("th")
                tds = row.find_all("td")

                # Semester Header
                if th and not tds:
                    current_semester = th.get_text(strip=True)
                    semester_syllabus[current_semester] = []

                # Subjects
                elif current_semester and tds:
                    for td in tds:
                        subject = td.get_text(" ", strip=True)
                        if subject:
                            semester_syllabus[current_semester].append(subject)

        syllabus_data["semester_wise_syllabus"] = semester_syllabus

        # ==============================
        # SYLLABUS YOUTUBE VIDEO
        # ==============================
        iframe = syllabus_section.select_one(".vcmsEmbed iframe")
        syllabus_data["youtube_video"] = iframe.get("src") if iframe else None

        # ==============================
        # MBA SPECIALISATIONS TABLE
        # ==============================
        specialisations = []
        tables = content_block.find_all("table") if content_block else []

        if len(tables) > 1:
            spec_table = tables[1]
            rows = spec_table.find_all("tr")[1:]

            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    specialisations.append({
                        "specialisation": cols[0].get_text(" ", strip=True),
                        "average_salary": cols[1].get_text(" ", strip=True),
                        "colleges": cols[2].get_text(" ", strip=True)
                    })

        syllabus_data["specialisations"] = specialisations

        # ==============================
        # POPULAR SPECIALIZATION BOX
        # ==============================
        popular_specs = []
        spec_box = syllabus_section.select_one(".specialization-box")

        if spec_box:
            for li in spec_box.select("ul.specialization-list li"):
                popular_specs.append({
                    "name": li.find("a").get_text(strip=True),
                    "url": li.find("a")["href"],
                    "college_count": li.find("p").get_text(strip=True)
                })

        syllabus_data["popular_specializations"] = popular_specs

        # ==============================
        # SYLLABUS FAQs
        # ==============================
        faqs = []
        faq_questions = syllabus_section.select(".sectional-faqs > div.html-0")
        faq_answers = syllabus_section.select(".sectional-faqs > div._16f53f")

        for q, a in zip(faq_questions, faq_answers):
            faqs.append({
                "question": q.get_text(" ", strip=True).replace("Q:", "").strip(),
                "answer": a.get_text(" ", strip=True).replace("A:", "").strip()
            })

        syllabus_data["faqs"] = faqs

    data["syllabus_section"] = syllabus_data

    # ==============================
    # TYPES OF DISTANCE MBA COURSES SECTION
    # ==============================
    types_section = soup.find("section", id="chp_section_topratecourses")
    types_data = {}

    if types_section:

        # Section Title
        title = types_section.find("h2")
        types_data["title"] = title.get_text(strip=True) if title else None

        content_block = types_section.select_one(".wikkiContents")

        # Intro Paragraphs
        intro_paras = []
        if content_block:
            for p in content_block.select("p"):
                text = p.get_text(" ", strip=True)
                if text and "Source:" not in text:
                    intro_paras.append(text)
        
        types_data["description"] = intro_paras
        
        # ==============================
        # TYPES TABLE
        # ==============================
        courses = []
        table = content_block.find("table") if content_block else None

        if table:
            rows = table.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    course = {
                        "course_name": cols[0].get_text(" ", strip=True),
                        "course_url": cols[0].find("a")["href"] if cols[0].find("a") else None,
                        "duration": cols[1].get_text(" ", strip=True),
                        "details": cols[2].get_text(" ", strip=True)
                    }
                    courses.append(course)

        types_data["course_types"] = courses

        # ==============================
        # POPULAR COURSES BOX
        # ==============================
        popular_courses = []
        popular_box = types_section.select_one(".specialization-box")

        if popular_box:
            for li in popular_box.select("ul.specialization-list li"):
                name_tag = li.find("strong")
                course_link = li.find("a")

                offered_by = None
                offered_link = None
                offered_tag = li.find("label", class_="grayLabel")
                if offered_tag:
                    offered_anchor = offered_tag.find_parent("a")
                    if offered_anchor:
                        offered_by = offered_anchor.get_text(" ", strip=True).replace("Offered By", "").strip()
                        offered_link = offered_anchor["href"]

                rating = li.select_one(".rating-block")
                reviews = li.select_one("a.view_rvws")

                popular_courses.append({
                    "course_name": name_tag.get_text(strip=True) if name_tag else None,
                    "course_url": course_link["href"] if course_link else None,
                    "offered_by": offered_by,
                    "offered_by_url": offered_link,
                    "rating": rating.get_text(strip=True) if rating else None,
                    "reviews": reviews.get_text(strip=True) if reviews else None,
                    "reviews_url": reviews["href"] if reviews else None
                })

        types_data["popular_courses"] = popular_courses

        # ==============================
        # FAQs
        # ==============================
        faqs = []
        faq_questions = types_section.select(".sectional-faqs > div.html-0")
        faq_answers = types_section.select(".sectional-faqs > div._16f53f")

        for q, a in zip(faq_questions, faq_answers):
            faqs.append({
                "question": q.get_text(" ", strip=True).replace("Q:", "").strip(),
                "answer": a.get_text(" ", strip=True).replace("A:", "").strip()
            })

        types_data["faqs"] = faqs

    data["types_of_distance_mba_courses"] = types_data

    # POPULAR COLLEGES SECTION
    # ==============================
    popular_colleges_section = soup.find("section", id="chp_section_popularcolleges")
    popular_colleges_data = {}
    
    if popular_colleges_section:
    
        # Section title
        title = popular_colleges_section.find("h2")
        popular_colleges_data["title"] = title.get_text(strip=True) if title else None
    
        content_block = popular_colleges_section.select_one(".wikkiContents")
    
        # ------------------------------
        # Description Paragraphs
        # ------------------------------
        description = []
        if content_block:
            for p in content_block.select("p"):
                text = p.get_text(" ", strip=True)
                if text and "Source:" not in text:
                    description.append(text)
    
        popular_colleges_data["description"] = description
    
        # ------------------------------
        # Tables (Private + Government)
        # ------------------------------
        tables = content_block.find_all("table") if content_block else []
    
        private_colleges = []
        government_colleges = []
    
        # ✅ First table → Private colleges
        if len(tables) >= 1:
            rows = tables[0].find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    link = cols[0].find("a")
                    private_colleges.append({
                        "college_name": cols[0].get_text(" ", strip=True),
                        "college_url": link["href"] if link else None,
                        "total_fees": cols[1].get_text(" ", strip=True)
                    })
    
        # ✅ Second table → Government colleges
        if len(tables) >= 2:
            rows = tables[1].find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    link = cols[0].find("a")
                    government_colleges.append({
                        "college_name": cols[0].get_text(" ", strip=True),
                        "college_url": link["href"] if link else None,
                        "fees": cols[1].get_text(" ", strip=True)
                    })
    
        popular_colleges_data["private_colleges"] = private_colleges
        popular_colleges_data["government_colleges"] = government_colleges
    
        # ------------------------------
        # YouTube Video
        # ------------------------------
        iframe = popular_colleges_section.select_one(".vcmsEmbed iframe")
        popular_colleges_data["youtube_video"] = iframe.get("src") if iframe else None
    
    data["popular_colleges_section"] = popular_colleges_data
    
    # ==============================
    # SALARY & CAREER SECTION
    # ==============================
    salary_section = soup.find("section", id="chp_section_salary")
    salary_data = {}

    if salary_section:

        # ------------------------------
        # Title
        # ------------------------------
        title = salary_section.find("h2")
        salary_data["title"] = title.get_text(strip=True) if title else None

        content_block = salary_section.select_one(".wikkiContents")

        description = []

        if content_block:
            for elem in content_block.find_all("p"):  # recursive=True by default
                text = elem.get_text(" ", strip=True)
                if text and "Source:" not in text:
                    description.append(text)

        salary_data["description"] = description
        
        # ------------------------------
        # Tables
        # ------------------------------
        tables = content_block.find_all("table") if content_block else []

        # ✅ Table 1: Employment Areas
        employment_areas = []
        if len(tables) >= 1:
            rows = tables[0].find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    employment_areas.append({
                        "area": cols[0].get_text(" ", strip=True),
                        "description": cols[1].get_text(" ", strip=True)
                    })

        salary_data["employment_areas"] = employment_areas

        # ✅ Table 2: Job Profiles & Salary
        salary_profiles = []
        if len(tables) >= 2:
            rows = tables[1].find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    salary_profiles.append({
                        "job_profile": cols[0].get_text(" ", strip=True),
                        "average_salary": cols[1].get_text(" ", strip=True)
                    })

        salary_data["salary_profiles"] = salary_profiles

        # ✅ Table 3: Top Recruiters
        top_recruiters = []
        if len(tables) >= 3:
            rows = tables[2].find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                for col in cols:
                    name = col.get_text(" ", strip=True)
                    if name:
                        top_recruiters.append(name)

        salary_data["top_recruiters"] = top_recruiters

        faqs = []

        faq_questions = salary_section.select(".sectional-faqs > .listener")

        for q in faq_questions:
            question = q.get_text(" ", strip=True).replace("Q:", "").strip()

            answer_container = q.find_next_sibling("div", class_="_16f53f")
            answer = None

            if answer_container:
                answer_content = answer_container.select_one(".cmsAContent")
                if answer_content:
                    answer = answer_content.get_text(" ", strip=True)

            if question and answer:
                faqs.append({
                    "question": question,
                    "answer": answer
                })

        salary_data["faqs"] = faqs

    data["salary_section"] = salary_data

    return data

def scrape_online_mba_overview(driver):

    driver.get(PCOMBA_C_URL)
    time.sleep(3)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')


    section = soup.find("section", id="chp_courses_overview")
    data = {}

    title = soup.find("div",class_="a54c")
    h1 = title.text.strip()
    data["title"] = h1
    # Updated Date
    updated_div = section.select_one(".f48b div span")
    data["updated_on"] = updated_div.get_text(strip=True) if updated_div else None

    # Author Info
    author_block = section.select_one(".be8c p._7417 a")
    author_role = section.select_one(".be8c p._7417 span.b0fc")
    data["author"] = {
        "name": author_block.get_text(strip=True) if author_block else None,
        "profile_url": author_block["href"] if author_block else None,
        "role": author_role.get_text(strip=True) if author_role else None
    }

    # Main content
    content_div = section.find("div", class_="wikkiContents")
    data["content"] = []

    for elem in content_div.find_all(
        ["h2", "p", "ul", "ol", "table"], recursive=True
    ):
        if elem.name == "h2":
            data["content"].append({
                "type": "heading",
                "text": elem.get_text(strip=True)
            })

        elif elem.name == "p":
            data["content"].append({
                "type": "paragraph",
                "text": elem.get_text(" ", strip=True)
            })

        elif elem.name == "ul":
            items = [li.get_text(strip=True) for li in elem.find_all("li")]
            data["content"].append({
                "type": "unordered_list",
                "items": items
            })

        elif elem.name == "ol":
            items = [li.get_text(strip=True) for li in elem.find_all("li")]
            data["content"].append({
                "type": "ordered_list",
                "items": items
            })

        elif elem.name == "table":
            table_data = []
            for row in elem.find_all("tr"):
                cols = [col.get_text(" ", strip=True) for col in row.find_all(["td", "th"])]
                if cols:
                    table_data.append(cols)

            data["content"].append({
                "type": "table",
                "rows": table_data
            })

    return data

def scrape_online_mba_syllabus(driver):
    driver.get(PCOMBA_S_URL)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    syllabus_data = {
        "years": []
    }

    current_year = None
    current_semester = None

    for elem in soup.find_all(["h2", "h3", "table"]):

        # -------- YEAR --------
        if elem.name == "h2":
            current_year = {
                "year_title": elem.get_text(strip=True),
                "semesters": []
            }
            syllabus_data["years"].append(current_year)

        # -------- SEMESTER --------
        elif elem.name == "h3" and current_year:
            current_semester = {
                "semester_title": elem.get_text(strip=True),
                "papers": []
            }
            current_year["semesters"].append(current_semester)

        # -------- TABLE --------
        elif elem.name == "table" and current_semester:
            rows = elem.find_all("tr")
            current_paper = None
            paper_found = False

            for row in rows:
                cols = row.find_all("td")

                # ===== SEM 3+ FORMAT (Paper row) =====
                if len(cols) == 1 and cols[0].has_attr("colspan"):
                    paper_found = True
                    current_paper = {
                        "paper_title": cols[0].get_text(strip=True),
                        "units": []
                    }
                    current_semester["papers"].append(current_paper)

                elif paper_found and len(cols) == 2 and current_paper:
                    unit = cols[0].get_text(strip=True)
                    topics = [li.get_text(strip=True) for li in cols[1].find_all("li")]

                    if not topics:
                        topics = [p.get_text(strip=True) for p in cols[1].find_all("p")]

                    current_paper["units"].append({
                        "unit": unit,
                        "topics": topics
                    })

            # ===== SEM 1 & 2 FORMAT =====
            if not paper_found:
                for row in rows[1:]:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        current_semester["papers"].append({
                            "paper_title": cols[0].get_text(strip=True),
                            "topics": [
                                li.get_text(strip=True)
                                for li in cols[1].find_all("li")
                            ]
                        })

    return syllabus_data

def scrape_jobs_overview_section(driver):
    driver.get(PCOMBA_JOB_URL)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    section = soup.find("section", id="chp_jobs_overview")
    if not section:
        return {}

    data = {}
    title = soup.find("div",class_="a54c")
    data["title"]=title.text.strip()
    # ---------------- META ----------------
    meta = section.find("div", class_="f48b")
    if meta:
        span = meta.find("span")
        data["updated_on"] = span.get_text(strip=True) if span else None

        author = meta.find("a")
        data["author"] = author.get_text(strip=True) if author else None

        spans = meta.find("span",class_="b0fc")
        data["designation"] = spans.get_text(strip=True) if author else None


    # ---------------- INTRO ----------------
    intro_div = section.find("div", id="wikkiContents_chp_jobs_overview_0")
    intro_p = intro_div.find("p") if intro_div else None
    data["intro"] = intro_p.get_text(" ", strip=True) if intro_p else None

    # ---------------- SECTIONS (HEADING + PARAGRAPH + DATA) ----------------
    sections = []

    # Utility to get paragraph below h2
    def get_paragraph(h2_tag):
        p = h2_tag.find_next_sibling("p")
        return p.get_text(" ", strip=True) if p else None

    # ---------------- JOB PROFILES ----------------
    job_h2 = section.find("h2", id="chp_jobs_toc_0")
    job_table = job_h2.find_next("table") if job_h2 else None
    job_profiles = {}
    current_cat = None

    if job_table:
        rows = job_table.find_all("tr")[1:]  # skip header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) == 2:
                current_cat = cols[0].get_text(" ", strip=True)
                role = cols[1].get_text(" ", strip=True)
                job_profiles[current_cat] = [role]
            elif len(cols) == 1 and current_cat:
                role = cols[0].get_text(" ", strip=True)
                job_profiles[current_cat].append(role)

    if job_h2:
        sections.append({
            "heading": job_h2.get_text(" ", strip=True),
            "paragraph": get_paragraph(job_h2),
            "data": job_profiles
        })

    # ---------------- AVERAGE SALARY ----------------
    salaries = []
    sal_h2 = section.find("h2", id="chp_jobs_toc_1")
    sal_table = sal_h2.find_next("table") if sal_h2 else None

    if sal_table:
        for row in sal_table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) == 2:
                salaries.append({
                    "job_profile": cols[0].get_text(strip=True),
                    "average_salary": cols[1].get_text(strip=True)
                })

    if sal_h2:
        sections.append({
            "heading": sal_h2.get_text(" ", strip=True),
            "paragraph": get_paragraph(sal_h2),
            "data": salaries
        })

    # ---------------- DEPARTMENTS ----------------
    depts = []
    dept_h2 = section.find("h2", id="chp_jobs_toc_2")
    dept_table = dept_h2.find_next("table") if dept_h2 else None

    if dept_table:
        for row in dept_table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) == 2:
                depts.append({
                    "department": cols[0].get_text(" ", strip=True),
                    "vacancies": cols[1].get_text(strip=True)
                })

    if dept_h2:
        sections.append({
            "heading": dept_h2.get_text(" ", strip=True),
            "paragraph": get_paragraph(dept_h2),
            "data": depts
        })

    # ---------------- JOB TIPS ----------------
    tips = []
    tips_h2 = section.find("h2", id="chp_jobs_toc_4")
    ol = tips_h2.find_next("ol") if tips_h2 else None

    if ol:
        for li in ol.find_all("li"):
            tips.append(li.get_text(" ", strip=True))

    if tips_h2:
        sections.append({
            "heading": tips_h2.get_text(" ", strip=True),
            "paragraph": get_paragraph(tips_h2),
            "tips": tips
        })

    data["sections"] = sections

    return data

def scrape_admission_overview_section(driver):
    driver.get(PCOMBA_ADDMISSION_URL)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # HTML में div id "wikkiContents_chp_admission_overview_0" है
    section = soup.find("div", id="wikkiContents_chp_admission_overview_0")
    if not section:
        return {}

    data = {}
    
    # Title (शीर्षक)
    title_element = section.find("h2", id="chp_admission_toc_0")
    data["title"] = title_element.get_text(strip=True) if title_element else "Online MBA Admission"
    
    # ---------------- META INFORMATION ----------------
    data["updated_on"] = None
    data["author"] = None
    data["designation"] = None
    
    # ---------------- INTRODUCTION TEXT ----------------
    introduction_text = []
    paragraphs = section.find_all("p", style="text-align: justify;")
    
    # पहले 3 paragraphs जो introduction के हैं
    for i, p in enumerate(paragraphs[:3]):
        intro_text = p.get_text(strip=True)
        introduction_text.append(intro_text)
    
    data["introduction"] = introduction_text
    
    # ---------------- LATEST UPDATES ----------------
    latest_updates = []
    
    # Latest Updates section ढूंढना
    for p in section.find_all("p"):
        span = p.find("span", style="color: #e03e2d;")
        if span and "Online MBA Latest Updates:" in span.get_text():
            updates_list = p.find_next("ul")
            if updates_list:
                for li in updates_list.find_all("li"):
                    update_text = li.get_text(strip=True)
                    latest_updates.append(update_text)
            break
    
    data["latest_updates"] = latest_updates
    
    # ---------------- IIMS ADMISSION TABLE ----------------
    iim_admissions = []
    
    # IIMs section ढूंढना
    iim_heading = section.find("h3", id="chp_admission_toc_0_0")
    if iim_heading:
        iim_table = iim_heading.find_next("table")
        if iim_table:
            rows = iim_table.find_all("tr")[1:]  # Header row skip
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    # Institute name और link
                    institute_cell = cols[0]
                    institute_name = institute_cell.get_text(strip=True)
                    
                    institute_link = None
                    link_tag = institute_cell.find("a")
                    if link_tag:
                        institute_link = link_tag.get("href")
                    
                    # Exams accepted
                    exams_cell = cols[1]
                    exams_accepted = exams_cell.get_text(strip=True)
                    
                    # Application status
                    status_cell = cols[2]
                    application_status = status_cell.get_text(strip=True)
                    
                    iim_data = {
                        "institute": institute_name,
                        "institute_link": institute_link,
                        "exams_accepted": exams_accepted,
                        "application_status": application_status,
                        "type": "IIM"
                    }
                    iim_admissions.append(iim_data)
    
    data["iim_admissions"] = iim_admissions
    
    # ---------------- GOVERNMENT COLLEGES TABLE ----------------
    government_colleges = []
    
    # Government colleges section ढूंढना
    govt_heading = section.find("h2", id="chp_admission_toc_1")
    if govt_heading:
        govt_table = govt_heading.find_next("table")
        if govt_table:
            rows = govt_table.find_all("tr")[1:]  # Header row skip
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    # College name और link
                    college_cell = cols[0]
                    college_name = college_cell.get_text(strip=True)
                    
                    college_link = None
                    link_tag = college_cell.find("a")
                    if link_tag:
                        college_link = link_tag.get("href")
                    
                    # Exams accepted
                    exams_cell = cols[1]
                    exams_accepted = exams_cell.get_text(strip=True)
                    
                    # Application status
                    status_cell = cols[2]
                    application_status = status_cell.get_text(strip=True)
                    
                    # Status link
                    status_link = None
                    status_link_tag = status_cell.find("a")
                    if status_link_tag:
                        status_link = status_link_tag.get("href")
                    
                    govt_data = {
                        "name": college_name,
                        "college_link": college_link,
                        "exams_accepted": exams_accepted,
                        "application_status": application_status,
                        "status_link": status_link,
                        "type": "Government"
                    }
                    government_colleges.append(govt_data)
    
    data["government_colleges"] = government_colleges
    
    # ---------------- PRIVATE COLLEGES TABLE ----------------
    private_colleges = []
    
    # Private colleges section ढूंढना
    private_heading = section.find("h2", id="chp_admission_toc_2")
    if private_heading:
        private_table = private_heading.find_next("table")
        if private_table:
            rows = private_table.find_all("tr")[1:]  # Header row skip
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    # College name और link
                    college_cell = cols[0]
                    college_name = college_cell.get_text(strip=True)
                    
                    college_link = None
                    link_tag = college_cell.find("a")
                    if link_tag:
                        college_link = link_tag.get("href")
                    
                    # Exams accepted
                    exams_cell = cols[1]
                    exams_accepted = exams_cell.get_text(strip=True)
                    
                    # Application status
                    status_cell = cols[2]
                    application_status = status_cell.get_text(strip=True)
                    
                    # Status link
                    status_link = None
                    status_link_tag = status_cell.find("a")
                    if status_link_tag:
                        status_link = status_link_tag.get("href")
                    
                    private_data = {
                        "name": college_name,
                        "college_link": college_link,
                        "exams_accepted": exams_accepted,
                        "application_status": application_status,
                        "status_link": status_link,
                        "type": "Private"
                    }
                    private_colleges.append(private_data)
    
    data["private_colleges"] = private_colleges
    
    # ---------------- ALSO READ LINKS ----------------
    also_read_links = []
    
    # Also Read section ढूंढना
    for p in section.find_all("p"):
        span = p.find("span", style="color: #e03e2d;")
        if span and "Also Read:" in span.get_text():
            # अगले paragraphs से links extract करना
            next_elem = p.find_next_sibling()
            while next_elem and next_elem.name == "p":
                link_tag = next_elem.find("a")
                if link_tag:
                    link_text = link_tag.get_text(strip=True)
                    link_url = link_tag.get("href")
                    also_read_links.append({
                        "text": link_text,
                        "url": link_url
                })
                next_elem = next_elem.find_next_sibling()
            break
    
    data["also_read_links"] = also_read_links
    
    # ---------------- QUICK LINKS TABLE ----------------
    quick_links = []
    
    # Quick Links section ढूंढना
    for p in section.find_all("p"):
        span = p.find("span", style="color: #e03e2d;")
        if span and "Quick Links:" in span.get_text():
            quick_table = p.find_next("table")
            if quick_table:
                rows = quick_table.find_all("tr")
                for row in rows:
                    links = row.find_all("a")
                    for link in links:
                        link_text = link.get_text(strip=True)
                        link_url = link.get("href")
                        quick_links.append({
                            "text": link_text,
                            "url": link_url
                        })
            break
    
    data["quick_links"] = quick_links
    
    # ---------------- SECTION TEXT CONTENT ----------------
    section_content = []
    
    # पहले H2 के बाद के paragraphs
    main_heading = section.find("h2", id="chp_admission_toc_0")
    if main_heading:
        next_elem = main_heading.find_next_sibling()
        while next_elem:
            if next_elem.name == "p" and next_elem.get("style") == "text-align: justify;":
                section_content.append(next_elem.get_text(strip=True))
            elif next_elem.name in ["h3", "h2"]:
                break
            next_elem = next_elem.find_next_sibling()
    
    data["section_content"] = section_content
    
    # ---------------- ADDITIONAL SECTIONS TEXT ----------------
    # Government colleges के पहले paragraph
    govt_section_text = []
    if govt_heading:
        next_elem = govt_heading.find_next_sibling()
        while next_elem:
            if next_elem.name == "p" and next_elem.get("style") == "text-align: justify;":
                govt_section_text.append(next_elem.get_text(strip=True))
            elif next_elem.name == "table":
                break
            next_elem = next_elem.find_next_sibling()
    
    # Private colleges के पहले paragraph
    private_section_text = []
    if private_heading:
        next_elem = private_heading.find_next_sibling()
        while next_elem:
            if next_elem.name == "p" and next_elem.get("style") == "text-align: justify;":
                private_section_text.append(next_elem.get_text(strip=True))
            elif next_elem.name == "table":
                break
            next_elem = next_elem.find_next_sibling()
    
    data["government_section_text"] = govt_section_text
    data["private_section_text"] = private_section_text
    
    # ---------------- IIM SECTION TEXT ----------------
    iim_section_text = []
    if iim_heading:
        next_elem = iim_heading.find_next_sibling()
        while next_elem:
            if next_elem.name == "p" and next_elem.get("style") == "text-align: justify;":
                iim_section_text.append(next_elem.get_text(strip=True))
            elif next_elem.name == "table":
                break
            next_elem = next_elem.find_next_sibling()
    
    data["iim_section_text"] = iim_section_text

    
    
    return data

def scrape_shiksha_qa(driver):
    driver.get(PCOMBA_Q_URL)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.post-col[questionid][answerid][type='Q']"))
        )
    except:
        print("No Q&A blocks loaded!")
        return {}

    soup = BeautifulSoup(driver.page_source, "html.parser")

    result = {
        "tag_name": None,
        "description": None,
        "stats": {},
        "questions": []
    }

    # Optional: get tag name & description if exists
    tag_head = soup.select_one("div.tag-head")
    if tag_head:
        tag_name_el = tag_head.select_one("h1.tag-p")
        desc_el = tag_head.select_one("p.tag-bind")
        if tag_name_el:
            result["tag_name"] = tag_name_el.get_text(strip=True)
        if desc_el:
            result["description"] = desc_el.get_text(" ", strip=True)

    # Stats
    stats_cells = soup.select("div.ana-table div.ana-cell")
    stats_keys = ["Questions", "Discussions", "Active Users", "Followers"]
    for key, cell in zip(stats_keys, stats_cells):
        count_tag = cell.select_one("b")
        if count_tag:
            value = count_tag.get("valuecount") or count_tag.get_text(strip=True)
            result["stats"][key] = value

    questions_dict = {}

    for post in soup.select("div.post-col[questionid][answerid][type='Q']"):
        q_text_el = post.select_one("div.dtl-qstn .wikkiContents")
        if not q_text_el:
            continue
        question_text = q_text_el.get_text(" ", strip=True)

        # Tags
        tags = [{"tag_name": a.get_text(strip=True), "tag_url": a.get("href")}
                for a in post.select("div.ana-qstn-block .qstn-row a")]

        # Followers
        followers_el = post.select_one("span.followersCountTextArea")
        followers = int(followers_el.get("valuecount", "0")) if followers_el else 0

        # Author
        author_el = post.select_one("div.avatar-col .avatar-name")
        author_name = author_el.get_text(strip=True) if author_el else None
        author_url = author_el.get("href") if author_el else None

        # Answer text
        answer_el = post.select_one("div.avatar-col .rp-txt .wikkiContents")
        answer_text = answer_el.get_text(" ", strip=True) if answer_el else None

        # Upvotes / downvotes
        upvote_el = post.select_one("a.up-thumb.like-a")
        downvote_el = post.select_one("a.up-thumb.like-d")
        upvotes = int(upvote_el.get_text(strip=True)) if upvote_el and upvote_el.get_text(strip=True).isdigit() else 0
        downvotes = int(downvote_el.get_text(strip=True)) if downvote_el and downvote_el.get_text(strip=True).isdigit() else 0

        # Posted time (if available)
        time_el = post.select_one("div.col-head span")
        posted_time = time_el.get_text(strip=True) if time_el else None

        # Group by question
        if question_text not in questions_dict:
            questions_dict[question_text] = {
                "tags": tags,
                "followers": followers,
                "answers": []
            }
        questions_dict[question_text]["answers"].append({
            "author": {"name": author_name, "profile_url": author_url},
            "answer_text": answer_text,
            "upvotes": upvotes,
            "downvotes": downvotes,
            "posted_time": posted_time
        })

    # Convert dict to list
    for q_text, data in questions_dict.items():
        result["questions"].append({
            "question_text": q_text,
            "tags": data["tags"],
            "followers": data["followers"],
            "answers": data["answers"]
        })

    return result


def scrape_tag_cta_D_block(driver):
    driver.get(PCOMBA_QD_URL)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    result = {
        "questions": []  # store all Q&A and discussion blocks
    }

    # Scrape all Q&A and discussion blocks
    qa_blocks = soup.select("div.post-col[questionid][answerid][type='Q'], div.post-col[questionid][answerid][type='D']")
    for block in qa_blocks:
        block_type = block.get("type", "Q")
        qa_data = {
          
            "posted_time": None,
            "tags": [],
            "question_text": None,
            "followers": 0,
            "views": 0,
            "author": {
                "name": None,
                "profile_url": None,
            },
            "answer_text": None,
        }

        # Posted time
        posted_span = block.select_one("div.col-head span")
        if posted_span:
            qa_data["posted_time"] = posted_span.get_text(strip=True)

        # Tags
        tag_links = block.select("div.ana-qstn-block div.qstn-row a")
        for a in tag_links:
            qa_data["tags"].append({
                "tag_name": a.get_text(strip=True),
                "tag_url": a.get("href")
            })

        # Question / Discussion text
        question_div = block.select_one("div.dtl-qstn a div.wikkiContents")
        if question_div:
            qa_data["question_text"] = question_div.get_text(" ", strip=True)

        # Followers
        followers_span = block.select_one("span.followersCountTextArea, span.follower")
        if followers_span:
            qa_data["followers"] = int(followers_span.get("valuecount", "0"))

        # Views
        views_span = block.select_one("div.right-cl span.viewers-span")
        if views_span:
            views_text = views_span.get_text(strip=True).split()[0].replace("k","000").replace("K","000")
            try:
                qa_data["views"] = int(views_text)
            except:
                qa_data["views"] = views_text

        # Author info
        author_name_a = block.select_one("div.avatar-col a.avatar-name")
        if author_name_a:
            qa_data["author"]["name"] = author_name_a.get_text(strip=True)
            qa_data["author"]["profile_url"] = author_name_a.get("href")

        # Answer / Comment text
        answer_div = block.select_one("div.avatar-col div.wikkiContents")
        if answer_div:
            paragraphs = answer_div.find_all("p")
            if paragraphs:
                qa_data["answer_text"] = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
            else:
                # Sometimes discussion/comment text is direct text without <p>
                qa_data["answer_text"] = answer_div.get_text(" ", strip=True)

        result["questions"].append(qa_data)

    return result



def scrape_mba_colleges():
    driver = create_driver()

      

    try:
       data = {
              "Online MBA":{
                   "overviews":extract_overview_data(driver),
                "course":scrape_online_mba_overview(driver),
                "syllabus":scrape_online_mba_syllabus(driver),
                "JOB":scrape_jobs_overview_section(driver),
                "addmision":scrape_admission_overview_section(driver),
                "QA":{
                 "QA_ALL":scrape_shiksha_qa(driver),
                 "QA_D":scrape_tag_cta_D_block(driver),
                },
                
                   }
                }
       
       
        
        # data["overview"] =  overviews
        # data["courses"] = courses

    finally:
        driver.quit()
    
    return data



import time

DATA_FILE =  "distance_mba_data.json"
UPDATE_INTERVAL = 6 * 60 * 60  # 6 hours

def auto_update_scraper():
    # Check last modified time
    # if os.path.exists(DATA_FILE):
    #     last_mod = os.path.getmtime(DATA_FILE)
    #     if time.time() - last_mod < UPDATE_INTERVAL:
    #         print("⏱️ Data is recent, no need to scrape")
    #         return

    print("🔄 Scraping started")
    data = scrape_mba_colleges()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("✅ Data scraped & saved successfully")

if __name__ == "__main__":

    auto_update_scraper()

