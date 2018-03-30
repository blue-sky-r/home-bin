#!/usr/bin/env python3
#
# Normalize IPA - iphone app filename from Info.plist properties (configurable)
#
# Usefull for archiving purposes when multiple app versions are stored localy.

import zipfile
import sys, os, re
import plistlib

FORMAT  = '%CFBundleName-v%CFBundleVersion-ios%MinimumOSVersion'
FORMAT2 = '%CFBundleDisplayName-v%CFBundleVersion-ios%MinimumOSVersion'

MAJOR = 'MinimumOSVersion DTPlatformVersion CFBundleVersion CFBundleDisplayName CFBundleName'

INFO = '/Info.plist'

_version_ = '2018.3'

_usage_ = """
= IPA rename = normalize ipa filename = version {} =

> {} [-n] [-k key] [-f format] src.ipa

 n         ... dry-run, do not rename anything, just show what would be done
 k key     ... do not rename, just display specific key matched as case-sensitive substring
 k all     ... do not rename, just display complete list of properties
 k major   ... do not rename, just display list of major properties
 k 'k1 k2' ... do not rename, just display k1 and k2 property
 f format  ... specify format string (default {})
 src.ipa   ... source file(s) (shell expansion apply)

examples:

 dry-run only:
 {} -n /NAS/apps/ttb.ipa

 display list of properties:
 {} -k all /NAS/apps/ttb.ipa

 use alternate format for normalization:
 {} -f '%CFBundleDisplayName-v%CFBundleVersion-ios%MinimumOSVersion' /NAS/apps/ttb.ipa

 shell expansion to process all files in specifix dir:
 {} /NAS/apps/*.ipa
"""

ERR = {
    2: 'ERR: ZIP error:{}',
    3: 'ERR: {} not found',
    4: 'ERR: not valid IPA file:{}',
    5: 'ERR: {} returns empty property list'
}

def usage():
    if len(sys.argv) > 1: return
    S0 = sys.argv[0]
    print(_usage_.format(_version_, S0, FORMAT, S0, S0, S0, S0))
    sys.exit(1)

def error(code, par=''):
    """ print message ERR[exitcode] and die with exitcode """
    print(ERR.get(code,'').format(par), file=sys.stderr)

def ipa_readplist(ipa, plist):
    """ read plist from ipa/zip file or die with error """
    root = None
    try:
        with zipfile.ZipFile(ipa, 'r') as zip:
            err = zip.testzip()
            if err:
                error(2, err)
                return
            for zinfo in zip.infolist():
                #print("{}".format(zinfo.filename))
                if zinfo.filename.endswith(plist):
                    data = zip.read(zinfo)
                    break
                else:
                    error(3, INFO)
                    return
            root = plistlib.loads(data)
    except zipfile.BadZipFile:
        error(4, ipa)
    return root

def print_plist(plist, match='all', sep=' '):
    """ print plist keys matching substring match """
    # multiple match - match has multiple keys separated by separator sep
    if sep in match:
        for k in match.split(sep):
            print("{}: {}".format(k, plist.get(k, '')))
        return
    # single match - do substring match
    for k in plist:
        if match == 'all' or match in k:
            print("{}: {}".format(k, plist.get(k, '')))
    return

def format_name(plist, format, space='_', ext='.ipa'):
    """ build new name based on format tokens """
    # start with format string
    name = format
    # all %tokens
    for token in re.findall('(%[A-Z][a-zA-Z]+)', format):
        # replace with plist
        name = name.replace(token, plist.get(token[1:],''), 1)
    # space replacement
    return name.replace(' ', space) + ext


# ======
#  MAIN
# ======

# usage help
usage()

# init
frm, key, dry = FORMAT, None, False

# iterate cmd line parameters
it = iter(sys.argv[1:])
for par in it:

    # dry run: -n
    if par == '-n':
        dry = True
        continue

    # format string: -format 'format string'
    if par.startswith('-f'):
        frm = next(it)
        continue

    # just show key(s): -key key or -key 'k1 k2 k3' or -key all
    if par.startswith('-k'):
        key = next(it)
        continue

    # filename
    ipa = par
    plist = ipa_readplist(ipa, INFO)
    if plist is None:
        error(5, ipa)
        continue

    # display major keys: -key major
    if key == 'major':
        print_plist(plist, MAJOR)
        continue

    # display key(s): -key *key* or -key all
    if key:
        print_plist(plist, key)
        continue

    # rename
    newname = ipa.replace(os.path.basename(ipa), format_name(plist, frm))
    # verbose output
    print("{} -> {}".format(ipa, newname), end=' ')
    if dry:
        print()
        continue
    try:
        os.rename(ipa, newname)
        print('OK')
    except OSError as e:
        print('ERR: {}'.format(e.strerror))
