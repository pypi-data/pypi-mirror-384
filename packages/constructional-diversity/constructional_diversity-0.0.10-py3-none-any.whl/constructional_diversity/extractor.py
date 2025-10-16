import os
import csv
import pandas as pd
import spacy

def extract_verb_dependency(input_dir: str):
    nlp = spacy.load("en_core_web_sm")

    filelist = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith(".txt")]

    csv_path = os.path.join(input_dir, "CSV_verb_dependency_information.csv")
    xlsx_path = os.path.join(input_dir, "XLS_verb_dependency_information.xlsx")

    with open(csv_path, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["file_name", "sentence_raw", "verb", "dependency", "dependent_list", "dependent_count"])

        for filepath in filelist:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                text = f.read()

            print(filepath + "=====================================")
            doc = nlp(text)

            for sent in doc.sents:
                sent_doc = nlp(sent.text)
                for token in sent_doc:
                    if (token.pos_ == "VERB" and token.dep_ != "aux") or (token.pos_ == "AUX" and token.dep_ != "aux"):
                        dependent_list = [child.dep_ for child in token.children]
                        dep_string = ' '.join(dependent_list)
                        dependent_count = len(dependent_list)

                        writer.writerow([os.path.basename(filepath), sent.text, token.lemma_, dep_string, dependent_list, dependent_count])

    df = pd.read_csv(csv_path)
    df.to_excel(xlsx_path, index=False)
