import os
import shutil

def delete_unwanted_dirs(root_path):
    """
    Deletes '__pycache__' directories from the specified path.
    """
    for root, dirs, files in os.walk(root_path, topdown=True):
        # Remove '__pycache__' from the list of directories to traverse
        if '__pycache__' in dirs:
            try:
                shutil.rmtree(os.path.join(root, '__pycache__'))
                print(f"Deleted: {os.path.join(root, '__pycache__')}")
            except OSError as e:
                print(f"Error deleting {os.path.join(root, '__pycache__')}: {e}")
            dirs.remove('__pycache__')


def consolidate_files(root_path, exceptions, output_file):
    """
    Consolidates the content of files in a directory into a single file,
    excluding specified exceptions.
    """
    with open(output_file, 'w', encoding='utf-8', errors='ignore') as outfile:
        for root, dirs, files in os.walk(root_path):
            # Skip the 'myenv' directory if it somehow still exists
            if 'myenv' in dirs and os.path.join(root, 'myenv') == os.path.join(root_path, 'myenv'):
                dirs.remove('myenv')

            for file in files:
                if file not in exceptions and file != os.path.basename(output_file) and file != '.env':
                    file_path = os.path.join(root, file)
                    try:
                        outfile.write(f"{'='*40}\n")
                        outfile.write(f"File: {file_path}\n")
                        outfile.write(f"{'='*40}\n\n")
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            outfile.write(infile.read())
                        outfile.write("\n\n")
                    except Exception as e:
                        outfile.write(f"Could not read file: {file_path}. Error: {e}\n\n")

def main():
    """
    Main function to drive the script.
    """
    folder_path = input("Enter the path of the folder to process: ")
    if not os.path.isdir(folder_path):
        print("Error: The provided path is not a valid directory.")
        return

    exceptions_str = input("Enter file names to exclude (comma-separated, e.g., file1.txt,file2.py): ")
    exceptions = [item.strip() for item in exceptions_str.split(',')]

    consolidated_filename = "consolidated_code.txt"
    output_file_path = os.path.join(os.getcwd(), consolidated_filename)

    print("\nStep 1: Deleting unwanted directories...")
    delete_unwanted_dirs(folder_path)

    print("\nStep 2: Consolidating files...")
    consolidate_files(folder_path, exceptions, output_file_path)

    print(f"\nProcess complete. All files have been consolidated into '{output_file_path}'")

if __name__ == "__main__":
    main()
