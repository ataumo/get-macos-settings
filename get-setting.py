#!/usr/bin/env python3

from distutils.log import debug
from fileinput import filename
from sqlite3 import Timestamp
import sys
import argparse
import logging
import os
from datetime import datetime
import subprocess
import plistlib
import json
import pbPlist

#logging.info("You passed an argument.")
#logging.debug("Your Argument: %s" % args.argument)

################################################################################
#                                                                              #
#                                 FUNCTIONS                                    #
#                                                                              #
################################################################################

#MAIN_DOMAINS = [".GlobalPreferences_m","NSGlobalDomain"]
MAIN_DOMAINS = ["NSGlobalDomain", "com.apple.systempreferences", "com.apple.finder", "com.apple.desktopservices", "com.apple.Safari", "com.apple.AppleMultitouchTrackpad", "com.apple.dock","com.apple.universalaccess"]
BAD_DOMAINS = ["com.apple.CloudSubscriptionFeatures.config","com.apple.Maps"]
#DOMAINS = [".GlobalPreferences_m","NSGlobalDomain", "ContextStoreAgent", "MobileMeAccounts", "UBF8T346G9.OfficeOneDriveSyncIntegration", "com.apple.AMPLibraryAgent", "com.apple.Accessibility"]
DOMAINS = []
DYNAMIC_CONTENT = {}

# Gather our code in a main() function

ignore_string = ["NSWindowFrameMainWindowFrameSystemPreferencesApp8.0",
                "_DKThrottledActivityLast_DKKnowledgeStorageLogging_DKKnowledgeStorageDidInsertEventsNotification"]

def get_timestamp_file_name():
    now = datetime.now()
    date_time = now.strftime("/tmp/config-%y%m%d-%H%M%S")
    return date_time

def check_outputs(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    output, err = process.communicate()
    return output.decode('ascii')

def quit_system_pref_app():
    os.system("osascript -e \'tell application \"System Preferences\" to quit\'")

def get_all_domains():
    output = check_outputs(["defaults", "domains"])
    output = output.replace('\n','')
    array = output.split(', ')
    return array

def get_all_domains_bis():
    dirlist = os.listdir('/Users/louiscoumau/Library/Preferences')
    return dirlist

def get_all_domains_bis_bis():
    path = '/Users/louiscoumau/Library/Preferences'
    gendir = (file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file)))
    return gendir

# to compare configurations from last snapshot
def compare_dicts(domain, before_dict, after_dict):
    if not after_dict:
        logging.debug("Domain " + domain + " does not exist")
        return
    for key in after_dict:
        logging.debug(key)
        # check key adding...
        if key in before_dict:
            if type(before_dict[key]) is dict and type(after_dict[key]) is dict:
                compare_dicts(domain, before_dict[key], after_dict[key])
            else:
                if after_dict[key] != before_dict[key]:
                    print("> "+domain+" : "+key+" : "+str(before_dict[key])+" -> "+ str(after_dict[key]))
        else:
            print("+ "+domain+" : "+key+"  = "+str(after_dict[key]))

def compare():
    print("DOMAIN   KEY     VALUES")
    for domain in DOMAINS:
        compare_dicts(
            domain,
            DYNAMIC_CONTENT[domain]["before"], 
            DYNAMIC_CONTENT[domain]["after"])

# def take_snapshot():
#     #snap_file = get_timestamp_file_name()
#     snap_file = "/tmp/config-220909-204341.plist"
#     #os.system("defaults read > " + snap_file)
#     return snap_file

def take_snapshot():
    snap_file = get_timestamp_file_name()
    output = check_outputs(["defaults", "read"])
    with open(snap_file, 'wb') as fp:
        plistlib.dump(output ,fp, fmt=plistlib.FMT_XML, sort_keys=True, skipkeys=False)
        logging.debug("plutil -convert json "+snap_file)
    return snap_file

