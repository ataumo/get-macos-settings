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
from unittest import case
import pbPlist
import biplist
from tabulate import tabulate

#logging.info("You passed an argument.")
#logging.debug("Your Argument: %s" % args.argument)

#MAIN_DOMAINS = [".GlobalPreferences_m","NSGlobalDomain"]
MAIN_DOMAINS = ["NSGlobalDomain", "com.apple.systempreferences", "com.apple.finder", "com.apple.desktopservices", "com.apple.Safari", "com.apple.AppleMultitouchTrackpad", "com.apple.dock","com.apple.universalaccess"]
BAD_DOMAINS = ["com.apple.CloudSubscriptionFeatures.config","com.apple.Maps"]
#DOMAINS = [".GlobalPreferences_m","NSGlobalDomain", "ContextStoreAgent", "MobileMeAccounts", "UBF8T346G9.OfficeOneDriveSyncIntegration", "com.apple.AMPLibraryAgent", "com.apple.Accessibility"]
DOMAINS = []
DYNAMIC_CONTENT = {}
PRINT_TABLE = []

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
    os.system("pkill -9 System\ Preferences")

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
    for key in after_dict:
        logging.debug(key)
        # check key adding...
        all_content = False
        to_print = True
        if all_content:
            to_print=True 
        else:
            if type(after_dict[key]) is biplist.Data:
                to_print=False
            if type(after_dict[key]) is datetime:
                to_print=False
        if key in before_dict:
            if type(before_dict[key]) is dict and type(after_dict[key]) is dict:
                compare_dicts(domain+' : '+key, before_dict[key], after_dict[key])
            elif type(before_dict[key]) is list and type(after_dict[key]) is list:
                compare_lists(domain+' : '+key, before_dict[key], after_dict[key])
            else:
                if after_dict[key] != before_dict[key] and to_print:
                    content_1 = json.dumps(before_dict[key], indent=4, default=lambda o: o.__dict__, sort_keys=True)
                    content_2 = json.dumps(after_dict[key], indent=4, default=lambda o: o.__dict__, sort_keys=True)
                    #print("> "+domain+" : "+key+" : "+str(before_dict[key])+" -> "+ str(after_dict[key]))
                    yellow_print("> "+domain+" : "+key+" : "+content_1+" -> "+ content_2)
                    #PRINT_TABLE.append(['>',domain, key, str(before_dict[key]), str(after_dict[key])])
        elif to_print:
            content = json.dumps(after_dict[key], indent=4, default=lambda o: o.__dict__, sort_keys=True)
            green_print("+ "+domain+" : "+key+" : "+ content)
            #PRINT_TABLE.append(['+',domain, key, '', str(after_dict[key])])



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


def snap_config(status=""):
    timestamp = datetime.now().strftime("%y%m%d-%H%M%S")
    directory = '/tmp/config-'+timestamp
    os.mkdir(directory)
    for domain in DOMAINS:
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
    # Snapshot case
    #
    if args.snapshot:
        if args.allDomains:
            print("Saving configuration for all domains...")
        else : 
            print("Saving configuration for these domains : ")
            print(DOMAINS)
        directory = snap_config()
        print(directory+" has been created.")

    #
    # Record case
    #           
    if args.record:
        print("Saving configuration...")
        #snap_file = take_snapshot()
        snap_config('before')
        answer = input("Recording... Do anything in System Preferences application... [o/Q] ") 
        if answer != "o": 
            print("Aborting...")
            exit(1)
        else: 
            quit_system_pref_app()
            snap_config('after')
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
    #
    # Setup domains array
    #
    if args.allDomains:
        DOMAINS = get_all_domains()
    else:
        DOMAINS = MAIN_DOMAINS
    
    
    logging.debug(DOMAINS)

    main(args, loglevel)
