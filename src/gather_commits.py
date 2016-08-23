import os
import subprocess
import pandas as pd


def parse_git_log_stats(log):
    """
    The collected stats will contain (list of lists):
    - commit hash
    - author
    - date
    - commit message
    - file name
    - change_type [ins, del]
    - change (one entry per file)
    """
    entries = list()

    for line in log.split("\n"):
        if line.startswith("commit"):
            # new commit
            commit = line.split(" ")[1]

            # check if previous co

        elif line.startswith("Author:"):
            author = line.split("Author:")[1].strip()

        elif line.startswith("Date:"):
            date = line.split("Date:")[1].strip()

        elif line.startswith(" " * 4):
            msg = line.strip()

        elif line.startswith(tuple([str(i) for i in range(10)]) + ("-", )):
            file_name = line.split("\t")[-1]
            for change, change_type in zip(line.split("\t")[:-1], ("ins", "del")):
                entries.append([commit, author, date, msg, file_name, change_type, change])

    return pd.DataFrame(
        entries, columns=["hash", "author", "date", "message", "file_name", "change_type", "change"])


root_dir = "/home/afr/workspace/"
output_file = "data/git_log.csv"

output_dir = os.path.dirname(output_file)
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

output = pd.DataFrame()
for repo in os.listdir(root_dir):
    print(repo)

    repo_dir = os.path.join(root_dir, repo, ".git")

    # run git log command
    try:
        out = subprocess.check_output(["git", "-C", repo_dir, "log", "--numstat", "--date=iso"])
    except subprocess.CalledProcessError:  # will occur if not a git repo
        continue

    # save log of the repo
    with open(os.path.join(output_dir, repo + ".log"), "w") as handle:
        handle.writelines(out)

    # write repo header to file
    parsed = parse_git_log_stats(out)
    parsed["repository"] = repo

    output = output.append(parsed)

output.to_csv(output_file, index=False)


# Filter
# chose which file types to exclude
file_types = [
    "py", "R", "sh", "Makefile",
    "ipynb", "md", "yaml", "yml"]

output = output[output["file_name"].str.contains("|".join(["\." + x + "$" for x in file_types]))]

# chose which authors to keep
authors = ["rendeiro"]
output = output[output["author"].str.contains("|".join(authors))]

# keep only repos with more than X commits
min_commits = 2
counts = output.groupby("repository")['hash'].count()
output = output[output["repository"].isin(counts[counts > min_commits].index)]

output.to_csv("data/git_log.filtered.csv", index=False)


# anonymize repositories
mapping = dict(zip(output['repository'].unique(), range(len(output['repository'].unique()))))
output['repository'] = ["repo" + str(mapping[x]) for x in output['repository']]
output.to_csv("data/git_log.filtered.anonymized.csv", index=False)
