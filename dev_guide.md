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


For fresh developer
    1. switch to staging branch: git checkout staging
    2. Create a feature branch on your local:
        > git checkout dev_[your name/feature name] (i.e: dev_kuddus)
    3. make necessary changes and commit
    3. if you want to publish those changes on remote as well as your branch
        > git push origin dev_kuddus
    4. if you want to publish those changes on remote but not your branch:
        > switch to 'staging': git checkout staging
        > merge code from your 'dev_kuddus' local branch to 'staging' branch: git merge dev_kuddus
        > publish the commits to remote: git push origin staging

How to sync up with other git branches as well as your feature branch:
	Lets assume your remote 'origin' is setup already.

	1. make changes on a feature branch say 'dev_kuddus', commit that changes on local
	2. push that changes to remote branch 'dev_kuddus'
	3. share your commits via 'staging' branch
		> switch to 'staging' local branch: git checkout staging
		> merge the commits of your branch: git merge dev_kuddus
		> push the changes to origin branch 'staging'
		> resume on your local branch: git checkout 'dev_kuddus'

	4. whoever then, working on his branch say 'dev_boyati', merge the updated code from staging branch
		> switch to 'staging' local branch: git checkout staging
		> pull the new code: git pull
		> switch to your local branch 'dev_boyati': git checkout dev_boyati
		> update your local branch from 'staging': git merge staging
		> update your remote branch 'dev_boyati': git push

