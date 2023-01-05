# import sys

# from .db import conn, read_tags, read_files
# from .obsidian_cli import main
from .obsidian_cli import main

if __name__ == "__main__":
    main()
    # if len(sys.argv) == 2 and sys.argv[1] == "tags":
    #     tags = read_tags(conn)
    #     for tag in tags:
    #         sys.stdout.write(tag + "\n")

    # elif len(sys.argv) == 3 and sys.argv[1] == "files":
    #     files = read_files(conn, sys.argv[2])
    #     for p, f, e in files:
    #         sys.stdout.write(f"{p}/{f}{e}\n")

    # elif len(sys.argv) == 3 and sys.argv[1] == "open":
    #     main(["open", sys.argv[2]])

    # conn.commit()
    # conn.close()
