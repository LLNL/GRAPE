import os
import option
import utility
import grapeMenu
import grapeGit as git
import grapeConfig


class Clone(option.Option):
    """ grape-clone
    Clones a git repo and configures it for use with git.

    Usage: grape-clone <url> <path> [--recursive] [--allNested]

    Arguments:
        <url>       The URL of the remote repository
        <path>      The directory where you want to clone the repo to.

    Options:
        --recursive   Recursively clone submodules.
        --allNested   Get all nested subprojects. 
        
    """

    def __init__(self):
        super(Clone, self).__init__()
        self._key = "clone"
        self._section = "Getting Started"

    #Clones the default repo into a new local repo
    def description(self):
        return "Clone a repo and configure it for grape"

    def execute(self, args):
        remotepath = args["<url>"]
        destpath = args["<path>"]
        rstr = "--recursive" if args["--recursive"] else ""
        git.clone(" %s %s %s" % (rstr, remotepath, destpath))
        print("Clone succeeded!")
        os.chdir(destpath)
        grapeConfig.read()
        menu = grapeMenu.menu()
        if args["--allNested"]:
            configArgs = ["--uv","--uvArg=--allNestedSubprojects"]
        else: 
            configArgs = []
        return menu.applyMenuChoice("config", configArgs)

    def setDefaultConfig(self, config):
        pass
