from subprocess import run

# Keeps the translations up-to-date by extracting, updating, and compiling them in one step.
run(
    [
        "fastapi-rtk",
        "translate",
        "build",
        "--root-path",
        "./fastapi_rtk/lang",
        "--extract-dir",
        "./fastapi_rtk",
        "--no-merge-with-internal",
    ]
)
