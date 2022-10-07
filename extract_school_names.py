import requests
from bs4 import BeautifulSoup
from typing import List
import re

# local imports
import school_constants


class ExtractSchoolNames:
    def __init__(self, school: str, role: str):
        """
        Attributes:
            school (str): name of school
            role (str): ['faculty', 'phd']. Must be either faculty or student pages to parse through
        """
        self.school = school
        self.role = role

    def pipeline(self) -> List[str]:
        """Run pipeline to pull relevant names for school

        Iterates through all the webpages of the specified school and role to pull names

        Returns:
            List[str]: names as 'firstname lastname'

        Raises:
            Exception: "Invalid choice for role to parse: {role}. Must be either 'faculty' or 'phd'"
        """
        if self.role == "faculty":
            websites = school_constants.DEPT_WEBSITES_FACULTY.get(self.school)
            get_names_function = self._get_faculty_names
        elif self.role == "phd":
            websites = school_constants.DEPT_WEBSITES_PHD.get(self.school)
            get_names_function = self._get_phd_names
        else:
            raise Exception(
                f"Invalid choice for role to parse: {self.role}. Must be either 'faculty' or 'phd'"
            )

        all_names = []
        for url in websites:

            class_names_list = get_names_function(url)
            if self.school in school_constants.NAMES_TO_CLEAN:
                class_names_list = [" ".join(n.split(", ")[::-1]) for n in class_names_list]

            all_names.extend(class_names_list)
        return all_names

    def _get_faculty_names(self, url: str) -> List[str]:
        """Retrieve names from faculty website

        For a given website, retrieve the relevant faculty names for the specified school

        Arguments:
            url (str): website url to pull names from
        Returns:
            List[str]: names of individuals
        """

        # Retrieve keys based on school name
        html_class_name = school_constants.FACULTY_CLASS.get(self.school)
        html_class_position = school_constants.FACULTY_ROLE.get(self.school)
        row_tag = school_constants.FACULTY_NAME_ROW_TAG.get(self.school)
        name_tag = school_constants.FACULTY_NAME_TAG.get(self.school)

        # Rutger's adjunct page uses a different tag for names
        if url == "https://statistics.rutgers.edu/people-pages/adjunct-faculty":
            name_tag = "h4"

        # Gets html
        people_html = requests.get(
            url, verify=False, headers={"User-Agent": "Mozilla/5.0"}
        )
        html = BeautifulSoup(people_html.text, "html.parser")

        # Get tag for name
        people_class = html.find_all(name_tag, {"class": html_class_name})

        # Add case for texas_am
        if self.school == "texas_am":
            people_class = html.find_all(name_tag, {"data-title": html_class_name})

        # Add case for iowa
        if self.school == "iowa":
            people_class = html.find_all("td")

        # This is used if the website includes all faculty roles together
        # Used to parse out roles of faculty with our exclusion criteria
        if html_class_position is not None:
            role_class = html.find_all(
                school_constants.ROLE_TAG.get(self.school), {"class": html_class_position}
            )

        # Subset to get only relevant faculty if the webpage includes excluded faculty
        filteridx = [True] * len(people_class)
        if html_class_position is not None:
            filteridx = []
            for row in role_class:
                # Special cases
                if self.school in school_constants.ROLE_NAME_TAG.keys():
                    row = row.find(school_constants.ROLE_NAME_TAG.get(self.school))
                if self.school == "cornell":
                    # Exclude tags not related to role
                    if any(x in str(row) for x in school_constants.EXCLUDED_TAGS):
                        continue
                # Get a list of bool for which False represents excluded faculty
                filteridx.append(
                    not any(x in str(row) for x in school_constants.EXCLUDED_FACULTY)
                )
            # Special case for chicago and texas_am
            if self.school in ["chicago", "purdue", "texas_am"]:
                for person in people_class:
                    row = person.find(html_class_position).text.strip()
                    filteridx.append(
                        not any(x in str(row) for x in school_constants.EXCLUDED_FACULTY)
                    )

        class_names = []
        # Special case for florida
        if self.school == "florida":
            people_class = people_class[0]

            # Get name and role information
            class_name_row = people_class.find_all(row_tag)
            role_name_row = people_class.find_all(html_class_position)

            for row in class_name_row:
                class_names.append(re.search(r".*\/>([^</]*)", str(row)).group(1))

            for row in role_name_row:
                position = re.search(r"<p>(.*?)<br/>", str(row))
                if position is not None:
                    position = position.group(1)
                else:
                    continue
                filteridx.append(
                    not any(x in str(position) for x in school_constants.EXCLUDED_FACULTY)
                )
        else:
            for row in people_class:
                # Get names of faculty when row does not need to be parsed
                if row_tag is None:
                    if row is not None:
                        class_names.append(re.sub(" +", " ", row.get_text().strip()))
                # Get names of faculty when row needs to be parsed
                else:
                    name = row.find(row_tag)
                    if name is not None:
                        name_to_add = re.sub(" +", " ", name.text.strip())
                        class_names.append(name_to_add)
                # Special case for ucla
                if self.school == "ucla":
                    first_name = (
                        row.find("span", {"class": row_tag[0]}).get_text().strip()
                    )
                    last_name = (
                        row.find("span", {"class": row_tag[1]}).get_text().strip()
                    )
                    class_names.append(first_name + " " + last_name)

        # Get final names, excluding unwanted elements
        class_names = [
            x.replace(", Ph.D.", "")
            for x in class_names
            if not re.search(r"[\d\n@-]", x)
        ]
        class_names = [i for (i, v) in zip(class_names, filteridx) if v]

        # This section is needed to parse schools whose website organizes faculty by role-level tables
        if self.school in school_constants.FACULTY_TABLE.keys():
            class_names = []
            for table_name in school_constants.FACULTY_TABLE.get(self.school):
                ones_to_keep = html.find_all("div", {"class": table_name})

                if self.school in ["harvard", "wisconsin"]:
                    ones_to_keep = ones_to_keep[0]
                    names_to_keep = ones_to_keep.find_all(
                        name_tag, {"class": html_class_name}
                    )

                if self.school == "stanford":
                    ones_to_keep = ones_to_keep[0:3]
                    names_to_keep = [
                        x.find_all(name_tag, {"class": html_class_name})
                        for x in ones_to_keep
                    ]

                if self.school == "penn":
                    ones_to_keep = [x.find("ul") for x in ones_to_keep]
                    names_to_keep = [
                        x.find_all(name_tag, {"class": html_class_name})
                        for x in ones_to_keep
                    ][0]

                if self.school == "minnesota":
                    ones_to_keep = html.find(table_name)
                    names_to_keep = ones_to_keep.find_all(name_tag)

                if self.school == "uci":
                    ones_to_keep = [html.find_all(table_name)[i] for i in [0, 2]]
                    names_to_keep = [x.find_all("tr") for x in ones_to_keep]
                    names_to_keep = [
                        item.find_all(name_tag)
                        for sublist in names_to_keep
                        for item in sublist
                    ]
                    names_to_keep = [
                        item for sublist in names_to_keep for item in sublist
                    ]

                if self.school == "columbia":
                    names_to_keep = [
                        x.find(name_tag, {"class": html_class_name})
                        for x in ones_to_keep
                    ]

                names_to_keep = [x.get_text().strip() for x in names_to_keep]
                names_to_keep = [x for x in names_to_keep if not re.search(r"[@-]", x)]

                class_names.extend(names_to_keep)

        return class_names

    def _get_phd_names(self, url: str) -> List[str]:
        """Retrieve names from phd website

        For a given website, retrieve the name of phd student for the specified school

        Arguments:
            url (str): website url to pull names from
        Returns:
            List[str]: names of individuals
        """
        # Retrieve keys based on school name
        html_class_name = school_constants.PHD_CLASS.get(self.school)
        html_class_position = school_constants.PHD_ROLE.get(self.school)
        row_tag = school_constants.PHD_NAME_ROW_TAG.get(self.school)
        name_tag = school_constants.PHD_NAME_TAG.get(self.school)

        # Gets html
        people_html = requests.get(
            url, verify=False, headers={"User-Agent": "Mozilla/5.0"}
        )
        html = BeautifulSoup(people_html.text, "html.parser")

        # Get tag for name
        people_class = html.find_all(name_tag, {"class": html_class_name})

        # Add case for texas_am
        if self.school == "texas_am":
            people_class = html.find_all(name_tag, {"data-title": html_class_name})

        # Add case for minnesota phd
        if self.school == "minnesota":
            # Take the first section (phd students. Second section is masters)
            people_class = people_class[0].find("table").find_all("li")

        # This is used if the website includes all faculty roles together
        # Used to parse out roles of faculty with our exclusion criteria
        if html_class_position is not None:
            role_class = html.find_all(
                school_constants.ROLE_TAG.get(self.school), {"class": html_class_position}
            )

        # Special case for unc
        if self.school == "unc":
            role_class = html.find_all(
                school_constants.ROLE_TAG.get(self.school), {"class": None}
            )
            role_class = [x.get_text() for x in role_class if "Student" in x.get_text()]

        # Subset to get only relevant phd and faculty
        filteridx = [True] * len(people_class)
        if html_class_position is not None:
            filteridx = []
            for row in role_class:
                filteridx.append(not any(x in str(row) for x in school_constants.EXCLUDED_PHD))

        # Special case for chicago and texas_am
        if self.school == "purdue":
            for person in people_class:
                row = person.find(html_class_position).text.strip()
                filteridx.append(not any(x in str(row) for x in school_constants.EXCLUDED_PHD))

        class_names = []
        # Special case for florida
        if self.school == "florida":
            people_class = people_class[0]
            class_name_row = people_class.find_all(row_tag)
            filteridx = [True] * len(class_name_row)

            for row in class_name_row:
                class_names.append(re.findall(r"<strong>(.*?)</strong>", str(row))[0])
        else:
            for row in people_class:
                if row_tag is None:
                    if row is not None:
                        class_names.append(re.sub(" +", " ", row.get_text().strip()))
                else:
                    name = row.find(row_tag)
                    if name is not None:
                        name_to_add = re.sub(" +", " ", name.text.strip())
                        class_names.append(name_to_add)

        # Get final names
        class_names = [x for x in class_names if not re.search(r"[\d\n@-]", x)]
        class_names = [i for (i, v) in zip(class_names, filteridx) if v]

        # Special case for uci; first table is relevant
        if self.school == "uci":
            ones_to_keep = html.find_all("table")[1]
            names_to_keep = ones_to_keep.find_all(name_tag, {"class": html_class_name})
            class_names = [x.get_text().strip() for x in names_to_keep]

        return class_names


if __name__ == "__main__":

    extract_names = ExtractSchoolNames("unc", "faculty")
    print(extract_names.pipeline())
