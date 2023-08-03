# import databutton as db
import streamlit as st
import re
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords
import urllib.robotparser
from urllib.parse import urlparse, urljoin
import pandas as pd


# Download NLTK data for stopwords
nltk.download("stopwords")
nltk.download("punkt")

# Functions


def is_url_indexable(url):
    # Parse the robots.txt file for the given URL
    rp = urllib.robotparser.RobotFileParser()
    robots_txt_url = f"{url.rstrip('/')}/robots.txt"

    try:
        rp.set_url(robots_txt_url)
        rp.read()
    except Exception as e:
        print(f"Error reading robots.txt: {e}")
        return False

    # Check if the URL is allowed to be indexed
    return rp.can_fetch("*", url)


def calculate_title_score(html_content, return_title=False):
    try:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        # Extract the page title
        title = (
            soup.title.string.strip().encode("latin-1").decode("utf-8")
            if soup.title
            else ""
        )

        # Calculate the score based on title length
        title_length = len(title)
        length_score = 0
        if 50 <= title_length <= 60:
            length_score = 50
        elif title_length > 60:
            length_score = max(0, int(50 - (title_length - 60)))
        else:
            length_score = min(50, int(50 * (title_length / 50)))

        # Calculate the score based on word reoccurrence
        content = soup.get_text().lower()
        words_in_title = [word.lower() for word in title.split()]
        stop_words = set(stopwords.words("english"))
        words_in_title = [word for word in words_in_title if word not in stop_words]
        word_reoccurrence_score = 0

        for word in words_in_title:
            if word in content:
                word_reoccurrence_score += 1

        word_reoccurrence_score = min(
            50, int(50 * word_reoccurrence_score / len(words_in_title))
        )
        total_score = length_score + word_reoccurrence_score

        return total_score, title if return_title else total_score
    except Exception as e:
        print(f"Error occurred while processing HTML: {e}")
        return 0, "" if return_title else 0


def calculate_description_score(html_content, return_description=False):
    try:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        # Extract the page description from the meta tag
        meta_description = soup.find("meta", attrs={"name": "description"})

        if meta_description and "content" in meta_description.attrs:
            description = (
                meta_description["content"].strip().encode("latin-1").decode("utf-8")
            )
        else:
            description = ""

        # Calculate the score based on title length
        description_length = len(description)
        length_score = 0
        if 150 <= description_length <= 160:
            length_score = 100
        elif description_length > 160:
            length_score = max(0, int(100 - abs(description_length - 160) / 160 * 100))
        else:
            length_score = min(100, int(100 * (description_length / 150)))

        return length_score, description if return_description else length_score
    except Exception as e:
        print(f"Error occurred while processing HTML: {e}")
        return 0, "" if return_description else 0


def has_self_referencing_canonical(html_content, url):
    try:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Find the canonical link element
        canonical_link = soup.find("link", {"rel": "canonical"})

        # If canonical_link is None, there is no canonical link, so return False
        if not canonical_link:
            return False

        # Get the href attribute of the canonical link
        canonical_url = canonical_link.get("href")

        # Compare the canonical URL with the current page URL
        return url == canonical_url
    except Exception as e:
        print(f"Error occurred while processing HTML from {url}: {e}")
        return False


def has_robot_meta_tag(html_content):
    try:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Find the robots meta tag
        robots_meta_tag = soup.find("meta", {"name": "robots"})

        # If robots_meta_tag is None, there is no robots meta tag, so return False
        if not robots_meta_tag:
            return False

        return True
    except Exception as e:
        print(f"Error occurred while processing HTML: {e}")
        return False


def has_x_robots_tag(headers):
    try:
        # Check if the X-Robots-Tag header is present in the response headers
        x_robots_tag = headers.get("X-Robots-Tag")

        return bool(x_robots_tag)
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while making the request to the URL: {e}")
        return False


def count_words_chatacters(html_content):
    try:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Get the text content from the page
        text_content = soup.get_text()

        # Tokenize the text into words using nltk's word_tokenize
        words = text_content.split(" ")

        # # Remove non-alphanumeric characters, punctuation, and convert to lowercase
        words = [re.sub(r"\W+", "", word.lower()) for word in words]

        # # Remove any empty or single-character words
        words = [word for word in words if len(word) > 1]

        # Load stop words for both English and Thai
        stop_words = set(stopwords.words("english"))

        # Filter out stop words
        words = [word for word in words if word not in stop_words]

        # Count the words and return the result
        word_count = len(words)
        return word_count, len("".join(words))

    except Exception as e:
        st.error(e)
        print(f"Error occurred while processing HTML: {e}")
        return 0

