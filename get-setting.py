#!/usr/bin/env python3

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
from unittest import case
import pbPlist
import biplist
from tabulate import tabulate

#logging.info("You passed an argument.")
#logging.debug("Your Argument: %s" % args.argument)

# Mains domains are used by default when '-a', '--all-domains' option is not given
MAIN_DOMAINS = ["NSGlobalDomain", "com.apple.systempreferences", "com.apple.finder", "com.apple.desktopservices", "com.apple.Safari", "com.apple.AppleMultitouchTrackpad", "com.apple.dock","com.apple.universalaccess"]
# A domain to ignore is one on which it is strongly recommended not to manually apply any modifications (because the data is too complex) or because it provides no information about the OS configuration.
EXCLUDED_DOMAINS = ["com.apple.CloudSubscriptionFeatures.config","com.apple.Maps", "com.apple.spaces.plist"]
DYNAMIC_CONTENT = {}
PRINT_TABLE = []

MAX_VALUE_LENGTH = 15

################################################################################
#                                                                              #
#                                 FUNCTIONS                                    #
#                                                                              #
################################################################################
OKGREEN = '\033[92m'
WARNING = '\033[93m'
ENDC = '\033[0m'
######
def yellow_print(string):
    print(f"{WARNING}"+string+f"{ENDC}")
def green_print(string):
    print(f"{OKGREEN}"+string+f"{ENDC}")
######

def truncate_text(text_object):
    """
    Truncate the input text to a length defined by MAX_VALUE_LENGTH, 
    and append '...' at the end if the text is longer than this limit.
    """
    text=str(text_object)
    # Remove all newline characters
    cleaned_text = text.replace('\n', ' ')
    if len(cleaned_text) > MAX_VALUE_LENGTH:
        return cleaned_text[:MAX_VALUE_LENGTH - 3] + "..."
    else:
        return cleaned_text

def custom_serializer(o):
    if isinstance(o, datetime):
        # Convert datetime object to ISO 8601 string format
        return o.isoformat()
    # Fallback for other objects
    return o.__dict__

def is_valid_timestamp(value):
    # Check if the value is a float and within a reasonable timestamp range
    # In macOS, timestamps in Property List (plist) files are represented as the number of seconds since the reference date, 
    # which is January 1, 2001, 00:00:00 UTC (978310800). This is different from the Unix timestamp format, 
    # which is based on the number of seconds since January 1, 1970.
    # source : https://www.epochconverter.com/coredata
    start=978310800
    unix_timestamp = start+value
    if isinstance(unix_timestamp, float) and 1577840400 <= unix_timestamp <= 32503680000:  # Between 2020 and 3000 (as unix time stamp)
        try:
            # Try to convert it to a datetime object
            timestamp=datetime.fromtimestamp(unix_timestamp)
            logging.debug("timestamp :" + str(timestamp))
            return True
        except (OSError, ValueError):
            # If there's an error in conversion, it's not a valid timestamp
            return False
    return False

def dir_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)

