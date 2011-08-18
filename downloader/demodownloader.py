'''
Created on 31.05.2010

@author: Malte Legenhausen
'''

from functools import partial

import logging
import ftplib
import zipfile
import os
import sys
import re
import ConfigParser
import datetime
import time


LOCAL_PATTERN = re.compile(
    "^([0-9]{4})([0-9]{2})([0-9]{2})-([0-9]{2})([0-9]{2})-(\\w+)\.zip$",
    re.IGNORECASE
)

REMOTE_PATTERN = re.compile(
    "^([0-9]{4})([0-9]{2})([0-9]{2})-([0-9]{2})([0-9]{2})-(\\w+)\.dem$",
    re.IGNORECASE
)

logging.basicConfig(
    level=logging.NOTSET, 
    format="%(asctime)s:%(levelname)s:%(message)s"
)

def zipped_name(filename):
    return filename.split(".")[0] + ".zip"

def demo_name(filename):
    return filename.split(".")[0] + ".dem"

def download(ftp, filename):
    with open(filename, "wb") as fp:
        ftp.retrbinary("RETR %s" % filename, fp.write)
    
def has_changed_remotely(ftp, filename, remote_size):
    logging.info("Checking if remote file %s has changed..." % filename)
    zippedfile = zipfile.ZipFile(zipped_name(filename))
    local_size = zippedfile.getinfo(filename).file_size
    if local_size < remote_size:
        logging.info("Size of %s has been changed from %d to %d." % (filename, local_size, remote_size))
        return True
    
    logging.info("File %s has not be changed." % filename)
    return False
    
def batch_download(ftp, files):
    downloaded = []
    for filename in files:        
        logging.info("Downloading %s..." % filename)    
        try:
            download(ftp, filename)
            downloaded.append(filename)
        except Exception:
            logging.error("Unable to download %s." % filename)
            os.remove(filename)
        else:
            logging.info("%s successful downloaded." % filename)
    return downloaded

def determine_files(ftp, new_demos, changed_demos, maps, days, line):
    tokens = line.split()
    filename = tokens[-1]
    
    if not filename.endswith(".dem"):
        return
    
    match = REMOTE_PATTERN.match(filename)
    if not match.group(6) in maps:
        return

    if is_expired(filename, days, REMOTE_PATTERN):
        logging.debug("%s is expired", filename)
        return
 
    # Remote file size
    size = int(tokens[4])
    if not os.path.exists(zipped_name(filename)):
        new_demos.append(filename)
    elif has_changed_remotely(ftp, filename, size):
        changed_demos.append(filename)
        
def retr_demolist(ftp, maps, days):
    new_demos = []
    changed_demos = []
    callback = partial(determine_files, ftp, new_demos, changed_demos, maps, days)
    ftp.retrlines('LIST', callback)
    return new_demos, changed_demos
            
def download_demos(address, username, password, path, maps, days):
    downloaded = []
    ftp = ftplib.FTP(address)
    ftp.set_pasv(True)
    try:
        ftp.login(username, password)
        ftp.cwd(path)
        logging.info("Start downloading demos from %s..." % address)
        new_demos, changed_demos = retr_demolist(ftp, maps, days)
        logging.info("%d new and %d changed demos found." % (len(new_demos), len(changed_demos)))
        new_demos = batch_download(ftp, new_demos)
        changed_demos = batch_download(ftp, changed_demos)
        if downloaded:
            logging.info("Download complete.")
    except Exception, e:
        logging.error("Unable to connect to %s. (%s)" % (address, e))
    finally:
        ftp.close()
    
    return new_demos, changed_demos

def compress_file(file):
    zipfilename = zipped_name(file)
    logging.info("Compressing file %s to %s..." % (file, zipfilename))
    try:
        zip = zipfile.ZipFile(zipfilename, "w", zipfile.ZIP_DEFLATED)
        zip.write(file)
        logging.info("File %s compressed." % file)
    except Exception:
        logging.error("Unable to zip file %s" % file)
    finally:
        zip.close()

def compress_demos(files):
    logging.info("Start compressing %d files" % len(files))
    for file in files:
        compress_file(file)
    logging.info("Compressing finished")
    
def delete_demos(files):
    logging.info("Removing all *.dem files...")
    for file in files:
        os.remove(file)
    logging.info("All *.dem files removed.")
    
def file_to_timestamp_map(filename, pattern=LOCAL_PATTERN):
    match = pattern.match(filename)
    datetime_group = match.group(1, 2, 3, 4, 5)
    year, month, day, hour, minute = map(lambda x: int(x), datetime_group)
    timetuple = datetime.datetime(year, month, day, hour, minute).timetuple()
    timestamp = time.mktime(timetuple)
    return int(timestamp), match.group(6)
    
def is_expired(filename, days, pattern=LOCAL_PATTERN):
    timestamp, _ = file_to_timestamp_map(filename, pattern)
    offset = int(days) * 24 * 60 * 60 # days in seconds
    return timestamp + offset < int(time.time())

def delete_expired_files(days):
    logging.info("Remove all expired *.dem files...")
    for filename in os.listdir('.'):
        if LOCAL_PATTERN.match(filename) and is_expired(filename, int(days)):
            os.remove(filename)
    logging.info("All expired *.dem files removed.")    
        
def main(argv):
    config = ConfigParser.RawConfigParser()
    config.read(argv[1])
    os.chdir(config.get('general', 'workspace'))
    
    new_demos, changed_demos = download_demos(
        config.get('ftp', 'address'), 
        config.get('ftp', 'username'), 
        config.get('ftp', 'password'), 
        config.get('ftp', 'path'),
        config.get('general', 'maps').split(","),
	config.get('general', 'expiration')
    )
    
    all_demos = new_demos + changed_demos
    if all_demos:
        compress_demos(all_demos)
        delete_demos(all_demos)
        
    expiration = config.get('general','expiration')
    delete_expired_files(expiration)

if __name__ == '__main__':
    main(sys.argv)
