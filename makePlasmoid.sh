#!/bin/bash

zip  -x ".git/*" -x ".project" -x ".settings/*" -x ".pydevproject"  -x "*/*.pyc" -x ".gitignore" -x "makePlasmoidPkg.sh"  -r ../plasma_gcal.plasmoid .
scp ../plasma_gcal.plasmoid gdr@pornel.net:public_html/gdrwpl/heavy/
