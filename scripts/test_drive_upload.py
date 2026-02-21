import os
from app.services.drive_service import drive_service, upload_or_replace

def main():
    folder_id = os.environ["MUSCLEMEMOIRS_DRIVE_FOLDER_ID"]
    svc = drive_service()

    with open("hello_drive.txt", "w", encoding="utf-8") as f:
        f.write("OAuth upload success!\n")

    file_id = upload_or_replace(svc, folder_id, "hello_drive.txt")
    print("Uploaded/Replaced file_id:", file_id)

if __name__ == "__main__":
    main()