def find_images(html_content):
    try:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all occurrences of the <img> tag (images)
        img_tags = soup.find_all("img")

        # Initialize lists to store different types of image links
        total_image_links = []
        image_links_with_no_alt = []
        image_links_with_alt = []

        # Extract image links and check for alt attribute
        for img_tag in img_tags:
            image_link = img_tag.get("src")
            total_image_links.append(image_link)
            alt_text = img_tag.get("alt", "")
            if not alt_text:
                image_links_with_no_alt.append(image_link)
            else:
                image_links_with_alt.append(image_link)

        # Remove duplicates by converting to set and back to list
        total_image_links = list(set(total_image_links))
        image_links_with_no_alt = list(set(image_links_with_no_alt))
        image_links_with_alt = list(set(image_links_with_alt))

        return total_image_links, image_links_with_no_alt, image_links_with_alt

    except Exception as e:
        print(f"Error occurred while processing HTML: {e}")
        return [], [], []


def extract_headings(html_content):
    try:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Initialize a nested list to store the heading contents
        headings_list = [[] for _ in range(6)]

        # Find all occurrences of heading tags (h1 to h6)
        for i in range(1, 7):
            heading_tags = soup.find_all(f"h{i}")
            for heading_tag in heading_tags:
                # Extract the content of the heading tag and add it to the respective list
                heading_text = heading_tag.get_text().strip().encode("latin-1").decode("utf-8")
                headings_list[i - 1].append(heading_text)

        # Count the total number of heading tags
        # total_headings = sum(len(heading_list) for heading_list in headings_list)

        return headings_list

    except Exception as e:
        print(f"Error occurred while processing HTML: {e}")
        return [[], [], [], [], [], []]



def find_links(html_content, url):
    try:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all occurrences of the <a> tag (links)
        link_tags = soup.find_all("a")

        # Get the base URL from the input URL
        base_url = urlparse(url).scheme + "://" + urlparse(url).netloc

        # Initialize lists to store different types of links
        all_links = []
        internal_links = []
        external_links = []

        # Extract links from link tags
        for link_tag in link_tags:
            link = link_tag.get("href")
            if link:
                absolute_link = urljoin(base_url, link)  # Convert to absolute URL
                all_links.append(absolute_link)
                if base_url in absolute_link:
                    internal_links.append(absolute_link)
                else:
                    external_links.append(absolute_link)

        # Remove duplicates by converting to set and back to list
        unique_links = list(set(all_links))

        return all_links, internal_links, external_links, unique_links

    except Exception as e:
        print(f"Error occurred while processing HTML: {e}")
        return [], [], [], []



def is_valid_url(input_text):
    # Regular expression pattern to match a URL link
    url_pattern = re.compile(
        r"^(https?://)?"  # Match http or https (optional)
        r"([\da-z.-]+)\.([a-z.]{2,6})"  # Match domain name
        r"(:\d{1,5})?"  # Match port number (optional)
        r"(/[\w .-]*)*"  # Match path (optional)
        r"(\?[&=\w.-]*)?"  # Match query string (optional)
        r"(#\w*)?$",  # Match anchor (optional)
        re.IGNORECASE,
    )

    return bool(url_pattern.match(input_text))


