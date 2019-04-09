** DO NOT COMMIT ON MASTER BRANCH DIRECTLY, MERGE CODE VIA PULL REQUEST

repository branch structure to follow:

                     master
                        |
                        |
                     staging
     ___________________|______________________________.....
     |               |                |              |
     |               |                |              |
    dev_kuddus      feature1         dev_boyati      .....


    * 'master' branch is for production/finalized version
    * 'staging' branch is for testing/intermediate stage for inter-branch communication
    * all the children of 'staging' branch are feature branches or dedicated dev branch for individual developer
    * 'dev_kuddus' branch holder has to confirm the updated code of his branch is on 'staging' so that 'dev_boyati' branch holder can update code from 'staging'
    * 'dev_boyati' branch holder has to update code from 'staging'


For fresh developer:

    1. clone this repo on your local machine
    2. switch to staging branch: git checkout staging
    3. Create a feature branch on your local:
        > git checkout dev_[your name/feature name] (i.e: dev_kuddus)
    4. make necessary changes and commit
    5. if you want to publish those changes on remote as well as your branch
        > git push origin dev_kuddus
    6. if you want to publish those changes on remote but not your branch:
        > switch to 'staging': git checkout staging
        > merge code from your 'dev_kuddus' local branch to 'staging' branch: git merge dev_kuddus
        > publish the commits to remote: git push origin staging

How to sync up with other git branches as well as your feature branch:

	Lets assume your remote 'origin' is setup already.

	1. make changes on a feature branch say 'dev_kuddus', commit those changes on local
	2. check if there is any updated code and pull the updated code (if any): git pull
	3. merge updated code (if any) with local code and push those changes to remote branch 'dev_kuddus': git push
	4. share your commits via 'staging' branch
		> switch to 'staging' local branch: git checkout staging
		> pull the updated code: git pull
		> merge the codes of your branch to 'staging': git merge dev_kuddus
		> push the changes to origin branch 'staging' resolving merge conflict (if any): git push
		> resume on your local branch: git checkout 'dev_kuddus'
		> merge the updated code (if any) from 'staging' : git merge staging
		> publish your updated code (if any): git push

	5. whoever then, working on his branch say 'dev_boyati', merge the updated code from staging branch
		> switch to 'staging' local branch: git checkout staging
		> pull the new code: git pull
		> switch to your local branch 'dev_boyati': git checkout dev_boyati
		> update your local branch from 'staging': git merge staging
		> update your remote branch 'dev_boyati': git push

    * 2nd point needs to perform always for any branch you visit.
