import os

# Set tmp_folder environment variable
os.environ["tmp_folder"] = os.path.join(os.getcwd(), "tmp_folder")
tmp_folder = os.environ["tmp_folder"]

if not os.path.exists(tmp_folder):
    os.makedirs(tmp_folder)


code_generation_prompt = f"""Can you create strictly a Python script snippet alone no extra text i should be able to 
run the script as it is using Playwright that:

Executes multiple test cases for UAT without defining explicit functions.
Raises appropriate exceptions for each test case.
Logs detailed information (test case description and exception details) to a specified log file ({tmp_folder}/test.log).
Please provide the code snippet."

This revised statement directly addresses the key requirements of the original prompt, focusing on the core functionalities and desired outcomes.
return:
'''python

\\ generated_code

'''

"""