def get_html_from_url(url, return_headers=False):
    try:
        # Send an HTTP GET request to the specified URL
        response = requests.get(url)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Return the HTML content of the page
            return response.text, response.headers if return_headers else response.text

        else:
            print(f"Request failed with status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
    return None, None if return_headers else None


# MAIN app

website_url = st.text_input("URL", placeholder="https://www.example.com/")
if is_valid_url(website_url):
    with st.spinner("กำลังโหลด content..."):
        html_content, headers = get_html_from_url(website_url, return_headers=True)
    if html_content:
        overview_tab, headings_tab, links_tab, images_tab = st.tabs(
            ["Overview", "Headings", "Links", "Images"]
        )
        with overview_tab:
            title_score, title = calculate_title_score(html_content, return_title=True)
            st.metric(
                label="Title Score (เต็ม 100 คะแนน):",
                value=title_score,
                delta_color="off",
                help="แท็ก Title ใน HTML เป็นปัจจัยสำคัญในการเพิ่ม SEO ของหน้าเว็บ ควรสะท้อนถึงเนื้อหาของหน้าอย่างถูกต้องและรวม keyword ที่เกี่ยวข้องภายในความยาวที่แนะนำคือ 50-60 ตัวอักษร",
            )
            if 50 <= len(title) <= 60:
                st.success(f"Title: {title}\n\nความยาว {len(title)} ตัวอักษร")
            else:
                st.warning(f"Title: {title}\n\nความยาว {len(title)} ตัวอักษร")

            description_score, description = calculate_description_score(
                html_content, return_description=True
            )
            st.metric(
                label="Description Score (เต็ม 100 คะแนน):",
                value=description_score,
                delta_color="off",
                help="แท็ก description ใน HTML ให้ข้อมูลสรุปสั้นๆ เกี่ยวกับเนื้อหาของหน้าเว็บ ปรากฏในผลลัพธ์ของเครื่องมือค้นหาภายใต้ชื่อหน้าและ URL Description ที่เขียนอย่างดีสามารถปรับปรุงอัตราการคลิกผ่านโดยล่อลวงให้ผู้ใช้คลิกที่ผลลัพธ์",
            )
            if 150 <= len(title) <= 160:
                st.success(
                    f"Description: {description}\n\nความยาว {len(description)} ตัวอักษร"
                )
            else:
                st.warning(
                    f"Description: {description}\n\nความยาว {len(description)} ตัวอักษร"
                )
            st.caption(
                "URL",
                help="URL ของหน้าเว็บคือที่อยู่ที่สามารถพบได้บนอินเทอร์เน็ต ควรสั้น อธิบาย และมี keyword ที่เกี่ยวข้อง",
            )
            if is_url_indexable(website_url):
                st.success(f"URL ของคุณ Index ได้ 👍")
            else:
                st.error(
                    f"robots.txt ของ website ของคุณ ไม่มี disallow directives\n\nไฟล์ robots.txt เป็นมาตรฐานของเว็บไซต์ใช้เพื่อสื่อสารกับโปรแกรมรวบรวมข้อมูลเว็บและเครื่องมือค้นหา โดยระบุว่าส่วนใดของเว็บไซต์ไม่ควรได้รับการรวบรวมข้อมูลหรือจัดทำ index ใน search engine"
                )

            st.caption(
                "Canonical",
                help="แท็ก Canonical ใน HTML ระบุเวอร์ชันที่ต้องการของหน้าเว็บสำหรับเครื่องมือค้นหา ช่วยป้องกันปัญหาเนื้อหาที่ซ้ำกันโดยบอกเครื่องมือค้นหาว่า URL ใดที่จะจัด index ในผลการค้นหา",
            )
            if has_self_referencing_canonical(html_content, website_url):
                st.success(f"เว็บของคุณมี canonical tag👍")
            else:
                st.error(f"เว็บของคุณไม่มี canonical tag 🔴")

            col1, col2 = st.columns(2)
            with col1:
                st.caption(
                    "Robots",
                    help="เมตาแท็ก Robot ใน HTML จะบอกเครื่องมือค้นหาเกี่ยวกับวิธีรวบรวมข้อมูลและจัดทำ index ของหน้าเว็บ สามารถใช้เพื่อป้องกันไม่ให้เครื่องมือค้นหาจัดทำ index หน้าหรือเพื่อป้องกันไม่ให้เครื่องมือค้นหาติดตามลิงก์ที่ไม่จำเป็นบนหน้าเว็บ",
                )
                if has_robot_meta_tag(html_content):
                    st.info(f"เว็บของคุณมี Robots tag")
                else:
                    st.info(
                        f"เว็บของคุณไม่มี Robots tag\n\nไฟล์ robots.txt เป็นมาตรฐานของเว็บไซต์ใช้เพื่อสื่อสารกับโปรแกรมรวบรวมข้อมูลเว็บและเครื่องมือค้นหา โดยระบุว่าส่วนใดของเว็บไซต์ไม่ควรได้รับการรวบรวมข้อมูลหรือจัดทำ index ใน search engine"
                    )
                st.caption("จำนวนคำ")
                words_count, characters_count = count_words_chatacters(html_content)
                st.info(words_count)
            with col2:
                st.caption(
                    "X Robots tag",
                    help="ส่วนหัวการตอบสนอง HTTP ของ X-Robots-Tag ใน HTML จะบอกเครื่องมือค้นหาเกี่ยวกับวิธีรวบรวมข้อมูลและจัดทำ index ของหน้าเว็บ สามารถใช้เพื่อป้องกันไม่ให้เครื่องมือค้นหาจัดทำ index ของหน้าที่ไม่จำเป็น หรือเพื่อป้องกันไม่ให้เครื่องมือค้นหาติดตามลิงก์บนหน้า",
                )
                if has_x_robots_tag(headers):
                    st.info(f"เว็บของคุณมี X Robots tag")
                else:
                    st.info(f"เว็บของคุณไม่มี X Robots tag")
                st.caption("จำนวนตัวอักษร")
                st.info(characters_count)

            col1, col2, col3, col4 = st.columns(4)
            headings_list = extract_headings(html_content)
            with col1:
                st.caption("H1")
                st.info(len(headings_list[0]))
                st.caption("H5")
                st.info(len(headings_list[4]))
                
            with col2:
                st.caption("H2")
                st.info(len(headings_list[1]))
                st.caption("H6")
                st.info(len(headings_list[5]))
            with col3:
                st.caption("H3")
                st.info(len(headings_list[2]))
                st.caption("จำนวนรูป")
                image_links, image_links_with_no_alt, image_links_with_alt = find_images(html_content)
                st.info(len(image_links))
            with col4:
                st.caption("H4")
                st.info(len(headings_list[3]))
                st.caption("จำนวนลิงค์")
                all_links, internal_links, external_links, unique_links = find_links(html_content, website_url)
                st.info(len(all_links))

        with headings_tab:
            st.subheader("H1", anchor=False)
            if headings_list[0]:
                for heading in headings_list[0]:
                    st.caption(heading)
            else:
                st.warning("ไม่มี H1")
            st.subheader("H2", anchor=False)
            if headings_list[1]:
                for heading in headings_list[1]:
                    st.caption(heading)
            else:
                st.warning("ไม่มี H2")
            st.subheader("H3", anchor=False)
            if headings_list[2]:
                for heading in headings_list[2]:
                    st.caption(heading)
            else:
                st.info("ไม่มี H3")
            st.subheader("H4", anchor=False)
            if headings_list[3]:
                for heading in headings_list[3]:
                    st.caption(heading)
            else:
                st.info("ไม่มี H4")
            st.subheader("H5", anchor=False)
            if headings_list[4]:
                for heading in headings_list[4]:
                    st.caption(heading)
            else:
                st.info("ไม่มี H5")
            st.subheader("H6", anchor=False)
            if headings_list[5]:
                for heading in headings_list[5]:
                    st.caption(heading)
            else:
                st.info("ไม่มี H6")

        with links_tab:
            all_links_tab, internal_links_tab, external_links_tab, unique_links_tab = st.tabs(["All Links", "Internal Links", "External Links", "Unique Links"])

            with all_links_tab:
                for link in all_links:
                    st.markdown(f"[{link}]({link})")
            with internal_links_tab:
                for link in internal_links:
                    st.markdown(f"[{link}]({link})")
            with external_links_tab:
                for link in external_links:
                    st.markdown(f"[{link}]({link})")
            with unique_links_tab:
                for link in unique_links:
                    st.markdown(f"[{link}]({link})")
        with images_tab:
            image_links_tab, images_no_alt, images_with_alt = st.tabs(["Image Links", "Images with no Alt", "Images with Alt"])
            with image_links_tab:
                for link in image_links:
                    st.markdown(f"[{link}]({link})")
            with images_no_alt:
                for link in image_links_with_no_alt:
                    st.markdown(f"[{link}]({link})")
            with images_with_alt:
                for link in image_links_with_alt:
                    st.markdown(f"[{link}]({link})")

    else:
        st.error("Failed to retrieve HTML content.")
else:
    st.subheader("โปรดใส่ Link URL ☝️ และกด Enter",anchor=False)