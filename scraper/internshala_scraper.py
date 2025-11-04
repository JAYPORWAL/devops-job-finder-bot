import requests
from bs4 import BeautifulSoup

class InternshalaScraper:
    def __init__(self):
        self.base_url = "https://internshala.com/internships"

    def search(self, query):
        print(f"Scraping Internshala for {query} internships...")
        params = {"q": query, "location": "India"}
        response = requests.get(self.base_url, params=params, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        jobs = []
        listings = soup.select("div.individual_internship")

        for listing in listings:
            title_tag = listing.find("h3", class_="heading_4_5")
            company_tag = listing.find("p", class_="company_name")
            link_tag = listing.find("a", class_="view_detail_button")

            if not title_tag or not company_tag or not link_tag:
                continue

            title = title_tag.text.strip()
            company = company_tag.text.strip()
            link = "https://internshala.com" + link_tag["href"]

            jobs.append({
                "title": title,
                "company": company,
                "link": link,
                "source": "Internshala"
            })

        print(f"Found {len(jobs)} Internshala internships.")
        return jobs


if __name__ == "__main__":
    scraper = InternshalaScraper()
    results = scraper.search("DevOps")
    for job in results:
        print(job["title"], "-", job["company"], "-", job["link"])
