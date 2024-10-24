import argparse
import logging
import hashlib
import os
import shutil
import time

def parse_arguments():
    """
    Returns the source folder, replica folder, interval and log file path
    """
    parser = argparse.ArgumentParser(description="Synchronizes two folders.")
    parser.add_argument("source", help="Source folder path")
    parser.add_argument("replica", help="Replica folder path")
    parser.add_argument("interval", type=int, help="Synchronization interval (seconds)")
    parser.add_argument("logfile", help="Path to the log file")
    return parser.parse_args()

def setup_logging(logfile):
    """
    Configures logging to write to both a file and console output
    """
    logging.basicConfig(filename=logfile, level=logging.INFO,
                        format='%(asctime)s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S')
    logging.getLogger().addHandler(logging.StreamHandler())

def calculate_md5(file_path):
    """
    Calculates the MD5 checksum of a file
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):  # Read the file in chunks
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def sync_folders(source, replica):
    """
    Copies new or updated files from the source to the replica and removes files in the replica that no longer exist in the source
    """
    # Check files in source and synchronize them in the replica
    for dirpath, _, filenames in os.walk(source):
        rel_path = os.path.relpath(dirpath, source)  # Relative path to handle subdirectories
        replica_dir = os.path.join(replica, rel_path)

        # Create directory in replica if it doesn't exist
        if not os.path.exists(replica_dir):
            os.makedirs(replica_dir)
            logging.info(f"Directory created: {replica_dir}")

        # Copy or update files
        for file in filenames:
            src_file = os.path.join(dirpath, file)
            replica_file = os.path.join(replica_dir, file)

            if not os.path.exists(replica_file) or calculate_md5(src_file) != calculate_md5(replica_file):
                shutil.copy2(src_file, replica_file)  # Copy with metadata (timestamps)
                logging.info(f"Copied file: {src_file} to {replica_file}")

    # Remove files from replica that no longer exist in source
    for dirpath, _, filenames in os.walk(replica):
        rel_path = os.path.relpath(dirpath, replica)
        source_dir = os.path.join(source, rel_path)

        if not os.path.exists(source_dir):
            shutil.rmtree(dirpath)  # Remove directory if it doesn't exist in source
            logging.info(f"Directory removed: {dirpath}")
            continue

        # Remove individual files
        for file in filenames:
            replica_file = os.path.join(dirpath, file)
            source_file = os.path.join(source_dir, file)

            if not os.path.exists(source_file):
                os.remove(replica_file)
                logging.info(f"File removed: {replica_file}")

def main():
    """
    Synchronizes folders every given interval, up to a max of 5 times (this one i decided to put myself, it's not require in the PDF you sent me)
    """
    args = parse_arguments()
    setup_logging(args.logfile)

    max_syncs = 5
    sync_count = 0

    while sync_count < max_syncs:
        logging.info(f"Starting synchronization {sync_count + 1}/{max_syncs}")
        sync_folders(args.source, args.replica)
        logging.info(f"Synchronization {sync_count + 1} completed. Next sync in {args.interval} seconds.")
        sync_count += 1
        time.sleep(args.interval)

    logging.info("Reached maximum number of synchronizations. Exiting...")

if __name__ == "__main__":
    main()
