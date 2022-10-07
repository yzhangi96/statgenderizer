import requests
from bs4 import BeautifulSoup
from typing import List
import re

# local imports
import journal_constants


class ExtractAuthorNames:
    def __init__(self, journal: str):
        """
        Attributes:
            journal (str): name of journal
        """
        self.journal = journal

    def pipeline(self) -> List[str]:
        """Run pipeline to pull relevant names for journal

        Iterates through all the webpages of the specified journal to pull names

        Returns:
            List[str]: names as 'firstname lastname'

        """

        all_names = []
        for url in journal_constants.WEBSITES.get(self.journal):
            class_names_list = self._get_author_names(url)
            all_names.extend(class_names_list)
        return all_names

    def _get_author_names(self, url: str) -> List[str]:
        """Retrieve names from journal website

        For a given website, retrieve the author names for the specified journal

        Arguments:
            url (str): website url to pull names from
        Returns:
            List[str]: names of individuals
        """

        # Retrieve keys based on journal name
        html_class_name = journal_constants.NAME_CLASS.get(self.journal)
        name_tag = journal_constants.NAME_TAG.get(self.journal)

        # Gets html
        people_html = requests.get(
            url, verify=False, headers={"User-Agent": "Mozilla/5.0"}
        )
        html = BeautifulSoup(people_html.text, "html.parser")

        # Get tag for name
        people_class = html.find_all(name_tag, {"class": html_class_name})

        class_names = []
        for row in people_class:
                name = row.get_text()
                name = [x.strip() for x in re.split(r'[&,]+', name)]
                class_names.extend(name)

        return class_names


if __name__ == "__main__":

    extract_names = ExtractAuthorNames("jss")
    print(extract_names.pipeline())