def check_outputs(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    output, err = process.communicate()
    return output.decode('ascii')

def quit_system_pref_app():
    os.system(r"pkill -9 System\ Preferences")

def get_all_domains():
    output = check_outputs(["defaults", "domains"])
    output = output.replace('\n','')
    array = output.split(', ')
    return array

# to compare configurations from last snapshot
def compare_dicts(domain, before_dict, after_dict):
    if not after_dict:
        logging.debug("Domain " + domain + " does not exist")
        return
    if type(after_dict) is not dict:
        logging.debug("This content is not a dict")
        return
    for key in after_dict.keys():
        logging.debug("----------------------------> " + str(key))
        # check added keys...
        all_content = False
        to_print = True
        if all_content:
            to_print=True 
        else:
            # ignore this types 
            if isinstance(after_dict[key], biplist.Data):
                to_print=False
            # datetime
            if isinstance(after_dict[key], datetime):
                to_print=False
            # timestamps
            if isinstance(after_dict[key], float) and is_valid_timestamp(after_dict[key]):
                to_print=False
        # data exists in two configurations
        if key in before_dict:
            if isinstance(before_dict[key], dict) and isinstance(after_dict[key], dict):
                compare_dicts(domain+' : '+key, before_dict[key], after_dict[key])
            elif isinstance(before_dict[key], list) and isinstance(after_dict[key], list):
                compare_lists(domain+' : '+key, before_dict[key], after_dict[key])
            else:
                if after_dict[key] != before_dict[key] and to_print:
                    if not isinstance(after_dict[key], dict):
                        content_1 = before_dict[key]
                        content_2 = after_dict[key]
                    else :
                        content_1 = json.dumps(before_dict[key], indent=4, default=custom_serializer, sort_keys=True)
                        content_2 = json.dumps(after_dict[key], indent=4, default=custom_serializer, sort_keys=True)

                    yellow_print("> "+domain+" : "+str(key)+" : "+truncate_text(content_1)+" -> "+ truncate_text(content_2))
                    PRINT_TABLE.append(['>',domain, key, str(content_1), str(content_2)])
        # data does not exists in new configuration (new value)
        elif to_print:
            if isinstance(after_dict[key], dict):
                content = json.dumps(after_dict[key], indent=4, default=custom_serializer, sort_keys=True)
            else:
                content = after_dict[key]
            green_print("+ "+domain+" : "+key+" : "+ truncate_text(content))
            PRINT_TABLE.append(['+',domain, key, '', str(content)])



def compare_lists(domain, before_list, after_list):
    if not after_list:
        logging.debug("Domain " + domain + " does not exist")
        return
    for i in range(len(after_list)):
        logging.debug(after_list[i])
        # check key adding...
        all_content = False
        to_print = True
        if all_content:
            to_print=True 
        else:
            if after_list[i] is biplist.Data:
                to_print=False
            if after_list[i] is datetime:
                to_print=False
        if after_list[i] == 'NSPSignatureInfo':
            print('OK')
        if after_list[i] in before_list:
            before_index = before_list.index(after_list[i])
            if type(before_list[before_index]) is dict and type(after_list[i]) is dict:
                compare_dicts(domain+' : '+ str(i) , before_list[before_index], after_list[i])
            elif type(before_list[before_index]) is list and len(before_list[before_index])>1 and type(after_list[i]) is list:
                compare_dicts(domain+' : '+ str(i), before_list[before_index], after_list[i])
            #else:
                #if to_print:
                    #print("> "+domain+" : "+str(i)+" : "+str(before_list[before_index])+" -> "+ str(after_list[i]))
                    #PRINT_TABLE.append(['>',domain, str(i), str(before_list[i]), str(after_list[i])])
        elif to_print:
            content = json.dumps(after_list[i], indent=4, default=lambda o: o.__dict__, sort_keys=True)
            green_print("+ "+domain+" : "+str(i)+" : "+ content)
            #PRINT_TABLE.append(['+',domain, str(i), '', str(after_list[i])])

def compare():
    print("-------- DIFF ---------")
    col_names = ["Status", "Domain", "Key", "Old value", "New value"]
    #t=PrettyTable(['Symbol', 'Domain', ''])
    for domain in DYNAMIC_CONTENT:
        if "before" in DYNAMIC_CONTENT[domain] and "after" in DYNAMIC_CONTENT[domain]: 
            compare_dicts(
                domain,
                DYNAMIC_CONTENT[domain]["before"], 
                DYNAMIC_CONTENT[domain]["after"])
    print(tabulate(PRINT_TABLE, headers=col_names))

def export_config(domain, directory):
    filename = directory + '/' + domain + ".plist"
    command = "defaults export '"+ domain +"' " + filename
    error = os.system(command)
    if error:
        return ""
    logging.debug(command)
    return filename


def snap_config(scope_domains, status=""):
    logging.debug("Function : snap_config")
    timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
    directory = '/tmp/config-'+timestamp
    os.mkdir(directory)
    for domain in scope_domains:
        filename = export_config(domain, directory)
        if filename != "":
            if not status:
                output, content = get_content_from_plist(filename)
                if domain not in DYNAMIC_CONTENT:
                    DYNAMIC_CONTENT[domain] = {}
                DYNAMIC_CONTENT[domain][status] = content
        else:
            logging.error("Error to save this domain : "+ domain)
    return directory


def get_content_from_plist(path):
    try:
        file = pbPlist.pbPlist.PBPlist(path)
    except Exception:
        logging.error("Error parsing file " + path)
        return False, {}
    if not file.root:
        return False, {}
    content = file.root
    return True, content

def get_content_from_directory(status, directory):
    for domain in os.listdir(directory):
        f = os.path.join(directory, domain)
        # checking if it is a file
        if os.path.isfile(f):
            logging.debug(f)
            output, content = get_content_from_plist(f)
            if domain not in DYNAMIC_CONTENT:
                DYNAMIC_CONTENT[domain] = {}
            DYNAMIC_CONTENT[domain][status] = content



def main(args, loglevel):
    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)

    # Close any open System Preferences panes, to prevent them from overriding settings we’re about to change
    quit_system_pref_app()

    #
    # Setup domains array
    #
    if args.allDomains:
        logging.debug("Getting all domains...")
        scope_domains = get_all_domains()
        logging.debug("Done.")
    else:
        scope_domains = MAIN_DOMAINS
        logging.debug("Selected domains :%s\n" % str(MAIN_DOMAINS))

    #
    # Snapshot case
    #
    if args.snapshot:
        if args.allDomains:
            print("Saving configuration for all domains...")
        else : 
            print("Saving configuration for these domains : ")
            print(scope_domains)
        directory = snap_config(scope_domains)
        print(directory+" has been created.")

    #
    # Record case
    #           
    if args.record:
        print("Saving configuration...")
        #snap_file = take_snapshot()
        snap_config(scope_domains, 'before')
        answer = input("Recording... Do anything in System Preferences application... [o/Q] ") 
        if answer != "o": 
            print("Aborting...")
            exit(1)
        else: 
            quit_system_pref_app()
            snap_config(scope_domains, 'after')
            # modification
            #DYNAMIC_CONTENT[DOMAINS[1]]["after"]["AppleMiniaturizeOnDoubleClick"] = '1'
            compare()

    if args.diff:
        oldconfig, newconfig = args.diff
        print(oldconfig, newconfig)
        get_content_from_directory('before',oldconfig)
        get_content_from_directory('after',newconfig)
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
    # Parameters
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
    parser.add_argument(
        "-d", 
        "--diff", 
        nargs=2,
        type=dir_path,
        metavar=('old-config-directory', 'new-config-directory'),
        help="to compare 2 configurations (they mys be already saved in directory)")

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    main(args, loglevel)