def take_snapshots():
    snap_files = []
    snap_file = get_timestamp_file_name()
    for domain in DOMAINS:
        filename = snap_file + "-" + domain + ".plist"
        snap_files.append(filename)
        error = os.system("defaults read "+ domain +" > " + filename)
        if error:
            filename = snap_file + "-" + domain
            os.system("defaults read "+ domain +" > " + filename)
        logging.debug("defaults read "+ domain +" > " + filename)
    return snap_files

def take_snapshots_from_timestamp(domain, timestamp):
    filename = "/tmp/config-" + timestamp + domain + ".plist"
    command = "defaults export '"+ domain +"' " + filename
    error = os.system(command)
    if error:
        logging.error("Error to save this domain : "+ domain)
        return ""
    logging.debug(command)
    return filename


def snap_and_save(status):
    timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
    for domain in DOMAINS:
        filename = take_snapshots_from_timestamp(domain, timestamp)
        if filename != "":
            output, content = get_content_from_plist(filename)
            if domain not in DYNAMIC_CONTENT:
                DYNAMIC_CONTENT[domain] = {}
            DYNAMIC_CONTENT[domain][status] = content
        else:
            logging.debug("File is empty")

def snap_and_save_bis(status):
    #timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
    for domain in DOMAINS:
        filename = '/Users/louiscoumau/Library/Preferences/'+domain
        content = get_content_from_plist(filename)
        if domain not in DYNAMIC_CONTENT:
            DYNAMIC_CONTENT[domain]={}
        DYNAMIC_CONTENT[domain][status] = content
    return True



def get_dict_from_file(filename):
    with open(filename, 'rb') as fp:
        #pl = plistlib.load(fp, dict_type=dict)
        pl = json.load(fp)
    return pl

def get_content_from_plist(path):
    test = pbPlist.pbPlist.PBPlist(path)
    try:
        file = pbPlist.pbPlist.PBPlist(path)
    except Exception:
        logging.error("Error parsing file " + path)
        return False, {}
    if not file.root:
        return False, {}
    content = file.root
    return True, content

def get_value_from_key(content,key):
    return content.get(key, None)



def main(args, loglevel):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)

    # Close any open System Preferences panes, to prevent them from overriding settings we’re about to change
    quit_system_pref_app()

    #
    # Snapshot case
    #
    if args.snapshot:
        print("Saving configuration...")
        take_snapshot()

    #
    # Record case
    #           
    if args.record:
        print("Saving configuration...")
        #snap_file = take_snapshot()
        snap_and_save('before')
        answer = input("Recording... Do anything in System Preferences application... [o/Q] ") 
        if answer != "o": 
            print("Aborting...")
            exit(1)
        else: 
            quit_system_pref_app()
            #new_snaps_files = take_snapshots()
            snap_and_save('after')
            # modification
            #DYNAMIC_CONTENT[DOMAINS[1]]["after"]["AppleMiniaturizeOnDoubleClick"] = '1'
            compare()


################################################################################
#                                                                              #
#                                 MAIN CODE                                    #
#                                                                              #
################################################################################


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Does a thing to some stuff.",
        epilog="As an alternative to the commandline, params can be placed in a file, one per line, and specified on the commandline like '%(prog)s @params.conf'.",
        fromfile_prefix_chars='@')
    # TODO Specify your real parameters here.
    parser.add_argument(
        "-r", 
        "--record", 
        action="store_true",
        help="to record a modification in files settings")
    parser.add_argument(
        "-a", 
        "--allDomains", 
        action="store_true",
        help="to record a modification in files settings from all domains")
    parser.add_argument(
        "-s", 
        "--snapshot", 
        action="store_true",
        help="to take a snapshot of a current configuration")
    parser.add_argument(
        "-v", 
        "--verbose", 
        action="store_true",
        help="to enable a verbose mode")

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    #
    # Setup domains array
    #
    if args.allDomains:
        DOMAINS = get_all_domains()
    else:
        DOMAINS = MAIN_DOMAINS
    
    logging.debug(DOMAINS)

    main(args, loglevel)
