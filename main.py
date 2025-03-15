import pandas as pd
from tabulate import tabulate
import asyncio
import aiohttp
import aiofiles
import ssl
import os


class ImageDownloader:
    def __init__(self):
        self.images_dir_path = self._get_images_dir_path()
        self._links = self._get_links()
        self.tasks = []
        self.statuses = pd.DataFrame({"Link": [], "Status": []})
        self.ssl_context = self._create_ssl_context()

    def _create_ssl_context(self):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def _check_directory_access(self, directory_path):
        return (
            os.path.exists(directory_path) and 
            os.path.isdir(directory_path) and
            os.access(directory_path, os.W_OK)
        )

    def _get_images_dir_path(self):
        while True:
            print("Enter the directory to save images: ", end="", flush=True)
            path = input()
            if not self._check_directory_access(path):
                print("Directory not available, enter another one.")
            else:
                return path

    def _get_links(self):
        print("Enter image URLs (press Enter to finish):")
        return [link for link in iter(input, "")]

    def _update_status(self, url, status):
        max_length = 50
        if len(url) > max_length:
            url = url[:30]+"..."+url[-30:]
        self.statuses.loc[len(self.statuses)] = [url, status]

    async def _download_image(self, session, url, path):
        try:
            async with session.get(url, ssl=self.ssl_context) as response:
                if response.status != 200:
                    return self._update_status(url, "Error")

                async with aiofiles.open(path, "wb") as f:
                    async for chunk in response.content.iter_chunked(1024):
                        await f.write(chunk)

            self._update_status(url, "Success")

        except Exception:
            return self._update_status(url, "Error")

    async def download_images(self):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i, url in enumerate(self._links, start=1):
                path = f"{self.images_dir_path}/image_{i}.jpg"
                task = asyncio.create_task(self._download_image(session, url, path))
                tasks.append(task)

            await asyncio.gather(*tasks)

        print(tabulate(self.statuses, headers="keys", tablefmt="grid", showindex=False))


async def main():
    downloader = ImageDownloader()
    await downloader.download_images()


if __name__ == "__main__":
    asyncio.run(main())
    