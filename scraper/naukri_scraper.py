import requests
from bs4 import BeautifulSoup

class NaukriScraper:
    def __init__(self):
        self.base_url = "https://www.naukri.com"

    def search(self, query):
        print(f"Scraping Naukri for {query} jobs...")
        query = query.replace(" ", "-")
        url = f"{self.base_url}/{query}-jobs"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        jobs = []
        listings = soup.find_all("article", class_="jobTuple")

        for listing in listings:
            title_tag = listing.find("a", class_="title")
            company_tag = listing.find("a", class_="subTitle")
            if not title_tag or not company_tag:
                continue

            link = title_tag["href"]
            title = title_tag.text.strip()
            company = company_tag.text.strip()

            jobs.append({
                "title": title,
                "company": company,
                "link": link,
                "source": "Naukri"
            })

        print(f"Found {len(jobs)} Naukri jobs.")
        return jobs


if __name__ == "__main__":
    scraper = NaukriScraper()  # ✅ make sure this is OUTSIDE the class
    results = scraper.search("DevOps")
    for job in results:
        print(job["title"], "-", job["company"], "-", job["link"])
