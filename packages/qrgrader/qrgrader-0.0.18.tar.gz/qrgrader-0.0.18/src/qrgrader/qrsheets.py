import argparse
import os
import re
import sys

import yaml

from qrgrader.common import check_workspace, Nia, get_workspace_paths, get_date
from qrgrader.encrypt import decrypt
from qrgrader.secret import get_secret
from qrgrader.utils import makedir

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qrgrader.gdrive import GDrive, Sheets

client_secrets_json = '''
{

}
'''


def main():
    parser = argparse.ArgumentParser(description='Upload and download sheets from Google Sheets')
    parser.add_argument('-d', '--download', help='Download sheet', action="append", default=[])
    parser.add_argument('-D', '--download-all', help='Download sheet', action="store_true")
    parser.add_argument('-f', '--file', help='Config file')
    parser.add_argument('-F', '--filter', help='Filter names')
    parser.add_argument('-g', '--upload-pdf', help='Specify folder id for uploading', action="store_true")
    parser.add_argument('-i', '--folder-id', help='Specify folder id for uploading', default=None)
    parser.add_argument('-l', '--list', help='Create a PDF sheet', action="store_true")
    parser.add_argument('-p', '--folder-path', help='Specify folder path for uploading', default=None)
    parser.add_argument('-P', '--shared-folder-name', help='Specify folder name for uploading or listing', default=None)
    parser.add_argument('-u', '--upload', help='Upload sheet', action="append", default=[])
    parser.add_argument('-U', '--upload-all', help='Upload all sheets', action="store_true")
    parser.add_argument('-w', '--workbook', help='Workbook name')
    parser.add_argument('-x', '--diff', help='Difference')
    parser.add_argument('-y', '--yeah', help="Answer 'yes' to all questions", action="store_true")
    args = vars(parser.parse_args())

    if not check_workspace():
        print("ERROR: qrsheets must be run from a workspace directory")
        sys.exit(1)

    dir_workspace, dir_data, _, dir_generated, dir_xls, _, dir_source = get_workspace_paths(os.getcwd())
    date = get_date()

    if not check_workspace():
        print("ERROR: qrsheets must be run from a workspace directory")
        sys.exit(1)

    # Create json file with client secrets
    makedir("config")
    if not os.path.exists("config" + os.sep + "client_secret.json"):
        with open("config" + os.sep + "client_secret.json", "w", encoding='utf-8') as f:
            secret = get_secret()
            passwd = input("Enter password for QRGrader secret: ")
            try:
                client_secrets_json = decrypt(secret, passwd)
            except Exception as e:
                print("Password incorrect. You may request a password to dantard@unizar.es", e)
                sys.exit(1)
            f.write(client_secrets_json)

    # Load config file if provided
    if args["file"] is not None:
        with open(args["file"], "r", encoding='utf-8') as f:
            file_args = yaml.safe_load(f)
            args.update(file_args)

    if args["file"] is None and args["workbook"] is None and args["upload_pdf"] is False and args["list"] is False:
        print("You must specify at least one of the following options: --file, --workbook, --upload-pdf, --list")
        return

    if args.get("upload_pdf") or args.get("list"):

        gd = GDrive(config_dir="config")

        if args["folder_id"] is not None:
            folder_id = args["folder_id"]
        elif args["folder_path"] is not None:
            folder_id = gd.get_folder_id_by_path(args["folder_path"])
        elif args["shared_folder_name"] is not None:
            folder_id = gd.get_shared_folder_id(args["shared_folder_name"])
        else:
            print("You must specify a folder-id, folder-path or shared-folder-name")
            sys.exit(1)

        if folder_id is None:
            print("Folder does not exist, exiting.")
            sys.exit(1)

        if args.get("upload_pdf"):
            for file in os.listdir("results" + os.sep + "pdf"):
                if file.endswith(".pdf"):
                    print("Uploading file", file)
                    gd.upload_file("results" + os.sep + "pdf" + os.sep + file, folder_id)
            print("All files uploaded to folder", folder_id)
            args["list"] = folder_id

        if args.get("list", None):

            nias = Nia(dir_xls + os.sep + str(date) + "_nia.csv")
            nias.load()

            files = gd.ls(folder_id)

            files.sort(key=lambda x: x[0].lower())

            with open("results" + os.sep + "xls" + os.sep + date + "_pdf.csv", "w", encoding='utf-8') as f:
                f.write("EXAM ID" + "\t" + "NIA" + "\t" + "LINK" + "\t" + "QUIZ" + "\t" + "OPEN" + "\t" + "TOTAL" + "\n")
                for i, file in enumerate(files):
                    name = file[0].replace(".pdf", "")
                    link = "https://drive.google.com/u/3/uc?id=" + file[1]
                    nia = nias.get_nia(name)
                    fb_quiz = "=round(VLOOKUP(A" + str(i+2) + ",'"+date+"_raw'!A:Z,4,false),2)"
                    fb_open = "=round(VLOOKUP(A" + str(i + 2) + ",'"+date+"_raw'!A:Z,5,false),2)"
                    fb_total = "=round(VLOOKUP(A" + str(i + 2) + ",'"+date+"_raw'!A:Z,6,false),1)"

                    f.write(name + "\t" + str(nia) + "\t" + link + "\t" +
                            fb_quiz + "\t" + fb_open + "\t" + fb_total + "\n")

            print("Written to results/xls/{}_pdf.csv ({} rows)".format(date, len(files)))

    args_workbook = args.get("workbook", None)
    if args_workbook is not None:

        args_upload = args.get("upload", [])
        args_filter = args.get("filter", None)
        args_download = args.get("download", [])
        args_download_all = args.get("download_all", False)
        args_yes = args.get("yeah")
        args_upload_all = args.get("upload_all", False)
        args_diff = args.get("diff", None)

        # args_filter = date if args_filter is None else args_filter
        args_filter = None if args_filter == "." else args_filter

        if len(args_upload) > 0 and args_upload_all:
            print("You cannot use both --upload and --upload-all")
            return

        if len(args_download) > 0 and args_download_all:
            print("You cannot use both --download and --download-all")
            return

        sh = Sheets(base_folder="results/xls", config_dir="config")
        sh.open(args_workbook)

        if args_upload_all:
            sh.upload_all(args_filter, args_yes)

        elif len(args_upload) > 0:
            sh.upload(args_upload, args_yes)

        if args_download_all:
            sh.download_all(args_filter, args_yes)
        elif len(args_download) > 0:
            sh.download(args_download, args_yes)

        if args_diff:
            sh.diff(args_diff)

    print("All Done :)")


if __name__ == "__main__":
    main()
