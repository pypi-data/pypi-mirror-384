import os

import pandas
import pandas as pd

from qrgrader.common import Nia, get_workspace_paths, get_date, StudentsData, Questions


class Raw:
    def __init__(self, filename):
        self.filename = filename
        self.raw = None

    def load(self):
        if os.path.exists(self.filename):
            self.raw = pandas.read_csv(self.filename, sep='\t', header=None)
            return True
        return False

    def get_row(self, exam_id):
        if self.raw is None:
            return None
        by_exam = self.raw[self.raw[1] == exam_id]
        if by_exam.empty:
            return None
        return by_exam.iloc[0, :].tolist()

    def get_exams(self):
        if self.raw is None:
            return None
        return self.raw.iloc[:, 1].tolist()


def main():
    (dir_workspace,
     dir_data,
     dir_scanned, _,
     dir_xls,
     dir_publish, _) = get_workspace_paths(os.getcwd())

    date = get_date()

    nia = Nia(dir_xls + os.sep + str(date) + "_nia.csv")
    nia.load()

    students_data = StudentsData(dir_xls + os.sep + "data.csv")
    students_data.load()

    questions = Questions(dir_xls + os.sep + str(date) + "_questions.csv")
    questions.load()

    raw = pd.read_csv(dir_xls + os.sep + str(date) + "_raw.csv", sep='\t', header=None)
    raw.iloc[:, 0] = raw.iloc[:, 0] * 1000 + raw.iloc[:, 1]
    raw.set_index(raw.iloc[:, 0], inplace=True)

    hdr = 4  # Number of header rows
    inserted = 0

    # Insert the NIA column
    raw.insert(inserted + 2, "NIA", "")
    for exam_id in raw.iloc[:, 0].tolist():
        raw.loc[exam_id, "NIA"] = nia.get_nia(exam_id)
    inserted += 1

    # Insert the GRADE column
    raw.insert(inserted + 2, "T", '=SUMPRODUCT(INDIRECT(ADDRESS(ROW(), COLUMN() + 1) & ":" '
                                      '& ADDRESS(ROW(), COLUMNS($A$1:$1))) * INDIRECT(ADDRESS(4, COLUMN() + 1) & ":" '
                                      '& ADDRESS(4, COLUMNS($A$1:$1))))')
    raw.insert(inserted + 2, "O", '=SUMPRODUCT(($G$3:$3="O") * INDIRECT(ADDRESS(ROW(), COLUMN() + 2) & ":" '
                                      '& ADDRESS(ROW(), COLUMNS($A$1:$1)))* INDIRECT(ADDRESS(4, COLUMN() + 2) & ":" '
                                      '& ADDRESS(4, COLUMNS($A$1:$1))))')
    raw.insert(inserted + 2, "Q", '=SUMPRODUCT(($G$3:$3<>"O") *INDIRECT(ADDRESS(ROW(), COLUMN() + 3) & ":" '
                                      '& ADDRESS(ROW(), COLUMNS($A$1:$1)))* INDIRECT(ADDRESS(4, COLUMN() + 3) & ":" '
                                      '& ADDRESS(4, COLUMNS($A$1:$1))))')

    inserted += 3

    # Fill the header
    percent_answ = '=SUM(OFFSET(INDIRECT("RC", FALSE), 1, 0, ROWS(A:A)-ROW(), 1))/COUNT(OFFSET(INDIRECT("RC", FALSE), 1, 0, ROWS(A:A)-ROW(), 1))'
    percent_ques = ('=SUM(OFFSET(INDIRECT("RC", FALSE), ' + str(hdr) + ', -3, ROWS(A:A) - ROW()-4, 4))/COUNT(OFFSET(INDIRECT("RC", FALSE), '
                    + str(hdr) + ', 0, ROWS(A:A)-ROW(), 1))')

    names, qn, ans_letter, ans_value = [""] * (inserted + 2), [""] * (inserted + 2), [""] * (inserted + 2), [""] * (inserted + 2)
    ans_perc = ["Exam ID", "#", "NIA", "Q", "O", "T"]

    for question in questions.get_questions():
        if questions.get_type(question) == "Q":
            names.extend([questions.get_text(question), "", "", percent_ques])
            qn.extend([question, question, question, question])
            ans_value.extend([questions.get_value(question, i + 1) for i in range(4)])
            ans_letter.extend([chr(65 + i) for i in range(4)])
            ans_perc.extend([percent_answ] * 4)
        else:
            names.append(questions.get_text(question))
            qn.append(question)
            ans_letter.append("O")
            ans_value.append(questions.get_value(question, 1))
            ans_perc.append(percent_ques)

    #print(raw.shape, len(names), len(qn), len(ans_letter), len(ans_value), len(ans_perc))

    raw.loc[-5] = names
    raw.loc[-4] = qn
    raw.loc[-3] = ans_letter
    raw.loc[-2] = ans_value
    raw.loc[-1] = ans_perc

    df = raw.sort_index().reset_index(drop=True)

    df.to_csv(dir_xls + os.sep + str(date) + "_table.csv", sep='\t', index=False, header=False)

if __name__ == "__main__":
    main()
