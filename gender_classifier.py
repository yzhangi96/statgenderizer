import requests, json
import pandas as pd
import os

#global constant
FOLDER = "/Desktop/WSDS"


class RunGenderClassifier:
    def __init__(self, name_df: pd.DataFrame = None):
        """Classify gender of name using genderize.io api

        Attributes:
            name_list (pd.DataFrame): should contain at minimum a column "name" representing firstname lastname.
                If None, will pull in the file "namesmanual.csv" from FOLDER, which should also contain a column
                "male", which is 1 if male, 0 if female
        """

        self.name_df = name_df
        if self.name_df is None:
            name_df = pd.read_csv(os.environ["HOME"] + FOLDER + "/namesmanual.csv")
            name_df = name_df.iloc[:5]
            self.name_df = name_df[name_df.male.notna()]

        self._getgenders()

    def _getgenders(self):
        """Call genderize.io api

        Adapted from https://github.com/acceptable-security/gender.py to use genderize.io api.
        See the link for documentation
        """
        names = self.name_df["name"].tolist()
        names = [x.split()[0] for x in names]

        url = ""
        cnt = 0
        if not isinstance(names, list):
            names = [
                names,
            ]

        for name in names:
            if url == "":
                url = "name[0]=" + name
            else:
                cnt += 1
                url = url + "&name[" + str(cnt) + "]=" + name

        req = requests.get("https://api.genderize.io?" + url)
        results = json.loads(req.text)

        retrn = []
        # changed from original to return only predicted gender
        for result in results:
            if result["gender"] is not None:
                retrn.append(result["gender"])
            else:
                retrn.append("None")

        self.name_df["pred"] = retrn

        # Remap labels
        gender_dict = {"male": 1.0, "female": 0.0}
        self.name_df = self.name_df.replace({"pred": gender_dict})


if __name__ == "__main__":
    genderclassifier = RunGenderClassifier()
    pred_df = genderclassifier.name_df
    # pd.to_csv(pred_df, os.environ["HOME"] + FOLDER + "/namesmanualresults.csv")
