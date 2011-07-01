#!/bin/bash

zip  -x ".git/*" -x ".project" -x ".settings/*" -x ".pydevproject"  -x "*/*.pyc" -x ".gitignore" -x "makePlasmoidPkg.sh"  -r ../plasma_gcal.plasmoid .
scp ../plasma_gcal.plasmoid gdr@gdr.name:/srv/gdr.geekhood.net/gdrwpl/heavy/
