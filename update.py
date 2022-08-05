#!/usr/bin/env python3
'''
Система доставки.

Позволяет скачивать / кешировать / обновлять все решения всех заданных Д/З всех
зарегистрированных пользователей и формировать «паспорт» решения с метаданными
(время первого/последнего коммита, закешированное расположение удалённых тестов
и т. п.).
'''

import datetime as dt
from os.path import dirname, realpath, isfile, isdir, join, basename, getsize
import zipfile
import urllib.request
import io

def get_task_list(tasks: str) -> list[(str, int, dt.date)]:

	with open(tasks) as f:
		names_tmp = f.readlines()
		
	tasks = []
	for i in range(len(names_tmp)):
		date = (names_tmp[i].split('/'))[0]
		date =  date[4:6] + '-' + date[6:] + '-' + date[:4]
		deadline = (dt.datetime.strptime(date, '%m-%d-%Y') + dt.timedelta(days = 7)).date()
		tasks.append((names_tmp[i][:-1], i, deadline))
	return tasks


def get_user_list(repositories: str) -> list[(str, int, str)]:
	with open(repositories) as r:
		repos_tmp = r.readlines()

	user_list = []	
	for i in range(len(repos_tmp)):
		tmp_data = repos_tmp[i].split()
		name = tmp_data[2]+ " " + tmp_data[3] + " " + tmp_data[4] 
		url = tmp_data[1]
		user_list.append((name, i, url))
	
	return user_list



def gitlabdir(url: str, save_dir: str) -> str:
    """
    Download directory from GitLab public archive
	:param url: Directory URL 
	:test_dir:  path of local directory
	:return:   path to directory with files
	"""
    
    base, path = url.split("/-/")
    branch = path.split("/")[1]
    path = "/".join(path.split("/")[2:])
    zipurl = f"{base}/-/archive/{branch}/archive.zip?path={path}"
    with urllib.request.urlopen(zipurl) as f:
    	zipdir = zipfile.ZipFile(io.BytesIO(f.read()))
    zipdir.extractall(save_dir)
    return save_dir + "/" + zipdir.namelist()[1] 

def githubdir(url: str, save_dir: str) -> str:
    """
    Download directory from GitHub public archive
	:param url: Directory URL 
	:test_dir: path of local directory
	:return:   path to directory with files
	"""
    
    base, path = url.split("/tree/")
    name = base.split("/")[-1]
    branch = path.split("/")[0]
    path = f"{name}-{branch}/" + "/".join(path.split("/")[1:])
    base = base.replace("//","//codeload.")
    zipurl = f"{base}/zip/{branch}"

    with urllib.request.urlopen(zipurl) as f:
        zipdir = zipfile.ZipFile(io.BytesIO(f.read()))

    
    zipdir.extractall(save_dir)
    return save_dir + "/" + path
    

def gitlabfile(url: str, save_dir: str) -> str:
	"""
    Download single file from GitLab
	:param url: File URL
	:param save_dir: path to directory to save
	:return:    path to file
	"""
	base, path = url.split("/-/")
	dpath = path.replace("blob/","raw/")+"?inline=false"
    
	with urllib.request.urlopen(base+"/-/"+dpath) as f:
		name = save_dir + "/" + basename(path)
		with open(f"{name}", 'wb') as file:
			file.write(f.read())
	
	return name

def githubfile(url: str, save_dir: str) -> str:
    """
    Download single file from GitHub
	:param url: File URL
	:param save_dir: path to directory to save
	:return:    path to file
	"""
    durl = url.replace("/blob/","/").replace("/github.com/", "/raw.githubusercontent.com/")
    with urllib.request.urlopen(durl) as f:
        name = save_dir + "/" + durl.split("/")[-1]
        with open(f"{name}", 'wb') as file:
            file.write(f.read())

    return name

#print(githubdir("https://github.com/ipsavitsky/pythonprac/tree/master/20210916/1", "./savitsky"))
#print(githubdir("https://github.com/ipsavitsky/pythonprac/tree/master/20210916", "./test"))
#print(gitlabdir("https://git.cs.msu.ru/s02190290/python-prac-2021/-/tree/main/20220221", "./test"))
#print(githubfile("https://github.com/ipsavitsky/pythonprac/blob/master/20210916/1/prog.py", "./test"))
