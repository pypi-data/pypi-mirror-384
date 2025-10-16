import cProfile
from linkaudit import linkaudit 


# Define the directory to check (replace with your actual directory)
book_directory = "/home/maikel/projects/pythondev/linkaudit/docs"

# Profile and save to a binary file
profiler = cProfile.Profile()
profiler.enable()
linkaudit.check_md_files(book_directory)
profiler.disable()
profiler.dump_stats("profile_output.prof")
    