# BOOKQUEST

Book quest is an ecommerce website where book lovers can buy any book they want. Our website also provide diverse reviews about books given buy our users, which can be used to make informed purchases. It also recommeds users popular books.

technical details:
It uses open api library to populate webiste, has a cacheing mechanism that stores previous queris and data recived form open library api to give seemless experience for users. Due to this mechanism as the number of users grow on website loading time will be almost negligable.

## for developer

### setting up project to run via vscode
- clone the repository form github into vscode

# creating virtual environment
- create virtual environment using "python3 -m venv venv" for mac "python -m venv venv" for windows
- activate virtual environment using "source .venv/bin/activate" for mac "venv\Scripts\activate" for windows

# installing requiremetns
- for windows use "pip install -r requirements.txt"
- for mac use "pip3 install -r requirements.txt"

# creating a feature branch
- create a feature branch you going to work on using "git branch feature_branch_name"(replace feature_branch_name with your branch name)

# commit in local repository
- add files to stagging area using "git add *"
- commit files uisng 'git commit -m "commit messgae"'

# push code to remote repository
- push code to remote using 
    - "git push origin feature_branch" if want to push changes made in current feature branch
    - "git push origin --all" if want to push changes made in all branches

# Make a pull request
- once the feature branch is pushed to remote repo
- make a pull request to merge the branch to main, using github web interface
- assign atleast one reviewer 


# to run via terminal
 - for windown run "python main.py" command
 - for mac run "pyton3 main.py" command

# to run docker image
- install docker in your device from https://www.docker.com/products/docker-desktop/
- run "docker pull janar363/book_quest:latest" command in terminal
- run "docker run -d -p 3000:3000 janar363/book_quest:latest " command in you terminal to run docker image and port it to localhost: 3000
- go to browser and type "localhost: 3000" to access the application

# docker run failed
- run "docker ps" to check if any image to ported to localost 3000
- if it returns any docker image running at the port copy it container id
- run "docker stop container_id" command to stop the image
- the follow above "to run docker image" steps to re-run docker image

- also make sure you docker is installed and running in you device
