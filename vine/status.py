import os
import option
import grapeGit as git
import utility
import config


class Status(option.Option):
    """
    Usage: grape-status [-u | --uno] 
              [--failIfInconsistent] 
              [--failIfMissingPublicBranches]
              [--failIfBranchesInconsistent]
              [--checkWSOnly]

    Options:
    --uno                          Do not show untracked files
    -u                             Show untracked files. 
    --failIfInconsistent           Fail if any consistency checks fail. 
    --failIfMissingPublicBranches  Fail if your workspace or your origin's workspace is missing public branches. 
    --failIfOnInconsistentBranches Fail if your subprojects are on branches that are inconsistent with what is checked out in your workspace. 
    --checkWSOnly                  Only check the workspace's projects' branches for consistency. Don't gather git statuses.
    

    """
    def __init__(self):
        super(Status, self).__init__()
        self._key = "status"
        self._section = "Workspace"

    def description(self):
        return "Gives the status for this workspace"
    
    # print the status for the entire workspace
    def printStatus(self, args):
        wsDir = utility.workspaceDir()
        statusArgs = ""
        if args["-u"]:
            statusArgs += "-u "
        if args["--uno"]:
            statusArgs += "-uno "
        
        launcher = utility.MultiRepoCommandLauncher(getStatus, 
                                        runInSubmodules=True, 
                                        runInSubprojects=True, 
                                        runInOuter=True,
                                        globalArgs=[statusArgs, wsDir])
        
        stati = launcher.launchFromWorkspaceDir(noPause=True)
        status = {}
        for s, r in (zip(stati, launcher.repos)):
            status[r] = s
            
        for sub in status.keys():
            for line in status[sub]: 
                lstripped = line.strip()
                if lstripped:
                    # filter out branch tracking status
                    # ## bugfix/bugfixday/DLThreadSafety...remotes/origin/bugfix/bugfixday/DLThreadSafety [ahead 1]
                    # ## bugfix/bugfixday/DLThreadSafety...remotes/origin/bugfix/bugfixday/DLThreadSafety [behind 29]
                    if lstripped[0:2] == "##":
                        if "[ahead" in lstripped or "[behind" in lstripped:
                            print os.path.abspath(os.path.join(wsDir, sub))+': ' + lstripped
                        continue
                    # print other statuses
                    print ' ' + lstripped
    
    def checkForLocalPublicBranches(self, args):
        publicBranchesExist = True
        # Check that all public branches exist locally. 
        cfg = config.grapeConfig.grapeConfig()
        publicBranches = cfg.getPublicBranchList()
        missingBranches = config.Config.checkIfPublicBranchesExist(cfg, utility.workspaceDir(), 
                                                                   publicBranches)
        
        if (len(missingBranches) > 0 ): 
            for mb in missingBranches:
                utility.printMsg("Repository is missing public branch %s, attempting to fetch it now..." % mb)
                try:
                    git.fetch("origin %s:%s" % (mb, mb))
                    utility.printMsg("%s added as a local branch" % mb)
                except git.GrapeGitError as e:
                    print e.gitOutput
                    publicBranchesExist = False
        return publicBranchesExist
                    
    def checkForConsistentWorkspaceBranches(self, args):
        consistentBranchState = True
        cfg = config.grapeConfig.grapeConfig()
        publicBranches = cfg.getPublicBranchList()
        wsDir = utility.workspaceDir()
        os.chdir(wsDir)
        wsBranch = git.currentBranch()
        subPubMap = cfg.getMapping("workspace", "submodulepublicmappings")
        if wsBranch in publicBranches:
            for sub in git.getActiveSubmodules():
                os.chdir(os.path.join(wsDir,sub))
                subbranch = git.currentBranch()
                if subbranch != subPubMap[wsBranch]:
                    consistentBranchState=False
                    utility.printMsg("Submodule %s on branch %s when grape expects it to be on %s" %
                                     (sub, subbranch, subPubMap[wsBranch]))
        else:
            for sub in git.getActiveSubmodules():
                os.chdir(os.path.join(wsDir,sub))
                subbranch = git.currentBranch()
                if subbranch != wsBranch:
                    consistentBranchState = False
                    utility.printMsg("Submodule %s on branch %s when grape expects it to be on %s" % 
                                     (sub, subbranch, wsBranch))
                    
        # check that nested subproject branching is consistent
        for nested in config.grapeConfig.GrapeConfigParser.getAllActiveNestedSubprojectPrefixes():
            os.chdir(os.path.join(wsDir,nested))
            nestedbranch = git.currentBranch()
            if nestedbranch != wsBranch: 
                consistentBranchState = False
                utility.printMsg("Nested Project %s on branch %s when grape expects it to be on %s" % 
                                 (nested,nestedbranch, wsBranch))

        return consistentBranchState
        
    def execute(self, args):

        with utility.cd(utility.workspaceDir()):
            
    
            if not args["--checkWSOnly"]:
                self.printStatus(args)
    
            # Sanity check workspace layout
            publicBranchesExist = self.checkForLocalPublicBranches(args)       
            
            
            # Check that submodule branching is consistent
            consistentBranchState = self.checkForConsistentWorkspaceBranches(args)
        
        retval = True
        if args["--failIfInconsistent"]:
            retval = retval and publicBranchesExist and consistentBranchState
        if args["--failIfMissingPublicBranches"]:
            retval = retval and publicBranchesExist
        if args["--failIfBranchesInconsistent"]:
            retval = retval and consistentBranchState
        return retval        

    
    def setDefaultConfig(self, config):
        pass

def getStatus(branch='', repo='', args=''):
    statusArgs = args[0]
    wsDir = args[1]
    toReturn = []
    
    sub = repo
    if not sub.strip():
        return ""
    try:
        
        with utility.cd(sub):        
            subStatus = git.status("--porcelain -b %s" % statusArgs).split('\n')
            for line in subStatus: 
                strippedL = line.strip()
                if strippedL:
                    tokens = strippedL.split()
                    tokens[0] = tokens[0].strip()
                    if len(tokens[0]) == 1: 
                        tokens[0] = " %s " % tokens[0]
                    if wsDir == sub:
                        relPath = ""
                        toReturn.append(' '.join([tokens[0], tokens[1]]))
                    else:
                        relPath = os.path.relpath(sub, wsDir)                        
                        toReturn.append(' '.join([tokens[0], '/'.join([relPath, tokens[1]])]))
        return toReturn
    except Exception as e:
        print e

