import pytest

from codemie_test_harness.tests.enums.tools import ResearchToolName

search_tools_test_data = [
    (
        ResearchToolName.GOOGLE_SEARCH,
        """
            Run Google Search Tool and query: AI trends.
            Represent in JSON format with title and link
        """,
        50,
    ),
    pytest.param(
        ResearchToolName.TAVILY_SEARCH,
        """
            Run Google Search Tool and query: AI trends
            Represent in JSON format with title and link
        """,
        50,
        marks=pytest.mark.skip(
            reason="Temporarily skipping Tavily test until it is fixed"
        ),
    ),
]
interactions_tools_test_data = [
    (
        ResearchToolName.GOOGLE_PLACES,
        "Find McDonald in the Kyiv on the Khreschatyk, 19-a",
        """
            I found a McDonald's location on Khreschatyk Street in Kyiv:
            McDonald's
            Address: Khreschatyk St, 19-a, Kyiv, Ukraine
            Rating: 4.4 (based on 21,802 user ratings)
            Open Now: Yes
            Price Level: 2
        """,
    ),
    (
        ResearchToolName.GOOGLE_PLACES_FIND_NEAR,
        "Find McDonalds in the Kyiv near Khreschatyk in radius 2 km",
        """
            I found several McDonald's locations near Khreschatyk in Kyiv, within a 2 km radius. However, all these locations are temporarily closed. Here are the details:
            
            1. **McDonald's**
               - **Address:** Sofiivs'ka St, 1/2, Kyiv
               - **Rating:** 4.3 based on 11,090 reviews
               - **[View Photo](https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=AciIO2fMNnp003CQSug6AmJuJXZ0myKILfuo4iNiSDpi6mTJm2zgnwFbWazL-5UC9MGU6e8TZ5jzorgsFj3QfmeEuICUKkKv9vvgKWXItQo4h2TdXgNxV2U-WHuz-cLDT0d56YoVpRFxjitp1Fmly-XEwhZj_UqgVW2d2qAI5lwjk4_aLdbZznWWZ212blOjpF4VY987Q8D9wVEUHnl-y72Ev6A7ywNvV3VJKGuE5szP6JRj7GI9r-0ToIuC8dub3-lkgyQUuF56Sfki6M46ePndL5mk-KIuJOfH54EINyBqp-z3Q9xA85T93pCcW6bMxDk5XqfG7nQfpZr5yO8-zfJj51NNJzjF8vsevvfXDIoUVDGXNJfllLcXCxA6uaoYHK0ynmMaX4_6X_R2FtM_UoimzUuw9cqQPBK_FryGvD9qO5Bx7zW_HMb3D6TMax2iNtSrkwd59Bz7XC4ud6MqdoWn7rXGR_Z52XR1KaGFnFMW_4NI0MI6_hFVjvUBp7xnzvfABaaG5o2imuVRzf4khUthFRyXTil8ht36C-ijIVvg8HdODerT8LN6IoV4pCg5XekDNpIqxhJf)**
              
            2. **McDonald's**
               - **Address:** Khreschatyk St, 19-a, Kyiv
               - **Rating:** 4.4 based on 21,848 reviews
               - **[View Photo](https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=AciIO2fLPseD2rR9t8necj88rGG-3xzeNQGmho05h5SQ7i8tjQ8zG0wPEbLXz0m0ZzKxR6inczyc5GW_8WkJ5PmuDJLXYuEB0-pwow4tdnXkW5GynclZsRklxzEAV49X7IBsLXSaw1-WhISnkEWYMzb8PM6WkORf_IKBw8cD6AsQ93rLMusReVT37Cwo9ZiCqaOeMTDyc7MSN9Md7MhN0ezi-cphTe6VfFT9zMPSVyM-_yjb9bjzHsFjnK343C1QjMIZeBdRwz-Raw68xvecUu9FF6JLx8vPlW8kkbgdS9p9DX7AAS3NccBwFEBEGPryDYCzNKHew_0NRqcaQW9KQfWPuBeApArqbEXyeVCRdCPe0MwOy4wQER9_PtnaltlfKGBHD8fAWH3hS35erkkQE6GQ7_5KQxExVsXSq7hiVxUd_Mh0geOT2KSUl7A8Gkcq3AbqeTXTp5V6454vX-yq55WEpCUvdB6DJNGGxdCO8q4YJm3SuEyyN3B4f3QIg2HsiOVv9KPK3A29hYsX_IGgDcwsD720zltJEYbIevGZ3OtFrv_Yp-kGDBaYPmZD-M6i8qy6zS7aTfkWNLjcjQ)**
              
            3. **McDonald's**
               - **Address:** Velyka Vasylkivska St, 22, Kyiv
               - **Rating:** 4.3 based on 10,710 reviews
               - **[View Photo](https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=AciIO2dOxDjqq7UHyeqKwh9VO8o9uq3iqfWDPLgVKMwwwjBhmb3cG2rAohIjtemD29g67NcsKzx-dWVqsmkRkqz8XhU6HlbrJEtq_TL7xVYQTImFHXq9kElkR9I0gnpA-rDZoD_RYlcmuRKURTNom8VC6sjzszcozz6QNwjOnl7f55MJq6O9eoJQ0g3iu-ecXGt6bELpx2oa9urOqqjrapGH4yKOQKPp_36MEJVkuD6IohzuLMqpQdlIlNp8WP7SiEZb9CD1DalNuk5H__jsZ35zMKVCpWYMnkZGSN0_-DOFrfXnhC-b6MKYrB_9D6pUjpsfIPvi2qHHf4LRho-P2OR71g1P7WlRf25h1g9DdX3uMe7kMtU0sxRvUMSiAe6Sy9D8s7qrIEb8DcfFQxkFgoQs6fTb-RCEKAwqQtMlJ96nd2kmRU100MDSWsiUy7ifLn6LK343O9_e-RJyobXSo8WovvUs1QxA2kh2z6UMHVxorNPV5wclkE3J3cLYzUTvL5P7t3OBDVGiTdcPzE-5Z7P63VF-jUHU9Hv2l6-KHjwa4r8wIDgB7shW_iJEuHgv04NxD2p95onx)**
              
            4. **McDonald's**
               - **Address:** Borychiv Descent, 10А, Kyiv
               - **Rating:** 4.5 based on 14,818 reviews
               - **[View Photo](https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=AciIO2efC3DMYMgEycgpEkR5IhrJIwufUliminn1HZmICsch982EeMsgXS9kKkZRvOkvWnnI-os45avQFWAUFR_bWy8R2BwGbW1V37En8BwrFVGznWkIEFZeCVTVPI_s8K4Hj77_l5WLzYnh5wCMCsPZQtTjk26CdvM3Kg1MdJQdZAIFcc26jErp3h6bw7MRY245XbVl2w-41jSOlayQ8voyUUtVVzeGgKVN1kUh-cc2An72nvGjdBQP2S-_8pwGJ5Sz0CcakvCT2VnAdTKz4ywZ5pNxdpKRz17wPvQAkj9jdKrHN5J5jmqjUu_QQFMFfkfNR2P6OEaNxMT5mPizohzU7e1_A3dWHRZxB9bAmxZ9EpQkyeZb3ppwtM24pCkSQ8Cz_9b8qBLleIWolLtXBLyTM54z4XtCSlc-X1wmjyIkca6Cd5D_8jafJbd10uj6wiA5VdhWcv1l_yJSnq0-0t1STfqI0VUVITpAEEU0ZB0TTheuQUuLa6quMjzU8fnYiMzh9YyY8CrLt8xXEMuOwPJrh94iA4-5AKOeJO4LPVehpNdKVWLKXYEwfilMaouuEHheVBS6ANRn)**
              
            5. **McDonald's**
               - **Address:** Bohdana Khmel'nyts'koho St, 40/25, Kyiv
               - **Rating:** 4.3 based on 6,187 reviews
               - **[View Photo](https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=AciIO2eeKwvPbZ89_onqK5_s5Zv8kV5TxY5ZIM5ZwR-q8vPuyxAhXp-X6A4LDdLQEtBc3WhH3IJtIiwf6wSqGqLQeuoxIzUqqTR1VM2bYp1FfQwVhVrTVf2bHixPt1z847PYQMCO4ibGE1c0EUQI8S6K_2SnCvmb0PO8AC5GMY-ociHR6rbR8QEiKnYFSd04w349_u-f_q8kntKLS1TnOphOhOFatS_TJFS8AO8JQbV9jILByYncmH6dkQxw7eqqpY--bFjk5y3n1bsP0haKdyLGRwN3d0aqFkRUvtqNPg7KU1Hx0_5uwBb4C_o4XXZXvWhi_fwanNTF_XpyTTcrmw_7IerLVMhoZmM89j3Un8qQi7_prhJBT3Un3zwLKvXs-cr4R9StGn_dT9D73RoOGHP16wjSrfCZ8BMNBM6JgqTxKzLjvf8yGKWeYs5pTctcjcsqw_vc9cOhTHewN2wcRc_AdQ6Snj191P6UiVUGnytXyhKCM6yjOXvVjNLjbDNfZz5CeJZjsNJDuL7kH64vG_EQgR5eHqQUTVWD2Fm7wJE-YtP2MtOGEptncDVQtRSt6ALBj0kUi9t3)**
              
            Please note that the status may change, so it's advisable to check the latest updates before making plans.
        """,
    ),
    (
        ResearchToolName.WIKIPEDIA,
        "Short description of AI from Wikipedia",
        """
            Artificial intelligence (AI) is the capability of computer systems to perform tasks requiring human intelligence,
            such as learning, reasoning, problem-solving, and decision-making. It encompasses various technologies and methods,
            including machine learning and neural networks, enabling machines to perceive their environment, adapt, and take
            actions to achieve specific goals. AI applications include virtual assistants, self-driving cars, recommendation systems,
            and advanced game play, with ongoing advancements raising ethical and regulatory considerations.
        """,
    ),
    (
        ResearchToolName.WEB_SCRAPPER,
        "Web Scrap this page https://webscraper.io/about-us",
        """
            Here is the scraped content from the [Web Scraper - About Us](https://webscraper.io/about-us) page:
            # About us | Web Scraper
            ## Our story
            Web Scraper started as a Chrome browser extension in 2013. Its popularity quickly grew as it was the most advanced and completely free. Today Web Scraper is both a free browser extension and also a Cloud based Web Scraping solution for complete automation.
            ## Our mission
            Our mission is to make web data accessible to everyone by making the most advanced and easiest to use web scraping tool.
            ![About us image](https://webscraper.io/img/about-us.jpg)
            ## Company data
            - **Company**: “Web Graph“ SIA
            - **Registration number**: 40203093908
            - **VAT number**: LV40203093908
            - **Address**: Ubelu 5-71, Adazi, Latvia, LV-2164
            - **Bank**: “Swedbank” AS
            - **Bank account**: LV31HABA0551044098666
            ## Products
            - [Web Scraper browser extension](https://chromewebstore.google.com/detail/web-scraper-free-web-scra/jnhgnonknehpejjnehehllkliplmbmhn?hl=en)
            - [Web Scraper Cloud](https://webscraper.io/cloud-scraper)
            ## Company
            - [About us](https://webscraper.io/about-us)
            - [Contact](https://webscraper.io/contact)
            - [Website Privacy Policy](https://webscraper.io/privacy-policy)
            - [Browser Extension Privacy Policy](https://webscraper.io/extension-privacy-policy)
            - [Media kit](https://webscraper.io/downloads/Web_Scraper_Media_Kit.zip)
            - [Jobs](https://webscraper.io/jobs)
            ## Resources
            - [Blog](https://webscraper.io/blog)
            - [Documentation](https://webscraper.io/documentation)
            - [Video Tutorials](https://webscraper.io/tutorials)
            - [Screenshots](https://webscraper.io/screenshots)
            - [Test Sites](https://webscraper.io/test-sites)
            - [Forum](https://forum.webscraper.io/)
            - [Status](https://status.webscraper.io/)
            ## Contact Us
            - Email: [info@webscraper.io](mailto:info@webscraper.io)
            - Address: Ubelu 5-71, Adazi, Latvia, LV-2164
            **Copyright © 2025 Web Scraper | All rights reserved**
        """,
    ),
]
