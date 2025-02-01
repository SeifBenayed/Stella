from playwright.sync_api import sync_playwright
import time
from PIL import Image
import os
from utils.file_utils import FileUtils
from llms.llm import anthropic_supported_models


class WebCrawler:

    def __init__(self, llm_id):
        # Set tmp_folder environment variable
        if not os.getenv("tmp_folder"):
            os.environ["tmp_folder"] = os.path.join(os.getcwd(), "tmp_folder")
            tmp_folder = os.environ["tmp_folder"]
            os.makedirs(tmp_folder)
        else:
            tmp_folder = os.environ["tmp_folder"]

        self.file_utils = FileUtils(tmp_folder)
        self.llm_id = llm_id
        self.links = []
        self.mode = os.getenv("crawl_mode")


    def compress_image(self):
        img = Image.open(self.file_utils.screenshot_path)
        img_w, img_h = img.size
        img = img.crop([0,0, img_w, img_h//3])
        img.save(self.file_utils.screenshot_path, "png")


    def get_links(self, page):
        self.links = page.evaluate('''() => {
                    const anchorElements = Array.from(document.querySelectorAll('a'));
                    return anchorElements.map(anchor => anchor.href);
                }''')
        return self.links


    def browse(self, site_url):
        with sync_playwright() as p:
            try:
                # Launch Firefox in headless mode with specific arguments
                browser = p.firefox.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage'
                    ]
                )

                # Create a context that ignores HTTPS errors
                context = browser.new_context(ignore_https_errors=True)
                page = context.new_page()

                # Navigate to the URL with a timeout
                page.goto(site_url,
                          wait_until='networkidle',
                          timeout=30000)  # 30 seconds timeout

                # Scroll the page
                page.mouse.wheel(0, 15000)

                if self.mode != "tool_mode":
                    self.get_links(page)

                # Save the page content and screenshot

                self.file_utils.write_file(self.file_utils.html_path, page.content())
                page.screenshot(path=self.file_utils.screenshot_path, full_page=True)

                # Wait for any final processing
                time.sleep(10)
                if self.llm_id in anthropic_supported_models:
                    self.compress_image()
            except Exception as e:
                print(f"Error during browsing: {str(e)}")
                raise e

            finally:
                if 'browser' in locals():
                    browser.close()