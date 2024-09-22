# TODO

This project is currently in development. **We welcome your contribution too !**

## TODO LIST
- [ ] Improve grobal efficent (optimize loops or identify useless instructions to remove it)
- [ ] Feed the list of domains 
  - [ ] to be ignored (EXCLUDED_DOMAINS)
  - [ ] default domains (MAIN_DOMAINS)
> A domain to ignore is one on which it is strongly recommended not to manually apply any modifications (because the data is too complex) or because it provides no information about the OS configuration.

- As arguments:
  - [ ] Add option to ignore all datetime changes (only for modified values, not created ones)
  - [ ] Add option to extract data to csv. It could be done by 2 ways : 
    - At the last print, when the PRINT_TABLE value is printed, this value could be converted to csv format and stored in file
    - When comparing, when data is added to the PRINT_TABLE list
  - [ ] Add option to get diff more efficienlty (but less beauty) with diff tool `plist-diff.sh` 
    - `./plist-diff.sh /tmp/config-240921-134636 /tmp/config-240921-134727`
  - [ ] Add option to convert diff to a csv file formated to be read by [HardeningPuppy](https://github.com/ataumo/macos_hardening) script, as "Registry policies".

## DONE
- [X] Add timestamps in time ingore option 