"""CLI entrypoint for a non-uploading private Python Worker build."""

from data_intel.worker_build import main

if __name__ == "__main__":
    raise SystemExit(main())
