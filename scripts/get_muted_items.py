import os

def get_project_access_tokens():

    os.environ['HOME']



def get_token_file_path():
    # Returns: file path of csv file with the project_name, read_access_tokens
    
    os.environ.get('ROLLBAR_TOKEN_FILE_PATH')


def main():
    print("Hello World")

if __name__ == "__main__":
    main()