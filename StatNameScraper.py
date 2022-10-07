import pandas as pd
from pydantic import BaseModel

# local imports
from extract_school_names import ExtractSchoolNames
from extract_author_names import ExtractAuthorNames
from gender_classifier import RunGenderClassifier
import school_constants
import journal_constants


class StatNameScraper(BaseModel):
    def pipeline(self) -> pd.DataFrame:
        """Pipeline for scraping names from top statistics departments and journals

        For "Revisiting the Glass Ceiling: A Study of the Gender Gap in Statistics Academia" abstract presented
        at 2022 WSDS Conference. Departments scraped are the top 29 from 2022 U.S. News Best Statistics Program
        Rankings. Top journals' (SRJ Journal 2021 rankings) 2021 issues

        Return:
            pd.DataFrame: [school/journal, full_name, pred_gender]
        """

        # Get all school and journal names
        all_names_df = self._get_all_names_schools("faculty")
        all_names_df.append(self._get_all_names_schools("phd"))
        all_names_df.append(self._get_all_names_journals())

        # pull in genderizer and add the column
        genderClassifier = RunGenderClassifier()
        all_names_df = genderClassifier.validation_analysis(all_names_df)

        return all_names_df

    def _get_all_names_schools(self, role: str) -> pd.DataFrame:
        """Extract names from schools

        Iterate through all schools to pull names of phd students or faculty

        Arguments:
            role (str): faculty or phd

        Returns:
            pd.DataFrame: [school/journal, name]
        """

        final_df = pd.DataFrame()
        for school in school_constants.DEPT_WEBSITES_FACULTY.keys():
            extract_names = ExtractSchoolNames(school=school, role=role)
            full_name = extract_names.pipeline()

            names_df = pd.DataFrame(
                {
                    "school/journal": school,
                    "name": full_name,
                }
            )

            final_df.append(names_df)

        return final_df

    @staticmethod
    def _get_all_names_journals() -> pd.DataFrame:
        """
        Iterate through all journals to pull name.

        Returns:
            pd.DataFrame: [school/journal, fullname, firstname]
        """

        journals = []
        names = []

        for journal in journal_constants.WEBSITES.keys():
            extract_names = ExtractAuthorNames(journal=journal)
            full_name = extract_names.pipeline()
            journals.extend([journal] * len(full_name))
            names.extend(full_name)

        final_df = pd.DataFrame({"school/journal": journals, "name": names})
        return final_df
